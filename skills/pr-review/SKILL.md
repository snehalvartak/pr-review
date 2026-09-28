---
name: pr-review
description: Use when reviewing AI-generated code changes (a diff, working tree changes, or a branch) and the reviewer needs to see quickly how control flow changed — new branches, loops, early returns, removed error paths, changed call contracts, rewired routes or handlers, weakened tests — rather than read an explanation of the diff.
compatibility: Requires git. Uses subagents and an HTML artifact tool when the agent has them; works without either.
---

# PR Review

## Overview

The reviewer already has the diff. What they lack is the *shape* change:
which paths through the code are new, which are gone, and where a caller's
assumptions just broke. This skill renders that as one page of delta
diagrams — before and after merged into a single graph, color-coded —
with independently-found doubts pinned to the nodes that cause them.

**Visuals, not prose.** No summaries, no "why", no restated diff hunks.
Every word on the page is a node label, a file:line, or a ≤10-word doubt.

## Scope

Run every git command from the repo root (`git rev-parse --show-toplevel`).
Each scope fixes a **base** and a diff command, written `DIFF` below; every
step uses the same `DIFF` so they all see the same files.

- Default: working tree vs `HEAD` — staged, unstaged, **and untracked**
  files (`git diff HEAD` alone silently skips new files). Snapshot the tree
  into a throwaway index; the user's own index is not touched:
  ```sh
  idx=$(git rev-parse --git-path pr-review/index); mkdir -p "${idx%/*}"
  cp "$(git rev-parse --git-path index)" "$idx" 2>/dev/null
  GIT_INDEX_FILE="$idx" git add -A
  ```
  `DIFF` = `GIT_INDEX_FILE="$(git rev-parse --git-path pr-review/index)" git diff --cached HEAD`.
  No commits yet → use the empty tree `4b825dc642cb6eb9a060e54bf8d69288fbee4904`
  in place of `HEAD`.
- `branch`: commits on the current branch. Default branch =
  `git symbolic-ref --short refs/remotes/origin/HEAD`, else `main`, else
  `master`; base = `git merge-base HEAD <default>`;
  `DIFF` = `git diff <base> HEAD`.
- `<commit-range>`: `DIFF` = `git diff <range>`; base = its left side.

Before source is `git show <base>:<path>`; after source is the working
file (default scope) or `git show <right side>:<path>`.

Empty diff, or nothing left after step 1 → say so, stop.

## Process

### 1. Filter

Drop from everything below, and count as "excluded" in the header:
lockfiles, vendored deps, minified/bundled output, binaries, and generated
files (a `generated`/`do not edit` header, `*.pb.*`, `*_gen.*`,
`dist/`/`build/`). **Not** snapshots or golden files — regenerated
expectations are Tests rows (step 3).

If the repo root has `.prreviewignore` (one gitignore-style glob per line;
blank lines and `#` comments skipped; `!` negation unsupported), exclude
those paths too so they are never read: end every `DIFF` with
`-- ':(top,exclude,glob)<pattern>' …` (pathspecs go last, after all
options). Translate each line
first: no `/` → prefix `**/`; leading `/` → drop it; trailing `/` →
append `**`. (`top` anchors the pattern at the repo root; without it,
patterns resolve against the current directory.)

Excluded files are counted, not read, and left out of the header's
file and +/− totals (compare `DIFF --name-only` with and without the
exclusions to get the count).

### 2. Detect moves

A piped `git diff` prints no move markers unless color is forced, so run
the scope's `DIFF` with pinned move colors and turn them into text:

```sh
git -c color.diff.oldMoved='bold magenta' -c color.diff.newMoved='bold cyan' \
  diff -M --color=always --color-moved=plain --color-moved-ws=allow-indentation-change \
  <DIFF revs> [-- <exclusions>] \
  | perl -pe 's/^\e\[1;35m-/-MOVED /; s/^\e\[1;36m\+/+MOVED /; s/\e\[[0-9;]*m//g'
```

(Default scope: keep the `GIT_INDEX_FILE=…` prefix and `--cached`.)
`-MOVED`/`+MOVED` lines are relocated code; `rename from`/`rename to`
headers are moved files. No `-C`: a copy is new code, not a move — the
original still exists. Code that was moved (renamed file, function
relocated, helper extracted) is **one** change, not a delete plus an add:

- Moved unchanged → a Rest line: `a.py:fn → b.py:fn (moved)`.
- Moved and edited → classify it as below, diffing against the *old*
  body; header gets `moved from a.py:10`.
