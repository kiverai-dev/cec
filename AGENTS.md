# AGENTS.md

## Проект: MVP "ТестАналитики"

Система оценки качества здравоохранения в лечебно-профилактическом учреждении.

---

## Архитектура

### Воркфлоу
1. Пользователь загружает PDF файл или архив (ZIP/RAR)
2. Извлечение текста из PDF (PyMuPDF)
3. LLM преобразует данные в JSON
4. LLM анализирует JSON
5. Пользователь получает аналитику

### Стек технологий
- **Frontend:** Streamlit
- **Backend:** Python 3.11
- **Database:** SQLite + SQLAlchemy
- **LLM:** OpenAI-совместимый API (OpenAI, llama.cpp, Ollama, vLLM и др.)
- **Deployment:** Docker Compose

### Роли пользователей
- `admin` — полный доступ, управление пользователями и настройками
- `analyst` — загрузка и анализ файлов
- `viewer` — только просмотр результатов

---

## Структура проекта

```
/mnt/projects/cec/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # Streamlit entrypoint + роутинг
│   ├── config.py                  # Конфигурация из .env
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py              # User, Upload, Analysis, Setting
│   │   ├── session.py             # SQLite engine/session
│   │   └── crud.py                # CRUD операции
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── pages.py               # UI: login, register, logout
│   │   └── roles.py               # @require_role декоратор
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── pdf_extractor.py       # PyMuPDF извлечение текста
│   │   ├── llm_client.py          # HTTP клиент llama.cpp
│   │   ├── analyzer.py            # Промпты + анализ
│   │   └── schemas.py             # Pydantic схемы
│   │
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── users.py               # UI: CRUD пользователей
│   │   └── settings.py            # UI: настройка llama.cpp
│   │
│   ├── ui/                        # НЕ называть "pages" — Streamlit MPA автонавигация
│   │   ├── __init__.py
│   │   ├── dashboard.py           # Главная страница
│   │   ├── upload.py              # Загрузка PDF/архива
│   │   ├── history.py             # История загрузок
│   │   └── analysis.py            # Результат анализа
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── archive.py             # Распаковка ZIP/RAR
│   │   └── validators.py          # Валидация файлов
│   │
│   └── entrypoint.sh              # Инициализация БД → запуск
│
├── tests/
│   ├── __init__.py
│   ├── test_pdf_extractor.py
│   └── test_llm_client.py
│
└── data/                          # Docker volume (gitignored)
    ├── uploads/
    ├── results/
    ├── db/
    └── models/
```

---

## База данных (SQLite)

### Таблица: users
| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER PK | Автоинкремент |
| username | VARCHAR(50) UNIQUE | Логин |
| email | VARCHAR(255) UNIQUE NULLABLE | Email (для будущей миграции) |
| password_hash | VARCHAR(255) | bcrypt хеш |
| role | VARCHAR(20) | admin / analyst / viewer |
| is_active | BOOLEAN | Активен ли пользователь |
| created_at | DATETIME | Дата создания |

### Таблица: uploads
| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER PK | Автоинкремент |
| user_id | INTEGER FK | Связь с users.id |
| filename | VARCHAR(255) | Имя файла |
| file_path | VARCHAR(500) | Путь к файлу на диске |
| status | VARCHAR(20) | pending / processing / done / error |
| error_message | TEXT | Текст ошибки (если есть) |
| created_at | DATETIME | Дата загрузки |

### Таблица: analyses
| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER PK | Автоинкремент |
| upload_id | INTEGER FK | Связь с uploads.id |
| extracted_json | TEXT | Извлечённый JSON |
| result_text | TEXT | Результат анализа |
| created_at | DATETIME | Дата анализа |

### Таблица: settings
| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER PK | Автоинкремент |
| key | VARCHAR(100) UNIQUE | Ключ настройки |
| value | TEXT | Значение |
| updated_at | DATETIME | Дата обновления |

---

## CRUD функции

### Users
- `create_user(username: str, password: str, role: str) -> User`
- `authenticate_user(username: str, password: str) -> User | None`
- `get_user_by_id(user_id: int) -> User | None`
- `get_user_by_username(username: str) -> User | None`
- `get_all_users() -> list[User]`
- `update_user(user_id: int, **kwargs) -> User`
- `delete_user(user_id: int) -> bool`
- `set_user_active(user_id: int, is_active: bool) -> User`

### Uploads
- `create_upload(user_id: int, filename: str, file_path: str) -> Upload`
- `get_upload_by_id(upload_id: int) -> Upload | None`
- `get_uploads_by_user(user_id: int, limit: int = 50) -> list[Upload]`
- `get_all_uploads(limit: int = 100) -> list[Upload]`
- `update_upload_status(upload_id: int, status: str, error_message: str = None) -> Upload`
- `delete_upload(upload_id: int) -> bool` — каскадно удаляет связанный Analysis

