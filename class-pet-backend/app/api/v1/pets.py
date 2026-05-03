"""宠物：查询 + 改名（读取时自动跑衰减）"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_teacher
from app.models.pet import Pet
from app.models.teacher import Teacher
from app.schemas.pet import PetOut, PetUpdate
from app.services.pet_service import apply_decay, derive_status, exp_threshold

router = APIRouter(prefix="/pets", tags=["pets"])


def _ensure_pet_owned(db: Session, pet_id: int, teacher_id: int) -> Pet:
    pet = db.get(Pet, pet_id)
    if pet is None:
        raise HTTPException(status_code=404, detail="宠物不存在")
    # 通过学生关联查老师
    if pet.student.class_.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="无权操作他人宠物")
    return pet


def _pet_to_out(pet: Pet) -> PetOut:
    out = PetOut.model_validate(pet)
    out.status = derive_status(pet)
    out.exp_to_next_level = exp_threshold(pet.level)
    return out


@router.get("/{pet_id}", response_model=PetOut)
def get_pet(
    pet_id: int,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """读取宠物（先跑衰减再返回，保证状态新鲜）"""
    pet = _ensure_pet_owned(db, pet_id, current.id)
    apply_decay(pet)
    db.commit()
    db.refresh(pet)
    return _pet_to_out(pet)


@router.patch("/{pet_id}", response_model=PetOut)
def rename_pet(
    pet_id: int,
    payload: PetUpdate,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """给宠物改名"""
    pet = _ensure_pet_owned(db, pet_id, current.id)
    pet.name = payload.name
    db.commit()
    db.refresh(pet)
    return _pet_to_out(pet)
