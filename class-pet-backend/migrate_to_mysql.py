"""SQLite → MySQL 一键迁移向导

前置条件：
  - MySQL 8 已安装并启动
  - 已创建数据库与用户（脚本里也可以选择"脚本帮我创建"）
  - 当前 .env 是 SQLite 配置（脚本会自动备份再改写）

执行：
  cd class-pet-backend
  python migrate_to_mysql.py

脚本流程：
  1. 收集 MySQL 连接信息
  2. 测试连接 + 可选创建 database
  3. 备份当前 SQLite 文件
  4. 备份 .env 为 .env.sqlite.bak
  5. 改写 .env 到 MySQL
  6. 在 MySQL 建表 + 写 seed (init_db.py)
  7. 把 SQLite 数据搬到 MySQL (migrate_sqlite_to_mysql.py)
  8. 双向计数验证
"""
import io
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
SQLITE_FILE = ROOT / "class_pet.db"
ENV_FILE = ROOT / ".env"


def fail(msg: str) -> None:
    print(f"\n[失败] {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"  [OK] {msg}")


def step(n: int, total: int, desc: str) -> None:
    print(f"\n========== [{n}/{total}] {desc} ==========")


def ask(prompt: str, default: str = "") -> str:
    p = f"{prompt} (默认 {default}): " if default else f"{prompt}: "
    val = input(p).strip()
    return val or default


def ask_yes(prompt: str, default: bool = False) -> bool:
    suffix = "Y/n" if default else "y/N"
    val = input(f"{prompt} ({suffix}): ").strip().lower()
    if not val:
        return default
    return val in ("y", "yes")


def main() -> None:
    print("=" * 60)
    print("  班级养宠物系统 - SQLite → MySQL 一键迁移向导")
    print("=" * 60)

    # —— 0. 前置检查 ——
    if not SQLITE_FILE.exists():
        fail(f"找不到 SQLite 数据库 {SQLITE_FILE}")

    try:
        import pymysql  # noqa: F401
    except ImportError:
        fail("缺少 pymysql 依赖，请先 pip install pymysql")

    # —— 1. 收集连接信息 ——
    step(1, 8, "MySQL 连接信息")
    host = ask("Host", "127.0.0.1")
    port = ask("Port", "3306")
    db_name = ask("Database 名", "teacher_app")
    user = ask("用户名", "classpet")
    password = input("密码（输入不显示，回车即用）: ").strip()
    if not password:
        fail("密码不能为空")

    # —— 2. 测连接 + 可选建库 ——
    step(2, 8, "测试 MySQL 连接")
    import pymysql
    try:
        # 先试目标用户连目标库
        conn = pymysql.connect(host=host, port=int(port), user=user,
                               password=password, charset="utf8mb4",
                               database=db_name)
        conn.close()
        ok("用目标用户成功连接到目标 database")
    except pymysql.Error as e:
        print(f"  连不上：{e}")
        if not ask_yes("是否用 root 帮你创建 database 和用户？", default=True):
            fail("已取消。请手动创建好 database 和用户后再次运行")
        root_pass = input("请输入 MySQL root 密码: ").strip()
        try:
            root_conn = pymysql.connect(host=host, port=int(port), user="root",
                                        password=root_pass, charset="utf8mb4")
            with root_conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                            f"DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci")
                cur.execute(f"CREATE USER IF NOT EXISTS '{user}'@'localhost' "
                            f"IDENTIFIED BY '{password}'")
                cur.execute(f"GRANT ALL ON `{db_name}`.* TO '{user}'@'localhost'")
                cur.execute("FLUSH PRIVILEGES")
            root_conn.commit()
            root_conn.close()
            ok(f"已创建 database `{db_name}` 和用户 `{user}`")
        except pymysql.Error as e:
            fail(f"创建失败：{e}")

    new_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}?charset=utf8mb4"
    print(f"  目标 URL：{new_url.replace(password, '***')}")

    # —— 3. 备份 SQLite ——
    step(3, 8, "备份 SQLite 数据库")
    backup_dir = ROOT.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    backup_path = backup_dir / f"class_pet_pre_mysql_{ts}.db"
    shutil.copy(SQLITE_FILE, backup_path)
    ok(f"已备份到 {backup_path}（出问题可恢复）")

    # —— 4. 备份 .env ——
    step(4, 8, "备份 .env")
    if ENV_FILE.exists():
        shutil.copy(ENV_FILE, ROOT / ".env.sqlite.bak")
        ok(".env 已备份为 .env.sqlite.bak（回滚时改回即可）")
    else:
        # 从 example 拷贝
        ex = ROOT / ".env.example"
        if ex.exists():
            shutil.copy(ex, ENV_FILE)
            ok("从 .env.example 生成 .env")
        else:
            fail("既没有 .env 也没有 .env.example，请检查项目")

    # —— 5. 改写 .env 的 DATABASE_URL ——
    step(5, 8, "改写 .env 的 DATABASE_URL")
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    written = False
    new_lines: list[str] = []
    for line in lines:
        if line.startswith("DATABASE_URL="):
            new_lines.append(f"DATABASE_URL={new_url}")
            written = True
        else:
            new_lines.append(line)
    if not written:
        new_lines.append(f"DATABASE_URL={new_url}")
    ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    ok("DATABASE_URL 已切到 MySQL")

    # —— 6. 在 MySQL 建表 + seed ——
    step(6, 8, "在 MySQL 建表 + 写预置数据 (init_db.py)")
    r = subprocess.run([sys.executable, "init_db.py"], cwd=ROOT)
    if r.returncode != 0:
        fail("init_db.py 失败，请检查 MySQL 连接和权限")
    ok("MySQL 表已就绪")

    # —— 7. 搬迁数据 ——
    step(7, 8, "搬迁 SQLite 数据 → MySQL (migrate_sqlite_to_mysql.py)")
    r = subprocess.run(
        [sys.executable, "migrate_sqlite_to_mysql.py",
         "--src", str(SQLITE_FILE), "--yes"],
        cwd=ROOT,
    )
    if r.returncode != 0:
        fail("数据搬迁失败")
    ok("数据已搬到 MySQL")

    # —— 8. 双向计数验证 ——
    step(8, 8, "双向计数验证")
    import sqlite3
    src = sqlite3.connect(SQLITE_FILE)
    dst = pymysql.connect(host=host, port=int(port), user=user,
                          password=password, database=db_name, charset="utf8mb4")

    KEY_TABLES = ["teachers", "classes", "students", "pets", "behaviors",
                  "homeworks", "homework_records", "shop_items"]
    all_match = True
    print(f"  {'表':<20} {'SQLite':>10} {'MySQL':>10}  状态")
    print(f"  {'-' * 20} {'-' * 10} {'-' * 10}  ----")
    for t in KEY_TABLES:
        try:
            sq = src.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            with dst.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM `{t}`")
                my = cur.fetchone()[0]
            status = "OK" if sq == my else "DIFF !"
            if sq != my:
                all_match = False
            print(f"  {t:<20} {sq:>10} {my:>10}  {status}")
        except Exception as e:
            print(f"  {t:<20}  {e}")
            all_match = False

    src.close()
    dst.close()

    print()
    if all_match:
        print("=" * 60)
        print("  [DONE] 迁移完成！启动服务：")
        print("    uvicorn app.main:app --reload")
        print()
        print("  如需回滚：")
        print("    cp .env.sqlite.bak .env  # 或手动改 DATABASE_URL")
        print("=" * 60)
    else:
        print("=" * 60)
        print("  [警告] 计数有不一致项，请检查上方表格")
        print("  数据未丢失：原 SQLite 文件和备份都还在")
        print("  回滚：cp .env.sqlite.bak .env")
        print("=" * 60)


if __name__ == "__main__":
    main()
