"""积分规则（替代硬编码预设按钮，按老师隔离）"""
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ScoreRule(Base):
    __tablename__ = "score_rules"
    __table_args__ = (UniqueConstraint("teacher_id", "label", name="uq_rule_teacher_label"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    label: Mapped[str] = mapped_column(String(50), nullable=False)        # 例："回答问题"
    category: Mapped[str] = mapped_column(String(20), nullable=False)    # 学习/纪律/积极/消极
    score: Mapped[int] = mapped_column(Integer, nullable=False)          # -10 ~ +10
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
