"""
Главный файл приложения Text Re-phraser
"""

import os
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
from ui.base import BaseUI
from ui.tabs.text_tab import TextTab
from ui.tabs.results_tab import ResultsTab
from ui.tabs.images_tab import ImagesTab
from ui.tabs.settings_tab import SettingsTab
from ui.tabs.moderators_tab import ModeratorsTab
from ui.tabs.books_tab import BooksTab
from config import ADMIN_USERNAME, ADMIN_PASSWORD, TAB_NAMES
from core.users import authenticate_moderator
from core.session_store import create_session, get_session, delete_session

# Куки для «Запомнить меня» — инициализация в начале скрипта
COOKIE_PREFIX = "med_book/"
cookies = EncryptedCookieManager(
    prefix=COOKIE_PREFIX,
    password=os.environ.get("COOKIES_PASSWORD", "med_book_session_secret_change_in_production"),
)
 

class TextRephraserApp:
    """Главный класс приложения Text Re-phraser"""

    def __init__(self):
        """Инициализация приложения"""
        self.ui = BaseUI()
        self.tabs = {
            'books': BooksTab(),
            'text': TextTab(),
            'results': ResultsTab(),
            'images': ImagesTab(),
            'settings': SettingsTab(),
            'moderators': ModeratorsTab(),
        }

        # Проверка авторизации
        if not st.session_state.get("authenticated", False):
            self.show_login()
            return

        # Кнопка выхода в сайдбаре
        with st.sidebar:
            name = st.session_state.get("display_name") or st.session_state.get("username") or ""
            role = st.session_state.get("user_role", "guest")
            if name:
                st.caption(f"Пользователь: {name} ({role})")
            st.markdown("---")
            if st.button("Выйти", width="stretch"):
                try:
                    auth_token = cookies["auth_token"]
                    delete_session(auth_token)
                    del cookies["auth_token"]
                    cookies.save()
                except (KeyError, TypeError, AttributeError):
                    pass
                st.session_state.authenticated = False
                st.session_state.user_role = "guest"
                st.session_state.username = ""
                st.session_state.display_name = ""
                st.rerun()

        # Создание табов
        user_role = st.session_state.get("user_role", "guest")
        if user_role == "admin":
            tab_names = TAB_NAMES
        elif user_role == "moderator":
            tab_names = ["Книги"]
        else:
            tab_names = []
        tab_containers = self.ui.create_tabs(tab_names)
        tab_map = dict(zip(tab_names, tab_containers))

        # Отображение табов (защита от пустого tab_map при роли guest)
        if "Книги" not in tab_map:
            return
        self.tabs['books'].render(tab_map["Книги"])
        if user_role == "admin":
            self.tabs['text'].render(tab_map["Перефразирование"])
            self.tabs['results'].render(tab_map["Результаты"])
            self.tabs['images'].render(tab_map["Иллюстрации"])
            self.tabs['settings'].render(tab_map["Настройки"])
        if user_role == "admin":
            self.tabs['moderators'].render(tab_map["Модераторы"])

    def show_login(self):
        """Отображение формы входа"""
        # Стилизация страницы входа
        st.markdown("""
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

            html, body, .stApp, [class*="css"]  {
                font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans", sans-serif;
                color: #0b0f14;
            }

            /* Make login page feel like a standalone landing */
            header, footer { visibility: hidden; height: 0; }
            #MainMenu { visibility: hidden; }
            .stApp { background: radial-gradient(1200px 800px at 15% 10%, #e9f1ff 0%, rgba(233,241,255,0) 55%),
                             radial-gradient(900px 700px at 85% 20%, #ffe9f1 0%, rgba(255,233,241,0) 50%),
                             linear-gradient(135deg, #f7fafc 0%, #eef2ff 35%, #f8fafc 100%); }
            .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
            .login-card {
                width: min(520px, 100%);
                background: rgba(255, 255, 255, 0.86);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(15, 23, 42, 0.08);
                border-radius: 18px;
                box-shadow: 0 18px 50px rgba(2, 6, 23, 0.10);
                padding: 28px 28px 22px;
            }
            .brand {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 14px;
                margin-bottom: 14px;
            }
            .brand-left { display: flex; flex-direction: column; gap: 4px; }
            .brand-title { font-size: 28px; font-weight: 700; letter-spacing: -0.02em; line-height: 1.1; }
            .brand-subtitle { color: rgba(15, 23, 42, 0.68); font-size: 14px; }
            .badge {
                font-size: 12px;
                font-weight: 600;
                color: rgba(2, 6, 23, 0.78);
                background: rgba(99, 102, 241, 0.10);
                border: 1px solid rgba(99, 102, 241, 0.18);
                padding: 6px 10px;
                border-radius: 999px;
                white-space: nowrap;
            }

            /* Labels (Логин/Пароль) */
            .stTextInput label, .stPasswordInput label {
                color: #0b0f14 !important;
                font-weight: 600 !important;
            }

            /* Input text (в т.ч. пароль) */
            div[data-baseweb="input"] input {
                color: #0b0f14 !important;
                background: #ffffff !important;
                border: 1px solid rgba(15, 23, 42, 0.18) !important;
                border-radius: 10px !important;
                padding: 10px 12px !important;
            }
            div[data-baseweb="input"] input::placeholder {
                color: rgba(15, 23, 42, 0.55) !important;
            }
            div[data-baseweb="input"] input:focus {
                border-color: rgba(99, 102, 241, 0.55) !important;
                box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.12) !important;
            }

            /* Button styling */
            .stButton button {
                border-radius: 10px !important;
                font-weight: 600 !important;
                padding: 10px 14px !important;
            }
            .stButton button[kind="primary"] {
                background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 55%, #db2777 120%) !important;
                border: none !important;
            }
            .stButton button[kind="primary"]:hover {
                filter: brightness(1.03);
            }
            .login-footer {
                margin-top: 14px;
                color: rgba(15, 23, 42, 0.55);
                font-size: 12px;
            }
            </style>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            st.markdown(
                """
                <div class="brand">
                  <div class="brand-left">
                    <div class="brand-title">Text Rephraser</div>
                    <div class="brand-subtitle">Интеллектуальная обработка научных текстов</div>
                  </div>
                  <div class="badge">Admin</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("#### Вход")

            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Логин", placeholder="Введите логин")
                password = st.text_input("Пароль", type="password", placeholder="Введите пароль")
                remember_me = st.checkbox("Запомнить меня", value=True, help="Сохранить вход в этом браузере на 30 дней")
                submit_button = st.form_submit_button("Войти", type="primary", width="stretch")

                if submit_button:
                    username_norm = (username or "").strip()
                    if username_norm == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                        st.session_state.authenticated = True
                        st.session_state.user_role = "admin"
                        st.session_state.username = ADMIN_USERNAME
                        st.session_state.display_name = "Администратор"
                        if remember_me:
                            token = create_session(ADMIN_USERNAME, "admin", "Администратор")
                            cookies["auth_token"] = token
                            cookies.save()
                        st.success("Успешный вход!")
                        st.rerun()
                    mod = authenticate_moderator(username_norm, password)
                    if mod is not None:
                        st.session_state.authenticated = True
                        st.session_state.user_role = "moderator"
                        st.session_state.username = mod.username
                        st.session_state.display_name = mod.name or mod.username
                        if remember_me:
                            token = create_session(mod.username, "moderator", mod.name or mod.username)
                            cookies["auth_token"] = token
                            cookies.save()
                        st.success("Успешный вход!")
                        st.rerun()
                    st.error("Неверный логин или пароль")

            st.markdown(
                '<div class="login-footer">Подсказка: логин и пароль задаются в <code>config.py</code>.</div>',
                unsafe_allow_html=True,
            )


def main():
    """Точка входа в приложение"""
    BaseUI.setup_page()
    BaseUI.init_session_state()

    # Восстановление сессии из куки при перезагрузке страницы (если пользователь выбрал «Запомнить меня»)
    if not st.session_state.get("authenticated", False):
        auth_token = None
        if cookies.ready():
            try:
                auth_token = cookies["auth_token"]
            except (KeyError, TypeError, AttributeError):
                pass
        if auth_token:
            session_data = get_session(auth_token)
            if session_data:
                st.session_state.pop("_cookie_wait_reruns", None)
                st.session_state.authenticated = True
                st.session_state.user_role = session_data.get("role", "guest")
                st.session_state.username = session_data.get("username", "")
                st.session_state.display_name = session_data.get("display_name", "")
                st.rerun()

        # Куки ещё не загружены (компонент не вернул их с браузера) — даём один шанс перезапустить, чтобы подхватить куки
        if not cookies.ready():
            wait_key = "_cookie_wait_reruns"
            reruns = st.session_state.get(wait_key, 0)
            if reruns < 3:
                st.session_state[wait_key] = reruns + 1
                st.spinner("Загрузка сессии...")
                st.rerun()
            st.session_state.pop(wait_key, None)
    else:
        st.session_state.pop("_cookie_wait_reruns", None)

    TextRephraserApp()


if __name__ == "__main__":
    main()
