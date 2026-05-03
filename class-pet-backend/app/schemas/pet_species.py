"""宠物物种 + 等级资源请求/响应模型"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# —— Asset（等级资源）——

class AssetCreate(BaseModel):
    level: int = Field(ge=1, le=999)
    emoji: str = Field(default="🥚", max_length=8)
    image_url: str | None = Field(default=None, max_length=255)


class AssetUpdate(BaseModel):
    emoji: str | None = Field(default=None, max_length=8)
    image_url: str | None = Field(default=None, max_length=255)


class AssetOut(BaseModel):
    id: int
    species_id: int
    level: int
    emoji: str
    image_url: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# —— Species（物种）——

class SpeciesCreate(BaseModel):
    code: str = Field(min_length=1, max_length=30, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=50)
    description: str = Field(default="", max_length=200)
    sort_order: int = 0


class SpeciesUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=200)
    sort_order: int | None = None
    # code 不允许改：影响存量 student.pet.species 数据完整性


class SpeciesOut(BaseModel):
    id: int
    code: str
    name: str
    description: str
    sort_order: int
    created_at: datetime
    assets: list[AssetOut] = []

    model_config = ConfigDict(from_attributes=True)
