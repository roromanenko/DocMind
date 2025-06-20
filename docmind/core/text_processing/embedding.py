"""
Async text embedding functionality using OpenAI text-embedding-ada-002 with smart token-based batching and intelligent retries
"""
import logging
import asyncio
import random
from typing import List, Optional, Tuple, Dict, Any
from openai import AsyncOpenAI
from openai import RateLimitError, APIError, APITimeoutError, APIConnectionError
import tiktoken
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    before_sleep_log,
    after_log
)

from docmind.config.settings import settings
from docmind.core.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Async embedding service with smart token-based batching and intelligent retries
    """
    
    def __init__(self):
        self._async_client: Optional[AsyncOpenAI] = None
        self._tokenizer: Optional[tiktoken.Encoding] = None
        self._model = settings.embedding_model
        self._dimension = settings.embedding_dimension
        self._max_tokens_per_batch = settings.embedding_max_tokens_per_batch
        self._max_batch_size = settings.embedding_max_batch_size
        self._max_text_tokens = settings.embedding_max_text_tokens
        self._batch_base_delay = settings.embedding_batch_base_delay
        self._batch_jitter_min = settings.embedding_batch_jitter_min
        self._batch_jitter_max = settings.embedding_batch_jitter_max
    
    def _get_async_client(self) -> AsyncOpenAI:
        """Get or create async OpenAI client with retry configuration"""
        if self._async_client is None:
            if not settings.openai_api_key:
                raise EmbeddingError("OpenAI API key not configured")
            
            # Create async client with retry configuration
            self._async_client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                max_retries=3,  # Built-in retries
                timeout=30.0    # Request timeout
            )
            logger.info("Async OpenAI client initialized with retry configuration")
        
        return self._async_client
    
    def _get_tokenizer(self) -> tiktoken.Encoding:
        """Get or create tokenizer for the embedding model"""
        if self._tokenizer is None:
            try:
                # Use the appropriate tokenizer for text-embedding-ada-002
                self._tokenizer = tiktoken.encoding_for_model("text-embedding-ada-002")
                logger.info("Tokenizer initialized for text-embedding-ada-002")
            except Exception as e:
                logger.warning(f"Failed to initialize tokenizer: {e}. Using cl100k_base as fallback.")
                self._tokenizer = tiktoken.get_encoding("cl100k_base")
        
        return self._tokenizer
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using the appropriate tokenizer
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        if not text:
            return 0
        
        tokenizer = self._get_tokenizer()
        return len(tokenizer.encode(text))
    
    def truncate_text_by_tokens(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit
        
        Args:
            text: Text to truncate
            max_tokens: Maximum number of tokens
            
        Returns:
            Truncated text
        """
        if not text:
            return ""
        
        tokenizer = self._get_tokenizer()
        tokens = tokenizer.encode(text)
        
        if len(tokens) <= max_tokens:
            return text
        
        # Truncate tokens and decode back to text
        truncated_tokens = tokens[:max_tokens]
        return tokenizer.decode(truncated_tokens)
    
    def create_smart_batches(self, texts: List[str]) -> List[List[Tuple[str, int]]]:
        """
        Create smart batches based on token count with pre-computed token counts
        
        Args:
            texts: List of texts to batch
            
        Returns:
            List of batches, where each batch contains (text, token_count) tuples
        """
        if not texts:
            return []
        
        # Pre-process texts: clean, truncate, and count tokens
        processed_texts = []
        for text in texts:
            # Clean and validate text
            if not text or not text.strip():
                cleaned_text = "empty text"
            else:
                cleaned_text = text.strip()
            
            # Truncate if too long
            if len(cleaned_text) > 1000:  # Quick check before tokenization
                cleaned_text = self.truncate_text_by_tokens(cleaned_text, self._max_text_tokens)
            
            # Count tokens once
            token_count = self.count_tokens(cleaned_text)
            processed_texts.append((cleaned_text, token_count))
        
        # Create batches based on token count
        batches = []
        current_batch = []
        current_tokens = 0
        
        for text_tuple in processed_texts:
            text, token_count = text_tuple
            
            # Check if adding this text would exceed limits
            would_exceed_tokens = current_tokens + token_count > self._max_tokens_per_batch
            would_exceed_size = len(current_batch) >= self._max_batch_size
            
            if would_exceed_tokens or would_exceed_size:
                # Save current batch if it has content
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                    current_tokens = 0
            
            # Add text to current batch
            current_batch.append(text_tuple)
            current_tokens += token_count
        
        # Add final batch if it has content
        if current_batch:
            batches.append(current_batch)
        
        logger.debug(f"Created {len(batches)} smart batches from {len(texts)} texts")
        return batches
    
    @retry(
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIConnectionError, APIError)),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        stop=stop_after_attempt(5),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO)
    )
    async def _make_async_embedding_request(self, input_texts: List[str]) -> List[List[float]]:
        """
        Make async embedding request with automatic retries
        
        Args:
            input_texts: List of texts to embed
            
        Returns:
            List of embeddings as List[float] (not numpy arrays)
            
        Raises:
            EmbeddingError: If all retries fail
        """
        try:
            client = self._get_async_client()
            response = await client.embeddings.create(
                model=self._model,
                input=input_texts
            )
            
            # Extract embeddings and convert to List[float] immediately
            embeddings = [data.embedding for data in response.data]
            return embeddings
            
        except (RateLimitError, APITimeoutError, APIConnectionError, APIError) as e:
            logger.warning(f"Async API request failed (retryable): {type(e).__name__}: {e}")
            raise  # Re-raise for tenacity to handle
        except Exception as e:
            logger.error(f"Async API request failed (non-retryable): {type(e).__name__}: {e}")
            raise EmbeddingError(f"Non-retryable error: {str(e)}")
    
    async def get_embeddings_async(self, texts: List[str], max_concurrent_batches: int = 3) -> List[List[float]]:
        """
        Generate embeddings asynchronously with intelligent retries and exponential backoff
        
        Args:
            texts: List of text strings to embed
            max_concurrent_batches: Maximum number of batches to process concurrently
            
        Returns:
            List of embeddings as List[float]
            
        Raises:
            EmbeddingError: If embedding generation fails after all retries
        """
        if not texts:
            return []
        
        try:
            # Create smart batches with pre-computed token counts
            batches = self.create_smart_batches(texts)
            
            if max_concurrent_batches <= 1:
                # Sequential processing
                all_embeddings = []
                for batch_idx, batch in enumerate(batches):
                    batch_texts = [text for text, _ in batch]
                    batch_tokens = sum(token_count for _, token_count in batch)
                    
                    logger.debug(f"Processing batch {batch_idx+1}/{len(batches)} with {len(batch)} texts, {batch_tokens} tokens")
                    
                    try:
                        batch_embeddings = await self._make_async_embedding_request(batch_texts)
                        all_embeddings.extend(batch_embeddings)
                        
                        logger.debug(f"Batch {batch_idx+1} processed successfully")
                        
                    except Exception as e:
                        logger.error(f"Failed to process batch {batch_idx+1} after all retries: {e}")
                        raise EmbeddingError(f"Batch processing failed: {str(e)}")
                    
                    # Rate limiting: adaptive delay between batches (non-blocking)
                    if batch_idx + 1 < len(batches):
                        base_delay = self._batch_base_delay
                        token_factor = batch_tokens / 1000
                        delay = base_delay * (1 + token_factor)
                        jitter = random.uniform(self._batch_jitter_min, self._batch_jitter_max)
                        delay = delay * jitter
                        
                        logger.debug(f"Waiting {delay:.3f}s before next batch")
                        await asyncio.sleep(delay)
                
                total_tokens = sum(token_count for batch in batches for _, token_count in batch)
                logger.info(f"Generated embeddings for {len(texts)} texts ({total_tokens} tokens) using {self._model}")
                return all_embeddings
            
            else:
                # Concurrent processing
                semaphore = asyncio.Semaphore(max_concurrent_batches)
                
                async def process_batch(batch: List[Tuple[str, int]], batch_idx: int) -> List[List[float]]:
                    async with semaphore:
                        batch_texts = [text for text, _ in batch]
                        batch_tokens = sum(token_count for _, token_count in batch)
                        logger.debug(f"Processing batch {batch_idx+1} with {len(batch)} texts, {batch_tokens} tokens")
                        return await self._make_async_embedding_request(batch_texts)
                
                # Create tasks for all batches
                tasks = [
                    process_batch(batch, idx) 
                    for idx, batch in enumerate(batches)
                ]
                
                # Execute all tasks concurrently
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Combine results and handle exceptions
                all_embeddings = []
                for idx, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"Batch {idx+1} failed: {result}")
                        raise EmbeddingError(f"Batch {idx+1} failed: {str(result)}")
                    all_embeddings.extend(result)  # type: ignore
                
                total_tokens = sum(token_count for batch in batches for _, token_count in batch)
                logger.info(f"Generated embeddings for {len(texts)} texts ({total_tokens} tokens) using concurrent processing")
                return all_embeddings
                
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise EmbeddingError(f"Embedding generation failed: {str(e)}")
    
    async def get_embedding_async(self, text: str) -> List[float]:
        """
        Generate embedding for a single text asynchronously
        
        Args:
            text: Text string to embed
            
        Returns:
            Embedding as List[float]
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        embeddings = await self.get_embeddings_async([text])
        return embeddings[0] if embeddings else []
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings generated by the current model"""
        return self._dimension
    
    async def validate_model_async(self) -> bool:
        """
        Validate that the embedding model is accessible asynchronously
        
        Returns:
            True if model is accessible, False otherwise
        """
        try:
            client = self._get_async_client()
            
            # Try to get model info asynchronously
            response = await client.models.list()
            available_models = [model.id for model in response.data]
            
            if self._model not in available_models:
                logger.warning(f"Model {self._model} not found in available models")
                return False
            
            logger.info(f"Embedding model {self._model} is accessible")
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate embedding model: {e}")
            return False
    
    def validate_model(self) -> bool:
        """
        Synchronous wrapper for validate_model_async
        """
        return asyncio.run(self.validate_model_async())
    
    async def get_stats_async(self) -> Dict[str, Any]:
        """Get embedding service statistics asynchronously"""
        try:
            client = self._get_async_client()
            
            # Get model info asynchronously
            response = await client.models.list()
            available_models = [model.id for model in response.data]
            
            # Test tokenizer
            tokenizer = self._get_tokenizer()
            test_tokens = self.count_tokens("This is a test sentence.")
            
            return {
                "model": self._model,
                "dimension": self._dimension,
                "model_available": self._model in available_models,
                "tokenizer_working": test_tokens > 0,
                "test_tokens": test_tokens,
                "async_client": True,
                "retry_config": {
                    "max_retries": 5,
                    "exponential_backoff": True,
                    "jitter": True
                },
                "available_models": available_models[:10],  # Show first 10 models
                "client_initialized": self._async_client is not None,
                "max_tokens_per_batch": self._max_tokens_per_batch,
                "max_text_tokens": self._max_text_tokens
            }
            
        except Exception as e:
            return {
                "model": self._model,
                "dimension": self._dimension,
                "error": str(e),
                "async_client": True,
                "client_initialized": self._async_client is not None
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Synchronous wrapper for get_stats_async
        """
        return asyncio.run(self.get_stats_async())
    
    def analyze_text_tokens(self, texts: List[str]) -> Dict[str, Any]:
        """
        Analyze token usage for a list of texts
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            Dictionary with token analysis
        """
        if not texts:
            return {"total_texts": 0, "total_tokens": 0, "avg_tokens": 0}
        
        token_counts = [self.count_tokens(text) for text in texts]
        total_tokens = sum(token_counts)
        
        return {
            "total_texts": len(texts),
            "total_tokens": total_tokens,
            "avg_tokens_per_text": round(total_tokens / len(texts), 2),
            "min_tokens": min(token_counts),
            "max_tokens": max(token_counts),
            "token_distribution": {
                "0-100": len([t for t in token_counts if t <= 100]),
                "101-500": len([t for t in token_counts if 101 <= t <= 500]),
                "501-1000": len([t for t in token_counts if 501 <= t <= 1000]),
                "1001+": len([t for t in token_counts if t > 1000])
            }
        }


# Global service instance for backward compatibility
_embedding_service = EmbeddingService()


# Backward compatibility functions
def get_embeddings_async(texts: List[str], max_concurrent_batches: int = 3) -> List[List[float]]:
    """Backward compatibility function"""
    return asyncio.run(_embedding_service.get_embeddings_async(texts, max_concurrent_batches))


def get_embedding_async(text: str) -> List[float]:
    """Backward compatibility function"""
    return asyncio.run(_embedding_service.get_embedding_async(text))


def get_embeddings(texts: List[str], max_tokens_per_batch: int = 8000) -> List[List[float]]:
    """Backward compatibility function"""
    return asyncio.run(_embedding_service.get_embeddings_async(texts))


def get_embedding(text: str) -> List[float]:
    """Backward compatibility function"""
    return asyncio.run(_embedding_service.get_embedding_async(text))


def get_embedding_dimension() -> int:
    """Backward compatibility function"""
    return _embedding_service.get_embedding_dimension()


def validate_embedding_model_async() -> bool:
    """Backward compatibility function"""
    return asyncio.run(_embedding_service.validate_model_async())


def validate_embedding_model() -> bool:
    """Backward compatibility function"""
    return _embedding_service.validate_model()


def get_embedding_stats_async() -> Dict[str, Any]:
    """Backward compatibility function"""
    return asyncio.run(_embedding_service.get_stats_async())


def get_embedding_stats() -> Dict[str, Any]:
    """Backward compatibility function"""
    return _embedding_service.get_stats()


def analyze_text_tokens(texts: List[str]) -> Dict[str, Any]:
    """Backward compatibility function"""
    return _embedding_service.analyze_text_tokens(texts)
