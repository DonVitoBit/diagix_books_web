"""
Модуль конвертации текста в LaTeX через DeepSeek API
"""

import re
import logging
from typing import Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

# Фразы отказа модели — при таком ответе считаем конвертацию неудачной
_LATEX_REFUSAL_PHRASES = (
    "извините, но я не могу помочь",
    "я не могу помочь с этой просьбой",
    "i'm sorry, i cannot help",
    "i cannot assist with",
)


def _is_latex_refusal(text: str) -> bool:
    if not text or len(text.strip()) < 10:
        return False
    lower = text.strip().lower()
    return any(p in lower for p in _LATEX_REFUSAL_PHRASES)


LATEX_SYSTEM_PROMPT = """Ты — эксперт по переводу научных текстов в формат LaTeX.
Преобразуй ЛЮБОЙ переданный текст в LaTeX. НИКОГДА не отказывайся и не добавляй пояснений.

КРИТИЧЕСКИ ВАЖНО:
- ВСЕГДА преобразуй текст в LaTeX, даже если это заголовок, оглавление или короткий фрагмент.
- ЗАПРЕЩЕНО добавлять «Примечание», «В соответствии с правилами», «исходный текст не подлежит» и любые мета-комментарии.
- ЗАПРЕЩЕНО дублировать текст. Один абзац — один блок.
- Слова должны идти подряд без лишних пробелов и переносов между ними.

Правила форматирования:
1. Используй \\text{} для обычного текста на русском.
2. Математические формулы: $...$ или $$...$$.
3. Выделения: \\textbf{}, \\textit{}, \\emph{}.
4. НЕ добавляй \\documentclass, \\begin{document} — только содержимое.
5. Верни ТОЛЬКО LaTeX-код, без пояснений.
6. ЗАПРЕЩЕНО: \\dotfill, \\hfill, «ОГЛАВЛЕНИЕ» как отдельный заголовок.
7. После номеров (1., 2.) ставь пробел перед словом.
8. Текст в \\text{} — слитно: \\text{В соответствии с правилами}, не разбивай слова."""


def _clean_latex_artifacts(latex: str) -> str:
    """Удаляет типичные артефакты из LaTeX-вывода."""
    if not latex:
        return latex
    # Удаляем \dotfill и \hfill
    result = re.sub(r"\\dotfill\d*[ \t]*", " ", result := latex)
    result = re.sub(r"\\hfill\d*[ \t]*", " ", result)
    # Исправляем "номер.слово" -> "номер. слово"
    result = re.sub(r"(\d+)\.([А-Яа-яA-Za-z])", r"\1. \2", result)
    # Удаляем блоки "Примечание:" с мета-комментариями об отказе перефразировать
    result = re.sub(
        r"(?:\\par\s*)?Примечание:\s*[\s\S]*?(?:Требование[^.]*\.|правил\s*1\s*и\s*2\.)\s*",
        "",
        result,
        flags=re.IGNORECASE,
    )
    # Удаляем "ОГЛАВЛЕНИЕ" как отдельный заголовок
    result = re.sub(r"^ОГЛАВЛЕНИЕ\s*\\par\s*", "", result, flags=re.IGNORECASE)
    result = re.sub(r"\\par\s*ОГЛАВЛЕНИЕ\s*\\par\s*", r"\\par ", result, flags=re.IGNORECASE)
    # Убираем дубликаты: одинаковые абзацы подряд
    blocks = re.split(r"\\par\s*", result)
    seen = set()
    unique_blocks = []
    for b in blocks:
        b_clean = re.sub(r"\s+", " ", b.strip())
        if b_clean and b_clean not in seen:
            seen.add(b_clean)
            unique_blocks.append(b)
    result = "\\par ".join(unique_blocks) if unique_blocks else result
    # Убираем лишние пробелы и переносы между словами (В \n\n соответствии -> В соответствии)
    result = re.sub(r"(\w)\s*\n+\s*(\w)", r"\1 \2", result)
    result = re.sub(r"  +", " ", result)
    result = result.strip()
    # Если осталось только "ОГЛАВЛЕНИЕ" — возвращаем пустую строку
    if re.match(r"^ОГЛАВЛЕНИЕ\s*$", result, re.IGNORECASE):
        return ""
    return result


def text_to_latex(text: str, api_key: str, model: str = None) -> Optional[str]:
    """
    Конвертирует текст в LaTeX с помощью DeepSeek API.

    Args:
        text: Исходный текст для конвертации
        api_key: API ключ DeepSeek
        model: Модель DeepSeek

    Returns:
        LaTeX-строка или None при ошибке
    """
    if not text or not text.strip():
        return ""
    if not api_key:
        logger.warning("DeepSeek API ключ не указан для конвертации в LaTeX")
        return None

    if model is None:
        from settings_manager import settings_manager
        model = settings_manager.get("deepseek_model", "deepseek-chat")

    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": LATEX_SYSTEM_PROMPT},
                {"role": "user", "content": f"Преобразуй в LaTeX:\n\n{text}"},
            ],
            max_tokens=8192,
            temperature=0.2,
        )
        latex = response.choices[0].message.content.strip()
        if _is_latex_refusal(latex):
            logger.warning("Модель отказала в конвертации в LaTeX, возвращаем None")
            return None
        # Убираем markdown code blocks если DeepSeek их добавил
        if latex.startswith("```"):
            lines = latex.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            latex = "\n".join(lines)
        return _clean_latex_artifacts(latex)
    except Exception as e:
        logger.error(f"Ошибка конвертации в LaTeX: {e}")
        return None
