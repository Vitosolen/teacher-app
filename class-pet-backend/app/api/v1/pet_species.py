"""宠物物种 + 等级资源 CRUD（全局共享，所有登录老师可读，可写）+ 图片上传

注意：物种是全局资源，没有 teacher_id 隔离 —— 任何老师都能改。
后续若需要权限分级（如管理员独占），加 role 字段判断。
"""
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_db, get_current_teacher
from app.models.pet_species import PetSpecies, PetSpeciesAsset
from app.models.teacher import Teacher
from app.schemas.pet_species import (
    SpeciesCreate, SpeciesUpdate, SpeciesOut,
    AssetCreate, AssetUpdate, AssetOut,
)

# 上传约束
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB（可放大到任意值；超过会消耗内存，建议 ≤ 50MB）

# 静态目录与 main.py 中 mount 一致
STATIC_PETS_DIR = Path(__file__).resolve().parents[3] / "static" / "pets"

router = APIRouter(prefix="/pet-species", tags=["pet-species"])


# —— 内部 ——

def _get_species_or_404(db: Session, species_id: int) -> PetSpecies:
    s = db.get(PetSpecies, species_id)
    if s is None:
        raise HTTPException(status_code=404, detail="物种不存在")
    return s


def _get_asset_or_404(db: Session, asset_id: int) -> PetSpeciesAsset:
    a = db.get(PetSpeciesAsset, asset_id)
    if a is None:
        raise HTTPException(status_code=404, detail="资源不存在")
    return a


# —— 物种 ——

@router.get("", response_model=list[SpeciesOut])
def list_species(
    db: Session = Depends(get_db),
    _: Teacher = Depends(get_current_teacher),
):
    """列出所有物种 + 各等级资源（前端按 level 算 fallback）"""
    rows = (
        db.query(PetSpecies)
        .options(selectinload(PetSpecies.assets))
        .order_by(PetSpecies.sort_order.asc(), PetSpecies.id.asc())
        .all()
    )
    # 让 assets 按 level 升序输出
    for s in rows:
        s.assets.sort(key=lambda a: a.level)
    return rows


@router.post("", response_model=SpeciesOut, status_code=status.HTTP_201_CREATED)
def create_species(
    payload: SpeciesCreate,
    db: Session = Depends(get_db),
    _: Teacher = Depends(get_current_teacher),
):
    s = PetSpecies(
        code=payload.code, name=payload.name,
        description=payload.description, sort_order=payload.sort_order,
    )
    db.add(s)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"code「{payload.code}」已存在")
    db.refresh(s)
    return s


@router.patch("/{species_id}", response_model=SpeciesOut)
def update_species(
    species_id: int,
    payload: SpeciesUpdate,
    db: Session = Depends(get_db),
    _: Teacher = Depends(get_current_teacher),
):
    s = _get_species_or_404(db, species_id)
    if payload.name is not None: s.name = payload.name
    if payload.description is not None: s.description = payload.description
    if payload.sort_order is not None: s.sort_order = payload.sort_order
    db.commit()
    db.refresh(s)
    return s


@router.delete("/{species_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_species(
    species_id: int,
    db: Session = Depends(get_db),
    _: Teacher = Depends(get_current_teacher),
):
    """删除物种（连带删 assets）。不影响存量 student.pet.species 字段值，
    只是显示时找不到资源会走兜底 emoji。"""
    s = _get_species_or_404(db, species_id)
    db.delete(s)
    db.commit()


# —— 资源（等级 emoji / image_url）——

@router.post("/{species_id}/assets", response_model=AssetOut, status_code=status.HTTP_201_CREATED)
def create_asset(
    species_id: int,
    payload: AssetCreate,
    db: Session = Depends(get_db),
    _: Teacher = Depends(get_current_teacher),
):
    """新增等级资源。同 (species_id, level) 已存在时返回 400（请用 PATCH 更新）"""
    _get_species_or_404(db, species_id)
    a = PetSpeciesAsset(
        species_id=species_id, level=payload.level,
        emoji=payload.emoji, image_url=payload.image_url,
    )
    db.add(a)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"等级 {payload.level} 已存在，请编辑或删除原条目")
    db.refresh(a)
    return a


@router.patch("/{species_id}/assets/{asset_id}", response_model=AssetOut)
def update_asset(
    species_id: int,
    asset_id: int,
    payload: AssetUpdate,
    db: Session = Depends(get_db),
    _: Teacher = Depends(get_current_teacher),
):
    a = _get_asset_or_404(db, asset_id)
    if a.species_id != species_id:
        raise HTTPException(status_code=400, detail="资源不属于该物种")
    if payload.emoji is not None: a.emoji = payload.emoji
    if payload.image_url is not None: a.image_url = payload.image_url
    db.commit()
    db.refresh(a)
    return a


@router.delete("/{species_id}/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    species_id: int,
    asset_id: int,
    db: Session = Depends(get_db),
    _: Teacher = Depends(get_current_teacher),
):
    a = _get_asset_or_404(db, asset_id)
    if a.species_id != species_id:
        raise HTTPException(status_code=400, detail="资源不属于该物种")
    db.delete(a)
    db.commit()


@router.post("/{species_id}/assets/{asset_id}/upload", response_model=AssetOut)
async def upload_asset_image(
    species_id: int,
    asset_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: Teacher = Depends(get_current_teacher),
):
    """上传图片到该等级资源。
    - 支持 png/jpg/webp/gif，最大 2MB
    - 文件保存到 static/pets/<species>_lv<level>_<ts>.<ext>
    - asset.image_url 自动更新为 /static/pets/<filename>
    - 旧图片不会自动删除（保留在磁盘，避免覆盖时浏览器仍持有缓存导致 404）
    """
    a = _get_asset_or_404(db, asset_id)
    if a.species_id != species_id:
        raise HTTPException(status_code=400, detail="资源不属于该物种")
    species = _get_species_or_404(db, species_id)

    # 类型校验（不信任客户端 filename，按 content-type 推断扩展名）
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型 {content_type}，只接受 PNG/JPG/WEBP/GIF",
        )
    ext_map = {
        "image/png": ".png", "image/jpeg": ".jpg",
        "image/webp": ".webp", "image/gif": ".gif",
    }
    ext = ext_map[content_type]

    # 大小校验：超限早停
    body = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(body) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"文件超过 {MAX_UPLOAD_BYTES // 1024 // 1024} MB 上限",
        )
    if len(body) == 0:
        raise HTTPException(status_code=400, detail="文件为空")

    # 写盘：时间戳防缓存 + 多次上传不互相覆盖
    STATIC_PETS_DIR.mkdir(parents=True, exist_ok=True)
    ts = int(time.time() * 1000)
    filename = f"{species.code}_lv{a.level}_{ts}{ext}"
    full_path = STATIC_PETS_DIR / filename
    full_path.write_bytes(body)

    # URL 路径与 main.py 的 mount("/static") 对齐
    a.image_url = f"/static/pets/{filename}"
    db.commit()
    db.refresh(a)
    return a
