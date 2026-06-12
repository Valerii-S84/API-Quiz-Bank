# Server Dirty Worktree Deploy Handling - 2026-06-12

## Scope

Safely handle the dirty tracked server worktree before production hotfix deploy.

No dirty server files were deleted.

## Server Context

| Field | Value |
|---|---|
| Host | `ubuntu-8gb-nbg1-1` |
| User | `root` |
| Path | `/opt/api-quiz-bank` |
| Branch before handling | `main` |
| SHA before handling | `904babbd998adcf43cfbc7945d5f24d499ec47c4` |

## Dirty Files

Tracked dirty file count: `2`.

| File | Git mode/blob | File mode/owner | SHA-256 |
|---|---|---|---|
| `src/quizbank_mvp/trusted_delivery.py` | `100644 7d2af1994e3e9a9caf767a8cf46ffb13d4f34189` | `777 UNKNOWN:UNKNOWN` | `7cba862b58aca62196ec5a16a792cfcbd01b8a4baeda5ad75e9606928e43aed4` |
| `tests/test_shorts_factory_backend.py` | `100644 74bb59cdc70150de3e49659c7c203fef6039a8d1` | `777 UNKNOWN:UNKNOWN` | `aba6446bf236440ad89f9a71d999b934df495a842b482b22766084d88205fd41` |

Sanitized diff summary:

```text
src/quizbank_mvp/trusted_delivery.py |  7 ++++++-
tests/test_shorts_factory_backend.py | 13 +++++++++++++
2 files changed, 19 insertions(+), 1 deletion(-)
```

No raw diff content was printed or copied into reports.

## Backup

| Field | Value |
|---|---|
| Backup path | `/root/api-quiz-bank-dirty-backup-20260612-054009` |
| Backup directory mode | `700` |
| Patch backup | `/root/api-quiz-bank-dirty-backup-20260612-054009/server_dirty_worktree.patch` |
| Patch mode | `600 root:root` |

Backup verification:

```text
600 root:root 2593 /root/api-quiz-bank-dirty-backup-20260612-054009/server_dirty_worktree.patch
777 1000:1000 12136 /root/api-quiz-bank-dirty-backup-20260612-054009/tests/test_shorts_factory_backend.py
777 1000:1000 5867 /root/api-quiz-bank-dirty-backup-20260612-054009/src/quizbank_mvp/trusted_delivery.py
```

## Stash

| Field | Value |
|---|---|
| Message | `pre-next-route-hotfix-backup-2026-06-12` |
| Stash ref | `stash@{0} be0713dade0968e3ac61b1e61e2a31a89e8aa09e` |

After backup and stash, `git status --short` on the server was clean.

## Result

Dirty tracked changes were backed up and stashed before checkout. The server was
then moved to `release/next-route-hotfix-2026-06-11` at
`9cfdc8ebefa452bd41bb094726068379bca748ca`.
