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