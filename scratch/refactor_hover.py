import os
import re

css_path = r'c:\Users\vedan\OneDrive\Attachments\Documents\GitHub\aurora-ai\frontend\style.css'
js_path = r'c:\Users\vedan\OneDrive\Attachments\Documents\GitHub\aurora-ai\frontend\app.js'

with open(css_path, 'r', encoding='utf-8') as f:
    css = f.read()

with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# --- CSS CHANGES ---
# Remove all .card-wrap:hover .card-expand logic
css = re.sub(r'\.card-wrap:hover \.card-expand\s*\{[^}]*\}', '', css)
css = re.sub(r'\.card-wrap:first-child \.card-expand\s*\{[^}]*\}', '', css)
css = re.sub(r'\.card-wrap:first-child:hover \.card-expand\s*\{[^}]*\}', '', css)
css = re.sub(r'\.card-wrap:last-child \.card-expand\s*\{[^}]*\}', '', css)
css = re.sub(r'\.card-wrap:last-child:hover \.card-expand\s*\{[^}]*\}', '', css)
css = re.sub(r'\.card-wrap:hover \.card-expand\.expand-[^\s{]*\s*\{[^}]*\}', '', css)

# Make .card-expand hidden by default so it doesn't show in the row
css = css.replace('.card-expand{', '.card-expand{display:none;')

# Add portal CSS
portal_css = '''
/* ── HOVER PORTAL ARCHITECTURE ─────────────────────────────────────── */
#hover-portal {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 90; /* Below sidebar (200), header (100) */
}
.portal-card {
    position: absolute;
    pointer-events: auto;
    width: 340px;
    background: rgba(13,13,13,0.95);
    backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    border-radius: var(--r-lg);
    box-shadow: 0 24px 64px rgba(0,0,0,0.8), 0 0 0 1px rgba(255,255,255,0.04);
    overflow: hidden;
    transform: scale(0.92);
    opacity: 0;
    transition: transform 300ms cubic-bezier(0.22, 1, 0.36, 1), opacity 300ms ease;
    will-change: transform, opacity;
    display: flex;
    flex-direction: column;
}
.portal-card.active {
    transform: scale(1.15);
    opacity: 1;
}
.portal-card.exit {
    transform: scale(0.92);
    opacity: 0;
}
/* Re-use interior styles for portal */
.portal-card .card-expand__img { width:100%; height:150px; object-fit:cover; }
.portal-card .card-expand__body { padding:18px; }
.portal-card .card-expand__title { font-size:1.05rem; font-weight:700; color:white; margin-bottom:6px; }
.portal-card .card-expand__meta { display:flex; align-items:center; gap:8px; font-size:0.85rem; color:var(--text-muted); margin-bottom:12px; }
.portal-card .card-expand__pct { color:var(--match-green); font-weight:700; }
.portal-card .card-expand__genres { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:14px; font-size:0.78rem; color:var(--text-muted); }
.portal-card .card-expand__genres span:not(:last-child)::after { content:"•"; margin-left:6px; }
.portal-card .card-expand__ai { background:rgba(139,92,246,0.08); border:1px solid rgba(139,92,246,0.18); border-radius:var(--r-md); padding:12px; margin-bottom:16px; }
.portal-card .card-expand__ai-label { font-size:0.7rem; text-transform:uppercase; letter-spacing:1px; color:var(--streamora-purple); font-weight:700; margin-bottom:8px; }
.portal-card .card-expand__ai ul { list-style:none; padding:0; margin:0; }
.portal-card .card-expand__ai li { font-size:0.8rem; color:var(--text-secondary); padding:2px 0; display:flex; align-items:center; gap:6px; }
.portal-card .card-expand__btns { display:flex; gap:8px; }
.portal-card .card-expand__btn { width:38px; height:38px; border-radius:50%; border:2px solid rgba(255,255,255,0.35); background:rgba(20,20,20,0.5); color:#fff; display:flex; align-items:center; justify-content:center; cursor:pointer; transition:all 0.2s; }
.portal-card .card-expand__btn:hover { border-color:#fff; background:#fff; color:#000; }
.portal-card .card-expand__btn--play { background:#fff; color:#000; border-color:#fff; }
'''

css = css + '\n' + portal_css

