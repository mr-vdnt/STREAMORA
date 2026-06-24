/* ======================================================================
   AURORA AI — 3D Spatial Cinematic Frontend
   Netflix × Apple TV × VisionOS Experience
   ====================================================================== */

// ── DOM References ────────────────────────────────────────────────────
const sidebar       = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebarNav    = document.getElementById('sidebar-nav');
const profileTrig   = document.getElementById('profile-trigger');
const userIdInput   = document.getElementById('user-id-input');
const topbar        = document.getElementById('topbar');

const searchTrigger = document.getElementById('search-trigger');
const searchOverlay = document.getElementById('search-overlay');
const searchClose   = document.getElementById('search-close');
const searchInput   = document.getElementById('search-input');
const searchResults = document.getElementById('search-results');

const aiTrigger     = document.getElementById('ai-trigger');
const aiPanel       = document.getElementById('ai-panel');
const aiPanelClose  = document.getElementById('ai-panel-close');
const chatInput     = document.getElementById('chat-input');
const sendBtn       = document.getElementById('send-btn');
const chatHistory   = document.getElementById('chat-history');
const acDropdown    = document.getElementById('autocomplete-dropdown');

const mainEl        = document.getElementById('main');
const heroSection   = document.getElementById('hero-section');
const contentRows   = document.getElementById('content-rows');

const modalOverlay  = document.getElementById('movie-detail-modal');
const modalBody     = document.getElementById('modal-body');
const closeModalBtn = document.getElementById('close-modal-btn');

// ── State ─────────────────────────────────────────────────────────────
let globalMovies = [];
let myList = JSON.parse(localStorage.getItem('aurora_mylist') || '[]');
let currentPage = 'home';
let token = localStorage.getItem('aurora_token');
let userId = localStorage.getItem('aurora_user_id') || 32;

async function authFetch(url, options = {}) {
    if (!token) throw new Error('Unauthenticated');
    options.headers = options.headers || {};
    options.headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(url, options);
    if (res.status === 401) {
        document.getElementById('login-overlay').style.display = 'flex';
        token = null;
        localStorage.removeItem('aurora_token');
        throw new Error('Session expired');
    }
    return res;
}

// ══════════════════════════════════════════════════════════════════════
//  INIT
// ══════════════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    const loginOverlay = document.getElementById('login-overlay');
    const loginForm = document.getElementById('login-form');
    const logoutBtn = document.getElementById('logout-btn');
    const adminLink = document.getElementById('admin-link');
    const userDisplay = document.getElementById('current-user-display');
    const loginError = document.getElementById('login-error');

    // Auto-setup Guest Session if not logged in
    if (!token) {
        token = "guest-token";
        userId = 32;
        localStorage.setItem('aurora_token', token);
        localStorage.setItem('aurora_user_id', userId);
        localStorage.setItem('aurora_role', 'Standard');
        localStorage.setItem('aurora_username', 'Guest');
    }

    if (token) {
        if (loginOverlay) loginOverlay.style.display = 'none';
        if (userDisplay) userDisplay.textContent = `User: ${localStorage.getItem('aurora_username') || 'Guest'}`;
        if (logoutBtn) logoutBtn.style.display = 'inline-block';
        if (adminLink) {
            if (localStorage.getItem('aurora_role') === 'Administrator') {
                adminLink.style.display = 'inline-block';
            } else {
                adminLink.style.display = 'none';
            }
        }
        navigateTo('home');
    }

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const fd = new FormData();
            fd.append('username', document.getElementById('login-username').value);
            fd.append('password', document.getElementById('login-password').value);
            try {
                const res = await fetch('/token', { method: 'POST', body: fd });
                if (!res.ok) throw new Error('Failed');
                const data = await res.json();
                token = data.access_token;
                userId = data.user_id;
                localStorage.setItem('aurora_token', token);
                localStorage.setItem('aurora_user_id', userId);
                localStorage.setItem('aurora_role', data.role);
                localStorage.setItem('aurora_username', document.getElementById('login-username').value);
                if (loginOverlay) loginOverlay.style.display = 'none';
                if (loginError) loginError.style.display = 'none';
                if (userDisplay) userDisplay.textContent = `User: ${document.getElementById('login-username').value}`;
                if (logoutBtn) logoutBtn.style.display = 'inline-block';
                if (adminLink) {
                    if (data.role === 'Administrator') {
                        adminLink.style.display = 'inline-block';
                    } else {
                        adminLink.style.display = 'none';
                    }
                }
                navigateTo('home');
            } catch(err) {
                if (loginError) loginError.style.display = 'block';
            }
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('aurora_token');
            localStorage.removeItem('aurora_user_id');
            localStorage.removeItem('aurora_role');
            localStorage.removeItem('aurora_username');
            window.location.reload();
        });
    }
});

// ══════════════════════════════════════════════════════════════════════
//  SIDEBAR & MOBILE NAVIGATION
// ══════════════════════════════════════════════════════════════════════
const mobileMenuBtn = document.getElementById('mobile-menu-btn');
const sidebarBackdrop = document.getElementById('sidebar-backdrop');

function toggleMobileSidebar() {
    sidebar.classList.toggle('open');
    sidebarBackdrop.classList.toggle('active');
    document.body.style.overflow = sidebar.classList.contains('open') ? 'hidden' : '';
}

function closeMobileSidebar() {
    sidebar.classList.remove('open');
    sidebarBackdrop.classList.remove('active');
    document.body.style.overflow = '';
}

sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('expanded');
});

if(mobileMenuBtn) mobileMenuBtn.addEventListener('click', toggleMobileSidebar);
if(sidebarBackdrop) sidebarBackdrop.addEventListener('click', closeMobileSidebar);

// Close sidebar on mobile when clicking a nav link
document.querySelectorAll('.sidebar__link').forEach(link => {
    link.addEventListener('click', () => {
        if (window.innerWidth <= 768) closeMobileSidebar();
    });
});

// Gesture Support
let touchStartX = 0;
let touchEndX = 0;

document.addEventListener('touchstart', e => {
    touchStartX = e.changedTouches[0].screenX;
}, {passive: true});

document.addEventListener('touchend', e => {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
}, {passive: true});

