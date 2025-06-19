# DocMind - Scalable RAG Application

Масштабируемое приложение на основе Retrieval-Augmented Generation (RAG) для обработки документов и интеллектуального поиска с использованием LLM.

## 🏗️ Архитектура

### Технологический стек

**Backend:**
- **FastAPI** - веб-фреймворк для API
- **SQLAlchemy + Alembic** - ORM и миграции БД
- **PostgreSQL** - основная база данных
- **Redis + Celery** - очереди и фоновые задачи
- **Chroma/Qdrant** - векторная база данных

**AI/ML:**
- **OpenAI GPT-4o** - LLM для генерации ответов
- **sentence-transformers** - для создания embeddings
- **langchain** - RAG pipeline

**Frontend:**
- **React + TypeScript** - веб-интерфейс
- **Electron** - десктопное приложение

### Архитектурный паттерн

Проект использует **Clean Architecture** с элементами **CQRS**:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   FastAPI   │  │   React     │  │   Electron  │         │
│  │   (API)     │  │   (Web)     │  │  (Desktop)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Use Cases │  │   Commands  │  │   Queries   │         │
│  │   (Services)│  │   (CQRS)    │  │   (CQRS)    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Entities  │  │   Value     │  │   Domain    │         │
│  │             │  │   Objects   │  │   Services  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ PostgreSQL  │  │   Vector DB │  │   File      │         │
│  │   (ORM)     │  │   (Chroma)  │  │   Storage   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Структура проекта

```
DocMind/
├── docmind/                    # Основной пакет
│   ├── core/                   # Доменная логика
│   │   ├── domain/            # Сущности и бизнес-логика
│   │   ├── application/       # Use cases и сервисы
│   │   └── infrastructure/    # Адаптеры для внешних систем
│   ├── api/                   # API слой
│   │   ├── routes/           # API маршруты
│   │   ├── middleware/       # Промежуточное ПО
│   │   └── dependencies/     # Зависимости API
│   ├── services/             # Бизнес-сервисы
│   │   ├── document_processing/  # Обработка документов
│   │   ├── embedding/        # Работа с embeddings
│   │   ├── rag/             # RAG pipeline
│   │   └── vector_store/    # Векторная БД
│   ├── utils/               # Утилиты
│   └── config/              # Конфигурация
├── frontend/                # Веб-интерфейс
├── tests/                   # Тесты
├── docs/                    # Документация
├── scripts/                 # Скрипты развертывания
├── docker/                  # Docker конфигурация
├── main.py                  # Точка входа
├── pyproject.toml          # Зависимости Poetry
└── README.md               # Документация
```

## 🚀 Установка и запуск

### Предварительные требования

- Python 3.9+
- Poetry
- PostgreSQL
- Redis
- Node.js 18+ (для frontend)

### 1. Клонирование и установка зависимостей

```bash
git clone <repository-url>
cd DocMind

# Установка Python зависимостей
poetry install

# Активация виртуального окружения
poetry shell
```

### 2. Настройка окружения

Создайте файл `.env` в корне проекта:

```env
# Application
DEBUG=true
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost/docmind
DATABASE_ECHO=false

# Redis
REDIS_URL=redis://localhost:6379

# Vector Database
VECTOR_DB_TYPE=chroma
VECTOR_DB_URL=

# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.7

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Document Processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_FILE_SIZE=104857600

# File Storage
UPLOAD_DIR=./uploads
TEMP_DIR=./temp

# Security
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# CORS
ALLOWED_ORIGINS=["http://localhost:3000"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

### 3. Настройка базы данных

```bash
# Создание миграций
alembic revision --autogenerate -m "Initial migration"

# Применение миграций
alembic upgrade head
```

### 4. Запуск приложения

```bash
# Запуск API сервера
poetry run python main.py

# Или через uvicorn
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Запуск фоновых задач

```bash
# Запуск Celery worker
poetry run celery -A docmind.core.infrastructure.celery_app worker --loglevel=info

# Запуск Celery beat (для периодических задач)
poetry run celery -A docmind.core.infrastructure.celery_app beat --loglevel=info
```

## 🔧 Основные функции

### Обработка документов

- **Поддерживаемые форматы:** PDF, DOCX, TXT
- **Автоматическая очистка:** удаление шумов, нормализация
- **Умная нарезка:** с учетом семантики и контекста
- **Извлечение метаданных:** автор, дата создания, тема и т.д.

### RAG Pipeline

1. **Загрузка документа** → извлечение текста
2. **Предобработка** → очистка и нормализация
3. **Нарезка на чанки** → оптимальный размер с перекрытием
4. **Генерация embeddings** → векторные представления
5. **Сохранение в векторной БД** → индексация для поиска
6. **Поиск релевантных чанков** → по запросу пользователя
7. **Генерация ответа** → с использованием LLM

### Масштабируемость

- **Асинхронная обработка** → Celery для фоновых задач
- **Пакетная обработка** → эффективная работа с большими объемами
- **Кэширование** → Redis для быстрого доступа
- **Горизонтальное масштабирование** → Docker контейнеры

## 🧪 Тестирование

```bash
# Запуск всех тестов
poetry run pytest

# Запуск с покрытием
poetry run pytest --cov=docmind

# Запуск конкретных тестов
poetry run pytest tests/unit/
poetry run pytest tests/integration/
```

## 📊 Мониторинг и логирование

- **Структурированное логирование** → JSON формат
- **Метрики производительности** → время обработки, размеры файлов
- **Аудит запросов** → логирование всех операций
- **Health checks** → мониторинг состояния сервисов

## 🔒 Безопасность

- **Аутентификация** → JWT токены
- **Авторизация** → ролевая модель доступа
- **Валидация файлов** → проверка типов и размеров
- **Rate limiting** → защита от DDoS
- **CORS** → настройка доступа к API

