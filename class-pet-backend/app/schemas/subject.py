"""科目请求/响应模型"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=30)
    color: str = Field(default="#409EFF", max_length=16)
    sort_order: int = 0


class SubjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=30)
    color: str | None = Field(default=None, max_length=16)
    sort_order: int | None = None


class SubjectOut(BaseModel):
    id: int
    teacher_id: int
    name: str
    color: str
    sort_order: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
