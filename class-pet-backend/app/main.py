"""FastAPI 入口：CORS + 路由挂载 + 静态文件"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import api_router
from app.core.config import settings

app = FastAPI(
    title="班级养宠物系统 API",
    description="老师端 - 班级/学生/宠物/行为管理",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件（用户上传的宠物图片等存放在这里）
# 目录：class-pet-backend/static/   →   URL：/static/...
STATIC_ROOT = Path(__file__).resolve().parent.parent / "static"
STATIC_ROOT.mkdir(exist_ok=True)
(STATIC_ROOT / "pets").mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_ROOT)), name="static")

app.include_router(api_router)


@app.get("/")
def root():
    return {"service": "class-pet-api", "docs": "/docs"}
