import os

APP_NAME = os.getenv("APP_NAME", "ТестАналитики")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/db/app.db")
API_URL = os.getenv("API_URL", "http://localhost:8080")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))

ALLOWED_EXTENSIONS = {".pdf", ".zip", ".rar"}
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

DEFAULT_SETTINGS = {
    "api_url": API_URL,
    "model_name": "local-model",
    "api_key": "",
    "temperature": "0.7",
    "max_tokens": "2048",
}
