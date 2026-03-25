# Установка и запуск

## Требования

- **Python** 3.8 или выше
- **ОС**: Linux, macOS, Windows
- **Интернет** — для API (OpenAI, DeepSeek, Gemini, PubMed, NanoBanana, DALL-E)

## Шаг 1: Клонирование и виртуальное окружение

```bash
cd /path/to/med_book
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# или
.venv\Scripts\activate      # Windows
```

## Шаг 2: Установка зависимостей

```bash
pip install -r requirements.txt
```

### Основные пакеты

| Пакет | Версия | Назначение |
|-------|--------|------------|
| streamlit | ≥1.28.0 | Веб-интерфейс |
| openai | ≥1.0.0 | Клиент OpenAI API (DeepSeek тоже) |
| PyMuPDF | ≥1.21.0 | Извлечение текста и изображений из PDF |
| python-docx | ≥0.8.11 | Чтение DOCX |
| markdown | ≥3.4.1 | Рендеринг Markdown |
| requests | ≥2.28.0 | HTTP-запросы (Gemini REST, PubMed) |
| tiktoken | ≥0.7.0 | Разбиение текста по токенам |
| langdetect | ≥1.0.9 | Определение языка |

## Шаг 3: Настройка API-ключей

Минимум для перефразирования и генерации статей — один из:

- **OpenAI** — [platform.openai.com](https://platform.openai.com)
- **DeepSeek** — [platform.deepseek.com](https://platform.deepseek.com)
- **Gemini** — [aistudio.google.com](https://aistudio.google.com)

Ключи вводятся в веб-интерфейсе на вкладке **Настройки** и сохраняются в `settings.json`.

## Шаг 4: Запуск веб-приложения

```bash
python run_web_app.py
```

Приложение будет доступно по адресу: **http://localhost:8501**

### Параметры запуска

```bash
python run_web_app.py --host 0.0.0.0 --port 8501
# --host 0.0.0.0 — доступ из сети
# --port 8501 — порт (по умолчанию 8501)
# --install — попытка установить недостающие зависимости
```

### Альтернативный запуск

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

## Шаг 5: Вход в систему

По умолчанию:

- **Логин**: `admin`
- **Пароль**: `admin123`

Изменить в `config.py`:

```python
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
```

## Проверка установки

```bash
# Проверка синтаксиса
python -m py_compile main.py app.py

# Проверка импортов
python -c "from main import TextProcessor; from app import TextRephraserApp; print('OK')"

# Проверка сервера (после запуска)
python check_server.py
```

## Остановка сервера

```bash
# В терминале
Ctrl+C

# Или
python stop_server.py
```

## Устранение проблем

### ModuleNotFoundError

```bash
pip install -r requirements.txt
```

### Ошибка API-ключа

- Убедитесь, что ключ введён в Настройках
- Проверьте провайдер (OpenAI / DeepSeek / Gemini)
- Убедитесь, что ключ действителен и есть квота

### Не удалось извлечь текст из файла

- Проверьте формат: PDF, TXT, MD, DOCX
- Убедитесь, что файл не повреждён и не защищён паролем

### WebSocket connection failed

При доступе через nginx — см. [Развёртывание](DEPLOYMENT.md).
