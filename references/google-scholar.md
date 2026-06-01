# Google Scholar Browser Workflow

Use Chrome DevTools MCP and DOM extraction. Google Scholar has no public API. Keep requests serial and paced.

## Search

Build a URL:

```text
https://scholar.google.com/scholar?q=<keywords>&as_ylo=<start-year>&as_yhi=<end-year>&num=10&hl=en
```

Optional parameters:

| Intent | Parameter |
| --- | --- |
| author | `as_sauthors` |
| publication | `as_publication` |
| exact phrase | `as_epq` |
| exclude words | `as_eq` |
| title only | `as_occt=title` |

Use `navigate_page`, then extract structured results with `evaluate_script`:

```javascript
async () => {
  for (let i = 0; i < 20; i++) {
    if (document.querySelector('#gs_res_ccl') ||
        document.querySelector('#gs_captcha_ccl')) break;
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  if (document.querySelector('#gs_captcha_ccl') ||
      document.body.innerText.includes('unusual traffic')) {
    return { error: 'captcha' };
  }
  return Array.from(document.querySelectorAll('#gs_res_ccl .gs_r.gs_or.gs_scl'))
    .map((item, index) => {
      const title = item.querySelector('.gs_rt a');
      const citedBy = item.querySelector('.gs_fl a[href*="cites"]');
      const fulltext = item.querySelector('.gs_ggs a, .gs_or_ggsm a');
      return {
        rank: index + 1,
        data_cid: item.getAttribute('data-cid') || '',
        title: title?.textContent?.trim() || '',
        url: title?.href || '',
        metadata: item.querySelector('.gs_a')?.textContent?.trim() || '',
        snippet: item.querySelector('.gs_rs')?.textContent?.trim() || '',
        citation_count: Number(citedBy?.textContent?.match(/\d+/)?.[0] || 0),
        fulltext_url: fulltext?.href || ''
      };
    });
}
```

Preserve `data_cid`, result URL, citation count, direct PDF or HTML URL, related
results URL, and versions URL:

```javascript
const related = item.querySelector('.gs_fl a[href*="related"]');
const versions = item.querySelector('.gs_fl a[href*="cluster"]');
```

Store:

```json
{
  "related_url": "",
  "versions_url": "",
  "versions_count": 0
}
```

Use versions links as legitimate full-text fallback candidates when the primary
result does not expose an accessible PDF or HTML page.

## Pagination

Google Scholar uses a zero-based `start` query parameter with increments of 10:

| Page | Parameter |
| --- | --- |
| 1 | omit `start` or use `start=0` |
| 2 | `start=10` |
| N | `start=(N - 1) * 10` |

To fetch more candidates, modify the current URL, navigate serially, and run the
same extraction logic. Preserve existing search parameters. Keep result counts
small to reduce CAPTCHA risk.

## Citation Tracking

When the user requests citation-chain analysis, use the Scholar cluster ID:

```text
https://scholar.google.com/scholar?cites=<data_cid>&hl=en&num=10
```

Run the same result extraction logic on the cited-by page. Preserve the citing
papers' `data_cid` values so the user can continue recursively or import selected
papers. Citation tracking is optional during routine screening, but available
without any sibling skill.

## CAPTCHA

If a CAPTCHA or unusual-traffic page appears:

1. Stop all Google Scholar operations.
2. Ask the user to complete verification in the browser.
3. Wait for confirmation before retrying.

Do not automatically retry.

## Import

For selected results:

1. Fetch each citation dialog from the Scholar page:

```javascript
async cid => {
  const response = await fetch(
    `https://scholar.google.com/scholar?q=info:${cid}:scholar.google.com/&output=cite`,
    { credentials: 'include' }
  );
  const html = await response.text();
  const doc = new DOMParser().parseFromString(html, 'text/html');
  return Array.from(doc.querySelectorAll('#gs_citi a')).map(link => ({
    format: link.textContent.trim(),
    url: link.href
  }));
}
```

2. Navigate serially to each BibTeX URL and read `document.body.innerText`.
3. Parse BibTeX into JSON and include the original `url`, `fullTextUrl`, and DOI when known.
4. Run:

```text
<python> "<skill-dir>/scripts/scholar_to_zotero.py" "<papers.json>"
```

Return to the Scholar results page after export.

## Full-Text Fallback

Prefer:

1. direct PDF or HTML links visible in Scholar results
2. accessible copies from the Scholar versions page
3. DOI URL or publisher page
4. abstract-only screening

Do not treat a missing PDF as an import failure. Do not add unofficial
copyright-bypassing sources to this workflow.
