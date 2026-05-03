"""积分规则请求/响应模型"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


CATEGORIES = ("学习", "纪律", "积极", "消极")


class ScoreRuleCreate(BaseModel):
    label: str = Field(min_length=1, max_length=50)
    category: str = Field(min_length=1, max_length=20)
    score: int = Field(ge=-100, le=100)
    sort_order: int = 0
    active: bool = True


class ScoreRuleUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=50)
    category: str | None = Field(default=None, max_length=20)
    score: int | None = Field(default=None, ge=-100, le=100)
    sort_order: int | None = None
    active: bool | None = None


class ScoreRuleOut(BaseModel):
    id: int
    teacher_id: int
    label: str
    category: str
    score: int
    sort_order: int
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
