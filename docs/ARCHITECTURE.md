# Архитектура проекта

## Структура директорий

```
med_book/
├── app.py                    # Точка входа Streamlit, авторизация, табы
├── main.py                   # TextProcessor, CLI, LLM-адаптеры (OpenAI/DeepSeek/Gemini)
├── config.py                 # Константы: температура, лимиты, табы, пароль админа
├── settings_manager.py       # Хранение настроек в settings.json
├── illustration_pipeline.py  # Извлечение/генерация изображений (NanoBanana, DALL-E, TCIA)
├── run_web_app.py            # Запуск Streamlit с проверкой зависимостей
├── check_server.py           # Проверка доступности сервера
├── stop_server.py            # Остановка процесса Streamlit
│
├── core/                     # Ядро приложения
│   ├── db.py                 # SQLite: книги, версии, комментарии, модераторы
│   ├── users.py              # Модераторы, хеширование паролей
│   ├── auth.py               # Верификация паролей
│   ├── pubmed.py             # Поиск статей в PubMed (NCBI E-utilities)
│   ├── pdf_export.py         # Экспорт текста в PDF (PyMuPDF)
│   ├── latex_export.py      # Компиляция LaTeX в PDF
│   └── latex_converter.py    # Конвертация markdown → LaTeX
│
├── ui/                       # Веб-интерфейс
│   ├── base.py               # BaseUI: настройка страницы, табы, session state
│   ├── tabs/
│   │   ├── books_tab.py      # Книги: список, редактирование, версии, доступ
│   │   ├── text_tab.py       # Перефразирование, генерация статей, иллюстрации
│   │   ├── results_tab.py    # Результаты перефразирования
│   │   ├── images_tab.py     # Иллюстрации, перерисовка
│   │   ├── settings_tab.py   # Настройки, API-ключи, провайдер LLM
│   │   └── moderators_tab.py # Управление модераторами (admin)
│   └── components/
│       ├── file_uploader.py  # Загрузка файлов
│       ├── progress_display.py
│       ├── image_gallery.py
│       └── latex_preview.py
│
├── deploy/                   # Развёртывание
│   ├── nginx-streamlit.conf  # Конфиг nginx для Streamlit + WebSocket
│   ├── nginx-http-upgrade.conf
│   ├── med_book.service      # systemd unit
│   └── setup_nginx_websocket.sh
│
├── extracted_images/         # Извлечённые из PDF изображения
├── output/                   # Выходные файлы (original.txt, paraphrased.txt)
├── settings.json             # Настройки (создаётся при первом запуске)
├── app.db                    # SQLite БД (создаётся при первом использовании)
└── requirements.txt
```

## Поток данных

### Перефразирование текста

```
Файл (PDF/TXT/MD/DOCX)
    → TextProcessor.read_input_file()
    → split_block_tokens() / split_block()
    → _paraphrase_one_chunk() [параллельно через ThreadPoolExecutor]
    → OpenAI / DeepSeek / Gemini API
    → process_text() → объединение чанков
    → save_file() или callback в UI
```

### Генерация статьи по теме

```
Тема + (опционально) План
    → generate_article_plan() — LLM генерирует JSON-план
    → execute_article_searches() — PubMed по searchQueries
    → generate_article_final_stream() — стриминг статьи с учётом контекста
    → (опционально) generate_article_image_prompts() + замена маркеров
    → _render_article_display() — Markdown → HTML
```

### Иллюстрации

```
PDF → extract_images_from_pdf() → extracted_images/
Текст статьи → generate_article_image_prompts() → маркеры [ILLUSTRATION_N]
Промпт → NanoBanana API / DALL-E 2 → изображение
Маркер в тексте → замена на <img> в HTML
```

## Роли пользователей

| Роль | Доступ |
|------|--------|
| **admin** | Все табы: Книги, Перефразирование, Результаты, Иллюстрации, Настройки, Модераторы |
| **moderator** | Только Книги (список книг, к которым выдан доступ) |
| **guest** | Только форма входа |

Данные входа: `config.ADMIN_USERNAME`, `config.ADMIN_PASSWORD`. Модераторы хранятся в `core/users.py` (файл `users.json`).

## Провайдеры LLM

Поддерживаются три провайдера (настраивается в Настройках):

1. **OpenAI** — `openai` Python SDK, модели gpt-4o и др.
2. **DeepSeek** — OpenAI-совместимый API (`api.deepseek.com`), модель `deepseek-chat`
3. **Gemini** — REST API `generativelanguage.googleapis.com`, модели `gemini-2.5-flash`, `gemini-2.5-pro` и др.

`TextProcessor` при инициализации выбирает клиент по `settings_manager.get("llm_provider")`.

## База данных (SQLite)

- **books** — переписанные книги (title, original_text, paraphrased_text, theme, temperature, created_by)
- **book_versions** — версии текста с change_note
- **book_comments** — комментарии к абзацам
- **moderator_book_access** — доступ модераторов к книгам
- **moderators** — учётные записи модераторов (в `core/users.py`, отдельный JSON)

## Зависимости между модулями

```
app.py
  ├── ui/base.py
  ├── ui/tabs/*.py
  │     ├── main.TextProcessor
  │     ├── core/db
  │     ├── core/pubmed
  │     ├── illustration_pipeline
  │     └── settings_manager
  └── config

main.py
  ├── settings_manager
  ├── config
  └── core/pubmed
```
