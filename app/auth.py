"""
Простая авторизация по паролю.
Для защиты демо от несанкционированного доступа.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

from app.config import settings

# Генерируем session-токены при валидном пароле
_active_tokens: set[str] = set()


def verify_password(password: str) -> bool:
    """
    Проверяет пароль.
    
    Args:
        password: Введённый пользователем пароль.
        
    Returns:
        True если пароль верный.
    """
    return hmac.compare_digest(password.strip(), settings.APP_PASSWORD)


def create_session_token() -> str:
    """
    Создаёт новый session-токен.
    
    Returns:
        Hex-строка токена.
    """
    token = secrets.token_hex(32)
    _active_tokens.add(token)
    return token


def verify_token(token: str) -> bool:
    """
    Проверяет session-токен.
    
    Args:
        token: Токен из заголовка Authorization.
        
    Returns:
        True если токен валидный.
    """
    if not settings.APP_PASSWORD:
        # Если пароль не задан — пропускаем авторизацию
        return True
    return token in _active_tokens


def revoke_token(token: str) -> None:
    """Отзывает session-токен."""
    _active_tokens.discard(token)
