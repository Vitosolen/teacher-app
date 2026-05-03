"""班级请求/响应模型"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    grade: str = Field(default="", max_length=20)


class ClassUpdate(BaseModel):
    """班级编辑：所有字段可选"""
    name: str | None = Field(default=None, min_length=1, max_length=50)
    grade: str | None = Field(default=None, max_length=20)


class ClassOut(BaseModel):
    id: int
    name: str
    grade: str
    teacher_id: int
    created_at: datetime
    student_count: int = 0  # 业务层填充

    model_config = ConfigDict(from_attributes=True)
