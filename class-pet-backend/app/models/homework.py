"""作业表（班级 + 科目下的一份作业模板，会为班内每生展开为 homework_records）"""
from datetime import datetime, date

from sqlalchemy import String, DateTime, Date, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Homework(Base):
    __tablename__ = "homeworks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # 任务类型：homework=作业（默认，需订正），exam=考试/成绩登记（不订正）
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="homework", index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # 关联：所有学生记录（删作业级联删 records）
    records: Mapped[list["HomeworkRecord"]] = relationship(  # type: ignore  # noqa: F821
        back_populates="homework", cascade="all, delete-orphan"
    )
