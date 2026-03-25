"""
Конфигурационный файл для приложения Text Re-phraser
"""

# Основные настройки приложения
APP_TITLE = "Text Re-phraser"
APP_ICON = ""
LAYOUT = "wide"

# Настройки перефразирования текста
DEFAULT_TEMPERATURE = 0.4
MIN_TEMPERATURE = 0.0
MAX_TEMPERATURE = 1.0
MAX_TOKENS = 2000
# Размер чанка для перефразирования (ТОКЕНЫ модели, а не символы).
# Больше токенов в чанке → меньше вызовов API (быстрее и дешевле), но выше риск переполнения контекста.
# 600 токенов — хороший баланс для gpt‑4o / deepseek-chat на научных текстах.
MAX_CHUNK_LENGTH = 600
# Сколько чанков обрабатывать параллельно внутри одного блока (1 = как раньше, 3–5 быстрее)
MAX_CONCURRENT_REQUESTS = 4

# Настройки файлов
SUPPORTED_FILE_TYPES = ["pdf", "txt", "md", "docx"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Настройки изображений
EXTRACTED_IMAGES_DIR = "extracted_images"
MAX_IMAGES_IN_CAROUSEL = 10
DEFAULT_IMAGE_SIZE = "512x512"

# Настройки табов
TAB_NAMES = ["Книги", "Перефразирование", "Результаты", "Иллюстрации", "Настройки", "Модераторы"]

# Настройки темы по умолчанию
DEFAULT_THEME = "РЕНТГЕНОДИАГНОСТИКА ЗАБОЛЕВАНИЙ КОСТЕЙ И СУСТАВОВ"

# Настройки брендинга для изображений
BRAND_STYLES = {
    "medical": "Modern medical illustration style, professional healthcare design",
    "modern": "Contemporary medical illustration with clean lines and modern aesthetic",
    "classic": "Classic medical textbook illustration style, detailed and traditional"
}

# Стили иллюстраций NanaBanana (ключ -> описание на английском для промпта)
ILLUSTRATION_STYLES = {
    "minimalist": "Minimalist style. Clean forms, minimal details, limited color palette. Focus on idea and simplicity.",
    "cartoon": "Cartoon style. Simplified forms, expressive characters, bright colors. Good for popularization and easy explanations.",
    "academic": "Academic scientific atlas style. Strict scientific presentation, high accuracy, neutral colors. For educational and scientific materials.",
    "realistic": "Realistic style. Maximum closeness to reality, detailed objects and textures.",
    "semi_realistic": "Semi-realistic style. Balance between realism and graphics: recognizable but simplified for clarity.",
    "diagrammatic": "Diagrammatic schematic style. Graphic schemes, lines, arrows, symbols. Good for explaining processes and structures.",
    "infographic": "Infographic style. Data and comparison visualization: charts, labels, numbers, icons.",
    "isometric": "Isometric style. Objects in pseudo-3D isometric perspective. Often used in technical and educational illustrations.",
    "3d": "3D visualization style. Volumetric models, light and shadow, modern technological look.",
    "editorial": "Editorial illustration style. Artistic, metaphorical presentation for magazines and articles. Often for covers and key illustrations.",
}

# Настройки модели OpenAI
DEFAULT_MODEL = "gpt-4o"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"

# Настройки API ключей (маски для отображения)
API_KEY_MASK_PREFIX = 8
API_KEY_MASK_SUFFIX = 4

# Настройки прогресса
PROGRESS_UPDATE_INTERVAL = 0.1

# Настройки кеширования
CACHE_TTL_SECONDS = 3600  # 1 час

# Настройки логирования
LOG_LEVEL = "INFO"
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# Данные для входа (Администратор)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
