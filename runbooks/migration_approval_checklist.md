# Migration Approval Checklist

Status: required for production-impacting schema or data migrations.

Before merge:

- migration file is versioned and reviewed;
- backward/forward compatibility impact is documented;
- backup freshness is verified;
- rollback or restore path is identified;
- local/unit/contract tests covering migration-sensitive behavior pass;
- production operator approval is recorded for production runtime execution;
- changelog or release note impact is recorded.

Execution guardrails:

- do not run destructive SQL without scoped approval;
- do not modify production data manually outside the approved runbook;
- stop release if backup, restore, readiness or smoke checks fail.
