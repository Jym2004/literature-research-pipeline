#!/usr/bin/env python3
"""Search arXiv and emit portable structured metadata."""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any


def base_arxiv_id(value: str) -> str:
    """Return an arXiv identifier without URL wrappers or version suffixes."""
    identifier = value.strip().rstrip("/").split("/")[-1]
    identifier = re.sub(r"\.pdf$", "", identifier, flags=re.IGNORECASE)
    return re.sub(r"v\d+$", "", identifier)


def serialize_result(result: Any) -> dict[str, Any]:
    """Convert one arxiv.Result instance to a stable JSON record."""
    identifier = base_arxiv_id(result.entry_id)
    published = getattr(result, "published", None)
    updated = getattr(result, "updated", None)
    return {
        "arxiv_id": identifier,
        "title": (getattr(result, "title", "") or "").strip(),
        "authors": [
            getattr(author, "name", str(author))
            for author in (getattr(result, "authors", None) or [])
        ],
        "published": published.isoformat() if published else "",
        "updated": updated.isoformat() if updated else "",
        "abs_url": f"https://arxiv.org/abs/{identifier}",
        "pdf_url": f"https://arxiv.org/pdf/{identifier}.pdf",
        "summary": (getattr(result, "summary", "") or "").strip(),
        "primary_category": getattr(result, "primary_category", "") or "",
        "categories": list(getattr(result, "categories", None) or []),
        "doi": getattr(result, "doi", "") or "",
        "journal_ref": getattr(result, "journal_ref", "") or "",
        "comment": getattr(result, "comment", "") or "",
    }


def search_arxiv(query: str, limit: int) -> list[dict[str, Any]]:
    """Run one relevance-sorted arXiv query."""
    import arxiv  # type: ignore[import-not-found]

    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=limit,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    return [serialize_result(result) for result in client.results(search)]


def render_text(records: list[dict[str, Any]]) -> str:
    """Render records for interactive use."""
    if not records:
        return "No papers found on arXiv."
    blocks = []
    for index, record in enumerate(records, start=1):
        authors = ", ".join(record["authors"]) or "Unknown"
        blocks.append(
            "\n".join(
                [
                    f"[{index}] {record['title']}",
                    f"Authors: {authors}",
                    f"Published: {record['published'] or 'Unknown'}",
                    f"arXiv ID: {record['arxiv_id']}",
                    f"URL: {record['abs_url']}",
                    f"PDF: {record['pdf_url']}",
                    f"Summary: {record['summary']}",
                ]
            )
        )
    return "\n\n".join(blocks)


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="arXiv query string")
    parser.add_argument("--max-papers", type=int, default=10)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    if args.max_papers < 1:
        parser.error("--max-papers must be positive")

    try:
        records = search_arxiv(args.query, args.max_papers)
    except ImportError:
        print(
            f"Error: install the arxiv package with: {sys.executable} -m pip install arxiv",
            file=sys.stderr,
        )
        return 1
    except Exception as exc:
        print(f"Error querying arXiv: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(records, ensure_ascii=False, indent=2))
    else:
        print(render_text(records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
