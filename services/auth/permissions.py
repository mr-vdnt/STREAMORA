from fastapi import Request, HTTPException
from services.security.user_data import get_user_by_username

def get_current_user(request: Request):
    """
    Dependency to get the current authenticated user from request state.
    The AuthMiddleware is responsible for verifying the token and populating request.state.user.
    """
    user_payload = getattr(request.state, "user", None)
    if not user_payload:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    username = user_payload.get("sub")
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    return user

def get_optional_user(request: Request):
    """
    Dependency to get the current user, but allows anonymous access (returns None).
    """
    user_payload = getattr(request.state, "user", None)
    if not user_payload:
        return None
    return get_user_by_username(user_payload.get("sub"))

class RoleChecker:
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: dict = get_current_user):
        user_role = current_user.get("role", "Standard")
        if user_role not in self.allowed_roles:
            raise HTTPException(status_code=403, detail="Operation not permitted")
        return current_user

def require_admin(request: Request):
    user = get_current_user(request)
    if user.get("role") != "Administrator":
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user
