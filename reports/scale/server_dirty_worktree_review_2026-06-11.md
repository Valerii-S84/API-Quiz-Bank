# Server Dirty Worktree Review - 2026-06-11

Status: `Done for review; no cleanup executed`.

Scope: read-only review of `/opt/api-quiz-bank` dirty tracked files blocking a
clean hotfix deploy. No secrets, raw headers, database configuration values or
quiz content were printed.

## Server Snapshot

| Check | Result |
|---|---|
| Server host/user/path | `ubuntu-8gb-nbg1-1` / `root` / `/opt/api-quiz-bank` |
| Branch | `main` |
| Current SHA | `904babbd998adcf43cfbc7945d5f24d499ec47c4` |
| Server `origin/main` ref | `904babbd998adcf43cfbc7945d5f24d499ec47c4` |
| Production deploy/restart/migration | not executed |

The server remote refs were not fetched during this review; the deploy plan
contains an explicit future `git fetch` step.

## Dirty Files

`git status --short` showed exactly two dirty tracked files:

- `src/quizbank_mvp/trusted_delivery.py`
- `tests/test_shorts_factory_backend.py`

Sanitized diff stat:

```text
src/quizbank_mvp/trusted_delivery.py |  7 ++++++-
tests/test_shorts_factory_backend.py | 13 +++++++++++++
2 files changed, 19 insertions(+), 1 deletion(-)
```

## Sanitized Change Summary

| File | Summary | Markers observed | Runtime criticality |
|---|---|---|---|
| `src/quizbank_mvp/trusted_delivery.py` | Expands trusted answer-enabled consumer handling | `DEUTSCH_TRAINER_BOT_CONSUMER_ID`, `ANSWER_ENABLED_CONSUMERS` | Access/projection behavior; production-critical and unrelated to `/v1/quiz-items/next` performance |
| `tests/test_shorts_factory_backend.py` | Adds test coverage for the new trusted consumer projection | `DEUTSCH_TRAINER_BOT_CONSUMER_ID`, `answer_enabled_projection` | Test-only but tied to the runtime access change |

No raw secret values were printed. The string marker `trainer_key` appears only
inside test code and was not recorded as a raw credential.

## Hash / Mode Evidence

The dirty server worktree content differs from the release-branch target:

| File | Release branch blob | Server worktree blob | Release mode | Server mode |
|---|---|---|---|---|
| `src/quizbank_mvp/trusted_delivery.py` | `9e92124a4a1d9c43deb2c2e051e2d866e59af351` | `dc561c26847f7aad4fe257cc43d81dac63e4272e` | `100644` | `777` |
| `tests/test_shorts_factory_backend.py` | `d75737da7aa499e41bb095ca1aac6c6ff00b2085` | `7df0307c2bd4e98e6162bc4986b9f81bc65361ac` | `100644` | `777` |

Because the hashes differ, the dirty state must not be silently ignored or
overwritten during hotfix deployment.

## Handling Plan

Do not run cleanup without a separate explicit deploy/cleanup approval.

Safe choices for the next execution window:

1. Abort deploy if these dirty changes cannot be classified or approved.
2. If the dirty trusted-consumer change must remain in production, first move it
   into the git source-of-truth through a separate branch/PR, then create a new
   deploy target that combines it with the next-route hotfix.
3. If the dirty trusted-consumer change may be temporarily parked, create a
   root-only server patch backup and stash only these two paths before checking
   out the hotfix release branch.

The patch/stash option must be executed only after approval, for example:

```bash
cd /opt/api-quiz-bank
install -d -m 0700 var/deploy-safety/next-route-hotfix-20260611
git diff -- src/quizbank_mvp/trusted_delivery.py tests/test_shorts_factory_backend.py \
  > var/deploy-safety/next-route-hotfix-20260611/server_dirty_trusted_delivery.patch
chmod 600 var/deploy-safety/next-route-hotfix-20260611/server_dirty_trusted_delivery.patch
git stash push -m pre-next-route-hotfix-dirty-trusted-delivery-2026-06-11 -- \
  src/quizbank_mvp/trusted_delivery.py tests/test_shorts_factory_backend.py
git status --short
```

No `git reset --hard`, `git checkout .` or `git clean` is part of the prepared
path.
