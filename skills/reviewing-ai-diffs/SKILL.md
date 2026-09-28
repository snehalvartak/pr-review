---
name: reviewing-ai-diffs
description: Use when reviewing AI-generated code changes (a diff, working tree changes, or a branch) and the reviewer needs to see quickly how control flow changed — new branches, loops, early returns, removed error paths, changed call contracts — rather than read an explanation of the diff.
---

# Reviewing AI Diffs

## Overview

The reviewer already has the diff. What they lack is the *shape* change:
which paths through the code are new, which are gone, and where a caller's
assumptions just broke. This skill renders that as one page of delta
flowcharts — before and after merged into a single graph, color-coded —
with independently-found doubts pinned to the nodes that cause them.

**Visuals, not prose.** No summaries, no "why", no restated diff hunks.
Every word on the page is a node label, a file:line, or a ≤10-word doubt.

## Scope

- Default: `git diff HEAD` (staged + unstaged).
- `branch`: current branch vs. its merge-base with the default branch.
- `<commit-range>`: that range.

Empty diff → say so, stop.

## Process

### 1. Classify every changed function

From `git diff`, list each changed function/method. For each, read its
**full before and after source** (`git show <base>:<path>` and the working
file) — never draw from the hunk alone. Put it in exactly one bucket:

| Bucket | Test | Rendered as |
|---|---|---|
| **Flow** | Branches, loops, returns, raises/throws, try/catch, awaits, or calls added/removed/reordered | Delta flowchart |
| **Value** | Same flow; an expression, constant, default arg, or signature changed | One table row: old → new |
| **Rest** | Formatting, renames, comments, imports, tests, config, docs | One line: path +a −d |

New functions are **Flow** (all nodes `add`) unless they're straight-line.
Deleted functions: one `del` node in the call graph, no flowchart.

### 2. Find callers

For every Flow/Value function whose return values, raised errors, params,
or side effects changed, grep its call sites. These feed the call graph and
the independent check.

### 3. Independent check — all functions in parallel

One subagent per Flow/Value function (batch trivial ones), dispatched at
once. Give it only: before source, after source, call sites. **Not** the
conversation, the intent, or your flowchart — independence is the point.

Ask it to return doubts only, each as `L<line> | ≤10 words`, max 3, ranked
by impact, or `clean`. Correctness only: edge cases, error paths,
off-by-one, null/None, contract breaks at call sites, concurrency. No style.

### 4. Draw

Copy `template.html` (next to this file) and fill it in. Delete sections
that would be empty.

**Delta flowchart** (one per Flow function, `flowchart TD`): a single graph
that is the *union* of before and after.

| Element | Syntax |
|---|---|
| Node unchanged | `A["label · L12"]` |
| Node added | `A["label · L12"]:::add` |
| Node removed | `A["label"]:::del` (no line — it's gone) |
| Node changed in place | `A["new label · L12"]:::mod` |
| Edge unchanged / added / removed | `-->` / `==>` / `-.-x` |
| Branch condition | `A{"cond"}` — ≤3 words, diamonds grow fast |
| Entry / exit | `A(["name(args)"])` / `A(["return x · L20"])` |

Rules:
- Every surviving node carries its after-file line number — this is how
  the reader jumps to the diff, and how a wrong graph gets caught.
- Labels ≤5 words, code-ish (`raise_for_status`, `retry ≤3`), no sentences.
- Show removed exits explicitly (`raise to caller`, `return 404`) — a
  vanished error path is the most-missed change in AI diffs.
- ≤15 nodes. Collapse untouched stretches into one node: `["… 8 lines"]`.
- Append `⚠n` to the label of the node each doubt anchors to; list the
  doubt text under the graph.
- HTML-escape `<`, `>`, `&` inside labels.

**Call graph** (`flowchart LR`, only if any changed function has callers):
changed functions + direct callers. Color changed functions by bucket
(`mod`, or `add`/`del`). Label a caller edge only when its contract
changed: `C -->|"may get None ⚠"| F`.

**Order**: Flow sections by ⚠ count desc, then by node delta. Chips in the
header follow the same order and include Value rows.

### 5. Publish

Load `artifact-design` (required by the Artifact tool; the template already
follows its contract). Publish via the `Artifact` tool with `icon: "flow"`.
No Artifact tool available → write the file into the repo's scratch/temp
dir and give the path.

Chat reply: the link and one line — `N flows · M value changes · K ⚠`.
Nothing else.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Drawing before and after as two graphs | One merged graph; color carries the delta |
| Drawing from the hunk | Read full before/after source; hunks hide the surrounding branches |
| Flowchart for a one-expression change | That's a Value row |
| Missing the removed error path | Draw the old exit as a `del` node with a `-.-x` edge |
| Nodes without line numbers | Every surviving node gets `· L<n>` |
| Adding a summary, "why", or diff excerpt | The reader has git; the page is graphs, rows, and ⚠ lines only |
| Giving the subagent intent or your graph | Before/after source + callers only |
| Doubts phrased as confirmed bugs, or >3 per function | ≤3, ranked, ≤10 words, stated as doubts |
| Narrating the report in chat | Link + one count line |
