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
   intent explicitly in the chunk (see step 3) so the user can correct it
   if it's wrong.

Tag each chunk with a risk category, e.g. `core-logic` / `data-mutation` /
`auth` (high) vs. `boilerplate` / `formatting` / `tests` (low) — these are
illustrative, not an exhaustive list; use whatever label fits the change.
Compute the risk tag independent of which ordering the user picks next, so
the tag isn't biased by the order chosen.

Ask the user once, before the first chunk, two things — real questions
requiring real answers; wait for both before presenting chunk 1, even if
the user is in a hurry. Noting a default and moving on without waiting is
the same mistake as skipping the question outright. Don't re-ask either
per chunk.

1. Review in **intent order** (default — mirrors how a human would narrate
   a PR) or **risk-first** (riskiest chunk first)? Skip this one only if
   the user already named an ordering when invoking (e.g.
   `reviewing-ai-diffs risk-first`).
2. Want a **live companion Artifact** — a diff-annotated page, updated
   after every chunk as the review happens — alongside this chat, or just
   the chat? Default: chat only. See step 5 for what the companion looks
   like and why it has to start now, not at wrap-up, to be worth anything.

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
2. **Concrete doubts**, each anchored to a specific line, call, or node —
   edge cases, error/null handling, off-by-one, contract changes visible
   at call sites — or an explicit "no issues found". Never a rubber stamp.
   The anchor is what lets a doubt be marked directly on the chunk's
   diagram in step 3 instead of relayed as a separate sentence.

Chunks whose risk tag is formatting- or boilerplate-only may share one
batched check (a single subagent covering all of them); every other chunk
gets its own dedicated check.

While the user reads the current chunk, you may pre-dispatch the next
chunk's check in the background to cut waiting between chunks; discard and
re-run it if a fix-now edit touched that chunk's files.

### 3. Present the chunk

Every chunk opens with the same one-line header — consistent shape keeps
each one fast to scan regardless of how deep into the diff you are:

```markdown
## Chunk N: <short name> — risk: <risk tag>
```

Add a **Why** line only if the intent isn't obvious from the header and
diagram alone, or if it's inferred rather than sourced — mark
"(inferred)" so the user can correct it. Skip it when the diagram already
makes the intent self-evident; restating the obvious is exactly the kind
of reading that adds up across chunks without adding signal.

Then **one diagram** — never more than one — sized to the smallest shape
that captures what actually changed:

| Change shape | Diagram |
|---|---|
| Control/data flow (retry logic, auth check, request handling) | `mermaid` sequence diagram, or pseudocode |
| New or changed call path | Call-tree sketch |
| File layout, structural/module reorg | File tree |
| UI/component structure | Component tree |
| Mostly-new block the user needs verbatim/copyable | Plain code excerpt (not the full raw diff) |
| Nothing above fits (e.g. a single constant/config value) | 2-4 concise prose bullets — the fallback, not the default |

When most of the surrounding shape already existed before this chunk and
only part of it changed, render that same diagram as a `diff` (only the
changed lines/nodes marked, `+`/`-`, rest of the shape implied) instead of
redrawing the whole thing — a one-line arithmetic fix inside an unchanged
function is a two-line diff snippet, not a full pseudocode block. Show the
whole shape, undiffed, only when most of it is new.

Mark the subagent's doubts directly on the diagram, at the anchor from
step 2 — an inline `⚠` note on the relevant line, node, or edge — instead
of a separate "Worth checking" list. Cap at the three most material
doubts, ranked: relaying every doubt the subagent raised recreates the
overload this skill exists to prevent. An intent-vs-apparent-behavior
mismatch always makes the cut; style-level nits never do (out of scope
here). If doubts were cut by the cap, add one line below the diagram:
"…and N lower-priority doubts — ask to see them." If the subagent found
nothing, add no markers and end with one line — "Independent check:
clean." — not a padded bullet list.

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

If the companion Artifact was requested (step 1), redeploy it now too —
right after the chunk is finalized, not while it's still being discussed,
so it never shows a verdict that's still in flux. Append this chunk's
section (see step 5 for the shape) to whatever the Artifact already has
from earlier chunks; don't rebuild it from scratch each time. Share the
link the first time it's published, then stay quiet about it — it's a
side channel the user can check whenever they want, not something to
narrate every chunk.

### 5. Wrap up

After the last chunk, summarize from the state file:
- Chunks approved as-is.
- Chunks flagged, with the user's note.
- Chunks marked `stale` (approved, then touched by a later fix) — these
  need a re-look before merge.
- Subagent doubts raised but never resolved.

Delete the state file — the review is done. Offer to fix any
flagged/unresolved items immediately.

If a companion Artifact has been running since step 1, this is its last
update, not its first build: prepend the roll-up (chunks approved, chunks
flagged with notes, chunks marked `stale`, doubts never resolved) above
the per-chunk sections that were already published, and redeploy once
more. If the user skipped the companion at step 1 and only wants a record
now, offer once to build one retroactively from the state file — but say
plainly that it's a wrap-up document at that point, not something that
helped while reviewing; that's what step 1's question is for next time.

Either way, the Artifact is a diff-annotated walkthrough, not prose about
one: for each chunk, in the order it was reviewed, its diff hunk(s) with
GitHub-style line coloring (added/removed) sit next to the same diagram
and Why line (if shown) used to present that chunk in chat, doubts marked
in the same place, plus the final verdict — anchored to the same hunk,
never collected separately from the code. Built from diff text and chunk
content already gathered during the loop; no re-fetching or re-analysis.
Load the `artifact-design` skill (bundled with Claude Code/claude.ai, not
part of this repo — it's the same skill the `Artifact` tool itself asks
callers to load) before building or updating it.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Chunking by file instead of by intent | Group by what changed *together for a reason*, even across files |
| Skipping the independent subagent check to save time | It's the step that catches plausible-but-wrong code; the walkthrough's value collapses without it |
| Presenting all chunks in one message | One chunk, one message, wait for the user's response before the next |
| Subagent's doubts stated as confirmed bugs | Mark as a doubt on the diagram, not a confirmed bug — the subagent can be wrong too |
| Marking every subagent doubt on the diagram | Three most material, ranked — a wall of markers is its own overload |
| Giving the subagent only the diff hunk, no callers | Contract changes (new `None` return, flipped indexing) are invisible without call sites |
| Defaulting to prose bullets for a chunk | Prose is the fallback only when no diagram shape fits — pick the smallest matching diagram first |
| Stacking more than one diagram for a single chunk | Pick one shape — the point is the smallest fitting view, not full coverage |
| Writing a Why line when the diagram already makes intent obvious | Skip it — only state Why when it's non-obvious or inferred |
| Asking the ordering or companion-Artifact question but not waiting for an answer (e.g. defaulting and mentioning the alternative as an aside) because the user seems rushed, or re-asking either every chunk | Ask both once, at the start, and wait — "in a hurry" is exactly the pressure this skill is designed to hold up under |
| Building the diff-annotated Artifact as prose with the diff as an afterthought | Anchor each chunk's explanation next to its own diff hunk, styled like a PR view — the diff is the point, not a caption under it |
| Only offering the companion Artifact at wrap-up, after the user already reviewed the whole diff in chat | Ask at step 1, before chunk 1 — an artifact that only exists once the review is over never helped during the review |