- Extracted helper → the parent's chart shows the call as a `mod` node
  `helper() · L40`; the helper gets its own chart only if its body is
  not a verbatim move.

### 3. Classify every change

For each changed function/method, read its **full before and after
source** (see Scope) — never draw from the hunk alone. Put each change in
exactly one bucket:

| Bucket | Test | Rendered as |
|---|---|---|
| **Flow** | Branches, loops, returns, raises/throws, try/catch, awaits, or calls added/removed/reordered | Delta flowchart |
| **Interaction** | The changed flow crosses a component boundary (HTTP client ↔ handler, producer ↔ consumer, emit ↔ listener) or its correctness depends on ordering/concurrency (awaits, locks, parallel tasks, retries across a call) | Delta sequence diagram |
| **Wiring** | Code outside functions that changes *what runs*: route/handler tables, middleware or decorator registration, DI bindings, feature flags, cron/queue subscriptions, exported entry points | Nodes and edges in the Calls graph |
| **Value** | Same flow; an expression, constant, default arg, config value, or signature changed | One row: old → new |
| **Shape** | A returned object, API request/response, event payload, DB schema, or struct/type gained, lost, renamed, or retyped fields | One row: key diff `+new −old ~retyped` |
| **Tests** | Test files, snapshots, golden files | Rows for weakened assertions only (see below) |
| **Rest** | Formatting, renames, comments, imports, docs, pure moves | One line: path +a −d |

New functions are **Flow** (all nodes `add`) unless straight-line.
Deleted functions: one `del` node in the Calls graph, no chart, plus any
call sites still referencing it.

**Tests** — list only changes that make a test able to pass where it
previously couldn't. AI edits do this to get green:
- assertion deleted, or made looser (`==` → `in`/`>=`, exact → `ANY`, `assertRaises` removed)
- expected value changed (flag ⚠ if the new value merely matches the changed code)
- test skipped, xfail'd, commented out, or its setup mocks out the code under test
- `try/except` or `catch` wrapped around the call under test
- snapshot/golden files regenerated → one row per group
  (`12 .snap files updated`); ⚠ if the code they capture changed in the
  same diff

New tests and strengthened assertions → one Rest line for the file.

### 4. Find callers

For every Flow/Interaction/Value/Shape item whose return values, raised
errors, params, fields, or side effects changed, grep its call sites. These feed
the Calls graph and the independent check.

### 5. Independent check — all at once, in parallel

One subagent per Flow/Interaction/Value/Shape/Wiring item (batch trivial ones),
plus one for all Tests rows. Give it only: before source, after source
with line numbers (`cat -n`), call sites (for Tests: the old and new test
plus the code under test).
**Not** the conversation, the intent, or your diagram — independence is
the point.

No subagent tool (e.g. pi)? Run each check yourself as a separate pass
*before* drawing: read only the before/after source and callers, write the
doubts down, then move on. Weaker than a fresh context, still better than
checking against your own diagram.

Ask it to return doubts only, each as `L<line> | ≤10 words` (`path:line`
when the item spans files, e.g. Wiring), max 3, ranked by impact, or
`clean`. Lines are **after-file** lines; for removed code, cite the
nearest surviving line. Correctness only: edge cases, error paths,
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
| Branch condition | `A{"cond · L8"}` — ≤3 words, diamonds grow fast |
| Entry / exit | `A(["name(args) · L6"])` / `A(["return x · L20"])` |

**Delta sequence diagram** (Interaction; `sequenceDiagram`): participants
are components (functions, services, queues), not lines of code.

| Element | Syntax |
|---|---|
| Message unchanged | `A->>B: label · L12` |
| Message added | wrap in `rect rgba(46,160,67,0.15)` … `end` |
| Message removed | `A--xB: ✗ label` wrapped in `rect rgba(248,81,73,0.12)` … `end` |
| Concurrency | `par` / `and` / `end` blocks; `loop`, `alt`, `opt` as needed |

Rules for both:
- Every surviving node/message carries its after-file line number —
  conditions, entries, and route nodes included. This is how the reader
  jumps to the diff, and how a wrong graph gets caught. Removed nodes
  carry none.
- Labels ≤5 words, code-ish (`raise_for_status`, `retry ≤3`), no sentences.
- Show removed exits explicitly (`raise to caller`, `return 404`) — a
  vanished error path is the most-missed change in AI diffs.
- ≤15 nodes/messages. Collapse untouched stretches: `["… 8 lines"]`.
- Append `⚠n` to the label each doubt anchors to; list doubt text under
  the diagram.
