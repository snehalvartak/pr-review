---
name: reviewing-ai-diffs
description: Use when reviewing AI-generated code changes (a diff, working tree changes, or a branch) and the size or unfamiliarity of the change makes it hard to spot subtly-wrong-but-plausible-looking code, or when a diff spans multiple files/concerns and reviewing it all at once would be overwhelming.
---

# Reviewing AI Diffs

## Overview

AI-written code lacks the "why" a human author carries in their head, and
large diffs compound that into overload. This skill splits a diff into
intent-grouped chunks, has each independently pre-screened by a subagent,
and compiles the result into a single visual artifact — one small diagram
per chunk, doubts marked in place — so you read it at your own pace
instead of being walked through a chat Q&A.

## When to Use

- Reviewing a diff (working tree, branch, or commit range) that an AI
  assistant produced, before committing/merging it.
- The diff spans multiple files or concerns, or you don't have full context
  on why each part was written.

Not for: style or over-engineering review, or spec-vs-standards review of a
finished PR — use a dedicated review skill for those if you have one. This
skill produces a report to read, not a turn-by-turn chat walkthrough — it
doesn't ask you to approve, flag, or fix chunks as it goes; any resulting
code changes are a separate step you take afterward.

## Scope

Default: diff of working tree against `HEAD` (`git diff HEAD`) — staged and
unstaged combined.

- `reviewing-ai-diffs branch` — diff current branch against its base (e.g. `main`).
- `reviewing-ai-diffs <commit-range or description>` — user-specified scope.
- `reviewing-ai-diffs risk-first` (combinable with the above) — compile
  chunks riskiest-first instead of the intent-order default.

If the diff is empty, say so and stop. Don't proceed to chunking.

## The Process

### 1. Split the diff into intent chunks

One chunk = one coherent piece of work (e.g. "added retry logic to the
fetch client"), even if it spans multiple files. Never chunk by file — that
reintroduces the overload the skill exists to prevent. If a single intent
still exceeds roughly a screenful (~150 changed lines or ~5 files), split
it into sub-chunks under the same intent — a chunk the reader can't scan in
one look defeats the point.

Intent source, in priority order:
1. A plan/spec doc for the work, a linked issue, or recent commit messages
   — use to label and group the chunks. Treat this as the author's claimed
   intent, not verified fact, even as the top-priority source: it can be
   the same AI's own narrative about the diff under review. Check it
   against the diff itself — if a chunk's actual changes go beyond what the
   source describes, chunk by what the diff does, not by what the source
   claims, and carry the gap into step 3 as a doubt.
2. Otherwise, infer intent from the diff itself, and state the inferred
   intent explicitly in the chunk (see step 3) so it's clear it's a guess.

Either way, the stated intent orients the reader — it never substitutes for
the independent check in step 2, and a match between stated intent and
actual behavior is never grounds on its own for treating a chunk as
acceptable. Intent (this step), the diff, and the independent findings
(step 2) are three separate things the compiled artifact (step 3) keeps
visually distinct; the reader forms the acceptance decision after reading
all three, not this skill.

Tag each chunk with a risk category, e.g. `core-logic` / `data-mutation` /
`auth` (high) vs. `boilerplate` / `formatting` / `tests` (low) — these are
illustrative, not an exhaustive list; use whatever label fits the change.

Order the chunks intent-order by default (mirrors how a human would
narrate a PR), or risk-first if named at invocation. No question to ask
here — the invocation argument is the only override.

### 2. Independent check, dispatched in parallel for every chunk

For each chunk, dispatch a subagent with the chunk's diff, its surrounding
code, and the **call sites of any changed functions** (grep for callers —
contract changes like a new `None` return or flipped indexing only show up
at the callers). Give it nothing else: not the conversation history, not
the stated intent, not why the code was written. This independence is the
point — a subagent with no stake in the code being right, and no exposure
to the narrative that justified it, catches what a same-context re-read
misses. Its answer to "what does this code appear to do" is reconstructed
from the code and its callers alone, never inherited from the authoring
agent's account of it — that's what makes the comparison against stated
intent in step 3 a real check instead of the same story read back.

Dispatch every chunk's check at once, in parallel — there's no chat pacing
to hide latency behind, so there's no reason to serialize them. Chunks
whose risk tag is formatting- or boilerplate-only may share one batched
check instead of one each.

Ask each subagent to return two things:
1. **What the code appears to do**, in its own words. Compare this against
   the chunk's stated intent when compiling — a mismatch between apparent
   behavior and stated intent is itself a top-ranked doubt.
2. **Concrete doubts**, each anchored to a specific line, call, or node —
   edge cases, error/null handling, off-by-one, contract changes visible
   at call sites — or an explicit "no issues found". Never a rubber stamp.
   The anchor is what lets a doubt be marked directly on the chunk's
   diagram in step 3 instead of relayed as a separate sentence.

### 3. Compile the artifact

One Artifact, built once all checks are back — not assembled incrementally,
since there's no per-chunk pause to redeploy between.

Open with an overview strip: one line per chunk — name, risk tag, doubt
count — in the order chosen in step 1. This is the whole diff's shape at a
glance, before any per-chunk detail.

Then, for each chunk, in that same order:

- **Header**: name + risk tag.
- **Why**, only if the intent isn't obvious from the header and diagram
  alone. State it as a claim, not a confirmed fact, whichever source it
  came from — mark "(inferred)" when guessed from the diff, or "(as
  stated)" when sourced from a plan/issue/commit message, so the reader
  never mistakes either for something this skill has verified. Skip it
  when the diagram already makes intent self-evident.
