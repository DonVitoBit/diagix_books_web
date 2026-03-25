# Развёртывание

## Локальный запуск для разработки

```bash
python run_web_app.py --host localhost --port 8501
```

## Развёртывание на сервере

### 1. Подготовка окружения

```bash
# На сервере
cd /home/user1/med_book
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Запуск через systemd

Файл `deploy/med_book.service`:

```ini
[Unit]
Description=Text Rephraser Streamlit App
After=network.target

[Service]
Type=simple
User=user1
WorkingDirectory=/home/user1/med_book
Environment="PATH=/home/user1/med_book/.venv/bin"
ExecStart=/home/user1/med_book/.venv/bin/python run_web_app.py --host 127.0.0.1 --port 8501
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Установка:

```bash
sudo cp deploy/med_book.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable med_book
sudo systemctl start med_book
sudo systemctl status med_book
```

### 3. Nginx (обратный прокси + WebSocket)

Streamlit использует WebSocket (`/_stcore/stream`). Без корректной настройки nginx будет ошибка «WebSocket connection failed».

#### Шаг 1: map для WebSocket

В `/etc/nginx/nginx.conf` внутри блока `http { }` добавьте первой строкой:

```nginx
include /home/user1/med_book/deploy/nginx-http-upgrade.conf;
```

#### Шаг 2: Конфиг сайта

```bash
sudo cp deploy/nginx-streamlit.conf /etc/nginx/sites-available/med_book
sudo ln -sf /etc/nginx/sites-available/med_book /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
```

#### Шаг 3: Проверка и перезагрузка

```bash
sudo nginx -t && sudo systemctl reload nginx
```

### 4. Важные параметры nginx

- `proxy_read_timeout` и `proxy_send_timeout` — увеличены для стриминга (например, 86400)
- `proxy_set_header Upgrade $http_upgrade` и `Connection $connection_upgrade` — для WebSocket
- Путь `/_stcore/stream` — без trailing slash

Подробнее: `deploy/README_NGINX.md`, `deploy/WEBSOCKET_FIX.md`.

## Безопасность

1. **Пароль администратора** — изменить в `config.py` перед деплоем.
2. **HTTPS** — настроить SSL в nginx (Let's Encrypt).
3. **API-ключи** — хранятся в `settings.json`; не коммитить в git.
4. **Ограничение доступа** — при необходимости использовать nginx `allow`/`deny` или базовую аутентификацию.

## Переменные окружения

При необходимости можно вынести чувствительные данные в переменные:

```bash
export OPENAI_API_KEY="sk-..."
export ADMIN_PASSWORD="..."
```

И читать их в `config.py` или `settings_manager.py`.

## Логи

- Streamlit: вывод в stdout/stderr (journalctl при systemd)
- Nginx: `/var/log/nginx/error.log`, `/var/log/nginx/access.log`

```bash
sudo journalctl -u med_book -f
```
