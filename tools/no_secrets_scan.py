#!/usr/bin/env python3
"""Fail CI when committed files look like credentials or key material."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIPPED_DIRECTORIES = {".git", ".mypy_cache", ".pytest_cache", "__pycache__", "var"}
SENSITIVE_FILE_PATTERNS = [
    re.compile(r"^\.env($|\.)"),
    re.compile(r"^(\.npmrc|\.pypirc|\.netrc)$"),
    re.compile(r"^id_rsa.*"),
    re.compile(r".*\.(pem|key|p12|pfx)$", re.IGNORECASE),
    re.compile(r".*credentials\.(json|ini|toml|yml|yaml)$", re.IGNORECASE),
]
SECRET_VALUE_PATTERNS = [
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    re.compile(r"\bbot[0-9]{6,}:[A-Za-z0-9_-]{30,}\b"),
    re.compile(
        r"(?i)\b(api[_-]?key|token|password|secret)\b\s*[:=]\s*['\"][^'\"]{16,}['\"]"
    ),
]


def should_skip(path: Path) -> bool:
    return any(part in SKIPPED_DIRECTORIES for part in path.relative_to(ROOT).parts)


def is_sensitive_filename(path: Path) -> bool:
    name = path.name
    return any(pattern.fullmatch(name) for pattern in SENSITIVE_FILE_PATTERNS)


def scan_text(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    findings = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if any(pattern.search(line) for pattern in SECRET_VALUE_PATTERNS):
            findings.append(f"{path.relative_to(ROOT)}:{line_number}: secret-like value")
    return findings


def scan_repository() -> list[str]:
    findings = []
    for path in sorted(ROOT.rglob("*")):
        if path.is_dir() or should_skip(path):
            continue
        relative_path = path.relative_to(ROOT)
        if is_sensitive_filename(path):
            findings.append(f"{relative_path}: sensitive filename")
            continue
        findings.extend(scan_text(path))
    return findings


def main() -> int:
    findings = scan_repository()
    if findings:
        print("Potential committed secrets found:", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    print("No committed secrets detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
