"""单词词库 + 单词请求/响应模型"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ----- 单词 -----

class WordCreate(BaseModel):
    text: str = Field(min_length=1, max_length=100)
    translation: str = Field(default="", max_length=100)
    sort_order: int = 0


class WordUpdate(BaseModel):
    text: str | None = Field(default=None, min_length=1, max_length=100)
    translation: str | None = Field(default=None, max_length=100)
    sort_order: int | None = None


class WordBatchCreate(BaseModel):
    """批量导入：每行一条；可写 'apple 苹果' 也可只写 'apple'"""
    lines: list[str] = Field(min_length=1, max_length=500)


class WordOut(BaseModel):
    id: int
    group_id: int
    text: str
    translation: str
    sort_order: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----- 词库（分组）-----

class WordGroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str = Field(default="", max_length=200)
    lang: str = Field(default="en-US", max_length=16)
    sort_order: int = 0


class WordGroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=200)
    lang: str | None = Field(default=None, max_length=16)
    sort_order: int | None = None


class WordGroupOut(BaseModel):
    id: int
    teacher_id: int
    name: str
    description: str
    lang: str
    sort_order: int
    created_at: datetime
    word_count: int = 0  # 业务层填充

    model_config = ConfigDict(from_attributes=True)


class WordGroupDetailOut(WordGroupOut):
    """词库详情含全部单词"""
    words: list[WordOut] = []
