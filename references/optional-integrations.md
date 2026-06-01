# Optional Integrations

Use these workflows only when requested or when the core pipeline needs a
specific fallback. They are not required for routine multi-source screening.

## IEEE PDF Download

Use only when the user explicitly requests a local IEEE PDF download. Confirm
that the user has institutional, subscriber, or open-access permission.

Preferred direct PDF URL:

```text
{BASE_URL}/stampPDF/getPDF.jsp?tp=&arnumber={ARNUMBER}&ref=
```

Fallback wrapper URL:

```text
{BASE_URL}/stamp/stamp.jsp?tp=&arnumber={ARNUMBER}
```

Run downloads serially and wait at least 3 seconds between attempts. If a
request redirects to a document page or returns HTML, report that login or
access is required. Do not attempt to bypass subscription controls.

## IEEE Journal Or Conference Browse

Use when the user requests recent articles, popular articles, or issue browsing.
Preserve `punumber` for publications and `isnumber` for issues.

```text
{BASE_URL}/xpl/RecentIssue.jsp?punumber={PUNUMBER}
{BASE_URL}/xpl/topAccessedArticles.jsp?punumber={PUNUMBER}
{BASE_URL}/xpl/issues?punumber={PUNUMBER}
{BASE_URL}/xpl/tocresult.jsp?punumber={PUNUMBER}&isnumber={ISNUMBER}
{BASE_URL}/xpl/conhome/{PUNUMBER}/proceeding
```

Extract publication name, metrics when present, ISSN, available tabs, and
article links with their `arnumber` values.

## IEEE SA Standards Search

Use `https://standards.ieee.org/search/?q=<query>` when the user requests IEEE
or ANSI standards, draft projects, or an IEEE counterpart for an IEC or ISO
standard. IEEE SA is separate from IEEE Xplore.

State clearly:

- IEEE SA hosts catalog entries, projects, and status information.
- IEEE Xplore may host published IEEE standard full text subject to access.
- IEC and ISO originals must be obtained from their official publishers.

## Obsidian Synthesis

Read [obsidian-synthesis.md](obsidian-synthesis.md) when the user requests
cross-paper topic notes. Obsidian MCP is optional. Personal vault layouts such
as I.P.A.R.A must remain user configuration rather than a published default.

## MinerU PDF Parsing

Treat MinerU as an optional external integration for difficult PDFs or layout
extraction. Do not bundle a machine-specific WSL script by default because WSL
distro, Conda environment, CUDA configuration, output directory, and model
source differ between machines.

Document MinerU integration as optional if publishing a local deployment guide.

## Serper Paper Search

Treat Serper-backed paper search as an optional discovery fallback. It requires
an external API integration and quota. Do not make it a default dependency of
the portable skill.

## arXiv TeX Source Reading

For deep reading of an arXiv paper, TeX source extraction can be added later as
a portable optional module. Do not copy project-specific behavior that writes
summaries into an unrelated repository.
