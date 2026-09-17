"""Authentication helpers for field gateways, separate from user login."""
from __future__ import annotations

import hashlib
import hmac
import secrets

from shared.config import settings


def issue_gateway_token() -> str:
    """Return a high-entropy token once; callers must show it only at setup."""
    return secrets.token_urlsafe(32)


def hash_gateway_token(token: str) -> str:
    return hmac.new(
        settings.GATEWAY_TOKEN_PEPPER.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def gateway_token_matches(token: str, expected_hash: str) -> bool:
    return hmac.compare_digest(hash_gateway_token(token), expected_hash)