### Analyses
- `create_analysis(upload_id: int, extracted_json: str, result_text: str) -> Analysis`
- `get_analysis_by_upload(upload_id: int) -> Analysis | None`
- `get_analysis_by_id(analysis_id: int) -> Analysis | None`

### Settings
- `get_setting(key: str, default: str = None) -> str | None`
- `set_setting(key: str, value: str) -> Setting`
- `get_all_settings() -> dict`

---

## Аутентификация

### Механизм
- Хранение авторизованного пользователя в `st.session_state["user"]`
- bcrypt для хеширования паролей
- Редирект на `/login` если `st.session_state["user"]` is None

### Первый вход
- Если таблица `users` пуста → показать форму создания первого админа
- Страница `/setup` доступна только если БД пуста

### Декоратор ролей
```python
def require_role(*roles: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = st.session_state.get("user")
            if not user:
                st.error("Требуется авторизация")
                st.stop()
            if user.role not in roles:
                st.error("Недостаточно прав")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## PDF обработка

### Извлечение текста (PyMuPDF)
```python
import fitz  # PyMuPDF

def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text
```

### Распаковка архивов
- **ZIP:** стандартный `zipfile`
- **RAR:** библиотека `rarfile` (требует установленный `unrar` в Docker)

### Валидация файлов
- Разрешённые расширения: `.pdf`, `.zip`, `.rar`
- Максимальный размер: 50 MB (настраивается через env)
- Для архивов: проверка что внутри только PDF файлы

---

## LLM интеграция

### HTTP клиент
- Endpoint: `{API_URL}/v1/chat/completions`
- Формат: OpenAI-совместимый API
- Поддержка авторизации через Bearer token
- Обработка таймаутов и ошибок

### Поддерживаемые API
- OpenAI API (gpt-4, gpt-3.5-turbo)
- Локальные серверы (llama.cpp, Ollama, vLLM)
- OpenAI-совместимые API (Azure OpenAI, Anthropic через прокси)

### Пример запроса
```python
{
    "model": "gpt-4",
    "messages": [
        {"role": "system", "content": "Ты — медицинский аналитик..."},
        {"role": "user", "content": pdf_text}
    ],
    "temperature": 0.7,
    "max_tokens": 2048
}
```

### Настройки (таблица settings)
| Ключ | Значение по умолчанию | Описание |
|------|----------------------|----------|
| `api_url` | `http://localhost:8080` | URL API сервера |
| `model_name` | `local-model` | Имя модели |
| `api_key` | `""` | API ключ (опционально) |
| `temperature` | `0.7` | Температура генерации |
| `max_tokens` | `2048` | Максимальное количество токенов |

---

## Промпты

### Промпт 1: PDF → JSON
```
Ты — медицинский аналитик. Извлеки структурированные данные из текста медицинской документации.

Текст документа:
{pdf_text}

Верни результат строго в формате JSON:
{
  "patient_info": {
    "name": "ФИО пациента",
    "birth_date": "дата рождения",
    "gender": "пол"
  },
  "diagnoses": [
    {
      "code": "код МКБ",
      "name": "название диагноза",
      "date": "дата постановки"
    }
  ],
  "treatments": [
    {
      "type": "тип лечения",
      "description": "описание",
      "date": "дата"
    }
  ],
  "metadata": {
    "document_type": "тип документа",
    "institution": "название учреждения",
    "doctor": "ФИО врача",
    "date": "дата документа"
  }
}

Если какие-то данные отсутствуют в тексте, оставь поле null. Ответ должен содержать только валидный JSON без дополнительного текста.
```

### Промпт 2: JSON → Аналитика
```
Ты — эксперт по оценке качества медицинской документации. Проанализируй извлечённые данные и подготовь отчёт.

Данные:
{json_data}

Проведи анализ по следующим критериям:

1. **Полнота заполнения**
   - Оцените, насколько полно заполнены обязательные поля
   - Укажите отсутствующие данные

2. **Соответствие стандартам**
   - Проверьте корректность оформления
   - Соответствие формату МКБ для диагнозов

3. **Выявленные проблемы**
   - Противоречия в данных
   - Отсутствие необходимой информации
   - Ошибки оформления

4. **Рекомендации**
   - Что необходимо исправить
   - Что требует уточнения

5. **Общая оценка качества**
   - Числовая оценка от 1 до 10
   - Краткое обоснование

Ответ оформи на русском языке в структурированном виде с использованием Markdown.
```

---

## Streamlit UI

### Роутинг
Роутинг через `st.query_params` и условный рендеринг в `main.py`:

```python
def main():
    init_db()
    
    if not users_exist():
        show_setup_page()
        return
    
    if "user" not in st.session_state:
        show_login_page()
        return
    
    page = st.query_params.get("page", "dashboard")
    
    if page == "dashboard":
        show_dashboard()
    elif page == "upload":
        show_upload_page()
    elif page == "history":
        show_history_page()
    elif page == "analysis":
        show_analysis_page()
    elif page == "admin_users":
        show_admin_users()
    elif page == "admin_settings":
        show_admin_settings()
```

