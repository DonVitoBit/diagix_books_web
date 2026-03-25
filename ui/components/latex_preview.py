"""
Компонент предпросмотра LaTeX в Streamlit
"""

import json
import streamlit as st
import streamlit.components.v1 as components


def render_latex_preview(latex: str, height: int = 200, key: str = None) -> None:
    """
    Отображает предпросмотр LaTeX с помощью KaTeX.

    Args:
        latex: LaTeX-код для отображения
        height: Высота контейнера в пикселях
        key: Уникальный ключ для Streamlit
    """
    if not latex or not latex.strip():
        st.caption("LaTeX не сгенерирован")
        return

    # Разбиваем на блоки по двойному переносу и оборачиваем каждый в \[ \]
    blocks = [b.strip() for b in latex.strip().split("\n\n") if b.strip()]
    wrapped_blocks = []
    for block in blocks:
        if not block.startswith(("$$", "\\[", "\\begin")):
            block = f"\\[{block}\\]"
        wrapped_blocks.append(block)

    # Используем auto-render для контента с несколькими блоками
    content_html = "<br>".join(wrapped_blocks)

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
    <style>
        .latex-preview {{
            padding: 16px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            min-height: {height}px;
            overflow-x: auto;
            font-size: 1.05em;
        }}
    </style>
</head>
<body>
    <div class="latex-preview" id="latex-container"></div>
    <script>
        (function() {{
            var container = document.getElementById("latex-container");
            var content = {json.dumps(content_html)};
            container.innerHTML = content;
            try {{
                renderMathInElement(container, {{
                    delimiters: [
                        {{left: "$$", right: "$$", display: true}},
                        {{left: "\\\\[", right: "\\\\]", display: true}},
                        {{left: "$", right: "$", display: false}}
                    ],
                    throwOnError: false
                }});
            }} catch (e) {{
                container.innerHTML = "<pre style='color:#666;font-size:12px'>" + 
                    content.replace(/</g, "&lt;").replace(/>/g, "&gt;") + "</pre>";
            }}
        }})();
    </script>
</body>
</html>
"""

    components.html(html_content, height=height + 40, scrolling=True)
