"""密码哈希与 JWT 编解码"""
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str | int, expires_delta: Optional[timedelta] = None) -> str:
    """签发 JWT。subject 一般放 teacher_id"""
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[int]:
    """解码 JWT，成功返回 teacher_id，失败返回 None"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            return None
        return int(sub)
    except (JWTError, ValueError):
        return None
