#!/bin/bash

# Настройки сервера
SERVER="user1@95.174.93.35"
REMOTE_DIR="/home/user1/med_book"

echo "🚀 Начинаю быстрый деплой на $SERVER..."

# Синхронизация файлов (исключаем данные, конфиги и виртуальное окружение)
rsync -avz --progress \
    --exclude '.git/' \
    --exclude '.venv/' \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude 'app.db' \
    --exclude 'settings.json' \
    --exclude '.sessions.json' \
    --exclude 'extracted_images/' \
    --exclude 'output/' \
    --exclude 'generated_article_images/' \
    --exclude '*.log' \
    --exclude '*.tar.gz' \
    --exclude '*.zip' \
    --exclude 'app.py.backup*' \
    --exclude '.DS_Store' \
    --exclude 'node_modules/' \
    --exclude '_frontend_repo/' \
    --exclude 'frontend/' \
    ./ "$SERVER:$REMOTE_DIR/"

echo "🔄 Перезапуск сервиса med_book..."
ssh "$SERVER" "sudo -n systemctl restart med_book"

if [ $? -eq 0 ]; then
    echo "✅ Деплой успешно завершен! Приложение перезапущено."
    echo "🌐 Адрес: http://95.174.93.35:8501"
else
    echo "❌ Ошибка при перезапуске сервиса."
fi
