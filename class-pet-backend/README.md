# class-pet-backend

班级养宠物系统后端（FastAPI + SQLAlchemy + MySQL/SQLite）。

## 启动

```bash
# 1. 创建虚拟环境（已创建则跳过）
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
# 或 .venv\Scripts\activate     # Windows CMD

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 修改 .env 里的 DATABASE_URL 与 JWT_SECRET

# 4. 执行数据库迁移
alembic upgrade head

# 5. 启动服务
uvicorn app.main:app --reload --port 8000
```

服务起来后：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/v1/ping

## 切换 MySQL

修改 `.env`：

```
DATABASE_URL=mysql+pymysql://user:password@host:3306/class_pet?charset=utf8mb4
```

确保 MySQL 中已建库 `class_pet`，然后执行 `alembic upgrade head`。

## 测试

```bash
pytest -v
```