## 🚀 Развертывание

### Docker

```bash
# Сборка образов
docker-compose build

# Запуск всех сервисов
docker-compose up -d
```

### Production

- **Nginx** → reverse proxy и статические файлы
- **Gunicorn** → WSGI сервер для FastAPI
- **Supervisor** → управление процессами
- **Monitoring** → Prometheus + Grafana

## 📈 Рекомендации по оптимизации

### Нарезка текстов

- **Размер чанка:** 1000-1500 токенов
- **Перекрытие:** 10-20% от размера чанка
- **Семантическая нарезка:** по абзацам/главам
- **Адаптивная нарезка:** в зависимости от типа документа

### Выбор векторной БД

- **Chroma** → для начала (простота, локальная установка)
- **Qdrant** → для продакшена (производительность, масштабируемость)
- **Pinecone** → для облачного решения (managed service)

### Работа с большими файлами

- **Стриминг** → обработка по частям
- **Ограничение RAM** → батчевая обработка
- **Предварительная обработка** → сжатие, фильтрация
- **Асинхронная загрузка** → неблокирующие операции

## 🤝 Участие в разработке

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 🆘 Поддержка

- **Issues:** [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-repo/discussions)
- **Documentation:** [Wiki](https://github.com/your-repo/wiki)

# DocMind

Интеллектуальная система обработки документов с использованием RAG (Retrieval-Augmented Generation) и векторного поиска.

## 🚀 Возможности

- **Загрузка документов**: Поддержка PDF, DOCX, TXT, MD
- **Извлечение текста**: Автоматическое извлечение текста из различных форматов
- **Векторное хранилище**: Интеграция с Qdrant Cloud для семантического поиска
- **База данных**: PostgreSQL для хранения метаданных документов
- **REST API**: FastAPI для взаимодействия с системой

## 🏗️ Архитектура

```
docmind/
├── api/                    # API слой
│   ├── dependencies.py     # Зависимости API
│   ├── exceptions.py       # Обработка ошибок
│   ├── middleware.py       # Middleware
│   └── routers/           # API роутеры
├── core/                   # Бизнес-логика
│   ├── exceptions.py       # Бизнес-исключения
│   ├── repositories/       # Репозитории БД
│   ├── text_processing/    # Обработка текста
│   └── vector_store.py     # Векторное хранилище
├── models/                 # Модели данных
│   ├── database.py         # SQLAlchemy модели
│   └── schemas.py          # Pydantic схемы
├── config/                 # Конфигурация
│   └── settings.py         # Настройки приложения
└── scripts/               # Скрипты
    └── init_db.py         # Инициализация БД
```

## 📋 Требования

- Python 3.8+
- PostgreSQL 12+
- Redis (опционально)

## 🛠️ Установка

1. **Клонируйте репозиторий**:
```bash
git clone <repository-url>
cd DocMind
```

2. **Установите зависимости**:
```bash
pip install -r requirements.txt
```

3. **Настройте переменные окружения**:
```bash
cp env.example .env
```

Отредактируйте `.env` файл:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/docmind

# Qdrant Cloud
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-api-key

# OpenAI
OPENAI_API_KEY=your-openai-key

# Security
SECRET_KEY=your-secret-key
```

4. **Инициализируйте базу данных**:
```bash
python -m docmind.scripts.init_db
```

5. **Запустите приложение**:
```bash
python main.py
```

## 🗄️ Настройка PostgreSQL

### Локальная установка

1. **Установите PostgreSQL**:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql

# Windows
# Скачайте с https://www.postgresql.org/download/windows/
```

2. **Создайте базу данных**:
```bash
sudo -u postgres psql
CREATE DATABASE docmind;
CREATE USER docmind_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE docmind TO docmind_user;
\q
```

3. **Обновите DATABASE_URL**:
```env
DATABASE_URL=postgresql://docmind_user:your_password@localhost:5432/docmind
```

### Docker (альтернатива)

```bash
docker run --name postgres-docmind \
  -e POSTGRES_DB=docmind \
  -e POSTGRES_USER=docmind_user \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  -d postgres:13
```

## 📚 API Endpoints

### Документы

- `POST /documents/upload` - Загрузка документа
- `GET /documents/` - Список документов
- `GET /documents/{id}` - Получить документ
- `GET /documents/{id}/text` - Получить текст документа
- `DELETE /documents/{id}` - Удалить документ
- `PUT /documents/{id}/status` - Обновить статус

### Статус

- `GET /health` - Проверка здоровья
- `GET /api/v1/status` - Статус API
- `GET /api/v1/qdrant/status` - Статус Qdrant

## 🔧 Разработка

### Структура базы данных

```sql
CREATE TABLE documents (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'uploaded',
    content_preview TEXT,
    file_path VARCHAR(500) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    chunk_count INTEGER DEFAULT 0,
    vectorized BOOLEAN DEFAULT FALSE
);
```

### Миграции

Для изменения схемы базы данных:

1. Создайте новую миграцию
2. Обновите модель в `models/database.py`
3. Запустите миграцию

### Тестирование

```bash
# Запуск тестов
pytest

# Покрытие кода
pytest --cov=docmind
```

## 🚀 Масштабирование

### Горизонтальное масштабирование

- **База данных**: Используйте PostgreSQL с репликацией
- **Файловое хранилище**: Перейдите на S3 или MinIO
- **Векторное хранилище**: Qdrant Cloud поддерживает кластеризацию
- **API**: Используйте балансировщик нагрузки

### Мониторинг

- Логирование через структурированные логи
- Метрики производительности
- Алерты при ошибках

## 📄 Лицензия

MIT License

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch
3. Commit изменения
4. Push в branch
5. Создайте Pull Request 