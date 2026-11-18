#!/bin/sh
# Обновление на сервере после того, как новый код загружен (git pull или rsync).
set -e
cd "$(dirname "$0")/.."
./deploy/backup.sh
docker compose -f docker-compose.prod.yml up -d --build
docker image prune -f
docker compose -f docker-compose.prod.yml ps
