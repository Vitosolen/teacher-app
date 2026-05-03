"""科目管理（按老师隔离）"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_teacher
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectOut

router = APIRouter(prefix="/subjects", tags=["subjects"])


def _ensure_owned(db: Session, subject_id: int, teacher_id: int) -> Subject:
    s = db.get(Subject, subject_id)
    if s is None:
        raise HTTPException(status_code=404, detail="科目不存在")
    if s.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="无权操作他人科目")
    return s


@router.get("", response_model=list[SubjectOut])
def list_subjects(
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """列出当前老师的所有科目"""
    return (
        db.query(Subject)
        .filter(Subject.teacher_id == current.id)
        .order_by(Subject.sort_order.asc(), Subject.created_at.asc())
        .all()
    )


@router.post("", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
def create_subject(
    payload: SubjectCreate,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """新建科目（同老师下名字唯一）"""
    s = Subject(
        teacher_id=current.id,
        name=payload.name,
        color=payload.color,
        sort_order=payload.sort_order,
    )
    db.add(s)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"科目「{payload.name}」已存在")
    db.refresh(s)
    return s


@router.patch("/{subject_id}", response_model=SubjectOut)
def update_subject(
    subject_id: int,
    payload: SubjectUpdate,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """编辑科目"""
    s = _ensure_owned(db, subject_id, current.id)
    if payload.name is not None:
        s.name = payload.name
    if payload.color is not None:
        s.color = payload.color
    if payload.sort_order is not None:
        s.sort_order = payload.sort_order
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="科目名重复")
    db.refresh(s)
    return s


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """删除科目（连带该科目下作业）"""
    s = _ensure_owned(db, subject_id, current.id)
    db.delete(s)
    db.commit()
