# Test fixtures

Each fixture has a `base/` tree (the code before the change) and a
`diff.patch`. Build a scratch repo with the base committed and the patch
applied to the working tree, then run the skill there with the default
scope:

```sh
tests/setup.sh diff-with-bug          # prints the repo path (a temp dir)
tests/setup.sh wiring-and-tests /tmp/wt
```

The `wiring-and-tests` rename lands as an untracked `export.py`, so it
also checks that the default scope picks up untracked files.

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

## wiring-and-tests/diff.patch

Covers the non-function cases:

1. **`app.py`**: `@require_admin` removed from `GET /admin/export`
   (wiring change: the export is now public), plus a new `GET /health` route.
2. **`tests/test_export.py`**: `== 403` loosened to `in (200, 403)`,
   which makes the test pass despite the missing admin check.
3. **`utils/csv_tools.py` → `export.py`**: moved verbatim.
4. **`requirements.lock`**: lockfile bump.

**Passing run:**

- The Calls graph shows the route → `@require_admin` → handler path as
  removed and a direct route → handler edge as new, with a ⚠ doubt about
  the lost auth. `GET /health` shows as added.
- `app.py` and `export.py` nodes sit in separate lanes.
- The weakened assertion appears as a Tests row with a ⚠ doubt.
- The move is one `(moved)` line, not a delete plus an add.
- The lockfile is counted as excluded, not charted, and left out of the
  file and +/− totals.

[`example-report.html`](wiring-and-tests/example-report.html) is a
reference render.
