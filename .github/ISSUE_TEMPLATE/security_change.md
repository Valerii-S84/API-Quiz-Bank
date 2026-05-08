---
name: Security change
about: Track security, privacy, access control, or sensitive-boundary changes.
title: "security: "
labels: security
---

Use this template for non-sensitive security-boundary changes only. Do not use
it to disclose vulnerabilities with secrets, private identifiers, personal data
or exploitable operational details; follow `SECURITY.md` for sensitive reports.

## Scope

Security boundary:

Expected change:

## Sensitive Data Check

- [ ] No secrets, credentials, tokens, private keys, or `.env*` content are included.
- [ ] Logs and reports avoid sensitive payload dumps.
- [ ] External services or production systems are not wired without explicit approval.

## Verification

Required checks or review gates:
