"""单词分组（老师独立的"词库"，听写时按词库展开）"""
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WordGroup(Base):
    __tablename__ = "word_groups"
    __table_args__ = (UniqueConstraint("teacher_id", "name", name="uq_wgroup_teacher_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    # 朗读语言：en-US / zh-CN / en-GB / ja-JP 等，前端 SpeechSynthesisUtterance.lang 直接用
    lang: Mapped[str] = mapped_column(String(16), nullable=False, default="en-US")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    words: Mapped[list["Word"]] = relationship(  # type: ignore  # noqa: F821
        back_populates="group", cascade="all, delete-orphan"
    )
