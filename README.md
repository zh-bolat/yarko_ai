# 🌍 Яркотревел AI — Автоматический разбор сообщений туристов

AI-инструмент для автоматической классификации и разбора сообщений от туристов.

## Что делает

- Принимает текст сообщения от туриста
- Классифицирует intent (подбор тура, проблема, вопрос, спам)
- Извлекает параметры (люди, дети, бюджет, даты, направления)
- Генерирует черновик ответа менеджеру
- Оценивает уверенность и стоимость разбора

## Быстрый старт

```bash
# 1. Клонировать
git clone https://github.com/YOUR_USER/yarko-ai.git
cd yarko-ai

# 2. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate

# 3. Установить зависимости
make install

# 4. Настроить переменные окружения
make env
# Отредактируйте .env — добавьте GEMINI_API_KEY

# 5. Запустить
make dev
```

Откройте http://localhost:8000

## Стек

- **Python 3.11+** + **FastAPI**
- **Google Gemini 2.0 Flash** — AI-модель
- **python-telegram-bot** — Telegram-бот
- **Pydantic v2** — валидация

## API

### POST /api/analyze
Разбор одного сообщения.
```json
{"message": "Нас 3 человека, хотим в горы, бюджет 20 000"}
```

### POST /api/batch
Разбор нескольких сообщений.
```json
{"messages": ["Сообщение 1", "Сообщение 2"]}
```

### POST /api/auth
Авторизация по паролю.
```json
{"password": "yarko2026"}
```

## Тесты

```bash
make test           # Все тесты
make test-analyze   # 12 тестовых сообщений
make test-edge      # Edge cases
make test-telegram  # Telegram-бот
```

## Деплой (Render.com)

1. Push в GitHub
2. Подключить репо на [render.com](https://render.com)
3. Добавить env vars: `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `APP_PASSWORD`
4. Deploy!

## Лицензия

MIT
