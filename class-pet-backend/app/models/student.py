"""学生表"""
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    student_no: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 可消费积分余额（加分累加，扣分不扣，购物扣减）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # 关联关系
    class_: Mapped["Class"] = relationship(back_populates="students")  # type: ignore  # noqa: F821
    pet: Mapped["Pet"] = relationship(  # type: ignore  # noqa: F821
        back_populates="student", uselist=False, cascade="all, delete-orphan"
    )
    behaviors: Mapped[list["Behavior"]] = relationship(  # type: ignore  # noqa: F821
        back_populates="student", cascade="all, delete-orphan"
    )
