"""seed: add house and furniture shop items

Revision ID: 95f48e1bb9f1
Revises: b0e3c966c295
Create Date: 2026-05-02 01:24:42.727918

新增 2 类商品：
- 房子（3 件）：宠物的家，同类互斥（一次只能激活一个）
- 家具（5 件）：装饰房子，不互斥（可同时摆放多件）
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '95f48e1bb9f1'
down_revision: Union[str, Sequence[str], None] = 'b0e3c966c295'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    shop_items_table = sa.table(
        'shop_items',
        sa.column('name', sa.String),
        sa.column('item_type', sa.String),
        sa.column('price', sa.Integer),
        sa.column('icon', sa.String),
        sa.column('description', sa.String),
        sa.column('effect_hunger', sa.Integer),
        sa.column('effect_mood', sa.Integer),
        sa.column('consumable', sa.Boolean),
        sa.column('sort_order', sa.Integer),
    )
    op.bulk_insert(shop_items_table, [
        # 房子（3 件，互斥）—— consumable=false 表示可重复装备/卸下
        {'name': '简易木屋', 'item_type': '房子', 'price': 300, 'icon': '🛖',
         'description': '温馨的小木屋，宠物的第一个家',
         'effect_hunger': 0, 'effect_mood': 0, 'consumable': False, 'sort_order': 31},
        {'name': '温馨小屋', 'item_type': '房子', 'price': 600, 'icon': '🏡',
         'description': '带烟囱的乡村小屋',
         'effect_hunger': 0, 'effect_mood': 0, 'consumable': False, 'sort_order': 32},
        {'name': '梦幻城堡', 'item_type': '房子', 'price': 1500, 'icon': '🏰',
         'description': '只有积分大佬才配拥有',
         'effect_hunger': 0, 'effect_mood': 0, 'consumable': False, 'sort_order': 33},
        # 家具（5 件，不互斥，多件并存装饰）
        {'name': '椅子', 'item_type': '家具', 'price': 50, 'icon': '🪑',
         'description': '简单的椅子',
         'effect_hunger': 0, 'effect_mood': 0, 'consumable': False, 'sort_order': 41},
        {'name': '盆栽', 'item_type': '家具', 'price': 60, 'icon': '🪴',
         'description': '让房间充满生机',
         'effect_hunger': 0, 'effect_mood': 0, 'consumable': False, 'sort_order': 42},
        {'name': '沙发', 'item_type': '家具', 'price': 80, 'icon': '🛋️',
         'description': '舒服的沙发',
         'effect_hunger': 0, 'effect_mood': 0, 'consumable': False, 'sort_order': 43},
        {'name': '画作', 'item_type': '家具', 'price': 100, 'icon': '🖼️',
         'description': '挂在墙上的艺术品',
         'effect_hunger': 0, 'effect_mood': 0, 'consumable': False, 'sort_order': 44},
        {'name': '床', 'item_type': '家具', 'price': 120, 'icon': '🛏️',
         'description': '让宠物好好休息',
         'effect_hunger': 0, 'effect_mood': 0, 'consumable': False, 'sort_order': 45},
    ])


def downgrade() -> None:
    # 按名字精确删除（避免误删用户自建项 —— 但当前商品全是预置的）
    op.execute(
        "DELETE FROM shop_items WHERE name IN "
        "('简易木屋','温馨小屋','梦幻城堡','椅子','盆栽','沙发','画作','床')"
    )
