# Platform Support

The bundled Python scripts use Python standard-library paths and HTTP APIs.
They are intended to run on Windows, Linux, and macOS.

## Python Launcher

Use the Python launcher available on the target machine:

| Platform | Typical launcher |
| --- | --- |
| Windows | `python` or `py -3` |
| Linux | `python3` |
| macOS | `python3` |

In all skill commands, replace `<python>` with the available launcher and
replace `<skill-dir>` with the absolute installed skill directory.

Example:

```text
<python> "<skill-dir>/scripts/preflight.py" --json
```

Forward slashes in documented script paths are intentional. Python accepts
them on Windows, Linux, and macOS.

## Installation Directory

Install the whole folder under `${CODEX_HOME}/skills`. When `CODEX_HOME` is
unset, use:

| Platform | Default location |
| --- | --- |
| Windows | `%USERPROFILE%\.codex\skills` |
| Linux | `~/.codex/skills` |
| macOS | `~/.codex/skills` |

## Runtime Dependencies

Required on every platform:

- Python 3.10 or later
- `arxiv` Python package
- Zotero Desktop
- Chrome DevTools MCP
- Zotero MCP

Install the Python dependency with:

```text
<python> -m pip install arxiv
```

## Validation Scope

`scripts/preflight.py` validates the operating system, Python version, bundled
scripts, the `arxiv` package, and the local Zotero Connector API.

MCP registrations and browser authentication remain manual checks.

## Tested Status

- Windows: validated locally.
- Linux: portable code path implemented; run preflight and an import smoke test
  on the target machine before claiming verified support.
- macOS: portable code path implemented; run preflight and an import smoke test
  on the target machine before claiming verified support.
