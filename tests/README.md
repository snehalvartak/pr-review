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

## misleading-intent/diff.patch + commit-message.txt

A single-chunk diff (the same `fetch_client.py` retry loop from
`diff-with-bug`) paired with a commit message (`commit-message.txt`) that
undersells what the diff actually does: it claims retries are for
"transient network errors," but the diff retries on every
`requests.RequestException` (including `HTTPError` from 4xx responses,
which aren't transient) and silently returns `None` instead of raising
once retries are exhausted — a contract change the message doesn't
mention at all.

Used to verify the skill doesn't treat the commit message as ground truth
for what the chunk is for: step 1 sources intent from it (it's the
top-priority source), but must not let it define the chunk's scope
uncritically, and step 2's independent check must still find the
retry-non-transient-errors and silent-`None`-return issues without being
handed the commit message at all.

**Passing run:** the compiled artifact's "Why" line for this chunk is
labeled "(as stated)", not presented as verified fact. The
retry-scope-vs-message and silent-contract-change issues both appear as
doubts (the mismatch between stated intent and actual behavior is a
top-ranked doubt per `SKILL.md`), rather than being hidden behind the
commit message's narrower framing. If the skill instead reports this
chunk as simply "adds retry for transient errors" with no doubts, that's
a failing run — it means the authoring agent's account defined the
review instead of orienting it.
