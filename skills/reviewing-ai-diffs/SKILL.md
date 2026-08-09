---
name: reviewing-ai-diffs
description: Use when reviewing AI-generated code changes (a diff, working tree changes, or a branch) and the size or unfamiliarity of the change makes it hard to spot subtly-wrong-but-plausible-looking code, or when a diff spans multiple files/concerns and reviewing it all at once would be overwhelming.
---

# Reviewing AI Diffs

## Overview

AI-written code lacks the "why" a human author carries in their head, and
large diffs compound that into overload. This skill walks a diff one
logical chunk at a time, each pre-screened by an independent subagent
before you see it, so you never face the whole diff at once and get a
second opinion on top of your own.

## When to Use

- Reviewing a diff (working tree, branch, or commit range) that an AI
  assistant produced, before committing/merging it.
- The diff spans multiple files or concerns, or you don't have full context
  on why each part was written.

Not for: style or over-engineering review, or spec-vs-standards review of a
finished PR — use a dedicated review skill for those if you have one. This
skill is about comprehension and catching plausible-but-wrong code under
review fatigue.

## Scope

Default: diff of working tree against `HEAD` (`git diff HEAD`) — staged and
unstaged combined.

- `reviewing-ai-diffs branch` — diff current branch against its base (e.g. `main`).
- `reviewing-ai-diffs <commit-range or description>` — user-specified scope.

If the diff is empty, say so and stop. Don't proceed to chunking.

If a state file from an interrupted review exists (see step 4) and its
first line matches the current scope and diff hash, offer to resume — skip
chunks already approved, re-present the rest. If the first line doesn't
match, it's leftover from a different review — delete it and start fresh.

## The Loop

### 1. Split the diff into intent chunks

One chunk = one coherent piece of work (e.g. "added retry logic to the
fetch client"), even if it spans multiple files. Never chunk by file — that
reintroduces the overload the skill exists to prevent. If a single intent
still exceeds roughly a screenful (~150 changed lines or ~5 files), split
it into sub-chunks under the same intent — a chunk the user can't scan in
one look defeats the point.

Intent source, in priority order:
1. A plan/spec doc for the work, a linked issue, or recent commit messages
   — use as ground truth for what each chunk is for.
2. Otherwise, infer intent from the diff itself, and state the inferred
   intent explicitly in the chunk (see template below) so the user can
   correct it if it's wrong.

Tag each chunk with a risk category, e.g. `core-logic` / `data-mutation` /
`auth` (high) vs. `boilerplate` / `formatting` / `tests` (low) — these are
illustrative, not an exhaustive list; use whatever label fits the change.
Compute the risk tag independent of which ordering the user picks next, so
the tag isn't biased by the order chosen.

Ask the user once, before the first chunk: review in **intent order**
(default — mirrors how a human would narrate a PR) or **risk-first**
(riskiest chunk first)? This is a real question requiring a real answer —
wait for it before presenting chunk 1, even if the user is in a hurry.
Noting the default and moving on without waiting is the same mistake as
skipping the question outright. Don't re-ask per chunk. Skip the question
only if the user already named an ordering when invoking (e.g.
`reviewing-ai-diffs risk-first`).

### 2. Independent check, before showing the user anything

For each chunk, dispatch a subagent with the chunk's diff, its surrounding
code, and the **call sites of any changed functions** (grep for callers —
contract changes like a new `None` return or flipped indexing only show up
at the callers). Give it nothing else: not the conversation history, not
the stated intent, not why the code was written. This independence is the
point — a subagent with no stake in the code being right, and no exposure
to the narrative that justified it, catches what a same-context re-read
misses.

Ask it to return two things:
1. **What the code appears to do**, in its own words. Back in the main
   loop, compare this against the chunk's "Why" — a mismatch between
   apparent behavior and stated intent is itself a top-ranked doubt.
2. **Concrete doubts** — edge cases, error/null handling, off-by-one,
   contract changes visible at call sites — or an explicit "no issues
   found". Never a rubber stamp.

Chunks whose risk tag is formatting- or boilerplate-only may share one
batched check (a single subagent covering all of them); every other chunk
gets its own dedicated check.

While the user reads the current chunk, you may pre-dispatch the next
chunk's check in the background to cut waiting between chunks; discard and
re-run it if a fix-now edit touched that chunk's files.

### 3. Present the chunk

Use this template for every chunk — consistent shape keeps each one fast to
scan regardless of how deep into the diff you are:

```markdown
## Chunk N: <short name> — risk: <risk tag>

**What changed:** <2-4 bullets, concise, not a raw diff dump>

**Why:** <the intent — from the plan/commits, or "(inferred)" if guessed>

**Worth checking:** <subagent's doubts, phrased as questions to verify, not
as confirmed bugs — or "Independent check found nothing." if clean>

<short inline code excerpt only if it helps, not the full diff>
```

Cap **Worth checking** at the three most material doubts, ranked — relaying
every doubt the subagent raised recreates the overload this skill exists to
prevent. An intent-vs-apparent-behavior mismatch always makes the cut;
style-level nits never do (out of scope here). If real doubts were cut by
the cap, end the list with "…and N lower-priority doubts — ask to see them."

### 4. Take the user's response

One of:
- **Approve** → move to next chunk.
- **Ask a question** → answer using the actual code, re-present the chunk.
- **Correct the why** → the inferred intent was wrong; update it, re-rank
  the doubts against the corrected intent (a mismatch doubt may dissolve —
  or a new one may appear), re-present.
- **Flag a concern** → record it, then move to next chunk (or fix now).
- **Fix now** → edit the code, re-run the independent check (step 2) on the
  new version, then re-present before moving on. If the edit also touched
  files from an already-approved chunk, mark that chunk `stale` in the
  state file — it resurfaces in the wrap-up.

Advance only on an explicit approve or flag-and-move-on — never auto-advance.

Keep a state file at `$(git rev-parse --git-dir)/review-state.md` — always
outside the working tree (a path inside it would pollute the very diff
under review), and correct even in worktrees where `.git` is a file. Its
first line is the scope plus a hash of the diff (e.g.
`git diff HEAD | shasum`), which is what makes resume detection safe. After
each verdict, append one line: chunk name, verdict, any note. This is what
makes an interrupted review resumable and feeds the wrap-up.

### 5. Wrap up

After the last chunk, summarize from the state file:
- Chunks approved as-is.
- Chunks flagged, with the user's note.
- Chunks marked `stale` (approved, then touched by a later fix) — these
  need a re-look before merge.
- Subagent doubts raised but never resolved.

Delete the state file — the review is done. Offer to fix any
flagged/unresolved items immediately. Then offer — once,
not per-chunk — to publish the summary as an HTML Artifact if the user wants
a persistent record; otherwise the markdown summary in chat is the whole
deliverable.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Chunking by file instead of by intent | Group by what changed *together for a reason*, even across files |
| Skipping the independent subagent check to save time | It's the step that catches plausible-but-wrong code; the walkthrough's value collapses without it |
| Presenting all chunks in one message | One chunk, one message, wait for the user's response before the next |
| Subagent's doubts stated as confirmed bugs | Frame as "worth checking" — the subagent can be wrong too |
| Relaying every subagent doubt verbatim | Three most material, ranked — a wall of maybes is its own overload |
| Giving the subagent only the diff hunk, no callers | Contract changes (new `None` return, flipped indexing) are invisible without call sites |
| Asking the ordering question but not waiting for an answer (e.g. defaulting and mentioning the alternative as an aside) because the user seems rushed, or re-asking it every chunk | Ask once, at the start, and wait — "in a hurry" is exactly the pressure this skill is designed to hold up under |
