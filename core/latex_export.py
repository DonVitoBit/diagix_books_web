"""
Экспорт LaTeX в файлы .tex и .pdf
"""

import logging
import os
import shutil
import subprocess
import tempfile
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

LATEX_PREAMBLE = r"""
\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T2A]{fontenc}
\usepackage[russian]{babel}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{parskip}
\setlength{\parindent}{0pt}
\begin{document}
"""

LATEX_END = r"""
\end{document}
"""


def build_full_latex_document(content: str) -> str:
    """Собирает полный LaTeX-документ с преамбулой."""
    if not content or not content.strip():
        return LATEX_PREAMBLE.strip() + "\n\n" + LATEX_END.strip()
    return LATEX_PREAMBLE + content.strip() + "\n" + LATEX_END


def latex_to_pdf(latex_content: str) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Компилирует LaTeX в PDF.

    Returns:
        (pdf_bytes, error_message): PDF как bytes или (None, сообщение об ошибке)
    """
    full_tex = build_full_latex_document(latex_content)
    tmpdir = None
    try:
        tmpdir = tempfile.mkdtemp()
        tex_path = os.path.join(tmpdir, "document.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(full_tex)

        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "document.tex"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            timeout=60,
        )

        pdf_path = os.path.join(tmpdir, "document.pdf")
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                return f.read(), None
        else:
            err = result.stderr or result.stdout or "pdflatex не создал PDF"
            return None, err[:500]
    except FileNotFoundError:
        return None, "pdflatex не найден. Установите TeX Live (https://tug.org/texlive/) или MacTeX."
    except subprocess.TimeoutExpired:
        return None, "Превышено время компиляции LaTeX."
    except Exception as e:
        return None, str(e)[:500]
    finally:
        if tmpdir and os.path.exists(tmpdir):
            try:
                shutil.rmtree(tmpdir)
            except Exception:
                pass


def is_pdflatex_available() -> bool:
    """Проверяет, установлен ли pdflatex."""
    try:
        subprocess.run(["pdflatex", "--version"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
