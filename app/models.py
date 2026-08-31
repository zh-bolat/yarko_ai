"""
Pydantic-модели для запросов и ответов API.
Определяет JSON-схему для структурированного вывода Gemini.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class Intent(str, Enum):
    """Классификация намерения туриста."""
    TOUR_SEARCH = "подбор_тура"
    PROBLEM_URGENT = "проблема_срочно"
    GENERAL_QUESTION = "общий_вопрос"
    SPAM = "спам"


class Sentiment(str, Enum):
    """Тональность сообщения."""
    POSITIVE = "позитивный"
    NEUTRAL = "нейтральный"
    NEGATIVE = "негативный"


# ──────────────────────────────────────────────
# Запросы
# ──────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    """Запрос на разбор одного сообщения."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Текст сообщения от туриста",
        examples=["Привет! Нас 3 человека, хотим на выходные в горы."],
    )


class BatchAnalyzeRequest(BaseModel):
    """Запрос на разбор нескольких сообщений."""
    messages: list[str] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Список сообщений для разбора",
    )


class AuthRequest(BaseModel):
    """Запрос авторизации по паролю."""
    password: str = Field(..., description="Пароль для доступа")


# ──────────────────────────────────────────────
# Ответы
# ──────────────────────────────────────────────

class TokenUsage(BaseModel):
    """Использование токенов для оценки стоимости."""
    input: int = Field(0, description="Количество входных токенов")
    output: int = Field(0, description="Количество выходных токенов")


class GeminiAnalyzeResponse(BaseModel):
    """Схема ответа от Gemini API."""

    # Базовые поля (по ТЗ)
    intent: Intent = Field(..., description="Классификация намерения")
    people_count: Optional[int] = Field(None, description="Количество человек")
    has_children: bool = Field(False, description="Есть ли дети в группе")
    budget_max: Optional[int] = Field(None, description="Максимальный бюджет (руб)")
    is_urgent: bool = Field(False, description="Требуется ли срочная реакция")
    draft_reply: Optional[str] = Field(None, description="Черновик ответа туристу")

    # Расширенные поля (бонус)
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Уверенность в классификации")
    children_ages: list[int] = Field(default_factory=list, description="Возрасты детей")
    budget_per_person: bool = Field(False, description="Бюджет указан на человека")
    urgency_reason: Optional[str] = Field(None, description="Причина срочности")
    destination_preferences: list[str] = Field(default_factory=list, description="Предпочтения по направлению")
    desired_dates: Optional[str] = Field(None, description="Даты как указал турист")
    extracted_dates_iso: Optional[str] = Field(None, description="Даты в ISO-формате")
    special_requests: list[str] = Field(default_factory=list, description="Особые пожелания")
    language: str = Field("ru", description="Язык сообщения")
    sentiment: Sentiment = Field(Sentiment.NEUTRAL, description="Тональность")
    notes: Optional[str] = Field(None, description="Заметки AI о неоднозначностях")

class AnalyzeResponse(GeminiAnalyzeResponse):
    """Результат разбора сообщения, включая метаданные стоимости."""
    # Метаданные стоимости
    cost_rub: float = Field(0.0, description="Стоимость разбора (руб)")
    tokens_used: TokenUsage = Field(default_factory=TokenUsage, description="Использованные токены")


class BatchAnalyzeResponse(BaseModel):
    """Результат разбора нескольких сообщений."""
    results: list[AnalyzeResponse] = Field(..., description="Список результатов")
    total_cost_rub: float = Field(0.0, description="Общая стоимость всех разборов")


class HealthResponse(BaseModel):
    """Ответ healthcheck."""
    status: str = "ok"
    version: str = "1.0.0"
    model: str = ""


class AuthResponse(BaseModel):
    """Ответ авторизации."""
    success: bool
    message: str


class ErrorResponse(BaseModel):
    """Ответ с ошибкой."""
    error: str
    detail: Optional[str] = None
