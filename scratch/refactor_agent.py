import re

with open(r'c:\Users\vedan\OneDrive\Attachments\Documents\GitHub\aurora-ai\services\agent\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update imports
import_str = '''from services.security.auth import get_current_user, create_access_token, verify_password, get_user, ACCESS_TOKEN_EXPIRE_MINUTES, timedelta, get_optional_user, hash_password
from services.security.user_data import init_db, create_user, get_watchlist, save_watchlist, get_history, save_history, update_user_profile'''

content = re.sub(r'from services\.security\.auth import .*', import_str, content)

# 2. Update /token
token_old = '''@app.post("/token")
@limiter.limit("10/minute")
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        log_event(who=form_data.username, what="LOGIN_FAILED", where="/token", details="Invalid credentials")
        return JSONResponse(status_code=401, content={"detail": "Incorrect username or password"})
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"], "user_id": user["user_id"]},
        expires_delta=access_token_expires
    )
    log_event(who=user["username"], what="LOGIN_SUCCESS", where="/token", details=f"Role: {user['role']}")
    return {"access_token": access_token, "token_type": "bearer", "user_id": user["user_id"], "role": user["role"]}'''

token_new = '''class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    display_name: str

@app.post("/register")
@limiter.limit("5/minute")
def register_user(request: Request, req: RegisterRequest):
    if len(req.password) < 6:
        return JSONResponse(status_code=400, content={"detail": "Password must be at least 6 characters"})
    user_id = create_user(req.username, req.email, hash_password(req.password), req.display_name)
    if not user_id:
        return JSONResponse(status_code=400, content={"detail": "Username or email already exists"})
    return {"status": "success", "user_id": user_id}

@app.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    user_data = dict(current_user)
    user_data.pop("hashed_password", None)
    return user_data

@app.get("/me/watchlist")
def get_my_watchlist(current_user: dict = Depends(get_current_user)):
    return get_watchlist(current_user["id"])

@app.put("/me/watchlist")
def update_my_watchlist(items: list, current_user: dict = Depends(get_current_user)):
    save_watchlist(current_user["id"], items)
    return {"status": "success"}

@app.get("/me/history")
def get_my_history(current_user: dict = Depends(get_current_user)):
    return get_history(current_user["id"])

@app.put("/me/history")
def update_my_history(items: list, current_user: dict = Depends(get_current_user)):
    save_history(current_user["id"], items)
    return {"status": "success"}

@app.post("/token")
@limiter.limit("10/minute")
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        log_event(who=form_data.username, what="LOGIN_FAILED", where="/token", details="Invalid credentials")
        return JSONResponse(status_code=401, content={"detail": "Incorrect username or password"})
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"], "user_id": user["id"]},
        expires_delta=access_token_expires
    )
    log_event(who=user["username"], what="LOGIN_SUCCESS", where="/token", details=f"Role: {user['role']}")
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user_id": user["id"], 
        "role": user["role"],
        "display_name": user["display_name"],
        "email": user["email"]
    }'''

content = content.replace(token_old, token_new)

# 3. Update endpoints to use optional user
content = content.replace('current_user: dict = Depends(get_current_user)', 'current_user: dict = Depends(get_optional_user)')
# Except for proxy_events
content = content.replace('def proxy_events(request: Request, req: EventRequest, current_user: dict = Depends(get_optional_user)):', 'def proxy_events(request: Request, req: EventRequest, current_user: dict = Depends(get_current_user)):')

# Fix user_id logic
content = content.replace('user_id = current_user["user_id"]', 'user_id = current_user["id"] if current_user else 32')

# 4. Update startup event
startup_old = '''@app.on_event("startup")
async def startup_event():
    asyncio.create_task(heartbeat_loop())'''

startup_new = '''@app.on_event("startup")
async def startup_event():
    init_db()
    admin = get_user("admin")
    if not admin:
        create_user("admin", "admin@streamora.ai", hash_password("adminpass"), "Administrator")
    asyncio.create_task(heartbeat_loop())'''

content = content.replace(startup_old, startup_new)

with open(r'c:\Users\vedan\OneDrive\Attachments\Documents\GitHub\aurora-ai\services\agent\main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated main.py')
