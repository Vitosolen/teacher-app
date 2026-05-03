"""宠物拥有的物品（兑换历史 + 当前装备/消耗状态）"""
from datetime import datetime

from sqlalchemy import DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PetOwnedItem(Base):
    __tablename__ = "pet_owned_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pet_id: Mapped[int] = mapped_column(
        ForeignKey("pets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    shop_item_id: Mapped[int] = mapped_column(
        ForeignKey("shop_items.id", ondelete="RESTRICT"), nullable=False
    )
    equipped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # 仅衣服用
    acquired_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)   # 食品/玩具消耗时间

    # 关联：方便取商品定义
    shop_item: Mapped["ShopItem"] = relationship()  # type: ignore  # noqa: F821
