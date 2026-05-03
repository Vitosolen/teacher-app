"""认证相关请求/响应模型"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=72)
    display_name: str = Field(min_length=1, max_length=50)


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TeacherOut(BaseModel):
    id: int
    username: str
    display_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
