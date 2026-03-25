#!/bin/bash
# Запускать НА СЕРВЕРЕ с sudo: sudo bash /home/user1/med_book/deploy/setup_nginx_websocket.sh
# Настраивает nginx для WebSocket Streamlit (/_stcore/stream), чтобы не было "bad response from the server".

set -e
MED_BOOK_DIR="${1:-/home/user1/med_book}"
NGINX_HTTP_CONF="/etc/nginx/nginx.conf"
UPGRADE_Snippet="map \$http_upgrade \$connection_upgrade {\n    default upgrade;\n    ''      close;\n}\n"

echo "=== Настройка nginx для WebSocket (Streamlit) ==="
echo "Директория проекта: $MED_BOOK_DIR"

# 1. Проверить, что в nginx.conf есть map для connection_upgrade
if grep -q "connection_upgrade\|nginx-http-upgrade" "$NGINX_HTTP_CONF" 2>/dev/null; then
  echo "OK: map connection_upgrade уже есть в $NGINX_HTTP_CONF"
else
  echo ""
  echo "!!! Важно: добавьте вручную в $NGINX_HTTP_CONF внутри блока http { } первой строкой:"
  echo "    include $MED_BOOK_DIR/deploy/nginx-http-upgrade.conf;"
  echo "Затем снова запустите этот скрипт."
  echo ""
  exit 1
fi

# 2. Копировать конфиг сайта
cp "$MED_BOOK_DIR/deploy/nginx-streamlit.conf" /etc/nginx/sites-available/med_book
echo "OK: конфиг скопирован в /etc/nginx/sites-available/med_book"

# 3. Включить сайт
ln -sf /etc/nginx/sites-available/med_book /etc/nginx/sites-enabled/med_book
echo "OK: сайт включён"

# 4. Удалить default при необходимости (опционально)
if [ -f /etc/nginx/sites-enabled/default ]; then
  rm -f /etc/nginx/sites-enabled/default
  echo "OK: default отключён"
fi

# 5. Проверка и перезагрузка
nginx -t && systemctl reload nginx
echo "=== Nginx перезагружен. WebSocket для /_stcore/stream должен работать. ==="
