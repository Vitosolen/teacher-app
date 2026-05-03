# SQLite → MySQL 一键迁移指南

> 当你需要把现有 SQLite 数据库迁移到 MySQL 时（例如多老师并发、上云服务器），照着本文做。
>
> **关键保证**：原 SQLite 文件全程只读，迁移失败可一键回滚。

---

## 0. 什么时候需要迁移

| 情况 | 建议 |
|---|---|
| 一两个老师本地用 | **不迁**，SQLite 够 |
| 一所学校多老师同时用 | 迁 |
| 部署到云服务器 / 公网 | 迁 |
| 数据量超过 10 万条 behaviors | 迁 |
| 想要更可靠的备份恢复机制（mysqldump / 主从）| 迁 |

---

## 1. 准备 MySQL（一次性）

如果机器上还没装 MySQL：

**Windows**：去 <https://dev.mysql.com/downloads/installer/> 下载 MySQL Installer，选 Server only，记下 root 密码。

**Mac**：`brew install mysql && brew services start mysql`

**Ubuntu**：`sudo apt install mysql-server && sudo systemctl start mysql`

启动后能用 `mysql -u root -p` 登进去就 OK。

---

## 2. 一键迁移（推荐）

```powershell
# 1. 进后端目录、激活虚拟环境
cd class-pet-backend
.\.venv\Scripts\Activate.ps1     # macOS/Linux: source .venv/bin/activate

# 2. 跑向导
python migrate_to_mysql.py
```

向导会问你这些信息（按回车用默认值）：

```
Host (默认 127.0.0.1):              ← 直接回车
Port (默认 3306):                    ← 直接回车
Database 名 (默认 teacher_app):     ← 直接回车
用户名 (默认 classpet):              ← 直接回车
密码: ************                  ← 输入你想用的密码
```

**第一次跑**：脚本测连接 → 失败时会问"是否用 root 帮你创建 database 和用户" → 输入 root 密码 → 自动创建。

**后续步骤全自动**（约 30 秒）：
- ✅ 备份当前 SQLite 到 `backups/class_pet_pre_mysql_<时间戳>.db`
- ✅ 备份 `.env` 到 `.env.sqlite.bak`
- ✅ 改写 `.env` 的 `DATABASE_URL`
- ✅ 在 MySQL 建表 + 写预置 seed
- ✅ 搬迁所有业务数据（保留 ID 和外键）
- ✅ 双向计数验证（每张表 SQLite vs MySQL 数量必须一致）

完成后会看到：
```
[DONE] 迁移完成！启动服务：
  uvicorn app.main:app --reload
```

启动服务、登录原账号验证 → 完事。

---

## 3. 验证清单

迁移后建议手动复查：

- [ ] 原老师账号能正常登录（密码 hash 已搬过来）
- [ ] 班级数 / 学生数 / 宠物数与之前一致
- [ ] 行为时间线（最近打分）记录条数对得上
- [ ] 商城里学生 points 余额没变
- [ ] 已上传的宠物图片能显示（图片存 `static/pets/`，跟数据库无关）

如果发现不一致 → **直接回滚**（看下一节），数据没丢。

---

## 4. 回滚到 SQLite

迁移过程不动 SQLite 文件，所以回滚就是改回配置：

```powershell
cd class-pet-backend
copy .env.sqlite.bak .env
# macOS/Linux: cp .env.sqlite.bak .env

# 重启服务
uvicorn app.main:app --reload
```

数据全回来了。MySQL 那边的 database 不用动（保留也行，删了也行）。

---

## 5. 手动迁移（如果向导不工作）

向导本质上是封装了 4 个动作。手动等价于：

```powershell
cd class-pet-backend

# Step A: 备份 SQLite
copy class_pet.db ..\backups\class_pet_pre_mysql.db

# Step B: 在 MySQL 里建库（用 mysql 客户端登 root）
mysql -u root -p
mysql> CREATE DATABASE teacher_app DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
mysql> CREATE USER 'classpet'@'localhost' IDENTIFIED BY '你的密码';
mysql> GRANT ALL ON teacher_app.* TO 'classpet'@'localhost';
mysql> FLUSH PRIVILEGES;
mysql> EXIT;

# Step C: 改 .env
copy .env .env.sqlite.bak
# 编辑 .env：
# DATABASE_URL=mysql+pymysql://classpet:你的密码@127.0.0.1:3306/teacher_app?charset=utf8mb4

# Step D: 让 MySQL 建表
.\.venv\Scripts\Activate.ps1
python init_db.py

# Step E: 搬数据
python migrate_sqlite_to_mysql.py
# 输 yes 确认
```

---

## 6. 生产环境（线上有用户在用）

如果服务已经在跑、有老师在线使用，按这个流程：

1. **公告**：提前一天通知所有老师"明早 0-1 点维护"
2. **维护时间停服**：关掉 uvicorn / nginx
3. **跑 `tools/backup.ps1` 双备份**：本地一份 + 同步到 OneDrive / 移动硬盘
4. **跑 `python migrate_to_mysql.py`** —— 全自动 30 秒完成
5. **快速冒烟测试**：登 2-3 个不同老师账号，看数据是否完整
6. **恢复服务**

整个停服窗口约 10 分钟，含验证。

---

## 7. 常见问题

### Q1: 向导问到 root 密码我没装 MySQL？
先按 §1 装好 MySQL 再跑向导。装时会让你设 root 密码，记下来。

### Q2: 报错 `Access denied for user 'classpet'@'localhost'`？
说明用户没创建或密码错。重新跑向导，让它用 root 帮你创建即可（输 y 进入 root 流程）。

### Q3: 迁移后启动报 `pymysql 模块没装`？
```bash
pip install pymysql cryptography
```
（`requirements.txt` 已经包含了，正常 `pip install -r requirements.txt` 不会缺）

### Q4: 双向验证有 `DIFF` 怎么办？
- 不要慌，原 SQLite 和备份都在
- 跑回滚（§4）回到 SQLite 状态
- 看 MySQL 对应表是哪几行不一致
- 通常是字符编码（CREATE DATABASE 时漏了 utf8mb4）—— 删 database 重建用 utf8mb4 即可

### Q5: 后续怎么备份 MySQL（不再用 backup.ps1）？
```bash
mysqldump -u classpet -p teacher_app > teacher_app_$(date +%Y%m%d).sql
```

---

## 8. 文件清单

| 文件 | 角色 |
|---|---|
| `class-pet-backend/migrate_to_mysql.py` | **一键向导**（推荐入口） |
| `class-pet-backend/migrate_sqlite_to_mysql.py` | 底层数据搬迁脚本（向导内部调用） |
| `class-pet-backend/init_db.py` | 建表 + seed（任何数据库都能用） |
| `tools/backup.ps1` / `backup.sh` | SQLite 备份脚本 |
| `class-pet-backend/.env.sqlite.bak` | 迁移时自动生成的 .env 备份（回滚用） |
| `backups/` | 自动备份目录 |

---

## TL;DR

```powershell
cd class-pet-backend
python migrate_to_mysql.py
# 按提示输入密码，30 秒后完成
# 启动：uvicorn app.main:app --reload
```

回滚：`cp .env.sqlite.bak .env`