function handleSwipe() {
    if (window.innerWidth > 768) return;
    const swipeDist = touchEndX - touchStartX;
    if (swipeDist > 50 && touchStartX < 30) {
        // Swipe Right from edge
        if (!sidebar.classList.contains('open')) toggleMobileSidebar();
    } else if (swipeDist < -50) {
        // Swipe Left
        if (sidebar.classList.contains('open')) closeMobileSidebar();
    }
}

// Accessibility: Close on Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && sidebar.classList.contains('open')) {
        closeMobileSidebar();
    }
});

// ══════════════════════════════════════════════════════════════════════
//  TOPBAR SCROLL
// ══════════════════════════════════════════════════════════════════════
window.addEventListener('scroll', () => {
    topbar.classList.toggle('scrolled', window.scrollY > 40);
}, { passive: true });

// ══════════════════════════════════════════════════════════════════════
//  PROFILE DROPDOWN
// ══════════════════════════════════════════════════════════════════════
profileTrig.addEventListener('click', (e) => {
    if (e.target.closest('.profile-dropdown') && e.target.tagName !== 'A') return;
    profileTrig.classList.toggle('open');
});
document.addEventListener('click', (e) => {
    if (!profileTrig.contains(e.target)) profileTrig.classList.remove('open');
});

// ══════════════════════════════════════════════════════════════════════
//  SEARCH OVERLAY
// ══════════════════════════════════════════════════════════════════════
searchTrigger.addEventListener('click', (e) => {
    e.preventDefault();
    navigateTo('search');
});
searchClose.addEventListener('click', closeSearch);
searchOverlay.addEventListener('click', (e) => {
    if (e.target === searchOverlay) closeSearch();
});

function closeSearch() {
    searchOverlay.classList.remove('open');
    searchInput.value = '';
    searchResults.innerHTML = '';
}

let searchTimer;
searchInput.addEventListener('input', () => {
    const q = searchInput.value.trim();
    if (q.length < 2) { searchResults.innerHTML = ''; return; }
    clearTimeout(searchTimer);
    searchTimer = setTimeout(async () => {
        try {
            const r = await authFetch(`/autocomplete?q=${encodeURIComponent(q)}`);
            if (!r.ok) return;
            const titles = await r.json();
            searchResults.innerHTML = titles.map(t => `
                <div class="search-hit" onclick="executeSearch('Similar to ${esc(t)}')">
                    <div>
                        <div class="search-hit__title">${t}</div>
                        <div class="search-hit__sub">Find similar titles</div>
                    </div>
                </div>
            `).join('');
        } catch (e) { /* network error */ }
    }, 250);
});

function executeSearch(query) {
    closeSearch();
    aiPanel.classList.add('open');
    chatInput.value = query;
    handleSend();
}

// ══════════════════════════════════════════════════════════════════════
//  AI PANEL
// ══════════════════════════════════════════════════════════════════════
aiTrigger.addEventListener('click', () => aiPanel.classList.add('open'));
aiPanelClose.addEventListener('click', () => aiPanel.classList.remove('open'));

function addMsg(text, isUser) {
    const d = document.createElement('div');
    d.className = `ai-msg ${isUser ? 'ai-msg--user' : 'ai-msg--bot'}`;
    d.innerHTML = text;
    chatHistory.appendChild(d);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

async function handleSend() {
    const query = chatInput.value.trim();
    if (!query) return;
    const userId = parseInt(userIdInput.value) || 32;

    addMsg(query, true);
    chatInput.value = '';
    acDropdown.style.display = 'none';

    showSkeletonRows();

    try {
        const resp = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, query })
        });
        const data = await resp.json();

        if (data.intent === 'explanation') {
            addMsg(data.response, false);
            contentRows.innerHTML = '';
            return;
        }

        let movies = Array.isArray(data.response) ? data.response : (data.response && data.response.value);
        if (movies && movies.length > 0) {
            let rowTitle = 'Aurora Recommendations';
            if (data.intent === 'trending') rowTitle = 'Trending Now';
            else if (data.intent === 'similar_movies') rowTitle = 'Because You Searched';
            else if (data.intent === 'genre_search') rowTitle = 'Genre Discovery';

            renderResults(movies, rowTitle);
            addMsg(`Found ${movies.length} titles for you.`, false);
        } else {
            contentRows.innerHTML = '';
            addMsg("I couldn't find anything matching that.", false);
        }
    } catch (err) {
        contentRows.innerHTML = '';
        addMsg('Connection issue. Please try again.', false);
    }
}

sendBtn.addEventListener('click', handleSend);
chatInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') handleSend(); });

// Autocomplete
let acTimer;
chatInput.addEventListener('input', () => {
    const q = chatInput.value.trim();
    if (q.length < 2) { acDropdown.style.display = 'none'; return; }
    clearTimeout(acTimer);
    acTimer = setTimeout(async () => {
        try {
            const r = await authFetch(`/autocomplete?q=${encodeURIComponent(q)}`);
            if (!r.ok) return;
            const list = await r.json();
            if (list.length > 0) {
                acDropdown.innerHTML = list.map(t =>
                    `<div class="ac-item" onclick="pickAc('${esc(t)}')">${t}</div>`
                ).join('');
                acDropdown.style.display = 'block';
            } else {
                acDropdown.style.display = 'none';
            }
        } catch (e) { /* ignore */ }
    }, 300);
});

function pickAc(title) {
    chatInput.value = `Similar to ${title}`;
    acDropdown.style.display = 'none';
    handleSend();
}

// ══════════════════════════════════════════════════════════════════════
//  SPA ROUTER
// ══════════════════════════════════════════════════════════════════════
function navigateTo(page) {
    currentPage = page;
    window.shownItems = []; 

    document.querySelectorAll('.sidebar__link').forEach(l => {
        l.classList.toggle('active', l.dataset.page === page);
    });
    document.querySelectorAll('.bottom-nav__item').forEach(l => {
        l.classList.toggle('active', l.dataset.page === page);
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });

    switch (page) {
        case 'home':
            loadHomePage();
            break;
        case 'categories':
            loadCategoriesTab();
            break;
        case 'library':
            renderLibraryTab();
            break;
        case 'search':
            loadSearchPage();
            break;
        case 'my-list':
            renderMyList();
            break;
    }
}

