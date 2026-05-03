"""作业 / 成绩请求/响应模型

作业（type='homework'）：日常作业，批改后低于 90 分的需要订正
成绩（type='exam'）：考试 / 课堂测验，仅记分不订正
"""
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict


HOMEWORK_TYPES = ("homework", "exam")


class HomeworkCreate(BaseModel):
    class_id: int
    subject_id: int
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(default="")
    due_date: date | None = None
    type: str = Field(default="homework", max_length=20)


class HomeworkRecordOut(BaseModel):
    id: int
    homework_id: int
    student_id: int
    student_name: str = ""    # 业务层填充
    student_no: str = ""
    status: str
    score: int | None = None
    comment: str
    scored_at: datetime | None = None
    needs_correction: bool = False
    corrected: bool = False
    corrected_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HomeworkRecordUpdate(BaseModel):
    """批改：分数 0-100、评语；批改作业时若 score<90 自动置 needs_correction=true"""
    score: int | None = Field(default=None, ge=0, le=100)
    comment: str | None = Field(default=None, max_length=500)
    status: str | None = Field(default=None, max_length=20)
    corrected: bool | None = None  # 老师可显式标记"已订正"


class HomeworkOut(BaseModel):
    id: int
    class_id: int
    class_name: str = ""
    subject_id: int
    subject_name: str = ""
    subject_color: str = "#409EFF"
    type: str = "homework"
    title: str
    content: str
    due_date: date | None = None
    created_at: datetime

    # 列表页统计
    total_count: int = 0
    graded_count: int = 0
    correction_pending_count: int = 0  # 需订正未订正数（仅作业）

    model_config = ConfigDict(from_attributes=True)


class HomeworkDetailOut(HomeworkOut):
    records: list[HomeworkRecordOut] = []
