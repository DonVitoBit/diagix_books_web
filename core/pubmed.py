"""
Утилиты для поиска свежих статей на PubMed через NCBI E-utilities.
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional

import requests

logger = logging.getLogger(__name__)

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_API_KEY = "889ea21c0e08281b51b7bd188a0c238c6908"
TOOL_NAME = "med_book_app"
CONTACT_EMAIL = "med_book@app.local"


def _build_common_params() -> Dict[str, str]:
    params: Dict[str, str] = {
        "tool": TOOL_NAME,
        "email": CONTACT_EMAIL,
    }
    if PUBMED_API_KEY:
        params["api_key"] = PUBMED_API_KEY
    return params


def _sanitize_phrase(phrase: str) -> str:
    """Убирает символы, недопустимые в поисковой фразе PubMed в кавычках."""
    return re.sub(r'[\[\]()"]', " ", phrase.strip()).strip()


def search_pubmed_ids(
    query: str,
    max_results: int = 5,
    sort: str = "relevance",
    theme_in_title_abstract: Optional[str] = None,
) -> List[str]:
    """Ищет статьи в PubMed и возвращает список PMID (строки).
    sort: 'relevance' — по релевантности (лучше подбор), 'pub date' — по дате выхода.
    theme_in_title_abstract: если задано, только статьи, где эта фраза есть в заголовке или аннотации [tiab].
    При 0 результатах с точной фразой — повторяет поиск с ключевым словом (первое слово фразы)."""
    if not query or not query.strip():
        return []
    term = query.strip()
    theme_phrase = _sanitize_phrase(theme_in_title_abstract) if theme_in_title_abstract else ""
    params = {
        "db": "pubmed",
        "sort": sort if sort in ("relevance", "pub date") else "relevance",
        "retmode": "json",
        "retmax": str(max_results),
    }
    params.update(_build_common_params())

    def _do_search(search_term: str) -> List[str]:
        p = {**params, "term": search_term}
        try:
            resp = requests.get(f"{EUTILS_BASE}/esearch.fcgi", params=p, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return [str(i) for i in data.get("esearchresult", {}).get("idlist", []) if i]
        except Exception as e:
            logger.warning(f"Не удалось выполнить поиск PubMed: {e}")
            return []

    if theme_phrase:
        # Сначала с точной фразой в [tiab]
        term_with_theme = f'"{theme_phrase}"[tiab] AND ({term})'
        ids = _do_search(term_with_theme)
        if not ids:
            # Fallback: ключевое слово (первое) в [tiab] — шире, но всё ещё по теме
            first_word = theme_phrase.split()[0] if theme_phrase.split() else ""
            if len(first_word) > 2:
                term_fallback = f'{first_word}[tiab] AND ({term})'
                ids = _do_search(term_fallback)
                if ids:
                    logger.info(f"PubMed: fallback на «{first_word}[tiab]» для «{query[:50]}…»")
        return ids
    return _do_search(term)


def fetch_pubmed_entries(
    query: str,
    max_results: int = 5,
    sort: str = "relevance",
    theme_in_title_abstract: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Возвращает список статей PubMed по запросу в виде словарей.
    Каждый элемент: {"title", "journal", "year", "pmid"}.
    sort: 'relevance' — по релевантности, 'pub date' — по дате.
    theme_in_title_abstract: если задано, только статьи с этой фразой в заголовке/аннотации.
    """
    ids = search_pubmed_ids(
        query, max_results=max_results, sort=sort,
        theme_in_title_abstract=theme_in_title_abstract,
    )
    if not ids:
        return []

    params = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "json",
    }
    params.update(_build_common_params())

    try:
        resp = requests.get(f"{EUTILS_BASE}/esummary.fcgi", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning(f"Не удалось получить сводки PubMed: {e}")
        return []

    result = data.get("result", {})
    entries: List[Dict[str, Any]] = []

    for pmid in ids:
        item = result.get(str(pmid))
        if not item:
            continue
        title = (item.get("title") or "").strip()
        if not title:
            continue
        journal = (item.get("fulljournalname") or item.get("source") or "").strip()
        pubdate = item.get("pubdate") or ""
        year = pubdate.split(" ")[0].strip() if pubdate else ""
        entries.append({"title": title, "journal": journal, "year": year, "pmid": str(pmid)})

    return entries


def fetch_abstracts_for_pmids(
    pmids: List[str],
    batch_size: int = 20,
    timeout: int = 15,
) -> Dict[str, str]:
    """
    Для каждого PMID получает аннотацию статьи через efetch (XML).
    Возвращает словарь pmid -> текст аннотации (или пустая строка, если аннотации нет).
    """
    if not pmids:
        return {}
    pmids = [str(p).strip() for p in pmids if str(p).strip()]
    out: Dict[str, str] = {p: "" for p in pmids}
    for i in range(0, len(pmids), batch_size):
        batch = pmids[i : i + batch_size]
        params = {
            "db": "pubmed",
            "id": ",".join(batch),
            "retmode": "xml",
        }
        params.update(_build_common_params())
        try:
            resp = requests.get(f"{EUTILS_BASE}/efetch.fcgi", params=params, timeout=timeout)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
        except Exception as e:
            logger.warning(f"PubMed efetch (аннотации) для batch: {e}")
            continue
        for article in root.findall(".//PubmedArticle"):
            pmid_el = article.find(".//PMID")
            pmid = pmid_el.text.strip() if pmid_el is not None and pmid_el.text else None
            if not pmid:
                continue
            abstract_parts = []
            for ab in article.findall(".//Abstract/AbstractText"):
                if ab.text:
                    abstract_parts.append(ab.text.strip())
                if ab.tail and ab.tail.strip():
                    abstract_parts.append(ab.tail.strip())
            out[pmid] = " ".join(abstract_parts).strip() if abstract_parts else ""
    return out


def _title_words(text: str) -> set:
    """Разбивает текст на слова (для проверки по границам слов)."""
    return set(re.findall(r"[a-zа-яё0-9]+", text.lower()))


def score_entry_by_theme(entry: Dict[str, Any], theme_phrase: str) -> int:
    """Возвращает число слов темы, встречающихся в заголовке статьи (для сортировки по релевантности)."""
    if not theme_phrase or not entry:
        return 0
    title_words = _title_words(entry.get("title") or "")
    theme_words = _title_words(_sanitize_phrase(theme_phrase))
    return sum(1 for w in theme_words if w in title_words)


def filter_entries_by_title_relevance(
    entries: List[Dict[str, Any]],
    theme_phrase: str,
    min_words_in_title: int = 2,
) -> List[Dict[str, Any]]:
    """
    Оставляет только статьи, в заголовке которых встречается минимум min_words_in_title
    слов из theme_phrase как отдельные слова (по границам слов, без подстрок типа 'hiv' в 'shiv').
    Сортирует по убыванию релевантности (больше совпадений — выше).
    """
    if not theme_phrase or not entries:
        return entries
    theme_words = _title_words(_sanitize_phrase(theme_phrase))
    if not theme_words:
        return entries
    if len(theme_words) < 2:
        min_words_in_title = 1
    scored: List[tuple] = []
    for e in entries:
        title_words = _title_words(e.get("title") or "")
        matches = sum(1 for w in theme_words if w in title_words)
        if matches >= min_words_in_title:
            scored.append((matches, e))
    if not scored:
        return entries
    scored.sort(key=lambda x: -x[0])  # больше совпадений — выше
    return [e for _, e in scored]


def fetch_pubmed_summaries(query: str, max_results: int = 5) -> str:
    """
    Возвращает краткое текстовое описание нескольких свежих статей PubMed по запросу.

    Формат: список пунктов «Название (Журнал, Год, PMID: ...)».
    Этот текст вставляется в промпт как вспомогательный контекст.
    """
    entries = fetch_pubmed_entries(query, max_results=max_results)
    if not entries:
        return ""

    lines = []
    for e in entries:
        parts = [e["title"]]
        meta = ", ".join(p for p in [e["journal"], e["year"]] if p)
        if meta:
            parts.append(f"({meta})")
        parts.append(f"PMID: {e['pmid']}")
        lines.append("- " + " ".join(parts))
    return "\n".join(lines)

