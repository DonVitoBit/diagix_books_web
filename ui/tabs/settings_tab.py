"""
Модуль вкладки настроек и информации
"""

import streamlit as st
from openai import OpenAI
from settings_manager import (
    has_api_key, get_api_key, set_api_key, settings_manager,
    get_nanobanana_api_key, set_nanobanana_api_key,
    get_dalle_api_key, set_dalle_api_key,
    get_google_search_api_key, set_google_search_api_key,
    get_google_search_engine_id, set_google_search_engine_id,
    get_tavily_api_key, set_tavily_api_key,
    get_deepseek_api_key, set_deepseek_api_key,
    get_gemini_api_key, set_gemini_api_key,
    get_llm_provider, set_llm_provider
)


# Таймаут проверки ключа (секунды), чтобы не зависать при недоступности API
OPENAI_VERIFY_TIMEOUT = 10.0

from ui.utils import slider_value_for_step


def _verify_openai_api_key(api_key: str) -> tuple[bool, str]:
    """
    Проверяет ключ OpenAI реальным запросом к API.
    Возвращает (успех, сообщение).
    """
    if not api_key or not api_key.strip():
        return False, "Ключ не указан"
    try:
        client = OpenAI(api_key=api_key.strip(), timeout=OPENAI_VERIFY_TIMEOUT)
        # Минимальный запрос: список моделей — не списывает квоту
        next(iter(client.models.list()), None)
        return True, "Ключ действителен, API доступен"
    except Exception as e:
        err = str(e).strip()
        if "timeout" in err.lower() or "timed out" in err.lower():
            return False, "Таймаут: API не ответил вовремя. Проверьте интернет или попробуйте позже."
        if "Incorrect API key" in err or "invalid_api_key" in err or "401" in err:
            return False, "Неверный или недействительный API ключ"
        if "rate_limit" in err.lower() or "429" in err:
            return False, "Превышен лимит запросов (ключ при этом может быть верным)"
        return False, f"Ошибка проверки: {err[:200]}"


