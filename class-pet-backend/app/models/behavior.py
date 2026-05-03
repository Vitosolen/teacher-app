"""行为记录表"""
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Behavior(Base):
    __tablename__ = "behaviors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)        # -10 ~ +10
    category: Mapped[str] = mapped_column(String(20), nullable=False)  # 学习/纪律/积极/消极
    reason: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    # 关联触发的积分规则（可空：兼容自定义打分）
    score_rule_id: Mapped[int | None] = mapped_column(
        ForeignKey("score_rules.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 关联关系
    student: Mapped["Student"] = relationship(back_populates="behaviors")  # type: ignore  # noqa: F821