- Node IDs are short and alphanumeric (`n1`, `ret`); never `end`, which
  fails the whole diagram.

**Escape everything you fill in** — code reaches labels, table cells,
doubts, and headings alike: `&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;`
everywhere (unescaped, `List<String>` vanishes as a tag). Inside Mermaid
labels also `"` → `#quot;`; a bare `"` fails the whole diagram.

**Anchor IDs** (`f-…`, `t-…`, `s-…`) are path + name, slugged
(`f-src-api-orders-create`), so same-named functions in different files
(`main`, `__init__`) don't collide.

**Calls graph** (`flowchart LR`; include if any changed function has
callers, any function was deleted, or any Wiring changed; doubts from
Wiring items go under it): changed functions, their direct callers,
and Wiring entry points as stadium nodes (`R(["GET /orders"])`,
`F(["flag new_checkout"])`, `M(["auth middleware"])`). Color by delta as
above; a removed registration is a `del` node or `-.-x` edge. Label a
caller edge only when its contract changed: `C -->|"may get None ⚠"| F`
or `C -->|"loses .total ⚠"| F`. When nodes span 2+ modules, group each
module in a lane: `subgraph api["src/api"]` … `end`, then
`class api,web lane` — lanes only, no nesting.

**Large diffs**: full diagrams for at most **8** Flow/Interaction items —
the top 8 by ⚠ count, then by node delta. The rest go in the "More flows"
table as one row each (fn, file:line, nodes +a −d, ⚠ text). Every item
still gets its independent check.

**Order**: diagram sections by ⚠ count desc, then node delta. Header chips
follow the same order and include Value, Shape, and Tests rows with ⚠;
Wiring chips link to `#calls`.

**Header counts** skip zeros and excluded files:
`N files · +a −d · F flows · R wiring · V value/shape · T tests · ⚠ K · X excluded`.

### 7. Publish

- **Artifact tool available** (Claude Code / claude.ai): load
  `artifact-design` (the tool requires it; the template already follows
  its contract), then publish with `icon: "flow"`.
- **Otherwise** (Cursor, OpenCode, pi, …): prepend
  `<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">`
  (the template has no document skeleton because the Artifact tool adds
  one; without it the page renders in quirks mode with a guessed
  encoding), write it to
  `$(git rev-parse --git-dir)/pr-review/report.html` — inside `.git`, so
  it is never committed — open it (`open` on macOS, `xdg-open` on Linux,
  `start ""` on Windows), and give the path. The page loads Mermaid from
  a CDN when opened locally.

Chat reply: the link and one line —
`F flows · R wiring · V value/shape · T tests · K ⚠`. Nothing else.

## Common Mistakes

| Mistake | Fix |
|---|---|
| `git diff HEAD` for the default scope | It skips untracked files; snapshot into the throwaway index |
| `--color-moved` on piped output | No markers without `--color=always`; use the step 2 pipeline |
| A bare `"` in a Mermaid label, or a node named `end` | `#quot;`; short alphanumeric IDs |
| Drawing before and after as two graphs | One merged graph; color carries the delta |
| Drawing from the hunk | Read full before/after source; hunks hide the surrounding branches |
| Flowchart for a one-expression change | That's a Value row |
| Missing the removed error path | Draw the old exit as a `del` node with a `-.-x` edge |
| Nodes without line numbers | Every surviving node gets `· L<n>` |
| Route/flag/middleware change filed under Rest | That's Wiring — it changes what runs; put it in the Calls graph |
| Test edits filed under Rest, or snapshots excluded as generated | Weakened assertions, skips, and changed expectations (snapshots included) get Tests rows |
| Moved code shown as delete + add | Detect moves first; diff the moved body against its old self |
| Flowchart for a client↔server or producer↔consumer change | Use a sequence diagram |
| 30 full diagrams on one page | Top 8 drawn; the rest are "More flows" rows |
| Charting lockfiles or generated code | Exclude; count them in the header; honor `.prreviewignore` |
| Returned dict/payload keys changed, filed as Value | Shape row with a key diff; label the caller edge with what it loses |
| Adding a summary, "why", or diff excerpt | The reader has git; the page is diagrams, rows, and ⚠ lines only |
| Giving the subagent intent or your graph | Before/after source + callers only |
| Doubts phrased as confirmed bugs, or >3 per item | ≤3, ranked, ≤10 words, stated as doubts |
| Narrating the report in chat | Link + one count line |