// ── Home Page ─────────────────────────────────────────────────────────
async function loadHomePage() {
    heroSection.innerHTML = '';
    heroSection.style.display = 'none';
    contentRows.innerHTML = '';
    showSkeletonRows();

    window.shownItems = []; 

    await fetchAndRender('Top Picks For You', 'Top Picks For You', true);
    await fetchAndRender('Trending Now', 'Trending Now', false);
    await fetchAndRender('Mind-Bending Sci-Fi', 'Mind-Bending Sci-Fi', false);

    const genres = [
        { q: 'Action', title: 'Action Thrillers' },
        { q: 'Comedy', title: 'Comedy Classics' },
        { q: 'Horror', title: 'Horror & Supernatural' },
        { q: 'Drama', title: 'Dramatic Masterpieces' },
        { q: 'Romance', title: 'Romance & Love Stories' },
        { q: 'Thriller', title: 'High-Stakes Thrillers' },
        { q: 'Anime', title: 'Anime & Animation' },
        { q: 'Hidden Gems', title: 'Hidden Gems' }
    ];

    for (const g of genres) {
        await new Promise(resolve => setTimeout(resolve, 80));
        await fetchAndRender(g.q, g.title, false);
    }
}

// ── Category Page ─────────────────────────────────────────────────────
async function loadCategoryPage(mainQuery, extraQueries, pageTitle) {
    heroSection.innerHTML = '';
    heroSection.style.display = 'none';
    contentRows.innerHTML = `
        <div class="row-section" style="padding-top:80px;">
            <h1 class="row-section__title" style="font-size:2.2rem;margin-bottom:32px;">${pageTitle}</h1>
        </div>
    `;
    showSkeletonRows(false);
    await fetchAndRender(mainQuery, `Popular ${pageTitle}`);

    for (const q of extraQueries) {
        await fetchAndRender(q, q);
    }
}

async function fetchAndRender(query, rowTitle, isHero = false) {
    try {
        const resp = await authFetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, exclude_ids: window.shownItems || [] })
        });
        const data = await resp.json();
        let movies = Array.isArray(data.response) ? data.response : (data.response && data.response.value);
        if (movies && movies.length > 0) {
            movies.forEach(m => {
                if (!window.shownItems.includes(m.item_id)) {
                    window.shownItems.push(m.item_id);
                }
            });
            globalMovies = [...globalMovies, ...movies];
            
            if (isHero && !heroSection.innerHTML) {
                renderHero(movies[0]);
                appendRow(rowTitle, movies.slice(1));
            } else {
                appendRow(rowTitle, movies);
            }
            }
        }
    } catch (e) { /* silently skip failed row */ }
}

// ── My List ───────────────────────────────────────────────────────────
function renderMyList() {
    heroSection.innerHTML = '';
    heroSection.style.display = 'none';

    if (myList.length === 0) {
        contentRows.innerHTML = `
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:70vh;text-align:center;padding:0 20px;">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg>
                <h2 style="font-size:2rem;font-weight:700;color:var(--text-primary);margin:24px 0 12px;">Your Watchlist is Empty</h2>
                <p style="color:var(--text-muted);max-width:400px;">Browse movies and click the + button on any card to save it here.</p>
            </div>
        `;
        return;
    }

    contentRows.innerHTML = '';
    appendRow('My Watchlist', myList);
}

function toggleMyList(movie) {
    const idx = myList.findIndex(m => m.item_id === movie.item_id);
    if (idx >= 0) {
        myList.splice(idx, 1);
    } else {
        myList.push(movie);
    }
    localStorage.setItem('aurora_mylist', JSON.stringify(myList));
}

function isInMyList(id) {
    return myList.some(m => m.item_id === id);
}

// ── Click History Tracking ───────────────────────────────────────────
function addToHistory(movie) {
    if (!movie) return;
    let history = JSON.parse(localStorage.getItem('aurora_history') || '[]');
    history = history.filter(m => m.item_id !== movie.item_id);
    history.unshift(movie);
    if (history.length > 10) history.pop();
    localStorage.setItem('aurora_history', JSON.stringify(history));
}

// ── Categories Tab ───────────────────────────────────────────────────
let selectedCategory = null;

function loadCategoriesTab() {
    heroSection.innerHTML = '';
    heroSection.style.display = 'none';
    
    if (selectedCategory) {
        loadSingleCategoryPage(selectedCategory);
    } else {
        renderCategorySelectionGrid();
    }
}

function renderCategorySelectionGrid() {
    contentRows.innerHTML = `
        <div class="category-selection-container" style="padding: 80px 24px 24px;">
            <h1 style="font-size: 2.2rem; font-weight: 800; color: var(--text-primary); margin-bottom: 32px;">Explore Categories</h1>
            <div class="category-cards-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 16px;">
                ${[
                    { name: 'Action', grad: 'linear-gradient(135deg, #EF4444, #B91C1C)', icon: '🎬' },
                    { name: 'Comedy', grad: 'linear-gradient(135deg, #F59E0B, #D97706)', icon: '😂' },
                    { name: 'Sci-Fi', grad: 'linear-gradient(135deg, #8B5CF6, #4C1D95)', icon: '🚀' },
                    { name: 'Horror', grad: 'linear-gradient(135deg, #374151, #111827)', icon: '👻' },
                    { name: 'Drama', grad: 'linear-gradient(135deg, #3B82F6, #1D4ED8)', icon: '🎭' },
                    { name: 'Romance', grad: 'linear-gradient(135deg, #EC4899, #BE185D)', icon: '💖' },
                    { name: 'Thriller', grad: 'linear-gradient(135deg, #10B981, #047857)', icon: '🕵️' },
                    { name: 'Anime', grad: 'linear-gradient(135deg, #06B6D4, #0891B2)', icon: '🌸' },
                    { name: 'Mind-Bending', grad: 'linear-gradient(135deg, #EC4899, #8B5CF6)', icon: '🌀' },
                    { name: 'Hidden Gems', grad: 'linear-gradient(135deg, #14B8A6, #0F766E)', icon: '💎' }
                ].map(c => `
                    <div class="category-card" onclick="selectCategory('${c.name}')" 
                         style="background: ${c.grad}; height: 110px; border-radius: var(--r-md); display: flex; flex-direction: column; justify-content: center; align-items: center; cursor: pointer; transition: transform var(--t-fast) var(--ease-out), box-shadow var(--t-fast) var(--ease-out); border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 8px 16px rgba(0,0,0,0.3);">
                        <span style="font-size: 2rem; margin-bottom: 8px;">${c.icon}</span>
                        <span style="font-weight: 700; color: white; font-size: 0.95rem; text-shadow: 0 2px 4px rgba(0,0,0,0.5);">${c.name}</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    
    document.querySelectorAll('.category-card').forEach(card => {
        card.addEventListener('mouseover', () => {
            card.style.transform = 'translateY(-4px) scale(1.03)';
            card.style.boxShadow = '0 12px 24px rgba(0,0,0,0.4)';
        });
        card.addEventListener('mouseout', () => {
            card.style.transform = 'translateY(0) scale(1)';
            card.style.boxShadow = '0 8px 16px rgba(0,0,0,0.3)';
        });
    });
}

