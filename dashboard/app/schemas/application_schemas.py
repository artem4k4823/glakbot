from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ApplicationQuestion(BaseModel):
    """Один вопрос анкеты. Ограничения повторяют лимиты модальных окон Discord."""

    label: str = Field(..., min_length=1, max_length=45)
    placeholder: str = Field("", max_length=100)
    style: Literal["short", "paragraph"] = "short"
    required: bool = True
    min_length: int = Field(0, ge=0, le=4000)
    max_length: int = Field(1000, ge=1, le=4000)

    @model_validator(mode="after")
    def check_lengths(self):
        if self.min_length > self.max_length:
            raise ValueError(f"«{self.label}»: минимальная длина больше максимальной")
        return self


DEFAULT_QUESTIONS: List[dict] = [
    {"label": "Как к вам обращаться?", "placeholder": "Имя или ник", "style": "short",
     "required": True, "min_length": 2, "max_length": 50},
    {"label": "Сколько вам лет?", "placeholder": "Например: 18", "style": "short",
     "required": True, "min_length": 1, "max_length": 3},
    {"label": "Откуда вы узнали о сервере?", "placeholder": "Друг, реклама, поиск...", "style": "short",
     "required": True, "min_length": 2, "max_length": 100},
    {"label": "Расскажите немного о себе", "placeholder": "Чем увлекаетесь, зачем пришли на сервер...",
     "style": "paragraph", "required": True, "min_length": 10, "max_length": 1000},
]


class ApplicationConfigSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    enabled: bool = True
    title: str = Field("📋 Анкета для вступления", min_length=1, max_length=255)
    description: str = Field(
        "Чтобы получить доступ к серверу, заполните короткую анкету. "
        "Администрация рассмотрит её и выдаст роль.",
        min_length=1,
        max_length=4000,
    )
    color: str = Field("#5865F2", pattern=r"^#[0-9a-fA-F]{6}$")
    banner_url: Optional[str] = Field(None, max_length=500)
    button_label: str = Field("Заполнить анкету", min_length=1, max_length=80)
    questions: List[ApplicationQuestion] = Field(
        default_factory=lambda: [ApplicationQuestion(**q) for q in DEFAULT_QUESTIONS],
        min_length=1,
        max_length=5,
    )
    approved_role_id: Optional[str] = None
    review_channel_id: Optional[str] = None
    dm_on_decision: bool = True
    approve_message: str = Field(
        "✅ Ваша анкета на сервере **{server}** одобрена! Добро пожаловать.", max_length=2000
    )
    reject_message: str = Field(
        "❌ Ваша анкета на сервере **{server}** отклонена.\nПричина: {reason}", max_length=2000
    )

    @field_validator("banner_url", "approved_role_id", "review_channel_id", mode="before")
    @classmethod
    def empty_to_none(cls, v):
        return v or None


class ApplicationAnswer(BaseModel):
    question: str
    answer: str


class ApplicationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    guild_id: str
    user_id: str
    user_name: str
    user_avatar: Optional[str] = None
    answers: List[ApplicationAnswer] = []
    status: str
    reject_reason: Optional[str] = None
    reviewer_name: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None


class ApplicationRejectRequest(BaseModel):
    reason: str = Field("", max_length=1000)


class ApplicationDecisionResult(BaseModel):
    application: ApplicationSchema
    dm_sent: Optional[bool] = None  # None — ЛС отключены в настройках
