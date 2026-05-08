# Public MVP / Protected Beta Support and Security Contact Record

Date: 2026-05-08

Scope: Public MVP / Protected Beta only. This is not a production support SLA,
formal vulnerability disclosure program or paid-customer support process.

## Public Non-Sensitive Intake

| Path | Use |
|---|---|
| GitHub issue template `support_abuse` | Non-sensitive support, content quality, abuse, access/quota and privacy-routing reports. |
| GitHub issue template `security_change` | Non-sensitive security/privacy/access-control change tracking. |
| `SECURITY.md` | Routing rule for sensitive reports and public issue restrictions. |
| `runbooks/privacy_request_workflow.md` | Manual export, deletion, correction and access-scope complaint workflow. |

## Private Sensitive Intake

| Field | Record |
|---|---|
| Owner | project owner / authorized VPS operator |
| Private channel | owner-controlled private channel outside the public repository |
| Repository disclosure | exact private address, handles and credentials are intentionally not committed |
| Allowed sensitive reports | security, privacy, abuse, corpus-integrity issues with sensitive details |
| Public issue rule | do not post secrets, private identifiers, raw request dumps or learner personal data |

## Gate Decision

```text
GO for Public MVP / Protected Beta contact gate
NO-GO for production security disclosure or SLA-backed support
```

## Limitations

- No formal vulnerability disclosure program is configured.
- No production incident SLA is configured.
- Private contact reachability is owner-maintained outside this repository.