function selectCategory(name) {
    selectedCategory = name;
    loadSingleCategoryPage(name);
}

async function loadSingleCategoryPage(categoryName) {
    contentRows.innerHTML = `
        <div class="category-detail-header" style="padding: 80px 24px 24px; display: flex; align-items: center; gap: 16px;">
            <button class="back-btn" onclick="selectedCategory = null; loadCategoriesTab();" 
                    style="display: flex; align-items: center; gap: 8px; color: var(--text-primary); background: var(--glass-bg-2); border: 1px solid var(--glass-border); padding: 8px 16px; border-radius: var(--r-pill); font-size: 0.9rem; font-weight: 600; cursor: pointer;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
                Back
            </button>
            <h1 class="category-detail-title" style="font-size: 2.2rem; font-weight: 800; color: var(--text-primary); margin: 0;">${categoryName}</h1>
        </div>
        <div id="category-grid-results" class="movies-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 20px; padding: 0 24px 40px;">
        </div>
    `;
    
    const gridResults = document.getElementById('category-grid-results');
    gridResults.innerHTML = Array(12).fill(0).map(() => `
        <div class="card-wrap skeleton" style="height: 220px; border-radius: var(--r-md); aspect-ratio: 2/3; width: 100%;"></div>
    `).join('');
    
    try {
        const resp = await authFetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: categoryName, exclude_ids: [] })
        });
        const data = await resp.json();
        let movies = Array.isArray(data.response) ? data.response : (data.response && data.response.value);
        if (movies && movies.length > 0) {
            gridResults.innerHTML = '';
            globalMovies = [...globalMovies, ...movies];
            movies.forEach(movie => {
                const card = document.createElement('div');
                card.innerHTML = createMovieCardHTML(movie);
                const card3d = card.querySelector('.card-3d');
                if (card3d) attachTilt(card3d);
                gridResults.appendChild(card.firstElementChild);
            });
        } else {
            gridResults.innerHTML = `<div class="no-results" style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 40px;">No titles found for ${categoryName}.</div>`;
        }
    } catch(e) {
        gridResults.innerHTML = `<div class="no-results" style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 40px;">Error loading titles. Please try again.</div>`;
    }
}

function createMovieCardHTML(movie) {
    const m = movie.rich_metadata || {};
    const t = movie.title || 'Unknown';
    const poster = movie.poster_url || placeholder(t);
    const backdrop = movie.backdrop_url || poster;
    const score = m.match_percentage || randScore();
    const genres = (m.tags || []).slice(0, 3).map(g => `<span>${g}</span>`).join('');
    const saved = isInMyList(movie.item_id);

    return `
    <div class="card-wrap" onclick="openModal(${movie.item_id})" style="cursor: pointer;">
        <div class="card-3d" data-id="${movie.item_id}" tabindex="0">
            <img src="${poster}" alt="${t}" loading="lazy" onerror="this.src='${placeholder(t)}'">
            <div class="card-3d__badge">${score}%</div>
        </div>
        <div class="card-expand">
            <img src="${backdrop}" class="card-expand__img" alt="" loading="lazy" onerror="this.src='${placeholder(t)}'">
            <div class="card-expand__body">
                <div class="card-expand__title">${t}</div>
                <div class="card-expand__meta">
                    <span class="card-expand__pct">${score}% Match</span>
                    ${m.year ? `<span>${m.year}</span>` : ''}
                    ${m.runtime ? `<span>${m.runtime}</span>` : ''}
                </div>
                <div class="card-expand__genres">${genres}</div>
                <div class="card-expand__ai">
                    <div class="card-expand__ai-label">Why Aurora Picked This</div>
                    <ul>
                        <li>Matches your preferred genres</li>
                        <li>High thematic similarity</li>
                        <li>Popular among similar viewers</li>
                    </ul>
                </div>
                <div class="card-expand__btns">
                    <button class="card-expand__btn card-expand__btn--play" onclick="event.stopPropagation(); openModal(${movie.item_id})" aria-label="Play">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
                    </button>
                    <button class="card-expand__btn" onclick="event.stopPropagation(); toggleSave(${movie.item_id}); this.setAttribute('aria-label', isInMyList(${movie.item_id}) ? 'Remove from list' : 'Add to list'); this.querySelector('svg').innerHTML = isInMyList(${movie.item_id}) ? '<line x1=&quot;5&quot; y1=&quot;12&quot; x2=&quot;19&quot; y2=&quot;12&quot;/>' : '<line x1=&quot;12&quot; y1=&quot;5&quot; x2=&quot;12&quot; y2=&quot;19&quot;/><line x1=&quot;5&quot; y1=&quot;12&quot; x2=&quot;19&quot; y2=&quot;12&quot;/>';" aria-label="${saved ? 'Remove from list' : 'Add to list'}">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            ${saved ? '<line x1="5" y1="12" x2="19" y2="12"/>' : '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>'}
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    </div>`;
}

