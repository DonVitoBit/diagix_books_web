# Конфигурация

## Файл настроек: settings.json

Создаётся при первом запуске. Сохраняется в корне проекта.

### Структура

```json
{
  "openai_api_key": "",
  "deepseek_api_key": "",
  "gemini_api_key": "",
  "gemini_model": "gemini-2.5-flash",
  "llm_provider": "openai",
  "model": "gpt-4o",
  "deepseek_model": "deepseek-chat",
  "temperature": 0.4,
  "max_tokens": 8192,
  "max_tokens_article": 32768,
  "include_research": false,
  "plan_steps": 10,
  "style_science": 3,
  "style_depth": 3,
  "style_accuracy": 3,
  "style_readability": 3,
  "style_source_quality": 3,
  "nanobanana_api_key": "",
  "dalle_api_key": "",
  "google_search_api_key": "",
  "google_search_engine_id": "",
  "tavily_api_key": "",
  "auto_illustration": false,
  "illustration_quality": "high",
  "brand_style": "medical",
  "tcia_enabled": false,
  "tcia_timeout": 30
}
```

## Параметры (config.py)

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `MAX_CHUNK_LENGTH` | Размер чанка в токенах для перефразирования | 600 |
| `MAX_CONCURRENT_REQUESTS` | Параллельных запросов к API в блоке | 4 |
| `SUPPORTED_FILE_TYPES` | Поддерживаемые форматы | pdf, txt, md, docx |
| `MAX_FILE_SIZE` | Макс. размер файла (байт) | 10 MB |
| `EXTRACTED_IMAGES_DIR` | Папка для извлечённых изображений | extracted_images |
| `DEFAULT_TEMPERATURE` | Температура по умолчанию | 0.4 |
| `MIN_TEMPERATURE` / `MAX_TEMPERATURE` | Диапазон | 0.0–1.0 |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Учётные данные администратора | admin / admin123 |

## Провайдеры LLM

| Провайдер | Ключ | Модели |
|-----------|------|--------|
| **openai** | `openai_api_key` | gpt-4o, gpt-4 и др. |
| **deepseek** | `deepseek_api_key` | deepseek-chat |
| **gemini** | `gemini_api_key` | gemini-2.5-flash, gemini-2.5-pro, gemini-3-*-preview |

## API-ключи для иллюстраций

| Сервис | Ключ | Назначение |
|--------|------|------------|
| **NanoBanana** | `nanobanana_api_key` | Генерация изображений (api.nanobananaapi.ai) |
| **DALL-E 2** | `dalle_api_key` или `openai_api_key` | Генерация через OpenAI |
| **Google Custom Search** | `google_search_api_key` + `google_search_engine_id` | Поиск клинических изображений |
| **Tavily** | `tavily_api_key` | Поиск медицинских изображений |
| **TCIA** | — | Бесплатный доступ к медицинским изображениям (`tcia_enabled`) |

## Управление стилем статьи (1–5)

| Параметр | Описание |
|----------|----------|
| `style_science` | Научность и глубина |
| `style_depth` | Детализация |
| `style_accuracy` | Точность и доказательность |
| `style_readability` | Читаемость |
| `style_source_quality` | Качество источников |
| `plan_steps` | Количество пунктов плана при генерации статьи по теме (5–20) |

## Temperature (уровень перефразирования)

| Диапазон | Режим | Рекомендация |
|----------|-------|--------------|
| 0.0–0.3 | Консервативный | Медицинские документы |
| 0.4–0.6 | Сбалансированный | Научные статьи |
| 0.7–1.0 | Творческий | Популяризация |

## Программный доступ к настройкам

```python
from settings_manager import settings_manager, get_api_key, set_api_key

# Получить
value = settings_manager.get("temperature", 0.4)

# Установить
settings_manager.set("temperature", 0.5)

# API-ключи
api_key = get_api_key()
set_api_key("sk-...")
```
