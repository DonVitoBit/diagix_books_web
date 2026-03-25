"""
Экспорт текста в PDF с книжной вёрсткой.

Важно: рендеринг `fitz.Story` в вашей версии PyMuPDF (1.27.1)
требует FzDevice, поэтому используем стабильный ручной рендеринг через TextWriter.
"""

import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# Поля страницы (как в книге)
MARGIN_LEFT = 50
MARGIN_RIGHT = 50
MARGIN_TOP = 60
MARGIN_BOTTOM = 60

FONT_SIZE = 11
LINE_HEIGHT = 1.2

# Максимальная ширина изображения на странице (в пунктах)
MAX_IMAGE_WIDTH = 400
IMAGE_TOP_MARGIN = 20


def _find_figure_refs_in_block(block: str) -> List[int]:
    """Находит номера рисунков в блоке текста (рис. 1, рисунок 1, на рисунке 1, Рис. 1. Схема...)."""
    refs: List[int] = []
    patterns = [
        r"(?:на\s+)?рис(?:унке|унок|\.)?\s*(\d+)",
        r"рис\s*\.?\s*(\d+)",
        r"рисунок\s*(\d+)",
    ]
    for pat in patterns:
        for m in re.finditer(pat, block, re.IGNORECASE):
            try:
                n = int(m.group(1))
                if n > 0 and n not in refs:
                    refs.append(n)
            except (ValueError, IndexError):
                continue
    return sorted(refs)


_FIG_MD_RE = re.compile(
    r"!\[(?P<alt>[^\]]*)\]\(\s*(?P<kind>file:|data:image/)[^)]+\)",
    re.IGNORECASE,
)

_FIG_MD_FILE_RE = re.compile(
    r"!\[(?P<alt>[^\]]*)\]\(\s*file:(?P<path>[^)]+)\)",
    re.IGNORECASE,
)
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$")


