"""班级 CRUD + 随机点名"""
import random

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_teacher
from app.models.class_ import Class
from app.models.student import Student
from app.models.teacher import Teacher
from app.schemas.class_ import ClassCreate, ClassOut, ClassUpdate
from app.schemas.student import StudentOut
from app.api.v1.students import _student_to_out

router = APIRouter(prefix="/classes", tags=["classes"])


@router.get("", response_model=list[ClassOut])
def list_classes(
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """列出当前老师的所有班级"""
    rows = (
        db.query(
            Class,
            func.count(Student.id).label("student_count"),
        )
        .outerjoin(Student, Student.class_id == Class.id)
        .filter(Class.teacher_id == current.id)
        .group_by(Class.id)
        .order_by(Class.created_at.desc())
        .all()
    )
    result = []
    for cls, cnt in rows:
        out = ClassOut.model_validate(cls)
        out.student_count = cnt
        result.append(out)
    return result


@router.post("", response_model=ClassOut, status_code=status.HTTP_201_CREATED)
def create_class(
    payload: ClassCreate,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """创建班级"""
    cls = Class(name=payload.name, grade=payload.grade, teacher_id=current.id)
    db.add(cls)
    db.commit()
    db.refresh(cls)
    out = ClassOut.model_validate(cls)
    out.student_count = 0
    return out


@router.patch("/{class_id}", response_model=ClassOut)
def update_class(
    class_id: int,
    payload: ClassUpdate,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """编辑班级（改名、改年级）"""
    cls = db.get(Class, class_id)
    if cls is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    if cls.teacher_id != current.id:
        raise HTTPException(status_code=403, detail="无权操作他人班级")
    if payload.name is not None:
        cls.name = payload.name
    if payload.grade is not None:
        cls.grade = payload.grade
    db.commit()
    db.refresh(cls)
    # 返回时附 student_count
    cnt = db.query(func.count(Student.id)).filter(Student.class_id == cls.id).scalar() or 0
    out = ClassOut.model_validate(cls)
    out.student_count = cnt
    return out


class RandomPickPayload(BaseModel):
    count: int = Field(ge=1, le=200)


@router.post("/{class_id}/random-pick", response_model=list[StudentOut])
def random_pick(
    class_id: int,
    payload: RandomPickPayload,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """随机点名：从班级学生中随机抽取 count 人（不重复）"""
    cls = db.get(Class, class_id)
    if cls is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    if cls.teacher_id != current.id:
        raise HTTPException(status_code=403, detail="无权操作他人班级")
    students = db.query(Student).filter(Student.class_id == class_id).all()
    if not students:
        raise HTTPException(status_code=400, detail="班级内没有学生")
    n = min(payload.count, len(students))
    picked = random.sample(students, n)
    return [_student_to_out(s) for s in picked]


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """删除班级（连带学生、宠物、行为级联删）"""
    cls = db.get(Class, class_id)
    if cls is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    if cls.teacher_id != current.id:
        raise HTTPException(status_code=403, detail="无权操作他人班级")
    db.delete(cls)
    db.commit()
