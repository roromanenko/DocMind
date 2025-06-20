"""
Text cleaning and normalization functionality
"""
import logging
import re
import unicodedata
from typing import Optional, Dict, Any, Literal
from docmind.config.settings import settings

# HTML parsing
try:
    from bs4 import BeautifulSoup
    import html
    HTML_PARSING_AVAILABLE = True
except ImportError:
    HTML_PARSING_AVAILABLE = False
    BeautifulSoup = None
    html = None

logger = logging.getLogger(__name__)

# Type for Unicode normalization forms
UnicodeForm = Literal['NFC', 'NFD', 'NFKC', 'NFKD']


class TextCleaner:
    """
    Service for cleaning and normalizing text content
    """
    
    def __init__(self, 
                 remove_html: Optional[bool] = None,
                 normalize_whitespace: Optional[bool] = None,
                 normalize_punctuation: Optional[bool] = None,
                 remove_control_chars: Optional[bool] = None,
                 unicode_normalization: Optional[bool] = None,
                 min_sentence_length: Optional[int] = None,
                 min_words: Optional[int] = None,
                 unicode_format: Optional[UnicodeForm] = None):
        """
        Initialize text cleaner with settings from config or custom values
        """
        # Use settings defaults if not provided
        self.remove_html = remove_html if remove_html is not None else settings.text_cleaning_remove_html
        self.normalize_whitespace = normalize_whitespace if normalize_whitespace is not None else settings.text_cleaning_normalize_whitespace
        self.normalize_punctuation = normalize_punctuation if normalize_punctuation is not None else settings.text_cleaning_normalize_punctuation
        self.remove_control_chars = remove_control_chars if remove_control_chars is not None else settings.text_cleaning_remove_control_chars
        self.unicode_normalization = unicode_normalization if unicode_normalization is not None else settings.text_cleaning_unicode_normalization
        self.min_sentence_length = min_sentence_length if min_sentence_length is not None else settings.text_cleaning_min_sentence_length
        self.min_words = min_words if min_words is not None else settings.text_cleaning_min_words
        
        # Validate and set unicode format
        unicode_format_value = unicode_format if unicode_format is not None else settings.text_cleaning_unicode_format
        if unicode_format_value not in ('NFC', 'NFD', 'NFKC', 'NFKD'):
            logger.warning(f"Invalid unicode format: {unicode_format_value}. Using NFC.")
            unicode_format_value = 'NFC'
        self.unicode_format: UnicodeForm = unicode_format_value
        
        # Compile regex patterns for better performance
        self._compile_regex_patterns()
        
        # Check HTML parsing availability
        if self.remove_html and not HTML_PARSING_AVAILABLE:
            logger.warning("HTML parsing not available (beautifulsoup4 not installed). HTML removal will be disabled.")
            self.remove_html = False
    
    def _compile_regex_patterns(self):
        """Compile regex patterns for better performance"""
        # Whitespace normalization patterns
        self._multiple_spaces_pattern = re.compile(r'[ \t]+')
        self._multiple_newlines_pattern = re.compile(r'\n\s*\n\s*\n+')
        self._single_newlines_pattern = re.compile(r'(?<!\n)\n(?!\n)')
        self._final_spaces_pattern = re.compile(r' +')
        
        # Punctuation normalization patterns
        self._smart_quotes_pattern = re.compile(r'["""]')
        self._smart_apostrophes_pattern = re.compile(r'[\u2018\u2019]')
        self._dashes_pattern = re.compile(r'[–—]')
        self._ellipsis_pattern = re.compile(r'\.{3,}')
        self._space_before_punct_pattern = re.compile(r'\s+([.,!?;:])')
        self._duplicate_punct_pattern = re.compile(r'([.,!?;:])\s*([.,!?;:])')
        self._space_after_punct_pattern = re.compile(r'([.,!?;:])([A-Za-z])')
        
        # Control characters pattern (non-printable except newlines, tabs, carriage returns)
        self._control_chars_pattern = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]')
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned and normalized text
        """
        if not text or not text.strip():
            return ""
        
        # Unicode normalization
        if self.unicode_normalization:
            text = unicodedata.normalize(self.unicode_format, text)
        
        # Remove HTML tags if enabled
        if self.remove_html:
            text = self._remove_html_tags(text)
        
        # Remove control characters if enabled
        if self.remove_control_chars:
            text = self._remove_control_characters(text)
        
        # Normalize whitespace if enabled
        if self.normalize_whitespace:
            text = self._normalize_whitespace(text)
        
        # Normalize punctuation if enabled
        if self.normalize_punctuation:
            text = self._normalize_punctuation(text)
        
        # Final cleanup
        text = text.strip()
        
        logger.debug(f"Text cleaned: {len(text)} characters")
        return text
    
    def _remove_html_tags(self, text: str) -> str:
        """Remove HTML/XML tags using BeautifulSoup"""
        if not HTML_PARSING_AVAILABLE or html is None or BeautifulSoup is None:
            # Fallback to simple regex if BeautifulSoup not available
            text = re.sub(r'<[^>]+>', '', text)
            return text
        
        try:
            # Unescape HTML entities first
            text = html.unescape(text)
            
            # Parse with BeautifulSoup and extract text
            soup = BeautifulSoup(text, "lxml")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            return text
        except Exception as e:
            logger.warning(f"HTML parsing failed: {e}. Falling back to regex.")
            # Fallback to simple regex
            text = re.sub(r'<[^>]+>', '', text)
            return text
    
    def _remove_control_characters(self, text: str) -> str:
        """Remove control characters using compiled regex"""
        return self._control_chars_pattern.sub('', text)
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace characters using compiled patterns"""
        # Replace multiple spaces with single space
        text = self._multiple_spaces_pattern.sub(' ', text)
        
        # Normalize line breaks
        # Replace multiple newlines with double newlines
        text = self._multiple_newlines_pattern.sub('\n\n', text)
        
        # Replace single newlines with spaces (except for double newlines)
        text = self._single_newlines_pattern.sub(' ', text)
        
        # Clean up any remaining multiple spaces
        text = self._final_spaces_pattern.sub(' ', text)
        
        return text
    
    def _normalize_punctuation(self, text: str) -> str:
        """Normalize punctuation marks using compiled patterns"""
        # Normalize quotes
        text = self._smart_quotes_pattern.sub('"', text)  # Smart quotes to straight quotes
        text = self._smart_apostrophes_pattern.sub("'", text)  # Smart apostrophes to straight
        
        # Normalize dashes
        text = self._dashes_pattern.sub('-', text)  # En/em dashes to hyphen
        
        # Normalize ellipsis
        text = self._ellipsis_pattern.sub('...', text)
        
        # Fix spacing around punctuation
        text = self._space_before_punct_pattern.sub(r'\1', text)  # Remove space before punctuation
        text = self._duplicate_punct_pattern.sub(r'\1', text)  # Remove duplicate punctuation
        
        # Fix spacing after punctuation
        text = self._space_after_punct_pattern.sub(r'\1 \2', text)
        
        return text
    
    def clean_sentences(self, sentences: list[str]) -> list[str]:
        """
        Clean a list of sentences and filter out short ones (by word count and length)
        
        Args:
            sentences: List of sentence strings
            
        Returns:
            List of cleaned sentences
        """
        cleaned_sentences = []
        
        for sentence in sentences:
            cleaned = self.clean_text(sentence)
            if cleaned:
                words = cleaned.split()
                if len(cleaned.strip()) >= self.min_sentence_length and len(words) >= self.min_words:
                    cleaned_sentences.append(cleaned.strip())
        
        return cleaned_sentences
    
    def get_cleaning_stats(self, original_text: str, cleaned_text: str) -> Dict[str, Any]:
        """
        Get statistics about the cleaning process
        
        Args:
            original_text: Original text before cleaning
            cleaned_text: Text after cleaning
            
        Returns:
            Dictionary with cleaning statistics
        """
        return {
            "original_length": len(original_text),
            "cleaned_length": len(cleaned_text),
            "reduction_percent": round((1 - len(cleaned_text) / len(original_text)) * 100, 2) if original_text else 0,
            "original_words": len(original_text.split()),
            "cleaned_words": len(cleaned_text.split()),
            "word_reduction_percent": round((1 - len(cleaned_text.split()) / len(original_text.split())) * 100, 2) if original_text.split() else 0
        }


# Global cleaner instance with default settings
text_cleaner = TextCleaner() 