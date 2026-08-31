"""
Контекст-менеджер для склейки сообщений в Telegram.

Алгоритм:
1. Получили сообщение от user_id
2. Сохраняем в буфер: {user_id: [msg1, msg2, ...]}
3. Запускаем таймер на 30 секунд
4. Если за 30 сек пришло ещё сообщение — добавляем, сбрасываем таймер
5. Когда таймер истёк — склеиваем и отправляем на разбор
6. TTL буфера: 1 час
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class UserBuffer:
    """Буфер сообщений одного пользователя."""
    user_id: int
    messages: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_message_at: float = field(default_factory=time.time)
    timer_task: Optional[asyncio.Task] = field(default=None, repr=False)
    dialog_history: list[dict] = field(default_factory=list)

    @property
    def is_expired(self) -> bool:
        """Проверяет, истёк ли TTL буфера."""
        return (time.time() - self.created_at) > settings.MESSAGE_BUFFER_TTL_SEC

    @property
    def is_full(self) -> bool:
        """Проверяет, достигнут ли лимит сообщений."""
        return len(self.messages) >= settings.MESSAGE_BUFFER_MAX_MESSAGES

    @property
    def merged_text(self) -> str:
        """Склеивает все сообщения в один текст."""
        return "\n\n".join(self.messages)

    def add_message(self, text: str) -> None:
        """Добавляет сообщение в буфер."""
        self.messages.append(text)
        self.last_message_at = time.time()

    def add_to_history(self, role: str, text: str) -> None:
        """Добавляет сообщение в историю диалога."""
        self.dialog_history.append({
            "role": role,
            "text": text,
            "timestamp": time.time(),
        })

    def cancel_timer(self) -> None:
        """Отменяет текущий таймер."""
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()
            self.timer_task = None


class ContextManager:
    """
    Менеджер контекста для склейки сообщений Telegram.
    
    Хранит буферы по user_id, управляет таймерами ожидания
    и вызывает callback при готовности склеенного сообщения.
    """

    def __init__(self) -> None:
        self._buffers: dict[int, UserBuffer] = {}

    async def add_message(
        self,
        user_id: int,
        text: str,
        on_ready: Callable,
    ) -> None:
        """
        Добавляет сообщение в буфер пользователя.
        
        Args:
            user_id: ID пользователя Telegram.
            text: Текст сообщения.
            on_ready: Callback, вызывается когда буфер готов к обработке.
                      Принимает (user_id, merged_text, dialog_history).
        """
        # Очищаем просроченные буферы
        self._cleanup_expired()

        # Получаем или создаём буфер
        buffer = self._buffers.get(user_id)
        if buffer is None or buffer.is_expired:
            buffer = UserBuffer(user_id=user_id)
            self._buffers[user_id] = buffer

        # Добавляем сообщение
        buffer.add_message(text)
        buffer.add_to_history("user", text)

        # Отменяем предыдущий таймер
        buffer.cancel_timer()

        # Если буфер полон — обрабатываем сразу
        if buffer.is_full:
            logger.info(f"Buffer full for user {user_id}, processing immediately")
            await self._process_buffer(user_id, on_ready)
            return

        # Запускаем новый таймер
        buffer.timer_task = asyncio.create_task(
            self._wait_and_process(user_id, on_ready)
        )

    async def _wait_and_process(
        self,
        user_id: int,
        on_ready: Callable,
    ) -> None:
        """Ждёт таймаут и обрабатывает буфер."""
        try:
            await asyncio.sleep(settings.MESSAGE_BUFFER_TIMEOUT_SEC)
            await self._process_buffer(user_id, on_ready)
        except asyncio.CancelledError:
            logger.debug(f"Timer cancelled for user {user_id} (new message received)")

    async def _process_buffer(
        self,
        user_id: int,
        on_ready: Callable,
    ) -> None:
        """Обрабатывает готовый буфер."""
        buffer = self._buffers.get(user_id)
        if buffer is None:
            return

        merged = buffer.merged_text
        history = buffer.dialog_history.copy()

        # Очищаем сообщения, но сохраняем историю
        buffer.messages.clear()
        buffer.timer_task = None

        logger.info(
            f"Processing buffer for user {user_id}: "
            f"{len(merged)} chars from {len(history)} messages"
        )

        await on_ready(user_id, merged, history)

    def get_history(self, user_id: int) -> list[dict]:
        """Возвращает историю диалога пользователя."""
        buffer = self._buffers.get(user_id)
        if buffer is None or buffer.is_expired:
            return []
        return buffer.dialog_history

    def clear_history(self, user_id: int) -> None:
        """Очищает историю диалога пользователя."""
        buffer = self._buffers.get(user_id)
        if buffer:
            buffer.dialog_history.clear()
            # Обновляем created_at, чтобы начать сессию заново
            import time
            buffer.created_at = time.time()

    def add_bot_reply(self, user_id: int, text: str) -> None:
        """Добавляет ответ бота в историю диалога."""
        buffer = self._buffers.get(user_id)
        if buffer:
            buffer.add_to_history("bot", text)

    def _cleanup_expired(self) -> None:
        """Удаляет просроченные буферы."""
        expired = [
            uid for uid, buf in self._buffers.items()
            if buf.is_expired
        ]
        for uid in expired:
            self._buffers[uid].cancel_timer()
            del self._buffers[uid]

        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired buffers")


# Синглтон
context_manager = ContextManager()
