# Справочник API

## main.py — TextProcessor

### Класс TextProcessor

Основной класс для обработки текста.

```python
from main import TextProcessor

processor = TextProcessor(
    api_key=None,           # Берётся из settings
    temperature=0.4,
    include_research=False,
    style_controls=None
)
```

#### Методы

| Метод | Описание |
|-------|----------|
| `read_input_file(path)` | Извлекает текст из PDF, TXT, MD, DOCX. Возвращает `str`. |
| `process_text(text, theme, callback=None)` | Перефразирует текст по блокам. Возвращает `str`. |
| `process(input_path, output_path, theme)` | Полный цикл: чтение → перефразирование → сохранение. Возвращает `(bool, str)`. |
| `generate_article_plan(theme, audience, num_plan_steps=10)` | Генерирует план статьи (JSON). num_plan_steps: 5–20. Возвращает `List[dict]`. |
| `execute_article_searches(plan, theme, max_chars)` | Поиск в PubMed по плану. Возвращает `(context, sources_list)`. |
| `generate_article_stream(theme, source_texts)` | Стриминг статьи по теме (без плана). Генератор `str`. |
| `generate_article_final_stream(theme, plan, search_context, audience, sources_list)` | Стриминг статьи по плану с PubMed. Генератор `str`. |
| `generate_article_image_prompts(article, num_images)` | Добавляет маркеры и промпты для иллюстраций. Возвращает `(article, prompts)`. |
| `save_file(content, output_path)` | Сохраняет текст в файл. |

#### Исключения

- `QuotaExhaustedError` — исчерпана квота API (частичный результат сохраняется).

---

## core/db.py — База данных

### Функции для книг

| Функция | Описание |
|---------|----------|
| `init_db()` | Инициализация таблиц. |
| `create_book(...)` | Создание книги. |
| `list_books()` | Список всех книг. |
| `get_book(book_id)` | Получение книги по ID. |
| `update_book_paraphrased(book_id, text)` | Обновление переписанного текста. |
| `rename_book(book_id, new_title)` | Переименование. |
| `delete_book(book_id)` | Удаление. |
| `restore_version(book_id, version_id, created_by)` | Восстановление версии. |
| `add_comment(book_id, author, text, paragraph_index)` | Добавление комментария. |

### Функции для модераторов

| Функция | Описание |
|---------|----------|
| `get_moderator_books(username)` | Книги, доступные модератору. |
| `grant_moderator_access(book_id, username, granted_by)` | Выдать доступ. |
| `revoke_moderator_access(book_id, username)` | Отозвать доступ. |

---

## core/pubmed.py — PubMed

| Функция | Описание |
|---------|----------|
| `search_pubmed_ids(query, max_results, sort, theme_in_title_abstract)` | Поиск PMID. При 0 результатах — fallback с первым словом темы. |
| `fetch_pubmed_entries(query, ...)` | Получение статей с аннотациями. |
| `fetch_pubmed_summaries(query, max_results)` | Краткие резюме для контекста. |
| `filter_entries_by_title_relevance(entries, theme, min_words_in_title)` | Фильтрация по границам слов, сортировка по релевантности. |
| `score_entry_by_theme(entry, theme_phrase)` | Оценка релевантности статьи (число слов темы в заголовке). |

---

## core/users.py — Модераторы

| Функция | Описание |
|---------|----------|
| `authenticate_moderator(username, password)` | Проверка логина/пароля. Возвращает объект модератора или `None`. |
| `add_moderator(name, username, password)` | Добавление модератора. |
| `list_moderators()` | Список модераторов. |
| `delete_moderator(username)` | Удаление. |
| `set_moderator_password(username, new_password)` | Смена пароля. |

---

## settings_manager.py

| Функция | Описание |
|---------|----------|
| `get_api_key()` | OpenAI API key. |
| `get_deepseek_api_key()` | DeepSeek API key. |
| `get_gemini_api_key()` | Gemini API key. |
| `get_llm_provider()` | Текущий провайдер: openai, deepseek, gemini. |
| `has_active_api_key()` | Есть ли ключ для текущего провайдера. |
| `get_nanobanana_api_key()`, `get_dalle_api_key()` | Ключи для иллюстраций. |
| `settings_manager.get(key, default)` | Получить настройку. |
| `settings_manager.set(key, value)` | Установить настройку. |

---

## illustration_pipeline.py — IllustrationPipeline

| Метод | Описание |
|-------|----------|
| `extract_images_from_pdf(pdf_path, image_callback)` | Извлечение изображений из PDF. |
| `generate_image_nanobanana(prompt, ...)` | Генерация через NanoBanana API. |
| `redraw_image_with_dalle(prompt, image_path, ...)` | Перерисовка через DALL-E 2. |
| `redraw_image_with_nanobanana(...)` | Перерисовка через NanoBanana. |

---

## CLI (main.py)

```bash
python main.py [OPTIONS]

Options:
  --input-file PATH      Входной файл
  --output-file PATH     Выходной файл (default: output/paraphrased.txt)
  --theme TEXT           Тематика
  --temperature FLOAT    0.0–1.0
  --api-key TEXT         API-ключ
  --provider {openai,deepseek,gemini}  Провайдер LLM
  --include-research     Добавить PubMed-ремарки
  --set-api-key TEXT     Сохранить ключ
  --clear-api-key        Удалить ключ
  --show-settings        Показать настройки
```
