"""学生作业记录（一份作业 × 一名学生 = 一条 record，可批改打分点评）"""
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class HomeworkRecord(Base):
    __tablename__ = "homework_records"
    __table_args__ = (
        UniqueConstraint("homework_id", "student_id", name="uq_record_homework_student"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    homework_id: Mapped[int] = mapped_column(
        ForeignKey("homeworks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # 状态：未提交/已提交/已批改
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="未提交")
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)        # 0-100
    comment: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    scored_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # 订正：仅 type=homework 的作业用；批改时若 score<90 自动置 needs_correction=True
    needs_correction: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    corrected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    corrected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # 关联
    homework: Mapped["Homework"] = relationship(back_populates="records")  # type: ignore  # noqa: F821
