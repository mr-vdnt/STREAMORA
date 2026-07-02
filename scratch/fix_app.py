import re

js_path = r'c:\Users\vedan\OneDrive\Attachments\Documents\GitHub\aurora-ai\frontend\app.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Update DOMContentLoaded logic
old_dom_auth = """    // Auth Check
    if (token) {
        try {
            const res = await authFetch('/me');
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
    }"""

new_dom_auth = """    // Auth Check
    if (token) {
        try {
            const res = await authFetch('/me');
            if (res.ok) {
                const userData = await res.json();
                userProfile = userData;
                userId = userData.id;
                isGuest = false;
                await syncWatchlistFromBackend();
                hideAuthScreen();
                initApp();
            } else {
                // Token is invalid
                localStorage.removeItem('streamora_jwt');
                localStorage.removeItem('streamora_profile');
                token = null;
                showAuthScreen();
            }
        } catch(e) {
            localStorage.removeItem('streamora_jwt');
            localStorage.removeItem('streamora_profile');
            token = null;
            showAuthScreen();
        }
    } else {
        showAuthScreen();
    }"""

js = js.replace(old_dom_auth, new_dom_auth)

# 2. Update hover portal click listener
hover_click_logic = """
hoverPortal.addEventListener('click', (e) => {
    // Let buttons handle themselves
    if (e.target.closest('.card-expand__btn')) return;
    
    // Otherwise open modal for the source card
    if (activeSourceCard) {
        const id = activeSourceCard.dataset.id || activeSourceCard.getAttribute('onclick')?.match(/\\d+/)?.[0];
        if (id) {
            openModal(id);
            closePortalCard();
        }
    }
});
"""

# Check if we already appended hoverPortal click logic
if "hoverPortal.addEventListener('click'" not in js:
    # Append to the end
    js += '\n' + hover_click_logic
    
with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)

print("Updated app.js successfully.")
