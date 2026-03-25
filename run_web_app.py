#!/usr/bin/env python3
"""
Скрипт для запуска веб-приложения Text Re-phraser
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
import os


REQUIRED_MODULES = [
    "streamlit",
    "openai",
    "fitz",  # PyMuPDF
    "docx",  # python-docx
    "markdown",
    "langdetect",
]


def _in_venv() -> bool:
    return getattr(sys, "base_prefix", sys.prefix) != sys.prefix


def _missing_modules() -> list[str]:
    missing: list[str] = []
    for module in REQUIRED_MODULES:
        if importlib.util.find_spec(module) is None:
            missing.append(module)
    return missing


def _print_install_help(missing: list[str]) -> None:
    print("❌ Не установлены зависимости для запуска.")
    print(f"Отсутствуют модули: {', '.join(missing)}")
    print()
    if not _in_venv():
        print("💡 Рекомендуется запускать в виртуальном окружении:")
        print("  python3 -m venv .venv")
        print("  source .venv/bin/activate")
        print()
    print("Установите зависимости и повторите запуск:")
    print("  python -m pip install -r requirements.txt")


def _try_install_requirements() -> bool:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    """Запуск веб-приложения Streamlit"""

    parser = argparse.ArgumentParser(description="Run Text Re-phraser Streamlit app")
    parser.add_argument("--host", default="localhost", help="Server address (default: localhost)")
    parser.add_argument("--port", type=int, default=8501, help="Server port (default: 8501)")
    parser.add_argument(
        "--install",
        action="store_true",
        help="Try to install missing dependencies via pip (requires internet access)",
    )
    args, unknown = parser.parse_known_args()

    print("🚀 Запуск веб-приложения Text Re-phraser...")
    print("=" * 50)

    # Проверка наличия файла app.py
    if not os.path.exists("app.py"):
        print("❌ Ошибка: файл app.py не найден!")
        print("💡 Убедитесь, что вы находитесь в корневой директории проекта")
        sys.exit(2)

    missing = _missing_modules()
    if missing:
        if args.install:
            print("⚠️ Обнаружены отсутствующие зависимости. Пытаюсь установить через pip...")
            if not _try_install_requirements():
                print("❌ Установка зависимостей не удалась.")
                _print_install_help(missing)
                sys.exit(1)
            missing = _missing_modules()

        if missing:
            _print_install_help(missing)
            sys.exit(1)

    print("\n" + "=" * 50)
    print("🌐 Запуск веб-сервера...")
    print(f"📱 Приложение будет доступно по адресу: http://{args.host}:{args.port}")
    print("🛑 Для остановки нажмите Ctrl+C")
    print("=" * 50)

    # Запуск Streamlit
    try:
        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",
            "--server.address",
            str(args.host),
            "--server.port",
            str(args.port),
            "--server.enableWebsocketCompression=false",
            "--server.enableCORS=false",
            "--server.enableXsrfProtection=false",
            *unknown,
        ]
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n\n👋 Веб-приложение остановлено пользователем")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка запуска: {e}")
        print("💡 Попробуйте запустить вручную: streamlit run app.py")

if __name__ == "__main__":
    main()
