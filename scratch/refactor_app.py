import re

with open(r'c:\Users\vedan\OneDrive\Attachments\Documents\GitHub\aurora-ai\frontend\app.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update initial variables
vars_old = '''let token = 'guest-token';
let userId = 32;'''
vars_new = '''let token = localStorage.getItem('streamora_jwt') || null;
let userProfile = JSON.parse(localStorage.getItem('streamora_profile')) || null;
let userId = userProfile ? userProfile.id : null;
let isGuest = false;
let isAuthModeLogin = true;'''
content = content.replace(vars_old, vars_new)

# 2. Add auth logic
auth_logic = '''
// ══════════════════════════════════════════════════════════════════════
//  AUTH LOGIC
// ══════════════════════════════════════════════════════════════════════
window.toggleAuthMode = function() {
    isAuthModeLogin = !isAuthModeLogin;
    const title = document.getElementById('auth-subtitle');
    const submitBtn = document.getElementById('auth-submit-btn');
    const toggleText = document.getElementById('auth-toggle-text');
    const toggleLink = document.getElementById('auth-toggle-link');
    const signupFields = document.querySelectorAll('.signup-only');
    const errorEl = document.getElementById('auth-error');
    
    errorEl.style.display = 'none';
    
    if (isAuthModeLogin) {
        title.textContent = 'Sign in to your account';
        submitBtn.textContent = 'Sign In';
        toggleText.textContent = 'Don\\'t have an account?';
        toggleLink.textContent = 'Sign Up';
        signupFields.forEach(f => f.style.display = 'none');
    } else {
        title.textContent = 'Create your account';
        submitBtn.textContent = 'Sign Up';
        toggleText.textContent = 'Already have an account?';
        toggleLink.textContent = 'Sign In';
        signupFields.forEach(f => f.style.display = 'block');
    }
}

window.submitAuth = async function() {
    const errorEl = document.getElementById('auth-error');
    errorEl.style.display = 'none';
    
    const username = document.getElementById('auth-username').value;
    const password = document.getElementById('auth-password').value;
    const btn = document.getElementById('auth-submit-btn');
    const originalText = btn.textContent;
    btn.textContent = 'Processing...';
    btn.disabled = true;
    
    try {
        if (!isAuthModeLogin) {
            const email = document.getElementById('auth-email').value;
            const displayName = document.getElementById('auth-display-name').value || username;
            
            const regRes = await fetch('http://127.0.0.1:8004/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, email, password, display_name: displayName})
            });
            
            if (!regRes.ok) {
                const data = await regRes.json();
                throw new Error(data.detail || 'Registration failed');
            }
        }
        
        // Login (always done, either explicitly or after signup)
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        
        const res = await fetch('http://127.0.0.1:8004/token', {
            method: 'POST',
            body: formData
        });
        
        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.detail || 'Login failed');
        }
        
        const data = await res.json();
        token = data.access_token;
        userProfile = {
            id: data.user_id,
            username: username,
            role: data.role,
            display_name: data.display_name,
            email: data.email
        };
        userId = data.user_id;
        isGuest = false;
        
        localStorage.setItem('streamora_jwt', token);
        localStorage.setItem('streamora_profile', JSON.stringify(userProfile));
        
        // Sync watchlist from backend
        await syncWatchlistFromBackend();
        
        hideAuthScreen();
        initApp();
        
    } catch (e) {
        errorEl.textContent = e.message;
        errorEl.style.display = 'block';
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

window.continueAsGuest = function() {
    isGuest = true;
    token = null;
    userId = null;
    userProfile = null;
    hideAuthScreen();
    initApp();
}

function hideAuthScreen() {
    const screen = document.getElementById('auth-screen');
    if (screen) {
        screen.style.opacity = '0';
        setTimeout(() => {
            screen.style.display = 'none';
        }, 500);
    }
}

function showAuthScreen() {
    const screen = document.getElementById('auth-screen');
    if (screen) {
        screen.style.display = 'flex';
        // Trigger reflow
        void screen.offsetWidth;
        screen.style.opacity = '1';
    }
}

async function syncWatchlistFromBackend() {
    if (isGuest || !token) return;
    try {
        const res = await authFetch('http://127.0.0.1:8004/me/watchlist');
        if (res.ok) {
            const backendList = await res.json();
            // Merge with local list if local items exist that aren't in backend
            const merged = [...backendList];
            myList.forEach(localItem => {
                if (!merged.find(i => i.item_id === localItem.item_id)) {
                    merged.push(localItem);
                }
            });
            myList = merged;
            localStorage.setItem('streamora_mylist', JSON.stringify(myList));
            
            // Sync merged list back to backend
            await authFetch('http://127.0.0.1:8004/me/watchlist', {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(myList)
            });
        }
    } catch (e) {
        console.error('Watchlist sync error', e);
    }
}

async function syncWatchlistToBackend() {
    if (isGuest || !token) return;
    try {
        await authFetch('http://127.0.0.1:8004/me/watchlist', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(myList)
        });
    } catch(e) {}
}
'''
# Insert auth logic after INIT block
init_idx = content.find('//  INIT')
content = content[:init_idx] + auth_logic + '\n' + content[init_idx:]

# 3. Update DOMContentLoaded logic to check auth
dom_loaded_old = '''document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('streamora_theme') || 'neon';
    applyTheme(savedTheme);
    
    const savedFormat = localStorage.getItem('streamora_current_format') || 'all';
    window.currentFormat = savedFormat;
    window.updateFormatTabs();
    
    // Bind all logo click events for robust Home navigation'''
dom_loaded_new = '''document.addEventListener('DOMContentLoaded', async () => {
    const savedTheme = localStorage.getItem('streamora_theme') || 'neon';
    applyTheme(savedTheme);
    
    const savedFormat = localStorage.getItem('streamora_current_format') || 'all';
    window.currentFormat = savedFormat;
    window.updateFormatTabs();
    
    // Auth Check
    if (token) {
        try {
            const res = await authFetch('http://127.0.0.1:8004/me');
            if (res.ok) {
                await syncWatchlistFromBackend();
                hideAuthScreen();
                initApp();
            } else {
                showAuthScreen();
            }
        } catch(e) {
            showAuthScreen();
        }
    } else {
        showAuthScreen();
    }
});

function initApp() {
    // Bind all logo click events for robust Home navigation'''
content = content.replace(dom_loaded_old, dom_loaded_new)

# Fix initApp closing brace
content = content.replace('    renderApp();\n});', '    renderApp();\n}\n\n// Trigger initApp manually if not using DOMContentLoaded\n// initApp();')

# 4. Update authFetch to handle null token
authfetch_old = '''async function authFetch(url, options = {}) {
    options.headers = options.headers || {};
    options.headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(url, options);
    return res;
}'''
authfetch_new = '''async function authFetch(url, options = {}) {
    options.headers = options.headers || {};
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    const res = await fetch(url, options);
    return res;
}'''
content = content.replace(authfetch_old, authfetch_new)

# 5. Update Watchlist saving
toggle_old = '''localStorage.setItem('streamora_mylist', JSON.stringify(myList));
            updateMyListUI();'''
toggle_new = '''localStorage.setItem('streamora_mylist', JSON.stringify(myList));
            updateMyListUI();
            if (!isGuest) { syncWatchlistToBackend(); }'''
content = content.replace(toggle_old, toggle_new)

# 6. Update Account tab rendering
acct_old = '''html = `
            <div class="content-header">
                <h2>Account Settings</h2>
            </div>
            
            <div style="background:var(--bg-glass); border:1px solid var(--border-glass); border-radius:24px; padding:40px; margin-bottom:30px;">
                <div style="display:flex; align-items:center; gap:30px; margin-bottom:40px;">
                    <div style="width:100px; height:100px; border-radius:50%; background:linear-gradient(45deg, var(--streamora-cyan), var(--streamora-purple));"></div>
                    <div>
                        <h3 style="font-size:1.8rem; margin:0 0 10px 0; color:white;">Explorer Guest</h3>
                        <p style="color:var(--text-secondary); margin:0;">Premium Member • Since 2024</p>
                    </div>
                </div>'''

acct_new = '''
            const dName = userProfile ? userProfile.display_name : 'Guest User';
            const email = userProfile ? userProfile.email : 'Not logged in';
            const role = userProfile ? userProfile.role : 'Guest';
            const initial = dName.charAt(0).toUpperCase();
            
            html = `
            <div class="content-header">
                <h2>Account Settings</h2>
            </div>
            
            <div style="background:var(--bg-glass); border:1px solid var(--border-glass); border-radius:24px; padding:40px; margin-bottom:30px;">
                <div style="display:flex; align-items:center; gap:30px; margin-bottom:40px;">
                    <div style="width:100px; height:100px; border-radius:50%; background:linear-gradient(45deg, var(--streamora-cyan), var(--streamora-purple)); display:flex; justify-content:center; align-items:center; font-size:3rem; color:black; font-weight:bold; box-shadow:0 0 20px rgba(6,182,212,0.4);">
                        ${initial}
                    </div>
                    <div>
                        <h3 style="font-size:1.8rem; margin:0 0 10px 0; color:white;">${dName}</h3>
                        <p style="color:var(--text-secondary); margin:0;">${email} • ${role}</p>
                    </div>
                </div>'''
content = content.replace(acct_old, acct_new)

# 7. Update Logout handler
logout_old = '''window.performLogOut = function() {
    closeDrawerModalDirect();
    alert('You have logged out of Streamora AI.');
};'''
logout_new = '''window.performLogOut = function() {
    closeDrawerModalDirect();
    token = null;
    userId = null;
    userProfile = null;
    isGuest = false;
    localStorage.removeItem('streamora_jwt');
    localStorage.removeItem('streamora_profile');
    showAuthScreen();
};'''
content = content.replace(logout_old, logout_new)

with open(r'c:\Users\vedan\OneDrive\Attachments\Documents\GitHub\aurora-ai\frontend\app.js', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated app.js')
