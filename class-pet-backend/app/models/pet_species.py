"""宠物物种字典 + 等级资源映射（全局共享，所有老师可用）

- pet_species：物种主表（code 对应 students.pet.species 字段值）
- pet_species_assets：物种 × 等级阈值 → 资源（emoji 优先，image_url 留给下次迭代）

Fallback 由前端按 level 查找：取 species 下 level<=current_level 中最大那档。
"""
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PetSpecies(Base):
    __tablename__ = "pet_species"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)   # 'dragon' / 'cat' ...
    name: Mapped[str] = mapped_column(String(50), nullable=False)                # '小龙' / '小猫' ...
    description: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    assets: Mapped[list["PetSpeciesAsset"]] = relationship(
        back_populates="species", cascade="all, delete-orphan",
    )


class PetSpeciesAsset(Base):
    __tablename__ = "pet_species_assets"
    __table_args__ = (
        UniqueConstraint("species_id", "level", name="uq_species_level"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    species_id: Mapped[int] = mapped_column(
        ForeignKey("pet_species.id", ondelete="CASCADE"), index=True, nullable=False
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)         # 等级阈值（≥ 此 level 时启用）
    emoji: Mapped[str] = mapped_column(String(8), nullable=False, default="🥚")
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    species: Mapped["PetSpecies"] = relationship(back_populates="assets")
