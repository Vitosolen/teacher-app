"""一键数据库初始化（首次安装用）

绕过 alembic 在 SQLite + Windows 下偶发不 commit 的问题。
做法：直接用 SQLAlchemy create_all 建表 + 手动写入 alembic_version + 写入 seed 数据。

幂等：重复跑不会破坏已有数据；表已存在不会再建，seed 已存在不会重复插。
"""
from datetime import datetime
import io
import os
from pathlib import Path

# 让 alembic 等工具能 import 到 app 包
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Windows cmd 默认 GBK，强制 UTF-8 输出避免中文 / emoji 报错
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from sqlalchemy import inspect, text
from app.db.base import Base
from app.db.session import engine

# 必须导入所有 model 才能让 metadata 注册到位
from app.models.teacher import Teacher  # noqa: F401
from app.models.class_ import Class  # noqa: F401
from app.models.student import Student  # noqa: F401
from app.models.pet import Pet  # noqa: F401
from app.models.behavior import Behavior  # noqa: F401
from app.models.subject import Subject  # noqa: F401
from app.models.score_rule import ScoreRule  # noqa: F401
from app.models.homework import Homework  # noqa: F401
from app.models.homework_record import HomeworkRecord  # noqa: F401
from app.models.shop_item import ShopItem  # noqa: F401
from app.models.pet_owned_item import PetOwnedItem  # noqa: F401
from app.models.word_group import WordGroup  # noqa: F401
from app.models.word import Word  # noqa: F401
from app.models.pet_species import PetSpecies, PetSpeciesAsset  # noqa: F401


# 与 alembic/versions/ 下最新文件保持同步：每次新增迁移更新此值
LATEST_ALEMBIC_HEAD = "b38c3ba0c167"


def init_schema() -> None:
    """建表（幂等）"""
    Base.metadata.create_all(engine)
    print("[OK] 数据库表已创建（或已存在）")


