"""仪表盘聚合接口：登录首页用，一次 RTT 拿齐所有概览数据"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_teacher
from app.models.behavior import Behavior
from app.models.class_ import Class
from app.models.homework import Homework
from app.models.homework_record import HomeworkRecord
from app.models.pet import Pet
from app.models.student import Student
from app.models.teacher import Teacher

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard(
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """返回当前老师的概览数据"""
    teacher_id = current.id
    # "今天" 按北京时间（UTC+8）切割：北京 0 点对应 UTC 16:00（前一天）
    # 数据库写入用 datetime.utcnow()（naive UTC），所以这里用 UTC 时刻做边界
    BJT = timezone(timedelta(hours=8))
    now_bj = datetime.now(BJT)
    today_start_bj = now_bj.replace(hour=0, minute=0, second=0, microsecond=0)
    today_start = today_start_bj.astimezone(timezone.utc).replace(tzinfo=None)  # 转回 naive UTC
    week_ago = today_start - timedelta(days=6)  # 含今天共 7 天

    # 当前老师的班级 id 列表（多个查询要复用）
    own_class_ids = [
        c.id for c in db.query(Class.id).filter(Class.teacher_id == teacher_id).all()
    ]

    # 总览：班级、学生、宠物
    class_count = len(own_class_ids)
    if own_class_ids:
        student_count = (
            db.query(func.count(Student.id))
            .filter(Student.class_id.in_(own_class_ids))
            .scalar() or 0
        )
        adopted_count = (
            db.query(func.count(Pet.id))
            .join(Student, Student.id == Pet.student_id)
            .filter(Student.class_id.in_(own_class_ids))
            .scalar() or 0
        )
    else:
        student_count = 0
        adopted_count = 0

    # 今日打分汇总
    today_q = db.query(
        func.count(Behavior.id).label("count"),
        func.sum(case((Behavior.score > 0, Behavior.score), else_=0)).label("plus_sum"),
        func.sum(case((Behavior.score < 0, 1), else_=0)).label("minus_count"),
    ).filter(
        Behavior.teacher_id == teacher_id,
        Behavior.created_at >= today_start,
    ).first()
    today_count = int(today_q.count or 0) if today_q else 0
    today_plus = int(today_q.plus_sum or 0) if today_q else 0
    today_minus = int(today_q.minus_count or 0) if today_q else 0

    # 待办：未批改作业 + 待订正
    if own_class_ids:
        ungraded_count = (
            db.query(func.count(HomeworkRecord.id))
            .join(Homework, Homework.id == HomeworkRecord.homework_id)
            .filter(
                Homework.class_id.in_(own_class_ids),
                Homework.type == "homework",
                HomeworkRecord.status != "已批改",
            )
            .scalar() or 0
        )
        correction_pending = (
            db.query(func.count(HomeworkRecord.id))
            .join(Homework, Homework.id == HomeworkRecord.homework_id)
            .filter(
                Homework.class_id.in_(own_class_ids),
                Homework.type == "homework",
                HomeworkRecord.needs_correction.is_(True),
                HomeworkRecord.corrected.is_(False),
            )
            .scalar() or 0
        )
    else:
        ungraded_count = 0
        correction_pending = 0

    # 积分排行榜 Top 5（含班级名）
    points_rank = []
    if own_class_ids:
        rows = (
            db.query(Student, Class.name)
            .join(Class, Class.id == Student.class_id)
            .filter(Student.class_id.in_(own_class_ids))
            .order_by(Student.points.desc(), Student.id.asc())
            .limit(5)
            .all()
        )
        points_rank = [
            {
                "id": s.id, "name": s.name, "points": s.points,
                "class_name": cname,
            }
            for s, cname in rows
        ]

    # 宠物等级排行榜 Top 5
    level_rank = []
    if own_class_ids:
        rows = (
            db.query(Pet, Student, Class.name)
            .join(Student, Student.id == Pet.student_id)
            .join(Class, Class.id == Student.class_id)
            .filter(Student.class_id.in_(own_class_ids))
            .order_by(Pet.level.desc(), Pet.exp.desc())
            .limit(5)
            .all()
        )
        level_rank = [
            {
                "pet_id": p.id, "student_id": stu.id,
                "pet_name": p.name, "species": p.species,
                "level": p.level, "exp": p.exp,
                "student_name": stu.name, "class_name": cname,
            }
            for p, stu, cname in rows
        ]

    # 最近 7 天打分趋势（每天打分次数；按北京时间分桶）
    trend_rows = (
        db.query(
            func.date(Behavior.created_at).label("day"),
            func.count(Behavior.id).label("cnt"),
        )
        .filter(
            Behavior.teacher_id == teacher_id,
            Behavior.created_at >= week_ago,
        )
        .group_by(func.date(Behavior.created_at))
        .all()
    )
    m = {str(r.day): int(r.cnt) for r in trend_rows}
    trend = []
    for i in range(7):
        d = (week_ago + timedelta(days=i)).date()
        trend.append({"date": str(d), "count": m.get(str(d), 0)})

    # 最近班级（最多 4 个）
    recent_classes = []
    if own_class_ids:
        rows = (
            db.query(Class, func.count(Student.id).label("sc"))
            .outerjoin(Student, Student.class_id == Class.id)
            .filter(Class.teacher_id == teacher_id)
            .group_by(Class.id)
            .order_by(Class.created_at.desc())
            .limit(4)
            .all()
        )
        recent_classes = [
            {
                "id": c.id, "name": c.name, "grade": c.grade,
                "student_count": int(sc or 0),
            }
            for c, sc in rows
        ]

    return {
        "overview": {
            "class_count": class_count,
            "student_count": student_count,
            "adopted_count": adopted_count,
            "unadopted_count": student_count - adopted_count,
        },
        "today": {
            "behavior_count": today_count,
            "points_granted": today_plus,
            "minus_count": today_minus,
        },
        "todo": {
            "ungraded_homework_records": ungraded_count,
            "correction_pending": correction_pending,
        },
        "points_rank": points_rank,
        "level_rank": level_rank,
        "trend_7d": trend,
        "recent_classes": recent_classes,
    }
