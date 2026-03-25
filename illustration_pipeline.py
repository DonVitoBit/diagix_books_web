#!/usr/bin/env python3
"""
Модуль автоматической иллюстрации книги
"""

import os
import json
import logging
import requests
import time
import base64
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import fitz  # PyMuPDF

try:
    from google import genai
    from google.genai import types
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False
    logging.warning("Google GenAI library not available. Install with: pip install google-genai")
from settings_manager import (
    get_nanobanana_api_key,
    get_dalle_api_key,
    get_google_search_api_key,
    get_google_search_engine_id,
    get_tavily_api_key,
    settings_manager
)
from config import ILLUSTRATION_STYLES

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IllustrationPipeline:
    """Класс для автоматической иллюстрации книги"""
    
    def __init__(self):
        """Инициализация pipeline иллюстраций"""
        self.nanobanana_api_key = get_nanobanana_api_key()
        self.dalle_api_key = get_dalle_api_key()
        self.google_search_api_key = get_google_search_api_key()
        self.google_search_engine_id = get_google_search_engine_id()
        self.tavily_api_key = get_tavily_api_key()
        self.tcia_enabled = settings_manager.get("tcia_enabled", True)
        self.auto_illustration = settings_manager.get("auto_illustration", False)
        self.illustration_quality = settings_manager.get("illustration_quality", "high")
        self.brand_style = settings_manager.get("brand_style", "medical")

        # Список патологий в розыске
        self.pathology_search_list = self._load_pathology_search_list()

        # Метаданные изображений
        self.image_metadata = self._load_image_metadata()

        logger.info("IllustrationPipeline инициализирован")
        logger.info(f"NanoBanana API: {'✅' if self.nanobanana_api_key else '❌'}")
        logger.info(f"DALL-E 2 API: {'✅' if self.dalle_api_key else '❌'}")
        logger.info(f"Google Search API: {'✅' if self.google_search_api_key and self.google_search_engine_id else '❌'}")
        logger.info(f"TCIA API: {'✅' if self.tcia_enabled else '❌'}")

    def _load_pathology_search_list(self) -> List[Dict]:
        """Загрузка списка патологий в розыске"""
        search_list_file = Path("pathology_search_list.json")
        if search_list_file.exists():
            try:
                with open(search_list_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Ошибка загрузки списка патологий: {e}")
        return []

    def _save_pathology_search_list(self):
        """Сохранение списка патологий в розыске"""
        search_list_file = Path("pathology_search_list.json")
        try:
            with open(search_list_file, 'w', encoding='utf-8') as f:
                json.dump(self.pathology_search_list, f, ensure_ascii=False, indent=2)
            logger.info(f"Список патологий сохранен в {search_list_file}")
        except Exception as e:
            logger.error(f"Ошибка сохранения списка патологий: {e}")

    def _load_image_metadata(self) -> Dict[str, Dict]:
        """Загрузка метаданных изображений"""
        metadata_file = Path("image_metadata.json")
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Ошибка загрузки метаданных изображений: {e}")
        return {}

    def _save_image_metadata(self):
        """Сохранение метаданных изображений"""
        metadata_file = Path("image_metadata.json")
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.image_metadata, f, ensure_ascii=False, indent=2)
            logger.info(f"Метаданные изображений сохранены в {metadata_file}")
        except Exception as e:
            logger.error(f"Ошибка сохранения метаданных изображений: {e}")

    def extract_images_from_pdf(self, pdf_path: str, image_callback=None) -> List[Dict]:
        """Извлечение изображений из PDF с их описанием"""
        images = []
        used_xrefs = set()
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    
                    # Пропуск дубликатов
                    if xref in used_xrefs:
                        continue
                    used_xrefs.add(xref)
                    
                    try:
                        pix = fitz.Pixmap(doc, xref)
                    except Exception as e:
                        logger.debug(f"Пропуск xref {xref}: не удалось создать Pixmap — {e}")
                        continue

                    # Конвертация CMYK и других цветовых пространств в RGB для сохранения в PNG
                    try:
                        if pix.n - pix.alpha >= 4:  # CMYK или больше компонентов
                            pix = fitz.Pixmap(fitz.csRGB, pix)
                    except Exception as e:
                        logger.debug(f"Пропуск xref {xref}: конвертация в RGB — {e}")
                        pix = None
                        continue

                    if pix is None or (pix.n - pix.alpha > 3):
                        pix = None
                        continue

                    if pix.n - pix.alpha <= 3:  # GRAY или RGB
                        # 1. Проверка площади (фильтр фоновых подложек)
                        img_rects = page.get_image_rects(xref)
                        if img_rects:
                            r = img_rects[0]
                            page_area = page.rect.width * page.rect.height
                            img_area = r.width * r.height
                            if img_area > page_area * 0.7: # Порог 70% площади страницы
                                logger.info(f"Пропущено полностраничное фоновое изображение (площадь: {img_area/page_area:.2%})")
                                pix = None
                                continue

                        # 2. Фильтр: слишком маленькие изображения (иконки, линии, мусор)
                        if pix.width < 80 or pix.height < 80:
                            logger.info(f"Пропущено маленькое изображение ({pix.width}x{pix.height})")
                            pix = None
                            continue

                        # 3. Фильтр: пустые, однотонные или градиентные артефакты
                        if self._is_image_blank(pix):
                            logger.info(f"Пропущено пустое или артефактное изображение")
                            pix = None
                            continue

                        # Получаем текст вокруг изображения для контекста
                        text_around = self._get_text_around_image(page, img)
                        
                        image_info = {
                            "page": page_num + 1,
                            "index": img_index,
                            "xref": xref,
                            "width": pix.width,
                            "height": pix.height,
                            "text_around": text_around,
                            "classification": self._classify_image(text_around),
                            "pathology": self._extract_pathology(text_around),
                            "file_path": f"extracted_images/page_{page_num+1}_img_{img_index}.png"
                        }
                        
                        # Сохраняем изображение
                        os.makedirs("extracted_images", exist_ok=True)
                        pix.save(image_info["file_path"])

                        # Сохраняем метаданные изображения
                        metadata_key = image_info["file_path"]
                        self.image_metadata[metadata_key] = {
                            "page": image_info["page"],
                            "index": image_info["index"],
                            "width": image_info["width"],
                            "height": image_info["height"],
                            "text_around": image_info["text_around"],
                            "classification": image_info["classification"],
                            "pathology": image_info["pathology"],
                            "file_path": image_info["file_path"]
                        }

                        images.append(image_info)

                        # Логируем извлечение изображения
                        log_message = f"Извлечено изображение: {image_info['file_path']}"
                        logger.info(log_message)

                        # Вызываем callback для отображения изображения в UI
                        if image_callback:
                            image_callback(image_info["file_path"], image_info["page"], img_index + 1)
                    
                    pix = None
            
            doc.close()

            # Сохраняем метаданные изображений
            self._save_image_metadata()

            logger.info(f"Извлечено {len(images)} изображений из PDF")
            if len(images) == 0:
                logger.warning(
                    "Изображения в PDF не найдены. Возможные причины: "
                    "CMYK/другие цветовые пространства (теперь конвертируются в RGB), "
                    "все картинки отфильтрованы по размеру/пустоте, "
                    "или графика только векторная (не извлекается через get_images)."
                )
            return images
            
        except Exception as e:
            logger.error(f"Ошибка извлечения изображений: {e}")
            return []

    def _get_text_around_image(self, page, img) -> str:
        """Получение текста вокруг изображения для контекста"""
        try:
            # Получаем прямоугольник изображения
            img_rect = page.get_image_rects(img[0])[0]

            # Расширяем область поиска текста (больше область для лучшего контекста)
            expanded_rect = fitz.Rect(
                img_rect.x0 - 100, img_rect.y0 - 100,
                img_rect.x1 + 100, img_rect.y1 + 100
            )

            # Пробуем разные методы извлечения текста
            text = ""

            # Метод 1: get_textbox с расширенной областью
            try:
                text = page.get_textbox(expanded_rect)
            except:
                pass

            # Метод 2: get_text с параметрами для лучшего извлечения
            if not text.strip():
                try:
                    text = page.get_text("text", clip=expanded_rect)
                except:
                    pass

            # Очищаем и нормализуем текст
            if text:
                text = self._clean_extracted_text(text)

            return text.strip()

        except Exception as e:
            logger.warning(f"Не удалось получить текст вокруг изображения: {e}")
            return ""

    def _clean_extracted_text(self, text: str) -> str:
        """Очистка и нормализация извлеченного текста"""
        if not text:
            return ""

        import re

        # Удаляем лишние пробелы и переносы строк
        text = re.sub(r'\n+', ' ', text)  # Заменяем множественные переносы на пробелы
        text = re.sub(r'\s+', ' ', text)  # Заменяем множественные пробелы на один

        # Удаляем странные символы и артефакты OCR
        text = re.sub(r'[^\w\s\.,;:!?\-\(\)\[\]{}«»""''"\'а-яёa-z0-9]', '', text, flags=re.IGNORECASE | re.UNICODE)

        # Исправляем распространенные проблемы с переносами слов
        # Ищем паттерны вида "слово-\nслово" и объединяем их
        text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)

        # Удаляем слишком короткие фрагменты (менее 3 символов), которые могут быть шумом
        words = text.split()
        filtered_words = []
        for word in words:
            if len(word) >= 3 or word in ['рис', 'рис.', 'и', 'в', 'на', 'с', 'к', 'у', 'за', 'из', 'от', 'до', 'по', 'при', 'для', 'как', 'что', 'или', 'это', 'так']:
                filtered_words.append(word)

        text = ' '.join(filtered_words)

        # Удаляем повторяющиеся слова (часто бывает в PDF)
        words = text.split()
        cleaned_words = []
        prev_word = None
        for word in words:
            if word != prev_word:
                cleaned_words.append(word)
                prev_word = word

        text = ' '.join(cleaned_words)

        # Ограничиваем длину текста (берем первые 500 символов наиболее релевантного контента)
        if len(text) > 500:
            # Ищем начало описания рисунка
            patterns = [r'рис\.\s*\d+', r'рисунок\s*\d+', r'табл\.\s*\d+', r'схема\s*\d+']
            start_pos = len(text)
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    start_pos = min(start_pos, match.start())

            if start_pos < len(text) - 100:  # Если нашли паттерн не в конце
                text = text[start_pos:start_pos + 500]
            else:
                text = text[:500]

        return text.strip()

    def _classify_image(self, text_around: str) -> str:
        """Классификация изображения на энциклопедическое или клиническое"""
        text_lower = text_around.lower()
        
        # Ключевые слова для клинических изображений
        clinical_keywords = [
            "рентген", "снимок", "патология", "заболевание", "диагноз",
            "симптом", "лечение", "пациент", "клинический", "медицинский",
            "анализ", "исследование", "томография", "ультразвук", "мрт"
        ]
        
        # Ключевые слова для энциклопедических изображений
        encyclopedia_keywords = [
            "строение", "анатомия", "схема", "диаграмма", "иллюстрация",
            "структура", "орган", "система", "функция", "процесс"
        ]
        
        clinical_score = sum(1 for keyword in clinical_keywords if keyword in text_lower)
        encyclopedia_score = sum(1 for keyword in encyclopedia_keywords if keyword in text_lower)
        
        if clinical_score > encyclopedia_score:
            return "clinical"
        elif encyclopedia_score > 0:
            return "encyclopedia"
        else:
            return "unknown"

    def _extract_pathology(self, text_around: str) -> Optional[str]:
        """Извлечение названия патологии из текста"""
        # Простая эвристика для извлечения патологии
        # В реальной реализации можно использовать NLP
        text_lower = text_around.lower()
        
        # Список известных патологий
        pathologies = [
            "перелом", "остеопороз", "артрит", "артроз", "опухоль",
            "киста", "воспаление", "инфекция", "некроз", "склероз"
        ]
        
        for pathology in pathologies:
            if pathology in text_lower:
                return pathology
        
        return None

    def _is_image_blank(self, pix) -> bool:
        """Проверка, является ли изображение пустым, фоновым, шумом или градиентом"""
        try:
            samples = pix.samples
            if not samples:
                return True
            
            # Выборка данных для анализа
            step = max(1, len(samples) // 8000)
            data_subset = list(samples[::step])
            
            if len(data_subset) < 100:
                return True
                
            import statistics
            mean_val = sum(data_subset) / len(data_subset)
            stdev = statistics.stdev(data_subset)
            
            # 1. Проверка на уникальность цветов (маски и простые градиенты)
            # Порог 10: допускаем схемы и ч/б рисунки с малым числом цветов
            unique_values = len(set(data_subset))
            if unique_values < 10:
                logger.debug(f"Пропущено: слишком мало уникальных цветов ({unique_values})")
                return True

            # 2. Проверка контрастности (стандартное отклонение)
            if stdev < 15:
                logger.debug(f"Пропущено: низкая контрастность (stdev: {stdev:.2f})")
                return True

            # 3. Анализ диапазона яркости (перцентили)
            sorted_samples = sorted(data_subset)
            p5 = sorted_samples[int(len(sorted_samples) * 0.05)]
            p95 = sorted_samples[int(len(sorted_samples) * 0.95)]
            if (p95 - p5) < 50:
                logger.debug(f"Пропущено: узкий динамический диапазон ({p95-p5})")
                return True

            # 4. Детектор гладкости/размытости (Mean Absolute Difference)
            diffs = [abs(data_subset[i] - data_subset[i-1]) for i in range(1, len(data_subset))]
            mean_diff = sum(diffs) / len(diffs)
            if mean_diff < 3.0:
                logger.debug(f"Пропущено: слишком гладкое/размытое (mean_diff: {mean_diff:.2f})")
                return True

            # 5. Проверка "информативности" (преобладание одного цвета)
            most_common_color = max(set(data_subset), key=data_subset.count)
            if data_subset.count(most_common_color) / len(data_subset) > 0.90:
                logger.debug(f"Пропущено: 90%+ изображения состоит из одного цвета")
                return True
            
            # 6. Экстремальная яркость
            if mean_val > 240 or mean_val < 15:
                return True
            
            return False
        except Exception as e:
            logger.debug(f"Ошибка при проверке изображения: {e}")
            return False

    def check_tcia_availability(self) -> bool:
        """Проверка доступности TCIA API"""
        try:
            response = requests.get(
                "https://services.cancerimagingarchive.net/services/v4/TCIA/query/getCollectionValues",
                timeout=5  # Быстрая проверка, 5 секунд
            )
            return response.status_code == 200
        except:
            return False

    def search_dicom_in_tcia(self, pathology: str, error_callback=None) -> List[Dict]:
        """Поиск DICOM файлов в TCIA по патологии"""
        if not self.tcia_enabled or not pathology:
            return []

        # Быстрая проверка доступности TCIA
        if not self.check_tcia_availability():
            logger.warning("TCIA API недоступен, пропуск поиска")
            if error_callback:
                error_callback("TCIA API недоступен")
            return []

        # Получаем таймаут из настроек, по умолчанию 30 секунд
        tcia_timeout = settings_manager.get('tcia_timeout', 30)
        max_retries = 2

        for attempt in range(max_retries):
            try:
                logger.info(f"Поиск в TCIA для патологии '{pathology}' (попытка {attempt + 1}/{max_retries})")

                # TCIA API endpoint
                base_url = "https://services.cancerimagingarchive.net/services/v4/TCIA/query"

                # Поиск коллекций по ключевым словам
                search_url = f"{base_url}/getCollectionValues"
                response = requests.get(search_url, timeout=tcia_timeout)

                if response.status_code == 200:
                    collections = response.json()
                    matching_collections = []

                    for collection in collections:
                        if pathology.lower() in collection.get("Collection", "").lower():
                            matching_collections.append(collection)

                    logger.info(f"Найдено {len(matching_collections)} коллекций в TCIA для патологии '{pathology}'")
                    return matching_collections
                else:
                    logger.warning(f"Ошибка запроса к TCIA API: {response.status_code}")
                    if attempt == max_retries - 1:  # Последняя попытка
                        return []

            except requests.exceptions.Timeout:
                error_msg = f"Таймаут подключения к TCIA (попытка {attempt + 1}/{max_retries}): {tcia_timeout} сек"
                logger.warning(error_msg)
                if attempt == max_retries - 1:  # Последняя попытка
                    if error_callback:
                        error_callback(error_msg)
                    return []
                # Ждем перед следующей попыткой
                time.sleep(2)

            except requests.exceptions.ConnectionError:
                error_msg = f"Ошибка подключения к TCIA (попытка {attempt + 1}/{max_retries})"
                logger.warning(error_msg)
                if attempt == max_retries - 1:  # Последняя попытка
                    if error_callback:
                        error_callback(error_msg)
                    return []
                # Ждем перед следующей попыткой
                time.sleep(2)

            except Exception as e:
                error_msg = f"Ошибка поиска в TCIA: {e}"
                logger.error(error_msg)
                if error_callback:
                    error_callback(error_msg)
                return []

        return []

    def search_images_google(self, query: str, num_results: int = 5, error_callback=None) -> List[Dict]:
        """Поиск изображений через Google Custom Search API"""
        if not self.google_search_api_key or not self.google_search_engine_id:
            logger.info("Google Search API не настроен, пропуск")
            return []

        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.google_search_api_key,
                "cx": self.google_search_engine_id,
                "q": query,
                "searchType": "image",
                "num": num_results
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []
            if "items" in data:
                for item in data["items"]:
                    results.append({
                        "title": item.get("title"),
                        "url": item.get("link"),
                        "thumbnail": item.get("image", {}).get("thumbnailLink")
                    })
            
            return results
        except Exception as e:
            error_msg = f"Ошибка поиска Google: {e}"
            logger.error(error_msg)
            if error_callback:
                error_callback(error_msg)
            return []

    def search_images_tavily(self, query: str, num_results: int = 5, error_callback=None) -> List[Dict]:
        """Поиск изображений через Tavily API"""
        if not self.tavily_api_key:
            logger.info("Tavily API ключ не настроен, пропуск")
            return []

        try:
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": self.tavily_api_key,
                "query": query,
                "include_images": True,
                "max_results": num_results
            }

            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()

            results = []
            if "images" in data:
                for img in data["images"]:
                    if isinstance(img, str):
                        results.append({
                            "title": query,
                            "url": img,
                            "thumbnail": None
                        })
                    elif isinstance(img, dict):
                        results.append({
                            "title": img.get("title", query),
                            "url": img.get("url"),
                            "thumbnail": None
                        })
            
            return results
        except Exception as e:
            error_msg = f"Ошибка поиска Tavily: {e}"
            logger.error(error_msg)
            if error_callback:
                error_callback(error_msg)
            return []

    def generate_image_nanobanana(
        self, prompt: str, style: str = "medical", errors: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Генерация изображения через Google GenAI (NanaBanana Pro / Gemini 3 Pro Image).
        Возвращает путь к сохранённому файлу или None.
        """
        if not GOOGLE_GENAI_AVAILABLE:
            msg = "Библиотека google-genai не установлена."
            if errors is not None: errors.append(msg)
            logger.error(msg)
            return None

        if not self.nanobanana_api_key:
            msg = "Google (NanoBanana) API ключ не настроен."
            if errors is not None: errors.append(msg)
            logger.warning(msg)
            return None

        def _err(msg: str) -> None:
            if errors is not None:
                errors.append(msg)
            logger.warning(msg)

        def _pretty_model_name(model_name: str) -> str:
            m = (model_name or "").strip().lower()
            if m == "nanobanana-2":
                return "NanaBanana 2"
            return model_name or "unknown"

        def _normalize_model_name(model_name: str) -> str:
            """Нормализует пользовательские алиасы модели в ID, ожидаемый Google GenAI."""
            m = (model_name or "").strip()
            if not m:
                return "gemini-3-pro-image-preview"
            low = m.lower().replace("_", "-").replace(" ", "-")
            if low in {"nanobanana2", "nanobanana-2", "nana-banana-2", "nana-banana2", "nana-bananna-2"}:
                return "gemini-3-pro-image-preview"
            return m

        try:
            # Инициализация клиента
            client = genai.Client(api_key=self.nanobanana_api_key)
            # По умолчанию используем gemini-3-pro-image-preview
            model_id = _normalize_model_name(settings_manager.get("nanobanana_model", "gemini-3-pro-image-preview"))
            _err(f"INFO: NanoBanana модель для генерации: {_pretty_model_name(model_id)} ({model_id})")
            
            # Возвращаем влияние выбранного стиля: добавляем style-инструкцию из config.
            style_prefix = ILLUSTRATION_STYLES.get(style) or ILLUSTRATION_STYLES.get("academic", "")
            style_clause = f" Style guidance: {style_prefix}." if style_prefix else ""
            science = int(settings_manager.get("style_science", 3))
            label_clause = (
                " Use very simple Russian labels for children and broad audience (1-3 words), avoid complex terminology."
                if science <= 2
                else " Use medically precise Russian labels where needed."
            )
            # Промпт согласно спецификации: профессиональное качество, свет, 8K + стиль.
            full_prompt = (
                f"Generate a high-quality, professional image: {prompt}."
                f" Make it artistic, detailed, with cinematic lighting and 8K quality."
                f"{style_clause}{label_clause}"
            )
            
            # Настройка конфига для получения изображения
            kwargs = {}
            if hasattr(types, "GenerateContentConfig"):
                try:
                    if hasattr(types, "Modality"):
                        kwargs["config"] = types.GenerateContentConfig(response_modalities=[types.Modality.IMAGE])
                    else:
                        kwargs["config"] = types.GenerateContentConfig(response_modalities=["IMAGE"])
                except Exception:
                    pass

            def _gen(model_name: str):
                return client.models.generate_content(
                    model=model_name,
                    contents=[types.Content(parts=[types.Part(text=full_prompt)])],
                    **kwargs,
                )

            # Генерация контента (с fallback на Flash, если Pro недоступен на ключе)
            try:
                resp = _gen(model_id)
            except Exception as e:
                err = str(e)
                _err(f"Google GenAI: не удалось вызвать {model_id}: {err[:120]}")
                fallback_model = "gemini-2.5-flash-image"
                _err(f"INFO: fallback на модель: {fallback_model}")
                resp = _gen(fallback_model)

            # Обработка ответа (ищем inline_data с изображением)
            img_bytes = None
            if resp.candidates:
                for part in resp.candidates[0].content.parts:
                    if part.inline_data:
                        img_bytes = part.inline_data.data
                        break
            
            if not img_bytes:
                _err(f"Google API: ответ не содержит данных изображения. Ответ: {resp.text[:100] if hasattr(resp, 'text') else 'пусто'}")
                return None

            # Сохранение файла
            os.makedirs("generated_article_images", exist_ok=True)
            import uuid
            filename = f"google_gen_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join("generated_article_images", filename)
            
            with open(filepath, "wb") as f:
                f.write(img_bytes)
            
            logger.info(f"Изображение сохранено: {filepath}")
            return filepath

        except Exception as e:
            _err(f"Ошибка Google GenAI: {str(e)[:150]}")
            return None

    def generate_image_dalle(
        self, prompt: str, size: str = "512x512", style: str = "natural", errors: Optional[List[str]] = None
    ) -> Optional[str]:
        """Генерация изображения через DALL-E 2 API"""
        if not self.dalle_api_key:
            logger.warning("DALL-E 2 API ключ не настроен")
            return None

        def _err(msg: str) -> None:
            if errors is not None:
                errors.append(msg)
            logger.warning(msg)

        try:
            import openai
            client = openai.OpenAI(api_key=self.dalle_api_key)
            medical_prompt = f"Medical illustration in {style} style: {prompt}"
            if "medical" in style.lower():
                medical_prompt += ". Professional medical diagram, clear and educational."

            response = client.images.generate(
                model="dall-e-2",
                prompt=medical_prompt,
                size=size,
                quality="standard",
                n=1,
            )

            image_url = response.data[0].url
            if image_url:
                import uuid
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    filename = f"dalle_redraw_{uuid.uuid4().hex[:8]}.png"
                    filepath = os.path.join("extracted_images", filename)
                    os.makedirs("extracted_images", exist_ok=True)
                    with open(filepath, 'wb') as f:
                        f.write(image_response.content)
                    return filepath
            return None
        except Exception as e:
            err_str = str(e)
            if "insufficient_quota" in err_str.lower() or "quota" in err_str.lower():
                _err("DALL-E: лимит/квота исчерпана")
            elif "invalid_api_key" in err_str.lower() or "401" in err_str:
                _err("DALL-E: неверный API ключ")
            else:
                _err(f"DALL-E: {err_str[:120]}")
            return None

    def process_illustrations(self, pdf_path: str, progress_callback=None, error_callback=None) -> Dict:
        """Основной процесс обработки иллюстраций"""
        logger.info(f"Начало обработки иллюстраций для {pdf_path}")

        # Извлекаем изображения из PDF
        images = self.extract_images_from_pdf(pdf_path, progress_callback)
        
        results = {
            "total_images": len(images),
            "processed_images": 0,
            "generated_images": 0,
            "search_results": 0,
            "pathologies_found": [],
            "pathologies_missing": [],
            "found_images": []  # Список найденных изображений с патологиями
        }
        
        for image in images:
            logger.info(f"Обработка изображения: {image['file_path']}")
            
            if image["classification"] == "clinical" and image["pathology"]:
                # Поиск DICOM в TCIA
                dicom_results = self.search_dicom_in_tcia(image["pathology"], error_callback)
                
                if dicom_results:
                    results["search_results"] += len(dicom_results)
                    results["pathologies_found"].append(image["pathology"])
                    for dicom in dicom_results:
                        if isinstance(dicom, dict):
                            results["found_images"].append({
                                "pathology": image["pathology"],
                                "source": "TCIA",
                                "title": dicom.get("Collection", "DICOM Collection"),
                                "url": None,
                                "thumbnail": None
                            })
                    logger.info(f"Найдены DICOM файлы для патологии: {image['pathology']}")
                else:
                    # Сначала пробуем Tavily (по желанию пользователя это теперь основной инструмент)
                    tavily_results = self.search_images_tavily(
                        f"{image['pathology']} medical illustration x-ray",
                        error_callback=error_callback
                    )

                    if tavily_results:
                        results["search_results"] += len(tavily_results)
                        for tav_img in tavily_results:
                            if isinstance(tav_img, dict):
                                results["found_images"].append({
                                    "pathology": image["pathology"],
                                    "source": "Tavily Search",
                                    "title": tav_img.get("title", "Medical Image"),
                                    "url": tav_img.get("url"),
                                    "thumbnail": None
                                })
                        logger.info(f"Найдены изображения в Tavily для патологии: {image['pathology']}")
                    else:
                        # Поиск в Google Images (вторым темпом)
                        google_results = self.search_images_google(
                            f"{image['pathology']} medical imaging x-ray",
                            error_callback=error_callback
                        )

                        if google_results:
                            results["search_results"] += len(google_results)
                            for google_img in google_results:
                                if isinstance(google_img, dict):
                                    results["found_images"].append({
                                        "pathology": image["pathology"],
                                        "source": "Google Images",
                                        "title": google_img.get("title", "Medical Image"),
                                        "url": google_img.get("url"),
                                        "thumbnail": google_img.get("thumbnail")
                                    })
                            logger.info(f"Найдены изображения в Google для патологии: {image['pathology']}")
                        else:
                            # Добавляем в список патологий в розыске
                            if image["pathology"] not in [p["pathology"] for p in self.pathology_search_list]:
                                self.pathology_search_list.append({
                                    "pathology": image["pathology"],
                                    "context": image["text_around"],
                                    "date_added": str(Path().cwd()),
                                    "status": "searching"
                                })
                                results["pathologies_missing"].append(image["pathology"])
                                logger.warning(f"Патология добавлена в розыск: {image['pathology']}")
            
            elif image["classification"] == "encyclopedia":
                # Генерация современной энциклопедической иллюстрации
                prompt = f"Modern medical illustration: {image['text_around'][:100]}"
                generated_image = self.generate_image_nanobanana(prompt, self.brand_style)
                
                if generated_image:
                    results["generated_images"] += 1
                    logger.info(f"Сгенерирована энциклопедическая иллюстрация")
            
            results["processed_images"] += 1
        
        # Сохраняем обновленный список патологий в розыске
        self._save_pathology_search_list()
        
        logger.info(f"Обработка завершена: {results}")
        return results

    def get_pathology_search_list(self) -> List[Dict]:
        """Получение списка патологий в розыске"""
        return self.pathology_search_list

    def redraw_image_with_nanobanana(self, image_info: Dict, custom_prompt: Optional[str] = None, size: str = "512x512") -> Tuple[Optional[str], Optional[str]]:
        """Перерисовка изображения через Google Gemini (Nano Banana). Возвращает (путь_к_файлу или None, сообщение_об_ошибке или None)."""
        if not GOOGLE_GENAI_AVAILABLE:
            msg = "Библиотека google-genai не установлена. Установите: pip install google-genai"
            logger.error(msg)
            return None, msg

        if not self.nanobanana_api_key:
            msg = "NanoBanana (Gemini) API ключ не настроен. Укажите ключ в Настройках."
            logger.warning(msg)
            return None, msg

        try:
            # Создаем промпт на основе описания изображения
            if custom_prompt:
                prompt = custom_prompt
            else:
                text_around = image_info.get("text_around", "")
                pathology = image_info.get("pathology", "")
                classification = image_info.get("classification", "unknown")

                # Создаем промпт в зависимости от типа изображения
                if classification == "clinical" and pathology:
                    prompt = f"Medical X-ray or clinical imaging showing {pathology}. Professional medical diagnostic image, clear anatomical details, educational for medical students."
                elif classification == "encyclopedia":
                    prompt = f"Medical illustration diagram: {text_around[:200]}. Clean, professional medical illustration, anatomical accuracy, educational style."
                else:
                    prompt = f"Medical illustration: {text_around[:200]}. Professional healthcare visual, clear and informative."

                # Добавляем стиль брендинга
                if self.brand_style == "medical":
                    prompt += " Modern medical illustration style, professional healthcare design."
                elif self.brand_style == "modern":
                    prompt += " Contemporary medical illustration with clean lines and modern aesthetic."
                elif self.brand_style == "classic":
                    prompt += " Classic medical textbook illustration style, detailed and traditional."

            # Парсим размер изображения
            try:
                if "x" in size:
                    width, height = map(int, size.split("x"))
                else:
                    # Если размер передан как строка типа "512x512"
                    width = height = int(size.split("x")[0]) if "x" in size else int(size)
            except (ValueError, IndexError):
                width = height = 512  # fallback

            # Ограничиваем размер (Gemini имеет ограничения)
            if width > 2048:
                width = 2048
            if height > 2048:
                height = 2048

            logger.info(f"Перерисовка изображения: {image_info.get('file_path', 'unknown')}")
            logger.info(f"Промпт: {prompt}")
            logger.info(f"Размер: {width}x{height}")

            # Инициализация клиента через API key
            client = genai.Client(api_key=self.nanobanana_api_key)

            def _normalize_model_name(model_name: str) -> str:
                m = (model_name or "").strip()
                if not m:
                    return "gemini-3-pro-image-preview"
                low = m.lower().replace("_", "-").replace(" ", "-")
                if low in {"nanobanana2", "nanobanana-2", "nana-banana-2", "nana-banana2", "nana-bananna-2"}:
                    return "gemini-3-pro-image-preview"
                return m

            # Для перерисовки (Image-to-Image) используем gemini-3-pro-image-preview
            model = _normalize_model_name(settings_manager.get("nanobanana_model", "gemini-3-pro-image-preview"))
            logger.info(f"Использование модели: {model} (NanoBanana Img2Img)")
            # Для improveExistingImages UI сейчас message из функции не выводит напрямую,
            # но хотя бы логируем (и при необходимости можно будет вывести в UI).
            logger.info(f"NanoBanana Img2Img: модель = {model}")

            # Читаем исходное изображение
            image_path = image_info.get('file_path')
            if not image_path or not os.path.exists(image_path):
                msg = f"Не найден исходный файл: {image_path}"
                logger.error(msg)
                return None, msg

            with open(image_path, "rb") as f:
                source_image_bytes = f.read()

            # Инструкция для трансформации согласно спецификации + выбранный стиль.
            transform_prompt = custom_prompt or "Enhance this image professionally with cinematic lighting and artistic quality"
            style_prefix = ILLUSTRATION_STYLES.get(self.brand_style) or ILLUSTRATION_STYLES.get("academic", "")
            style_clause = f" Style guidance: {style_prefix}." if style_prefix else ""
            science = int(settings_manager.get("style_science", 3))
            label_clause = (
                " Use very simple Russian labels for children and broad audience (1-3 words), avoid complex terminology."
                if science <= 2
                else " Use medically precise Russian labels where needed."
            )
            instruction = (
                f'Transform this image according to the following instructions: "{transform_prompt}".'
                f" Generate a new image based on this.{style_clause}{label_clause}"
            )

            # Запрос изображения в ответе (response_modalities), если SDK поддерживает
            kwargs = {}
            if hasattr(types, "GenerateContentConfig"):
                try:
                    if hasattr(types, "Modality"):
                        kwargs["config"] = types.GenerateContentConfig(response_modalities=[types.Modality.TEXT, types.Modality.IMAGE])
                    else:
                        kwargs["config"] = types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"])
                except Exception:
                    pass

            # Генерация контента (изображение + текст -> изображение)
            def _gen(model_name: str):
                return client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Content(
                            parts=[
                                types.Part(
                                    inline_data=types.Blob(
                                        mime_type="image/jpeg",
                                        data=source_image_bytes,
                                    )
                                ),
                                types.Part(text=instruction),
                            ]
                        )
                    ],
                    **kwargs,
                )

            try:
                resp = _gen(model)
            except Exception as e:
                # fallback на Flash
                logger.warning(f"NanaBanana Pro недоступна, fallback на Flash: {str(e)[:120]}")
                logger.warning("INFO: fallback img2img модель: gemini-2.5-flash-image")
                resp = _gen("gemini-2.5-flash-image")

            # Обработка ответа
            img_bytes = None
            if resp.candidates:
                for part in resp.candidates[0].content.parts:
                    if part.inline_data:
                        img_bytes = part.inline_data.data
                        break
            
            if img_bytes:
                output_filename = f"redrawn_{Path(image_info['file_path']).stem}.png"
                output_path = Path("extracted_images") / output_filename
                output_path.write_bytes(img_bytes)
                logger.info(f"Изображение успешно сгенерировано NanaBanana Pro: {output_path}")
                return str(output_path), None

            msg = "Модель не вернула изображение в ответе. Проверьте доступ к модели gemini-2.5-flash-image и квоты."
            logger.error(msg)
            return None, msg

        except Exception as e:
            msg = str(e)
            logger.error(f"Ошибка перерисовки изображения через Google Gemini: {e}")
            return None, msg

    def get_image_metadata(self, image_path: str) -> Optional[Dict]:
        """Получение метаданных изображения по пути к файлу"""
        return self.image_metadata.get(image_path)

    def _generate_fallback_prompt(self, image_filename: str) -> str:
        """Генерация базового промпта при отсутствии метаданных"""
        try:
            # Извлекаем информацию из имени файла
            # Формат: page_X_img_Y.png
            parts = image_filename.replace('.png', '').split('_')
            if len(parts) >= 3 and parts[0] == 'page' and parts[2] == 'img':
                page_num = parts[1]
                img_num = parts[3] if len(parts) > 3 else parts[2]

                # Создаем базовый промпт для медицинского изображения
                base_prompt = f"Medical illustration from page {page_num}, image {img_num}. Professional healthcare visual showing anatomical or pathological medical content, clear and educational for medical students."

                # Добавляем специфические элементы в зависимости от номера страницы
                # (это грубая эвристика, но лучше чем ничего)
                try:
                    page_int = int(page_num)
                    if page_int <= 50:
                        base_prompt += " Focus on bone structure, skeletal system anatomy."
                    elif page_int <= 100:
                        base_prompt += " Focus on pathological conditions, diseases of bones and joints."
                    elif page_int <= 150:
                        base_prompt += " Focus on diagnostic imaging, X-rays, clinical cases."
                    elif page_int <= 200:
                        base_prompt += " Focus on treatment methods, surgical procedures."
                    else:
                        base_prompt += " Focus on advanced medical imaging and diagnostics."
                except ValueError:
                    pass

                return base_prompt
            else:
                # Неизвестный формат имени файла
                return f"Medical illustration: {image_filename}. Professional healthcare visual, clear and educational for medical students."

        except Exception as e:
            logger.warning(f"Ошибка генерации fallback промпта для {image_filename}: {e}")
            return f"Medical illustration from radiology textbook. Professional healthcare visual, clear and educational."

    def create_basic_metadata_for_all_images(self):
        """Создание базовых метаданных для всех изображений в extracted_images"""
        import os

        if not os.path.exists("extracted_images"):
            logger.warning("Папка extracted_images не существует")
            return

        # Получаем все PNG файлы
        image_files = [f for f in os.listdir("extracted_images") if f.endswith('.png')]
        logger.info(f"Найдено {len(image_files)} изображений")

        # Создаем базовые метаданные для изображений без них
        new_metadata_count = 0
        for image_file in image_files:
            image_path = f"extracted_images/{image_file}"
            if image_path not in self.image_metadata:
                # Создаем базовые метаданные
                try:
                    # Извлекаем информацию из имени файла
                    parts = image_file.replace('.png', '').split('_')
                    page_num = 1
                    img_index = 0

                    if len(parts) >= 2 and parts[0] == 'page':
                        try:
                            page_num = int(parts[1])
                        except ValueError:
                            pass

                    if len(parts) >= 4 and parts[2] == 'img':
                        try:
                            img_index = int(parts[3])
                        except ValueError:
                            pass

                    # Получаем размеры изображения
                    try:
                        from PIL import Image
                        with Image.open(f"extracted_images/{image_file}") as img:
                            width, height = img.size
                    except:
                        width, height = 800, 600  # значения по умолчанию

                    # Создаем базовые метаданные
                    self.image_metadata[image_path] = {
                        "page": page_num,
                        "index": img_index,
                        "width": width,
                        "height": height,
                        "text_around": "",  # Пустой текст - будет использоваться fallback промпт
                        "classification": "unknown",
                        "pathology": None,
                        "file_path": image_path
                    }
                    new_metadata_count += 1

                except Exception as e:
                    logger.warning(f"Ошибка создания метаданных для {image_file}: {e}")

        if new_metadata_count > 0:
            self._save_image_metadata()
            logger.info(f"Создано базовых метаданных для {new_metadata_count} изображений")
        else:
            logger.info("Все изображения уже имеют метаданные")

    def clear_pathology_search_list(self):
        """Очистка списка патологий в розыске"""
        self.pathology_search_list = []
        self._save_pathology_search_list()
        logger.info("Список патологий в розыске очищен")

def main():
    """Тестовая функция"""
    pipeline = IllustrationPipeline()
    
    # Тест с существующим PDF
    pdf_path = "input/Кости_глава_1.pdf"
    if os.path.exists(pdf_path):
        results = pipeline.process_illustrations(pdf_path)
        print(f"Результаты обработки: {results}")
    else:
        print(f"Файл {pdf_path} не найден")

if __name__ == "__main__":
    main()
