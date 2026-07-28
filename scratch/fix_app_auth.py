import sys
import re

app_js_path = 'frontend/app.js'
with open(app_js_path, 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(r"// Auth Check\s+if \(token\) \{.*?\s\} else \{\s+showAuthScreen\(\);\s+\}", re.DOTALL)

replacement = """// Auth Check
    try {
        const res = await authFetch('/me');
        if (res.ok) {
            const userData = await res.json();
            userProfile = userData;
            userId = userData.id;
            isGuest = false;
            localStorage.setItem('streamora_profile', JSON.stringify(userProfile));
            await syncWatchlistFromBackend();
            hideAuthScreen();
            initApp();
        } else {
            // Token is invalid or not logged in
            localStorage.removeItem('streamora_jwt');
            localStorage.removeItem('streamora_profile');
            showAuthScreen();
        }
    } catch(e) {
        showAuthScreen();
    }"""

new_content, count = pattern.subn(replacement, content)

if count > 0:
    with open(app_js_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully replaced.")
else:
    print("Pattern not found!")
