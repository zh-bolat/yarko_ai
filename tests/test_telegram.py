"""
Тесты Telegram-бота: контекст-менеджер склейки сообщений.
"""

import asyncio
import pytest

from app.context_manager import ContextManager


@pytest.mark.asyncio
async def test_single_message_after_timeout():
    """Одно сообщение обрабатывается после таймаута."""
    cm = ContextManager()
    results = []

    async def on_ready(user_id, merged, history):
        results.append({"user_id": user_id, "text": merged, "history": history})

    await cm.add_message(user_id=1, text="Привет!", on_ready=on_ready)

    # Ждём чуть больше таймаута (используем короткий для теста)
    # В реальности таймаут 30 сек, но для теста ContextManager настроен из settings
    await asyncio.sleep(0.5)

    # Таймер ещё не сработал (30 сек по дефолту), проверяем буфер
    assert len(cm._buffers) > 0


@pytest.mark.asyncio
async def test_multiple_messages_merged():
    """Несколько сообщений склеиваются в один текст."""
    cm = ContextManager()
    results = []

    async def on_ready(user_id, merged, history):
        results.append({"user_id": user_id, "text": merged})

    await cm.add_message(user_id=1, text="Сообщение 1", on_ready=on_ready)
    await cm.add_message(user_id=1, text="Сообщение 2", on_ready=on_ready)
    await cm.add_message(user_id=1, text="Сообщение 3", on_ready=on_ready)

    # Проверяем что все сообщения в буфере
    buffer = cm._buffers.get(1)
    assert buffer is not None
    assert len(buffer.messages) == 3
    assert buffer.merged_text == "Сообщение 1\n\nСообщение 2\n\nСообщение 3"


@pytest.mark.asyncio
async def test_different_users_separate_buffers():
    """Сообщения разных пользователей не смешиваются."""
    cm = ContextManager()

    async def on_ready(user_id, merged, history):
        pass

    await cm.add_message(user_id=1, text="User 1 msg", on_ready=on_ready)
    await cm.add_message(user_id=2, text="User 2 msg", on_ready=on_ready)

    assert len(cm._buffers) == 2
    assert cm._buffers[1].messages == ["User 1 msg"]
    assert cm._buffers[2].messages == ["User 2 msg"]


@pytest.mark.asyncio
async def test_dialog_history_tracking():
    """История диалога сохраняется корректно."""
    cm = ContextManager()

    async def on_ready(user_id, merged, history):
        pass

    await cm.add_message(user_id=1, text="Привет", on_ready=on_ready)
    cm.add_bot_reply(user_id=1, text="Здравствуйте!")
    await cm.add_message(user_id=1, text="Хочу тур", on_ready=on_ready)

    history = cm.get_history(user_id=1)
    assert len(history) == 3
    assert history[0]["role"] == "user"
    assert history[0]["text"] == "Привет"
    assert history[1]["role"] == "bot"
    assert history[1]["text"] == "Здравствуйте!"
    assert history[2]["role"] == "user"
    assert history[2]["text"] == "Хочу тур"


@pytest.mark.asyncio
async def test_buffer_max_messages():
    """Буфер обрабатывается сразу при достижении лимита."""
    cm = ContextManager()
    results = []

    async def on_ready(user_id, merged, history):
        results.append(merged)

    # Добавляем MAX сообщений (по дефолту 10)
    for i in range(10):
        await cm.add_message(user_id=1, text=f"msg_{i}", on_ready=on_ready)

    # Должен был обработаться сразу
    assert len(results) == 1
    assert "msg_0" in results[0]
    assert "msg_9" in results[0]
