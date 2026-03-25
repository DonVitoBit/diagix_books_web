# Исправление ошибок WebSocket (Streamlit за nginx)

Если в консоли браузера одна из ошибок:
- `WebSocket connection to 'ws://95.174.93.35/_stcore/stream' failed: There was a bad response from the server`
- `WebSocket connection to '.../_stcore/stream' failed: The network connection was lost`

то nginx не проксирует WebSocket или обрывает долгие соединения. Сделайте на сервере:

## 1. Подключиться к серверу

```bash
ssh -i ~/.ssh/id_ed25519 user1@95.174.93.35
```

## 2. Добавить поддержку WebSocket в nginx

**Вариант А — вручную (надёжно):**

```bash
# Открыть главный конфиг
sudo nano /etc/nginx/nginx.conf
```

Внутри блока `http { }` добавьте **самой первой строкой** (сразу после `http {`):

```
include /home/user1/med_book/deploy/nginx-http-upgrade.conf;
```

Сохраните (Ctrl+O, Enter, Ctrl+X).

**Вариант Б — скрипт:**

```bash
sudo bash /home/user1/med_book/deploy/setup_nginx_websocket.sh
```

Если скрипт напишет «Добавьте вручную» — выполните Вариант А.

## 3. Включить конфиг сайта и перезагрузить nginx

```bash
sudo cp /home/user1/med_book/deploy/nginx-streamlit.conf /etc/nginx/sites-available/med_book
sudo ln -sf /etc/nginx/sites-available/med_book /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

## 4. Убедиться, что Streamlit запущен

Если приложение под systemd:

```bash
sudo systemctl restart med_book
```

Если запускаете вручную:

```bash
cd /home/user1/med_book && source venv/bin/activate && python run_web_app.py --host 0.0.0.0 --port 8501
```

После этого откройте снова http://95.174.93.35 — ошибка WebSocket должна пропасть.
