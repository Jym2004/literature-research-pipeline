#!/usr/bin/env python3
"""Check portable literature pipeline prerequisites."""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ZOTERO_API = "http://127.0.0.1:23119/connector"
REQUIRED_SCRIPTS = (
    "arxiv_search.py",
    "arxiv_to_zotero.py",
    "scholar_to_zotero.py",
    "ieee_to_zotero.py",
)


def connector_request(endpoint: str) -> tuple[int, Any]:
    """Send a JSON POST request to the local Zotero Connector API."""
    request = urllib.request.Request(
        f"{ZOTERO_API}/{endpoint}",
        data=b"{}",
        headers={
            "Content-Type": "application/json",
            "X-Zotero-Connector-API-Version": "3",
        },
    )
    try:
        response = urllib.request.urlopen(request, timeout=3)
        body = response.read().decode("utf-8")
        return response.status, json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        return 0, str(exc)


def add_check(
    checks: list[dict[str, Any]],
    name: str,
    ok: bool,
    detail: str,
    required: bool = True,
) -> None:
    """Append one structured check result."""
    checks.append(
        {
            "name": name,
            "ok": ok,
            "required": required,
            "detail": detail,
        }
    )


def run_checks(skip_zotero: bool, skip_arxiv: bool) -> dict[str, Any]:
    """Return a machine-readable prerequisite report."""
    script_dir = Path(__file__).resolve().parent
    checks: list[dict[str, Any]] = []

    python_ok = sys.version_info >= (3, 10)
    add_check(
        checks,
        "operating-system",
        sys.platform.startswith(("win32", "linux", "darwin")),
        f"{platform.system()} {platform.release()} ({sys.platform})",
    )

    add_check(
        checks,
        "python",
        python_ok,
        (
            f"{sys.version_info.major}.{sys.version_info.minor}."
            f"{sys.version_info.micro} at {sys.executable}"
        ),
    )

    missing_scripts = [
        filename for filename in REQUIRED_SCRIPTS if not (script_dir / filename).is_file()
    ]
    add_check(
        checks,
        "bundled-scripts",
        not missing_scripts,
        "all bundled scripts present"
        if not missing_scripts
        else f"missing: {', '.join(missing_scripts)}",
    )

    if not skip_arxiv:
        arxiv_ok = importlib.util.find_spec("arxiv") is not None
        add_check(
            checks,
            "python-package-arxiv",
            arxiv_ok,
            "installed"
            if arxiv_ok
            else f"missing; install with: {sys.executable} -m pip install arxiv",
        )

    if not skip_zotero:
        ping_status, ping_data = connector_request("ping")
        add_check(
            checks,
            "zotero-connector",
            ping_status != 0,
            f"HTTP {ping_status}" if ping_status else f"unavailable: {ping_data}",
        )
        if ping_status != 0:
            collection_status, collection = connector_request("getSelectedCollection")
            collection_ok = collection_status == 200 and isinstance(collection, dict)
            if collection_ok:
                editable = collection.get("editable", True)
                files_editable = collection.get("filesEditable", True)
                name = collection.get("name", "Unknown")
                detail = (
                    f"collection={name!r}, editable={editable}, "
                    f"filesEditable={files_editable}"
                )
                collection_ok = bool(editable)
            else:
                detail = f"HTTP {collection_status}: {collection}"
            add_check(checks, "zotero-selected-collection", collection_ok, detail)

    failed_required = [
        check["name"] for check in checks if check["required"] and not check["ok"]
    ]
    return {
        "ok": not failed_required,
        "skill_dir": str(script_dir.parent),
        "checks": checks,
        "manual_checks": [
            "Chrome DevTools MCP is available for Google Scholar and IEEE Xplore.",
            "Zotero MCP is available for library lookup, notes, and tags.",
            "Obsidian MCP is available only if topic synthesis is requested.",
            "On Linux or macOS, use python3 when python is not on PATH.",
        ],
        "failed_required": failed_required,
    }


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-zotero",
        action="store_true",
        help="Skip local Zotero Connector checks.",
    )
    parser.add_argument(
        "--skip-arxiv",
        action="store_true",
        help="Skip the optional arxiv Python package check.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args()

    report = run_checks(skip_zotero=args.skip_zotero, skip_arxiv=args.skip_arxiv)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for check in report["checks"]:
            marker = "OK" if check["ok"] else "FAIL"
            print(f"[{marker}] {check['name']}: {check['detail']}")
        print("Manual checks:")
        for check in report["manual_checks"]:
            print(f"- {check}")
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
