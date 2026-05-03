"""作业管理：创建作业（自动绑定全班学生 records）+ 批改打分点评"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_teacher
from app.models.class_ import Class
from app.models.homework import Homework
from app.models.homework_record import HomeworkRecord
from app.models.student import Student
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.schemas.homework import (
    HomeworkCreate, HomeworkOut, HomeworkDetailOut,
    HomeworkRecordOut, HomeworkRecordUpdate, HOMEWORK_TYPES,
)

# 订正阈值：批改作业时分数 < 此值自动判定需订正
# 业务规则：未达 A 等级（[85-100]）就视为有错需订正
CORRECTION_THRESHOLD = 85

router = APIRouter(tags=["homeworks"])


# ----- 内部工具 -----

def _ensure_homework_owned(db: Session, homework_id: int, teacher_id: int) -> Homework:
    hw = db.get(Homework, homework_id)
    if hw is None:
        raise HTTPException(status_code=404, detail="作业不存在")
    cls = db.get(Class, hw.class_id)
    if cls is None or cls.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="无权操作他人作业")
    return hw


def _ensure_record_owned(db: Session, record_id: int, teacher_id: int) -> HomeworkRecord:
    rec = db.get(HomeworkRecord, record_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="作业记录不存在")
    hw = db.get(Homework, rec.homework_id)
    cls = db.get(Class, hw.class_id) if hw else None
    if cls is None or cls.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="无权操作他人作业记录")
    return rec


def _to_homework_out(db: Session, hw: Homework) -> HomeworkOut:
    cls = db.get(Class, hw.class_id)
    sub = db.get(Subject, hw.subject_id)
    total, graded, pending_correct = db.query(
        func.count(HomeworkRecord.id),
        func.sum(case((HomeworkRecord.status == "已批改", 1), else_=0)),
        # 需订正且未订正：仅作业才有意义
        func.sum(case(
            (
                (HomeworkRecord.needs_correction.is_(True)) &
                (HomeworkRecord.corrected.is_(False)),
                1,
            ),
            else_=0,
        )),
    ).filter(HomeworkRecord.homework_id == hw.id).first() or (0, 0, 0)
    out = HomeworkOut.model_validate(hw)
    out.class_name = cls.name if cls else ""
    out.subject_name = sub.name if sub else ""
    out.subject_color = sub.color if sub else "#409EFF"
    out.total_count = int(total or 0)
    out.graded_count = int(graded or 0)
    out.correction_pending_count = int(pending_correct or 0)
    return out


# ----- 路由 -----

@router.get("/homeworks", response_model=list[HomeworkOut])
def list_homeworks(
    class_id: int | None = None,
    subject_id: int | None = None,
    type: str | None = None,  # homework / exam
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """列出作业/考试（可按班级/科目/类型过滤）。仅返回当前老师班级下的"""
    own_class_ids = [
        c.id for c in db.query(Class).filter(Class.teacher_id == current.id).all()
    ]
    if not own_class_ids:
        return []
    q = db.query(Homework).filter(Homework.class_id.in_(own_class_ids))
    if class_id is not None:
        if class_id not in own_class_ids:
            raise HTTPException(status_code=403, detail="无权查看他人班级")
        q = q.filter(Homework.class_id == class_id)
    if subject_id is not None:
        q = q.filter(Homework.subject_id == subject_id)
    if type is not None:
        if type not in HOMEWORK_TYPES:
            raise HTTPException(status_code=400, detail=f"type 必须是 {HOMEWORK_TYPES} 之一")
        q = q.filter(Homework.type == type)
    rows = q.order_by(Homework.created_at.desc()).all()
    return [_to_homework_out(db, hw) for hw in rows]


@router.post("/homeworks", response_model=HomeworkOut, status_code=status.HTTP_201_CREATED)
def create_homework(
    payload: HomeworkCreate,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """创建作业 → 自动为班内每个学生建一条 homework_record"""
    cls = db.get(Class, payload.class_id)
    if cls is None or cls.teacher_id != current.id:
        raise HTTPException(status_code=403, detail="无权操作他人班级")
    sub = db.get(Subject, payload.subject_id)
    if sub is None or sub.teacher_id != current.id:
        raise HTTPException(status_code=403, detail="科目不存在或无权使用")

    if payload.type not in HOMEWORK_TYPES:
        raise HTTPException(status_code=400, detail=f"type 必须是 {HOMEWORK_TYPES} 之一")
    hw = Homework(
        class_id=payload.class_id,
        subject_id=payload.subject_id,
        type=payload.type,
        title=payload.title,
        content=payload.content,
        due_date=payload.due_date,
    )
    db.add(hw)
    db.flush()  # 拿到 hw.id

    # 自动绑定班级所有学生
    students = db.query(Student).filter(Student.class_id == payload.class_id).all()
    for s in students:
        db.add(HomeworkRecord(
            homework_id=hw.id, student_id=s.id, status="未提交", comment="",
        ))
    db.commit()
    db.refresh(hw)
    return _to_homework_out(db, hw)


@router.get("/homeworks/{homework_id}", response_model=HomeworkDetailOut)
def get_homework(
    homework_id: int,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """作业详情 + 全部学生 records（含学生姓名学号，便于前端表格直接渲染）"""
    hw = _ensure_homework_owned(db, homework_id, current.id)
    base = _to_homework_out(db, hw)
    # 拼装 records + 学生信息
    records = (
        db.query(HomeworkRecord, Student)
        .join(Student, Student.id == HomeworkRecord.student_id)
        .filter(HomeworkRecord.homework_id == homework_id)
        .order_by(Student.created_at.asc())
        .all()
    )
    rec_outs: list[HomeworkRecordOut] = []
    for rec, stu in records:
        ro = HomeworkRecordOut.model_validate(rec)
        ro.student_name = stu.name
        ro.student_no = stu.student_no
        rec_outs.append(ro)
    return HomeworkDetailOut(
        **base.model_dump(),
        records=rec_outs,
    )


@router.post(
    "/homeworks/{homework_id}/records",
    response_model=list[HomeworkRecordOut],
    status_code=status.HTTP_201_CREATED,
)
def add_homework_records(
    homework_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """给已有作业批量追加学生记录（中途新增学生时补绑）。

    请求体：{ "student_ids": [1, 2, 3] }
    - 必须是该作业所属班级的学生
    - 已有 record 的学生自动跳过（幂等）
    - 返回这次新建的 records 列表
    """
    hw = _ensure_homework_owned(db, homework_id, current.id)
    student_ids = payload.get("student_ids") or []
    if not isinstance(student_ids, list) or not student_ids:
        raise HTTPException(status_code=400, detail="student_ids 不能为空")

    students = (
        db.query(Student)
        .filter(Student.id.in_(student_ids), Student.class_id == hw.class_id)
        .all()
    )
    if len(students) != len(set(student_ids)):
        raise HTTPException(status_code=400, detail="存在不属于该作业班级的学生")

    existing = {
        r.student_id for r in db.query(HomeworkRecord).filter(
            HomeworkRecord.homework_id == homework_id,
            HomeworkRecord.student_id.in_(student_ids),
        ).all()
    }
    new_records: list[HomeworkRecord] = []
    for s in students:
        if s.id in existing:
            continue
        rec = HomeworkRecord(homework_id=homework_id, student_id=s.id, status="未提交", comment="")
        db.add(rec)
        new_records.append(rec)
    db.commit()
    for r in new_records:
        db.refresh(r)
    by_id = {s.id: s for s in students}
    out: list[HomeworkRecordOut] = []
    for rec in new_records:
        ro = HomeworkRecordOut.model_validate(rec)
        s = by_id.get(rec.student_id)
        if s:
            ro.student_name = s.name
            ro.student_no = s.student_no
        out.append(ro)
    return out


@router.delete("/homeworks/{homework_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_homework(
    homework_id: int,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    hw = _ensure_homework_owned(db, homework_id, current.id)
    db.delete(hw)
    db.commit()


@router.get("/students/{student_id}/scores")
def list_student_scores(
    student_id: int,
    subject_id: int | None = None,
    type: str | None = None,    # homework / exam / None=both
    limit: int = 100,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """学生历次成绩聚合（用于趋势分析）

    返回按 scored_at 升序的列表（便于前端从左到右画折线）。
    仅返回已批改（有分数）的记录。
    """
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    if student.class_.teacher_id != current.id:
        raise HTTPException(status_code=403, detail="无权查看他人学生记录")

    q = (
        db.query(HomeworkRecord, Homework, Subject)
        .join(Homework, Homework.id == HomeworkRecord.homework_id)
        .join(Subject, Subject.id == Homework.subject_id)
        .filter(
            HomeworkRecord.student_id == student_id,
            HomeworkRecord.score.isnot(None),
        )
    )
    if subject_id is not None:
        q = q.filter(Homework.subject_id == subject_id)
    if type is not None:
        if type not in HOMEWORK_TYPES:
            raise HTTPException(status_code=400, detail=f"type 必须是 {HOMEWORK_TYPES} 之一")
        q = q.filter(Homework.type == type)
    rows = q.order_by(HomeworkRecord.scored_at.asc().nulls_last(), HomeworkRecord.id.asc()).limit(limit).all()

    return [
        {
            "record_id": rec.id,
            "homework_id": hw.id,
            "homework_title": hw.title,
            "homework_type": hw.type,
            "subject_id": sub.id,
            "subject_name": sub.name,
            "subject_color": sub.color,
            "score": rec.score,
            "status": rec.status,
            "needs_correction": rec.needs_correction,
            "corrected": rec.corrected,
            "scored_at": rec.scored_at.isoformat() if rec.scored_at else None,
            "comment": rec.comment,
        }
        for rec, hw, sub in rows
    ]


@router.patch("/homework-records/{record_id}", response_model=HomeworkRecordOut)
def update_homework_record(
    record_id: int,
    payload: HomeworkRecordUpdate,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """批改：填分数 + 评语 → 状态自动变 已批改

    订正自动判定：批改作业（type=homework）时若 score < 90 → needs_correction=true
    （考试 type=exam 不触发订正）
    """
    rec = _ensure_record_owned(db, record_id, current.id)
    hw = db.get(Homework, rec.homework_id)

    if payload.score is not None:
        rec.score = payload.score
        rec.scored_at = datetime.utcnow()
        # 仅作业类型自动判定订正
        if hw is not None and hw.type == "homework":
            rec.needs_correction = payload.score < CORRECTION_THRESHOLD
            # 重新批改（重新打分）会重置已订正状态，要求学生再次订正
            if rec.needs_correction:
                rec.corrected = False
                rec.corrected_at = None
            else:
                # 分数变 ≥90 后清掉订正要求
                rec.corrected = False
                rec.corrected_at = None
    if payload.comment is not None:
        rec.comment = payload.comment
    if payload.status is not None:
        rec.status = payload.status
    elif payload.score is not None:
        rec.status = "已批改"
    if payload.corrected is not None:
        rec.corrected = payload.corrected
        rec.corrected_at = datetime.utcnow() if payload.corrected else None
    db.commit()
    db.refresh(rec)
    # 拼装学生信息
    stu = db.get(Student, rec.student_id)
    out = HomeworkRecordOut.model_validate(rec)
    if stu:
        out.student_name = stu.name
        out.student_no = stu.student_no
    return out
