# Zotero Workflow

Use Zotero as the paper-level system of record.

## Import Rules

1. Search Zotero through Zotero MCP before importing.
2. Match exact DOI first, then normalized title, then first author plus year.
3. Prefer a Connector-driven save that creates metadata and attaches the PDF in one session.
4. Treat attachment failure as a recoverable state.
5. When an item already exists but lacks a PDF, attach to the existing item rather than creating a duplicate.

Bundled scripts:

```text
<python> "<skill-dir>/scripts/scholar_to_zotero.py" "<papers.json>"
<python> "<skill-dir>/scripts/ieee_to_zotero.py" --json "<papers.json>"
<python> "<skill-dir>/scripts/arxiv_to_zotero.py" <arxiv-id-or-url> [--skip-pdf] [--json]
```

## State Tags

Apply tags that match the actual item state:

```text
discovered
screened
metadata-only
pdf-attached
html-fulltext
abstract-only
summarized
needs-pdf-retry
```

## Reading Card

Create at most one standardized child note per paper. Update the existing standardized note when better evidence becomes available. Do not overwrite unrelated notes.

```markdown
## Paper Reading Card
Source Basis: pdf-attached|html-fulltext|abstract-only
Summary Scope: screening|deep-read

### Research Question
[What problem does this paper solve?]

### Core Innovation
[What is genuinely new compared with prior work?]

### Method Overview
[Model, algorithm, system structure, or key mechanism]

### Key Results
[Most important experiments or conclusions]

### Limitations
[Boundary conditions, missing evaluations, or risks]

### Relevance To My Topic
[Direct connection to the user's current research topic]

### Worth Deep Reading Or Reproduction
[Yes / Maybe / No + reason]

### One-Sentence Takeaway
[A concise 20-40 word summary]
```

## Evidence Rules

- For `abstract-only`, frame innovation and limitation claims as provisional.
- For `html-fulltext`, state that the note is based on webpage full text.
- For `pdf-attached`, summarize from the attached PDF when available.
- Upgrade the same note and tags when a stronger text source becomes available.
- Keep screening notes around 150-300 words and deep-read notes around 300-800 words.
