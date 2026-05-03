"""FastAPI 依赖：DB Session、当前老师"""
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.teacher import Teacher

# tokenUrl 指向登录接口，用于 Swagger UI 的 Authorize 按钮
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_teacher(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Teacher:
    """从 JWT 解出 teacher_id 并加载 Teacher，未登录或 token 失效抛 401"""
    teacher_id = decode_access_token(token)
    if teacher_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    teacher = db.get(Teacher, teacher_id)
    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return teacher
