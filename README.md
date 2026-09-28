# pr-review

An [Agent Skill](https://agentskills.io) for Claude Code, Cursor, OpenCode,
and pi that turns an AI-generated diff into control-flow
pictures, not more text to read.

You can already see the diff in git. What's hard to see is how the *paths*
through the code changed: a new retry loop, an error that used to propagate
and is now swallowed, a caller that can suddenly get `None`. This skill
draws each changed function as one merged before/after flowchart
(added = green, removed = dashed red, changed = amber), pins independently
found doubts to the nodes that cause them, and keeps prose to a minimum.

![example](tests/diff-with-bug/example-report.png)

## Install

| Agent | Install | Run |
|---|---|---|
| Claude Code | `claude plugin marketplace add snehalvartak/pr-review`<br>`claude plugin install pr-review@pr-review` | `/pr-review:pr-review` |
| Cursor, OpenCode | `npx skills add snehalvartak/pr-review -a cursor -a opencode` | ask "review my diff with pr-review" |
| pi | `pi install git:github.com/snehalvartak/pr-review` | `/skill:pr-review` |

Without an installer, copy `skills/pr-review/` into any skills directory
your agent reads: `.agents/skills/` works for Cursor, OpenCode, and pi.

## Use

- Default: working tree vs `HEAD` (staged, unstaged, and untracked).
- `branch` — current branch vs its base.
- `<commit-range>` — a custom range.

On Claude Code the report is published as a private Artifact. Other
agents write it to `.git/pr-review/report.html` (never committed) and open
it in your browser. Agents without subagents (e.g. pi) run the
independent check as a separate pass instead.

To keep noisy paths out, and out of the token budget, add a
`.prreviewignore` at the repo root, one glob per line:

```
migrations/**
/docs/api/
```

Patterns are gitignore-style and anchored at the repo root.

Output is a single page:

- **Flow**: a delta flowchart per function whose branches, loops,
  returns, raises, or calls changed. Every node carries its line number.
- **Interaction**: a delta sequence diagram when the change crosses a
  component boundary (client ↔ handler, producer ↔ consumer) or depends
  on ordering.
- **Calls**: changed functions, their callers, and wiring (routes,
  middleware, flags, DI), grouped into one lane per module, with broken
  contracts and removed registrations marked.
- **Value changes**: one `old → new` row per function whose flow is the
  same but an expression, constant, or signature changed.
- **Shape changes**: a key diff (`+items −results ~total: int→str`) when a
  returned object, API payload, schema, or type changes fields.
- **Tests**: one row per weakened assertion, skip, or changed expectation
  (regenerated snapshots included).
- **No flow change**: one line per remaining file; moved code shows once
  as `(moved)`. Lockfiles and generated files are excluded and counted.
- **⚠ doubts**: from a subagent that sees only before/after source and
  call sites (not the intent), ≤3 per item, ≤10 words each.

Large diffs get full diagrams for the 8 riskiest items; the rest are rows.

Chat gets the link and one count line. Reference renders:
[`diff-with-bug`](tests/diff-with-bug/example-report.html),
[`wiring-and-tests`](tests/wiring-and-tests/example-report.html).

See [`skills/pr-review/SKILL.md`](skills/pr-review/SKILL.md)
for the full process, and
[`docs/2026-08-09-guided-review-design.md`](docs/2026-08-09-guided-review-design.md)
for the design rationale.

## Contributing

Bug reports, feature requests, and pull requests are welcome — see
[`CONTRIBUTING.md`](CONTRIBUTING.md) for how to report issues and submit
changes.
