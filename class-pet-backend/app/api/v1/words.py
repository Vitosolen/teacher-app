"""单词词库 + 单词管理（按老师隔离）

听写流程在前端用 Web Speech API 实现，后端只提供 CRUD 与批量导入。
"""
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_db, get_current_teacher
from app.models.teacher import Teacher
from app.models.word import Word
from app.models.word_group import WordGroup
from app.schemas.word import (
    WordCreate, WordUpdate, WordBatchCreate, WordOut,
    WordGroupCreate, WordGroupUpdate, WordGroupOut, WordGroupDetailOut,
)

router = APIRouter(tags=["words"])


# ----- 内部 -----

def _ensure_group_owned(db: Session, group_id: int, teacher_id: int) -> WordGroup:
    g = db.get(WordGroup, group_id)
    if g is None:
        raise HTTPException(status_code=404, detail="词库不存在")
    if g.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="无权操作他人词库")
    return g


def _ensure_word_owned(db: Session, word_id: int, teacher_id: int) -> Word:
    w = db.get(Word, word_id)
    if w is None:
        raise HTTPException(status_code=404, detail="单词不存在")
    if w.group.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="无权操作他人单词")
    return w


def _to_group_out(db: Session, g: WordGroup) -> WordGroupOut:
    cnt = db.query(func.count(Word.id)).filter(Word.group_id == g.id).scalar() or 0
    out = WordGroupOut.model_validate(g)
    out.word_count = int(cnt)
    return out


# ----- 词库（分组）-----

@router.get("/word-groups", response_model=list[WordGroupOut])
def list_groups(
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    groups = (
        db.query(WordGroup)
        .filter(WordGroup.teacher_id == current.id)
        .order_by(WordGroup.sort_order.asc(), WordGroup.created_at.desc())
        .all()
    )
    return [_to_group_out(db, g) for g in groups]


@router.post("/word-groups", response_model=WordGroupOut, status_code=status.HTTP_201_CREATED)
def create_group(
    payload: WordGroupCreate,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    g = WordGroup(
        teacher_id=current.id,
        name=payload.name,
        description=payload.description,
        lang=payload.lang,
        sort_order=payload.sort_order,
    )
    db.add(g)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"词库「{payload.name}」已存在")
    db.refresh(g)
    return _to_group_out(db, g)


@router.get("/word-groups/{group_id}", response_model=WordGroupDetailOut)
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    g = _ensure_group_owned(db, group_id, current.id)
    words = (
        db.query(Word)
        .filter(Word.group_id == group_id)
        .order_by(Word.sort_order.asc(), Word.id.asc())
        .all()
    )
    base = _to_group_out(db, g)
    return WordGroupDetailOut(
        **base.model_dump(),
        words=[WordOut.model_validate(w) for w in words],
    )


@router.patch("/word-groups/{group_id}", response_model=WordGroupOut)
def update_group(
    group_id: int,
    payload: WordGroupUpdate,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    g = _ensure_group_owned(db, group_id, current.id)
    if payload.name is not None:
        g.name = payload.name
    if payload.description is not None:
        g.description = payload.description
    if payload.lang is not None:
        g.lang = payload.lang
    if payload.sort_order is not None:
        g.sort_order = payload.sort_order
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="词库名重复")
    db.refresh(g)
    return _to_group_out(db, g)


@router.delete("/word-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    g = _ensure_group_owned(db, group_id, current.id)
    db.delete(g)
    db.commit()


# ----- 单词 -----

@router.post(
    "/word-groups/{group_id}/words",
    response_model=WordOut,
    status_code=status.HTTP_201_CREATED,
)
def create_word(
    group_id: int,
    payload: WordCreate,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    _ensure_group_owned(db, group_id, current.id)
    w = Word(
        group_id=group_id,
        text=payload.text,
        translation=payload.translation,
        sort_order=payload.sort_order,
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return w


@router.post(
    "/word-groups/{group_id}/words/batch",
    response_model=list[WordOut],
    status_code=status.HTTP_201_CREATED,
)
def batch_create_words(
    group_id: int,
    payload: WordBatchCreate,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """批量导入：每行一条，可空格/制表/逗号分隔单词与释义。

    支持格式：
      apple              → text=apple, translation=""
      apple 苹果         → text=apple, translation=苹果
      apple,苹果         → text=apple, translation=苹果
      apple\t苹果        → text=apple, translation=苹果
    """
    _ensure_group_owned(db, group_id, current.id)
    # 当前最大排序，新词追加在末尾
    base_order = (
        db.query(func.max(Word.sort_order)).filter(Word.group_id == group_id).scalar() or 0
    )
    created: list[Word] = []
    for idx, raw in enumerate(payload.lines):
        line = (raw or "").strip()
        if not line:
            continue
        # 用第一个分隔符（空白/逗号/制表）切两段
        parts = re.split(r"[\s,，\t]+", line, maxsplit=1)
        text = parts[0].strip()
        translation = parts[1].strip() if len(parts) > 1 else ""
        if not text:
            continue
        w = Word(
            group_id=group_id, text=text, translation=translation,
            sort_order=base_order + idx + 1,
        )
        db.add(w)
        created.append(w)
    db.commit()
    for w in created:
        db.refresh(w)
    return created


@router.patch("/words/{word_id}", response_model=WordOut)
def update_word(
    word_id: int,
    payload: WordUpdate,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    w = _ensure_word_owned(db, word_id, current.id)
    if payload.text is not None:
        w.text = payload.text
    if payload.translation is not None:
        w.translation = payload.translation
    if payload.sort_order is not None:
        w.sort_order = payload.sort_order
    db.commit()
    db.refresh(w)
    return w


@router.delete("/words/{word_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_word(
    word_id: int,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    w = _ensure_word_owned(db, word_id, current.id)
    db.delete(w)
    db.commit()
