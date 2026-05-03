"""宠物表（与学生 1:1）"""
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Pet(Base):
    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    species: Mapped[str] = mapped_column(String(30), nullable=False, default="幼龙")
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    exp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hunger: Mapped[int] = mapped_column(Integer, nullable=False, default=60)  # 0-100，越高越饱
    mood: Mapped[int] = mapped_column(Integer, nullable=False, default=80)    # 0-100，越高越开心
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # 关联关系
    student: Mapped["Student"] = relationship(back_populates="pet")  # type: ignore  # noqa: F821
