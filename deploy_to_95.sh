#!/bin/bash
# Деплой med_book на 95.174.93.35. Один скрипт: архив → загрузка → распаковка → venv → перезапуск.
# Требования: ssh-ключ с доступом user1@95.174.93.35, на сервере — python3, python3-venv, systemd (med_book).

set -e
HOST="95.174.93.35"
USER="user1"
REMOTE_DIR="/home/user1/med_book"
SSH_KEY="${HOME}/.ssh/id_ed25519"
ARCHIVE="med_book_deploy.tar.gz"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ---- 1) Сборка архива (только нужное для запуска, без тяжёлых каталогов) ----
echo "[1/5] Сборка архива..."
tar --exclude='.venv' \
    --exclude='venv' \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='frontend/node_modules' \
    --exclude='_frontend_repo' \
    --exclude='extracted_images' \
    --exclude='*.tar.gz' \
    --exclude='deploy.tar.gz' \
    --exclude='diagix_books_web.tar.gz' \
    --exclude='app.py.backup' \
    --exclude='app.py.backup2' \
    --exclude='app.py.backup_final' \
    --exclude="$ARCHIVE" \
    -czf "$ARCHIVE" .
echo "      Размер: $(du -h "$ARCHIVE" | cut -f1)"

# ---- 2) Загрузка ----
echo "[2/5] Загрузка на $USER@$HOST..."
scp -o StrictHostKeyChecking=no -o ConnectTimeout=30 ${SSH_KEY:+-i "$SSH_KEY"} "$ARCHIVE" "$USER@$HOST:/tmp/"

# ---- 3) Развёртывание на сервере ----
echo "[3/5] Развёртывание на сервере..."
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 ${SSH_KEY:+-i "$SSH_KEY"} "$USER@$HOST" "bash -s" -- "$REMOTE_DIR" "/tmp/$ARCHIVE" << 'REMOTE'
set -e
REMOTE_DIR="${1:-/home/user1/med_book}"
ARCHIVE_PATH="${2:-/tmp/med_book_deploy.tar.gz}"

# Бэкап данных (не терять при перезаливке)
BACKUP="/tmp/med_book_deploy_backup_$$"
mkdir -p "$BACKUP"
[ -f "$REMOTE_DIR/settings.json" ] && cp "$REMOTE_DIR/settings.json" "$BACKUP/"
[ -f "$REMOTE_DIR/app.db" ]        && cp "$REMOTE_DIR/app.db" "$BACKUP/"
[ -f "$REMOTE_DIR/users.json" ]    && cp "$REMOTE_DIR/users.json" "$BACKUP/"
[ -d "$REMOTE_DIR/venv" ]          && mv "$REMOTE_DIR/venv" "$BACKUP/venv"

# Очистка и распаковка
rm -rf "$REMOTE_DIR"
mkdir -p "$REMOTE_DIR"
cd "$REMOTE_DIR"
tar -xzf "$ARCHIVE_PATH"
rm -f "$ARCHIVE_PATH"

# Восстановление данных
[ -f "$BACKUP/settings.json" ] && mv "$BACKUP/settings.json" "$REMOTE_DIR/"
[ -f "$BACKUP/app.db" ]        && mv "$BACKUP/app.db" "$REMOTE_DIR/"
[ -f "$BACKUP/users.json" ]    && mv "$BACKUP/users.json" "$REMOTE_DIR/"
[ -d "$BACKUP/venv" ]          && mv "$BACKUP/venv" "$REMOTE_DIR/venv"
rm -rf "$BACKUP"

# Виртуальное окружение: если нет — создать и поставить зависимости
if [ ! -f "$REMOTE_DIR/venv/bin/python" ]; then
  echo "      Создание venv и установка зависимостей..."
  cd "$REMOTE_DIR"
  python3 -m venv venv
  ./venv/bin/pip install -q --upgrade pip
  ./venv/bin/pip install -q -r requirements.txt
else
  echo "      Обновление зависимостей в существующем venv..."
  "$REMOTE_DIR/venv/bin/pip" install -q --upgrade pip
  "$REMOTE_DIR/venv/bin/pip" install -q -r requirements.txt
fi

# Права на скрипты
chmod +x "$REMOTE_DIR/scripts/"*.sh 2>/dev/null || true
REMOTE

# ---- 4) Перезапуск приложения и обновление nginx (WebSocket) ----
echo "[4/5] Обновление nginx для WebSocket..."
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 ${SSH_KEY:+-i "$SSH_KEY"} "$USER@$HOST" "sudo cp $REMOTE_DIR/deploy/nginx-streamlit.conf /etc/nginx/sites-available/med_book && sudo nginx -t && sudo systemctl reload nginx" 2>/dev/null && echo "      Nginx обновлён и перезагружен." || echo "      Nginx не обновлён (нужен sudo). При ошибке WebSocket выполните на сервере: sudo bash $REMOTE_DIR/deploy/setup_nginx_websocket.sh"

echo "[5/5] Перезапуск med_book..."
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 ${SSH_KEY:+-i "$SSH_KEY"} "$USER@$HOST" "sudo systemctl restart med_book" 2>/dev/null && echo "      Сервис перезапущен." || echo "      Не удалось выполнить sudo systemctl restart med_book — перезапустите вручную на сервере."

echo ""
echo "=== Деплой завершён ==="
echo "Приложение: http://$HOST/"
