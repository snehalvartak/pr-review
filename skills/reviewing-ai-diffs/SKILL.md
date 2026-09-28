---
name: reviewing-ai-diffs
description: Use when reviewing AI-generated code changes (a diff, working tree changes, or a branch) and the reviewer needs to see quickly how control flow changed — new branches, loops, early returns, removed error paths, changed call contracts, rewired routes or handlers, weakened tests — rather than read an explanation of the diff.
---

# Reviewing AI Diffs

## Overview

The reviewer already has the diff. What they lack is the *shape* change:
which paths through the code are new, which are gone, and where a caller's
assumptions just broke. This skill renders that as one page of delta
diagrams — before and after merged into a single graph, color-coded —
with independently-found doubts pinned to the nodes that cause them.

**Visuals, not prose.** No summaries, no "why", no restated diff hunks.
Every word on the page is a node label, a file:line, or a ≤10-word doubt.

## Scope

- Default: `git diff HEAD` (staged + unstaged).
- `branch`: current branch vs. its merge-base with the default branch.
- `<commit-range>`: that range.

Empty diff → say so, stop.

## Process

### 1. Filter

Drop from everything below, and count as "excluded" in the header:
lockfiles, vendored deps, minified/bundled output, binaries, and generated
files (a `generated`/`do not edit` header, `*.pb.*`, `*_gen.*`,
snapshots, `dist/`/`build/`).

### 2. Detect moves

Run `git diff -M -C --color-moved=zebra` over the same scope. Code that
was moved (renamed file, function relocated, helper extracted) is **one**
change, not a delete plus an add:

- Moved unchanged → a Rest line: `a.py:fn → b.py:fn (moved)`.
- Moved and edited → classify it as below, diffing against the *old*
  body; header gets `moved from a.py:10`.
- Extracted helper → the parent's chart shows the call as a `mod` node
  `helper() · L40`; the helper gets its own chart only if its body is
  not a verbatim move.

### 3. Classify every change

For each changed function/method, read its **full before and after
source** (`git show <base>:<path>` and the working file) — never draw from
the hunk alone. Put each change in exactly one bucket:

| Bucket | Test | Rendered as |
|---|---|---|
| **Flow** | Branches, loops, returns, raises/throws, try/catch, awaits, or calls added/removed/reordered | Delta flowchart |
| **Interaction** | The changed flow crosses a component boundary (HTTP client ↔ handler, producer ↔ consumer, emit ↔ listener) or its correctness depends on ordering/concurrency (awaits, locks, parallel tasks, retries across a call) | Delta sequence diagram |
| **Wiring** | Code outside functions that changes *what runs*: route/handler tables, middleware or decorator registration, DI bindings, feature flags, cron/queue subscriptions, exported entry points | Nodes and edges in the Calls graph |
| **Value** | Same flow; an expression, constant, default arg, config value, or signature changed | One row: old → new |
| **Tests** | Test files | Rows for weakened assertions only (see below) |
| **Rest** | Formatting, renames, comments, imports, docs, pure moves | One line: path +a −d |

New functions are **Flow** (all nodes `add`) unless straight-line.
Deleted functions: one `del` node in the Calls graph, no chart.

**Tests** — list only changes that make a test able to pass where it
previously couldn't. AI edits do this to get green:
- assertion deleted, or made looser (`==` → `in`/`>=`, exact → `ANY`, `assertRaises` removed)
- expected value changed (flag ⚠ if the new value merely matches the changed code)
- test skipped, xfail'd, commented out, or its setup mocks out the code under test
- `try/except` or `catch` wrapped around the call under test

New tests and strengthened assertions → one Rest line for the file.

### 4. Find callers

For every Flow/Interaction/Value function whose return values, raised
errors, params, or side effects changed, grep its call sites. These feed
the Calls graph and the independent check.

### 5. Independent check — all at once, in parallel

One subagent per Flow/Interaction/Value/Wiring item (batch trivial ones),
plus one for all Tests rows. Give it only: before source, after source,
call sites (for Tests: the old and new test plus the code under test).
**Not** the conversation, the intent, or your diagram — independence is
the point.

Ask it to return doubts only, each as `L<line> | ≤10 words`, max 3, ranked
by impact, or `clean`. Correctness only: edge cases, error paths,
off-by-one, null/None, contract breaks at call sites, ordering/races,
tests that no longer test anything. No style.

