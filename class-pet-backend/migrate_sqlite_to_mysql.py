"""SQLite → MySQL 数据迁移工具

执行步骤（请严格按顺序）：

  1. 装 MySQL 8 并启动服务
  2. 创建数据库 + 用户：
       CREATE DATABASE teacher_app DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
       CREATE USER 'classpet'@'localhost' IDENTIFIED BY 'your_strong_password';
       GRANT ALL ON teacher_app.* TO 'classpet'@'localhost';
       FLUSH PRIVILEGES;
  3. 备份 SQLite：cp class_pet.db backups/class_pet_pre_migration.db
  4. 改 .env 的 DATABASE_URL：
       DATABASE_URL=mysql+pymysql://classpet:your_strong_password@127.0.0.1:3306/teacher_app?charset=utf8mb4
  5. 运行：python init_db.py   （让 MySQL 建好所有表）
  6. 运行：python migrate_sqlite_to_mysql.py
  7. 启动服务，验证数据

⚠️ 警告：脚本会覆盖目标 MySQL 中所有业务表数据。
"""
import argparse
import io
import os
import sqlite3
import sys
from pathlib import Path

# 让 import 到 app 包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from sqlalchemy import create_engine, text  # noqa: E402

from app.core.config import settings  # noqa: E402


# 表迁移顺序：外键被引用的表先迁
TABLE_ORDER = [
    "teachers",
    "classes",
    "students",
    "pets",
    "subjects",
    "score_rules",
    "behaviors",
    "shop_items",
    "pet_owned_items",
    "homeworks",
    "homework_records",
    "word_groups",
    "words",
    "pet_species",
    "pet_species_assets",
]


def assert_mysql() -> None:
    if not settings.DATABASE_URL.startswith("mysql"):
        print(f"[ABORT] 当前 DATABASE_URL 不是 MySQL：{settings.DATABASE_URL}")
        print("        请先改 .env 的 DATABASE_URL 为 mysql+pymysql://... 再运行")
        sys.exit(1)


def open_sqlite(path: str) -> sqlite3.Connection:
    if not Path(path).exists():
        print(f"[ABORT] SQLite 文件不存在：{path}")
        sys.exit(1)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def get_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]


def migrate_table(src: sqlite3.Connection, dst_conn, table: str) -> int:
    cols_src = get_columns(src, table)
    if not cols_src:
        print(f"  [{table}] SQLite 中无此表，跳过")
        return 0
    rows = list(src.execute(f"SELECT * FROM {table}"))
    if not rows:
        # 至少清一下目标表（避免 init_db.py 的 seed 残留与源数据冲突）
        dst_conn.execute(text(f"DELETE FROM {table}"))
        print(f"  [{table}] 0 行（已清空目标表）")
        return 0

    # 清空目标表
    dst_conn.execute(text(f"DELETE FROM {table}"))

    # 插入：用源端列顺序
    placeholders = ", ".join(f":{c}" for c in cols_src)
    cols_sql = ", ".join(f"`{c}`" for c in cols_src)
    insert_sql = f"INSERT INTO `{table}` ({cols_sql}) VALUES ({placeholders})"

    inserted = 0
    for row in rows:
        params = {c: row[c] for c in cols_src}
        dst_conn.execute(text(insert_sql), params)
        inserted += 1

    # 重置 AUTO_INCREMENT 到 max(id)+1（如果表有 id 列）
    if "id" in cols_src:
        max_id_row = dst_conn.execute(text(f"SELECT MAX(id) FROM `{table}`")).first()
        if max_id_row and max_id_row[0] is not None:
            dst_conn.execute(text(f"ALTER TABLE `{table}` AUTO_INCREMENT = {int(max_id_row[0]) + 1}"))

    return inserted


def migrate_alembic_version(src: sqlite3.Connection, dst_conn) -> None:
    rows = list(src.execute("SELECT version_num FROM alembic_version"))
    if not rows:
        return
    version = rows[0][0]
    dst_conn.execute(text("DELETE FROM alembic_version"))
    dst_conn.execute(text("INSERT INTO alembic_version (version_num) VALUES (:v)"),
                     {"v": version})
    print(f"  [alembic_version] {version}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", default="class_pet.db", help="SQLite 源数据库文件路径")
    parser.add_argument("--yes", action="store_true", help="跳过确认提示直接执行")
    args = parser.parse_args()

    assert_mysql()
    print(f"目标 MySQL：{settings.DATABASE_URL.split('@')[-1].split('?')[0]}")
    print(f"源 SQLite ：{args.src}\n")

    if not args.yes:
        ans = input("⚠️  将覆盖目标 MySQL 中所有业务表数据，继续？输入 yes 确认：")
        if ans.strip().lower() != "yes":
            print("已取消")
            return

    src = open_sqlite(args.src)
    dst_engine = create_engine(settings.DATABASE_URL)

    print("\n开始迁移 ...")
    total = 0
    with dst_engine.begin() as dst_conn:
        # 暂关外键约束，避免插入顺序问题
        dst_conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        try:
            for tbl in TABLE_ORDER:
                cnt = migrate_table(src, dst_conn, tbl)
                if cnt > 0:
                    print(f"  [{tbl}] {cnt} 行")
                total += cnt
            migrate_alembic_version(src, dst_conn)
        finally:
            dst_conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    print(f"\n[DONE] 迁移完成，共 {total} 行业务数据已搬到 MySQL")
    print("       验证：python -m uvicorn app.main:app  然后访问 /docs")


if __name__ == "__main__":
    main()
