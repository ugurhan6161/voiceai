#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  VoiceAI Platform — Otomatik Yedekleme Scripti
#  Cron: 0 2 * * * /opt/voiceai/scripts/backup.sh
#  Not: INSTALL_DIR env değişkeni ile farklı dizin belirtilebilir.
# ─────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${INSTALL_DIR:-$(dirname "$SCRIPT_DIR")}"
BACKUP_DIR="${BACKUP_DIR:-$INSTALL_DIR/backups}"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# shellcheck source=/dev/null
if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo "❌ HATA: $INSTALL_DIR/.env bulunamadı. INSTALL_DIR değişkenini kontrol edin." >&2
    exit 1
fi
source "$INSTALL_DIR/.env"

mkdir -p "$BACKUP_DIR"

echo "🗄️ Yedekleme başlıyor: $DATE"

# PostgreSQL yedeği
echo "📦 PostgreSQL yedekleniyor..."
docker exec voiceai-postgres pg_dumpall -U $POSTGRES_USER \
  | gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

# Yedek boyutunu göster
BACKUP_SIZE=$(du -sh "$BACKUP_DIR/postgres_$DATE.sql.gz" | cut -f1)
echo "✅ PostgreSQL yedeği: $BACKUP_SIZE"

# Eski yedekleri temizle
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
echo "🗑️  $RETENTION_DAYS günden eski yedekler silindi"

# Uzak depolama (rclone varsa)
if command -v rclone &> /dev/null && [ ! -z "$RCLONE_REMOTE" ]; then
  echo "☁️  Uzak depolamaya yükleniyor..."
  rclone copy "$BACKUP_DIR/postgres_$DATE.sql.gz" \
    "$RCLONE_REMOTE:$RCLONE_PATH/"
  echo "✅ Uzak yedekleme tamamlandı"
fi

echo "✅ Yedekleme tamamlandı: $DATE"