# --- JS CHANGES ---
js_portal_logic = '''
// ══════════════════════════════════════════════════════════════════════
//  HOVER PORTAL ARCHITECTURE (Netflix/Apple TV Style)
// ══════════════════════════════════════════════════════════════════════
let hoverPortal = document.getElementById('hover-portal');
if (!hoverPortal) {
    hoverPortal = document.createElement('div');
    hoverPortal.id = 'hover-portal';
    document.body.appendChild(hoverPortal);
}

let hoverTimer = null;
let activePortalCard = null;
let activeSourceCard = null;

// Clean up portal on scroll to prevent detached floating cards
window.addEventListener('scroll', () => {
    if (activePortalCard) {
        closePortalCard();
    }
}, {passive: true});
document.addEventListener('scroll', (e) => {
    if (e.target.classList && e.target.classList.contains('row-scroll')) {
        if (activePortalCard) closePortalCard();
    }
}, true);

document.addEventListener('mouseenter', (e) => {
    const cardWrap = e.target.closest('.card-wrap');
    if (!cardWrap) return;
    
    // Clear any existing timer
    if (hoverTimer) clearTimeout(hoverTimer);
    
    hoverTimer = setTimeout(() => {
        openPortalCard(cardWrap);
    }, 100); // 100ms delay as requested
}, true);

document.addEventListener('mouseleave', (e) => {
    const cardWrap = e.target.closest('.card-wrap');
    const portalCard = e.target.closest('.portal-card');
    
    if (cardWrap) {
        if (hoverTimer) clearTimeout(hoverTimer);
        // If we leave the cardWrap but don't enter the portalCard (handled by timeout), we close
        setTimeout(() => {
            if (activePortalCard && !activePortalCard.matches(':hover')) {
                closePortalCard();
            }
        }, 50);
    }
    
    if (portalCard) {
        closePortalCard();
    }
}, true);

function openPortalCard(cardWrap) {
    if (activePortalCard) closePortalCard();
    activeSourceCard = cardWrap;
    
    const expandData = cardWrap.querySelector('.card-expand');
    if (!expandData) return;
    
    const rect = cardWrap.getBoundingClientRect();
    const scrollY = window.scrollY;
    
    const portal = document.createElement('div');
    portal.className = 'portal-card';
    portal.innerHTML = expandData.innerHTML;
    
    // Calculate Edge Awareness
    const viewportWidth = window.innerWidth;
    const sidebarWidth = 80; // approximate collapsed sidebar
    
    const cardCenter = rect.left + (rect.width / 2);
    const portalWidth = 340;
    
    let leftPos = rect.left + (rect.width / 2) - (portalWidth / 2);
    let transformOrigin = 'center center';
    
    // Check left bound
    if (leftPos < sidebarWidth + 20) {
        leftPos = rect.left;
        transformOrigin = 'left center';
    } 
    // Check right bound
    else if (leftPos + portalWidth > viewportWidth - 20) {
        leftPos = rect.right - portalWidth;
        transformOrigin = 'right center';
    }
    
    portal.style.left = `${leftPos}px`;
    // Vertically align middle of portal to middle of card
    const portalHeightEst = 400; // rough estimate
    portal.style.top = `${rect.top + scrollY + (rect.height / 2) - (portalHeightEst / 2)}px`;
    portal.style.transformOrigin = transformOrigin;
    
    hoverPortal.appendChild(portal);
    
    // Adjust top precisely after rendering
    const actualHeight = portal.offsetHeight;
    portal.style.top = `${rect.top + scrollY + (rect.height / 2) - (actualHeight / 2)}px`;
    
    // Trigger animation next frame
    requestAnimationFrame(() => {
        portal.classList.add('active');
    });
    
    activePortalCard = portal;
}

function closePortalCard() {
    if (!activePortalCard) return;
    const portal = activePortalCard;
    activePortalCard = null;
    activeSourceCard = null;
    
    portal.classList.remove('active');
    portal.classList.add('exit');
    setTimeout(() => {
        if (portal.parentNode) portal.parentNode.removeChild(portal);
    }, 300);
}
'''

# Find the end of app.js and append it
js = js + '\n' + js_portal_logic

# Also remove the old updateTransformOrigin logic in app.js
js = re.sub(r'const updateTransformOrigin = .*?// Accessibility Keyboard', '// Accessibility Keyboard', js, flags=re.DOTALL)
js = js.replace("document.addEventListener('mouseenter', updateTransformOrigin, true);", "")
js = js.replace("document.addEventListener('focusin', updateTransformOrigin, true);", "")

with open(css_path, 'w', encoding='utf-8') as f:
    f.write(css)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)

print("Hover architecture fully replaced.")
