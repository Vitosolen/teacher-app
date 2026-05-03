"""行为请求/响应模型"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.pet import PetOut

VALID_CATEGORIES = ("学习", "纪律", "积极", "消极")


class BehaviorCreate(BaseModel):
    """
    支持两种调用方式：
    - 传 score_rule_id：从规则取 score/category/reason，老师不必每次填
    - 不传 score_rule_id：使用 score/category/reason 自定义打分
    """
    student_id: int
    score_rule_id: int | None = None
    # 放宽到 ±100，给老师更大自由（重大事件可一次性给大分数）
    score: int | None = Field(default=None, ge=-100, le=100)
    category: str | None = Field(default=None, max_length=20)
    reason: str = Field(default="", max_length=200)


class BehaviorUpdate(BaseModel):
    """编辑已有行为：只允许改备注层字段（category / reason），不允许改 score
    避免复杂的宠物属性回滚逻辑（已发生的衰减、升级无法准确反推）"""
    category: str | None = Field(default=None, max_length=20)
    reason: str | None = Field(default=None, max_length=200)


class BehaviorOut(BaseModel):
    id: int
    student_id: int
    teacher_id: int
    score: int
    category: str
    reason: str
    score_rule_id: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BehaviorWithPetOut(BaseModel):
    """记录行为后返回当前最新宠物状态 + 学生最新积分余额，便于前端实时刷新 UI"""
    behavior: BehaviorOut
    pet: PetOut
    student_points: int = 0  # 当前学生 points 余额
    leveled_up: bool = False
    levels_gained: int = 0


class BehaviorBatchCreate(BaseModel):
    """批量打分：给多名学生应用同一个规则/同一个分数"""
    student_ids: list[int] = Field(min_length=1, max_length=200)
    score_rule_id: int | None = None
    score: int | None = Field(default=None, ge=-100, le=100)
    category: str | None = Field(default=None, max_length=20)
    reason: str = Field(default="", max_length=200)


class BehaviorBatchOut(BaseModel):
    """批量打分结果：每个学生处理后的最新状态 + 升级总数"""
    results: list[BehaviorWithPetOut]
    total_students: int
    total_leveled_up: int
