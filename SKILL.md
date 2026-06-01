---
name: literature-research-pipeline
description: Run a portable Zotero-first literature workflow across Google Scholar, IEEE Xplore, and arXiv. Use when an AI coding agent needs to search multiple academic sources, screen and de-duplicate papers, import selected records and PDFs into Zotero, write structured reading-card notes, or optionally create an Obsidian topic synthesis. This skill is self-contained and must not depend on sibling source-specific skills.
---

# Literature Research Pipeline

## Purpose

Use this skill as a self-contained literature workflow. Keep Zotero as the paper-level system of record. Use Obsidian only for optional cross-paper synthesis.

Resolve all bundled scripts relative to this `SKILL.md`. Never call scripts through a hard-coded user profile path or a sibling skill directory.

## Runtime Contract

Require:

- Chrome DevTools MCP for Google Scholar and IEEE Xplore browser operations
- Zotero Desktop and its local Connector API at `http://127.0.0.1:23119/connector`
- Zotero MCP for library de-duplication, child notes, and tags
- Python 3.10 or later

Treat Obsidian MCP as optional. Use it only when the user requests a topic map, reading plan, method comparison, reproduction roadmap, or durable Obsidian note.

Before a full run, execute:

```text
<python> "<skill-dir>/scripts/preflight.py" --json
```

The preflight script cannot inspect MCP availability. Confirm the required MCP tools separately before browser or Zotero MCP work.
Read [references/platform-support.md](references/platform-support.md) when
installing on Windows, Linux, or macOS.

## Defaults

Infer missing values and state the assumptions briefly:

- sources: Google Scholar, IEEE Xplore, and arXiv
- year range: most recent 5 years
- shortlist: 10 de-duplicated candidates
- Zotero imports: best 5 candidates
- reading cards: best 3 imported papers
- citation threshold: no hard minimum
- ranking priority: direct relevance, then recency, credibility, citations, and full-text availability

Override these defaults when the user specifies a scope or count.

## Workflow

### 1. Check Preconditions

Run `scripts/preflight.py`. Confirm Chrome DevTools MCP and Zotero MCP are available. Confirm the selected Zotero collection is writable. Stop before import if the Connector API or target collection is unavailable.

### 2. Search Sources

Run browser branches serially because Chrome DevTools MCP shares page context.

- For Google Scholar, read [references/google-scholar.md](references/google-scholar.md).
- For IEEE Xplore, read [references/ieee-xplore.md](references/ieee-xplore.md).
- For arXiv, run:

```text
<python> "<skill-dir>/scripts/arxiv_search.py" "<query>" --max-papers <N> --format json
```

The bundled arXiv scripts use the official API politely with cross-process
throttling and local caching. When the API is cooling down after a `429` or
timeout, they fall back to official arXiv HTML pages. Preserve
`metadata_source` and the versioned arXiv identifier returned by the script.

Preserve stable source identifiers:

- Google Scholar: `data_cid`
- IEEE Xplore: `arnumber`
- arXiv: `arxiv_id`

### 3. Normalize And De-Duplicate

Normalize results into:

```json
{
  "source": "",
  "source_id": "",
  "title": "",
  "authors": [],
  "year": "",
  "doi": "",
  "venue": "",
  "citation_count": null,
  "abstract": "",
  "url": "",
  "pdf_url": "",
  "fulltext_url": "",
  "status": "discovered"
}
```

De-duplicate in this order:

1. exact DOI
2. normalized title
3. first author, year, and title similarity
4. Zotero MCP lookup before import

Do not create a second Zotero item when an equivalent library item already exists.

### 4. Screen And Rank

Rank with judgment rather than citation count alone. Consider topical relevance, publication year, source credibility, citation count, full-text availability, and whether an equivalent Zotero item already exists.

Present the shortlist before import when the user asks to review candidates first.

### 5. Import To Zotero

Read [references/zotero-workflow.md](references/zotero-workflow.md). Treat metadata creation and attachment creation as separate outcomes. Never block the pipeline because a PDF is unavailable.

Use the bundled scripts:

```text
<python> "<skill-dir>/scripts/scholar_to_zotero.py" "<papers.json>"
<python> "<skill-dir>/scripts/ieee_to_zotero.py" --json "<papers.json>"
<python> "<skill-dir>/scripts/arxiv_to_zotero.py" <arxiv-id-or-url> [--skip-pdf] [--json]
```

Track one content state per item:

- `metadata-only`
- `pdf-attached`
- `html-fulltext`
- `abstract-only`

### 6. Analyze And Write Reading Cards

Use the best available evidence in this order:

1. attached PDF
2. full-text HTML or webpage
3. abstract only

Write or update one standardized Zotero child note per paper. Do not overwrite unrelated user notes. Use the reading-card template and state tags in [references/zotero-workflow.md](references/zotero-workflow.md).

State uncertainty explicitly for `abstract-only` and `html-fulltext` summaries.

### 7. Optionally Synthesize In Obsidian

When the user requests durable topic-level knowledge, read [references/obsidian-synthesis.md](references/obsidian-synthesis.md). Write a cross-paper synthesis after Zotero write-back. Do not duplicate every Zotero reading card into Obsidian.

### 8. Use Optional Integrations When Requested

For IEEE PDF download, IEEE journal browsing, IEEE SA standards lookup, MinerU
PDF parsing, Serper discovery fallback, or arXiv TeX-source deep reading, read
[references/optional-integrations.md](references/optional-integrations.md).

## Failure Policy

- Google Scholar CAPTCHA: stop immediately and wait for manual verification.
- IEEE challenge, redirect, or login page: stop and wait for authentication.
- Zotero Connector unavailable: stop before import.
- PDF unavailable: keep metadata, use the next text source, and mark the state.
- Zotero MCP unavailable: allow search and screening, but stop before de-duplication or note write-back.

## Publishing

For migration and installation, read
[references/portability.md](references/portability.md). Before publishing to
GitHub, read [references/github-publishing.md](references/github-publishing.md)
and [references/provenance-audit.md](references/provenance-audit.md).
