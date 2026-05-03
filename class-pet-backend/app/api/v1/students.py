"""学生 CRUD（含批量导入；创建时自动建宠物）"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_db, get_current_teacher
from app.models.class_ import Class
from app.models.pet import Pet
from app.models.student import Student
from app.models.teacher import Teacher
from app.schemas.pet import PetOut, PetAdopt
from app.schemas.student import StudentCreate, StudentUpdate, StudentBatchCreate, StudentOut
from app.services.pet_service import derive_status, exp_threshold

router = APIRouter(tags=["students"])


def _ensure_class_owned(db: Session, class_id: int, teacher_id: int) -> Class:
    cls = db.get(Class, class_id)
    if cls is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    if cls.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="无权操作他人班级")
    return cls


def _ensure_student_owned(db: Session, student_id: int, teacher_id: int) -> Student:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    if student.class_.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="无权操作他人学生")
    return student


def _student_to_out(student: Student) -> StudentOut:
    """统一构造响应（含派生字段）"""
    out = StudentOut.model_validate(student)
    if student.pet:
        pet_out = PetOut.model_validate(student.pet)
        pet_out.status = derive_status(student.pet)
        pet_out.exp_to_next_level = exp_threshold(student.pet.level)
        out.pet = pet_out
    return out


@router.get("/classes/{class_id}/students", response_model=list[StudentOut])
def list_students(
    class_id: int,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """列出班级内学生（含宠物简要信息）"""
    _ensure_class_owned(db, class_id, current.id)
    students = (
        db.query(Student)
        .options(selectinload(Student.pet))
        .filter(Student.class_id == class_id)
        .order_by(Student.created_at.asc())
        .all()
    )
    return [_student_to_out(s) for s in students]


@router.post(
    "/classes/{class_id}/students",
    response_model=StudentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_student(
    class_id: int,
    payload: StudentCreate,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """添加单个学生（不自动建宠物，需后续主动领养）"""
    _ensure_class_owned(db, class_id, current.id)
    student = Student(class_id=class_id, name=payload.name, student_no=payload.student_no)
    db.add(student)
    db.commit()
    db.refresh(student)
    return _student_to_out(student)


@router.post(
    "/classes/{class_id}/students/batch",
    response_model=list[StudentOut],
    status_code=status.HTTP_201_CREATED,
)
def batch_create_students(
    class_id: int,
    payload: StudentBatchCreate,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """批量导入学生（不自动建宠物，需后续主动领养）"""
    _ensure_class_owned(db, class_id, current.id)
    created: list[Student] = []
    for raw in payload.names:
        name = raw.strip()
        if not name:
            continue
        student = Student(class_id=class_id, name=name)
        db.add(student)
        created.append(student)
    db.commit()
    for s in created:
        db.refresh(s)
    return [_student_to_out(s) for s in created]


@router.get("/students/{student_id}", response_model=StudentOut)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """学生详情（含宠物完整属性）"""
    student = _ensure_student_owned(db, student_id, current.id)
    return _student_to_out(student)


@router.patch("/students/{student_id}", response_model=StudentOut)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """编辑学生（改名、改学号）"""
    student = _ensure_student_owned(db, student_id, current.id)
    if payload.name is not None:
        student.name = payload.name
    if payload.student_no is not None:
        student.student_no = payload.student_no
    db.commit()
    db.refresh(student)
    return _student_to_out(student)


@router.post(
    "/students/{student_id}/adopt-pet",
    response_model=StudentOut,
    status_code=status.HTTP_201_CREATED,
)
def adopt_pet(
    student_id: int,
    payload: PetAdopt,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """学生领养宠物（每个学生只能有一只）"""
    student = _ensure_student_owned(db, student_id, current.id)
    if student.pet is not None:
        raise HTTPException(status_code=400, detail=f"{student.name} 已经有一只宠物了")
    pet = Pet(
        name=payload.name.strip(),
        species=payload.species,
        student=student,
    )
    db.add(pet)
    db.commit()
    db.refresh(student)
    return _student_to_out(student)


@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    """删除学生（连带宠物、行为级联删）"""
    student = _ensure_student_owned(db, student_id, current.id)
    db.delete(student)
    db.commit()
