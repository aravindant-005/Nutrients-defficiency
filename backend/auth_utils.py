import hashlib
import secrets
import base64

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return f"{salt}${pwd_hash}"

def verify_password(password: str, hashed_password: str) -> bool:
    if not hashed_password or '$' not in hashed_password:
        return False
    try:
        salt, pwd_hash = hashed_password.split('$', 1)
        expected_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
        return secrets.compare_digest(pwd_hash, expected_hash)
    except Exception:
        return False

def generate_token(email: str) -> str:
    raw = f"{email}:{secrets.token_hex(16)}"
    return base64.b64encode(raw.encode('utf-8')).decode('utf-8')
