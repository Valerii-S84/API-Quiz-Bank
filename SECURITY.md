# Security Policy

## Supported Scope

This repository currently contains documentation, source CSV assets, governance
data, seed contracts, local validation tooling, a protected public MVP/beta
runtime path and an owner-operated protected production API runtime path.

Security-sensitive areas include:

- raw corpus integrity and checksums;
- generated inventory and import manifests;
- future API/auth/billing/Telegram integration boundaries;
- privacy and compliance registers;
- any credentials, tokens, keys or environment files.

## Reporting

Use GitHub issues for non-sensitive security-boundary, documentation, corpus,
support, abuse or tooling reports. Use `.github/ISSUE_TEMPLATE/support_abuse.md`
for non-sensitive support/abuse intake and `.github/ISSUE_TEMPLATE/security_change.md`
for non-sensitive security-boundary changes.

Report suspected security, privacy, abuse or corpus-integrity issues that
include sensitive details to the project owner through the private owner channel
recorded in `reports/compliance/public_mvp_support_security_contact_2026-05-08.md`.
Do not open public issues containing secrets, credentials, private identifiers,
raw request dumps or sensitive operational details.

## Handling Rules

- Never commit `.env*`, private keys, bot tokens, API keys, billing secrets or cloud credentials.
- Do not paste secrets into logs, reports, generated artifacts or assistant responses.
- Treat LLM output and external payloads as untrusted input.
- Do not connect real Telegram, billing, database, hosting or production systems without explicit approval and a documented review path.

## Public MVP / Protected Beta Contact Gate

For Public MVP / Protected Beta, the repository-visible contact posture is:

- public non-sensitive support/abuse/privacy-routing issues through GitHub
  issue templates;
- private sensitive security/privacy channel held outside the public repository
  by the project owner;
- no secrets, private addresses or raw operational identifiers committed.

## Current Limitations

No broad public, school, paid-customer or external legal/privacy production
claim is covered by this policy. The supported production security scope is
limited to the owner-operated protected API runtime behind the required edge
and application API-key gates.
