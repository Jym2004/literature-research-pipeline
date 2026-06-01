#!/usr/bin/env python3
"""Search arXiv and emit portable structured metadata."""

from __future__ import annotations

import argparse
import json

from arxiv_support import search_records


def serialize_result(result: object) -> dict[str, object]:
    """Convert one portable record to a stable JSON payload."""
    return {
        "arxiv_id": result.arxiv_id,
        "arxiv_versioned_id": result.versioned_id,
        "title": result.title,
        "authors": result.authors,
        "published": result.published,
        "updated": result.updated,
        "abs_url": result.entry_id,
        "pdf_url": result.pdf_url,
        "summary": result.summary,
        "primary_category": result.primary_category,
        "categories": result.categories or [],
        "doi": result.doi,
        "journal_ref": result.journal_ref,
        "comment": result.comment,
        "metadata_source": result.metadata_source,
    }


def search_arxiv(query: str, limit: int) -> list[dict[str, object]]:
    """Search arXiv through the API with official HTML fallback."""
    return [serialize_result(result) for result in search_records(query, limit)]


def render_text(records: list[dict[str, object]]) -> str:
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
    except Exception as exc:
        print(f"Error querying arXiv: {exc}")
        return 1

    if args.format == "json":
        print(json.dumps(records, ensure_ascii=False, indent=2))
    else:
        print(render_text(records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
