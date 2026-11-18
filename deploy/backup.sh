#!/bin/sh
# Резервная копия базы: ./deploy/backup.sh  → backups/snaphelp_YYYY-MM-DD_HHMM.sql.gz
# Хранит последние 14 копий. Для ежедневного запуска добавьте в crontab:
#   0 4 * * * cd /opt/omnitracebot && ./deploy/backup.sh >> backups/backup.log 2>&1
set -e
cd "$(dirname "$0")/.."
mkdir -p backups
FILE="backups/snaphelp_$(date +%Y-%m-%d_%H%M).sql.gz"
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U postgres snaphelp_db | gzip > "$FILE"
ls -1t backups/snaphelp_*.sql.gz | tail -n +15 | xargs -r rm --
echo "OK: $FILE"
