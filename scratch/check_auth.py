import sys

with open(r'c:\Users\vedan\OneDrive\Attachments\Documents\GitHub\aurora-ai\frontend\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('scratch/auth_init_check.txt', 'w', encoding='utf-8') as out:
    for i, l in enumerate(lines[:500]):
        # Look for auth initialization or DOMContentLoaded
        if 'DOMContentLoaded' in l or 'auth-screen' in l or 'localStorage' in l or 'initApp' in l or 'checkAuth' in l or 'token' in l:
            out.write(f'{i+1}: {l}')
