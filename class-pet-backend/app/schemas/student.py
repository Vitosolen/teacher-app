"""学生请求/响应模型"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.pet import PetOut


class StudentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    student_no: str = Field(default="", max_length=30)


class StudentUpdate(BaseModel):
    """学生编辑：所有字段可选"""
    name: str | None = Field(default=None, min_length=1, max_length=50)
    student_no: str | None = Field(default=None, max_length=30)


class StudentBatchCreate(BaseModel):
    """批量导入：每行一个姓名（前端粘贴文本后切分传过来）"""
    names: list[str] = Field(min_length=1, max_length=200)


class StudentOut(BaseModel):
    id: int
    class_id: int
    name: str
    student_no: str
    points: int = 0  # 可消费积分余额
    created_at: datetime
    pet: Optional[PetOut] = None

    model_config = ConfigDict(from_attributes=True)
