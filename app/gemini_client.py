"""
Обёртка для Google Gemini API (google-genai SDK).
Отправляет сообщение туриста на разбор и возвращает структурированный JSON.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from google import genai
from google.genai import types

from app.config import settings
from app.models import AnalyzeResponse, TokenUsage, GeminiAnalyzeResponse
from app.prompt import SYSTEM_PROMPT, TELEGRAM_DIALOG_PROMPT

logger = logging.getLogger(__name__)

# Стоимость Gemini 3.5 Flash Lite (USD за 1M токенов)
PRICE_INPUT_PER_M = 0.075
PRICE_OUTPUT_PER_M = 0.30
USD_TO_RUB = 90.0


class GeminiClient:
    """Клиент для взаимодействия с Google Gemini API."""

    def __init__(self) -> None:
        self._configured = False
        self._client = None

    def _ensure_configured(self) -> None:
        """Ленивая инициализация — настраивает клиент при первом вызове."""
        if self._configured:
            return

        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY не задан. Добавьте его в .env файл."
            )

        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._configured = True
        logger.info(f"Gemini configured: model={settings.GEMINI_MODEL}")

    async def analyze_message(self, message: str) -> AnalyzeResponse:
        """
        Разбирает одно сообщение туриста.

        Args:
            message: Текст сообщения от туриста.

        Returns:
            AnalyzeResponse с результатом разбора.

        Raises:
            RuntimeError: Если GEMINI_API_KEY не задан.
            Exception: При ошибке API (после retry и fallback).
        """
        self._ensure_configured()

        # Обрезаем слишком длинные сообщения
        truncated = message[:settings.MAX_MESSAGE_LENGTH]

        response = await self._call_gemini(truncated)

        # Парсим JSON-ответ
        result = self._parse_response(response)

        return result

    async def generate_dialog_reply(
        self,
        message: str,
        context: list[dict],
    ) -> str:
        """
        Генерирует ответ для Telegram-диалога с учётом контекста.

        Args:
            message: Текущее сообщение туриста.
            context: История предыдущих сообщений.

        Returns:
            Текст ответа бота.
        """
        self._ensure_configured()

        # Форматируем контекст
        context_str = self._format_context(context)

        prompt = f"{TELEGRAM_DIALOG_PROMPT.format(context=context_str, message=message)}"

        # Для диалога не нужен structured output
        config = types.GenerateContentConfig(
            temperature=0.7,
        )

        # Используем async client
        response = await self._client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=config,
        )
        return response.text

    async def _call_gemini(
        self,
        message: str,
        use_fallback: bool = False,
    ):
        """
        Вызов Gemini API с retry и exponential backoff + fallback.

        Args:
            message: Текст для разбора.
            use_fallback: Использовать fallback-модель.

        Returns:
            Ответ от Gemini API.
        """
        model_name = settings.GEMINI_FALLBACK_MODEL if use_fallback else settings.GEMINI_MODEL
        max_retries = 3

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GeminiAnalyzeResponse,
            system_instruction=SYSTEM_PROMPT,
            temperature=0.3,
        )

        for attempt in range(max_retries):
            try:
                # В новом SDK асинхронные вызовы делаются через client.aio.models
                response = await self._client.aio.models.generate_content(
                    model=model_name,
                    contents=message,
                    config=config,
                )
                return response
            except Exception as e:
                wait_time = (2 ** attempt) * 0.5  # 0.5s, 1s, 2s
                logger.warning(
                    f"Gemini API attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying in {wait_time}s..."
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    # Все попытки исчерпаны
                    if not use_fallback:
                        logger.info("Switching to fallback model...")
                        return await self._call_gemini(message, use_fallback=True)
                    raise

    def _parse_response(self, response) -> AnalyzeResponse:
        """
        Парсит ответ Gemini в AnalyzeResponse.

        Args:
            response: Raw-ответ от Gemini API (новый SDK возвращает structured data).

        Returns:
            Валидированный AnalyzeResponse.
        """
        # Новый SDK позволяет получить объект напрямую, если был передан schema
        try:
            # response.text это JSON string. Если SDK сам распарсил, то можно достать.
            # По документации, SDK может распарсить в Pydantic автоматически 
            # через `parsed = GeminiAnalyzeResponse.model_validate_json(response.text)`
            parsed = GeminiAnalyzeResponse.model_validate_json(response.text)
            data = parsed.model_dump()
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            # Возвращаем fallback-ответ
            return AnalyzeResponse(
                intent="общий_вопрос",
                confidence=0.1,
                draft_reply="Извините, не удалось обработать сообщение. Попробуйте ещё раз.",
                notes="Ошибка парсинга ответа AI",
            )

        # Рассчитываем стоимость
        tokens_in = 0
        tokens_out = 0

        usage = getattr(response, "usage_metadata", None)
        if usage:
            tokens_in = getattr(usage, "prompt_token_count", 0) or 0
            tokens_out = getattr(usage, "candidates_token_count", 0) or 0

        cost_usd = (
            (tokens_in / 1_000_000) * PRICE_INPUT_PER_M
            + (tokens_out / 1_000_000) * PRICE_OUTPUT_PER_M
        )
        cost_rub = round(cost_usd * USD_TO_RUB, 4)

        data["cost_rub"] = cost_rub
        data["tokens_used"] = {"input": tokens_in, "output": tokens_out}

        # Нормализация
        valid_intents = {"подбор_тура", "проблема_срочно", "общий_вопрос", "спам"}
        if data.get("intent") not in valid_intents:
            data["intent"] = "общий_вопрос"
            data.setdefault("notes", "")
            if data["notes"]:
                data["notes"] += ". "
            data["notes"] = (data.get("notes") or "") + f"Оригинальный intent: {data.get('intent')}"

        try:
            return AnalyzeResponse(**data)
        except Exception as e:
            logger.error(f"Failed to validate response: {e}. Raw data: {data}")
            return AnalyzeResponse(
                intent=data.get("intent", "общий_вопрос"),
                confidence=float(data.get("confidence", 0.5)),
                people_count=data.get("people_count"),
                has_children=bool(data.get("has_children", False)),
                budget_max=data.get("budget_max"),
                is_urgent=bool(data.get("is_urgent", False)),
                draft_reply=data.get("draft_reply"),
                notes=f"Частичный разбор (ошибка валидации: {e})",
                cost_rub=cost_rub,
                tokens_used=TokenUsage(input=tokens_in, output=tokens_out),
            )

    @staticmethod
    def _format_context(context: list[dict]) -> str:
        """Форматирует историю диалога для промпта."""
        if not context:
            return "(нет предыдущих сообщений)"

        lines = []
        for msg in context[-10:]:  # Последние 10 сообщений
            role = "Турист" if msg.get("role") == "user" else "Бот"
            lines.append(f"{role}: {msg.get('text', '')}")

        return "\n".join(lines)


# Синглтон (ленивая инициализация — не падает без ключа)
gemini_client = GeminiClient()
