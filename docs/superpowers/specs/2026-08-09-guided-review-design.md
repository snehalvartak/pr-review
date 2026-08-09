# Guided Review — Design Spec

Date: 2026-08-09

_Note: shipped as the `reviewing-ai-diffs` skill — "guided-review" below was
the working name during design._

## Problem

Reviewing AI-generated code is harder than reviewing human-written code, even
with rules/skills already in place to constrain how the AI writes it. A human
author knows *why* each line exists; the same code from an AI reads as
unfamiliar and demands more effort to reconstruct intent. This gets worse
with large diffs (too many files/lines to hold in context at once), and it's
specifically hard to catch code that *looks* right but is subtly wrong —
"plausible but wrong" — because the reviewer has no independent signal to
distinguish confident-and-correct from confident-and-mistaken.

## Goals

- Cap cognitive load per review step: never present the whole diff at once.
- Preserve the "why" per change, since that's what's missing from
  AI-generated code relative to human-written code.
- Independently surface "plausible but wrong" code — not just have the
  code's own author (the same AI/context) re-read its own work.
- Fit into an existing review flow (pre-commit, on a diff) without requiring
  a PR or GitHub round-trip.

## Non-goals

- Not a replacement for `/code-review` or `ponytail-review` (style/over-engineering
  focus) — this is about comprehension and correctness under review fatigue.
- Not a CI-gate or automated approval mechanism — it's a human-in-the-loop
  walkthrough; the human always makes the final call.

## Design

### Invocation & scope

Skill name: `guided-review`. Invoked via `/guided-review` or by asking to
review recently generated code.

- Default scope: working tree diff against `HEAD` (staged + unstaged) — the
  common case of reviewing what an AI agent just wrote before committing.
- `/guided-review branch`: diff current branch vs. its base (e.g. `main`) —
  for reviewing work that spans multiple commits/sessions, like a PR.
- `/guided-review <commit-range | description>`: user-specified scope for
  ad-hoc cases.
- If the resulting diff is empty, report that and stop.

### Chunking

The diff is split into **logical chunks by intent**, not by file — one
chunk per coherent piece of work (e.g. "added retry logic to the fetch
client"), which may span multiple files.

Intent source, in priority order:
1. A plan/spec doc for the work (e.g. from `writing-plans`, a linked issue,
   recent commit messages) — used as ground truth.
2. Otherwise, intent is inferred directly from the diff. The inferred intent
   is stated explicitly as part of the chunk presentation so the user can
   correct it if it's wrong.

Each chunk also gets a **risk tag** (e.g. core-logic/data-mutation/auth vs.
boilerplate/formatting/tests), computed independent of ordering choice.

**Ordering**: default is intent order (mirrors how a human would narrate a
PR). At the start of a walkthrough, the user is asked once whether they want
intent order (default) or risk-first order (riskiest chunk first) — not
re-asked per chunk.

### Per-chunk review loop

For each chunk, in sequence:

1. **Independent adversarial check (subagent, before the user sees anything).**
   A fresh subagent receives only the chunk's diff and surrounding code —
   not the conversation history, not the stated "why" narrative — and is
   asked to try to break it: edge cases, error/null handling, off-by-one,
   mismatches between what the code actually does and the stated intent.
   It returns concrete doubts, or an explicit "no issues found." This is
   independent review, not the same context re-reading its own work, since
   self-review is prone to confirming its own assumptions.
2. **Present the chunk** to the user:
   - What changed (concise summary, not a raw diff dump)
   - Why (the intent, from the source above)
   - Risk tag
   - Any doubts the subagent raised, explicitly framed as "worth checking,"
     not as confirmed bugs — the subagent can also be wrong.
3. **User responds** with one of:
   - Approve → move to next chunk.
   - Ask a question → answered using the actual code, chunk re-presented.
   - Flag a concern → recorded, move to next chunk (or fix now, user's choice).
   - Request a fix now → Claude edits, then re-runs the adversarial check on
     the new version before moving on.
4. Advance only after an explicit approve or flag-and-move-on.

### Wrap-up

After the last chunk, produce a short summary:
- Chunks approved as-is.
- Chunks flagged, with the user's note.
- Any subagent doubts raised but never explicitly resolved.

Then offer to immediately fix any flagged/unresolved items, if there are any.

### Presentation format

Everything runs in the Claude Code chat itself — no separate browser/UI
infra, so the finished skill stays portable as a plugin (no dependency on
Superpowers' brainstorming-session server, which is a design-time tool, not
a runtime one).

- **Per-chunk loop:** plain markdown, in a consistent structured template —
  heading (chunk name + risk tag), "What changed" bullets, "Why" line,
  "Worth checking" doubts, a short inline code excerpt (not the raw diff).
  Markdown renders natively in the chat and keeps every chunk scannable in
  the same shape.
- **Wrap-up summary:** markdown by default. If the user wants a persistent
  record afterward, offer to additionally publish it as an HTML Artifact —
  a nicer static page for sharing/revisiting later. This is optional and
  only offered once, after the loop completes, not per-chunk.

## Open questions / future work

- Publishing this as a shareable Claude Code plugin on GitHub (stated goal,
  not part of this iteration — this spec covers the skill's behavior; a
  follow-up covers packaging/distribution as a plugin).
- Whether "risk-first" ordering should also support automatically switching
  mid-walkthrough if the user changes their mind (currently: asked once, up front).
