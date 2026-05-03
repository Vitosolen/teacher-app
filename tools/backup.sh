#!/usr/bin/env bash
# 班级养宠物系统 · SQLite 数据库自动备份（macOS / Linux）
#
# 用法：
#   chmod +x tools/backup.sh
#   ./tools/backup.sh
#
# 定时（每天凌晨 2 点）：
#   crontab -e
#   0 2 * * * /path/to/teacher-app/tools/backup.sh >> /tmp/class-pet-backup.log 2>&1

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/class-pet-backend/class_pet.db"
BACKUP_DIR="$ROOT/backups"
KEEP_DAYS=30

if [ ! -f "$SRC" ]; then
    echo "[错误] 数据库不存在：$SRC"
    exit 1
fi

mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M")
DST="$BACKUP_DIR/class_pet_$TIMESTAMP.db"

cp "$SRC" "$DST"
SIZE_KB=$(du -k "$DST" | cut -f1)
echo "[OK] 备份成功 → $DST (${SIZE_KB} KB)"

# 清理超期备份
DELETED=$(find "$BACKUP_DIR" -name 'class_pet_*.db' -mtime +$KEEP_DAYS -delete -print | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "[清理] 删除 $DELETED 个超 ${KEEP_DAYS} 天的旧备份"
fi

echo
echo "现有备份："
ls -lhS "$BACKUP_DIR"/class_pet_*.db 2>/dev/null | head -10
