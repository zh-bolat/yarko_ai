"""
Rate limiting для защиты API от злоупотреблений.
Использует slowapi (на базе limits).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

# Rate limiter по IP-адресу
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_GLOBAL_PER_MINUTE}/minute"],
)
