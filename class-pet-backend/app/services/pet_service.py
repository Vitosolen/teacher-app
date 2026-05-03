"""核心业务规则：行为分 → 宠物属性换算、衰减、升级"""
from dataclasses import dataclass
from datetime import datetime

from app.models.pet import Pet


# 业务规则常量（集中在这里方便后续调参）
DECAY_PER_DAY_HUNGER = 5   # 每 24 小时饥饿度衰减
DECAY_PER_DAY_MOOD = 5     # 每 24 小时心情衰减
EXP_PER_POSITIVE_SCORE = 10
MOOD_GAIN_PER_POSITIVE = 5
HUNGER_GAIN_PER_POSITIVE = 3
MOOD_LOSS_PER_NEGATIVE = 5  # 注意：负向时 score 已是负数，直接相乘
HUNGER_LOSS_PER_NEGATIVE = 2


@dataclass
class ApplyResult:
    """应用行为后的结果"""
    leveled_up: bool
    levels_gained: int


def _clamp(value: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, value))


def exp_threshold(level: int) -> int:
    """level 升到 level+1 需要的经验值"""
    return level * 100


def derive_status(pet: Pet) -> str:
    """派生状态（前端展示用，不入库）"""
    if pet.hunger <= 10 or pet.mood <= 10:
        return "虚弱"
    if pet.hunger <= 30:
        return "饥饿"
    if pet.mood <= 30:
        return "难过"
    return "健康"


def apply_decay(pet: Pet, *, now: datetime | None = None) -> None:
    """根据 last_updated_at 与现在的差值，应用饥饿/心情衰减（懒计算）

    每 24 小时各扣 5 点，封顶不低于 0；同时刷新 last_updated_at。
    """
    now = now or datetime.utcnow()
    elapsed = now - pet.last_updated_at
    days = int(elapsed.total_seconds() // 86400)
    if days <= 0:
        return
    pet.hunger = _clamp(pet.hunger - DECAY_PER_DAY_HUNGER * days)
    pet.mood = _clamp(pet.mood - DECAY_PER_DAY_MOOD * days)
    pet.last_updated_at = now


def apply_behavior(pet: Pet, score: int, *, now: datetime | None = None) -> ApplyResult:
    """应用一次行为分到宠物属性上，返回升级信息

    加分（score > 0，奖励）：经验、心情、饥饿都加
    减分（score < 0，惩罚）：心情、饥饿降低，不扣经验
    分数为 0：no-op
    """
    now = now or datetime.utcnow()
    # 先跑衰减
    apply_decay(pet, now=now)

    if score > 0:
        pet.exp += score * EXP_PER_POSITIVE_SCORE
        pet.mood = _clamp(pet.mood + score * MOOD_GAIN_PER_POSITIVE)
        pet.hunger = _clamp(pet.hunger + score * HUNGER_GAIN_PER_POSITIVE)
    elif score < 0:
        # score 为负数，直接乘以正系数即可得到负向变化
        pet.mood = _clamp(pet.mood + score * MOOD_LOSS_PER_NEGATIVE)
        pet.hunger = _clamp(pet.hunger + score * HUNGER_LOSS_PER_NEGATIVE)

    levels_gained = _process_level_up(pet)
    pet.last_updated_at = now
    return ApplyResult(leveled_up=levels_gained > 0, levels_gained=levels_gained)


def _process_level_up(pet: Pet) -> int:
    """根据当前 exp 进行升级，返回升的级数（可一次升多级）"""
    levels = 0
    while pet.exp >= exp_threshold(pet.level):
        pet.exp -= exp_threshold(pet.level)
        pet.level += 1
        levels += 1
        # 极端情况防御：避免错配数据导致死循环
        if levels > 100:
            break
    return levels
