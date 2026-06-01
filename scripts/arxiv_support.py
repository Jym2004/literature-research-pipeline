#!/usr/bin/env python3
"""Shared arXiv access with polite API throttling, caching, and HTML fallback."""

from __future__ import annotations

import hashlib
import html as html_lib
import json
import os
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterator


API_URL = "https://export.arxiv.org/api/query"
SEARCH_URL = "https://arxiv.org/search/"
ABS_URL = "https://arxiv.org/abs/{identifier}"
USER_AGENT = "literature-research-pipeline/1.0 (+https://info.arxiv.org/help/api/)"
API_TIMEOUT_SECONDS = 30
HTML_TIMEOUT_SECONDS = 20
MIN_API_INTERVAL_SECONDS = 3.1
RATE_LIMIT_COOLDOWN_SECONDS = 600
TIMEOUT_COOLDOWN_SECONDS = 60
SEARCH_CACHE_SECONDS = 86400
ABS_CACHE_SECONDS = 604800
CACHE_ROOT = Path(tempfile.gettempdir()) / "literature-research-pipeline" / "arxiv"
STATE_FILE = CACHE_ROOT / "state.json"
LOCK_FILE = CACHE_ROOT / "api.lock"

ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"


class ArxivAccessError(RuntimeError):
    """Raised when the arXiv API or official HTML fallback cannot be read."""


class ArxivCooldownError(ArxivAccessError):
    """Raised while a recent API failure is cooling down."""


@dataclass
class Author:
    """Minimal author object compatible with the previous arxiv.py result shape."""

    name: str


@dataclass
class ArxivRecord:
    """Portable metadata record used by search and Zotero import scripts."""

    arxiv_id: str
    versioned_id: str
    title: str
    authors: list[str]
    published: str = ""
    updated: str = ""
    summary: str = ""
    primary_category: str = ""
    categories: list[str] | None = None
    doi: str = ""
    journal_ref: str = ""
    comment: str = ""
    metadata_source: str = ""

    @property
    def entry_id(self) -> str:
        return f"https://arxiv.org/abs/{self.versioned_id or self.arxiv_id}"

    @property
    def pdf_url(self) -> str:
        return f"https://arxiv.org/pdf/{self.versioned_id or self.arxiv_id}.pdf"

    def to_result_adapter(self) -> "ResultAdapter":
        """Return an object compatible with the importer builder."""
        return ResultAdapter(self)


class ResultAdapter:
    """Expose record fields using the small subset consumed by the importer."""

    def __init__(self, record: ArxivRecord) -> None:
        self.entry_id = record.entry_id
        self.title = record.title
        self.authors = [Author(name) for name in record.authors]
        self.published = _parse_datetime(record.published)
        self.updated = _parse_datetime(record.updated)
        self.summary = record.summary
        self.primary_category = record.primary_category
        self.categories = record.categories or []
        self.doi = record.doi
        self.journal_ref = record.journal_ref
        self.comment = record.comment
        self.metadata_source = record.metadata_source
        self.versioned_id = record.versioned_id


def normalize_identifier(value: str, keep_version: bool = False) -> str:
    """Normalize an arXiv identifier or URL."""
    identifier = value.strip()
    identifier = re.sub(
        r"^https?://(?:www\.)?arxiv\.org/(?:abs|pdf)/",
        "",
        identifier,
        flags=re.IGNORECASE,
    )
    identifier = re.sub(r"\.pdf$", "", identifier.rstrip("/"), flags=re.IGNORECASE)
    return identifier if keep_version else re.sub(r"v\d+$", "", identifier)


def search_records(query: str, limit: int) -> list[ArxivRecord]:
    """Search arXiv through the API, then official HTML if the API is unavailable."""
    normalized_query = normalize_query(query)
    key = f"search:{normalized_query}:{limit}"
    cached = _read_cache(key, SEARCH_CACHE_SECONDS)
    if cached:
        return [_record_from_dict(item) for item in cached]
    try:
        records = _api_records(query=normalized_query, limit=limit)
    except ArxivAccessError:
        records = _html_search_records(query, limit)
    _write_cache(key, [_record_to_dict(record) for record in records])
    return records


def records_for_identifiers(identifiers: list[str]) -> list[ArxivRecord]:
    """Fetch ordered metadata by ID through the API, then official abstract pages."""
    versioned = [normalize_identifier(identifier, keep_version=True) for identifier in identifiers]
    cached: dict[str, ArxivRecord] = {}
    missing: list[str] = []
    for identifier in versioned:
        payload = _read_cache(f"abs:{identifier}", ABS_CACHE_SECONDS)
        if payload:
            cached[normalize_identifier(identifier)] = _record_from_dict(payload)
        else:
            missing.append(identifier)

    if missing:
        try:
            fetched = _api_records(identifiers=missing, limit=len(missing))
        except ArxivAccessError:
            fetched = [_html_abs_record(identifier) for identifier in missing]
        for record in fetched:
            cached[record.arxiv_id] = record
            _write_cache(f"abs:{record.versioned_id or record.arxiv_id}", _record_to_dict(record))
            _write_cache(f"abs:{record.arxiv_id}", _record_to_dict(record))

    absent = [identifier for identifier in versioned if normalize_identifier(identifier) not in cached]
    if absent:
        raise ArxivAccessError(f"Could not fetch metadata for: {', '.join(absent)}")
    return [cached[normalize_identifier(identifier)] for identifier in versioned]