// ── Library Tab ──────────────────────────────────────────────────────
async function renderLibraryTab() {
    heroSection.innerHTML = '';
    heroSection.style.display = 'none';
    contentRows.innerHTML = `
        <div class="row-section" style="padding-top:80px;">
            <h1 class="row-section__title" style="font-size:2.2rem;margin-bottom:32px;">Your Library</h1>
        </div>
    `;
    
    const history = JSON.parse(localStorage.getItem('aurora_history') || '[]');
    const watchlist = JSON.parse(localStorage.getItem('aurora_mylist') || '[]');
    
    if (watchlist.length > 0) {
        appendRow('Your Watchlist', watchlist);
    }
    
    if (history.length > 0) {
        appendRow('Recently Viewed', history);
        
        const seedMovie = history[0];
        await fetchAndRender(`Similar to ${seedMovie.title}`, `Because You Watched ${seedMovie.title}`);
    } else if (watchlist.length > 0) {
        const seedMovie = watchlist[0];
        await fetchAndRender(`Similar to ${seedMovie.title}`, `Because You Watched ${seedMovie.title}`);
    } else {
        contentRows.innerHTML += `
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:40vh;text-align:center;padding:0 20px;">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 19.5A2.5 2.5 0 0 0 6.5 22H20M4 19.5V3.5A2.5 2.5 0 0 1 6.5 1H20v21H6.5a2.5 2.5 0 0 1-2.5-2.5z"/></svg>
                <h2 style="font-size:1.8rem;color:var(--text-primary);margin:20px 0 10px;">Library is Empty</h2>
                <p style="color:var(--text-muted);max-width:400px;margin-bottom:24px;">Start browsing movies or add them to your watchlist to see personalized rows here.</p>
            </div>
        `;
        await fetchAndRender('Hidden Gems', 'Recommended For You');
    }
}

// ── Search Tab ──────────────────────────────────────────────────────
function loadSearchPage() {
    heroSection.innerHTML = '';
    heroSection.style.display = 'none';
    
    contentRows.innerHTML = `
        <div class="search-chatbot-container" style="padding: 80px 24px 20px; display: flex; flex-direction: column; height: calc(100vh - 150px); max-height: 700px; max-width: 800px; margin: 0 auto;">
            <div class="search-chatbot-header" style="text-align: center; margin-bottom: 20px;">
                <h1 style="font-size: 2rem; font-weight: 800; color: white; display: flex; align-items: center; justify-content: center; gap: 10px;">
                    <span class="ai-glow">✦</span> Aurora Assistant
                </h1>
                <p style="color: var(--text-muted); font-size: 0.9rem; margin-top: 6px;">Your conversational search. Enter movie titles, genres, moods, or themes.</p>
            </div>
            
            <div id="search-chat-history" class="chat-history-container" style="flex: 1; overflow-y: auto; padding: 16px; background: rgba(255,255,255,0.02); border: 1px solid var(--glass-border); border-radius: var(--r-lg); display: flex; flex-direction: column; gap: 16px; margin-bottom: 16px; scrollbar-width: none;">
                <div class="ai-msg ai-msg--bot" style="animation: msgIn 0.3s var(--ease-out);">
                    Hi! I'm Aurora, your AI cinematic companion. Type a movie name, genre, or request below, and I'll find the perfect match for you.<br><br>
                    💡 Try asking:<br>
                    • <em>"Recommend some mind-bending sci-fi movies"</em><br>
                    • <em>"Show me dark psychological thrillers"</em><br>
                    • <em>"Find movies similar to Interstellar"</em>
                </div>
            </div>
            
            <div class="search-chat-input-wrapper" style="position: relative; display: flex; gap: 10px; align-items: center;">
                <div style="position: relative; flex: 1;">
                    <input type="text" id="search-chat-input" placeholder="Search by name, genre, or describe your mood..." 
                           style="width: 100%; padding: 14px 20px; border-radius: var(--r-pill); background: rgba(255,255,255,0.04); border: 1px solid var(--glass-border); color: white; font-size: 0.95rem; outline: none; transition: border-color var(--t-fast);"
                           autocomplete="off">
                    <div id="search-autocomplete-dropdown" style="position: absolute; bottom: 100%; left: 0; right: 0; background: rgba(15,15,15,0.95); backdrop-filter: blur(20px); border: 1px solid var(--glass-border); border-radius: var(--r-md); max-height: 200px; overflow-y: auto; display: none; z-index: 10;"></div>
                </div>
                <button id="search-chat-send" 
                        style="width: 48px; height: 48px; border-radius: 50%; background: var(--aurora-cyan); color: black; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: transform var(--t-fast);"
                        onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                </button>
            </div>
        </div>
    `;
    
    const historyContainer = document.getElementById('search-chat-history');
    historyContainer.scrollTop = historyContainer.scrollHeight;
    
    const input = document.getElementById('search-chat-input');
    const send = document.getElementById('search-chat-send');
    const acDropdown = document.getElementById('search-autocomplete-dropdown');
    
    send.onclick = () => handleSearchSend(input, historyContainer, acDropdown);
    input.onkeydown = (e) => {
        if (e.key === 'Enter') handleSearchSend(input, historyContainer, acDropdown);
    };
    
    let searchAcTimer;
    input.addEventListener('input', () => {
        const q = input.value.trim();
        if (q.length < 2) { acDropdown.style.display = 'none'; return; }
        clearTimeout(searchAcTimer);
        searchAcTimer = setTimeout(async () => {
            try {
                const r = await authFetch(`/autocomplete?q=${encodeURIComponent(q)}`);
                if (!r.ok) return;
                const list = await r.json();
                if (list.length > 0) {
                    acDropdown.innerHTML = list.map(t =>
                        `<div class="ac-item" style="padding: 10px 16px; cursor: pointer; border-bottom: 1px solid rgba(255,255,255,0.03); transition: background 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.05)'" onmouseout="this.style.background='transparent'" onclick="pickSearchAc('${esc(t)}', document.getElementById('search-chat-input'), document.getElementById('search-autocomplete-dropdown'), document.getElementById('search-chat-history'))">${t}</div>`
                    ).join('');
                    acDropdown.style.display = 'block';
                } else {
                    acDropdown.style.display = 'none';
                }
            } catch (e) { /* ignore */ }
        }, 200);
    });
}

