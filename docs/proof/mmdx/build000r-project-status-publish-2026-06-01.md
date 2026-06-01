# build000r project-status MMDX publish proof

Timestamp: 2026-06-01T20:14:42Z

Bead: `build000r-portfolio-reality-idea-plan-ld7.6`

Stack: `diagrams/build000r-project-status.mmdx`

Recorded short link: `https://buildooor.com/mmdx/buildooor/build000r-project-status`

## Results

- README reviewed; no `AGENTS.md` exists in this repo.
- Preflight succeeded: `MMDX preflight OK: 6 charts`.
- Fragment generation succeeded with `--fragment-only --no-preflight`.
- Publish dry-run resolved the existing in-place endpoint:
  `https://buildooor.com/api/app-links/buildooor/build000r-project-status`.
- Dry-run source hash:
  `82808fe6e996610bad350938bdbace7b53ace68bb15a58203e0bdb55bdafc4cd`.
- Live publish attempted against the recorded slug and failed closed:
  `mmd: publish update failed (401): Invalid or expired access token`.

No duplicate short link was created.

## Commands

```bash
br show build000r-portfolio-reality-idea-plan-ld7.6 --json
br update build000r-portfolio-reality-idea-plan-ld7.6 --status in_progress --assignee codex-worker --json
python3 ~/repos/opensource/skills/mmdx/scripts/mmd.py diagrams/build000r-project-status.mmdx --preflight-only
python3 ~/repos/opensource/skills/mmdx/scripts/mmd.py diagrams/build000r-project-status.mmdx --fragment-only --no-preflight
python3 ~/repos/opensource/skills/mmdx/scripts/mmd.py publish-link diagrams/build000r-project-status.mmdx --username buildooor --slug build000r-project-status --title "Build000r Project Status" --dry-run
python3 ~/repos/opensource/skills/mmdx/scripts/mmd.py publish-link diagrams/build000r-project-status.mmdx --username buildooor --slug build000r-project-status --title "Build000r Project Status"
```

## Blocker

The recorded slug exists in the stack header and the dry-run target is correct,
but the available agent token is invalid or expired. Refresh
`BUILDOOOR_ACCESS_TOKEN` or `SPAPS_ACCESS_TOKEN`, then rerun the same
`publish-link` command to edit the recorded short link in place.
