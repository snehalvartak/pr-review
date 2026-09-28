# Contributing

Thanks for considering a contribution to `pr-review`.

## Reporting issues

Before opening an issue, search [existing issues](https://github.com/snehalvartak/pr-review/issues)
to see if it's already been reported.

When filing a bug, include:

- The scope you invoked the skill with (default working-tree diff, `branch`,
  or a custom range/description).
- What you expected to happen vs. what actually happened.
- The diff (or a minimal reproduction of it) that triggered the issue, if
  you can share it.
- The generated report (link or HTML), if you can share it.

For feature requests, describe the review scenario that's currently
awkward or unsupported, and what outcome you'd want instead.

## Contributing changes

1. Fork the repo and create a branch off `main`.
2. Make your change. The skill's behavior lives in
   [`skills/pr-review/SKILL.md`](skills/pr-review/SKILL.md);
   the report layout is `skills/pr-review/template.html`, and
   the rationale behind its design is in
   [`docs/2026-08-09-guided-review-design.md`](docs/2026-08-09-guided-review-design.md).
3. Test your change against the fixtures in [`tests/`](tests/README.md) —
   at minimum, run the skill against `tests/diff-with-bug/diff.patch` and
   confirm it meets the passing criteria in [`tests/README.md`](tests/README.md).
   Add a new fixture under `tests/` if your change affects classification,
   diagram rules, or the independent-check step in a way the existing
   fixture doesn't exercise.
4. Update `README.md` and/or `SKILL.md` if you changed user-facing behavior.
5. Open a pull request describing what changed and why, and how you
   verified it (which fixtures, what output you saw).

## Development notes

The skill is a plain [Agent Skill](https://agentskills.io):
`skills/pr-review/SKILL.md` plus `template.html`, with no build step.
Three thin manifests make it installable:

- `.claude-plugin/plugin.json` and `marketplace.json`: Claude Code
- `package.json` (`pi.skills`): pi
- nothing extra for Cursor/OpenCode; the `skills` CLI and both agents read
  `skills/pr-review/` directly

Keep `SKILL.md` agent-neutral: name tools by capability ("subagent",
"artifact tool") with a fallback, never assume one agent's tool exists.

To try changes locally:

- Claude Code: `claude plugin validate .` then
  `claude plugin marketplace add ./` and `claude plugin install pr-review@pr-review`
- Cursor/OpenCode/pi: `npx skills add ./ -a cursor -a opencode -a pi`
  from a scratch project
