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

**Passing run:** invoke the skill against this diff (e.g. apply it to a
scratch repo, or hand the patch to a test agent). The skill passes if the
compiled artifact has two separate intent chunk sections — not one blob,
not per-file — and the independent checks surface both planted issues,
marked directly on each chunk's diagram (capped at three ranked doubts
each). Exact wording and diagram choice will vary between runs; the two
issues being caught, and visibly anchored to the code that causes them, is
the bar.
