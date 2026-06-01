# Portability And Installation

This skill is publishable as one folder. It does not require sibling skills.

## Bundled Files

```text
literature-research-pipeline/
|-- SKILL.md
|-- LICENSE
|-- THIRD_PARTY_NOTICES.md
|-- agents/
|   `-- openai.yaml
|-- scripts/
|   |-- preflight.py
|   |-- arxiv_support.py
|   |-- arxiv_search.py
|   |-- arxiv_to_zotero.py
|   |-- scholar_to_zotero.py
|   `-- ieee_to_zotero.py
`-- references/
    |-- google-scholar.md
    |-- ieee-xplore.md
    |-- zotero-workflow.md
    |-- obsidian-synthesis.md
    |-- optional-integrations.md
    |-- github-publishing.md
    |-- platform-support.md
    |-- provenance-audit.md
    `-- portability.md
```

## External Runtime Dependencies

Required:

- Python 3.10 or later
- Zotero Desktop with local Connector API enabled
- Chrome DevTools MCP
- Zotero MCP

Optional:

- Obsidian MCP for topic-level synthesis
- MinerU for PDF layout extraction
- Serper-backed paper search as a discovery fallback

## Installation

Read [platform-support.md](platform-support.md). Copy the entire
`literature-research-pipeline` directory into the personal skills directory for
the target client:

```text
${CODEX_HOME}/skills
```

For Claude Code, use:

```text
~/.claude/skills
```

If `CODEX_HOME` is unset, use the platform default:

```text
Windows: %USERPROFILE%\.codex\skills
Linux:   ~/.codex/skills
macOS:   ~/.codex/skills
```

Then run:

```text
<python> "<skill-dir>/scripts/preflight.py" --json
```

Confirm MCP availability separately because a local Python process cannot inspect MCP registrations.

## GitHub Release

Before a public release, read
[github-publishing.md](github-publishing.md) and
[provenance-audit.md](provenance-audit.md). Publish the whole skill directory
only after upstream licenses are confirmed. Declare runtime dependencies, add a
compatible license, and remove personal paths, browser cookies, proxy
credentials, and generated Python caches.

## Path Rule

Always resolve `<skill-dir>` from the active `SKILL.md`. Never hard-code a
username, home directory, `.agents/skills`, or `.codex/skills` path inside
runtime commands.