function pickSearchAc(title, input, dropdown, history) {
    input.value = `Similar to ${title}`;
    dropdown.style.display = 'none';
    handleSearchSend(input, history, dropdown);
}

async function handleSearchSend(input, historyContainer, dropdown) {
    const query = input.value.trim();
    if (!query) return;
    
    input.value = '';
    dropdown.style.display = 'none';
    
    addSearchMsg(query, true, historyContainer);
    
    const loadingId = 'bot-loading-' + Date.now();
    addSearchMsg('<div class="skeleton" style="width: 50px; height: 16px;"></div>', false, historyContainer, loadingId);
    
    try {
        const resp = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify({ user_id: userId, query, exclude_ids: [] })
        });
        const data = await resp.json();
        
        const loadingBubble = document.getElementById(loadingId);
        if (loadingBubble) loadingBubble.remove();
        
        if (data.intent === 'explanation') {
            addSearchMsg(data.response, false, historyContainer);
            return;
        }
        
        let movies = Array.isArray(data.response) ? data.response : (data.response && data.response.value);
        if (movies && movies.length > 0) {
            addSearchMsg(`Found ${movies.length} titles for you:`, false, historyContainer);
            
            const rowSection = document.createElement('div');
            rowSection.style.margin = '10px 0';
            rowSection.style.width = '100%';
            
            const scrollContainer = document.createElement('div');
            scrollContainer.style.display = 'flex';
            scrollContainer.style.gap = '12px';
            scrollContainer.style.overflowX = 'auto';
            scrollContainer.style.padding = '8px 0';
            scrollContainer.style.scrollbarWidth = 'none';
            
            movies.forEach(movie => {
                const card = document.createElement('div');
                card.style.minWidth = '110px';
                card.style.width = '110px';
                card.style.flex = '0 0 auto';
                card.style.cursor = 'pointer';
                card.onclick = () => openModal(movie.item_id);
                
                const m = movie.rich_metadata || {};
                const poster = movie.poster_url || placeholder(movie.title);
                
                card.innerHTML = `
                    <div style="position: relative; border-radius: var(--r-sm); overflow: hidden; aspect-ratio: 2/3; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                        <img src="${poster}" alt="${movie.title}" style="width: 100%; height: 100%; object-fit: cover;">
                        <div style="position: absolute; top: 4px; right: 4px; background: rgba(0,0,0,0.8); color: var(--match-green); font-size: 0.7rem; font-weight: 700; padding: 2px 4px; border-radius: 4px;">${m.match_percentage || 88}%</div>
                    </div>
                    <div style="font-size: 0.75rem; font-weight: 600; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 4px; text-align: center;">${movie.title}</div>
                `;
                scrollContainer.appendChild(card);
            });
            
            rowSection.appendChild(scrollContainer);
            historyContainer.appendChild(rowSection);
            historyContainer.scrollTop = historyContainer.scrollHeight;
            
            globalMovies = [...globalMovies, ...movies];
        } else {
            addSearchMsg("I couldn't find anything matching that. Try typing another genre or name!", false, historyContainer);
        }
    } catch(err) {
        const loadingBubble = document.getElementById(loadingId);
        if (loadingBubble) loadingBubble.remove();
        addSearchMsg('Connection issue. Please try again.', false, historyContainer);
    }
}

function addSearchMsg(text, isUser, container, id) {
    const d = document.createElement('div');
    d.className = `ai-msg ${isUser ? 'ai-msg--user' : 'ai-msg--bot'}`;
    if (id) d.id = id;
    d.innerHTML = text;
    d.style.animation = 'msgIn 0.3s var(--ease-out)';
    container.appendChild(d);
    container.scrollTop = container.scrollHeight;
}

// ══════════════════════════════════════════════════════════════════════
//  RENDER ENGINE
// ══════════════════════════════════════════════════════════════════════

function renderResults(movies, mainTitle, isHome = false) {
    globalMovies = movies;
    contentRows.innerHTML = '';

    const sorted = [...movies].sort((a, b) => {
        return getScore(b) - getScore(a);
    });

    // Hero = #1
    renderHero(sorted[0]);

    const rest = sorted.slice(1);

    if (isHome) {
        appendRow(mainTitle, rest);
        const tierS = rest.filter(m => getScore(m) >= 95);
        const tierA = rest.filter(m => { const s = getScore(m); return s >= 88 && s < 95; });
        const tierB = rest.filter(m => getScore(m) < 88);
        if (tierS.length > 0) appendRow('Perfect Matches', tierS);
        if (tierA.length > 0) appendRow('Because You Watched Similar', tierA);
        if (tierB.length > 0) appendRow('Hidden Gems', tierB);
    } else {
        appendRow(mainTitle, rest);
    }
}

function renderHero(movie) {
    if (!movie) { heroSection.style.display = 'none'; return; }
    const m = movie.rich_metadata || {};
    const title = movie.title || 'Unknown';
    const bg = movie.backdrop_url || movie.poster_url || placeholder(title);
    const score = m.match_percentage || randScore();
    const synopsis = m.story_summary || movie.overview || 'A cinematic masterpiece recommended by Aurora AI.';
    const genres = (m.tags || ['Drama']).slice(0, 4).map(g => `<span class="gpill">${g}</span>`).join('');

    heroSection.style.display = 'flex';
    heroSection.innerHTML = `
        <div class="hero__bg" style="background-image:url('${bg}')"></div>
        <div class="hero__overlay"></div>
        <div class="hero__inner" onclick="openModal(${movie.item_id})" style="cursor: pointer;">
            <div class="hero__match">★ ${score}% Aurora Match</div>
            <h1 class="hero__title">${title}</h1>
            <div class="hero__meta">
                ${m.year ? `<span>${m.year}</span><span class="hero__meta-dot"></span>` : ''}
                ${m.runtime ? `<span>${m.runtime}</span><span class="hero__meta-dot"></span>` : ''}
                <span style="color:var(--match-green)">Highly Recommended</span>
            </div>
            <div class="hero__genres">${genres}</div>
            <p class="hero__desc">${synopsis}</p>
            <div class="hero__btns">
                <button class="hero-btn hero-btn--play" onclick="event.stopPropagation(); openModal(${movie.item_id})">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> Play
                </button>
                <button class="hero-btn hero-btn--info" onclick="event.stopPropagation(); openModal(${movie.item_id})">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg> More Info
                </button>
            </div>
        </div>
    `;
}

