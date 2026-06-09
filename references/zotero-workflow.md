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

## Note Write-Back Rules

Use Zotero MCP for reading-card notes:

```text
write_note(action="create", parentKey="<itemKey>", content="<reading-card>", tags=["summarized", "<state>"])
write_note(action="update", noteKey="<noteKey>", content="<updated-reading-card>")
write_tag(action="add", itemKey="<itemKey>", tags=["screened", "<state>", "summarized"])
```

Do not use the Connector API's `/connector/saveItems` endpoint to create child
notes for existing Zotero items. Connector `parentItemID` values are scoped to
the same Connector save session and are not the same as persistent Zotero item
keys such as `U7FBRAG4`. Using Connector note payloads with existing item keys
can create standalone notes in the selected collection instead of child notes.

Do not rely on Zotero's local `/api/users/...` HTTP endpoint for write-back
unless the current environment is explicitly verified to support writes. Some
Zotero versions expose local API reads while returning "Endpoint does not
support method" for writes. Prefer Zotero MCP write tools when available.

Before creating a new note, inspect the parent item's existing notes. If a note
contains the `## Paper Reading Card` header, update that note instead of
creating another one.

After writing, re-read the parent item and verify:

- the reading card appears under the parent item's notes or children
- the note is not a standalone collection-root note
- the parent item has tags matching the content state, e.g. `pdf-attached` and
  `summarized`

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
