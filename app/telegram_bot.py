"""
Telegram-бот — AI-агент для диалога с туристами.

Функционал:
- Ведёт диалог, уточняет детали заявки
- Склеивает несколько сообщений подряд (через ContextManager)
- Разбирает сообщение и отправляет красиво отформатированный результат
- Игнорирует спам
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.config import settings
from app.context_manager import context_manager
from app.gemini_client import gemini_client
from app.models import AnalyzeResponse

logger = logging.getLogger(__name__)

# Telegram Application (инициализируется при старте)
bot_app: Optional[Application] = None


async def init_telegram_bot() -> Optional[Application]:
    """
    Инициализирует Telegram-бота.
    
    Returns:
        Application или None если токен не задан.
    """
    global bot_app

    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set, bot disabled")
        return None

    bot_app = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .build()
    )

    # Регистрируем обработчики
    bot_app.add_handler(CommandHandler("start", _handle_start))
    bot_app.add_handler(CommandHandler("help", _handle_help))
    bot_app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_message)
    )

    # Устанавливаем webhook если URL задан
    if settings.TELEGRAM_WEBHOOK_URL:
        await bot_app.bot.set_webhook(
            url=settings.TELEGRAM_WEBHOOK_URL,
            allowed_updates=["message"],
        )
        logger.info(f"Webhook set: {settings.TELEGRAM_WEBHOOK_URL}")

    logger.info("Telegram bot initialized")
    return bot_app


async def _handle_start(update: Update, context) -> None:
    """Обработчик команды /start."""
    await update.message.reply_text(
        "👋 Привет! Я AI-ассистент Яркотревел.\n\n"
        "Напишите мне сообщение, и я помогу:\n"
        "🏔 Подобрать тур\n"
        "❓ Ответить на вопрос\n"
        "🚨 Передать срочную проблему менеджеру\n\n"
        "Просто напишите, чего хотите! 😊"
    )


async def _handle_help(update: Update, context) -> None:
    """Обработчик команды /help."""
    await update.message.reply_text(
        "📖 Как пользоваться:\n\n"
        "Просто напишите мне сообщение — например:\n"
        "• «Хотим на выходные вдвоём, бюджет 15 тысяч»\n"
        "• «Тур отменили, мы на вокзале!»\n\n"
        "Я разберу ваш запрос и передам менеджеру.\n"
        "Можете писать несколько сообщений подряд — "
        "я подожду и склею их в одну заявку."
    )


async def _handle_message(update: Update, context) -> None:
    """
    Обработчик текстовых сообщений.
    Добавляет в буфер и ждёт склейки.
    """
    user_id = update.effective_user.id
    text = update.message.text

    if not text or not text.strip():
        return

    clean_text = text.strip().lower()
    # Убираем знаки препинания в конце
    clean_text = re.sub(r'[!.,?]+$', '', clean_text).strip()

    logger.info(f"Message from user {user_id}: {text[:50]}...")

    # Быстрый перехват чистых приветствий
    greetings = {"привет", "здравствуйте", "добрый день", "доброе утро", "добрый вечер", "здрасти", "здравствуй", "приветствую"}
    if clean_text in greetings:
        await update.message.reply_text(
            "Здравствуйте! 👋 Чем могу вам помочь? (подбор тура, вопросы по бронированию или поддержка в поездке)"
        )
        return  # Не отправляем это в нейросеть, экономим токен и время

    # Добавляем в буфер с callback на обработку
    await context_manager.add_message(
        user_id=user_id,
        text=text.strip(),
        on_ready=lambda uid, merged, history: _process_ready(
            update, uid, merged, history
        ),
    )


async def _process_ready(
    update: Update,
    user_id: int,
    merged_text: str,
    dialog_history: list[dict],
) -> None:
    """
    Вызывается когда буфер готов к обработке.
    Ведет живой диалог или выдает JSON по команде.
    """
    try:
        # Если клиент запросил JSON (кодовое слово)
        if merged_text.strip().lower() == "json":
            # Формируем полный текст истории для разбора
            history_text = gemini_client._format_context(dialog_history)
            
            # Отправляем ВСЮ историю на разбор (как единый текст)
            result = await gemini_client.analyze_message(history_text)
            
            # 1. Отправляем красивую карточку
            reply = _format_result(result)
            await update.message.reply_text(reply, parse_mode="HTML")
            
            # 2. Отправляем сырой JSON
            raw_json = result.model_dump_json(indent=2)
            await update.message.reply_text(f"<pre>{raw_json}</pre>", parse_mode="HTML")
            
            # Очищаем историю после выгрузки, чтобы начать с чистого листа
            context_manager.clear_history(user_id)
            return

        # Иначе — ведем живой диалог с помощью AI
        reply_text = await gemini_client.generate_dialog_reply(merged_text, dialog_history)
        
        # Если спам или пустой ответ — игнорируем
        if not reply_text or not reply_text.strip():
            return
            
        await update.message.reply_text(reply_text)
        
        # Сохраняем ответ ИИ в историю
        context_manager.add_bot_reply(user_id, reply_text)

    except Exception as e:
        logger.error(f"Error processing message for user {user_id}: {e}")
        await update.message.reply_text(
            "😔 Произошла ошибка при обработке сообщения. "
            "Пожалуйста, попробуйте ещё раз или напишите менеджеру."
        )


def _format_result(result: AnalyzeResponse) -> str:
    """
    Форматирует результат разбора для Telegram (HTML).
    
    Args:
        result: Результат разбора.
        
    Returns:
        Отформатированное HTML-сообщение.
    """
    # Иконки для intent
    intent_icons = {
        "подбор_тура": "🏷",
        "проблема_срочно": "🚨",
        "общий_вопрос": "❓",
        "спам": "🚫",
    }

    intent_str = result.intent.value if hasattr(result.intent, "value") else str(result.intent)
    icon = intent_icons.get(intent_str, "📋")
    lines = [f"{icon} <b>{intent_str.replace('_', ' ').title()}</b>"]
    lines.append("")

    if result.people_count:
        children_info = ""
        if result.has_children and result.children_ages:
            ages = ", ".join(str(a) for a in result.children_ages)
            children_info = f" (дети: {ages} лет)"
        elif result.has_children:
            children_info = " (с детьми)"
        lines.append(f"👥 {result.people_count} человек{children_info}")

    if result.budget_max:
        per = " на чел." if result.budget_per_person else ""
        lines.append(f"💰 до {result.budget_max:,} ₽{per}".replace(",", " "))

    if result.desired_dates:
        lines.append(f"📅 {result.desired_dates}")

    if result.destination_preferences:
        lines.append(f"🏔 {', '.join(result.destination_preferences)}")

    if result.special_requests:
        lines.append(f"✨ {', '.join(result.special_requests)}")

    if result.is_urgent:
        lines.append(f"\n⚡ <b>СРОЧНО</b>: {result.urgency_reason or 'требуется реакция'}")

    if result.draft_reply:
        lines.append(f"\n💬 {result.draft_reply}")

    return "\n".join(lines)
