import re

def validate_password(password: str) -> bool:
    """
    Validates a password.
    Requires at least 8 characters.
    """
    if len(password) < 8:
        return False
    return True

def validate_email(email: str) -> bool:
    """
    Validates an email format.
    """
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False
    return True

def validate_username(username: str) -> bool:
    """
    Validates a username format.
    Only alphanumeric and underscores allowed. Length 3-30.
    """
    if not re.match(r"^\w{3,30}$", username):
        return False
    return True
