# Literature Research Pipeline

[中文](README.md) | English

A portable, Zotero-first Agent Skill for literature research workflows across Google Scholar, IEEE Xplore, and arXiv. It can be used with Codex and Claude Code.

## Features

- Search and screen papers across multiple sources
- Import records into Zotero with deduplication, tags, and structured reading notes
- Preserve metadata and provide a fallback workflow when PDF download fails
- Optionally create topic syntheses in Obsidian

## Requirements

- Python 3.10+
- Zotero Desktop
- Chrome DevTools MCP
- Zotero MCP

Optional component:

- Obsidian MCP

## Platform Support

- Windows: tested
- Linux / Ubuntu: portable implementation completed, but not yet smoke-tested
- macOS: portable implementation completed, but not yet smoke-tested

## Installation

Place this repository in the personal skills directory for your client and keep the directory name as:

```text
literature-research-pipeline
```

Common installation locations:

```text
Codex:       ~/.codex/skills/literature-research-pipeline
Claude Code: ~/.claude/skills/literature-research-pipeline
```

Claude Code also supports project-scoped installation:

```text
<project>/.claude/skills/literature-research-pipeline
```

Run the environment preflight check:

```text
<python> "<skill-dir>/scripts/preflight.py" --json
```

On Windows, `<python>` is typically `python` or `py -3`. On Linux and macOS, it is typically `python3`.

## MCP Dependencies

This repository does not bundle MCP server code. Configure the following components separately in your client before use:

- Chrome DevTools MCP: browser automation for Google Scholar and IEEE Xplore
- Zotero MCP: Zotero library lookup, deduplication, tags, and reading notes
- Obsidian MCP: optional topic synthesis in Obsidian

Zotero Desktop must also expose its local Connector API:

```text
http://127.0.0.1:23119/connector
```

## arXiv Access

The arXiv branch prefers the official API and respects its request interval. The scripts include cross-process throttling, a local cache, and cooldown handling. When the API returns `429` or times out, they automatically fall back to official arXiv search and abstract pages.

Thank you to arXiv for use of its open access interoperability.

## Release Status

The workflow has been tested on Windows. Linux / Ubuntu and macOS have not yet received complete real-machine testing.

See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for upstream attribution and license notes.
