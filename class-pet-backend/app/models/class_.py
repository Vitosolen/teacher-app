"""班级表"""
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Class(Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    grade: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # 关联关系
    teacher: Mapped["Teacher"] = relationship(back_populates="classes")  # type: ignore  # noqa: F821
    students: Mapped[list["Student"]] = relationship(  # type: ignore  # noqa: F821
        back_populates="class_", cascade="all, delete-orphan"
    )
