"""
auth_utils.py – Password hashing and JWT token helpers.
"""

import os
import jwt
import bcrypt
from datetime import datetime, timedelta

# In production, load this from an environment variable
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-sales-dashboard-key-2026")
ALGORITHM  = "HS256"
TOKEN_EXPIRE_HOURS = 24

# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

# ── JWT helpers ───────────────────────────────────────────────────────────────

def create_token(user_id: int, username: str) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    """Returns payload dict, or raises jwt.ExpiredSignatureError / jwt.InvalidTokenError."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
