"""Alembic 环境：从 .env 读 DATABASE_URL，从 app.db.base 读模型 metadata"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# 让 alembic 能 import 到 app 包
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from app.db.base import Base  # noqa: E402
# 必须在 Base 之后导入所有模型，让它们注册到 Base.metadata
from app.models.teacher import Teacher  # noqa: E402,F401
from app.models.class_ import Class  # noqa: E402,F401
from app.models.student import Student  # noqa: E402,F401
from app.models.pet import Pet  # noqa: E402,F401
from app.models.behavior import Behavior  # noqa: E402,F401
from app.models.subject import Subject  # noqa: E402,F401
from app.models.score_rule import ScoreRule  # noqa: E402,F401
from app.models.homework import Homework  # noqa: E402,F401
from app.models.homework_record import HomeworkRecord  # noqa: E402,F401
from app.models.shop_item import ShopItem  # noqa: E402,F401
from app.models.pet_owned_item import PetOwnedItem  # noqa: E402,F401
from app.models.word_group import WordGroup  # noqa: E402,F401
from app.models.word import Word  # noqa: E402,F401
from app.models.pet_species import PetSpecies, PetSpeciesAsset  # noqa: E402,F401

config = context.config
# 用 .env 的 DATABASE_URL 覆盖 alembic.ini 里的占位符
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        # SQLite 启用外键约束
        if connection.dialect.name == "sqlite":
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=connection.dialect.name == "sqlite",  # SQLite ALTER 兼容
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
