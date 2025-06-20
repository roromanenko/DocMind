# Qdrant Cloud Setup Guide

## 🚀 Настройка Qdrant Cloud для DocMind

### Шаг 1: Регистрация в Qdrant Cloud

1. **Перейдите на [cloud.qdrant.io](https://cloud.qdrant.io)**
2. **Зарегистрируйтесь** с помощью GitHub или email
3. **Подтвердите email** (если регистрировались через email)

### Шаг 2: Создание кластера

1. **Нажмите "Create Cluster"**
2. **Выберите план:**
   - **Free Tier** (для тестирования) - 1GB, 1 collection
   - **Starter** ($25/месяц) - 10GB, 5 collections
   - **Growth** ($100/месяц) - 100GB, 20 collections

3. **Выберите регион** (ближайший к вашим пользователям)
4. **Введите название кластера** (например: `docmind-production`)
5. **Нажмите "Create"**

### Шаг 3: Получение учетных данных

После создания кластера вы получите:

1. **URL кластера** - `https://your-cluster.cloud.qdrant.io`
2. **API ключ** - длинная строка символов

### Шаг 4: Настройка переменных окружения

Обновите файл `.env`:

```env
# Qdrant Cloud Configuration
QDRANT_URL=https://your-cluster.cloud.qdrant.io
QDRANT_API_KEY=your-qdrant-cloud-api-key
QDRANT_COLLECTION_NAME=docmind_chunks
QDRANT_VECTOR_SIZE=384
```

### Шаг 5: Тестирование подключения

Запустите приложение и проверьте статус:

```bash
# Запуск приложения
poetry run python main.py

# Проверка статуса Qdrant Cloud
curl http://localhost:8000/api/v1/qdrant/status

# Получение информации о кластере
curl http://localhost:8000/api/v1/qdrant/cluster
```

### Шаг 6: Веб-интерфейс Qdrant Cloud

1. **Перейдите в Dashboard** вашего кластера
2. **Откройте веб-интерфейс** - кнопка "Open Dashboard"
3. **Проверьте коллекцию** `docmind_chunks`

## 🔧 Конфигурация для разных окружений

### Development
```env
QDRANT_URL=https://dev-cluster.cloud.qdrant.io
QDRANT_API_KEY=dev-api-key
QDRANT_COLLECTION_NAME=docmind_dev
```

### Staging
```env
QDRANT_URL=https://staging-cluster.cloud.qdrant.io
QDRANT_API_KEY=staging-api-key
QDRANT_COLLECTION_NAME=docmind_staging
```

### Production
```env
QDRANT_URL=https://prod-cluster.cloud.qdrant.io
QDRANT_API_KEY=prod-api-key
QDRANT_COLLECTION_NAME=docmind_production
```

## 📊 Мониторинг и метрики

### В Qdrant Cloud Dashboard:
- **Использование памяти**
- **Количество точек**
- **Количество запросов**
- **Время ответа**

### В нашем приложении:
```bash
# Статус коллекции
GET /api/v1/qdrant/status

# Информация о кластере
GET /api/v1/qdrant/cluster
```

## 🔒 Безопасность

### API ключи:
- **Храните в секретах** (не в коде)
- **Используйте разные ключи** для разных окружений
- **Регулярно ротируйте** ключи

### Сетевая безопасность:
- **HTTPS** - все соединения шифруются
- **API ключи** - аутентификация всех запросов
- **IP фильтрация** - можно настроить в Enterprise плане

## 💰 Стоимость и лимиты

### Free Tier:
- **1GB** хранилища
- **1 коллекция**
- **1000 запросов/день**
- **Подходит для тестирования**

### Starter ($25/месяц):
- **10GB** хранилища
- **5 коллекций**
- **100,000 запросов/день**
- **Подходит для MVP**

### Growth ($100/месяц):
- **100GB** хранилища
- **20 коллекций**
- **1,000,000 запросов/день**
- **Подходит для продакшена**

## 🚨 Troubleshooting

### Ошибка подключения:
```json
{
  "status": "error",
  "error": "Connection failed",
  "message": "Qdrant Cloud service not available"
}
```

**Решение:**
1. Проверьте URL кластера
2. Проверьте API ключ
3. Проверьте интернет-соединение
4. Проверьте статус Qdrant Cloud

### Ошибка аутентификации:
```json
{
  "status": "error",
  "error": "Unauthorized",
  "message": "Invalid API key"
}
```

**Решение:**
1. Проверьте правильность API ключа
2. Убедитесь, что ключ активен
3. Проверьте права доступа

## 📈 Масштабирование

### Автоматическое масштабирование:
- **Qdrant Cloud** автоматически масштабируется
- **Нет необходимости** в ручной настройке
- **Платите только** за используемые ресурсы

### Ручное масштабирование:
- **Увеличьте план** в Dashboard
- **Создайте новые кластеры** для разных регионов
- **Используйте репликацию** для высокой доступности

## 🎯 Лучшие практики

1. **Используйте разные коллекции** для разных типов данных
2. **Настройте фильтры** для оптимизации поиска
3. **Мониторьте использование** ресурсов
4. **Регулярно очищайте** неиспользуемые данные
5. **Тестируйте производительность** с реальными данными 