function appendRow(title, movies) {
    if (!movies || movies.length === 0) return;

    const sec = document.createElement('section');
    sec.className = 'row-section';

    const cards = movies.map((movie, i) => {
        const m = movie.rich_metadata || {};
        const t = movie.title || 'Unknown';
        const poster = movie.poster_url || placeholder(t);
        const backdrop = movie.backdrop_url || poster;
        const score = m.match_percentage || randScore();
        const genres = (m.tags || []).slice(0, 3).map(g => `<span>${g}</span>`).join('');
        const saved = isInMyList(movie.item_id);

        return `
        <div class="card-wrap" data-idx="${i}" onclick="openModal(${movie.item_id})" style="cursor: pointer;">
            <div class="card-3d" data-id="${movie.item_id}" tabindex="0">
                <img src="${poster}" alt="${t}" loading="lazy" onerror="this.src='${placeholder(t)}'">
                <div class="card-3d__badge">${score}%</div>
            </div>
            <div class="card-expand">
                <img src="${backdrop}" class="card-expand__img" alt="" loading="lazy" onerror="this.src='${placeholder(t)}'">
                <div class="card-expand__body">
                    <div class="card-expand__title">${t}</div>
                    <div class="card-expand__meta">
                        <span class="card-expand__pct">${score}% Match</span>
                        ${m.year ? `<span>${m.year}</span>` : ''}
                        ${m.runtime ? `<span>${m.runtime}</span>` : ''}
                    </div>
                    <div class="card-expand__genres">${genres}</div>
                    <div class="card-expand__ai">
                        <div class="card-expand__ai-label">Why Aurora Picked This</div>
                        <ul>
                            <li>Matches your preferred genres</li>
                            <li>High thematic similarity</li>
                            <li>Popular among similar viewers</li>
                        </ul>
                    </div>
                    <div class="card-expand__btns">
                        <button class="card-expand__btn card-expand__btn--play" onclick="event.stopPropagation(); openModal(${movie.item_id})" aria-label="Play">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
                        </button>
                        <button class="card-expand__btn" onclick="event.stopPropagation(); toggleSave(${movie.item_id}); this.setAttribute('aria-label', isInMyList(${movie.item_id}) ? 'Remove from list' : 'Add to list'); this.querySelector('svg').innerHTML = isInMyList(${movie.item_id}) ? '<line x1=&quot;5&quot; y1=&quot;12&quot; x2=&quot;19&quot; y2=&quot;12&quot;/>' : '<line x1=&quot;12&quot; y1=&quot;5&quot; x2=&quot;12&quot; y2=&quot;19&quot;/><line x1=&quot;5&quot; y1=&quot;12&quot; x2=&quot;19&quot; y2=&quot;12&quot;/>';" aria-label="${saved ? 'Remove from list' : 'Add to list'}">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                ${saved ? '<line x1="5" y1="12" x2="19" y2="12"/>' : '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>'}
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>`;
    }).join('');

    sec.innerHTML = `
        <h2 class="row-section__title">${title}</h2>
        <div class="row-scroll">${cards}</div>
    `;

    contentRows.appendChild(sec);

    sec.querySelectorAll('.card-3d').forEach(attachTilt);
}

// ══════════════════════════════════════════════════════════════════════
//  3D TILT EFFECT
// ══════════════════════════════════════════════════════════════════════
function attachTilt(card) {
    card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const cx = rect.width / 2;
        const cy = rect.height / 2;
        const rotX = ((y - cy) / cy) * -8;
        const rotY = ((x - cx) / cx) * 8;
        card.style.transform = `perspective(800px) rotateX(${rotX}deg) rotateY(${rotY}deg) scale3d(1.04,1.04,1.04)`;
    });

    card.addEventListener('mouseleave', () => {
        card.style.transform = 'perspective(800px) rotateX(0) rotateY(0) scale3d(1,1,1)';
    });

    card.addEventListener('click', () => {
        const id = parseInt(card.dataset.id);
        if (id) openModal(id);
    });

    card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const id = parseInt(card.dataset.id);
            if (id) openModal(id);
        }
    });
}