def _split_table_row(line: str) -> List[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _normalize_markdown_tables(text: str) -> str:
    """Преобразует markdown-таблицы в читаемый plain-text для PDF."""
    lines = text.splitlines()
    out: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if "|" in line and i + 1 < len(lines) and _TABLE_SEP_RE.match(lines[i + 1].strip() or ""):
            header = _split_table_row(line)
            rows: List[List[str]] = []
            j = i + 2
            while j < len(lines):
                row_line = lines[j].strip()
                if not row_line or "|" not in row_line:
                    break
                rows.append(_split_table_row(row_line))
                j += 1

            if header:
                out.append("Таблица:")
                out.append(" | ".join(header))
                for r in rows:
                    out.append(" | ".join(r))
                out.append("")
            i = j
            continue

        out.append(line)
        i += 1
    return "\n".join(out)


def _clean_markdown_for_pdf(text: str) -> str:
    """Убирает `##`, `#`, `**` и markdown-ссылки вида [текст](#якорь)."""
    if not text:
        return ""

    # Нормализация markdown-таблиц до обычного текста
    text = _normalize_markdown_tables(text)

    # Удаляем маркеры иллюстраций, которые не должны попадать в итог
    text = re.sub(r"\[ILLUSTRATION_\d+\]", "", text)
    # Уплотняем пустые строки
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Заголовки Markdown -> просто текст заголовка
    text = re.sub(r"^#{1,3}\s+", "", text, flags=re.MULTILINE)

    # Горизонтальная линия
    text = re.sub(r"^\s*---\s*$", "", text, flags=re.MULTILINE)

    # Markdown ссылки [text](#anchor) -> text
    text = re.sub(r"\[([^\]]+)\]\(\s*#[^)]+\)", r"\1", text)

    # Выкидываем жир/курсив маркеры
    text = text.replace("**", "")
    text = text.replace("*", "")

    # Markdown картинка оставим только как след: заменяем на alt, чтобы не было синтаксиса
    # Но alt может быть длинным — это лучше, чем показывать `![...](file:...)`.
    def _repl_img(m: re.Match) -> str:
        alt = (m.group("alt") or "").strip()
        return alt

    text = _FIG_MD_FILE_RE.sub(_repl_img, text)
    text = _FIG_MD_RE.sub(_repl_img, text)

    # Списки: - item -> • item
    text = re.sub(r"^\s*-\s+", "• ", text, flags=re.MULTILINE)

    return text.strip()


def text_to_pdf(text: str) -> Tuple[Optional[bytes], Optional[str]]:
    """Создаёт PDF из текста с книжной вёрсткой (без вставки изображений)."""
    if not text or not text.strip():
        return None, "Нет текста для экспорта"

    try:
        doc = fitz.open()
        page_rect = fitz.Rect(0, 0, 595, 842)  # A4
        content_rect = fitz.Rect(
            MARGIN_LEFT,
            MARGIN_TOP,
            page_rect.width - MARGIN_RIGHT,
            page_rect.height - MARGIN_BOTTOM,
        )

        blocks = [b.strip() for b in _clean_markdown_for_pdf(text).split("\n\n") if b.strip()]
        if not blocks:
            return None, "Нет блоков для экспорта"

        page = doc.new_page(width=page_rect.width, height=page_rect.height)
        font = fitz.Font("tiro")  # Times-Roman (под кириллицу)
        y_pos = content_rect.y0

        for block in blocks:
            remaining = block
            while remaining:
                tw = fitz.TextWriter(page_rect)
                block_rect = fitz.Rect(content_rect.x0, y_pos, content_rect.x1, content_rect.y1)
                overflow = tw.fill_textbox(
                    block_rect,
                    remaining,
                    font=font,
                    fontsize=FONT_SIZE,
                    align=fitz.TEXT_ALIGN_LEFT,
                )
                tw.write_text(page)

                if overflow:
                    remaining = "\n".join(t[0] for t in overflow)
                    page = doc.new_page(width=page_rect.width, height=page_rect.height)
                    y_pos = content_rect.y0
                else:
                    remaining = ""
                    y_pos = tw.last_point.y + FONT_SIZE * LINE_HEIGHT * 0.5
                    if y_pos > content_rect.y1 - FONT_SIZE * 2:
                        page = doc.new_page(width=page_rect.width, height=page_rect.height)
                        y_pos = content_rect.y0

        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes, None

    except Exception as e:
        logger.error(f"Ошибка создания PDF: {e}")
        return None, str(e)[:300]


def text_to_pdf_with_images(
    text: str,
    image_paths: List[str],
) -> Tuple[Optional[bytes], Optional[str]]:
    """Создаёт PDF из текста и вставляет изображения после блоков со ссылками на рисунки.

    Текст может содержать markdown-изображения вида `![alt](file:/path/to.png)`.
    Мы убираем этот синтаксис из основного текста и вставляем картинки отдельно,
    чтобы в PDF не отображались `![...](file:...)`.
    """
    if not text or not text.strip():
        return None, "Нет текста для экспорта"

    image_paths = [p for p in (image_paths or []) if p and Path(p).exists()]
    if not image_paths:
        return text_to_pdf(text)

    try:
        # Сохраняем подписи к изображениям по порядку в тексте
        captions: List[str] = []
        for m in _FIG_MD_FILE_RE.finditer(text):
            alt = (m.group("alt") or "").strip()
            captions.append(alt)

        # Очищаем markdown синтаксис и заголовки/жир и т.п.
        # Но подписи к картинкам там превращаются в plain-text alt.
        # Для вставки изображений оставим figure-label ("Рис. N...") в тексте, а markdown-картинки — нет.
        cleaned_text = text
        cleaned_text = re.sub(r"!\[[^\]]*\]\(\s*file:[^)]+\)", "", cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r"!\[[^\]]*\]\(\s*data:image/[^)]+\)", "", cleaned_text, flags=re.IGNORECASE)
        cleaned_text = _clean_markdown_for_pdf(cleaned_text)

        doc = fitz.open()
        page_rect = fitz.Rect(0, 0, 595, 842)
        content_rect = fitz.Rect(
            MARGIN_LEFT,
            MARGIN_TOP,
            page_rect.width - MARGIN_RIGHT,
            page_rect.height - MARGIN_BOTTOM,
        )

        blocks = [b.strip() for b in cleaned_text.split("\n\n") if b.strip()]
        if not blocks:
            return None, "Нет блоков для экспорта"

        page = doc.new_page(width=page_rect.width, height=page_rect.height)
        font = fitz.Font("tiro")
        y_pos = content_rect.y0
        inserted_figures = set()

        for block in blocks:
            remaining = block
            while remaining:
                tw = fitz.TextWriter(page_rect)
                block_rect = fitz.Rect(content_rect.x0, y_pos, content_rect.x1, content_rect.y1)
                overflow = tw.fill_textbox(
                    block_rect,
                    remaining,
                    font=font,
                    fontsize=FONT_SIZE,
                    align=fitz.TEXT_ALIGN_LEFT,
                )
                tw.write_text(page)

                if overflow:
                    remaining = "\n".join(t[0] for t in overflow)
                    page = doc.new_page(width=page_rect.width, height=page_rect.height)
                    y_pos = content_rect.y0
                else:
                    remaining = ""
                    y_pos = tw.last_point.y + FONT_SIZE * LINE_HEIGHT * 0.5

                    # Вставляем изображения после упоминаний "Рис. N" в этом блоке
                    for fig_num in _find_figure_refs_in_block(block):
                        if fig_num in inserted_figures:
                            continue
                        idx = fig_num - 1
                        if idx < 0 or idx >= len(image_paths):
                            continue
                        img_path = image_paths[idx]
                        try:
                            img_doc = fitz.open(img_path)
                            rect = img_doc[0].rect
                            w_img, h_img = rect.width, rect.height
                            img_doc.close()

                            scale = min(1.0, MAX_IMAGE_WIDTH / max(w_img, 1))
                            w = w_img * scale
                            h = h_img * scale

                            if y_pos + h + IMAGE_TOP_MARGIN > content_rect.y1:
                                page = doc.new_page(width=page_rect.width, height=page_rect.height)
                                y_pos = content_rect.y0

                            y_pos += IMAGE_TOP_MARGIN
                            img_rect = fitz.Rect(content_rect.x0, y_pos, content_rect.x0 + w, y_pos + h)
                            page.insert_image(img_rect, filename=img_path)
                            y_pos += h + FONT_SIZE * LINE_HEIGHT

                            # Подпись к рисунку (по `alt` из markdown, если есть)
                            cap = captions[idx] if idx < len(captions) else ""
                            cap = (cap or "").strip()
                            if cap:
                                # Центрируем подпись
                                cap_font_size = 9
                                # Оставляем немного места до подписи
                                if y_pos > content_rect.y1 - cap_font_size * 2:
                                    page = doc.new_page(width=page_rect.width, height=page_rect.height)
                                    y_pos = content_rect.y0
                                page.insert_text(
                                    fitz.Point((content_rect.x0 + content_rect.x1) / 2, y_pos + cap_font_size),
                                    cap,
                                    fontname="tiro",
                                    fontsize=cap_font_size,
                                    color=(0, 0, 0),
                                    render_mode=0,
                                    align=fitz.TEXT_ALIGN_CENTER,
                                )
                                y_pos += cap_font_size * 1.2

                            inserted_figures.add(fig_num)
                            logger.info(f"Вставлено изображение рис. {fig_num} в PDF")
                        except Exception as img_e:
                            logger.warning(f"Не удалось вставить изображение {img_path}: {img_e}")

                    if y_pos > content_rect.y1 - FONT_SIZE * 2:
                        page = doc.new_page(width=page_rect.width, height=page_rect.height)
                        y_pos = content_rect.y0

        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes, None

    except Exception as e:
        logger.error(f"Ошибка создания PDF с изображениями: {e}")
        return None, str(e)[:300]

