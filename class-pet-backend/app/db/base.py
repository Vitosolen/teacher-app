"""SQLAlchemy 声明式基类（独立模块，避免循环导入）"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
