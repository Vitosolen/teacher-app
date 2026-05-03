"""单词条目（听写最小单元）"""
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("word_groups.id", ondelete="CASCADE"), index=True, nullable=False
    )
    text: Mapped[str] = mapped_column(String(100), nullable=False)         # 朗读内容："apple"
    translation: Mapped[str] = mapped_column(String(100), nullable=False, default="")  # 释义："苹果"
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    group: Mapped["WordGroup"] = relationship(back_populates="words")  # type: ignore  # noqa: F821