### 6. Draw

Copy `template.html` (next to this file) and fill it in. Delete sections
that would be empty.

**Delta flowchart** (Flow; `flowchart TD`): a single graph that is the
*union* of before and after.

| Element | Syntax |
|---|---|
| Node unchanged | `A["label · L12"]` |
| Node added | `A["label · L12"]:::add` |
| Node removed | `A["label"]:::del` (no line — it's gone) |
| Node changed in place | `A["new label · L12"]:::mod` |
| Edge unchanged / added / removed | `-->` / `==>` / `-.-x` |
| Branch condition | `A{"cond"}` — ≤3 words, diamonds grow fast |
| Entry / exit | `A(["name(args)"])` / `A(["return x · L20"])` |

**Delta sequence diagram** (Interaction; `sequenceDiagram`): participants
are components (functions, services, queues), not lines of code.

| Element | Syntax |
|---|---|
| Message unchanged | `A->>B: label · L12` |
| Message added | wrap in `rect rgba(46,160,67,0.15)` … `end` |
| Message removed | `A--xB: ✗ label` wrapped in `rect rgba(248,81,73,0.12)` … `end` |
| Concurrency | `par` / `and` / `end` blocks; `loop`, `alt`, `opt` as needed |

Rules for both:
- Every surviving node/message carries its after-file line number — this
  is how the reader jumps to the diff, and how a wrong graph gets caught.
- Labels ≤5 words, code-ish (`raise_for_status`, `retry ≤3`), no sentences.
- Show removed exits explicitly (`raise to caller`, `return 404`) — a
  vanished error path is the most-missed change in AI diffs.
- ≤15 nodes/messages. Collapse untouched stretches: `["… 8 lines"]`.
- Append `⚠n` to the label each doubt anchors to; list doubt text under
  the diagram.
- HTML-escape `<`, `>`, `&` inside labels.

**Calls graph** (`flowchart LR`; include if any changed function has
callers or any Wiring changed): changed functions, their direct callers,
and Wiring entry points as stadium nodes (`R(["GET /orders"])`,
`F(["flag new_checkout"])`, `M(["auth middleware"])`). Color by delta as
above; a removed registration is a `del` node or `-.-x` edge. Label a
caller edge only when its contract changed: `C -->|"may get None ⚠"| F`.

**Large diffs**: full diagrams for at most **8** Flow/Interaction items —
the top 8 by ⚠ count, then by node delta. The rest go in the "More flows"
table as one row each (fn, file:line, nodes +a −d, ⚠ text). Every item
still gets its independent check.

**Order**: diagram sections by ⚠ count desc, then node delta. Header chips
follow the same order and include Value and Tests rows with ⚠.

### 7. Publish

Load `artifact-design` (required by the Artifact tool; the template already
follows its contract). Publish via the `Artifact` tool with `icon: "flow"`.
No Artifact tool available → write the file into the repo's scratch/temp
dir and give the path.

Chat reply: the link and one line —
`N flows · M value changes · T test rows · K ⚠`. Nothing else.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Drawing before and after as two graphs | One merged graph; color carries the delta |
| Drawing from the hunk | Read full before/after source; hunks hide the surrounding branches |
| Flowchart for a one-expression change | That's a Value row |
| Missing the removed error path | Draw the old exit as a `del` node with a `-.-x` edge |
| Nodes without line numbers | Every surviving node gets `· L<n>` |
| Route/flag/middleware change filed under Rest | That's Wiring — it changes what runs; put it in the Calls graph |
| Test edits filed under Rest | Weakened assertions, skips, and changed expectations get Tests rows |
| Moved code shown as delete + add | Detect moves first; diff the moved body against its old self |
| Flowchart for a client↔server or producer↔consumer change | Use a sequence diagram |
| 30 full diagrams on one page | Top 8 drawn; the rest are "More flows" rows |
| Charting lockfiles or generated code | Exclude; count them in the header |
| Adding a summary, "why", or diff excerpt | The reader has git; the page is diagrams, rows, and ⚠ lines only |
| Giving the subagent intent or your graph | Before/after source + callers only |
| Doubts phrased as confirmed bugs, or >3 per item | ≤3, ranked, ≤10 words, stated as doubts |
| Narrating the report in chat | Link + one count line |
