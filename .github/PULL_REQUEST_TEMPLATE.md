## What changed and why



## How was this tested?

Which fixture(s) under `tests/` did you run the skill against, and what
did you observe? If you added a new fixture, describe what it covers.



## Checklist

- [ ] `README.md` and/or `SKILL.md` updated if user-facing behavior changed
- [ ] Ran the skill against `tests/diff-with-bug/diff.patch` (or another
      relevant fixture) and confirmed expected behavior
- [ ] `SKILL.md` frontmatter (`name`, `description`) still accurately
      describes when the skill should trigger, if it changed
- [ ] `.claude-plugin/plugin.json` version bumped, if this change affects
      installed behavior (skip for docs-only changes)
- [ ] Verified the plugin still installs/loads cleanly (e.g. via
      `claude plugin marketplace add <local-path>`), if `plugin.json` or
      the `skills/` layout changed
