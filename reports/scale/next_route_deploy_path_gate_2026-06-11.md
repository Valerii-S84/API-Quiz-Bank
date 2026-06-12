# Next Route Deploy Path Gate - 2026-06-11

Status: `Done for deploy-path preparation; production deploy not executed`.

Scope: prepare a clean documented source-of-truth path for the
`/v1/quiz-items/next` hotfix without touching the production runtime.

## Local Source Of Truth

| Check | Result |
|---|---|
| Local host/user/path | `DESKTOP-LLPPQ70` / `serputko` / `/mnt/c/Users/User/Desktop/API Quiz Bank` |
| Local branch | `codex/release-governance-evidence` |
| Local SHA | `9cfdc8ebefa452bd41bb094726068379bca748ca` |
| Local worktree | dirty only with deploy-path evidence reports from this task and prior stopped deploy evidence |
| Hotfix commit | `9cfdc8ebefa452bd41bb094726068379bca748ca` |
| Hotfix subject | `perf(selection): bound next route candidate pool` |

The hotfix commit contains the expected runtime and database files:

- `src/quizbank_mvp/selection_eligibility.py`
- `src/quizbank_mvp/selection.py`
- `src/quizbank_mvp/selection_diagnostics.py`
- `database/postgresql/011_add_next_route_selection_indexes.sql`
- `database/migrations/010_add_next_route_selection_indexes.sql`
- relevant tests and scale reports

Runtime-impacting diff from the current remote main tree to the hotfix target is
limited to:

- `src/quizbank_mvp/selection_eligibility.py`
- `src/quizbank_mvp/selection.py`
- `src/quizbank_mvp/selection_diagnostics.py`
- `database/postgresql/011_add_next_route_selection_indexes.sql`
- `database/migrations/010_add_next_route_selection_indexes.sql`

## Local Verification

| Command | Result |
|---|---|
| `python3 -m unittest discover -s tests -p "test_*.py"` | `Ran 372 tests ... OK` |
| `python3 tools/no_secrets_scan.py` | `No committed secrets detected.` |
| `git diff --check` | pass |

## Remote Check

| Check | Result |
|---|---|
| Remote | `git@github.com:Valerii-S84/API-Quiz-Bank.git` |
| `origin/main` after fetch | `a9238e32b40a40372310bb3989804f1281d9590c` |
| Hotfix in `origin/main` | no |
| Release branch created | `origin/release/next-route-hotfix-2026-06-11` |
| Release branch target | `9cfdc8ebefa452bd41bb094726068379bca748ca` |
| Hotfix in release branch | yes |

`origin/main` tree matched the already-merged pre-hotfix branch tree, so the
release branch does not drop current remote-main content. It adds the hotfix
target and its direct predecessor scale-evidence commit.

## Source-Of-Truth Decision

The clean deploy source-of-truth is:

```text
origin/release/next-route-hotfix-2026-06-11
target SHA: 9cfdc8ebefa452bd41bb094726068379bca748ca
```

No server-side manual copy deploy is needed or approved by this report.

## Production Impact

No production deploy, rebuild, restart, migration or smoke write was executed
while preparing this path.
