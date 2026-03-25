# -*- coding: utf-8 -*-
"""
Обработка статей: структура (заголовок, содержание, блоки, источники),
проверка орфографии и пунктуации, вставка ссылок в .md.
"""
import re
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

# Якорь для заголовка: из текста делаем id для ссылок (GitHub-style)
def _heading_to_anchor(line: str) -> str:
    s = line.strip()
    for prefix in ("## ", "# ", "### "):
        if s.startswith(prefix):
            s = s[len(prefix):].strip()
            break
    s = s.lower()
    s = re.sub(r"[^\w\s\-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s or "section"


def normalize_article_structure(text: str, title_override: Optional[str] = None) -> str:
    """
    Приводит текст к структуре: Заголовок → Содержание → Блоки статей → Источники.
    Извлекает заголовок (первый # или первая строка), собирает разделы ##,
    выносит «## Источники» в конец, формирует блок «Содержание» из заголовков.
    """
    if not text or not text.strip():
        return text
    text = text.strip()
    lines = text.split("\n")
    title = title_override
    rest_lines: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if title is None and stripped.startswith("# "):
            title = stripped[2:].strip()
            i += 1
            continue
        if title is None and stripped and not stripped.startswith("#"):
            title = stripped
            i += 1
            continue
        rest_lines.append(line)
        i += 1
    if not title:
        title = "Статья"
    body = "\n".join(rest_lines).strip()

    # Разбить по ## (не ###)
    section_pattern = re.compile(r"^(## )(.+)$", re.MULTILINE)
    parts = section_pattern.split(body)
    sections: List[Tuple[str, str]] = []
    current_header = ""
    current_content: List[str] = []
    for j, p in enumerate(parts):
        if j == 0 and p.strip():
            current_content.append(p.strip())
            continue
        if p == "## " and j + 1 < len(parts):
            if current_header or current_content:
                content = "\n\n".join(current_content).strip()
                if current_header or content:
                    sections.append((current_header, content))
            current_header = parts[j + 1].strip()
            current_content = []
            continue
        if p.strip() and p != "## " and not (j >= 1 and parts[j - 1] == "## "):
            current_content.append(p)
    if current_header or current_content:
        content = "\n\n".join(current_content).strip()
        if current_header or content:
            sections.append((current_header, content))

    # Удаляем уже существующие секции «Содержание», чтобы не дублировать TOC
    sections = [
        (head, content)
        for head, content in sections
        if (head or "").strip().lower() not in {"содержание", "оглавление"}
    ]

    # Отделить «Источники» в конец
    sources_key = "источники"
    main_sections: List[Tuple[str, str]] = []
    sources_section: Optional[Tuple[str, str]] = None
    for head, content in sections:
        if head.lower() == sources_key:
            sources_section = (head, content)
        else:
            main_sections.append((head, content))

    # Сборка: заголовок, содержание, блоки, источники
    out: List[str] = []
    out.append(f"# {title}")
    out.append("")

    headings_for_toc: List[str] = []
    for head, _ in main_sections:
        if head:
            headings_for_toc.append(head)
    if sources_section:
        headings_for_toc.append(sources_section[0] or "Источники")

    if headings_for_toc:
        out.append("## Содержание")
        out.append("")
        for h in headings_for_toc:
            anchor = _heading_to_anchor(h)
            out.append(f"- [{h}](#{anchor})")
        out.append("")
        out.append("---")
        out.append("")

    for head, content in main_sections:
        if head:
            out.append(f"## {head}")
        if content:
            out.append("")
            out.append(content.strip())
        out.append("")

    if sources_section:
        head, content = sources_section
        out.append(f"## {head or 'Источники'}")
        if content:
            out.append("")
            out.append(content.strip())

    return "\n".join(out).strip()


def check_spelling_ru(text: str) -> Tuple[str, List[str]]:
    """
    Проверка орфографии (и по возможности пунктуации) через Yandex Speller API.
    Возвращает (исправленный_текст, список_сообщений_об_ошибках).
    """
    try:
        import requests
    except ImportError:
        return text, ["Установите requests для проверки орфографии."]
    text_to_check = text
    if len(text_to_check) > 10000:
        text_to_check = text_to_check[:10000]
    url = "https://speller.yandex.net/services/spellservice.json/checkText"
    messages: List[str] = []
    try:
        r = requests.post(url, data={"text": text_to_check}, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.warning("Yandex Speller недоступен: %s", e)
        return text, []
    if not data:
        return text, []
    result = text
    for err in reversed(data):
        pos = int(err.get("pos", 0))
        len_err = int(err.get("len", 0))
        s = err.get("s", [])
        word = err.get("word", "")
        if s and isinstance(s, list) and len(s) > 0:
            replacement = s[0]
            result = result[:pos] + replacement + result[pos + len_err:]
        msg = err.get("message", "") or "Ошибка"
        messages.append(f"«{word}» — {msg}")
    return result, messages


def add_markdown_links(text: str) -> str:
    """
    В .md: в разделе «Источники» добавляет HTML-якоря перед пунктами списка,
    чтобы ссылки [1], [2] в тексте вели на соответствующий источник.
    Содержание (если есть) уже должно содержать ссылки вида [Раздел](#якорь).
    """
    if not text or not text.strip():
        return text
    lines = text.split("\n")
    out: List[str] = []
    in_sources = False
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if re.match(r"^##\s+", stripped) and "источники" in stripped.lower():
            in_sources = True
            out.append(line)
            i += 1
            continue
        if in_sources:
            # Поддерживаем оба формата нумерации источников:
            # 1) "1. ..." / "1) ..."
            # 2) "[1] ..." (как сейчас возвращает PubMed-формат)
            m1 = re.match(r"^(\d+)[\.\)]\s+", stripped)
            m2 = re.match(r"^\[(\d+)\]\s+", stripped)
            if m1:
                num = int(m1.group(1))
                out.append("")
                out.append(f'<a id="источник-{num}"></a>')
                out.append(line)
                i += 1
                continue
            if m2:
                num = int(m2.group(1))
                out.append("")
                out.append(f'<a id="источник-{num}"></a>')
                out.append(line)
                i += 1
                continue
        if re.match(r"^##\s+", stripped):
            in_sources = False
        out.append(line)
        i += 1
    result = "\n".join(out)

    # Ссылки [1], [2] в тексте → на якоря в Источниках
    def replace_ref(m):
        num = m.group(1)
        return f"[{num}](#источник-{num})"
    result = re.sub(r"\[(\d+)\]", replace_ref, result)
    return result
