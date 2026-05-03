"""行为：核心写入接口（事务内同时更新宠物属性 + 累加学生积分）"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_teacher
from app.models.behavior import Behavior
from app.models.score_rule import ScoreRule
from app.models.student import Student
from app.models.teacher import Teacher
from app.schemas.behavior import (
    BehaviorCreate, BehaviorUpdate, BehaviorOut, BehaviorWithPetOut, VALID_CATEGORIES,
    BehaviorBatchCreate, BehaviorBatchOut,
)
from app.schemas.pet import PetOut
from app.services.pet_service import apply_behavior, derive_status, exp_threshold

router = APIRouter(tags=["behaviors"])


def _resolve_score_args(
    db: Session,
    teacher_id: int,
    score_rule_id: int | None,
    score: int | None,
    category: str | None,
    reason: str,
) -> tuple[int, str, str, int | None]:
    """根据请求字段解析最终的 (score, category, reason, rule_id)。

    走 score_rule_id 路径时校验规则归属与 active 状态；
    走自定义路径时校验 score+category 必填且 category 合法。
    """
    if score_rule_id is not None:
        rule = db.get(ScoreRule, score_rule_id)
        if rule is None:
            raise HTTPException(status_code=404, detail="积分规则不存在")
        if rule.teacher_id != teacher_id:
            raise HTTPException(status_code=403, detail="无权使用他人规则")
        if not rule.active:
            raise HTTPException(status_code=400, detail="该规则已停用")
        return rule.score, rule.category, (reason or rule.label), rule.id
    if score is None or category is None:
        raise HTTPException(
            status_code=400,
            detail="未提供 score_rule_id 时必须填写 score 和 category",
        )
    if category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"category 必须是以下之一：{VALID_CATEGORIES}",
        )
    return score, category, reason, None


def _apply_score_to_student(
    db: Session,
    student: Student,
    teacher_id: int,
    score: int,
    category: str,
    reason: str,
    rule_id: int | None,
) -> BehaviorWithPetOut:
    """对单个学生应用一次打分，返回最新状态。调用方负责 db.commit()。"""
    if student.pet is None:
        raise HTTPException(status_code=500, detail=f"{student.name} 没有关联宠物（数据异常）")

    result = apply_behavior(student.pet, score)
    if score > 0:
        student.points = (student.points or 0) + score

    behavior = Behavior(
        student_id=student.id,
        teacher_id=teacher_id,
        score=score,
        category=category,
        reason=reason,
        score_rule_id=rule_id,
    )
    db.add(behavior)
    db.flush()  # 拿到 behavior.id

    pet_out = PetOut.model_validate(student.pet)
    pet_out.status = derive_status(student.pet)
    pet_out.exp_to_next_level = exp_threshold(student.pet.level)
    return BehaviorWithPetOut(
        behavior=BehaviorOut.model_validate(behavior),
        pet=pet_out,
        student_points=student.points,
        leveled_up=result.leveled_up,
        levels_gained=result.levels_gained,
    )


@router.post(
    "/behaviors",
    response_model=BehaviorWithPetOut,
    status_code=status.HTTP_201_CREATED,
)
def create_behavior(
    payload: BehaviorCreate,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """记录一次行为，事务内：写记录 → 跑衰减 → 应用换算 → 升级 → 累加积分余额 → 返回最新状态"""
    score, category, reason, rule_id = _resolve_score_args(
        db, current.id, payload.score_rule_id, payload.score, payload.category, payload.reason,
    )
    student = db.get(Student, payload.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    if student.class_.teacher_id != current.id:
        raise HTTPException(status_code=403, detail="无权对他人学生评分")

    out = _apply_score_to_student(db, student, current.id, score, category, reason, rule_id)
    db.commit()
    db.refresh(student)
    return out


@router.post(
    "/behaviors/batch",
    response_model=BehaviorBatchOut,
    status_code=status.HTTP_201_CREATED,
)
def batch_create_behavior(
    payload: BehaviorBatchCreate,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """批量打分：一次事务给多名学生应用同一规则/分数。
    任一学生不属于当前老师 → 整体回滚。"""
    score, category, reason, rule_id = _resolve_score_args(
        db, current.id, payload.score_rule_id, payload.score, payload.category, payload.reason,
    )
    if not payload.student_ids:
        raise HTTPException(status_code=400, detail="学生列表不能为空")

    students = (
        db.query(Student)
        .filter(Student.id.in_(payload.student_ids))
        .all()
    )
    found_ids = {s.id for s in students}
    missing = set(payload.student_ids) - found_ids
    if missing:
        raise HTTPException(status_code=404, detail=f"以下学生不存在：{sorted(missing)}")
    for s in students:
        if s.class_.teacher_id != current.id:
            raise HTTPException(status_code=403, detail=f"无权对学生「{s.name}」评分")

    # 保持调用方传入顺序
    by_id = {s.id: s for s in students}
    ordered = [by_id[i] for i in payload.student_ids]

    results: list[BehaviorWithPetOut] = []
    leveled_up_count = 0
    for student in ordered:
        out = _apply_score_to_student(db, student, current.id, score, category, reason, rule_id)
        if out.leveled_up:
            leveled_up_count += 1
        results.append(out)
    db.commit()
    return BehaviorBatchOut(
        results=results,
        total_students=len(results),
        total_leveled_up=leveled_up_count,
    )


def _ensure_behavior_owned(db: Session, behavior_id: int, teacher_id: int) -> Behavior:
    b = db.get(Behavior, behavior_id)
    if b is None:
        raise HTTPException(status_code=404, detail="行为记录不存在")
    if b.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="无权操作他人的行为记录")
    return b


@router.patch("/behaviors/{behavior_id}", response_model=BehaviorOut)
def update_behavior(
    behavior_id: int,
    payload: BehaviorUpdate,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """编辑行为记录（仅 category / reason，不允许改分数避免回滚宠物属性）"""
    b = _ensure_behavior_owned(db, behavior_id, current.id)
    if payload.category is not None:
        if payload.category not in VALID_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"category 必须是以下之一：{VALID_CATEGORIES}",
            )
        b.category = payload.category
    if payload.reason is not None:
        b.reason = payload.reason
    db.commit()
    db.refresh(b)
    return b


@router.delete("/behaviors/{behavior_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_behavior(
    behavior_id: int,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """删除行为记录。
    - 若原 score > 0：从 student.points 扣回该分数（保底 0）—— 让"误打加分"可撤销
    - 不回滚宠物 exp/mood/hunger/level：因后续可能已发生衰减/升级，无法精确还原
    """
    b = _ensure_behavior_owned(db, behavior_id, current.id)
    if b.score > 0:
        student = db.get(Student, b.student_id)
        if student is not None:
            student.points = max(0, (student.points or 0) - b.score)
    db.delete(b)
    db.commit()


@router.get("/students/{student_id}/behaviors", response_model=list[BehaviorOut])
def list_student_behaviors(
    student_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """获取某学生最近 N 条行为记录（默认 50 条，倒序）"""
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    if student.class_.teacher_id != current.id:
        raise HTTPException(status_code=403, detail="无权查看他人学生记录")
    behaviors = (
        db.query(Behavior)
        .filter(Behavior.student_id == student_id)
        .order_by(Behavior.created_at.desc())
        .limit(limit)
        .all()
    )
    return behaviors
