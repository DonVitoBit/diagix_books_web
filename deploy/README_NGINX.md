# Настройка nginx для Streamlit (WebSocket)

При доступе через `http://95.174.93.35` (порт 80) WebSocket-соединения Streamlit (`/_stcore/stream`) должны проксироваться с заголовками `Upgrade` и `Connection`. Без этого в браузере будет ошибка «WebSocket connection failed: bad response from the server».

## Быстрая установка на сервере

```bash
# 1. Подключиться к серверу
ssh -i ~/.ssh/id_ed25519 user1@95.174.93.35

# 2. Добавить map для WebSocket в nginx (обязательно для _stcore/stream)
# Вручную откройте /etc/nginx/nginx.conf и внутри блока http { } добавьте первой строкой:
#   include /home/user1/med_book/deploy/nginx-http-upgrade.conf;

# 3. Скопировать конфиг сайта
sudo cp /home/user1/med_book/deploy/nginx-streamlit.conf /etc/nginx/sites-available/med_book

# 4. Включить сайт
sudo ln -sf /etc/nginx/sites-available/med_book /etc/nginx/sites-enabled/

# 5. Удалить default, если конфликтует
sudo rm -f /etc/nginx/sites-enabled/default

# 6. Проверить и перезагрузить nginx
sudo nginx -t && sudo systemctl reload nginx
```

## Если nginx уже настроен

Добавьте в существующий `location /` или создайте отдельный блок:

```nginx
location /_stcore/stream {
    proxy_pass http://127.0.0.1:8501;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 86400;
}
```

**Важно:** путь `/_stcore/stream` — без trailing slash. В конфиге должен быть определён `map $http_upgrade $connection_upgrade` (файл `nginx-http-upgrade.conf`), и в `server` используется `proxy_set_header Connection $connection_upgrade;`.

## Если WebSocket всё равно падает (bad response)

1. Убедитесь, что в `/etc/nginx/nginx.conf` внутри `http { }` есть строка:  
   `include /home/user1/med_book/deploy/nginx-http-upgrade.conf;`
2. Убедитесь, что Streamlit запущен:  
   `cd /home/user1/med_book && source venv/bin/activate && python run_web_app.py --host 0.0.0.0 --port 8501`
3. Проверьте логи: `sudo tail -50 /var/log/nginx/error.log`

## Проверка

После настройки откройте http://95.174.93.35 — приложение должно загружаться без ошибок WebSocket в консоли браузера.