- **One diagram** — never more than one — sized to the smallest shape that
  captures what actually changed:

  | Change shape | Diagram |
  |---|---|
  | Control/data flow (retry logic, auth check, request handling) | `mermaid` sequence diagram, or pseudocode |
  | New or changed call path | Call-tree sketch |
  | File layout, structural/module reorg | File tree |
  | UI/component structure | Component tree |
  | Mostly-new block the reader needs verbatim/copyable | Plain code excerpt (not the full raw diff) |
  | Nothing above fits (e.g. a single constant/config value) | 2-4 concise prose bullets — the fallback, not the default |

  When most of the surrounding shape already existed before this chunk and
  only part of it changed, render that same diagram as a `diff` (only the
  changed lines/nodes marked, `+`/`-`, rest of the shape implied) instead
  of redrawing the whole thing — a one-line arithmetic fix inside an
  unchanged function is a two-line diff snippet, not a full pseudocode
  block. Show the whole shape, undiffed, only when most of it is new.
- The chunk's actual diff hunk(s), GitHub-style line coloring
  (added/removed), placed next to the diagram — the diagram is for fast
  scanning, the hunk is the ground truth underneath it; never collect the
  diff separately from the explanation.
- The subagent's doubts, marked directly on the diagram at the anchor from
  step 2 — an inline `⚠` note on the relevant line, node, or edge — instead
  of a separate "Worth checking" list. Cap at the three most material
  doubts, ranked: relaying every doubt recreates the overload this skill
  exists to prevent. An intent-vs-apparent-behavior mismatch always makes
  the cut; style-level nits never do (out of scope here). If doubts were
  cut by the cap, add one line: "…and N lower-priority doubts." If the
  subagent found nothing, add no markers and add one line instead:
  "Independent check: clean."

Load the `artifact-design` skill (bundled with Claude Code/claude.ai, not
part of this repo — it's the same skill the `Artifact` tool itself asks
callers to load) before building it.

### 4. Publish and hand off

Publish the Artifact and share the link in chat with one short line — total
chunks, how many carry doubts — not a per-chunk narration of what's
already on the page. The skill's job ends here: no wrap-up, no follow-up
questions, no tracking of what gets fixed. Reading the artifact and acting
on it is a separate step the reader takes on their own.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Chunking by file instead of by intent | Group by what changed *together for a reason*, even across files |
| Trusting a plan/spec/commit message's account of a chunk's scope over the diff itself | It can be the authoring AI's own narrative about its own diff — chunk by what the diff actually does, flag the gap as a doubt if the two disagree |
| Letting a stated-intent-vs-behavior match read as "this chunk passed" | It's one data point for the reader, not a verdict — this skill never decides acceptability, only surfaces intent, diff, and independent findings side by side |
| Skipping the independent subagent check to save time | It's the step that catches plausible-but-wrong code; the artifact's value collapses without it |
| Dispatching chunk checks one at a time | Dispatch all of them in parallel — nothing paces them anymore |
| Subagent's doubts stated as confirmed bugs | Mark as a doubt on the diagram, not a confirmed bug — the subagent can be wrong too |
| Marking every subagent doubt on the diagram | Three most material, ranked — a wall of markers is its own overload |
| Giving the subagent only the diff hunk, no callers | Contract changes (new `None` return, flipped indexing) are invisible without call sites |
| Defaulting to prose bullets for a chunk | Prose is the fallback only when no diagram shape fits — pick the smallest matching diagram first |
| Stacking more than one diagram for a single chunk | Pick one shape — the point is the smallest fitting view, not full coverage |
| Writing a Why line when the diagram already makes intent obvious | Skip it — only state Why when it's non-obvious or inferred |
| Showing the diagram without the actual diff hunk next to it | The diagram is for scanning, not a replacement for the real code — keep both, anchored together |
| Narrating chunks in chat while or after building the artifact | One short line with the link and a count — the artifact is the content, chat isn't a second copy of it |
| Asking whether to build the artifact, or waiting for per-chunk approval before continuing | Neither exists anymore — always build the artifact, compile every chunk, publish once |
