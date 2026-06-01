# Portfolio link-check baseline - 2026-06-01

Baseline for Bead `build000r-portfolio-reality-idea-plan-ld7.9`.

## Scope

`README.md` is the canonical portfolio source. The adopted path is:

```text
make check
└── python3 scripts/check_portfolio_readme.py
    ├── parse portfolio entries in README.md sections: primary, open source, side projects
    ├── require unlinked entries to appear in portfolio-link-policy.json
    └── fetch every unique Markdown HTTP link unless --offline is passed
```

No structured manifest exists yet, and this baseline does not broaden or
refactor the path.

## Environment

- Timestamp: `2026-06-01T18:20:31Z`
- Repo: `opensource/build000r`
- Branch: `main`
- Git HEAD: `2433dcf`
- OS: `Darwin 24.6.0 arm64`
- Python: `Python 3.12.13`

## Commands

```bash
br show build000r-portfolio-reality-idea-plan-ld7.9 --json
br update build000r-portfolio-reality-idea-plan-ld7.9 --status in_progress --json
sed -n '1,140p' README.md
sed -n '1,200p' Makefile
sed -n '1,220p' portfolio-link-policy.json
sed -n '1,260p' scripts/check_portfolio_readme.py
/usr/bin/time -p make check
python3 - <<'PY'
from pathlib import Path
import time
from scripts.check_portfolio_readme import load_policy, parse_entries, fetch_status
policy = load_policy(Path('portfolio-link-policy.json'))
entries, urls = parse_entries(Path('README.md'))
print(f'entries={len(entries)} linked={sum(1 for e in entries if e.url)} unlinked={sum(1 for e in entries if not e.url)} urls={len(urls)}')
for url in urls:
    start = time.perf_counter()
    status, source = fetch_status(url, 10.0)
    elapsed = time.perf_counter() - start
    override = policy.get('link_overrides', {}).get(url)
    allowed = 'override' if override else ('default' if status is not None and 200 <= status < 400 else 'not_allowed')
    print(f'{elapsed:.3f}s\tstatus={status}\tsource={source}\tallowed={allowed}\t{url}')
PY
/usr/bin/time -p python3 scripts/check_portfolio_readme.py --offline
br show build000r-portfolio-reality-idea-plan-ld7.10 --json
```

## Raw Timing

`/usr/bin/time -p make check`

```text
python3 scripts/check_portfolio_readme.py
portfolio README check passed: 7 linked entries, 7 intentional private entries, 11 links fetched
real 6.89
user 0.06
sys 0.02
```

`/usr/bin/time -p python3 scripts/check_portfolio_readme.py --offline`

```text
portfolio README check passed: 7 linked entries, 7 intentional private entries, offline
real 0.04
user 0.03
sys 0.00
```

## Counts

- Portfolio entries parsed from canonical README sections: `14`
- Linked portfolio entries: `7`
- Intentionally unlinked/private entries: `7`
- Unique Markdown HTTP links fetched by online check: `11`
- Policy overrides configured: `2`, both for npm package URLs that may return `403` to the checker

## Network and Link-Fetch Behavior

The checker fetches links serially. For each URL it tries `HEAD` first, then
falls back to `GET` only when `HEAD` returns `403` or `405`, or when the `HEAD`
request has a `URLError`. The default timeout is `10.0` seconds per request.

Measured online fetch details:

```text
entries=14 linked=7 unlinked=7 urls=11
0.072s	status=200	source=HEAD	allowed=default	https://buildooor.com
0.637s	status=200	source=HEAD	allowed=default	https://github.com/build000r/clawgs
0.696s	status=200	source=HEAD	allowed=default	https://github.com/build000r/dogswipe
0.670s	status=200	source=HEAD	allowed=default	https://github.com/build000r/etcha
0.788s	status=200	source=HEAD	allowed=default	https://github.com/build000r/skillbox
0.605s	status=200	source=HEAD	allowed=default	https://github.com/build000r/skills
0.686s	status=200	source=HEAD	allowed=default	https://github.com/build000r/swimmers
0.237s	status=200	source=HEAD	allowed=default	https://htmalabs.com
0.170s	status=200	source=HEAD	allowed=default	https://pypi.org/project/spaps/
0.064s	status=200	source=HEAD	allowed=override	https://www.npmjs.com/package/spaps
0.079s	status=200	source=HEAD	allowed=override	https://www.npmjs.com/package/spaps-sdk
```

Both npm links returned `200` via `HEAD` during this run; their configured
overrides remain relevant because the policy allows `403` for headless checker
variance.

## Known Manual Gap Against buildooor.com

The current path fetches `https://buildooor.com` as a URL, but it does not crawl
or compare the public site content against the README. There is no executable
sync from `buildooor.com`, and no assertion that the site contains the same
portfolio entries, descriptions, or public/private state. The README's stated
manual comparison requirement remains the only guard before publishing a claim
that points at an affected public page.

## Manifest Follow-Up Readiness

Bead `build000r-portfolio-reality-idea-plan-ld7.10` remains the right next step.
This baseline is enough for that manifest work to compare:

- current parse/check scope: README plus policy only
- expected counts: `14` entries, `7` linked entries, `7` intentional private entries, `11` fetched links
- online wall time: `6.89s`
- offline parse/policy wall time: `0.04s`
- current network behavior and per-link statuses
- explicit manual gap against `buildooor.com`
