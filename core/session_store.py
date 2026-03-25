"""
Хранение сессий для «Запомнить меня» — токен → данные пользователя.
Файл .sessions.json в корне проекта (добавлен в .gitignore).
"""

from __future__ import annotations

import json
import os
import secrets
import time
from pathlib import Path
from typing import Any

SESSIONS_FILE = Path(__file__).resolve().parent.parent / ".sessions.json"
COOKIE_MAX_AGE_DAYS = 30


def _load_sessions() -> dict[str, dict[str, Any]]:
    """Загружает сессии из файла."""
    if not SESSIONS_FILE.exists():
        return {}
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_sessions(sessions: dict[str, dict[str, Any]]) -> None:
    """Сохраняет сессии в файл."""
    SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)


def create_session(username: str, role: str, display_name: str) -> str:
    """Создаёт сессию и возвращает токен."""
    token = secrets.token_urlsafe(32)
    sessions = _load_sessions()
    sessions[token] = {
        "username": username,
        "role": role,
        "display_name": display_name,
        "expires_at": time.time() + COOKIE_MAX_AGE_DAYS * 86400,
    }
    _save_sessions(sessions)
    return token


def get_session(token: str) -> dict[str, Any] | None:
    """Возвращает данные сессии по токену или None, если невалидна."""
    if not token or not token.strip():
        return None
    sessions = _load_sessions()
    data = sessions.get(token.strip())
    if not data:
        return None
    if data.get("expires_at", 0) < time.time():
        del sessions[token.strip()]
        _save_sessions(sessions)
        return None
    return {
        "username": data.get("username", ""),
        "role": data.get("role", "guest"),
        "display_name": data.get("display_name", data.get("username", "")),
    }


def delete_session(token: str) -> None:
    """Удаляет сессию по токену."""
    if not token:
        return
    sessions = _load_sessions()
    if token in sessions:
        del sessions[token]
        _save_sessions(sessions)
