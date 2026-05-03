# 🐉 班级养宠物系统 · Class Pet System

> 老师端课堂管理工具：把"打分"游戏化——每个学生认领一只虚拟宠物，老师对学生行为加减分自动驱动宠物属性变化，积分可在商城兑换房子/家具/衣服/食物，宠物住进自己的家里。同时支持作业管理、成绩登记、单词听写、随机点名等课堂工具。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Vue](https://img.shields.io/badge/Vue-3-brightgreen.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.x-009688.svg)

---

## ✨ 核心特性

### 🎮 游戏化激励
- **6 种宠物物种**（小龙 / 小猫 / 小狗 / 小兔 / 熊猫 / 狐狸），每种 4 阶段成长 emoji
- **5 大类商品**（食品 / 衣服 / 玩具 / 房子 / 家具），共 20+ 件预置
- **真正的家**：买入房子后有完整屋内场景（家具按位置摆放、宠物住进去日常活动）
- **物种管理**：老师可自定义物种 + 上传自定义图片

### 📚 课堂工具
- **班级 / 学生 CRUD**：网格卡片视图，支持批量导入
- **打分系统**：自定义积分规则（替代硬编码），支持单选 / 批量 / 自定义分数（±100）
- **作业管理**：选班级 + 科目建作业 → 自动绑定全班 → 批改打分点评
- **作业订正**：分数 < 85（A 等）自动标记需订正，重新批改自动重置
- **成绩登记**：A1-A3 / B1-B3 / C1-C3 / D1-D3 等级自动判定 + 趋势分析折线图
- **单词听写**：批量粘贴 / Excel 导入 + 浏览器原生 TTS 朗读 + 6 种语言
- **随机点名**：转盘动画

### 🖥️ 高级功能
- **首页 Dashboard**：今日打分 / 待办 / 排行榜 / 7 天趋势
- **课堂大屏模式**：投影到教室前面，全班宠物可视化 + 实时打分动画
- **撒花动画 + 撤销 toast**：升级时撒花，5 秒内可撤回打分
- **拖拽排序**：物种顺序可视化拖拽

---

## 🚀 快速开始

### 环境要求

| 软件 | 最低版本 | 下载 |
|---|---|---|
| Python | 3.10 | <https://www.python.org/downloads/> |
| Node.js | 18 | <https://nodejs.org/> |

> Windows 装 Python 时务必勾选「Add to PATH」。

### Windows

```cmd
# 1. 克隆代码
git clone <你 fork 的仓库地址>
cd teacher-app

# 2. 一键安装（首次需 5-10 分钟）
install.bat

# 3. 一键启动
start.bat
```

启动后浏览器自动打开 <http://127.0.0.1:5173>。

### macOS / Linux

```bash
# 1. 克隆代码
git clone <你 fork 的仓库地址>
cd teacher-app

# 2. 给脚本执行权限
chmod +x install.sh start.sh

# 3. 一键安装
./install.sh

# 4. 启动
./start.sh
```

### 第一次使用

1. 打开 <http://127.0.0.1:5173>
2. 注册老师账号（用户名/密码/显示名）
3. 创建班级 → 添加学生（支持批量粘贴）
4. 给学生**领养宠物**（选物种 + 起名）
5. 开始打分、布置作业、批量加分、看 Dashboard

---

## 🛠️ 技术栈

**后端**
- Python 3.10+ / FastAPI / SQLAlchemy 2.x / Alembic / Pydantic v2
- 数据库：SQLite（开箱即用）/ MySQL（可选）
- 认证：JWT + bcrypt

**前端**
- Vue 3 + TypeScript + Vite
- Element Plus（UI 组件库）
- Pinia（状态管理）/ Vue Router / Axios
- xlsx (SheetJS)（Excel 导入）

**TTS（听写）**
- 浏览器原生 `SpeechSynthesisUtterance`，无需后端 / 服务费用

---

## 📁 项目结构

```
teacher-app/
├── class-pet-backend/      Python FastAPI 后端
│   ├── app/                业务代码（models / schemas / api / services）
│   ├── alembic/versions/   数据库迁移
│   ├── static/pets/        用户上传的宠物图片
│   ├── e2e_*.py            端到端测试脚本
│   ├── init_db.py          数据库初始化（首次安装自动调用）
│   └── requirements.txt
├── class-pet-frontend/     Vue 3 前端
│   ├── src/
│   │   ├── api/            HTTP 客户端（按模块拆分）
│   │   ├── stores/         Pinia 状态
│   │   ├── components/     可复用组件
│   │   ├── views/          页面视图
│   │   ├── composables/    工具组合
│   │   └── types/domain.ts 与后端对齐的类型
│   └── package.json
├── docs/                   详细文档
│   ├── 操作文档.md         给老师的使用手册
│   ├── 运维文档.md         部署 / 启停 / 排错
│   ├── 项目总结.md         架构 / 数据模型 / 13 张表清单
│   └── 经验记录.md         开发踩坑 + 复用模式
├── install.bat / install.sh  一键安装
├── start.bat / start.sh      一键启动
└── stop.bat                  Windows 停止服务
```

详细架构、API 速查、数据模型见 [`docs/项目总结.md`](docs/项目总结.md)。

---

## 🧪 端到端测试

后端附带 9 个 E2E 脚本（共 100+ 步），覆盖完整业务流：

```bash
cd class-pet-backend
source .venv/bin/activate    # Windows: .venv\Scripts\activate
python smoke_test.py             # 14 步基础冒烟
python e2e_via_proxy.py          # 16 步 MVP 全链路
python e2e_iter2.py              # 26 步迭代 2 功能
python e2e_dictation.py          # 12 步单词听写
python e2e_petworld.py           # 9 步房子家具装备
python e2e_adopt.py              # 9 步领养系统
python e2e_grade_correction.py   # 12 步成绩 + 订正
python e2e_species.py            # 12 步物种管理
```

> 跑前端 E2E 需先启动前端 dev server（部分脚本走 `http://127.0.0.1:5173/api` 代理）。

---

## ⚙️ 配置

### 后端环境变量 `class-pet-backend/.env`

```env
DATABASE_URL=sqlite:///./class_pet.db
JWT_SECRET=change-me-in-production-please
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

**生产部署务必修改 `JWT_SECRET`**，可用：

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 前端环境变量 `class-pet-frontend/.env.local`（可选）

默认后端跑在 8000 端口，如要改：

```env
VITE_BACKEND_PORT=8002
VITE_BACKEND_HOST=127.0.0.1
```

### 切到 MySQL（可选）

```env
DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/teacher_app?charset=utf8mb4
```

然后 `python init_db.py` 即可。详见 [`docs/运维文档.md`](docs/运维文档.md)。

---

## 🤝 贡献

欢迎提 Issue 和 PR！

代码风格：
- 后端：FastAPI 官方风格 + Pydantic v2，类型注解写完整
- 前端：Vue 3 Composition API + `<script setup>` + TS 严格模式

提交 PR 前：
1. 跑通 E2E 测试
2. `cd class-pet-frontend && npx vue-tsc --noEmit` 类型检查 0 错误
3. 在 PR 描述里说明改了哪些功能、为什么

---

## 📜 协议

[MIT License](LICENSE) — 自由使用、修改、商用，标注原作者即可。

---

## 🙏 致谢

- [Element Plus](https://element-plus.org/) — Vue 组件库
- [FastAPI](https://fastapi.tiangolo.com/) — 现代 Python web 框架
- 所有提建议、报 bug、贡献代码的老师朋友

---

**做这个项目的动机**：让"打分"这件抽象的事变成学生看得见、有情感连接的反馈，提高激励效果，同时给老师提供一套完整的课堂数字化工具。希望能帮到一线老师。
