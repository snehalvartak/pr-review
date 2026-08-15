# reviewing-ai-diffs

A Claude Code skill for reviewing AI-generated diffs without drowning in them.

AI-written code lacks the "why" a human author carries in their head, and
large diffs make that worse — too many files/lines to hold in context at
once, and it's specifically hard to catch code that *looks* right but is
subtly wrong. This skill splits a diff into intent chunks, has each
independently pre-screened by a subagent, and compiles the result into a
single visual report so you never face the whole diff as flat text.

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
- `/reviewing-ai-diffs risk-first` — compiles chunks riskiest-first instead
  of the intent-order default (combinable with the above).

No questions to answer up front. The skill chunks the diff by intent,
checks every chunk independently and in parallel, and compiles the result
into a single Artifact: an overview strip of every chunk's name, risk tag,
and doubt count, followed by each chunk's real diff hunk next to one small
diagram sized to the shape of the change — a sequence diagram, a call
tree, a file tree, a component tree, or a code excerpt, whichever is
smallest and fits — with any doubts an independent subagent raised marked
directly on it. Chat gets one line with the link and a doubt count; the
artifact is the report, and it's the only output — this skill doesn't ask
you to approve or fix anything as it goes, it just hands you something to
read.

See [`skills/reviewing-ai-diffs/SKILL.md`](skills/reviewing-ai-diffs/SKILL.md)
for the full process, and
[`docs/2026-08-09-guided-review-design.md`](docs/2026-08-09-guided-review-design.md)
for the design rationale.

## Contributing

Bug reports, feature requests, and pull requests are welcome — see
[`CONTRIBUTING.md`](CONTRIBUTING.md) for how to report issues and submit
changes.
