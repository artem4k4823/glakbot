# Деплой на omnitracebot.ru

Схема: один VPS. **Nginx + certbot** стоят прямо на сервере, приложение — в Docker Compose:

```
интернет ──443/80──▶ nginx (хост, сертификат Let's Encrypt от certbot)
                        │ proxy_pass 127.0.0.1:8000
                        ▼
              ┌──── Docker ──────────────────────────┐
              │ dashboard (FastAPI) ── db (Postgres) │
              │ bot (Discord) ─────────┘             │
              └──────────────────────────────────────┘
```

| Компонент | Что делает |
|---|---|
| nginx (хост) | принимает 80/443, HTTPS, проксирует на дашборд |
| certbot (хост) | выпускает сертификат и сам продлевает его (systemd-таймер) |
| `dashboard` | веб-панель; слушает только `127.0.0.1:8000`; при старте применяет миграции БД |
| `bot` | Discord-бот |
| `db` | PostgreSQL, наружу не открыт |

Файлы: `docker-compose.prod.yml`, `deploy/nginx/omnitracebot.ru.conf`, `.env.production.example`, `deploy/backup.sh`, `deploy/update.sh`.

---

## 1. Сервер

- VPS **за пределами РФ** (Нидерланды, Финляндия, Германия и т.п.). Discord в России замедлен/заблокирован — именно из-за этого бот локально не успевал отвечать на команды. Домен `.ru` при этом использовать можно.
- Ubuntu 22.04/24.04, от 1 ГБ RAM (лучше 2 ГБ), 10+ ГБ диска.

## 2. DNS

У регистратора домена создайте записи:

| Тип | Имя | Значение |
|---|---|---|
| A | `@` (omnitracebot.ru) | IP сервера |
| A | `www` | IP сервера |

Проверка (подождите 5–30 минут): `nslookup omnitracebot.ru` должен вернуть IP сервера. **Без этого certbot не выпустит сертификат.**

## 3. Discord Developer Portal

https://discord.com/developers/applications → ваше приложение:

1. **OAuth2 → Redirects** → добавьте `https://omnitracebot.ru/auth/callback` и сохраните.
2. **Bot → Reset Token** и **OAuth2 → Reset Secret** — выпустите новые. Старые лежат в истории git (файлы `.env` были закоммичены), поэтому их лучше считать скомпрометированными. Новые значения пойдут в `.env` на сервере.

## 4. Подготовка сервера

```bash
ssh root@IP_СЕРВЕРА

# Docker
curl -fsSL https://get.docker.com | sh

# Nginx и certbot
apt update
apt install -y nginx certbot python3-certbot-nginx

# Файрвол: только SSH и веб
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

mkdir -p /opt/omnitracebot
```

## 5. Загрузка кода

На своём компьютере (PowerShell, в папке проекта). Сначала закоммитьте изменения — архив собирается из коммита, поэтому `venv`, `.env` и мусор в него не попадут:

```powershell
git add -A
git commit -m "Анкеты и продакшен-деплой"
git archive --format=tar.gz -o omnitracebot.tar.gz HEAD
scp omnitracebot.tar.gz root@IP_СЕРВЕРА:/opt/omnitracebot/
```

На сервере:

```bash
cd /opt/omnitracebot
tar xzf omnitracebot.tar.gz && rm omnitracebot.tar.gz
chmod +x deploy/*.sh
```

> Альтернатива — приватный репозиторий на GitHub и `git clone` на сервере. Но тогда в репозиторий уйдёт история со старыми токенами — обязательно выполните сброс из шага 3.

## 6. Настройка `.env`

```bash
cd /opt/omnitracebot
cp .env.production.example .env
openssl rand -hex 32   # → POSTGRES_PASSWORD
openssl rand -hex 32   # → SECRET_KEY
nano .env
chmod 600 .env
```

Заполните: `BOT_TOKEN`, `CLIENT_ID`, `CLIENT_SECRET`, `SUPERADMIN_IDS` (ваш Discord ID), `POSTGRES_PASSWORD`, `SECRET_KEY`.
`DOMAIN=omnitracebot.ru` уже стоит; `REDIRECT_URI` собирается из него автоматически.

## 7. (Необязательно) Перенос данных с локальной базы

Если нужны уже созданные тикеты, категории и анкеты. На своём компьютере:

```powershell
docker exec snaphelp_postgres pg_dump -U postgres --clean --if-exists snaphelp_db > dump.sql
scp dump.sql root@IP_СЕРВЕРА:/opt/omnitracebot/
```

