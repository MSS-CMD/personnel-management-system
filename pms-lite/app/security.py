"""密码哈希与令牌生成（使用标准库，零额外依赖）。"""
import hashlib
import os
import secrets


def hash_password(password: str) -> str:
    """PBKDF2-HMAC-SHA256，返回 'salt:hash' 十六进制。"""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return salt.hex() + ":" + dk.hex()


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, dk_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return secrets.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False


def gen_token() -> str:
    return secrets.token_urlsafe(32)
