import os

app_path = r'c:\Users\vedan\OneDrive\Attachments\Documents\GitHub\aurora-ai\frontend\app.js'
with open(app_path, 'r', encoding='utf-8') as f:
    app_code = f.read()

# Fix awards and availability
old_awards = """    document.getElementById('modal-awards').textContent = m.awards || 'None';
    document.getElementById('modal-availability').textContent = m.availability || 'Available on Streamora';"""
new_awards = """    setMetaGrid('modal-awards', m.awards);
    setMetaGrid('modal-availability', m.availability);"""

if old_awards in app_code:
    app_code = app_code.replace(old_awards, new_awards)
    
# Remove static Academy Award Winner text
old_html_awards = """<div style="font-size: 1rem; color: var(--text-primary);">Academy Award Winner / Critic's Choice Award</div>"""
new_html_awards = """"""
if old_html_awards in app_code:
    app_code = app_code.replace(old_html_awards, new_html_awards)

old_html_avail = """<div style="font-size: 1rem; color: var(--streamora-cyan);">Available on Streamora Premium</div>"""
new_html_avail = """"""
if old_html_avail in app_code:
    app_code = app_code.replace(old_html_avail, new_html_avail)

with open(app_path, 'w', encoding='utf-8') as f:
    f.write(app_code)

print("Updated app.js for awards and availability.")
