# IEEE Xplore Browser Workflow

Use Chrome DevTools MCP. Run IEEE navigations serially and preserve `arnumber` as the source identifier.

## Base URL

Inspect existing browser pages before the first request. Reuse the active IEEE Xplore hostname because it may be an institutional proxy. If no IEEE page is open, use `https://ieeexplore.ieee.org` unless the user needs a proxy.

For every `navigate_page` call, use:

```javascript
Object.defineProperty(navigator, 'webdriver', {get: () => undefined})
```

Pass this string as `initScript`.

## Basic Search

For simple keyword search, build:

```text
{BASE_URL}/search/searchresult.jsp?queryText=<query>&highlight=true&returnFacets=ALL&returnType=SEARCH&matchPubs=true&rowsPerPage=25&pageNumber=1
```

Always quote multi-word phrases. Add a domain anchor when abbreviations are
ambiguous. If results exceed roughly 500, narrow the query. If there are no
results, remove one phrase or try synonyms.

## Advanced Search

Build URLs instead of filling forms:

```text
{BASE_URL}/search/searchresult.jsp?action=search&matchBoolean=true&queryText=<query>&highlight=true&returnType=SEARCH&matchPubs=true&rowsPerPage=25&pageNumber=1&ranges=<start>_<end>_Year
```

Use `AND` between different concepts. Use `OR` only for synonyms. Quote multi-word phrases.

Common command-search fields:

| Intent | Query field |
| --- | --- |
| title | `"Document Title":<term>` |
| author | `"Authors":<name>` |
| publication | `"Publication Title":<name>` |
| abstract | `"Abstract":<term>` |
| keywords | `"Author Keywords":<term>` |
| DOI | `"DOI":<value>` |
| article number | `"Article Number":<value>` |

Optional URL filters:

| Intent | Parameter |
| --- | --- |
| year range | `ranges=<start>_<end>_Year` |
| conferences | `contentType=conferences` |
| journals | `contentType=periodicals` |
| standards | `contentType=standards` |
| books | `contentType=books` |

After navigation, extract results with `evaluate_script` and a bounded wait loop:

```javascript
async () => {
  for (let i = 0; i < 30; i++) {
    if (document.querySelectorAll('.List-results-items .result-item').length ||
        document.querySelector('.Dashboard-header span')) break;
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  return Array.from(document.querySelectorAll('.List-results-items .result-item'))
    .map((item, index) => {
      const title = item.querySelector('h3 a[href*="/document/"]');
      const info = item.querySelector('.publisher-info-container')?.textContent?.trim() || '';
      return {
        rank: index + 1,
        title: title?.textContent?.trim() || '',
        arnumber: title?.href?.match(/\/document\/(\d+)/)?.[1] || '',
        authors: Array.from(item.querySelectorAll('.author a[href*="/author/"]'))
          .map(author => author.textContent.trim()),
        publication: item.querySelector('.description a[href*="/xpl/"]')?.textContent?.trim() || '',
        year: info.match(/Year:\s*(\d{4})/)?.[1] || '',
        cited_by: Number(item.textContent.match(/Cited by:.*?(\d+)/)?.[1] || 0),
        abstract: item.querySelector('.js-displayer-content span')?.textContent?.trim() || '',
        has_checkbox: !!item.querySelector('input[type="checkbox"]'),
        info
      };
    });
}
```

## Re-Parse Current Results

When the user manually changes filters or sorting, do not navigate. Run the same
extraction script on the current search page and also return:

```javascript
{
  current_url: window.location.href,
  url_params: Object.fromEntries(new URL(window.location.href).searchParams)
}
```

## Pagination And Sorting

Preserve all existing URL parameters and change only the requested values:

| Intent | Parameter update |
| --- | --- |
| next page | increment `pageNumber` |
| previous page | decrement `pageNumber`, minimum 1 |
| page N | set `pageNumber=N` |
| newest first | `sortType=newest` |
| most cited | `sortType=paper-citations` |
| relevance | remove `sortType` |
| show 100 | `rowsPerPage=100`, reset `pageNumber=1` |

Navigate serially and run the extraction script again.

## Article Details

Navigate to:

```text
{BASE_URL}/document/{ARNUMBER}/
```

Extract title, authors, abstract, DOI, publication, metadata, keywords, PDF URL,
`arnumber`, cited-by count, full-text views, section headings, and reference
count. Use DOM extraction with a bounded wait loop. Do not use `wait_for`
because IEEE pages can produce oversized snapshots.

Use these selectors:

| Field | Selector or strategy |
| --- | --- |
| title | `.document-title span` |
| authors | `.authors-info a[href*="/author/"]` |
| abstract | `.abstract-text div[xplmathjax]`, then `.abstract-text` |
| DOI | `a[href*="doi.org"]` |
| publication | `.stats-document-abstract-publishedIn a` |
| metadata | `.abstract-desktop-div .u-pb-1` |
| keywords | `.stats-keywords-module a`, then keyword-list fallbacks |
| PDF wrapper | `a[href*="stamp/stamp.jsp"]` |
| article number | parse `/document/<arnumber>/` from URL |
| section headings | `.document-toc a, h2` |
| references | `.reference-container, [class*="reference-item"]` |

## No-Result Handling

If no results are returned:

1. suggest broader keywords or synonyms
2. explain that IEEE Xplore does not host IEC, ISO, or CENELEC originals
3. search by technical topic instead of an IEC or ISO number
4. use the optional IEEE SA standards workflow when the user needs an IEEE or
   ANSI counterpart

## Access Challenges

After every navigation:

- stop for CAPTCHA or bot challenges and wait for user verification
- stop for redirects and wait for login or institutional authentication
- space out navigations to avoid rate limiting

## Import

Collect selected papers as structured JSON. Use this shape:

```json
{
  "title": "",
  "authors": [],
  "publication": "",
  "year": "",
  "doi": "",
  "abstract": "",
  "keywords": [],
  "arnumber": "",
  "url": "",
  "pdfUrl": "",
  "cookies": ""
}
```

Run:

```text
<python> "<skill-dir>/scripts/ieee_to_zotero.py" --json "<papers.json>"
```

PDF access may require authenticated browser cookies. If the PDF cannot be fetched, keep the imported metadata and mark the item `needs-pdf-retry`.

## Optional IEEE Operations

For explicit PDF downloads, journal browsing, or standards catalog lookup, read
[optional-integrations.md](optional-integrations.md). These capabilities are
packaged as optional references rather than mandatory pipeline stages.
