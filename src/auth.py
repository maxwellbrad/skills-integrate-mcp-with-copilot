"""Password storage and signed session helpers for the activities API."""

import base64
import hashlib
import hmac
import json
import os
import secrets
import tempfile
import time
from pathlib import Path
from typing import Any

PASSWORD_ITERATIONS = 600_000
SESSION_TTL_SECONDS = 8 * 60 * 60
DEFAULT_USERS_FILE = Path(__file__).with_name("users.json")
_FALLBACK_SESSION_SECRET = secrets.token_bytes(32)


def users_file() -> Path:
    return Path(os.environ.get("AUTH_USERS_FILE", DEFAULT_USERS_FILE))


def load_users() -> dict[str, dict[str, str]]:
    path = users_file()
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as user_file:
        data: Any = json.load(user_file)
    users = data.get("users") if isinstance(data, dict) else None
    if not isinstance(users, dict):
        raise ValueError("Account file must contain a 'users' object")

    normalized: dict[str, dict[str, str]] = {}
    for email, account in users.items():
        if (
            not isinstance(email, str)
            or not isinstance(account, dict)
            or account.get("role") not in {"student", "staff"}
            or not isinstance(account.get("password_hash"), str)
        ):
            raise ValueError("Account file contains an invalid account")
        normalized[email.strip().lower()] = account
    return normalized


def save_users(users: dict[str, dict[str, str]]) -> None:
    path = users_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_path = tempfile.mkstemp(dir=path.parent, prefix="users-")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as user_file:
            json.dump({"users": users}, user_file, indent=2)
            user_file.write("\n")
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PASSWORD_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PASSWORD_ITERATIONS,
        _encode(salt),
        _encode(digest),
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, digest_text = stored_hash.split("$", 3)
        iterations = int(iterations_text)
        if algorithm != "pbkdf2_sha256" or not 100_000 <= iterations <= 2_000_000:
            return False
        expected = _decode(digest_text)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), _decode(salt_text), iterations)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def encode_session_token(email: str) -> str:
    payload = {"email": email, "expires": int(time.time()) + SESSION_TTL_SECONDS}
    encoded_payload = _encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = hmac.new(_session_secret(), encoded_payload.encode(), hashlib.sha256).digest()
    return f"{encoded_payload}.{_encode(signature)}"


def decode_session_token(token: str) -> str | None:
    try:
        encoded_payload, encoded_signature = token.split(".", 1)
        signature = _decode(encoded_signature)
        expected = hmac.new(_session_secret(), encoded_payload.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            return None
        payload = json.loads(_decode(encoded_payload))
        if not isinstance(payload.get("email"), str) or payload.get("expires", 0) <= time.time():
            return None
        return payload["email"].strip().lower()
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def _session_secret() -> bytes:
    configured_secret = os.environ.get("AUTH_SESSION_SECRET")
    return configured_secret.encode() if configured_secret else _FALLBACK_SESSION_SECRET


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))