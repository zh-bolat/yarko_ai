"""
Тесты разбора 12 тестовых сообщений из ТЗ.
Проверяет корректность intent, параметров и структуры ответа.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models import AnalyzeResponse

# 12 тестовых сообщений из ТЗ
TEST_MESSAGES = [
    {
        "id": 1,
        "text": "Привет! Нас 3 человека (2 взрослых и ребёнок 8 лет). Хотим на эти выходные в горы или к воде, бюджет до 20 000 руб на всех. Что посоветуете?",
        "expected_intent": "подбор_тура",
        "expected_people": 3,
        "expected_children": True,
        "expected_budget": 20000,
        "expected_urgent": False,
    },
    {
        "id": 2,
        "text": "Алло, тур отменили?! Срочно перезвоните мне, мы уже стоим на вокзале!",
        "expected_intent": "проблема_срочно",
        "expected_people": None,
        "expected_children": False,
        "expected_budget": None,
        "expected_urgent": True,
    },
    {
        "id": 3,
        "text": "Здравствуйте, мы хотим поехать вдвоём с мужем",
        "expected_intent": "подбор_тура",
        "expected_people": 2,
        "expected_children": False,
        "expected_budget": None,
        "expected_urgent": False,
    },
    {
        "id": 4,
        "text": "Забыла написать — на 14-15 марта, бюджет тысяч 25, желательно с баней",
        "expected_intent": "подбор_тура",
        "expected_people": None,
        "expected_children": False,
        "expected_budget": 25000,
        "expected_urgent": False,
    },
    {
        "id": 5,
        "text": "здарова а есть чтонить недорогое на выхи в подмасковье вдвоем ну тыщ за 10 чтобы",
        "expected_intent": "подбор_тура",
        "expected_people": 2,
        "expected_children": False,
        "expected_budget": 10000,
        "expected_urgent": False,
    },
    {
        "id": 6,
        "text": "Добрый день! Я организатор, у меня тур на Алтай в июне. Как разместить его у вас на сайте и какая комиссия?",
        "expected_intent": "общий_вопрос",
        "expected_people": None,
        "expected_children": False,
        "expected_budget": None,
        "expected_urgent": False,
    },
    {
        "id": 7,
        "text": "Нас четверо, бюджет 20 000 на человека, но в целом больше 30 000 не потянем",
        "expected_intent": "подбор_тура",
        "expected_people": 4,
        "expected_children": False,
        "expected_budget": None,  # Ambiguous — could be 30000 or 80000
        "expected_urgent": False,
    },
    {
        "id": 8,
        "text": "ЗАРАБОТОК ОТ 5000 РУБ В ДЕНЬ НА ДОМУ БЕЗ ВЛОЖЕНИЙ ПИШИТЕ В ЛС @easymoney2026",
        "expected_intent": "спам",
        "expected_people": None,
        "expected_children": False,
        "expected_budget": None,
        "expected_urgent": False,
    },
    {
        "id": 9,
        "text": "Здравствуйте",
        "expected_intent": "общий_вопрос",
        "expected_people": None,
        "expected_children": False,
        "expected_budget": None,
        "expected_urgent": False,
    },
    {
        "id": 10,
        "text": "Оплатила тур неделю назад, деньги списались, а подтверждение так и не пришло. Уже второй раз пишу.",
        "expected_intent": "проблема_срочно",
        "expected_people": None,
        "expected_children": False,
        "expected_budget": None,
        "expected_urgent": True,
    },
    {
        "id": 11,
        "text": "Смотрю ваш тур на Куршскую косу 20-22 июня. Дети 4 и 11 лет, подойдёт им? И можно ли к вам с собакой?",
        "expected_intent": "подбор_тура",
        "expected_people": None,
        "expected_children": True,
        "expected_budget": None,
        "expected_urgent": False,
    },
    {
        "id": 12,
        "text": "Хотим что-нибудь на майские, компанией человек 8-10, желательно с активностями — сплав, квадроциклы. Бюджет обсуждаем.",
        "expected_intent": "подбор_тура",
        "expected_people": None,  # Range 8-10
        "expected_children": False,
        "expected_budget": None,
        "expected_urgent": False,
    },
]


@pytest.fixture
def auth_headers():
    """Заголовки с авторизацией для тестов."""
    # В тестах пароль пустой — авторизация пропускается
    return {"Authorization": "Bearer test-token"}


@pytest.mark.asyncio
@pytest.mark.parametrize("msg", TEST_MESSAGES, ids=[f"msg_{m['id']}" for m in TEST_MESSAGES])
async def test_analyze_message(msg, auth_headers):
    """Тестирует разбор каждого из 12 сообщений."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/analyze",
            json={"message": msg["text"]},
            headers=auth_headers,
        )

    assert response.status_code == 200, f"Message #{msg['id']}: {response.text}"

    data = response.json()
    result = AnalyzeResponse(**data)

    # Проверяем intent
    assert result.intent == msg["expected_intent"], (
        f"Message #{msg['id']}: expected intent '{msg['expected_intent']}', "
        f"got '{result.intent}'"
    )

    # Проверяем наличие детей
    assert result.has_children == msg["expected_children"], (
        f"Message #{msg['id']}: expected has_children={msg['expected_children']}, "
        f"got {result.has_children}"
    )

    # Проверяем срочность
    assert result.is_urgent == msg["expected_urgent"], (
        f"Message #{msg['id']}: expected is_urgent={msg['expected_urgent']}, "
        f"got {result.is_urgent}"
    )

    # Проверяем наличие draft_reply (кроме спама)
    if msg["expected_intent"] != "спам":
        assert result.draft_reply is not None and len(result.draft_reply) > 0, (
            f"Message #{msg['id']}: expected non-empty draft_reply"
        )

    # Проверяем confidence
    assert 0.0 <= result.confidence <= 1.0, (
        f"Message #{msg['id']}: confidence {result.confidence} out of range"
    )

    # Проверяем people_count если указан
    if msg["expected_people"] is not None:
        assert result.people_count == msg["expected_people"], (
            f"Message #{msg['id']}: expected people_count={msg['expected_people']}, "
            f"got {result.people_count}"
        )

    # Проверяем budget_max если указан
    if msg["expected_budget"] is not None:
        assert result.budget_max == msg["expected_budget"], (
            f"Message #{msg['id']}: expected budget_max={msg['expected_budget']}, "
            f"got {result.budget_max}"
        )


@pytest.mark.asyncio
async def test_batch_analyze(auth_headers):
    """Тестирует batch-разбор нескольких сообщений."""
    messages = [m["text"] for m in TEST_MESSAGES[:3]]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/batch",
            json={"messages": messages},
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 3
    assert "total_cost_rub" in data


@pytest.mark.asyncio
async def test_health():
    """Тестирует healthcheck."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
