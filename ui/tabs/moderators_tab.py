"""
Moderators management tab.
"""

from __future__ import annotations

import re
from datetime import datetime

import streamlit as st

from config import ADMIN_USERNAME
from core.users import add_moderator, delete_moderator, list_moderators, set_moderator_password
from core.db import grant_access, list_books, list_books_for_moderator, revoke_access


_USERNAME_RE = re.compile(r"^[a-zA-Z0-9._-]{3,32}$")


def _format_dt(value: str) -> str:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return value or ""


class ModeratorsTab:
    def render(self, tab):
        with tab:
            st.header("Модераторы")

            if st.session_state.get("user_role") != "admin":
                st.error("Доступ только для администратора.")
                return

            st.subheader("Создать модератора")
            with st.form("create_moderator_form", clear_on_submit=True):
                name = st.text_input("Имя", placeholder="Например: Иван Иванов")
                username = st.text_input("Логин", placeholder="Например: ivanov")
                password = st.text_input("Пароль", type="password", placeholder="Введите пароль")
                password2 = st.text_input("Повторите пароль", type="password", placeholder="Повторите пароль")
                submitted = st.form_submit_button("Создать", type="primary", width="stretch")

                if submitted:
                    username_norm = (username or "").strip()
                    if not username_norm:
                        st.error("Логин не может быть пустым.")
                        return
                    if username_norm == ADMIN_USERNAME:
                        st.error("Этот логин зарезервирован для администратора.")
                        return
                    if not _USERNAME_RE.match(username_norm):
                        st.error("Логин: 3–32 символа (латиница/цифры/._-).")
                        return
                    if not password or len(password) < 6:
                        st.error("Пароль должен быть минимум 6 символов.")
                        return
                    if password != password2:
                        st.error("Пароли не совпадают.")
                        return

                    try:
                        add_moderator(name=(name or "").strip(), username=username_norm, password=password)
                        st.success("Модератор создан. Он может войти по этим данным.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Не удалось создать модератора: {e}")

            st.markdown("---")
            st.subheader("Список модераторов")

            moderators = list_moderators()
            if not moderators:
                st.info("Пока нет созданных модераторов.")
                return

            for mod in moderators:
                label = f"{mod.username}" + (f" — {mod.name}" if mod.name else "")
                with st.expander(label, expanded=False):
                    st.write(f"**Имя:** {mod.name or '—'}")
                    st.write(f"**Логин:** {mod.username}")
                    st.write(f"**Создан:** {_format_dt(mod.created_at)}")

                    st.markdown("**Сменить пароль**")
                    colp1, colp2 = st.columns(2)
                    with colp1:
                        new_password = st.text_input(
                            "Новый пароль",
                            type="password",
                            key=f"pw1_{mod.username}",
                        )
                    with colp2:
                        new_password2 = st.text_input(
                            "Повторите пароль",
                            type="password",
                            key=f"pw2_{mod.username}",
                        )

                    colb1, colb2 = st.columns([1, 1])
                    with colb1:
                        if st.button("Сохранить пароль", key=f"savepw_{mod.username}", width="stretch"):
                            if not new_password or len(new_password) < 6:
                                st.error("Пароль должен быть минимум 6 символов.")
                            elif new_password != new_password2:
                                st.error("Пароли не совпадают.")
                            else:
                                try:
                                    set_moderator_password(mod.username, new_password)
                                    st.success("Пароль обновлён.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Не удалось обновить пароль: {e}")

                    with colb2:
                        if st.button("Удалить модератора", key=f"del_{mod.username}", width="stretch"):
                            try:
                                delete_moderator(mod.username)
                                st.success("Модератор удалён.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Не удалось удалить: {e}")

                    st.markdown("---")
                    st.markdown("**Доступ к книгам**")

                    books = list_books()
                    if not books:
                        st.info("Пока нет сохранённых книг. Сначала перепишите книгу во вкладке «Перефразирование».")
                        continue

                    current_books = {int(b["id"]) for b in list_books_for_moderator(mod.username)}
                    book_options = {f"#{b['id']} — {b['title']}": int(b["id"]) for b in books}
                    selected_labels = [label for label, book_id in book_options.items() if book_id in current_books]

                    selected = st.multiselect(
                        "Выдать доступ к книгам",
                        options=list(book_options.keys()),
                        default=selected_labels,
                        key=f"books_access_{mod.username}",
                    )

                    if st.button(
                        "Сохранить доступ к книгам",
                        key=f"save_access_{mod.username}",
                        width="stretch",
                    ):
                        desired_ids = {book_options[label] for label in selected}
                        to_add = sorted(desired_ids - current_books)
                        to_remove = sorted(current_books - desired_ids)
                        try:
                            for book_id in to_add:
                                grant_access(
                                    book_id=book_id,
                                    moderator_username=mod.username,
                                    granted_by=st.session_state.get("username", "admin"),
                                )
                            for book_id in to_remove:
                                revoke_access(book_id=book_id, moderator_username=mod.username)
                            st.success("Доступ к книгам обновлён.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Не удалось обновить доступ: {e}")
