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
let token = 'mock_token';
let userId = 32;

async function authFetch(url, options = {}) {
    options.headers = options.headers || {};
    options.headers['Authorization'] = `Bearer mock_token`;
    const res = await fetch(url, options);
    return res;
}

// ══════════════════════════════════════════════════════════════════════
//  INIT
// ══════════════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    const loginOverlay = document.getElementById('login-overlay');
    const logoutBtn = document.getElementById('logout-btn');
    const adminLink = document.getElementById('admin-link');
    const userDisplay = document.getElementById('current-user-display');
    const loginError = document.getElementById('login-error');

    if (loginOverlay) loginOverlay.style.display = 'none';
    if (userDisplay) userDisplay.textContent = `User: guest`;
    navigateTo('home');


    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('aurora_token');
        localStorage.removeItem('aurora_user_id');
        localStorage.removeItem('aurora_role');
        localStorage.removeItem('aurora_username');
        window.location.reload();
    });
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

function toggleMobileDrawer() {
    const drawer = document.getElementById('mobile-drawer');
    if (!drawer) return;
    const isActive = drawer.classList.contains('active');
    if (isActive) {
        drawer.classList.remove('active');
        sidebarBackdrop.classList.remove('active');
        document.body.style.overflow = '';
    } else {
        drawer.classList.add('active');
        sidebarBackdrop.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

if(mobileMenuBtn) mobileMenuBtn.addEventListener('click', toggleMobileDrawer);
if(sidebarBackdrop) sidebarBackdrop.addEventListener('click', toggleMobileDrawer);
const mobileDrawerClose = document.getElementById('mobile-drawer-close');
if(mobileDrawerClose) mobileDrawerClose.addEventListener('click', toggleMobileDrawer);

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
searchTrigger.addEventListener('click', () => {
    searchOverlay.classList.add('open');
    setTimeout(() => searchInput.focus(), 100);
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
    window.shownItems = []; // Reset exclusions on page navigate

    // Update sidebar & bottom nav active states
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
        case 'movies':
        case 'categories':
            loadCategoriesHub();
            break;
        case 'tv-series':
            loadCategoryPage('Trending TV Series', [
                'Dark Psychological Thrillers',
                'Feel-Good Family',
                'Historical Fiction'
            ], 'TV Series');
            break;
        case 'trending':
            heroSection.innerHTML = '';
            heroSection.style.display = 'none';
            contentRows.innerHTML = '';
            fetchAndRender('What is trending?', 'Trending Now');
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

    // Sequentially fetch dynamic semantic categories (Home shows multiple rows directly)
    await fetchAndRender('Top Picks For You', 'Top Picks For You', true);
    await fetchAndRender('Trending Now', 'Trending Now', false);
    await fetchAndRender('Mind-Bending Sci-Fi', 'Mind-Bending Sci-Fi', false);
    await fetchAndRender('Crime Masterpieces', 'Crime Masterpieces', false);
    await fetchAndRender('Feel-Good Family', 'Feel-Good Family', false);
    await fetchAndRender('Epic Adventures', 'Epic Adventures', false);
    await fetchAndRender('Dark Psychological Thrillers', 'Dark Psychological Thrillers', false);
    await fetchAndRender('Hidden Gems', 'Hidden Gems', false);
}

// ── Universal Categories Hub ──────────────────────────────────────────
function loadCategoriesHub() {
    heroSection.innerHTML = '';
    heroSection.style.display = 'none';
    
    const genres = [
        "Action", "Adventure", "Animation", "Biography", "Comedy", "Crime", 
        "Documentary", "Drama", "Family", "Fantasy", "History", "Horror", 
        "Music", "Mystery", "Romance", "Science Fiction", "Sports", "Thriller", 
        "War", "Western", "Psychological", "Cyberpunk", "Dystopian", "Time Travel", 
        "Epic Adventures", "Martial Arts", "Spy", "Survival", "Hidden Gems"
    ];

    let gridHtml = `<div class="row-section" style="padding-top:80px;">
        <h1 class="row-section__title" style="font-size:2.2rem;margin-bottom:32px;padding-left:40px;">Explore Categories</h1>
        <div class="category-hub">`;
        
    genres.forEach(g => {
        gridHtml += `<div class="category-pill" onclick="loadCategoryDetail('${g}')">${g}</div>`;
    });
    
    gridHtml += `</div></div>`;
    contentRows.innerHTML = gridHtml;
}

async function loadCategoryDetail(genre) {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    contentRows.innerHTML = `
        <div class="row-section" style="padding-top:80px;">
            <button onclick="loadCategoriesHub()" style="background:transparent;border:none;color:#a78bfa;cursor:pointer;margin-bottom:20px;font-size:1.1rem;">← Back to Categories</button>
            <h1 class="row-section__title" style="font-size:2.2rem;margin-bottom:32px;">${genre}</h1>
        </div>
    `;
    showSkeletonRows(false);
    
    // Reset exclusions so we don't accidentally hide movies from the previous page
    window.shownItems = [];
    
    await fetchAndRender(genre, `Popular in ${genre}`);
    await fetchAndRender(`More ${genre}`, `More ${genre}`);
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
            // Track shown items to prevent duplication across rows
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

// ══════════════════════════════════════════════════════════════════════
//  SEARCH -> MAP TO AI CHATBOT
// ══════════════════════════════════════════════════════════════════════
const desktopSearchTrigger = document.getElementById('search-trigger');
const mobileSearchBtn = document.getElementById('mobile-search-btn');

function openAiPanelFromSearch(e) {
    if(e) e.preventDefault();
    aiPanel.classList.add('open');
    chatInput.focus();
}

if (desktopSearchTrigger) desktopSearchTrigger.addEventListener('click', openAiPanelFromSearch);
if (mobileSearchBtn) mobileSearchBtn.addEventListener('click', openAiPanelFromSearch);

// ── My List ───────────────────────────────────────────────────────────
function renderMyList() {
    heroSection.innerHTML = '';
    heroSection.style.display = 'none';

    if (myList.length === 0) {
        contentRows.innerHTML = `
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:70vh;text-align:center;padding:0 20px;">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg>
                <h2 style="font-size:2rem;font-weight:700;color:var(--text-primary);margin:24px 0 12px;">Your List is Empty</h2>
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
                        <button class="card-expand__btn" onclick="event.stopPropagation(); toggleSave(${movie.item_id})" aria-label="${saved ? 'Remove from list' : 'Add to list'}">
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

    // Attach 3D tilt to newly added cards
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

    // Click → open modal
    card.addEventListener('click', () => {
        const id = parseInt(card.dataset.id);
        if (id) openModal(id);
    });

    // Keyboard
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
    // 1. Fire Event Processor tracking
    authFetch('/events/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_type: "click", item_id: id })
    }).catch(e => console.error("Event ingest failed:", e));

    // 2. Open Modal with loading state
    modalOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';

    // Reset fields to loading state
    document.getElementById('modal-title').textContent = 'Loading...';
    document.getElementById('modal-poster').src = '';
    document.getElementById('modal-backdrop').style.backgroundImage = 'none';
    document.getElementById('modal-synopsis').textContent = 'Fetching cinematic details...';
    document.getElementById('modal-genres').innerHTML = '';
    document.getElementById('modal-match').textContent = '';
    document.getElementById('modal-similar').innerHTML = '';

    try {
        // 3. Fetch massive payload
        const resp = await authFetch(`/movie/${id}`);
        const m = await resp.json();
        
        if (m.error) throw new Error(m.error);

        // Populate fields
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
        
        // Fetch Similar Movies via RAG Chatbot Endpoint dynamically
        const simContainer = document.getElementById('modal-similar');
        simContainer.innerHTML = '<p>Loading similar content...</p>';
        
        try {
            const simResp = await authFetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: "Movies strictly similar to " + m.title, exclude_ids: [] })
            });
            const simData = await simResp.json();
            const similarMovies = Array.isArray(simData.response) ? simData.response : (simData.response && simData.response.value);
            
            if (similarMovies && similarMovies.length > 0) {
                simContainer.innerHTML = similarMovies.slice(0, 8).map(sm => `
                    <div class="sim-card" onclick="openModal(${sm.item_id})">
                        <img src="${sm.poster_url || placeholder(sm.title)}" alt="${sm.title}" class="sim-poster">
                        <div class="sim-title">${sm.title}</div>
                    </div>
                `).join('');
            } else {
                simContainer.innerHTML = '<p>No similar titles found.</p>';
            }
        } catch (e) {
            simContainer.innerHTML = '<p>Failed to load similar titles.</p>';
        }

        // Add to list btn state
        const addBtn = document.getElementById('modal-add-list');
        const saved = isInMyList(id);
        addBtn.innerHTML = saved ? `✓ Added` : `+ Add to List`;
        addBtn.onclick = () => {
            toggleSave(id);
            addBtn.innerHTML = isInMyList(id) ? `✓ Added` : `+ Add to List`;
        };

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

// Close button listener rewrite
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
