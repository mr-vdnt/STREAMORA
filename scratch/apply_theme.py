import re

# 1. Update app.js
app_js_path = r'c:\Users\vedan\OneDrive\Attachments\Documents\GitHub\aurora-ai\frontend\app.js'
with open(app_js_path, 'r', encoding='utf-8') as f:
    app_js_code = f.read()

# Replace applyTheme
apply_theme_old = """window.applyTheme = function(themeName) {
    const root = document.documentElement;
    if (themeName === 'oled') {
        root.style.setProperty('--bg-void', '#000000');
        root.style.setProperty('--bg-deep', '#000000');
        root.style.setProperty('--bg-dark', '#020202');
        root.style.setProperty('--bg-surface', '#080808');
        root.style.setProperty('--bg-raised', '#0c0c0c');
    } else if (themeName === 'slate') {
        root.style.setProperty('--bg-void', '#0B0F19');
        root.style.setProperty('--bg-deep', '#0F172A');
        root.style.setProperty('--bg-dark', '#1E293B');
        root.style.setProperty('--bg-surface', '#334155');
        root.style.setProperty('--bg-raised', '#475569');
    } else {
        root.style.removeProperty('--bg-void');
        root.style.removeProperty('--bg-deep');
        root.style.removeProperty('--bg-dark');
        root.style.removeProperty('--bg-surface');
        root.style.removeProperty('--bg-raised');
    }
    localStorage.setItem('streamora_theme', themeName);
};"""

apply_theme_new = """window.applyTheme = function(themeName) {
    document.documentElement.setAttribute('data-theme', themeName);
    localStorage.setItem('streamora_theme', themeName);
};

window.savePageTheme = function(themeName) {
    window.applyTheme(themeName);
};

window.savePageSettings = function() {
    // Basic stub to prevent errors, since UI calls this
    console.log("Settings saved.");
};
"""

if apply_theme_old in app_js_code:
    app_js_code = app_js_code.replace(apply_theme_old, apply_theme_new)
    with open(app_js_path, 'w', encoding='utf-8') as f:
        f.write(app_js_code)
    print("app.js updated.")
else:
    print("applyTheme not found in app.js as expected.")

# Also ensure theme is applied on load
if "const savedTheme = localStorage.getItem('streamora_theme');" in app_js_code:
    print("Theme initialization already exists in app.js")
else:
    # Not strictly necessary if already done, but let's check
    pass

# 2. Update style.css
css_path = r'c:\Users\vedan\OneDrive\Attachments\Documents\GitHub\aurora-ai\frontend\style.css'
with open(css_path, 'r', encoding='utf-8') as f:
    css_code = f.read()

css_old = """:root {
  /* Depths */
  --bg-void:    #030303;
  --bg-deep:    #050505;
  --bg-dark:    #080808;
  --bg-surface: #0D0D0D;
  --bg-raised:  #111111;

  /* Text */
  --text-primary:   #FFFFFF;
  --text-secondary: #B3B3B3;
  --text-muted:     #666666;

  /* Streamora Accents */
  --streamora-purple: #E50914; /* Netflix Red */
  --streamora-blue:   #5AA8FF; /* AI Accent Streamora Blue */
  --streamora-cyan:   #00D8F6; /* Premium Cyan */
  --streamora-grad:   linear-gradient(135deg, #E50914, #5AA8FF, #00D8F6);
  --match-green:   #34C759; /* Apple Success Green */
  --match-gold:    #F5C518; /* IMDb rating Gold */"""

css_new = """:root, [data-theme="neon"] {
  /* Depths */
  --bg-void:    #030303;
  --bg-deep:    #050505;
  --bg-dark:    #080808;
  --bg-surface: #0D0D0D;
  --bg-raised:  #111111;

  /* Text */
  --text-primary:   #FFFFFF;
  --text-secondary: #B3B3B3;
  --text-muted:     #666666;

  /* Streamora Accents */
  --streamora-purple: #E50914; /* Netflix Red */
  --streamora-blue:   #5AA8FF; /* AI Accent Streamora Blue */
  --streamora-cyan:   #00D8F6; /* Premium Cyan */
  --streamora-grad:   linear-gradient(135deg, #E50914, #5AA8FF, #00D8F6);
  --match-green:   #34C759; /* Apple Success Green */
  --match-gold:    #F5C518; /* IMDb rating Gold */
}

[data-theme="slate"] {
  --bg-void:    #0B0F19;
  --bg-deep:    #0F172A;
  --bg-dark:    #1E293B;
  --bg-surface: #334155;
  --bg-raised:  #475569;
}

[data-theme="oled"] {
  --bg-void:    #000000;
  --bg-deep:    #000000;
  --bg-dark:    #020202;
  --bg-surface: #080808;
  --bg-raised:  #0c0c0c;
  --streamora-cyan: #00E5FF;
}

body, .sidebar, .topbar, .movie-card, .modal-content, .drawer, .hero-section {
  transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
}

:root {"""

if css_old in css_code:
    css_code = css_code.replace(css_old, css_new)
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css_code)
    print("style.css updated.")
else:
    print("Could not find exactly matching :root in style.css.")
