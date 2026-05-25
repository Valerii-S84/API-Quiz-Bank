"""Credential hashing primitives shared by consumer and admin auth."""

from __future__ import annotations

import hashlib


API_KEY_PREFIX_LENGTH = 12


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def api_key_prefix(raw_key: str) -> str:
    return raw_key[:API_KEY_PREFIX_LENGTH]


def admin_key_prefix(raw_key: str) -> str:
    return raw_key[:API_KEY_PREFIX_LENGTH]
