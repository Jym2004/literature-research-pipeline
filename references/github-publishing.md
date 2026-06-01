# GitHub Publishing Checklist

Publish the complete `literature-research-pipeline` directory. Do not publish
only `SKILL.md`; bundled scripts and references are required.

## Attribution

Read [provenance-audit.md](provenance-audit.md) and keep
`THIRD_PARTY_NOTICES.md` in every public release. Google Scholar and IEEE
workflow components are adapted from MIT-licensed upstream repositories.

## Required Repository Notes

State these points prominently in the GitHub repository description or release
notes:

1. This is a Codex skill for a Zotero-first literature workflow across Google
   Scholar, IEEE Xplore, and arXiv.
2. The skill is self-contained and does not require sibling skills.
3. Chrome DevTools MCP and Zotero MCP must be configured separately.
4. Zotero Desktop must be running locally for imports.
5. Python 3.10 or later is required.
6. The arXiv branch requires `<python> -m pip install arxiv`.
7. Obsidian MCP, MinerU, and Serper integrations are optional.
8. Windows, Linux, and macOS use the same Python scripts; Linux and macOS still
   require target-machine smoke tests before claiming verified support.

## Service And Access Disclosures

State these operational constraints:

- Google Scholar has no public API in this workflow. Browser automation can
  trigger CAPTCHA. The skill stops and waits for manual verification.
- IEEE Xplore browsing can require login, institutional access, or manual
  challenge completion.
- IEEE PDF downloads require valid access. The skill does not bypass paywalls
  or subscription controls.
- Zotero imports use the local Connector API at
  `http://127.0.0.1:23119/connector`.
- Zotero MCP is still required for library de-duplication, reading-card notes,
  and state tags.

## Privacy Notes

State that:

- Zotero Connector traffic is sent to localhost.
- Search queries are sent to Google Scholar, IEEE Xplore, and arXiv when their
  branches are used.
- Optional Obsidian writes affect the user's local vault.
- Users should review browser cookies, proxy URLs, collection names, vault
  paths, and exported sample data before publishing logs or screenshots.

Do not commit:

```text
__pycache__/
*.pyc
.env
browser cookies
proxy credentials
Zotero library exports containing private notes
personal Obsidian vault paths
institution-specific URLs unless intentionally documented as examples
```

## License Notes

Keep the bundled MIT `LICENSE` file unless intentionally changing to another
compatible license. Verify that every bundled script can be redistributed
under the selected license. If code was adapted from another repository,
retain required notices and attribution.

Keep `THIRD_PARTY_NOTICES.md` in the repository and release archive. The arXiv
scripts are independently written implementations.

Do not claim affiliation with Google Scholar, IEEE, arXiv, Zotero, Obsidian, or
MinerU. Mention trademarks only to explain interoperability.

## Installation Notes

Tell users to read [platform-support.md](platform-support.md) and copy the full
skill directory into:

```text
${CODEX_HOME}/skills
```

When `CODEX_HOME` is unset, use:

```text
Windows: %USERPROFILE%\.codex\skills
Linux:   ~/.codex/skills
macOS:   ~/.codex/skills
```

Then run:

```text
<python> "<skill-dir>/scripts/preflight.py" --json
```

Explain that MCP availability must be confirmed separately because the local
preflight script cannot inspect MCP registrations.

## Recommended Git Ignore

```gitignore
__pycache__/
*.py[cod]
.env
```
