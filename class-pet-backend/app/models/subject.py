"""科目表（按老师隔离）"""
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Subject(Base):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("teacher_id", "name", name="uq_subject_teacher_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(30), nullable=False)        # 例：语文、数学
    color: Mapped[str] = mapped_column(String(16), nullable=False, default="#409EFF")  # 卡片色
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