def normalize_query(query: str) -> str:
    """Wrap ordinary keywords in arXiv's explicit all-fields query syntax."""
    query = query.strip()
    if re.search(r"(^|\s)(all|ti|au|abs|co|jr|cat|id):", query, flags=re.IGNORECASE):
        return query
    return f"all:{query}"


def _api_records(
    query: str = "",
    identifiers: list[str] | None = None,
    limit: int = 10,
) -> list[ArxivRecord]:
    params = {
        "search_query": query,
        "id_list": ",".join(identifiers or []),
        "start": "0",
        "max_results": str(max(1, min(limit, 100))),
    }
    if query:
        params.update({"sortBy": "relevance", "sortOrder": "descending"})
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    body = _polite_api_get(url)
    return _parse_atom(body)


def _polite_api_get(url: str) -> bytes:
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    with _api_lock():
        state = _read_json(STATE_FILE, {})
        now = time.time()
        cooldown_until = float(state.get("cooldown_until", 0))
        if cooldown_until > now:
            raise ArxivCooldownError(
                f"arXiv API cooling down for {int(cooldown_until - now)} more seconds"
            )
        wait = MIN_API_INTERVAL_SECONDS - (now - float(state.get("last_request", 0)))
        if wait > 0:
            time.sleep(wait)
        state["last_request"] = time.time()
        _write_json(STATE_FILE, state)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=API_TIMEOUT_SECONDS) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                _set_cooldown(state, RATE_LIMIT_COOLDOWN_SECONDS)
                raise ArxivAccessError("arXiv API rate exceeded; using official HTML fallback") from exc
            raise ArxivAccessError(f"arXiv API HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            _set_cooldown(state, TIMEOUT_COOLDOWN_SECONDS)
            raise ArxivAccessError(f"arXiv API unavailable: {exc}") from exc


def _set_cooldown(state: dict[str, Any], seconds: int) -> None:
    state["cooldown_until"] = time.time() + seconds
    _write_json(STATE_FILE, state)


@contextmanager
def _api_lock() -> Iterator[None]:
    deadline = time.time() + 15
    while True:
        try:
            descriptor = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(descriptor)
            break
        except FileExistsError:
            try:
                if time.time() - LOCK_FILE.stat().st_mtime > 120:
                    LOCK_FILE.unlink()
                    continue
            except FileNotFoundError:
                continue
            if time.time() >= deadline:
                raise ArxivAccessError("Timed out waiting for the local arXiv API lock")
            time.sleep(0.2)
    try:
        yield
    finally:
        try:
            LOCK_FILE.unlink()
        except FileNotFoundError:
            pass


def _parse_atom(body: bytes) -> list[ArxivRecord]:
    root = ET.fromstring(body)
    records = []
    for entry in root.findall(f"{ATOM}entry"):
        versioned = normalize_identifier(_text(entry, f"{ATOM}id"), keep_version=True)
        categories = [item.attrib.get("term", "") for item in entry.findall(f"{ATOM}category")]
        primary = entry.find(f"{ARXIV}primary_category")
        records.append(
            ArxivRecord(
                arxiv_id=normalize_identifier(versioned),
                versioned_id=versioned,
                title=_clean(_text(entry, f"{ATOM}title")),
                authors=[
                    _clean(_text(author, f"{ATOM}name"))
                    for author in entry.findall(f"{ATOM}author")
                ],
                published=_text(entry, f"{ATOM}published"),
                updated=_text(entry, f"{ATOM}updated"),
                summary=_clean(_text(entry, f"{ATOM}summary")),
                primary_category=primary.attrib.get("term", "") if primary is not None else "",
                categories=[category for category in categories if category],
                doi=_text(entry, f"{ARXIV}doi"),
                journal_ref=_text(entry, f"{ARXIV}journal_ref"),
                comment=_text(entry, f"{ARXIV}comment"),
                metadata_source="api",
            )
        )
    return records


class _MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, list[str]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "meta":
            return
        values = dict(attrs)
        name = values.get("name") or values.get("property")
        content = values.get("content")
        if name and content:
            self.meta.setdefault(name, []).append(content)


def _html_abs_record(identifier: str) -> ArxivRecord:
    versioned = normalize_identifier(identifier, keep_version=True)
    key = f"abs:{versioned}"
    cached = _read_cache(key, ABS_CACHE_SECONDS)
    if cached:
        return _record_from_dict(cached)
    request = urllib.request.Request(
        ABS_URL.format(identifier=urllib.parse.quote(versioned)),
        headers={"User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=HTML_TIMEOUT_SECONDS) as response:
            html = response.read().decode("utf-8", errors="replace")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise ArxivAccessError(f"Could not read arXiv abstract page for {versioned}: {exc}") from exc
    parser = _MetaParser()
    parser.feed(html)
    meta = parser.meta
    title = _first(meta, "citation_title")
    if not title:
        raise ArxivAccessError(f"Missing metadata on arXiv abstract page for {versioned}")
    discovered = _first(meta, "citation_arxiv_id") or versioned
    record = ArxivRecord(
        arxiv_id=normalize_identifier(discovered),
        versioned_id=normalize_identifier(discovered, keep_version=True),
        title=_clean(title),
        authors=[_clean(author) for author in meta.get("citation_author", [])],
        published=_first(meta, "citation_date"),
        summary=_clean(_first(meta, "citation_abstract") or _first(meta, "description")),
        doi=_first(meta, "citation_doi"),
        metadata_source="html-abs-fallback",
    )
    _write_cache(key, _record_to_dict(record))
    return record


def _html_search_records(query: str, limit: int) -> list[ArxivRecord]:
    params = {
        "query": query,
        "searchtype": "all",
        "abstracts": "show",
        "order": "-announced_date_first",
        "size": "50",
    }
    request = urllib.request.Request(
        f"{SEARCH_URL}?{urllib.parse.urlencode(params)}",
        headers={"User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=HTML_TIMEOUT_SECONDS) as response:
            html = response.read().decode("utf-8", errors="replace")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise ArxivAccessError(f"Could not read arXiv HTML search results: {exc}") from exc
    records = []
    for block in re.findall(r'<li class="arxiv-result">(.*?)</li>', html, flags=re.DOTALL):
        identifier_match = re.search(r'href="https?://arxiv\.org/abs/([^"?#]+)"', block)
        title_match = re.search(r'<p class="title is-5 mathjax">(.*?)</p>', block, flags=re.DOTALL)
        if not identifier_match or not title_match:
            continue
        base_identifier = normalize_identifier(identifier_match.group(1))
        version_match = re.search(
            rf'id="{re.escape(base_identifier)}(v\d+)-abstract-full"',
            block,
        )
        versioned_identifier = (
            f"{base_identifier}{version_match.group(1)}" if version_match else base_identifier
        )
        author_block = re.search(r'<p class="authors">(.*?)</p>', block, flags=re.DOTALL)
        abstract_match = re.search(
            r'<span class="abstract-full[^"]*"[^>]*>(.*?)<a class="is-size-7"',
            block,
            flags=re.DOTALL,
        )
        submitted = re.search(
            r'>Submitted</span>\s*(\d{1,2}\s+\w+,\s+\d{4})',
            block,
        )
        categories = [
            _strip_tags(category)
            for category in re.findall(r'<span class="tag[^"]*"[^>]*>(.*?)</span>', block, flags=re.DOTALL)
        ]
        records.append(
            ArxivRecord(
                arxiv_id=base_identifier,
                versioned_id=versioned_identifier,
                title=_strip_tags(title_match.group(1)),
                authors=[
                    _strip_tags(author)
                    for author in re.findall(
                        r'<a href="/search/\?searchtype=author[^"]*">(.*?)</a>',
                        author_block.group(1) if author_block else "",
                        flags=re.DOTALL,
                    )
                ],
                published=_submitted_iso(submitted.group(1)) if submitted else "",
                summary=_strip_tags(abstract_match.group(1)) if abstract_match else "",
                primary_category=categories[0] if categories else "",
                categories=categories,
                metadata_source="html-search-fallback",
            )
        )
        if len(records) >= limit:
            break
    return records


def _cache_path(key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return CACHE_ROOT / f"{digest}.json"


def _read_cache(key: str, max_age: int) -> Any | None:
    path = _cache_path(key)
    try:
        if time.time() - path.stat().st_mtime > max_age:
            return None
        return _read_json(path, None)
    except FileNotFoundError:
        return None


def _write_cache(key: str, value: Any) -> None:
    _write_json(_cache_path(key), value)


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _record_to_dict(record: ArxivRecord) -> dict[str, Any]:
    return {
        "arxiv_id": record.arxiv_id,
        "versioned_id": record.versioned_id,
        "title": record.title,
        "authors": record.authors,
        "published": record.published,
        "updated": record.updated,
        "summary": record.summary,
        "primary_category": record.primary_category,
        "categories": record.categories or [],
        "doi": record.doi,
        "journal_ref": record.journal_ref,
        "comment": record.comment,
        "metadata_source": record.metadata_source,
    }


def _record_from_dict(payload: dict[str, Any]) -> ArxivRecord:
    return ArxivRecord(**payload)


def _text(element: ET.Element, path: str) -> str:
    child = element.find(path)
    return child.text.strip() if child is not None and child.text else ""


def _first(values: dict[str, list[str]], name: str) -> str:
    items = values.get(name, [])
    return items[0] if items else ""


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _strip_tags(value: str) -> str:
    return _clean(html_lib.unescape(re.sub(r"<[^>]+>", "", value)))


def _submitted_iso(value: str) -> str:
    try:
        return datetime.strptime(value, "%d %B, %Y").date().isoformat()
    except ValueError:
        return value


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y/%m/%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return None
