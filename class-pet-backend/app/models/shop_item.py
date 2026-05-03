"""商品表（系统全局预置）

- 食品：消耗品，食用后增加 hunger/mood
- 衣服：可装备，仅装饰
- 玩具：消耗品，使用后增加 mood
"""
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ShopItem(Base):
    __tablename__ = "shop_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    item_type: Mapped[str] = mapped_column(String(10), nullable=False)   # 衣服/食品/玩具
    price: Mapped[int] = mapped_column(Integer, nullable=False)         # 兑换需要的积分
    icon: Mapped[str] = mapped_column(String(8), nullable=False, default="🎁")
    description: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    effect_hunger: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    effect_mood: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consumable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
