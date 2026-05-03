"""认证：注册 / 登录 / 获取当前用户"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_teacher
from app.core.security import hash_password, verify_password, create_access_token
from app.models.score_rule import ScoreRule
from app.models.teacher import Teacher
from app.schemas.auth import RegisterIn, TokenOut, TeacherOut

router = APIRouter(prefix="/auth", tags=["auth"])

# 新老师注册时自动复制的默认积分规则（避免每个老师手动配置 9 条）
_DEFAULT_RULES: list[tuple[str, str, int, int]] = [
    # (label, category, score, sort_order)
    ("回答问题", "学习", 1, 1),
    ("举手发言", "积极", 2, 2),
    ("按时完成", "学习", 3, 3),
    ("热心助人", "积极", 4, 4),
    ("作业优秀", "学习", 5, 5),
    ("迟到", "纪律", -2, 11),
    ("违纪", "纪律", -3, 12),
    ("不交作业", "学习", -4, 13),
    ("扰乱课堂", "纪律", -5, 14),
]


@router.post("/register", response_model=TeacherOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    """注册新老师账号 + 自动复制默认积分规则"""
    exists = db.query(Teacher).filter(Teacher.username == payload.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="用户名已被使用")
    teacher = Teacher(
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
    )
    db.add(teacher)
    db.flush()  # 取到 teacher.id
    # 复制默认积分规则
    for label, category, score, order in _DEFAULT_RULES:
        db.add(ScoreRule(
            teacher_id=teacher.id, label=label, category=category,
            score=score, sort_order=order, active=True,
        ))
    db.commit()
    db.refresh(teacher)
    return teacher


@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """登录返回 JWT。表单字段：username / password（OAuth2PasswordRequestForm 标准格式）"""
    teacher = db.query(Teacher).filter(Teacher.username == form.username).first()
    if not teacher or not verify_password(form.password, teacher.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(subject=teacher.id)
    return TokenOut(access_token=token)


@router.get("/me", response_model=TeacherOut)
def me(current: Teacher = Depends(get_current_teacher)):
    """获取当前登录老师信息"""
    return current
