"""
Local users storage (moderators).

Stores users in `users.json` in the project root.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.auth import PasswordHash, hash_password, verify_password


USERS_FILE = Path("users.json")
SCHEMA_VERSION = 1


@dataclass
class Moderator:
    name: str
    username: str
    password: PasswordHash
    created_at: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_store() -> dict[str, Any]:
    return {"version": SCHEMA_VERSION, "moderators": []}


def load_store() -> dict[str, Any]:
    if not USERS_FILE.exists():
        return _default_store()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or data.get("version") != SCHEMA_VERSION:
            return _default_store()
        if "moderators" not in data or not isinstance(data["moderators"], list):
            data["moderators"] = []
        return data
    except Exception:
        return _default_store()


def save_store(store: dict[str, Any]) -> None:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)


def list_moderators() -> list[Moderator]:
    store = load_store()
    moderators: list[Moderator] = []
    for item in store.get("moderators", []):
        try:
            pw = PasswordHash(
                salt_b64=item["password"]["salt_b64"],
                hash_b64=item["password"]["hash_b64"],
                iterations=int(item["password"].get("iterations", 200_000)),
            )
            moderators.append(
                Moderator(
                    name=str(item.get("name", "")),
                    username=str(item.get("username", "")),
                    password=pw,
                    created_at=str(item.get("created_at", "")),
                )
            )
        except Exception:
            continue
    moderators.sort(key=lambda m: m.username.lower())
    return moderators


def get_moderator(username: str) -> Moderator | None:
    username_norm = (username or "").strip()
    for mod in list_moderators():
        if mod.username == username_norm:
            return mod
    return None


def add_moderator(*, name: str, username: str, password: str) -> None:
    name = (name or "").strip()
    username = (username or "").strip()
    if not username:
        raise ValueError("Username is required")
    if get_moderator(username) is not None:
        raise ValueError("Username already exists")

    pw = hash_password(password)
    store = load_store()
    store.setdefault("moderators", [])
    store["moderators"].append(
        {
            "name": name,
            "username": username,
            "password": asdict(pw),
            "created_at": _now_iso(),
        }
    )
    save_store(store)


def delete_moderator(username: str) -> None:
    username = (username or "").strip()
    store = load_store()
    before = len(store.get("moderators", []))
    store["moderators"] = [m for m in store.get("moderators", []) if m.get("username") != username]
    after = len(store.get("moderators", []))
    if before == after:
        raise ValueError("Moderator not found")
    save_store(store)


def set_moderator_password(username: str, new_password: str) -> None:
    username = (username or "").strip()
    store = load_store()
    found = False
    for m in store.get("moderators", []):
        if m.get("username") == username:
            m["password"] = asdict(hash_password(new_password))
            found = True
            break
    if not found:
        raise ValueError("Moderator not found")
    save_store(store)


def authenticate_moderator(username: str, password: str) -> Moderator | None:
    mod = get_moderator(username)
    if mod is None:
        return None
    if verify_password(password, mod.password):
        return mod
    return None

