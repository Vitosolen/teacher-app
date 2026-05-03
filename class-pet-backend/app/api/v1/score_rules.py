"""积分规则管理（替代硬编码预设按钮，按老师隔离）"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_teacher
from app.models.score_rule import ScoreRule
from app.models.teacher import Teacher
from app.schemas.score_rule import ScoreRuleCreate, ScoreRuleUpdate, ScoreRuleOut

router = APIRouter(prefix="/score-rules", tags=["score-rules"])


def _ensure_owned(db: Session, rule_id: int, teacher_id: int) -> ScoreRule:
    r = db.get(ScoreRule, rule_id)
    if r is None:
        raise HTTPException(status_code=404, detail="规则不存在")
    if r.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="无权操作他人规则")
    return r


@router.get("", response_model=list[ScoreRuleOut])
def list_rules(
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """列出当前老师的所有积分规则（含已禁用）"""
    return (
        db.query(ScoreRule)
        .filter(ScoreRule.teacher_id == current.id)
        .order_by(ScoreRule.sort_order.asc(), ScoreRule.id.asc())
        .all()
    )


@router.post("", response_model=ScoreRuleOut, status_code=status.HTTP_201_CREATED)
def create_rule(
    payload: ScoreRuleCreate,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    r = ScoreRule(
        teacher_id=current.id,
        label=payload.label,
        category=payload.category,
        score=payload.score,
        sort_order=payload.sort_order,
        active=payload.active,
    )
    db.add(r)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"规则「{payload.label}」已存在")
    db.refresh(r)
    return r


@router.patch("/{rule_id}", response_model=ScoreRuleOut)
def update_rule(
    rule_id: int,
    payload: ScoreRuleUpdate,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    r = _ensure_owned(db, rule_id, current.id)
    if payload.label is not None:
        r.label = payload.label
    if payload.category is not None:
        r.category = payload.category
    if payload.score is not None:
        r.score = payload.score
    if payload.sort_order is not None:
        r.sort_order = payload.sort_order
    if payload.active is not None:
        r.active = payload.active
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="规则名重复")
    db.refresh(r)
    return r


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    r = _ensure_owned(db, rule_id, current.id)
    db.delete(r)
    db.commit()