def stamp_alembic_version() -> None:
    """写入/更新 alembic_version 让后续迁移能正确识别起点"""
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL PRIMARY KEY
            )
        """))
        existing = list(conn.execute(text("SELECT version_num FROM alembic_version")))
        if not existing:
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES (:v)"),
                         {"v": LATEST_ALEMBIC_HEAD})
            print(f"✓ alembic_version 设置为 {LATEST_ALEMBIC_HEAD}")
        else:
            print(f"✓ alembic_version 已存在：{existing[0][0]}")


def seed_shop_items() -> None:
    """商品池预置：4 食品 + 5 衣服 + 3 玩具 + 3 房子 + 5 家具 = 20 件"""
    items = [
        # 食品
        ("苹果", "食品", 10, "🍎", "清甜可口的苹果", 5, 0, True, 1),
        ("胡萝卜", "食品", 15, "🥕", "宠物最爱", 10, 0, True, 2),
        ("蛋糕", "食品", 30, "🍰", "吃了心情愉悦", 20, 5, True, 3),
        ("大餐", "食品", 50, "🍖", "丰盛大餐，效果显著", 30, 5, True, 4),
        # 衣服
        ("蝴蝶结", "衣服", 30, "🎀", "可爱的蝴蝶结", 0, 0, False, 11),
        ("围巾", "衣服", 40, "🧣", "保暖又时尚", 0, 0, False, 12),
        ("礼帽", "衣服", 50, "🎩", "绅士风度", 0, 0, False, 13),
        ("墨镜", "衣服", 60, "🕶️", "酷酷的造型", 0, 0, False, 14),
        ("皇冠", "衣服", 200, "👑", "尊贵的象征", 0, 0, False, 15),
        # 玩具
        ("小球", "玩具", 20, "⚽", "玩耍专用", 0, 10, True, 21),
        ("玩偶", "玩具", 40, "🧸", "柔软的伙伴", 0, 20, True, 22),
        ("游戏机", "玩具", 100, "🎮", "欢乐时光", 0, 40, True, 23),
        # 房子
        ("简易木屋", "房子", 300, "🛖", "温馨的小木屋，宠物的第一个家", 0, 0, False, 31),
        ("温馨小屋", "房子", 600, "🏡", "带烟囱的乡村小屋", 0, 0, False, 32),
        ("梦幻城堡", "房子", 1500, "🏰", "只有积分大佬才配拥有", 0, 0, False, 33),
        # 家具
        ("椅子", "家具", 50, "🪑", "简单的椅子", 0, 0, False, 41),
        ("盆栽", "家具", 60, "🪴", "让房间充满生机", 0, 0, False, 42),
        ("沙发", "家具", 80, "🛋️", "舒服的沙发", 0, 0, False, 43),
        ("画作", "家具", 100, "🖼️", "挂在墙上的艺术品", 0, 0, False, 44),
        ("床", "家具", 120, "🛏️", "让宠物好好休息", 0, 0, False, 45),
    ]
    with engine.begin() as conn:
        existing = {r[0] for r in conn.execute(text("SELECT name FROM shop_items"))}
        added = 0
        for name, t, price, icon, desc, eh, em, cons, order in items:
            if name in existing:
                continue
            conn.execute(text("""
                INSERT INTO shop_items (name, item_type, price, icon, description,
                    effect_hunger, effect_mood, consumable, sort_order)
                VALUES (:n, :t, :p, :i, :d, :eh, :em, :c, :o)
            """), {
                "n": name, "t": t, "p": price, "i": icon, "d": desc,
                "eh": eh, "em": em, "c": cons, "o": order,
            })
            added += 1
        print(f"✓ 商品池：新增 {added} 件，总计 {len(existing) + added} 件")


def seed_pet_species() -> None:
    """6 种宠物 × 4 阶段成长 emoji（共 20 条资源）"""
    now = datetime.utcnow().isoformat()
    species_data = [
        ('dragon', '小龙', '神秘强大的小龙', 1,
         [(1, '🥚'), (2, '🦎'), (3, '🐉'), (5, '🐲')]),
        ('cat', '小猫', '可爱的小猫咪', 2,
         [(1, '🥚'), (2, '🐈'), (3, '🐱'), (5, '😺')]),
        ('dog', '小狗', '忠诚的小狗狗', 3,
         [(1, '🥚'), (2, '🐕'), (3, '🐶'), (5, '🦮')]),
        ('rabbit', '小兔', '蹦蹦跳跳的小兔', 4,
         [(1, '🥚'), (2, '🐰'), (3, '🐇'), (5, '🐰')]),
        ('panda', '熊猫', '圆滚滚的小熊猫', 5,
         [(1, '🥚'), (2, '🐼')]),
        ('fox', '狐狸', '机灵的小狐狸', 6,
         [(1, '🥚'), (2, '🦊')]),
    ]
    with engine.begin() as conn:
        existing_codes = {r[0] for r in conn.execute(text("SELECT code FROM pet_species"))}
        sp_added = 0
        as_added = 0
        for code, name, desc, order, assets in species_data:
            if code not in existing_codes:
                conn.execute(text("""
                    INSERT INTO pet_species (code, name, description, sort_order, created_at)
                    VALUES (:c, :n, :d, :o, :ts)
                """), {"c": code, "n": name, "d": desc, "o": order, "ts": now})
                sp_added += 1
            sid = conn.execute(text("SELECT id FROM pet_species WHERE code = :c"),
                               {"c": code}).scalar()
            existing_levels = {
                r[0] for r in conn.execute(text(
                    "SELECT level FROM pet_species_assets WHERE species_id = :sid"
                ), {"sid": sid})
            }
            for level, emoji in assets:
                if level in existing_levels:
                    continue
                conn.execute(text("""
                    INSERT INTO pet_species_assets (species_id, level, emoji, image_url, created_at)
                    VALUES (:sid, :lv, :e, NULL, :ts)
                """), {"sid": sid, "lv": level, "e": emoji, "ts": now})
                as_added += 1
        print(f"✓ 宠物物种：新增 {sp_added} 种 + {as_added} 条等级资源")


def main() -> None:
    db_file = engine.url.database
    if db_file:
        is_new = not Path(db_file).exists() if db_file != ":memory:" else False
        print(f"数据库文件：{db_file} ({'首次创建' if is_new else '已存在'})")

    # 1. 建表
    init_schema()
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"  共 {len(tables)} 张表：{', '.join(sorted(tables))}")

    # 2. 写入 alembic 版本号
    stamp_alembic_version()

    # 3. seed 公共数据
    seed_shop_items()
    seed_pet_species()

    # 注：注册老师时会自动复制 9 条默认积分规则给该老师，无需此处 seed

    print("\n[DONE] 初始化完成！")
    print("   启动后端：  uvicorn app.main:app --reload")
    print("   API 文档：  http://127.0.0.1:8000/docs")


if __name__ == "__main__":
    main()
