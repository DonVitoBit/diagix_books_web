"""
Базовый UI модуль для приложения Text Re-phraser
"""

import streamlit as st
from config import (
    APP_TITLE, APP_ICON, LAYOUT, TAB_NAMES
)
from settings_manager import has_api_key


class BaseUI:
    """Класс для базовой настройки Streamlit интерфейса"""

    @staticmethod
    def setup_page():
        """Настройка страницы Streamlit"""
        kwargs = {
            "page_title": APP_TITLE,
            "layout": LAYOUT,
            "initial_sidebar_state": "expanded",
        }
        if APP_ICON:
            kwargs["page_icon"] = APP_ICON
        st.set_page_config(**kwargs)

    @staticmethod
    def create_tabs(tab_names=None):
        """Создание вкладок приложения"""
        return st.tabs(tab_names if tab_names is not None else TAB_NAMES)

    @staticmethod
    def init_session_state():
        """Инициализация переменных состояния Streamlit"""
        if 'api_key_input' not in st.session_state:
            st.session_state.api_key_input = ""

        if 'api_key_saved' not in st.session_state:
            st.session_state.api_key_saved = has_api_key()

        if 'show_api_key_form' not in st.session_state:
            st.session_state.show_api_key_form = False

        if 'api_key_status' not in st.session_state:
            st.session_state.api_key_status = "API ключ " + ("сохранен" if has_api_key() else "не установлен")

        # Дополнительные переменные состояния для обработки текста
        if 'processing_complete' not in st.session_state:
            st.session_state.processing_complete = False

        if 'original_text' not in st.session_state:
            st.session_state.original_text = ""

        if 'paraphrased_text' not in st.session_state:
            st.session_state.paraphrased_text = ""

        # Переменные состояния для изображений
        if 'current_image_index' not in st.session_state:
            st.session_state.current_image_index = 0

        # Переменные состояния для API ключей
        if 'show_nanobanana_settings' not in st.session_state:
            st.session_state.show_nanobanana_settings = False

        # Состояние авторизации
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_role' not in st.session_state:
            st.session_state.user_role = "guest"  # guest|admin|moderator
        if 'username' not in st.session_state:
            st.session_state.username = ""
        if 'display_name' not in st.session_state:
            st.session_state.display_name = ""
