"""商城：列商品、兑换、装备、食用"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_teacher
from app.models.pet import Pet
from app.models.pet_owned_item import PetOwnedItem
from app.models.shop_item import ShopItem
from app.models.student import Student
from app.models.teacher import Teacher
from app.schemas.shop import (
    ShopItemOut, RedeemPayload, OwnedItemOut,
    RedeemResultOut, ConsumeResultOut,
)
from app.services.pet_service import apply_decay, _clamp

router = APIRouter(tags=["shop"])


# ----- 内部 -----

def _ensure_pet_owned(db: Session, pet_id: int, teacher_id: int) -> Pet:
    pet = db.get(Pet, pet_id)
    if pet is None:
        raise HTTPException(status_code=404, detail="宠物不存在")
    student = db.get(Student, pet.student_id)
    if student is None or student.class_.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="无权操作他人宠物")
    return pet


def _to_owned_out(rec: PetOwnedItem) -> OwnedItemOut:
    out = OwnedItemOut.model_validate(rec)
    out.item = ShopItemOut.model_validate(rec.shop_item)
    return out


# ----- 路由 -----

@router.get("/shop-items", response_model=list[ShopItemOut])
def list_shop_items(
    item_type: str | None = None,
    db: Session = Depends(get_db),
    _: Teacher = Depends(get_current_teacher),
):
    """全局商品列表，可按类型筛选（衣服/食品/玩具）"""
    q = db.query(ShopItem)
    if item_type:
        q = q.filter(ShopItem.item_type == item_type)
    return q.order_by(ShopItem.sort_order.asc()).all()


@router.post("/shop-items/{item_id}/redeem", response_model=RedeemResultOut)
def redeem(
    item_id: int,
    payload: RedeemPayload,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """学生用 points 兑换商品：扣 points → 加 owned_item"""
    item = db.get(ShopItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="商品不存在")
    student = db.get(Student, payload.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    if student.class_.teacher_id != current.id:
        raise HTTPException(status_code=403, detail="无权操作他人学生")
    if student.pet is None:
        raise HTTPException(status_code=500, detail="学生没有关联宠物")
    if (student.points or 0) < item.price:
        raise HTTPException(
            status_code=400,
            detail=f"积分不足：当前 {student.points or 0}，需要 {item.price}",
        )

    student.points = (student.points or 0) - item.price
    owned = PetOwnedItem(pet_id=student.pet.id, shop_item_id=item.id)
    db.add(owned)
    db.commit()
    db.refresh(student)
    db.refresh(owned)
    return RedeemResultOut(
        student_points=student.points,
        owned_item=_to_owned_out(owned),
    )


@router.get("/pets/{pet_id}/owned-items", response_model=list[OwnedItemOut])
def list_owned_items(
    pet_id: int,
    include_consumed: bool = False,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """宠物拥有的物品列表（默认隐藏已消耗）"""
    _ensure_pet_owned(db, pet_id, current.id)
    q = db.query(PetOwnedItem).filter(PetOwnedItem.pet_id == pet_id)
    if not include_consumed:
        q = q.filter(PetOwnedItem.consumed_at.is_(None))
    rows = q.order_by(PetOwnedItem.acquired_at.desc()).all()
    return [_to_owned_out(r) for r in rows]


# 装备规则：
# - 衣服 / 房子：同类互斥（同时只能装备 1 件，新装备自动卸下同类其他）
# - 家具：不互斥（可同时摆放多件作为装饰）
# - 食品 / 玩具：不可装备（应该用 consume 接口）
_EXCLUSIVE_TYPES = {"衣服", "房子"}
_EQUIPPABLE_TYPES = {"衣服", "房子", "家具"}


@router.post("/pets/{pet_id}/equip", response_model=list[OwnedItemOut])
def equip(
    pet_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """装备物品。衣服/房子互斥（同类自动替换），家具可多件并存。"""
    pet = _ensure_pet_owned(db, pet_id, current.id)
    owned_id = payload.get("owned_item_id")
    if not isinstance(owned_id, int):
        raise HTTPException(status_code=400, detail="缺少 owned_item_id")
    target = db.get(PetOwnedItem, owned_id)
    if target is None or target.pet_id != pet.id:
        raise HTTPException(status_code=404, detail="物品不属于该宠物")
    item_type = target.shop_item.item_type
    if item_type not in _EQUIPPABLE_TYPES:
        raise HTTPException(status_code=400, detail=f"{item_type}不可装备（请使用 consume 接口）")
    if target.consumed_at is not None:
        raise HTTPException(status_code=400, detail="物品已消耗")

    # 互斥类型：卸下同类其他已装备项
    if item_type in _EXCLUSIVE_TYPES:
        others = (
            db.query(PetOwnedItem)
            .join(PetOwnedItem.shop_item)
            .filter(
                PetOwnedItem.pet_id == pet.id,
                PetOwnedItem.equipped.is_(True),
            )
            .all()
        )
        for o in others:
            if o.id != target.id and o.shop_item.item_type == item_type:
                o.equipped = False
    target.equipped = True
    db.commit()

    rows = (
        db.query(PetOwnedItem)
        .filter(PetOwnedItem.pet_id == pet.id, PetOwnedItem.consumed_at.is_(None))
        .all()
    )
    return [_to_owned_out(r) for r in rows]


@router.post("/pets/{pet_id}/unequip", response_model=list[OwnedItemOut])
def unequip(
    pet_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """卸下衣服"""
    pet = _ensure_pet_owned(db, pet_id, current.id)
    owned_id = payload.get("owned_item_id")
    if not isinstance(owned_id, int):
        raise HTTPException(status_code=400, detail="缺少 owned_item_id")
    target = db.get(PetOwnedItem, owned_id)
    if target is None or target.pet_id != pet.id:
        raise HTTPException(status_code=404, detail="物品不属于该宠物")
    target.equipped = False
    db.commit()
    rows = (
        db.query(PetOwnedItem)
        .filter(PetOwnedItem.pet_id == pet.id, PetOwnedItem.consumed_at.is_(None))
        .all()
    )
    return [_to_owned_out(r) for r in rows]


@router.post("/pets/{pet_id}/consume", response_model=ConsumeResultOut)
def consume(
    pet_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """食用食品 / 玩耍玩具：应用 effect 后标记 consumed_at"""
    pet = _ensure_pet_owned(db, pet_id, current.id)
    owned_id = payload.get("owned_item_id")
    if not isinstance(owned_id, int):
        raise HTTPException(status_code=400, detail="缺少 owned_item_id")
    target = db.get(PetOwnedItem, owned_id)
    if target is None or target.pet_id != pet.id:
        raise HTTPException(status_code=404, detail="物品不属于该宠物")
    if target.consumed_at is not None:
        raise HTTPException(status_code=400, detail="物品已消耗")
    item = target.shop_item
    if not item.consumable:
        raise HTTPException(status_code=400, detail=f"{item.item_type}不可消耗")

    # 跑衰减再加 effect
    apply_decay(pet)
    pet.hunger = _clamp(pet.hunger + item.effect_hunger)
    pet.mood = _clamp(pet.mood + item.effect_mood)
    target.consumed_at = datetime.utcnow()
    pet.last_updated_at = datetime.utcnow()
    db.commit()
    db.refresh(pet)
    return ConsumeResultOut(
        pet_id=pet.id, hunger=pet.hunger, mood=pet.mood,
        owned_item_id=target.id,
    )
