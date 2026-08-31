"""
FastAPI приложение — основная точка входа.

Роуты:
- GET  /             — веб-интерфейс
- POST /api/analyze  — разбор одного сообщения
- POST /api/batch    — разбор нескольких сообщений
- POST /api/auth     — авторизация по паролю
- POST /api/telegram — webhook для Telegram-бота
- GET  /api/health   — healthcheck
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    BatchAnalyzeRequest,
    BatchAnalyzeResponse,
    AuthRequest,
    AuthResponse,
    HealthResponse,
    ErrorResponse,
)
from app.gemini_client import gemini_client
from app.auth import verify_password, create_session_token, verify_token
from app.rate_limiter import limiter

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Путь к статическим файлам
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

# Ссылка на Telegram bot app (заполняется при старте)
_telegram_app = None


# ──────────────────────────────────────────────
# Lifecycle
# ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация и завершение приложения."""
    global _telegram_app

    logger.info("🚀 Starting Yarko AI...")

    # Инициализируем Telegram-бота (если токен задан)
    if settings.TELEGRAM_BOT_TOKEN:
        try:
            from app.telegram_bot import init_telegram_bot
            _telegram_app = await init_telegram_bot()
        except Exception as e:
            logger.warning(f"Telegram bot init failed: {e}")
    else:
        logger.info("Telegram bot disabled (no token)")

    logger.info("✅ Yarko AI is ready")
    logger.info(f"   Model: {settings.GEMINI_MODEL}")
    logger.info(f"   Auth: {'enabled' if settings.APP_PASSWORD else 'disabled'}")
    logger.info(f"   Rate limit: {settings.RATE_LIMIT_PER_MINUTE}/min per IP")

    yield

    logger.info("👋 Shutting down Yarko AI...")


# ──────────────────────────────────────────────
# Приложение
# ──────────────────────────────────────────────

app = FastAPI(
    title="Яркотревел AI",
    description="AI-автоматизатор разбора сообщений туристов",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _check_auth(request: Request) -> bool:
    """Проверяет авторизацию для API-запросов."""
    if not settings.APP_PASSWORD:
        return True

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    return verify_token(token)


def _sanitize_input(text: str) -> str:
    """Базовая санитизация входного текста."""
    # Убираем нулевые байты и control characters (кроме \n, \t)
    cleaned = "".join(
        ch for ch in text
        if ch == "\n" or ch == "\t" or (ord(ch) >= 32)
    )
    return cleaned.strip()


# ──────────────────────────────────────────────
# Роуты
# ──────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    """Главная страница — веб-интерфейс."""
    html_path = STATIC_DIR / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.post("/api/auth", response_model=AuthResponse)
async def auth(body: AuthRequest):
    """Авторизация по паролю. Возвращает session-токен."""
    if verify_password(body.password):
        token = create_session_token()
        return AuthResponse(
            success=True,
            message=token,
        )
    raise HTTPException(status_code=401, detail="Неверный пароль")


@app.post(
    "/api/analyze",
    response_model=AnalyzeResponse,
    responses={401: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def analyze(request: Request, body: AnalyzeRequest):
    """Разбор одного сообщения туриста."""
    if not _check_auth(request):
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    # Санитизация
    clean_message = _sanitize_input(body.message)
    if not clean_message:
        raise HTTPException(status_code=422, detail="Сообщение пустое после очистки")

    try:
        result = await gemini_client.analyze_message(clean_message)
        return result
    except RuntimeError as e:
        # GEMINI_API_KEY не задан
        logger.error(f"Config error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Analyze error: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Ошибка AI-сервиса. Попробуйте через несколько секунд.",
        )


@app.post(
    "/api/batch",
    response_model=BatchAnalyzeResponse,
    responses={401: {"model": ErrorResponse}},
)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def batch_analyze(request: Request, body: BatchAnalyzeRequest):
    """Разбор нескольких сообщений. Максимум 20 штук."""
    if not _check_auth(request):
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    async def _process_one(message: str) -> AnalyzeResponse:
        clean_message = _sanitize_input(message)
        if not clean_message:
            return AnalyzeResponse(
                intent="общий_вопрос",
                confidence=0.0,
                notes="Пустое сообщение",
            )
        try:
            return await gemini_client.analyze_message(clean_message)
        except Exception as e:
            logger.error(f"Batch analyze error for message: {e}")
            return AnalyzeResponse(
                intent="общий_вопрос",
                confidence=0.0,
                draft_reply=None,
                notes=f"Ошибка обработки: {str(e)}",
            )

    tasks = [_process_one(msg) for msg in body.messages[:settings.MAX_BATCH_SIZE]]
    results = await asyncio.gather(*tasks)
    total_cost = sum(r.cost_rub for r in results)

    return BatchAnalyzeResponse(
        results=results,
        total_cost_rub=round(total_cost, 4),
    )


@app.post("/api/telegram")
async def telegram_webhook(request: Request):
    """Webhook для Telegram-бота."""
    if _telegram_app is None:
        raise HTTPException(status_code=503, detail="Telegram bot not configured")

    try:
        data = await request.json()
        from telegram import Update as TGUpdate
        update = TGUpdate.de_json(data=data, bot=_telegram_app.bot)
        await _telegram_app.process_update(update)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}", exc_info=True)
        return {"ok": False, "error": str(e)}


@app.get("/api/health", response_model=HealthResponse)
async def health():
    """Healthcheck эндпоинт."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        model=settings.GEMINI_MODEL,
    )


# ──────────────────────────────────────────────
# Статические файлы (монтируем после роутов)
# ──────────────────────────────────────────────

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ──────────────────────────────────────────────
# Запуск
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
