# Provenance Audit

Keep `THIRD_PARTY_NOTICES.md` in every public release. Re-run this audit when
adding or replacing bundled third-party-derived files.

## Current Status

The Google Scholar and IEEE Xplore sources have been recovered. The arXiv
scripts have been replaced with independently written portable implementations.

| Bundled file | Local source | Relationship | Release status |
| --- | --- | --- | --- |
| `scripts/arxiv_search.py` | new implementation | independently written | clear |
| `scripts/arxiv_to_zotero.py` | new implementation | independently written | clear |
| `scripts/scholar_to_zotero.py` | `https://github.com/cookjohn/gs-skills` | adapted from MIT upstream | retain notice |
| `scripts/ieee_to_zotero.py` | `https://github.com/cookjohn/ieee-skills` | adapted from MIT upstream | retain notice |

## Recovered Upstreams

| Component | Upstream repository | Revision reviewed | License status |
| --- | --- | --- | --- |
| Google Scholar workflow | `https://github.com/cookjohn/gs-skills` | `df03c99f1a741ff816e6f0e12c13308279bcd730` | MIT `LICENSE` file present |
| IEEE Xplore workflow | `https://github.com/cookjohn/ieee-skills` | `3ec1c13f99330ee967d176aa170a175ca4476e29` | upstream README declares MIT; no root `LICENSE` file present |

## Workflow Notes Versus Copied Expression

Ideas, procedures, and methods can be reimplemented without copying the
original wording or code. For example, the general sequence "search, normalize,
de-duplicate, import to Zotero, then write reading cards" can be documented as
this package's own workflow.

Do not assume that every Markdown reference is automatically clear for public
release. The browser workflow references were newly consolidated for this
package but were based on behavior and procedures from the local Google Scholar
and IEEE Xplore skill suites. Some JavaScript DOM extraction snippets remain
close to the local source material. Treat those snippets as unresolved until
they are attributed under a compatible upstream license or independently
rewritten.

Record upstream sources when known even where attribution is not legally
required. This improves transparency and makes later audits easier.

## Before Public Release

For each upstream repository:

1. record the repository URL and commit or release version
2. inspect its license file
3. preserve required copyright notices and attribution
4. include any required license text or `NOTICE` file
5. confirm that modifications and redistribution are permitted

The IEEE repository README declares MIT but does not include a root `LICENSE`
file at the reviewed revision. Keep that fact visible in
`THIRD_PARTY_NOTICES.md`. For maximum legal certainty, ask the upstream author
to add a license file or confirm the intended MIT terms.

## Suggested Attribution Record

Maintain a table in the public repository:

| Component | Upstream repository | Revision | License | Changes made |
| --- | --- | --- | --- | --- |
| Google Scholar workflow | `https://github.com/cookjohn/gs-skills` | `df03c99f1a741ff816e6f0e12c13308279bcd730` | MIT | consolidated and adapted |
| IEEE Xplore workflow | `https://github.com/cookjohn/ieee-skills` | `3ec1c13f99330ee967d176aa170a175ca4476e29` | README declares MIT | consolidated and adapted |
| arXiv scripts | independent implementation | local release | project license | rewritten for portability |

Do not fill unknown values with guesses.
