# ТестАналитики

Система оценки качества здравоохранения в лечебно-профилактическом учреждении.

## Описание

MVP приложение для анализа медицинских документов (PDF) с использованием LLM.

### Воркфлоу
1. Пользователь загружает PDF файл или архив (ZIP/RAR)
2. Извлечение текста из PDF
3. LLM преобразует данные в JSON
4. LLM анализирует JSON
5. Пользователь получает аналитику

## Технологии

- **Frontend:** Streamlit
- **Backend:** Python 3.11
- **Database:** SQLite + SQLAlchemy
- **LLM:** OpenAI-совместимый API (OpenAI, llama.cpp, Ollama, vLLM и др.)
- **Deployment:** Docker Compose

## Быстрый старт

### 1. Настройка окружения

```bash
cp .env.example .env
```

### 2. Запуск

```bash
docker-compose up -d
```

### 3. Доступ

Откройте браузер: http://localhost:8501

### 4. Настройка API

Войдите под администратором и перейдите в **Настройки LLM API**. Укажите:
- **API URL** — адрес вашего API (например, `https://api.openai.com`)
- **Имя модели** — название модели (например, `gpt-4`)
- **API ключ** — ключ авторизации (если требуется)

## Поддерживаемые API

| Провайдер | URL | Пример модели |
|-----------|-----|---------------|
| OpenAI | `https://api.openai.com` | gpt-4, gpt-3.5-turbo |
| llama.cpp | `http://localhost:8080` | local-model |
| Ollama | `http://localhost:11434` | llama3, mistral |
| vLLM | `http://localhost:8000` | ваша модель |
| Azure OpenAI | `https://your-resource.openai.azure.com` | ваша модель |

## Использование локального llama.cpp

Если хотите использовать локальную модель:

1. Раскомментируйте сервис `llamacpp` в `docker-compose.yml`
2. Поместите модель `.gguf` в `data/models/model.gguf`
3. Запустите: `docker-compose up -d`
4. В настройках укажите URL: `http://llamacpp:8080`

## Первый вход

При первом запуске база данных пуста. Система предложит создать учётную запись администратора.

## Роли пользователей

| Роль | Описание |
|------|----------|
| admin | Полный доступ, управление пользователями и настройками |
| analyst | Загрузка и анализ файлов |
| viewer | Только просмотр результатов |

## Структура проекта

```
├── docker-compose.yml      # Конфигурация Docker
├── Dockerfile              # Образ приложения
├── requirements.txt        # Python зависимости
├── .env.example           # Пример переменных окружения
│
├── app/
│   ├── main.py            # Точка входа Streamlit
│   ├── config.py          # Конфигурация
│   ├── database/          # Модели и CRUD
│   ├── auth/              # Аутентификация
│   ├── core/              # Бизнес-логика (PDF, LLM, аналитика)
│   ├── admin/             # Админ-панель
│   ├── ui/                # UI страницы
│   └── utils/             # Утилиты
│
└── data/                  # Данные (volume)
    ├── uploads/           # Загруженные файлы
    ├── results/           # Результаты
    └── db/                # База данных SQLite
```

## Переменные окружения

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| DATABASE_URL | sqlite:///data/db/app.db | Путь к БД |
| API_URL | http://localhost:8080 | URL API по умолчанию |
| APP_NAME | ТестАналитики | Название приложения |
| SECRET_KEY | — | Секретный ключ (измените в продакшене) |
| MAX_FILE_SIZE_MB | 50 | Максимальный размер файла |

## Разработка

### Установка зависимостей

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Локальный запуск

```bash
streamlit run app/main.py
```

### Тесты

```bash
pytest tests/
```

## Лицензия

MIT
