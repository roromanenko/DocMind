# Функциональность чанкинга в DocMind

## Обзор

DocMind теперь поддерживает автоматическое разбиение документов на смысловые блоки (чанки) для эффективного векторного поиска и анализа. Эта функциональность интегрирована в процесс ингестии документов и доступна через API.

## Архитектура

### Подход к чанкингу

Система использует **упрощенный подход** без хранения чанков в базе данных:
- Чанки генерируются **на лету** при запросе
- Метаданные о количестве чанков сохраняются в документе
- Это обеспечивает гибкость и упрощает архитектуру

### Компоненты

1. **TextChunker** (`docmind/core/text_processing/chunking.py`)
   - Основной сервис для разбиения текста
   - Настраиваемые параметры размера чанка и перекрытия
   - Интеллектуальное разбиение по границам предложений

2. **DocumentIngestionService** (обновлен)
   - Интеграция генерации чанков в процесс ингестии
   - Подсчет количества чанков для метаданных

3. **API эндпоинты** (новые)
   - `/documents/upload-with-chunks` - загрузка с возвратом чанков
   - `/documents/{document_id}/chunks` - получение чанков документа

## Конфигурация

### Настройки в `settings.py`

```python
# Document Processing
chunk_size: int = 1000        # Размер чанка в символах
chunk_overlap: int = 200      # Перекрытие между чанками
```

### Настройка чанкера

```python
from docmind.core.text_processing.chunking import TextChunker

# Использование настроек по умолчанию
chunker = TextChunker()

# Кастомные настройки
chunker = TextChunker(chunk_size=500, chunk_overlap=100)
```

## Использование

### 1. Загрузка документа с чанками

```bash
curl -X POST "http://localhost:8000/documents/upload-with-chunks" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@document.pdf"
```

**Ответ:**
```json
{
  "message": "Документ успешно загружен с чанками",
  "document": {
    "id": "uuid",
    "filename": "document.pdf",
    "chunk_count": 5,
    "status": "UPLOADED",
    ...
  },
  "chunks_count": 5,
  "chunks": [
    {
      "id": "chunk-uuid",
      "document_id": "document-uuid",
      "text": "Содержимое чанка...",
      "start_position": 0,
      "end_position": 1000,
      "length": 1000,
      "chunk_index": 0,
      "metadata": {...}
    }
  ]
}
```

### 2. Получение чанков существующего документа

```bash
curl -X GET "http://localhost:8000/documents/{document_id}/chunks" \
     -H "accept: application/json"
```

**Ответ:**
```json
{
  "document_id": "uuid",
  "chunks_count": 5,
  "chunks": [...]
}
```

### 3. Программное использование

```python
from docmind.core.text_processing.ingestion import DocumentIngestionService
from sqlalchemy.orm import Session

# Создание сервиса
service = DocumentIngestionService(db_session)

# Получение чанков документа
chunks = service.get_document_chunks(document_id)

# Обработка чанков
for chunk in chunks:
    print(f"Chunk {chunk['chunk_index']}: {chunk['text'][:100]}...")
```

## Алгоритм чанкинга

### 1. Предобработка текста
- Очистка от лишних пробелов и переносов строк
- Нормализация текста

### 2. Разбиение на предложения
- Использование регулярных выражений для определения границ предложений
- Сохранение семантической целостности

### 3. Формирование чанков
- Добавление предложений до достижения лимита размера
- Создание перекрытия между чанками для контекста
- Генерация уникальных ID для каждого чанка

### 4. Метаданные
Каждый чанк содержит:
- `id`: Уникальный идентификатор
- `document_id`: ID исходного документа
- `text`: Текстовое содержимое
- `start_position`, `end_position`: Позиции в исходном тексте
- `length`: Длина чанка
- `chunk_index`: Порядковый номер
- `metadata`: Дополнительные данные (имя файла, тип, размер)

## Преимущества подхода

### ✅ Плюсы
- **Простота**: Не требует дополнительных таблиц в БД
- **Гибкость**: Легко изменить параметры чанкинга
- **Консистентность**: Чанки всегда актуальны
- **Масштабируемость**: Не увеличивает размер БД

### ⚠️ Ограничения
- **Производительность**: Генерация при каждом запросе
- **Память**: Временное использование памяти
- **Кэширование**: Требует дополнительной реализации

## Примеры использования

### Тестирование чанкинга

```python
# test_chunking.py
from docmind.core.text_processing.chunking import TextChunker
import uuid

chunker = TextChunker(chunk_size=500, chunk_overlap=100)
document_id = uuid.uuid4()

chunks = chunker.split_text(long_text, document_id, metadata)
print(f"Generated {len(chunks)} chunks")
```

### Интеграция с векторным поиском

```python
# Будущая интеграция с Qdrant
for chunk in chunks:
    # Создание эмбеддинга
    embedding = embedding_model.encode(chunk['text'])
    
    # Сохранение в векторную БД
    vector_store.add_point(
        id=chunk['id'],
        vector=embedding,
        payload=chunk
    )
```

## Планы развития

1. **Кэширование чанков** в Redis для улучшения производительности
2. **Адаптивный чанкинг** на основе семантических границ
3. **Интеграция с Qdrant** для векторного поиска
4. **Параллельная обработка** больших документов
5. **Поддержка мультиязычности** в алгоритме чанкинга

## Заключение

Функциональность чанкинга обеспечивает основу для эффективного векторного поиска и анализа документов в DocMind. Упрощенный подход позволяет быстро внедрить функциональность и легко адаптировать её под конкретные потребности. 