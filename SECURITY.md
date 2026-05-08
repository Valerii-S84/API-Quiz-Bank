# Security Policy

## Supported Scope

This repository currently contains documentation, source CSV assets, governance data, seed contracts and local validation tooling. It does not contain a production runtime service.

Security-sensitive areas include:

- raw corpus integrity and checksums;
- generated inventory and import manifests;
- future API/auth/billing/Telegram integration boundaries;
- privacy and compliance registers;
- any credentials, tokens, keys or environment files.

## Reporting

Use GitHub issues for non-sensitive security-boundary, documentation, corpus or
tooling reports. Report suspected security, privacy, abuse or corpus-integrity
issues that include sensitive details to the project owner through a private
channel. Do not open public issues containing secrets, credentials, private
identifiers, raw request dumps or sensitive operational details.

## Handling Rules

- Never commit `.env*`, private keys, bot tokens, API keys, billing secrets or cloud credentials.
- Do not paste secrets into logs, reports, generated artifacts or assistant responses.
- Treat LLM output and external payloads as untrusted input.
- Do not connect real Telegram, billing, database, hosting or production systems without explicit approval and a documented review path.

## Current Limitations

No signed security contact, production incident process or formal vulnerability
disclosure program is configured yet. Sensitive reports still require a private
owner channel, which blocks broad public-beta or production claims until
resolved.