class SettingsTab:
    """Класс для управления вкладкой настроек"""

    def render(self, tab):
        """Отображение вкладки настроек"""
        with tab:
            st.header("Настройки и информация")

            self._render_llm_provider_settings()
            self._render_model_presets()
            self._render_openai_settings()
            self._render_deepseek_settings()
            self._render_gemini_settings()
            self._render_illustration_api_settings()
            self._render_token_budget()
            self._render_help_section()

    def _render_openai_settings(self):
        """Отображение настроек OpenAI API"""
        st.subheader("Управление API ключом")

        # Статус API ключа
        if has_api_key():
            st.success("API ключ сохранен")
            masked_key = get_api_key()
            if len(masked_key) > 12:
                masked_key = f"{masked_key[:8]}...{masked_key[-4:]}"
            st.code(f"Ключ: {masked_key}", language=None)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Изменить API ключ", width="stretch"):
                    st.session_state.show_api_key_settings = True
            with col2:
                if st.button("Удалить API ключ", width="stretch"):
                    settings_manager.clear_api_key()
                    st.session_state.api_key_saved = False
                    st.session_state.api_key_status = "API ключ не установлен"
                    st.success("API ключ удален.")
                    st.rerun()
        else:
            st.warning("API ключ не установлен")
            if st.button("Добавить API ключ", width="stretch"):
                st.session_state.show_api_key_settings = True

        # Форма для ввода API ключа
        if st.session_state.get('show_api_key_settings', False):
            with st.expander("Настройка API ключа", expanded=True):
                st.markdown("Введите ваш API ключ")

                new_api_key = st.text_input(
                    "API-ключ",
                    type="password",
                    help="Введите ваш API-ключ",
                    key="settings_api_key_input"
                )

                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    if st.button("Сохранить", width="stretch"):
                        if new_api_key and new_api_key.strip():
                            set_api_key(new_api_key.strip())
                            st.session_state.api_key_saved = True
                            st.session_state.api_key_status = "API ключ сохранен"
                            st.session_state.show_api_key_settings = False
                            st.success("API ключ успешно сохранен.")
                            st.rerun()
                        else:
                            st.error("API ключ не может быть пустым")

                with col2:
                    if st.button("Проверить", width="stretch"):
                        if new_api_key and new_api_key.strip():
                            with st.spinner("Проверка API ключа..."):
                                ok, message = _verify_openai_api_key(new_api_key.strip())
                            if ok:
                                st.success(message)
                            else:
                                st.error(message)
                        else:
                            st.error("Введите API ключ для проверки")

                with col3:
                    if st.button("Отмена", width="stretch"):
                        st.session_state.show_api_key_settings = False
                        st.rerun()

    def _render_llm_provider_settings(self):
        """Отображение выбора провайдера LLM"""
        st.subheader("Выбор провайдера LLM")

        # Явный порядок: все три провайдера отображаются в radio
        provider_options = [
            ("openai", "OpenAI (ChatGPT)"),
            ("deepseek", "DeepSeek"),
            ("gemini", "Google Gemini"),
        ]
        options_keys = [p[0] for p in provider_options]
        options_labels = {p[0]: p[1] for p in provider_options}

        current_provider = get_llm_provider()
        try:
            provider_index = options_keys.index(current_provider)
        except ValueError:
            provider_index = 0

        selected_provider = st.radio(
            "Выберите провайдера для перефразирования:",
            options=options_keys,
            format_func=lambda x: options_labels[x],
            index=provider_index,
            horizontal=True,
            key="llm_provider_radio",
        )

        if selected_provider != current_provider:
            set_llm_provider(selected_provider)
            st.success(f"Провайдер изменен на {options_labels[selected_provider]}")
            st.rerun()

    def _render_model_presets(self):
        """Пресеты настроек модели: сохранение текущих и выбор сохранённых."""
        st.markdown("---")
        st.subheader("Пресеты настроек модели")
        st.caption("Сохраните текущие настройки (провайдер, модель, температура, стиль статьи и т.д.) под именем и переключайтесь между ними.")

        presets = settings_manager.get_model_presets()
        preset_names = sorted(presets.keys())

        # Выбор и применение пресета
        col_sel, col_btn = st.columns([2, 1])
        with col_sel:
            options = ["— Выберите пресет —"] + preset_names
            selected = st.selectbox(
                "Сохранённые пресеты",
                options=options,
                index=0,
                key="settings_model_preset_select",
            )
        with col_btn:
            apply_clicked = st.button("Применить пресет", key="settings_apply_preset")
        if apply_clicked and selected and selected != "— Выберите пресет —":
            if settings_manager.load_model_preset(selected):
                st.success(f"Пресет «{selected}» применён. Обновите страницу или перейдите на вкладку «Текст», чтобы увидеть настройки.")
                st.rerun()
            else:
                st.error("Пресет не найден.")

        # Сохранение текущих настроек как новый пресет
        with st.expander("Сохранить текущие настройки как пресет", expanded=not preset_names):
            preset_name = st.text_input(
                "Название пресета",
                placeholder="Например: Статьи на Gemini, Быстрый перефраз…",
                key="settings_new_preset_name",
            )
            col_save, col_del = st.columns(2)
            with col_save:
                if st.button("Сохранить пресет", key="settings_save_preset"):
                    if (preset_name or "").strip():
                        settings_manager.save_model_preset(preset_name.strip())
                        st.success(f"Пресет «{preset_name.strip()}» сохранён.")
                        st.rerun()
                    else:
                        st.error("Введите название пресета.")
            with col_del:
                if selected and selected != "— Выберите пресет —" and st.button("Удалить выбранный пресет", key="settings_delete_preset"):
                    settings_manager.delete_model_preset(selected)
                    st.success(f"Пресет «{selected}» удалён.")
                    st.rerun()

    def _render_deepseek_settings(self):
        """Отображение настроек DeepSeek API"""
        # Гарантируем наличие флага в session_state
        if "show_deepseek_key_settings" not in st.session_state:
            st.session_state.show_deepseek_key_settings = False

        st.markdown("---")
        st.subheader("DeepSeek API")

        # Статус API ключа
        deepseek_key = get_deepseek_api_key()
        if deepseek_key:
            st.success("DeepSeek API ключ сохранен")
            masked_key = deepseek_key
            if len(masked_key) > 12:
                masked_key = f"{masked_key[:8]}...{masked_key[-4:]}"
            st.code(f"Ключ: {masked_key}", language=None)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Изменить DeepSeek ключ", width="stretch", key="btn_change_ds_key"):
                    st.session_state.show_deepseek_key_settings = True
                    st.rerun()
            with col2:
                if st.button("Удалить DeepSeek ключ", width="stretch", key="btn_delete_ds_key"):
                    set_deepseek_api_key("")
                    st.session_state.show_deepseek_key_settings = False
                    st.success("DeepSeek API ключ удален.")
                    st.rerun()
        else:
            st.warning("DeepSeek API ключ не установлен")
            if st.button("Добавить DeepSeek API ключ", width="stretch", key="btn_add_ds_key"):
                st.session_state.show_deepseek_key_settings = True
                st.rerun()

        # Форма для ввода API ключа
        if st.session_state.show_deepseek_key_settings:
            with st.expander("Настройка DeepSeek API", expanded=True):
                st.markdown("Введите ваш DeepSeek API ключ")

                new_ds_key = st.text_input(
                    "DeepSeek API-ключ",
                    type="password",
                    help="Введите ваш API-ключ от DeepSeek",
                    key="settings_deepseek_key_input"
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Сохранить DeepSeek", width="stretch", key="btn_save_ds_key"):
                        if new_ds_key and new_ds_key.strip():
                            set_deepseek_api_key(new_ds_key.strip())
                            st.session_state.show_deepseek_key_settings = False
                            st.success("DeepSeek API ключ успешно сохранен.")
                            st.rerun()
                        else:
                            st.error("API ключ не может быть пустым")

                with col2:
                    if st.button("Отмена ", width="stretch", key="btn_cancel_ds_key"):
                        st.session_state.show_deepseek_key_settings = False
                        st.rerun()

    def _render_gemini_settings(self):
        """Отображение настроек Gemini API"""
        st.markdown("---")
        st.subheader("Google Gemini API")

        gemini_key = get_gemini_api_key()
        if gemini_key:
            st.success("Gemini API ключ сохранен")
            masked_key = gemini_key
            if len(masked_key) > 12:
                masked_key = f"{masked_key[:8]}...{masked_key[-4:]}"
            st.code(f"Ключ: {masked_key}", language=None)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Изменить Gemini ключ", width="stretch"):
                    st.session_state.show_gemini_key_settings = True
            with col2:
                if st.button("Удалить Gemini ключ", width="stretch"):
                    set_gemini_api_key("")
                    st.success("Gemini API ключ удален.")
                    st.rerun()
        else:
            st.warning("Gemini API ключ не установлен")
            if st.button("Добавить Gemini API ключ", width="stretch"):
                st.session_state.show_gemini_key_settings = True

        if st.session_state.get("show_gemini_key_settings", False):
            with st.expander("Настройка Gemini API", expanded=True):
                st.markdown("Введите ваш Google AI (Gemini) API ключ")
                st.caption("Ключ можно получить в Google AI Studio: https://aistudio.google.com/apikey")

                new_gemini_key = st.text_input(
                    "Gemini API-ключ",
                    type="password",
                    help="Введите ваш API-ключ от Google Gemini",
                    key="settings_gemini_key_input"
                )

                # Проверенные ID для generateContent (production + preview)
                gemini_models = [
                    "gemini-3-pro-image-preview", # Новая модель для фото
                    "gemini-1.5-flash",          # Стабильная для AI Studio
                    "gemini-1.5-pro",            # Pro версия
                    "gemini-2.0-flash",          # Новое поколение
                    "gemini-2.0-flash-exp",
                    "gemini-2.0-pro-exp",
                    "gemini-2.5-flash",          
                    "gemini-2.5-pro",            
                ]
                current_model = settings_manager.get("gemini_model", "gemini-2.5-flash")
                idx = gemini_models.index(current_model) if current_model in gemini_models else 0
                selected_model = st.selectbox(
                    "Модель Gemini",
                    options=gemini_models,
                    index=idx,
                    help="Production: 2.5-flash / 2.5-pro / 2.5-flash-lite. Preview-модели могут меняться.",
                    key="settings_gemini_model",
                )
                if selected_model != current_model:
                    settings_manager.set("gemini_model", selected_model)
                    st.success(f"Модель сохранена: {selected_model}")

                _art = settings_manager.get("max_tokens_article", 32768)
                gemini_max_tokens = st.slider(
                    "Лимит токенов для статей (Gemini)",
                    min_value=100,
                    max_value=65536,
                    value=slider_value_for_step(_art, 100, 65536, 1024),
                    step=1024,
                    help="Максимальная длина ответа при генерации статей. 8192 — короткие статьи, 16384+ — полные. Gemini 2.5 поддерживает до 65536.",
                    key="settings_gemini_max_tokens",
                )
                if gemini_max_tokens != settings_manager.get("max_tokens_article", 32768):
                    settings_manager.set("max_tokens_article", int(gemini_max_tokens))
                    st.caption(f"Сохранено: {gemini_max_tokens} токенов")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Сохранить Gemini", width="stretch"):
                        if new_gemini_key and new_gemini_key.strip():
                            set_gemini_api_key(new_gemini_key.strip())
                            st.session_state.show_gemini_key_settings = False
                            st.success("Gemini API ключ успешно сохранен.")
                            st.rerun()
                        else:
                            st.error("API ключ не может быть пустым")

                with col2:
                    if st.button("Отмена Gemini", width="stretch"):
                        st.session_state.show_gemini_key_settings = False
                        st.rerun()

    def _render_illustration_api_settings(self):
        """Отображение настроек API для иллюстраций"""
        st.markdown("---")
        st.subheader("API ключи для иллюстраций")

        # DALL-E 2 API
        if get_dalle_api_key():
            st.success("DALL-E 2 API ключ настроен")
            if st.button("Удалить DALL-E 2 API ключ", width="stretch"):
                set_dalle_api_key("")
                st.rerun()
        else:
            st.warning("DALL-E 2 API ключ не установлен")
            if st.button("Добавить DALL-E 2 API ключ", width="stretch"):
                st.session_state.show_dalle_settings = True

        # NanoBanana API
        if get_nanobanana_api_key():
            st.success("NanoBanana API ключ настроен")
            if st.button("Удалить NanoBanana API ключ", width="stretch"):
                set_nanobanana_api_key("")
                st.rerun()
        else:
            st.warning("NanoBanana API ключ не установлен")
            if st.button("Добавить NanoBanana API ключ", width="stretch"):
                st.session_state.show_nanobanana_settings = True

        # Tavily API
        if get_tavily_api_key():
            st.success("Tavily Search API настроен")
            if st.button("Удалить Tavily API ключ", width="stretch"):
                set_tavily_api_key("")
                st.rerun()
        else:
            st.warning("Tavily Search API не настроен (рекомендуется)")
            if st.button("Добавить Tavily API ключ", width="stretch"):
                st.session_state.show_tavily_settings = True

        # Google Custom Search API
        if get_google_search_api_key() and get_google_search_engine_id():
            st.success("Google Custom Search API настроен")
            if st.button("Удалить Google Custom Search API", width="stretch"):
                set_google_search_api_key("")
                set_google_search_engine_id("")
                st.rerun()
        else:
            st.info("Google Custom Search API не настроен (опционально)")
            if st.button("Настроить Google Custom Search API", width="stretch"):
                st.session_state.show_google_settings = True

        # Формы настройки дополнительных API
        self._render_additional_api_forms()

    def _render_additional_api_forms(self):
        """Отображение форм для настройки дополнительных API"""

        # Форма DALL-E
        if st.session_state.get('show_dalle_settings', False):
            with st.expander("Настройка DALL-E 2 API", expanded=True):
                st.markdown("Введите ваш API ключ OpenAI для доступа к DALL-E 2")
                st.info("DALL-E 2 требует действующей подписки OpenAI и доступ к API")

                dalle_key = st.text_input(
                    "DALL-E 2 API-ключ",
                    type="password",
                    help="Введите ваш API-ключ от OpenAI (тот же, что используется для ChatGPT)",
                    key="dalle_api_key_input"
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Сохранить", width="stretch"):
                        if dalle_key and dalle_key.strip():
                            set_dalle_api_key(dalle_key.strip())
                            st.session_state.show_dalle_settings = False
                            st.success("DALL-E 2 API ключ сохранен.")
                            st.rerun()
                        else:
                            st.error("API ключ не может быть пустым")

                with col2:
                    if st.button("Отмена", width="stretch"):
                        st.session_state.show_dalle_settings = False
                        st.rerun()

        # Форма NanoBanana
        if st.session_state.get('show_nanobanana_settings', False):
            with st.expander("Настройка NanoBanana API", expanded=True):
                st.markdown("Введите ваш API ключ NanoBanana")

                nanobanana_key = st.text_input(
                    "NanoBanana API-ключ",
                    type="password",
                    help="Введите ваш API-ключ от NanoBanana",
                    key="nanobanana_api_key_input"
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Сохранить NanoBanana", width="stretch"):
                        if nanobanana_key and nanobanana_key.strip():
                            set_nanobanana_api_key(nanobanana_key.strip())
                            st.session_state.show_nanobanana_settings = False
                            st.success("NanoBanana API ключ сохранен.")
                            st.rerun()
                        else:
                            st.error("API ключ не может быть пустым")

                with col2:
                    if st.button("Отмена", width="stretch"):
                        st.session_state.show_nanobanana_settings = False
                        st.rerun()

        # Форма Tavily
        if st.session_state.get('show_tavily_settings', False):
            with st.expander("Настройка Tavily Search API", expanded=True):
                st.markdown("Введите ваш API ключ Tavily для поиска медицинских изображений")
                
                tavily_key = st.text_input(
                    "Tavily API-ключ",
                    type="password",
                    help="Введите ваш API-ключ от Tavily",
                    key="tavily_api_key_input"
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Сохранить Tavily", width="stretch"):
                        if tavily_key and tavily_key.strip():
                            set_tavily_api_key(tavily_key.strip())
                            st.session_state.show_tavily_settings = False
                            st.success("Tavily API ключ сохранен.")
                            st.rerun()
                        else:
                            st.error("API ключ не может быть пустым")

                with col2:
                    if st.button("Отмена  ", width="stretch"):
                        st.session_state.show_tavily_settings = False
                        st.rerun()

        # Форма Google Custom Search
        if st.session_state.get('show_google_settings', False):
            with st.expander("Настройка Google Custom Search API", expanded=True):
                st.markdown("Введите настройки Google Custom Search API")

                google_key = st.text_input(
                    "Google API Key",
                    type="password",
                    help="Введите ваш Google API Key",
                    key="google_api_key_input"
                )

                search_engine_id = st.text_input(
                    "Search Engine ID",
                    help="Введите ваш Custom Search Engine ID",
                    key="search_engine_id_input"
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Сохранить Google API", width="stretch"):
                        if google_key and search_engine_id:
                            set_google_search_api_key(google_key.strip())
                            set_google_search_engine_id(search_engine_id.strip())
                            st.session_state.show_google_settings = False
                            st.success("Google Custom Search API настроен.")
                            st.rerun()
                        else:
                            st.error("Заполните все поля")

                with col2:
                    if st.button("Отмена", width="stretch"):
                        st.session_state.show_google_settings = False
                        st.rerun()

    def _render_token_budget(self):
        """Отображение лимита расхода токенов и текущей статистики."""
        st.markdown("---")
        st.subheader("Лимит расхода токенов")
        st.caption("Установите месячный лимит расходов (в USD). 0 — без лимита.")

        current_budget = float(settings_manager.get("token_budget_usd", 0) or 0)
        budget = st.number_input(
            "Лимит расходов (USD / 30 дней)",
            min_value=0.0,
            max_value=1000.0,
            value=current_budget,
            step=1.0,
            format="%.2f",
            key="settings_token_budget",
        )
        if budget != current_budget:
            settings_manager.set("token_budget_usd", float(budget))
            st.success(f"Лимит сохранён: ${budget:.2f}")

        try:
            from core.db import get_token_usage_totals, list_token_usage
            totals = get_token_usage_totals(period_days=30)
            t_in = int(totals.get("total_input", 0))
            t_out = int(totals.get("total_output", 0))
            t_cost = float(totals.get("total_cost", 0) or 0)
            n_req = int(totals.get("num_requests", 0))
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Запросов (30 дн.)", f"{n_req:,}")
            with col2:
                st.metric("Входных токенов", f"{t_in:,}")
            with col3:
                st.metric("Выходных токенов", f"{t_out:,}")
            with col4:
                if budget > 0:
                    pct = min(100, t_cost / budget * 100) if budget else 0
                    st.metric("Расход", f"${t_cost:.4f}", delta=f"{pct:.0f}% от лимита")
                else:
                    st.metric("Расход", f"${t_cost:.4f}")

            with st.expander("Последние запросы", expanded=False):
                recent = list_token_usage(limit=20)
                if recent:
                    for r in recent:
                        cost_str = f"${r['cost_usd']:.6f}" if r.get("cost_usd") else "—"
                        st.caption(
                            f"{r.get('created_at', '')[:16]} • {r.get('operation', '')} • "
                            f"{r.get('provider', '')}/{r.get('model', '')} • "
                            f"вх {r.get('input_tokens', 0):,} / вых {r.get('output_tokens', 0):,} • {cost_str}"
                        )
                else:
                    st.caption("Нет данных.")
        except Exception:
            st.caption("Статистика расхода пока недоступна (будет после первого запроса).")

    def _render_help_section(self):
        """Отображение секции помощи"""
        st.markdown("---")
        st.subheader("Параметры обработки")

        current_temp = settings_manager.get("temperature", 0.4)
        st.markdown(f"""
        **Максимальная длина блока:** 500 символов
        **Температура (текущая):** {current_temp} (от 0.0 до 1.0)

        **Информация о температуре:**
        - **0.0-0.3**: Консервативный режим - минимальные изменения
        - **0.4-0.6**: Сбалансированный режим - умеренное перефразирование
        - **0.7-1.0**: Творческий режим - более вариативное переформулирование
        """)

        st.markdown("---")
        st.subheader("Максимальное количество токенов (LLM)")
        col_par, col_art = st.columns(2)
        with col_par:
            _mt = settings_manager.get("max_tokens", 8192)
            max_tokens = st.slider(
                "Перефразирование (макс. токенов на блок)",
                min_value=100,
                max_value=8192,
                value=slider_value_for_step(_mt, 100, 8192, 256),
                step=256,
                help="Ограничивает длину ответа модели при перефразировании одного блока.",
                key="settings_max_tokens",
            )
            if max_tokens != settings_manager.get("max_tokens", 8192):
                settings_manager.set("max_tokens", int(max_tokens))
                st.success(f"Сохранено: {max_tokens} токенов")
        with col_art:
            _mta = settings_manager.get("max_tokens_article", 32768)
            max_tokens_article = st.slider(
                "Генерация статей (макс. токенов)",
                min_value=100,
                max_value=65536,
                value=slider_value_for_step(_mta, 100, 65536, 1024),
                step=1024,
                help="Ограничивает длину статьи. 16384+ — полные статьи без обрыва. Gemini 2.5 до 65536.",
                key="settings_max_tokens_article",
            )
            if max_tokens_article != settings_manager.get("max_tokens_article", 32768):
                settings_manager.set("max_tokens_article", int(max_tokens_article))
                st.success(f"Сохранено: {max_tokens_article} токенов")

        st.subheader("Инструкции по использованию")
        st.markdown("""
        1. **Загрузите файл** в поддерживаемом формате (PDF, TXT, MD, DOCX)
        2. **Укажите тему текста** для более точного перефразирования
        3. **Настройте уровень перефразирования** (temperature) с помощью слайдера:
           - 0.0-0.3: Консервативный режим
           - 0.4-0.6: Сбалансированный режим (рекомендуется)
           - 0.7-1.0: Творческий режим
        4. **Настройте API-ключ** в разделе "Настройки"
        5. **Нажмите кнопку** "Начать перефразирование"
        6. **Просмотрите результаты** на вкладке "Результаты"

        **Подробнее:** см. файлы TEMPERATURE_FEATURE.md и USAGE_EXAMPLES.md
        """)

        st.subheader("Возможные проблемы")
        with st.expander("Распространенные ошибки и решения"):
            st.markdown("""
            **Ошибка API-ключа:**
            - Проверьте корректность ключа
            - Убедитесь, что ключ активен

            **Ошибка сети:**
            - Проверьте стабильность соединения

            **Ошибка файла:**
            - Проверьте формат файла
            - Убедитесь, что файл не поврежден
            """)
