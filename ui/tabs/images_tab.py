"""
Модуль вкладки автоматической иллюстрации книги
"""

import os
import tempfile
from pathlib import Path
import streamlit as st

try:
    from PIL import Image
    _PIL_UnidentifiedImageError = Image.UnidentifiedImageError
except ImportError:
    _PIL_UnidentifiedImageError = OSError
from ui.components.file_uploader import FileUploader
from ui.components.image_gallery import ImageGallery
from settings_manager import get_nanobanana_api_key, get_llm_provider, get_deepseek_api_key, get_api_key


def _safe_st_image(path_or_data, caption="", width="stretch"):
    """Показывает изображение через st.image; при ошибке (битый/неподдерживаемый файл) — сообщение."""
    try:
        st.image(path_or_data, caption=caption, width=width)
    except (_PIL_UnidentifiedImageError, OSError, Exception) as e:
        st.warning("Не удалось отобразить изображение: файл повреждён или формат не поддерживается.")
        st.caption(str(e)[:200])


class ImagesTab:
    """Класс для управления вкладкой иллюстраций"""

    def __init__(self):
        self.file_uploader = FileUploader()
        self.image_gallery = ImageGallery()

    def render(self, tab):
        """Отображение вкладки иллюстраций"""
        with tab:
            st.header("Автоматическая иллюстрация книги")

            pipeline_cls = self._get_pipeline_class()
            if pipeline_cls is None:
                return

            # Раздел загрузки книги
            self._render_pdf_upload_section()

            st.markdown("---")

            # Раздел просмотра изображений
            self._render_image_viewer_section()

    def _get_pipeline_class(self):
        """
        Ленивая загрузка IllustrationPipeline.

        Важно: вкладка иллюстраций не должна ломать запуск всего приложения,
        даже если не установлены опциональные зависимости (например, requests / pillow / google-genai).
        """
        try:
            from illustration_pipeline import IllustrationPipeline
            return IllustrationPipeline
        except Exception as e:
            st.warning("Модуль иллюстраций недоступен: не хватает зависимостей или есть ошибка импорта.")
            st.code(str(e))
            st.info(
                "Для включения вкладки «Иллюстрации» установите зависимости и перезапустите приложение:\n"
                "```\n"
                "python -m pip install -r requirements.txt\n"
                "python -m pip install requests pillow google-genai\n"
                "```\n"
                "Если вкладка не нужна — вы можете игнорировать это сообщение."
            )
            return None

    def _render_pdf_upload_section(self):
        """Отображение секции загрузки PDF"""
        st.subheader("Загрузка книги (PDF)")

        uploaded_pdf_book = self.file_uploader.render(
            label="Выберите PDF файл книги для извлечения изображений",
            allowed_types=["pdf"],
            help_text="Загрузите PDF книгу, чтобы извлечь из нее изображения и подписи."
        )

        if uploaded_pdf_book:
            file_info = self.file_uploader.get_file_info(uploaded_pdf_book)
            st.info(f"Загружен файл: {file_info['name']} ({file_info['size_mb']} MB)")

            extract_images = st.checkbox(
                "Извлечь изображения из загруженной книги",
                value=True,
                help="Если отмечено, изображения будут извлечены из PDF и сохранены в папку 'extracted_images/'."
            )

            if st.button("Извлечь изображения", type="primary", width="stretch"):
                if not extract_images:
                    st.error("Включите опцию извлечения изображений")
                else:
                    self._process_pdf_extraction(uploaded_pdf_book)

    def _process_pdf_extraction(self, uploaded_pdf_book):
        """Обработка извлечения изображений из PDF"""
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.text("Сохранение PDF файла...")
            progress_bar.progress(10)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_pdf_book.getvalue())
                temp_pdf_path = tmp_file.name

            status_text.text("Инициализация системы обработки...")
            progress_bar.progress(30)

            from illustration_pipeline import IllustrationPipeline
            pipeline = IllustrationPipeline()

            status_text.text("Извлечение изображений из PDF... (поиск на страницах)")
            progress_bar.progress(50)
            
            # Контейнер для отображения процесса извлечения
            st.markdown("### Процесс извлечения:")
            live_preview_container = st.empty()
            
            # Список для хранения путей извлеченных картинок (для превью)
            extracted_paths = []
            
            def show_extracted_image(img_path, page, count):
                extracted_paths.append(img_path)
                # Показываем последние 4 извлеченных изображения в ряд
                with live_preview_container.container():
                    cols = st.columns(4)
                    latest_images = extracted_paths[-4:]
                    for idx, path in enumerate(latest_images):
                        with cols[idx]:
                            _safe_st_image(path, caption=f"Стр. {page}", width="stretch")
                    st.caption(f"Найдено изображений: {len(extracted_paths)}")

            results = pipeline.extract_images_from_pdf(temp_pdf_path, image_callback=show_extracted_image)

            status_text.text("Анализ и классификация изображений...")
            progress_bar.progress(80)

            pipeline._save_image_metadata()

            progress_bar.progress(100)
            status_text.text("Извлечение завершено.")

            st.success(f"Извлечено **{len(results)}** изображений из книги.")

            if results:
                self._display_extraction_results(results)

            progress_bar.empty()
            status_text.empty()
            st.rerun()

        except Exception as e:
            st.error(f"Ошибка при извлечении изображений: {str(e)}")
        finally:
            if 'temp_pdf_path' in locals():
                try:
                    os.unlink(temp_pdf_path)
                except:
                    pass

    def _display_extraction_results(self, results):
        """Отображение результатов извлечения"""
        col_res1, col_res2, col_res3 = st.columns(3)

        with col_res1:
            st.metric("Всего изображений", len(results))

        clinical = sum(1 for r in results if r.get('classification') == 'clinical')
        encyclopedia = sum(1 for r in results if r.get('classification') == 'encyclopedia')

        with col_res2:
            st.metric("Клинические", clinical)

        with col_res3:
            st.metric("Энциклопедические", encyclopedia)

        st.subheader("Извлеченные изображения")
        preview_images = results[:6]
        cols = st.columns(3)
        for i, img_info in enumerate(preview_images):
            with cols[i % 3]:
                img_path = img_info.get('file_path', '')
                if os.path.exists(img_path):
                    _safe_st_image(img_path, caption=f"Изображение {i+1}", width=150)

    def _render_image_viewer_section(self):
        """Отображение секции просмотра изображений"""
        # Автоматический поиск всех изображений
        if not os.path.exists("extracted_images"):
            st.warning("Директория extracted_images не найдена")
            st.info("Изображения должны находиться в папке extracted_images/")
            return

        image_files = [f for f in os.listdir("extracted_images") if f.endswith(('.png', '.jpg', '.jpeg'))]

        if not image_files:
            st.info("Изображения не найдены в директории extracted_images")
            st.info("Добавьте изображения в папку extracted_images/ для работы с ними")
            return

        st.subheader(f"Найдено изображений: {len(image_files)}")

        # Сортировка изображений
        image_files.sort()

        # Инициализация индекса
        if 'current_image_index' not in st.session_state:
            st.session_state.current_image_index = 0

        # Навигация между изображениями
        self._render_image_navigation(image_files)

        # Отображение текущего изображения
        self._render_current_image(image_files)

    def _render_image_navigation(self, image_files):
        """Отображение элементов навигации"""
        col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

        with col_nav1:
            if st.button("Предыдущее", disabled=st.session_state.current_image_index == 0):
                st.session_state.current_image_index = max(0, st.session_state.current_image_index - 1)
                st.rerun()

        with col_nav2:
            selected_image = st.selectbox(
                "Выберите изображение:",
                image_files,
                index=st.session_state.current_image_index,
                format_func=lambda x: f"{st.session_state.current_image_index + 1}/{len(image_files)}: {x}",
                label_visibility="collapsed",
                key="image_selector"
            )
            st.session_state.current_image_index = image_files.index(selected_image)

        with col_nav3:
            if st.button("Следующее", disabled=st.session_state.current_image_index == len(image_files) - 1):
                st.session_state.current_image_index = min(len(image_files) - 1, st.session_state.current_image_index + 1)
                st.rerun()

    def _render_current_image(self, image_files):
        """Отображение текущего выбранного изображения"""
        selected_image = image_files[st.session_state.current_image_index]
        image_path = os.path.join("extracted_images", selected_image)
        from illustration_pipeline import IllustrationPipeline
        pipeline = IllustrationPipeline()
        metadata = pipeline.get_image_metadata(image_path)

        # Путь к перерисованному изображению (если есть)
        redrawn_filename = f"redrawn_{Path(selected_image).stem}.png"
        redrawn_path = os.path.join("extracted_images", redrawn_filename)

        # Создаем две колонки: Оригинал и Обработка
        col_orig, col_enhanced = st.columns(2)

        with col_orig:
            st.markdown("### Оригинал")
            _safe_st_image(image_path, caption=f"Оригинал: {selected_image}", width="stretch")
            
            # Метаданные под оригиналом
            if metadata:
                text_around = metadata.get("text_around", "").strip()
                if text_around:
                    st.markdown("#### Подпись к изображению")
                    st.info(text_around)
                
                # Компактная инфо-панель
                c1, c2 = st.columns(2)
                with c1:
                    st.caption(f"Стр: {metadata.get('page')}")
                with c2:
                    st.caption(f"Тип: {metadata.get('classification')}")

        with col_enhanced:
            st.markdown("### NanaBanana Pro")
            
            if os.path.exists(redrawn_path):
                _safe_st_image(redrawn_path, caption="Улучшено ИИ (без артефактов)", width="stretch")
                
                # Кнопка скачивания
                with open(redrawn_path, "rb") as file:
                    st.download_button(
                        label="Скачать результат",
                        data=file,
                        file_name=redrawn_filename,
                        mime="image/png",
                        key=f"dl_{selected_image}",
                        width="stretch"
                    )
                
                if st.button("Перерисовать заново", key=f"redraw_btn_{selected_image}", width="stretch"):
                    self._redraw_image(selected_image, image_path, metadata, pipeline)
            else:
                st.warning("Изображение еще не улучшено")
                st.info("NanaBanana Pro удалит артефакты, сделает изображение четким и повысит качество до HD.")
                
                if get_nanobanana_api_key():
                    if st.button("Улучшить через NanaBanana Pro", type="primary", key=f"redraw_btn_{selected_image}", width="stretch"):
                        self._redraw_image(selected_image, image_path, metadata, pipeline)
                else:
                    st.error("Настройте API ключ Nano Banana в 'Настройках'")

    def _extract_medical_terms(self, text: str) -> str:
        """Извлекает ключевые медицинские термины из текста и переводит их на английский"""
        # Словарь распространенных медицинских терминов
        medical_translations = {
            # Анатомия
            'легкое': 'lung',
            'сердце': 'heart',
            'печень': 'liver',
            'почки': 'kidneys',
            'желудок': 'stomach',
            'кишечник': 'intestine',
            'мозг': 'brain',
            'кости': 'bones',
            'суставы': 'joints',
            'кровь': 'blood',
            'мышцы': 'muscles',

            # Патологии
            'эмфизема': 'emphysema',
            'рак': 'cancer',
            'опухоль': 'tumor',
            'инфаркт': 'infarction',
            'инсульт': 'stroke',
            'перелом': 'fracture',
            'воспаление': 'inflammation',
            'инфекция': 'infection',
            'тромб': 'thrombus',
            'спазм': 'spasm',

            # Методы диагностики
            'рентген': 'x-ray',
            'томограмма': 'tomogram',
            'ультразвук': 'ultrasound',
            'компьютерная томография': 'CT scan',
            'магнитно-резонансная томография': 'MRI',

            # Клинические признаки
            'боль': 'pain',
            'отек': 'edema',
            'кровотечение': 'bleeding',
            'температура': 'fever',
            'давление': 'pressure',

            # Органы и системы
            'дыхательная система': 'respiratory system',
            'сердечно-сосудистая система': 'cardiovascular system',
            'пищеварительная система': 'digestive system',
            'нервная система': 'nervous system',
            'мочевыделительная система': 'urinary system',
        }

        found_terms = []

        # Приводим текст к нижнему регистру для поиска
        text_lower = text.lower()

        # Ищем совпадения с медицинскими терминами
        for ru_term, en_term in medical_translations.items():
            if ru_term in text_lower:
                found_terms.append(en_term)

        # Ищем специфические паттерны
        if 'рентген' in text_lower or 'радиография' in text_lower:
            found_terms.append('chest x-ray')

        if 'томограмма' in text_lower:
            found_terms.append('CT scan')

        if 'эмфизема легкого' in text_lower:
            found_terms.append('lung emphysema')

        # Удаляем дубликаты и ограничиваем количество терминов
        unique_terms = list(set(found_terms))[:5]  # Максимум 5 терминов

        if unique_terms:
            return ', '.join(unique_terms)
        else:
            # Если не найдено специфических терминов, возвращаем общий термин
            return 'medical anatomy'

        # Кнопка перерисовки удалена отсюда, так как она перенесена в _render_current_image
        pass

    def _redraw_image(self, selected_image, image_path, metadata, pipeline):
        """Перерисовка изображения через Nano Banana"""
        st.markdown("---")
        st.subheader("Перерисовка изображения")

        # Используем описание рисунка из подписи к изображению
        if metadata and metadata.get("text_around"):
            text_around = metadata["text_around"].strip()
            classification = metadata.get("classification", "unknown")

            # Извлекаем ключевые медицинские термины и создаем понятный промпт
            medical_terms = self._extract_medical_terms(text_around)

            if medical_terms:
                # Создаем понятный промпт на основе извлеченных терминов
                if classification == "clinical":
                    prompt = f"""Generate a detailed clinical medical illustration showing {medical_terms}.

Create a professional anatomical diagram with clear medical details, showing the pathology and anatomical structures. High-quality medical illustration style, anatomically accurate, educational purpose.

IMPORTANT: Generate a CLEAN image with NO text, NO labels, NO captions, NO writing, NO annotations, NO legends. Only pure visual medical illustration elements."""
                elif classification == "encyclopedia":
                    prompt = f"""Create a detailed anatomical diagram illustrating {medical_terms}.

Professional medical illustration style, clear anatomical structures, educational scientific diagram, precise medical details.

IMPORTANT: Generate a CLEAN image with NO text, NO labels, NO captions, NO writing, NO annotations, NO legends. Only pure visual medical illustration elements."""
                else:
                    prompt = f"""Generate a detailed medical illustration showing {medical_terms}.

Professional anatomical diagram, clear medical structures, high-quality educational illustration.

IMPORTANT: Generate a CLEAN image with NO text, NO labels, NO captions, NO writing, NO annotations, NO legends. Only pure visual medical illustration elements."""
            else:
                # Fallback для случаев, когда не удалось извлечь термины
                prompt = f"""Generate a detailed medical illustration of anatomical structures.

Professional medical illustration style, clear anatomical details, educational purpose.

IMPORTANT: Generate a CLEAN image with NO text, NO labels, NO captions, NO writing, NO annotations, NO legends. Only pure visual medical illustration elements."""

        else:
            # Fallback промпт если подпись отсутствует
            prompt = f"""Generate a detailed anatomical medical illustration.

Professional medical illustration style, clear anatomical structures, educational purpose.

IMPORTANT: Generate a CLEAN image with NO text, NO labels, NO captions, NO writing, NO annotations, NO legends. Only pure visual medical illustration elements."""

        # Улучшение промпта через DeepSeek/ChatGPT если доступно
        if st.checkbox("Улучшить промпт с помощью AI", value=True, help="Использовать LLM для создания детального художественного описания"):
            with st.spinner("Улучшение промпта через AI..."):
                try:
                    refine_prompt = f"""
                    На основе этой подписи к медицинскому рисунку: "{text_around}"
                    Создай детальный промпт на АНГЛИЙСКОМ языке для генерации высококачественной медицинской иллюстрации в стиле Imagen 3.
                    Опиши освещение, текстуру, анатомическую точность. 
                    Укажи, что на рисунке НЕ должно быть текста.
                    Верни ТОЛЬКО текст промпта на английском.
                    """
                    
                    from main import TextProcessor
                    # Инициализируем процессор с текущими настройками API
                    llm_processor = TextProcessor()
                    refined = llm_processor.client.chat.completions.create(
                        model=llm_processor.model,
                        messages=[
                            {"role": "system", "content": "You are an expert in medical illustration prompts for AI image generators."},
                            {"role": "user", "content": refine_prompt}
                        ],
                        temperature=0.7
                    ).choices[0].message.content.strip()
                    
                    if refined:
                        prompt = refined
                except Exception as e:
                    st.warning(f"Не удалось улучшить промпт через AI: {e}. Используется базовый промпт.")

        # Отображение промпта
        st.markdown("**Итоговый промпт для NanaBanana Pro:**")
        st.info(prompt)
        st.markdown("*Промпт оптимизирован для медицинской визуализации высокого качества*")

        # Показываем прогресс
        with st.spinner("Генерация изображения через Google Gemini..."):
            try:
                # Вызываем перерисовку
                result_path, redraw_error = pipeline.redraw_image_with_nanobanana(
                    image_info={
                        "file_path": image_path,
                        "text_around": prompt,
                        "classification": metadata.get("classification", "unknown") if metadata else "unknown",
                        "pathology": metadata.get("pathology") if metadata else None
                    },
                    custom_prompt=prompt,
                    size="1024x1024"
                )

                if result_path:
                    st.success("Изображение успешно перерисовано.")

                    # Отображаем результат
                    col_res1, col_res2 = st.columns(2)

                    with col_res1:
                        st.markdown("**Оригинал:**")
                        _safe_st_image(image_path, width="stretch")

                    with col_res2:
                        st.markdown("**Перерисовано:**")
                        _safe_st_image(result_path, caption=f"Перерисовано: {os.path.basename(result_path)}", width="stretch")

                    # Кнопка скачивания
                    with open(result_path, "rb") as file:
                        st.download_button(
                            label="Скачать изображение",
                            data=file,
                            file_name=os.path.basename(result_path),
                            mime="image/png",
                            key=f"download_redraw_{selected_image}"
                        )
                else:
                    st.error(redraw_error or "Не удалось перерисовать изображение. Проверьте API ключ и попробуйте снова.")

            except Exception as e:
                st.error(f"Ошибка при перерисовке: {str(e)}")
                st.info("Убедитесь, что API ключ NanoBanana корректен и у вас есть доступ к Google Gemini API")
