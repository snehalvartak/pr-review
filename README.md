# reviewing-ai-diffs

A Claude Code skill for reviewing AI-generated diffs without drowning in them.

AI-written code lacks the "why" a human author carries in their head, and
large diffs make that worse — too many files/lines to hold in context at
once, and it's specifically hard to catch code that *looks* right but is
subtly wrong. This skill walks a diff one logical chunk at a time, each
independently pre-screened by a subagent before you see it, so you never
face the whole diff at once.

## Install

```
claude plugin marketplace add snehalvartak/reviewing-ai-diffs
```

## Use

Ask Claude to review a diff, or invoke the skill directly:

```
/reviewing-ai-diffs
```

- Default: reviews your working tree diff against `HEAD` (staged + unstaged).
- `/reviewing-ai-diffs branch` — reviews the current branch against its base.
- `/reviewing-ai-diffs <commit-range or description>` — a custom scope.

For each chunk you'll see what changed, why (from a plan/issue/commit
message, or inferred), a risk tag, and anything an independent subagent
found worth checking. Approve, ask questions, flag concerns, or ask for a
fix before moving to the next chunk. A summary + optional shareable report
wraps up the review at the end.

See [`skills/reviewing-ai-diffs/SKILL.md`](skills/reviewing-ai-diffs/SKILL.md)
for the full process, and
[`docs/superpowers/specs/2026-08-09-guided-review-design.md`](docs/superpowers/specs/2026-08-09-guided-review-design.md)
for the design rationale.
