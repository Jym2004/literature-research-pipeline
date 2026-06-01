#!/usr/bin/env python3
"""Import arXiv papers into Zotero through the local Connector API."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any


CONNECTOR_URL = "http://127.0.0.1:23119/connector"
JSON_TIMEOUT_SECONDS = 15
PDF_TIMEOUT_SECONDS = 60
USER_AGENT = "literature-research-pipeline/1.0 (+https://arxiv.org)"


def normalize_identifier(value: str) -> str:
    """Normalize an arXiv URL or identifier to its unversioned identifier."""
    identifier = value.strip()
    identifier = re.sub(
        r"^https?://(?:www\.)?arxiv\.org/(?:abs|pdf)/",
        "",
        identifier,
        flags=re.IGNORECASE,
    )
    identifier = identifier.rstrip("/")
    identifier = re.sub(r"\.pdf$", "", identifier, flags=re.IGNORECASE)
    return re.sub(r"v\d+$", "", identifier)


def json_request(endpoint: str, payload: dict[str, Any] | None = None) -> tuple[int, Any]:
    """Send one JSON request to the Zotero Connector API."""
    request = urllib.request.Request(
        f"{CONNECTOR_URL}/{endpoint}",
        data=json.dumps(payload or {}, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Zotero-Connector-API-Version": "3",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=JSON_TIMEOUT_SECONDS) as response:
            text = response.read().decode("utf-8")
            return response.status, json.loads(text) if text else None
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(text) if text else None
        except json.JSONDecodeError:
            return exc.code, {"error": text}
    except (urllib.error.URLError, TimeoutError):
        return 0, None


def fetch_results(identifiers: list[str]) -> list[Any]:
    """Load arXiv metadata and preserve caller order."""
    import arxiv  # type: ignore[import-not-found]

    normalized = [normalize_identifier(identifier) for identifier in identifiers]
    results = list(arxiv.Client().results(arxiv.Search(id_list=normalized)))
    indexed = {
        normalize_identifier(getattr(result, "entry_id", "")): result
        for result in results
    }
    missing = [identifier for identifier in normalized if identifier not in indexed]
    if missing:
        raise ValueError(f"Could not fetch metadata for: {', '.join(missing)}")
    return [indexed[identifier] for identifier in normalized]


def creator(name: str) -> dict[str, str]:
    """Represent an arXiv author as a Zotero creator."""
    parts = name.strip().rsplit(" ", 1)
    if len(parts) == 2:
        return {
            "firstName": parts[0],
            "lastName": parts[1],
            "creatorType": "author",
        }
    return {"name": name.strip(), "creatorType": "author"}


def make_item(result: Any) -> tuple[dict[str, Any], str]:
    """Build one Zotero report item and its PDF URL."""
    identifier = normalize_identifier(result.entry_id)
    categories = list(getattr(result, "categories", None) or [])
    published = getattr(result, "published", None)
    extras = [f"arXiv: {identifier}"]
    if getattr(result, "journal_ref", None):
        extras.append(f"Journal: {result.journal_ref}")
    if getattr(result, "comment", None):
        extras.append(f"Comment: {result.comment}")
    if categories:
        extras.append(f"Categories: {', '.join(categories)}")

    item = {
        "itemType": "report",
        "title": (getattr(result, "title", "") or "").strip(),
        "abstractNote": getattr(result, "summary", "") or "",
        "date": published.date().isoformat() if published else "",
        "url": f"https://arxiv.org/abs/{identifier}",
        "DOI": getattr(result, "doi", "") or "",
        "archive": "arXiv",
        "libraryCatalog": "arXiv",
        "reportType": "Preprint",
        "institution": "arXiv",
        "accessDate": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "creators": [
            creator(getattr(author, "name", str(author)))
            for author in (getattr(result, "authors", None) or [])
        ],
        "tags": [{"tag": "arxiv", "type": 1}]
        + [{"tag": category, "type": 1} for category in categories],
        "attachments": [],
        "extra": "\n".join(extras),
    }
    return item, f"https://arxiv.org/pdf/{identifier}.pdf"


def session_id(items: list[dict[str, Any]]) -> str:
    """Create a deterministic Connector session identifier."""
    titles = "|".join(sorted(item.get("title", "") for item in items))
    return hashlib.sha256(titles.encode("utf-8")).hexdigest()[:16]


def fetch_pdf(url: str) -> tuple[bytes | None, str | None]:
    """Download one PDF and reject HTML or truncated responses."""
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/pdf,*/*"},
    )
    try:
        with urllib.request.urlopen(request, timeout=PDF_TIMEOUT_SECONDS) as response:
            data = response.read()
            content_type = response.headers.get("Content-Type", "")
        if len(data) < 1024:
            return None, f"response too small ({len(data)} bytes)"
        if data[:5] != b"%PDF-" and "application/pdf" not in content_type:
            return None, f"unexpected Content-Type: {content_type}"
        return data, None
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        return None, f"URL error: {exc.reason}"
    except TimeoutError:
        return None, f"timeout after {PDF_TIMEOUT_SECONDS}s"


def upload_pdf(session: str, parent_id: str, pdf_url: str, data: bytes) -> tuple[int, str]:
    """Attach a PDF binary to an item created in the same Connector session."""
    metadata = json.dumps(
        {
            "id": f"{parent_id}_pdf",
            "parentItemID": parent_id,
            "title": "Full Text PDF",
            "url": pdf_url,
            "contentType": "application/pdf",
        },
        ensure_ascii=False,
    )
    request = urllib.request.Request(
        f"{CONNECTOR_URL}/saveAttachment?sessionID={session}",
        data=data,
        headers={
            "Content-Type": "application/pdf",
            "Content-Length": str(len(data)),
            "X-Metadata": metadata,
            "X-Zotero-Connector-API-Version": "3",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=PDF_TIMEOUT_SECONDS) as response:
            return response.status, ""
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        return 0, str(exc)


def import_results(results: list[Any], skip_pdf: bool) -> dict[str, Any]:
    """Create items and attempt PDF uploads without blocking metadata import."""
    built = [make_item(result) for result in results]
    items = [item for item, _ in built]
    pdf_urls = [pdf_url for _, pdf_url in built]
    session = session_id(items)
    for index, item in enumerate(items):
        item["id"] = f"arxiv_{session}_{index}"

    status, response = json_request(
        "saveItems",
        {"sessionID": session, "uri": "", "items": items},
    )
    if status not in (201, 409):
        if status == 0:
            raise RuntimeError("Zotero Connector API is unavailable. Start Zotero Desktop.")
        raise RuntimeError(f"saveItems failed with HTTP {status}: {response}")

    attachments = []
    if status == 201 and not skip_pdf:
        for item, pdf_url in zip(items, pdf_urls):
            data, error = fetch_pdf(pdf_url)
            if data is None:
                attachments.append({"title": item["title"], "status": "failed", "error": error})
                continue
            upload_status, upload_error = upload_pdf(session, item["id"], pdf_url, data)
            attachments.append(
                {
                    "title": item["title"],
                    "status": "attached" if upload_status in (200, 201) else "failed",
                    "error": upload_error or None,
                }
            )

    collection_status, collection = json_request("getSelectedCollection")
    return {
        "success": True,
        "collection": collection.get("name", "Unknown")
        if collection_status == 200 and isinstance(collection, dict)
        else "Unknown",
        "already_saved": status == 409,
        "items": [
            {"title": item["title"], "url": item["url"], "pdf_url": pdf_url}
            for item, pdf_url in zip(items, pdf_urls)
        ],
        "attachments": attachments,
    }


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("identifiers", nargs="+", help="arXiv IDs or URLs")
    parser.add_argument("--skip-pdf", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args()

    try:
        results = fetch_results(args.identifiers)
        payload = import_results(results, skip_pdf=args.skip_pdf)
    except ImportError:
        payload = {
            "success": False,
            "error": f"Install the arxiv package with: {sys.executable} -m pip install arxiv",
        }
    except Exception as exc:
        payload = {"success": False, "error": str(exc)}

    if args.json or not payload["success"]:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Zotero collection: {payload['collection']}")
        for item in payload["items"]:
            print(f"- {item['title']}")
        for attachment in payload["attachments"]:
            print(f"  PDF {attachment['status']}: {attachment['title']}")
    return 0 if payload["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
