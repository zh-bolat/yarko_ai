"""
Конфигурация приложения. Загрузка переменных окружения.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env файл
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    """Настройки приложения из переменных окружения."""

    # Google Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    GEMINI_FALLBACK_MODEL: str = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite")

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_WEBHOOK_URL: str = os.getenv("TELEGRAM_WEBHOOK_URL", "")

    # Авторизация
    APP_PASSWORD: str = os.getenv("APP_PASSWORD", "yarko2026")

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    RATE_LIMIT_GLOBAL_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_GLOBAL_PER_MINUTE", "100"))

    # Контекст-менеджер (склейка сообщений Telegram)
    MESSAGE_BUFFER_TIMEOUT_SEC: int = int(os.getenv("MESSAGE_BUFFER_TIMEOUT_SEC", "0"))
    MESSAGE_BUFFER_MAX_MESSAGES: int = int(os.getenv("MESSAGE_BUFFER_MAX_MESSAGES", "10"))
    MESSAGE_BUFFER_TTL_SEC: int = int(os.getenv("MESSAGE_BUFFER_TTL_SEC", "3600"))

    # Общее
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # Лимиты
    MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "5000"))
    MAX_BATCH_SIZE: int = int(os.getenv("MAX_BATCH_SIZE", "20"))


settings = Settings()
