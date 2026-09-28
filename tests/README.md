# Test fixtures

## diff-with-bug/diff.patch

A two-intent diff with two planted issues, used to verify the skill's
independent-check step actually catches plausible-but-wrong code:

1. **`fetch_client.py` retry loop** — catches `requests.RequestException`,
   which includes `HTTPError` from `raise_for_status()`, so non-retryable
   4xx errors get retried; and it returns `None` on exhaustion where the
   old code raised (silent contract change for callers).
2. **`paginate.py`** — `start = (page - 1) * page_size` flips the function
   from 0-indexed to 1-indexed pages; existing 0-indexed callers silently
   shift a page, and `page=0` now yields a negative start.

**Passing run:** invoke the skill against this diff. It passes if:

- `fetch` gets a delta flowchart showing the new loop and `return None`
  as added, and the old raise-to-caller exit as removed.
- `page_bounds` is a Value row (`page * page_size` → `(page - 1) * page_size`),
  not a flowchart.
- Both planted issues appear as ⚠ doubts anchored to the right line.
- The page has no prose paragraphs; chat gets only the link and a count.

[`example-report.html`](diff-with-bug/example-report.html) is a reference
render. Wording and layout will vary between runs; the structure and the
two caught issues are the bar.
