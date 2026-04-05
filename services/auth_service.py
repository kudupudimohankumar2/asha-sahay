"""Simple email/password auth for ASHA Sahayak (SQLite-backed demo)."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
import time
from datetime import datetime
from typing import Any, Optional

from models.common import new_id
from services.db import get_db

logger = logging.getLogger(__name__)

_TOKEN_TTL_SEC = 7 * 24 * 3600
_PBKDF2_ITER = 120_000


def _secret() -> bytes:
    s = os.getenv("ASHA_AUTH_SECRET") or os.getenv("DATABRICKS_APP_NAME") or "asha-sahayak-dev-secret-change-me"
    return s.encode("utf-8")


def hash_password(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), _PBKDF2_ITER)
    return dk.hex(), salt


def verify_password(password: str, pw_hash: str, salt: str) -> bool:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), _PBKDF2_ITER)
    return hmac.compare_digest(dk.hex(), pw_hash)


def make_token(user_id: str) -> str:
    import base64

    exp = int(time.time()) + _TOKEN_TTL_SEC
    base = f"{user_id}|{exp}"
    sig = hmac.new(_secret(), base.encode("utf-8"), hashlib.sha256).hexdigest()
    raw = f"{base}|{sig}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def verify_token(token: str) -> Optional[dict[str, Any]]:
    import base64

    try:
        s = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        parts = s.split("|")
        if len(parts) != 3:
            return None
        user_id, exp_s, sig = parts
        expected = hmac.new(_secret(), f"{user_id}|{exp_s}".encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        if int(time.time()) > int(exp_s):
            return None
        row = get_db().fetch_one("SELECT * FROM app_users WHERE user_id = ?", (user_id,))
        if not row:
            return None
        return {
            "user_id": row["user_id"],
            "email": row["email"],
            "username": row["username"],
            "full_name": row["full_name"],
            "phone": row.get("phone", ""),
        }
    except Exception as e:
        logger.debug("token verify failed: %s", e)
        return None


def register_user(email: str, username: str, full_name: str, password: str, phone: str = "") -> dict[str, Any]:
    db = get_db()
    email = email.strip().lower()
    username = username.strip()
    if db.fetch_one("SELECT 1 FROM app_users WHERE email = ?", (email,)):
        raise ValueError("Email already registered")
    if db.fetch_one("SELECT 1 FROM app_users WHERE username = ?", (username,)):
        raise ValueError("Username already taken")
    pw_hash, salt = hash_password(password)
    uid = new_id()
    db.insert(
        "app_users",
        {
            "user_id": uid,
            "email": email,
            "username": username,
            "full_name": full_name.strip(),
            "phone": phone.strip(),
            "password_hash": pw_hash,
            "password_salt": salt,
            "created_at": datetime.utcnow().isoformat(),
        },
    )
    return {"user_id": uid, "email": email, "username": username, "full_name": full_name.strip(), "phone": phone.strip()}


def login_user(email_or_username: str, password: str) -> Optional[dict[str, Any]]:
    q = email_or_username.strip()
    row = get_db().fetch_one(
        "SELECT * FROM app_users WHERE email = ? OR username = ?",
        (q.lower(), q),
    )
    if not row:
        return None
    if not verify_password(password, row["password_hash"], row["password_salt"]):
        return None
    return {
        "user_id": row["user_id"],
        "email": row["email"],
        "username": row["username"],
        "full_name": row["full_name"],
        "phone": row.get("phone", ""),
    }


def ensure_demo_user() -> None:
    """Seed a demo account when the users table is empty."""
    db = get_db()
    n = db.fetch_one("SELECT COUNT(*) as c FROM app_users")
    if n and n.get("c", 0) > 0:
        return
    try:
        register_user(
            email="demo@asha.local",
            username="demo",
            full_name="Demo ASHA Worker",
            password="demo123",
            phone="",
        )
        logger.info("Seeded demo user demo@asha.local / demo123")
    except ValueError:
        pass