### Страницы

| Страница | Query param | Роли | Описание |
|----------|-------------|------|----------|
| Setup | — | все (если БД пуста) | Создание первого админа |
| Login | — | все | Форма входа |
| Dashboard | `?page=dashboard` | все | Главная страница, статистика |
| Upload | `?page=upload` | analyst, admin | Загрузка PDF/архива |
| History | `?page=history` | все | История загрузок с фильтрами |
| Analysis | `?page=analysis&id=` | все | Результат анализа |
| Admin Users | `?page=admin_users` | admin | Управление пользователями |
| Admin Settings | `?page=admin_settings` | admin | Настройка LLM API |

---

## Docker

### docker-compose.yml
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=sqlite:///data/db/app.db
      - API_URL=${API_URL:-http://localhost:8080}
      - APP_NAME=ТестАналитики
      - SECRET_KEY=${SECRET_KEY:-change-me-in-production}
      - MAX_FILE_SIZE_MB=50
    restart: unless-stopped

  # Раскомментируйте для использования локального llama.cpp
  # llamacpp:
  #   image: ghcr.io/ggerganov/llama.cpp:server
  #   ports:
  #     - "8080:8080"
  #   volumes:
  #     - ./data/models:/models
  #   command: >
  #     --model /models/model.gguf
  #     --host 0.0.0.0
  #     --port 8080
  #     --ctx-size 4096
  #     --threads 4
  #   restart: unless-stopped
```

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка unrar для работы с RAR архивами
RUN apt-get update && apt-get install -y unrar-free && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY app/ ./app/

# Создание директорий для данных
RUN mkdir -p /app/data/uploads /app/data/results /app/data/db /app/data/models

# Entrypoint
COPY app/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8501

ENTRYPOINT ["/entrypoint.sh"]
```

### entrypoint.sh
```bash
#!/bin/bash
set -e

# Инициализация базы данных
python -c "from app.database.session import init_db; init_db()"

# Запуск Streamlit
streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0
```

---

## Зависимости (requirements.txt)

```txt
streamlit>=1.32.0
sqlalchemy>=2.0.0
pymupdf>=1.24.0
httpx>=0.27.0
pydantic>=2.6.0
bcrypt>=4.1.0
python-multipart>=0.0.9
rarfile>=4.1
```

---

## Переменные окружения (.env.example)

```env
# База данных
DATABASE_URL=sqlite:///data/db/app.db

# LLM API
API_URL=http://localhost:8080

# Приложение
APP_NAME=ТестАналитики
SECRET_KEY=your-secret-key-change-in-production
MAX_FILE_SIZE_MB=50
```

---

## .gitignore

```
# Data
data/
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.venv/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

---

## Порядок реализации

1. **Инфраструктура**
   - `docker-compose.yml`
   - `Dockerfile`
   - `requirements.txt`
   - `.env.example`
   - `.gitignore`

2. **База данных**
   - `app/database/models.py`
   - `app/database/session.py`
   - `app/database/crud.py`

3. **Конфигурация**
   - `app/config.py`
   - `app/__init__.py`

4. **Аутентификация**
   - `app/auth/roles.py`
   - `app/auth/pages.py`

5. **PDF обработка**
   - `app/utils/validators.py`
   - `app/utils/archive.py`
   - `app/core/pdf_extractor.py`

6. **LLM интеграция**
   - `app/core/schemas.py`
   - `app/core/llm_client.py`

7. **Аналитика**
   - `app/core/analyzer.py`

8. **UI страницы**
   - `app/ui/dashboard.py`
   - `app/ui/upload.py`
   - `app/ui/history.py`
   - `app/ui/analysis.py`

9. **Админ-панель**
   - `app/admin/users.py`
   - `app/admin/settings.py`

10. **Главный файл**
    - `app/main.py`

11. **Entrypoint**
    - `app/entrypoint.sh`

12. **Документация**
    - `README.md`

13. **Тесты**
    - `tests/test_pdf_extractor.py`
    - `tests/test_llm_client.py`

---

## Метрики аналитики (базовые)

На MVP этапе реализуем базовые метрики:

1. **Полнота заполнения** — процент заполненных обязательных полей
2. **Соответствие стандартам** — проверка форматов (МКБ, даты)
3. **Проблемы** — выявление противоречий и пропусков
4. **Рекомендации** — предложения по улучшению
5. **Общая оценка** — числовой балл от 1 до 10

---

## Примечания

- Интерфейс на русском языке
- Название приложения: **ТестАналитики**
- База данных создаётся пустой, первый админ регистрируется через форму `/setup`
- Поле `email` в таблице `users` добавлено как `nullable=True` для будущей миграции аутентификации по email
