import bcrypt

# Dummy hash for constant-time comparisons when a user doesn't exist
DUMMY_HASH = "$2b$12$KIXeW44cM0f/yI55mEwL/e0eA.wM9U0d9WbC0wJ/R/B4m/fV7n11C"

def hash_password(password: str) -> str:
    """Hashes a password using bcrypt with a generated salt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False