// ══════════════════════════════════════════════════════════════════════
//  DETAIL MODAL
// ══════════════════════════════════════════════════════════════════════
async function openModal(id) {
    authFetch('/events/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_type: "click", item_id: id })
    }).catch(e => console.error("Event ingest failed:", e));

    modalOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';

    document.getElementById('modal-title').textContent = 'Loading...';
    document.getElementById('modal-poster').src = '';
    document.getElementById('modal-backdrop').style.backgroundImage = 'none';
    document.getElementById('modal-synopsis').textContent = 'Fetching cinematic details...';
    document.getElementById('modal-genres').innerHTML = '';
    document.getElementById('modal-match').textContent = '';
    document.getElementById('modal-similar').innerHTML = '';

    try {
        const resp = await authFetch(`/movie/${id}`);
        const m = await resp.json();
        
        if (m.error) throw new Error(m.error);

        document.getElementById('modal-title').textContent = m.title || 'Unknown';
        
        const posterUrl = m.poster_url || placeholder(m.title);
        const bgUrl = m.backdrop_url || posterUrl;
        document.getElementById('modal-poster').src = posterUrl;
        document.getElementById('modal-backdrop').style.backgroundImage = `url('${bgUrl}')`;
        
        document.getElementById('modal-match').textContent = `${m.match_percentage || 85}% Match`;
        document.getElementById('modal-year').textContent = m.year || '';
        document.getElementById('modal-rating').textContent = m.rating ? `IMDB ${m.rating}` : '';
        document.getElementById('modal-runtime').textContent = m.runtime || '';
        
        document.getElementById('modal-genres').innerHTML = (m.genres || []).map(g => `<span>${g}</span>`).join('');
        document.getElementById('modal-audience').textContent = m.audience_type || 'General';
        
        document.getElementById('modal-synopsis').textContent = m.story_summary || 'No overview available.';
        document.getElementById('modal-why').textContent = m.why_recommended || 'Highly correlated with your preferences.';
        
        document.getElementById('modal-director').textContent = m.director || 'Unknown';
        
        document.getElementById('modal-themes').innerHTML = (m.themes || []).map(t => `<span>${t}</span>`).join('');
        document.getElementById('modal-moods').innerHTML = (m.moods || []).map(t => `<span>${t}</span>`).join('');
        
        document.getElementById('modal-pacing').textContent = m.pacing || 'Steady';
        document.getElementById('modal-complexity').textContent = m.complexity || 'Medium';
        document.getElementById('modal-world').textContent = m.world_building || 'Standard';
        document.getElementById('modal-action').textContent = m.action_level || 'Medium';
        
        document.getElementById('adv-violence').textContent = m.violence_level || 'Low';
        document.getElementById('adv-language').textContent = m.language_severity || 'Mild';
        document.getElementById('adv-adult').textContent = m.adult ? 'Yes' : 'No';
        
        const simContainer = document.getElementById('modal-similar');
        if (m.similar_movies && m.similar_movies.length > 0) {
            simContainer.innerHTML = m.similar_movies.map(sm => `
                <div class="sim-card" onclick="openModal(${sm.item_id})">
                    <img src="${sm.poster_url || placeholder(sm.title)}" alt="${sm.title}" class="sim-poster">
                    <div class="sim-title">${sm.title}</div>
                    <div class="sim-match">${sm.score}% Match</div>
                </div>
            `).join('');
        } else {
            simContainer.innerHTML = '<p>No similar titles found.</p>';
        }

        const addBtn = document.getElementById('modal-add-list');
        const saved = isInMyList(id);
        addBtn.innerHTML = saved ? `✓ Added` : `+ Add to List`;
        addBtn.onclick = () => {
            toggleSave(id);
            addBtn.innerHTML = isInMyList(id) ? `✓ Added` : `+ Add to List`;
        };

        addToHistory({
            item_id: id,
            title: m.title || 'Unknown',
            poster_url: posterUrl,
            backdrop_url: bgUrl,
            rich_metadata: m
        });

    } catch (err) {
        document.getElementById('modal-title').textContent = 'Error loading details.';
        document.getElementById('modal-synopsis').textContent = 'Could not fetch data.';
    }
}

function toggleSave(id) {
    const movie = globalMovies.find(m => m.item_id === id) || myList.find(m => m.item_id === id);
    if (movie) toggleMyList(movie);
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        modalOverlay.classList.remove('active');
        document.body.style.overflow = '';
        closeSearch();
        aiPanel.classList.remove('open');
    }
});

closeModalBtn.addEventListener('click', () => {
    modalOverlay.classList.remove('active');
    document.body.style.overflow = '';
});
modalOverlay.addEventListener('click', (e) => {
    if (e.target === modalOverlay) {
        modalOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }
});

// ══════════════════════════════════════════════════════════════════════
//  UTILITIES
// ══════════════════════════════════════════════════════════════════════
function getScore(m) {
    return (m.rich_metadata || {}).match_percentage || 80;
}

function randScore() {
    return Math.floor(Math.random() * 12 + 85);
}

function placeholder(title) {
    const clean = encodeURIComponent((title || 'Movie').split(' (')[0].substring(0, 20));
    return `https://placehold.co/400x600/111/333?text=${clean}`;
}

function esc(str) {
    return (str || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

function showSkeletonRows(withHero = true) {
    if (withHero) {
        heroSection.style.display = 'flex';
        heroSection.innerHTML = `
            <div class="hero__overlay" style="background:var(--bg-void)"></div>
            <div class="hero__inner">
                <div class="skeleton" style="width:120px;height:28px;border-radius:var(--r-pill);margin-bottom:20px;"></div>
                <div class="skeleton" style="width:400px;height:52px;margin-bottom:16px;"></div>
                <div class="skeleton" style="width:300px;height:18px;margin-bottom:14px;"></div>
                <div class="skeleton" style="width:500px;height:60px;margin-bottom:28px;"></div>
                <div style="display:flex;gap:14px;">
                    <div class="skeleton" style="width:140px;height:50px;border-radius:var(--r-md);"></div>
                    <div class="skeleton" style="width:160px;height:50px;border-radius:var(--r-md);"></div>
                </div>
            </div>
        `;
    }
    const skeletonCards = Array(8).fill(`
        <div class="card-wrap">
            <div class="skeleton" style="width:100%;aspect-ratio:2/3;"></div>
        </div>
    `).join('');
    const skeletonRow = `
        <section class="row-section" style="${withHero ? '' : 'padding-top:0;'}">
            <div class="skeleton" style="width:200px;height:22px;margin-bottom:16px;"></div>
            <div class="row-scroll">${skeletonCards}</div>
        </section>
    `;
    contentRows.innerHTML = skeletonRow;
}

function emptyStateHTML() {
    const cats = ['Sci-Fi','Action','Comedy','Drama','Thriller','Horror','Romance','Animation','Mystery'];
    return `
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:60vh;text-align:center;padding:0 20px;">
            <h2 style="font-size:2.2rem;font-weight:700;color:var(--text-primary);margin-bottom:12px;">What would you like to watch?</h2>
            <p style="color:var(--text-muted);margin-bottom:40px;max-width:500px;">Explore categories or ask Aurora AI for personalized recommendations.</p>
            <div style="display:flex;gap:10px;flex-wrap:wrap;justify-content:center;max-width:600px;">
                ${cats.map(c => `
                    <button onclick="aiPanel.classList.add('open');chatInput.value='Recommend ${c.toLowerCase()} movies';handleSend();"
                        style="padding:10px 22px;border-radius:var(--r-pill);background:var(--glass-bg-2);border:1px solid var(--glass-border);color:var(--text-primary);font-size:0.9rem;font-weight:500;cursor:pointer;transition:all 150ms;backdrop-filter:blur(12px);"
                        onmouseover="this.style.background='var(--glass-bg-3)';this.style.transform='translateY(-2px)'"
                        onmouseout="this.style.background='var(--glass-bg-2)';this.style.transform='translateY(0)'"
                    >${c}</button>
                `).join('')}
            </div>
        </div>
    `;
}
