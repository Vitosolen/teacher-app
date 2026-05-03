"""宠物请求/响应模型"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class PetOut(BaseModel):
    id: int
    student_id: int
    name: str
    species: str
    level: int
    exp: int
    hunger: int
    mood: int
    last_updated_at: datetime
    created_at: datetime
    # 派生字段（业务层填充）
    status: str = "健康"
    exp_to_next_level: int = 100

    model_config = ConfigDict(from_attributes=True)


class PetUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class PetAdopt(BaseModel):
    """领养：起名 + 选物种（前端已知物种白名单，后端只校验长度不限定枚举）"""
    name: str = Field(min_length=1, max_length=50)
    species: str = Field(default="dragon", max_length=30)
