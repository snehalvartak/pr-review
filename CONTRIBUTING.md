# Contributing

Thanks for considering a contribution to `reviewing-ai-diffs`.

## Reporting issues

Before opening an issue, search [existing issues](https://github.com/snehalvartak/reviewing-ai-diffs/issues)
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
   [`skills/reviewing-ai-diffs/SKILL.md`](skills/reviewing-ai-diffs/SKILL.md);
   the report layout is `skills/reviewing-ai-diffs/template.html`, and
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

This repo is a [Claude Code plugin](https://code.claude.com/docs) —
`.claude-plugin/plugin.json` registers the skill under `skills/`. There's
no build step; changes to `SKILL.md` take effect the next time the skill
is invoked.

To try the skill locally without publishing, add this repo's path directly
via `claude plugin marketplace add <local-path>` instead of the GitHub URL.