На сервере **до первого полного запуска**:

```bash
cd /opt/omnitracebot
docker compose -f docker-compose.prod.yml up -d db
sleep 5
docker compose -f docker-compose.prod.yml exec -T db psql -U postgres snaphelp_db < dump.sql
rm dump.sql
```

## 8. Запуск

**Сначала остановите локального бота**, иначе с одним токеном будут работать две копии:

```powershell
docker compose down     # на своём компьютере
```

На сервере:

```bash
cd /opt/omnitracebot
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f bot dashboard caddy
```

Должно быть: в логах бота `... is ready`, у дашборда `Running upgrade ...` / `Uvicorn running`.
Проверка, что панель отвечает локально: `curl -I http://127.0.0.1:8000` → `HTTP/1.1 200`.

## 9. Nginx и HTTPS-сертификат (certbot)

```bash
# Конфиг сайта
cp /opt/omnitracebot/deploy/nginx/omnitracebot.ru.conf /etc/nginx/sites-available/omnitracebot.ru
ln -s /etc/nginx/sites-available/omnitracebot.ru /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# Проверка по http (должна открыться панель)
curl -I http://omnitracebot.ru

# Сертификат + автоматический редирект http → https
certbot --nginx -d omnitracebot.ru -d www.omnitracebot.ru \
  --redirect --agree-tos -m ВАШ_EMAIL --no-eff-email

# Проверка автопродления (сертификат живёт 90 дней, продлевается сам)
certbot renew --dry-run
systemctl list-timers | grep certbot
```

Certbot сам допишет в `/etc/nginx/sites-available/omnitracebot.ru` блок `listen 443 ssl` с путями к сертификату и редирект с 80 на 443.

Откройте https://omnitracebot.ru → «Войти через Discord».

## 10. Автобэкап базы

```bash
cd /opt/omnitracebot && ./deploy/backup.sh      # проверить вручную
crontab -e
# добавить строку:
0 4 * * * cd /opt/omnitracebot && ./deploy/backup.sh >> backups/backup.log 2>&1
```

Копии лежат в `/opt/omnitracebot/backups/`, хранятся последние 14. Иногда скачивайте их к себе:
`scp root@IP_СЕРВЕРА:/opt/omnitracebot/backups/*.sql.gz .`

Восстановление:
`gunzip -c backups/ФАЙЛ.sql.gz | docker compose -f docker-compose.prod.yml exec -T db psql -U postgres snaphelp_db`

## 11. Обновление кода

На компьютере — то же, что в шаге 5 (commit → `git archive` → `scp`). На сервере:

```bash
cd /opt/omnitracebot
tar xzf omnitracebot.tar.gz && rm omnitracebot.tar.gz
./deploy/update.sh     # бэкап → пересборка → перезапуск
```

`.env`, данные БД и конфиг nginx с сертификатом при обновлении не затрагиваются. Если меняли `deploy/nginx/omnitracebot.ru.conf` — не копируйте его поверх рабочего (затрёте блоки certbot), а внесите правки в `/etc/nginx/sites-available/omnitracebot.ru` вручную и выполните `nginx -t && systemctl reload nginx`.

## Полезные команды

```bash
cd /opt/omnitracebot
alias dc='docker compose -f docker-compose.prod.yml'
dc ps                  # статус
dc logs -f --tail 100 bot
dc restart bot
dc down                # остановить всё (данные сохраняются)
```

## Если что-то не работает

| Симптом | Причина / решение |
|---|---|
| certbot: `Connection refused` / `unauthorized` | DNS ещё не указывает на сервер или закрыты порты 80/443 (`ufw status`). |
| `502 Bad Gateway` | Не запущен дашборд: `dc ps`, `dc logs dashboard`; проверка `curl -I http://127.0.0.1:8000`. |
| Логи nginx | `tail -f /var/log/nginx/error.log` |
| После входа через Discord ошибка `redirect_uri` | В Developer Portal не добавлен `https://omnitracebot.ru/auth/callback` (шаг 3). |
| `docker compose` пишет «Укажите … в .env» | Не заполнена переменная в `.env`. |
| Бот онлайн, но команд нет | `Ctrl+R` в Discord; убедитесь, что локальный бот остановлен. |
| Не выдаётся роль при одобрении | Роль бота должна быть выше выдаваемой и иметь «Управлять ролями» — ошибка будет показана в панели. |
