"""商城与宠物物品请求/响应模型"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ShopItemOut(BaseModel):
    id: int
    name: str
    item_type: str          # 衣服/食品/玩具
    price: int
    icon: str
    description: str
    effect_hunger: int
    effect_mood: int
    consumable: bool
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class RedeemPayload(BaseModel):
    student_id: int


class OwnedItemOut(BaseModel):
    id: int
    pet_id: int
    shop_item_id: int
    # 业务层 _to_owned_out 填充。设默认值便于 model_validate 时缺字段不报错。
    item: ShopItemOut | None = None
    equipped: bool
    acquired_at: datetime
    consumed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class RedeemResultOut(BaseModel):
    """兑换结果：返回最新积分余额 + 新拥有的物品"""
    student_points: int
    owned_item: OwnedItemOut


class ConsumeResultOut(BaseModel):
    """食用/玩耍结果：返回宠物最新属性"""
    pet_id: int
    hunger: int
    mood: int
    owned_item_id: int
