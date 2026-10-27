import base64
import hashlib
import hmac
import json
import secrets
import time

SESSION_COOKIE = "hr_session"
SESSION_TTL_SECONDS = 12 * 60 * 60
PASSWORD_ITERATIONS = 310_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def create_session_token(account_id: int, signing_key: str) -> str:
    if not signing_key:
        raise RuntimeError("AUTH_SIGNING_KEY is required for authentication")
    payload = _b64encode(
        json.dumps({"sub": account_id, "exp": int(time.time()) + SESSION_TTL_SECONDS}).encode()
    )
    signature = hmac.new(
        signing_key.encode(), payload.encode(), hashlib.sha256
    ).digest()
    return f"{payload}.{_b64encode(signature)}"


def read_session_token(token: str | None, signing_key: str) -> int | None:
    if not token or not signing_key:
        return None
    try:
        payload, signature = token.split(".", 1)
        expected = _b64encode(
            hmac.new(
                signing_key.encode(), payload.encode(), hashlib.sha256
            ).digest()
        )
        if not hmac.compare_digest(signature, expected):
            return None
        padded = payload + "=" * (-len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(padded))
        account_id = claims["sub"]
        if not isinstance(account_id, int) or claims["exp"] <= time.time():
            return None
        return account_id
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None
