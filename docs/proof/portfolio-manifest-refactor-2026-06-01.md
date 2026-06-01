# Portfolio manifest refactor - 2026-06-01

Bead: `build000r-portfolio-reality-idea-plan-ld7.10`

## Scope

Moved the portfolio block source from hand-authored README-only copy to
`portfolio-manifest.json`, with `README.md` carrying the rendered public copy.
The repo remains intentionally tiny: no framework, build system, or site sync
was added.

`scripts/check_portfolio_readme.py` now:

- renders the README portfolio block from `portfolio-manifest.json`
- fails when the rendered block differs from the checked-in README block
- preserves the existing README link fetch behavior
- preserves the existing `portfolio-link-policy.json` unlinked/private-entry
  check

`portfolio-link-policy.json` was not changed because the public/private link
policy did not change. The same 7 unlinked entries remain explicitly justified
there, and the same npm link overrides remain available for headless checker
variance.

## Validation

```bash
python3 scripts/check_portfolio_readme.py --render-portfolio
python3 scripts/check_portfolio_readme.py --offline
make check
git diff --check
```

Observed results:

```text
python3 scripts/check_portfolio_readme.py --offline
portfolio README check passed: 7 linked entries, 7 intentional private entries, manifest matches README, offline

make check
python3 scripts/check_portfolio_readme.py
portfolio README check passed: 7 linked entries, 7 intentional private entries, manifest matches README, 11 links fetched
```

