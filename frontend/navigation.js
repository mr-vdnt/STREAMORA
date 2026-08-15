// Streamora navigation + resilient discovery shell.
// This file is intentionally loaded after app.js so it can replace the legacy
// request-heavy home/search/category renderers without changing the core player/modal code.

const STREAMORA_CATEGORIES = [
    "Action & Adventure", "Anime", "Children & Family Movies", "Classic Movies",
    "Comedies", "Documentaries", "Dramas", "Horror Movies", "Independent Movies",
    "International Movies", "Music", "Romantic Movies", "Sci-Fi & Fantasy",
    "Sports Movies", "Thrillers", "TV Shows"
];

const STREAMORA_CATEGORY_ICONS = {
    "Action & Adventure": "⚡", Anime: "✦", "Children & Family Movies": "🧸",
    "Classic Movies": "🎞️", Comedies: "😂", Documentaries: "🎥", Dramas: "🎭",
    "Horror Movies": "☠️", "Independent Movies": "◆", "International Movies": "🌍",
    Music: "♫", "Romantic Movies": "♥", "Sci-Fi & Fantasy": "◈",
    "Sports Movies": "◎", Thrillers: "◉", "TV Shows": "▣"
};

const ROUTES = { HOME: '/', MOVIE: '/movie/', TV: '/tv/', CATEGORY: '/category/' };
let streamoraFormat = localStorage.getItem('streamora_current_format') || 'all';
let streamoraSearchTimer = null;
let streamoraHomeRequest = 0;

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>'"]/g, ch => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[ch]));
}

function formatRuntime(item) {
    const runtime = Number(item?.runtime || item?.rich_metadata?.runtime || 0);
    if (!Number.isFinite(runtime) || runtime <= 0) return '';
    const hours = Math.floor(runtime / 60);
    const minutes = runtime % 60;
    if (hours) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
}

function normalizeItem(raw) {
    const item = raw || {};
    const type = String(item.content_type || item.entity_type || item.type || '').toLowerCase();
    const isSeries = type.includes('series') || type === 'tv' || type === 'show';
    const metadata = item.rich_metadata || {};
    return {
        ...item,
        item_id: item.item_id ?? item.id,
        title: item.title || metadata.title || 'Untitled',
        poster_url: item.poster_url || metadata.poster_url || '',
        backdrop_url: item.backdrop_url || metadata.backdrop_url || item.poster_url || '',
        year: item.year || metadata.year || (item.release_date || '').slice(0, 4),
        runtime: item.runtime || metadata.runtime || 0,
        rating: Number(item.rating ?? metadata.rating ?? 0) || 0,
        overview: item.overview || metadata.overview || '',
        content_type: isSeries ? 'series' : 'movie',
        genres: Array.isArray(item.genres) ? item.genres : (Array.isArray(metadata.genres) ? metadata.genres : [])
    };
}

function itemCard(item, compact = false) {
    const m = normalizeItem(item);
    const rating = m.rating > 0 ? `<span class="sr-rating">IMDb ${m.rating.toFixed(1)}</span>` : '';
    const runtime = formatRuntime(m);
    const meta = [m.year, runtime, m.content_type === 'series' ? 'TV Series' : 'Movie'].filter(Boolean).join(' • ');
    const poster = m.poster_url || m.backdrop_url;
    return `
        <article class="sr-card ${compact ? 'sr-card--compact' : ''}" tabindex="0" data-id="${escapeHtml(m.item_id)}">
            <button class="sr-card__button" type="button" aria-label="Open ${escapeHtml(m.title)}">
                <div class="sr-card__poster">
                    ${poster ? `<img src="${escapeHtml(poster)}" alt="${escapeHtml(m.title)}" loading="lazy" decoding="async">` : '<div class="sr-card__poster-fallback">STREAMORA</div>'}
                    <div class="sr-card__badges">${rating}</div>
                    <div class="sr-card__gradient"></div>
                    <div class="sr-card__info">
                        <strong>${escapeHtml(m.title)}</strong>
                        <span>${escapeHtml(meta)}</span>
                    </div>
                </div>
            </button>
        </article>`;
}

function bindCardClicks(root) {
    root.querySelectorAll('.sr-card').forEach(card => {
        const open = () => {
            const id = Number(card.dataset.id);
            if (id && typeof window.navigateToMovie === 'function') window.navigateToMovie(id);
        };
        card.addEventListener('click', open);
        card.addEventListener('keydown', e => {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); }
        });
    });
}

function ensureDiscoveryStyles() {
    if (document.getElementById('streamora-discovery-overrides')) return;
    const style = document.createElement('style');
    style.id = 'streamora-discovery-overrides';
    style.textContent = `
        .topbar__ai-btn,#ai-trigger,.ai-panel,.modal-footer-brand{display:none!important}
        #home-filter-section{display:block!important;background:transparent!important;border:0!important}
        .streamora-shell{max-width:1500px;margin:0 auto;padding:24px 4vw 80px}
        .streamora-switcher{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0 28px}
        .streamora-switcher button{border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.045);color:#c9c8d4;border-radius:999px;padding:11px 20px;font-weight:700;cursor:pointer;transition:.2s;backdrop-filter:blur(18px)}
        .streamora-switcher button:hover,.streamora-switcher button.active{color:#fff;border-color:rgba(157,93,255,.75);background:linear-gradient(135deg,rgba(116,65,255,.35),rgba(30,210,255,.16));box-shadow:0 0 28px rgba(117,70,255,.18)}
        .streamora-hero{position:relative;min-height:500px;border:1px solid rgba(255,255,255,.1);border-radius:28px;overflow:hidden;background:#0b0b10;box-shadow:0 30px 100px rgba(0,0,0,.45);margin-bottom:34px}
        .streamora-hero__bg{position:absolute;inset:0;background-size:cover;background-position:center;filter:saturate(1.08);transform:scale(1.02)}
        .streamora-hero__shade{position:absolute;inset:0;background:linear-gradient(90deg,#07070a 0%,rgba(7,7,10,.84) 30%,rgba(7,7,10,.32) 65%,rgba(7,7,10,.55) 100%),linear-gradient(0deg,#07070a 0%,transparent 45%)}
        .streamora-hero__content{position:relative;z-index:2;min-height:500px;max-width:700px;padding:70px 60px;display:flex;flex-direction:column;justify-content:flex-end}
        .streamora-kicker{font-size:.78rem;letter-spacing:.18em;text-transform:uppercase;color:#b6a4ff;font-weight:800;margin-bottom:12px}
        .streamora-hero h1{font-size:clamp(2.4rem,5vw,4.8rem);line-height:.98;margin:0 0 18px;color:#fff;letter-spacing:-.04em}
        .streamora-hero p{color:#d2d0dc;line-height:1.65;max-width:620px;margin:0 0 24px;font-size:1rem}
        .streamora-meta{display:flex;gap:12px;flex-wrap:wrap;color:#bcb9c8;font-size:.9rem;margin-bottom:24px}.streamora-meta b{color:#f5c518}
        .streamora-row{margin:0 0 34px}.streamora-row__head{display:flex;justify-content:space-between;align-items:end;margin-bottom:14px}.streamora-row__head h2{margin:0;color:#fff;font-size:1.2rem}.streamora-row__head span{color:#777487;font-size:.78rem}.streamora-cards{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(175px,210px);gap:16px;overflow-x:auto;padding:5px 3px 2px;scrollbar-width:none;-ms-overflow-style:none}.streamora-cards::-webkit-scrollbar{display:none!important}
        .sr-card{min-width:0}.sr-card__button{padding:0;border:0;background:transparent;width:100%;text-align:left;color:#fff;cursor:pointer}.sr-card__poster{position:relative;aspect-ratio:2/3;border-radius:16px;overflow:hidden;background:linear-gradient(135deg,#171720,#0b0b10);border:1px solid rgba(255,255,255,.09);box-shadow:0 15px 40px rgba(0,0,0,.3);transition:transform .25s,border-color .25s,box-shadow .25s}.sr-card:hover .sr-card__poster,.sr-card:focus .sr-card__poster{transform:translateY(-6px) scale(1.015);border-color:rgba(155,100,255,.55);box-shadow:0 22px 50px rgba(0,0,0,.45),0 0 28px rgba(116,65,255,.14)}.sr-card__poster img{width:100%;height:100%;object-fit:cover;display:block}.sr-card__gradient{position:absolute;inset:35% 0 0;background:linear-gradient(transparent,rgba(5,5,8,.96))}.sr-card__badges{position:absolute;top:9px;left:9px;z-index:2}.sr-rating{display:inline-flex;padding:5px 8px;border-radius:8px;background:rgba(8,8,12,.8);border:1px solid rgba(255,255,255,.12);color:#f5c518;font-size:.7rem;font-weight:800;backdrop-filter:blur(10px)}.sr-card__info{position:absolute;z-index:2;left:12px;right:12px;bottom:11px;display:flex;flex-direction:column;gap:3px}.sr-card__info strong{font-size:.9rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.sr-card__info span{font-size:.7rem;color:#b8b5c4}.sr-card__poster-fallback{height:100%;display:grid;place-items:center;color:#777487;font-size:.7rem;letter-spacing:.12em}
        .streamora-search{padding:50px 4vw 80px;max-width:1450px;margin:0 auto}.streamora-search h1{font-size:clamp(2rem,4vw,3rem);margin:0 0 24px;color:#fff;letter-spacing:-.04em}.streamora-search__box{position:relative}.streamora-search__box input{width:100%;box-sizing:border-box;padding:19px 58px 19px 54px;border-radius:18px;border:1px solid rgba(255,255,255,.13);background:rgba(255,255,255,.045);color:#fff;font-size:1rem;outline:none;backdrop-filter:blur(20px)}.streamora-search__box input:focus{border-color:rgba(151,91,255,.85);box-shadow:0 0 0 4px rgba(124,75,255,.1)}.streamora-search__icon{position:absolute;left:20px;top:50%;transform:translateY(-50%);color:#aaa7b7}.streamora-search__suggestions{display:flex;gap:9px;flex-wrap:wrap;margin:18px 0 32px}.streamora-chip{border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.04);color:#c6c3d0;border-radius:999px;padding:8px 13px;cursor:pointer}.streamora-chip:hover{color:#fff;border-color:rgba(154,96,255,.7);background:rgba(117,70,255,.12)}.streamora-autocomplete{position:absolute;left:0;right:0;top:calc(100% + 8px);z-index:1000;background:rgba(10,10,16,.97);border:1px solid rgba(255,255,255,.12);border-radius:18px;overflow:hidden;box-shadow:0 25px 80px rgba(0,0,0,.55);backdrop-filter:blur(24px)}.streamora-autocomplete button{width:100%;display:flex;gap:12px;align-items:center;border:0;background:transparent;color:#fff;padding:11px 15px;text-align:left;cursor:pointer}.streamora-autocomplete button:hover{background:rgba(255,255,255,.06)}.streamora-autocomplete img{width:36px;height:52px;object-fit:cover;border-radius:7px;background:#171720}
        .streamora-category-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:16px}.streamora-category{position:relative;min-height:150px;border:1px solid rgba(255,255,255,.1);border-radius:22px;background:radial-gradient(circle at 80% 15%,rgba(130,76,255,.24),transparent 42%),linear-gradient(145deg,rgba(255,255,255,.08),rgba(255,255,255,.025));color:#fff;display:flex;flex-direction:column;justify-content:flex-end;padding:20px;cursor:pointer;overflow:hidden;transition:.25s;box-shadow:inset 0 1px 0 rgba(255,255,255,.06)}.streamora-category:before{content:"";position:absolute;width:90px;height:90px;border-radius:50%;right:-25px;top:-25px;background:rgba(55,225,255,.1);filter:blur(4px)}.streamora-category:hover{transform:translateY(-5px);border-color:rgba(150,94,255,.65);box-shadow:0 22px 50px rgba(0,0,0,.35),0 0 30px rgba(122,72,255,.13)}.streamora-category__icon{font-size:2rem;margin-bottom:22px}.streamora-category__name{font-size:1rem;font-weight:800;max-width:160px;line-height:1.2}.streamora-empty{padding:80px 20px;text-align:center;color:#858292}
        @media(max-width:700px){.streamora-shell{padding:14px 16px 70px}.streamora-hero,.streamora-hero__content{min-height:440px}.streamora-hero__content{padding:30px}.streamora-cards{grid-auto-columns:145px}.streamora-category-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.streamora-category{min-height:125px;padding:14px}.streamora-category__icon{font-size:1.5rem;margin-bottom:16px}}
    `;
    document.head.appendChild(style);
}

async function fetchJson(path, { timeoutMs = 3500, signal } = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    if (signal) signal.addEventListener('abort', () => controller.abort(), { once: true });
    try {
        const response = await fetch(path, { credentials: 'include', signal: controller.signal, headers: { Accept: 'application/json' } });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } finally { clearTimeout(timer); }
}

function formatSwitcher() {
    return `<div class="streamora-switcher" role="tablist" aria-label="Content type">
        <button class="${streamoraFormat === 'all' ? 'active' : ''}" data-format="all">🔮 Combined Discovery</button>
        <button class="${streamoraFormat === 'movie' ? 'active' : ''}" data-format="movie">🎬 Movies Only</button>
        <button class="${streamoraFormat === 'series' ? 'active' : ''}" data-format="series">📺 TV Series Only</button>
    </div>`;
}

function bindFormatSwitcher(root) {
    root.querySelectorAll('[data-format]').forEach(button => button.addEventListener('click', () => {
        streamoraFormat = button.dataset.format;
        localStorage.setItem('streamora_current_format', streamoraFormat);
        renderHomePage();
    }));
}

function renderHomeSnapshot(payload, requestId) {
    if (requestId !== streamoraHomeRequest) return;
    const heroSection = document.getElementById('hero-section');
    const rows = document.getElementById('content-rows');
    if (!heroSection || !rows) return;

    const hero = normalizeItem(payload.hero);
    const sections = (payload.sections || payload.shelves || []).map(section => ({
        ...section,
        items: (section.items || []).map(normalizeItem).filter(Boolean)
    })).filter(section => section.items.length);

    heroSection.style.display = hero.title ? 'block' : 'none';
    heroSection.innerHTML = hero.title ? `
        <section class="streamora-hero">
            <div class="streamora-hero__bg" style="background-image:url('${escapeHtml(hero.backdrop_url || hero.poster_url)}')"></div>
            <div class="streamora-hero__shade"></div>
            <div class="streamora-hero__content">
                <div class="streamora-kicker">${hero.content_type === 'series' ? 'Featured Series' : 'Featured Movie'}</div>
                <h1>${escapeHtml(hero.title)}</h1>
                <div class="streamora-meta"><span>${escapeHtml(hero.year || '')}</span>${hero.rating > 0 ? `<b>IMDb ${hero.rating.toFixed(1)}</b>` : ''}<span>${escapeHtml(formatRuntime(hero))}</span></div>
                <p>${escapeHtml(hero.overview || 'Discover your next favorite title.')}</p>
                <div><button class="btn-watch" type="button" style="border:0;border-radius:999px;padding:12px 20px;background:#fff;color:#09090d;font-weight:800;cursor:pointer">View Details</button></div>
            </div>
        </section>` : '';
    const heroButton = heroSection.querySelector('.btn-watch');
    if (heroButton && hero.item_id) heroButton.onclick = () => window.navigateToMovie?.(hero.item_id);

    rows.innerHTML = `<div class="streamora-shell">${formatSwitcher()}${sections.map(section => `
        <section class="streamora-row">
            <div class="streamora-row__head"><h2>${escapeHtml(section.title || 'Recommended')}</h2><span>${section.items.length} titles</span></div>
            <div class="streamora-cards">${section.items.map(item => itemCard(item)).join('')}</div>
        </section>`).join('')}${!sections.length ? '<div class="streamora-empty">No titles are available yet. Try again in a moment.</div>' : ''}</div>`;
    const shell = rows.querySelector('.streamora-shell');
    if (shell) { bindFormatSwitcher(shell); bindCardClicks(shell); }
}

async function renderHomePage() {
    ensureDiscoveryStyles();
    const requestId = ++streamoraHomeRequest;
    const heroSection = document.getElementById('hero-section');
    const rows = document.getElementById('content-rows');
    if (!heroSection || !rows) return;

    heroSection.style.display = 'none';
    rows.innerHTML = `<div class="streamora-shell">${formatSwitcher()}<div class="streamora-empty">Loading your discovery universe…</div></div>`;
    bindFormatSwitcher(rows);

    try {
        const user = JSON.parse(localStorage.getItem('streamora_profile') || 'null');
        const userId = user?.id || 'demo_user';
        const data = await fetchJson(`/api/v3/home?user_id=${encodeURIComponent(userId)}&format=${streamoraFormat}`, { timeoutMs: 3500 });
        renderHomeSnapshot(data, requestId);
    } catch (error) {
        console.warn('[Streamora] fast home unavailable:', error);
        try {
            const fallback = await fetchJson(`/discover?limit=24&sort=popularity&type=${streamoraFormat === 'all' ? '' : streamoraFormat}`, { timeoutMs: 1800 });
            const items = (fallback.items || fallback.results || []).map(normalizeItem);
            renderHomeSnapshot({ hero: items[0], sections: [{ title: 'Popular Now', items }] }, requestId);
        } catch (fallbackError) {
            if (requestId === streamoraHomeRequest) {
                rows.innerHTML = `<div class="streamora-shell"><div class="streamora-empty"><h2 style="color:#fff">Streamora is temporarily unavailable</h2><p>The interface is alive; the catalog service did not respond within the safe UI budget.</p><button id="streamora-retry" style="margin-top:18px;border:0;border-radius:999px;padding:11px 20px;background:#fff;color:#09090d;font-weight:800;cursor:pointer">Retry</button></div></div>`;
                document.getElementById('streamora-retry')?.addEventListener('click', renderHomePage);
            }
        }
    }
}

function renderSearchPage() {
    ensureDiscoveryStyles();
    const hero = document.getElementById('hero-section');
    const rows = document.getElementById('content-rows');
    if (hero) { hero.innerHTML = ''; hero.style.display = 'none'; }
    if (!rows) return;

    rows.innerHTML = `<div class="streamora-search">
        <h1>Search & Discovery</h1>
        <div class="streamora-search__box">
            <span class="streamora-search__icon">⌕</span>
            <input id="streamora-search-input" type="search" autocomplete="off" placeholder="Search movies, TV series, actors, directors, genres…">
            <div id="streamora-search-autocomplete" class="streamora-autocomplete" hidden></div>
        </div>
        <div class="streamora-search__suggestions" id="streamora-search-chips"></div>
        <div id="streamora-search-results"></div>
    </div>`;

    const input = document.getElementById('streamora-search-input');
    const chips = document.getElementById('streamora-search-chips');
    const results = document.getElementById('streamora-search-results');
    const popular = ['Action', 'Comedy', 'Sci-Fi', 'Horror', 'Romance', 'Documentary', 'Animation', 'Thriller'];
    chips.innerHTML = `<span style="width:100%;color:#777487;font-size:.78rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase">Popular searches</span>${popular.map(q => `<button class="streamora-chip" data-q="${q}">${q}</button>`).join('')}`;
    chips.querySelectorAll('[data-q]').forEach(btn => btn.addEventListener('click', () => { input.value = btn.dataset.q; executeDiscoverySearch(btn.dataset.q); }));

    input.addEventListener('input', () => {
        clearTimeout(streamoraSearchTimer);
        const q = input.value.trim();
        if (q.length < 2) { document.getElementById('streamora-search-autocomplete').hidden = true; return; }
        streamoraSearchTimer = setTimeout(() => updateAutocomplete(q), 180);
    });
    input.addEventListener('keydown', e => { if (e.key === 'Enter') executeDiscoverySearch(input.value.trim()); });

    // Recommendations are shown before the user types, so the search screen is never empty.
    executeDiscoveryRecommendations(results);
}

async function updateAutocomplete(query) {
    const panel = document.getElementById('streamora-search-autocomplete');
    if (!panel) return;
    try {
        const data = await fetchJson(`/api/v2/autocomplete?q=${encodeURIComponent(query)}`, { timeoutMs: 1200 });
        const titles = data.titles || data.results || (Array.isArray(data) ? data : []);
        if (!titles.length) { panel.hidden = true; return; }
        panel.innerHTML = titles.slice(0, 8).map(title => {
            const item = typeof title === 'string' ? { title } : title;
            return `<button type="button" data-title="${escapeHtml(item.title || '')}">${item.poster_url ? `<img src="${escapeHtml(item.poster_url)}" alt="">` : ''}<span>${escapeHtml(item.title || '')}</span></button>`;
        }).join('');
        panel.hidden = false;
        panel.querySelectorAll('[data-title]').forEach(btn => btn.addEventListener('click', () => {
            const input = document.getElementById('streamora-search-input');
            if (input) input.value = btn.dataset.title;
            panel.hidden = true;
            executeDiscoverySearch(btn.dataset.title);
        }));
    } catch { panel.hidden = true; }
}

async function executeDiscoveryRecommendations(container) {
    container.innerHTML = `<section class="streamora-row"><div class="streamora-row__head"><h2>Suggestions for You</h2><span>Based on popularity until your profile has enough signals</span></div><div class="streamora-cards"><div class="streamora-empty">Curating…</div></div></section>`;
    try {
        const data = await fetchJson(`/discover?limit=12&sort=popularity`, { timeoutMs: 1800 });
        const items = (data.items || data.results || []).map(normalizeItem);
        container.innerHTML = `<section class="streamora-row"><div class="streamora-row__head"><h2>Suggestions for You</h2><span>Personalized as you interact</span></div><div class="streamora-cards">${items.map(item => itemCard(item)).join('')}</div></section>`;
        bindCardClicks(container);
    } catch {
        container.innerHTML = `<section class="streamora-row"><div class="streamora-row__head"><h2>Search recommendations</h2></div><div class="streamora-empty">Start typing a title, genre, actor, or director.</div></section>`;
    }
}

async function executeDiscoverySearch(query) {
    const container = document.getElementById('streamora-search-results');
    const input = document.getElementById('streamora-search-input');
    if (!container || !query) return;
    if (input) input.value = query;
    container.innerHTML = `<div class="streamora-empty">Searching…</div>`;
    try {
        const type = streamoraFormat === 'all' ? 'all' : streamoraFormat;
        const data = await fetchJson(`/api/v2/search/instant?q=${encodeURIComponent(query)}&limit=24&content_type=${type}`, { timeoutMs: 2200 });
        const items = (data.results || []).map(normalizeItem);
        container.innerHTML = `<section class="streamora-row"><div class="streamora-row__head"><h2>Results for “${escapeHtml(query)}”</h2><span>${items.length} titles</span></div><div class="streamora-cards">${items.map(item => itemCard(item)).join('')}</div></section>`;
        bindCardClicks(container);
    } catch {
        container.innerHTML = `<div class="streamora-empty">Search is temporarily unavailable. Try again.</div>`;
    }
}

function renderCategoriesPage() {
    ensureDiscoveryStyles();
    const hero = document.getElementById('hero-section');
    const rows = document.getElementById('content-rows');
    if (hero) { hero.innerHTML = ''; hero.style.display = 'none'; }
    if (!rows) return;
    rows.innerHTML = `<div class="streamora-shell">
        ${formatSwitcher()}
        <section style="padding:22px 0 28px"><div class="streamora-kicker">Explore</div><h1 style="font-size:clamp(2rem,4vw,3rem);color:#fff;margin:0 0 10px">Explore Hub</h1><p style="color:#888594;margin:0;max-width:700px">Browse a focused set of cinematic categories. No duplicate theme tags, no noisy taxonomy.</p></section>
        <div class="streamora-category-grid">${STREAMORA_CATEGORIES.map(category => `<button class="streamora-category" data-category="${escapeHtml(category)}"><span class="streamora-category__icon">${STREAMORA_CATEGORY_ICONS[category] || '◈'}</span><span class="streamora-category__name">${escapeHtml(category)}</span></button>`).join('')}</div>
    </div>`;
    const shell = rows.querySelector('.streamora-shell');
    bindFormatSwitcher(shell);
    shell.querySelectorAll('[data-category]').forEach(button => button.addEventListener('click', () => openCategory(button.dataset.category)));
}

async function openCategory(category) {
    const rows = document.getElementById('content-rows');
    if (!rows) return;
    rows.innerHTML = `<div class="streamora-shell"><div class="streamora-empty">Loading ${escapeHtml(category)}…</div></div>`;
    try {
        const data = await fetchJson(`/api/v2/genre/${encodeURIComponent(category)}`, { timeoutMs: 2500 });
        const sections = data.sections || data.shelves || [];
        const items = sections.flatMap(s => s.items || []).map(normalizeItem).slice(0, 30);
        rows.innerHTML = `<div class="streamora-shell">${formatSwitcher()}<section class="streamora-row"><div class="streamora-row__head"><h2>${escapeHtml(category)}</h2><span>${items.length} titles</span></div><div class="streamora-cards">${items.map(item => itemCard(item)).join('')}</div></section></div>`;
        const shell = rows.querySelector('.streamora-shell');
        bindFormatSwitcher(shell); bindCardClicks(shell);
    } catch {
        renderCategoriesPage();
    }
}

function navigateTo(page) {
    if (page === 'home') {
        streamoraFormat = 'all';
        localStorage.setItem('streamora_current_format', 'all');
        history.replaceState(null, '', ROUTES.HOME);
        document.querySelectorAll('.sidebar__link,.bottom-nav__item').forEach(el => el.classList.toggle('active', el.dataset.page === 'home'));
        renderHomePage();
        return;
    }
    if (page === 'categories') { history.replaceState(null, '', '/categories'); renderCategoriesPage(); }
    else if (page === 'search') { history.replaceState(null, '', '/search'); renderSearchPage(); }
    else if (page === 'favorites' && typeof window.renderFavoritesTab === 'function') window.renderFavoritesTab();
    else if (page === 'downloads' && typeof window.renderDownloadsTab === 'function') window.renderDownloadsTab();
    else if (page === 'account' && typeof window.renderAccountTab === 'function') window.renderAccountTab();
    else if (page === 'settings' && typeof window.renderSettingsTab === 'function') window.renderSettingsTab();
    document.querySelectorAll('.sidebar__link,.bottom-nav__item').forEach(el => el.classList.toggle('active', el.dataset.page === page));
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function initRouter() {
    ensureDiscoveryStyles();
    // Remove the legacy AI branding/button immediately, including if app.js recreated it.
    document.querySelectorAll('#ai-trigger,.topbar__ai-btn,.ai-panel,.modal-footer-brand').forEach(el => el.remove());
    navigateTo('home');
}

window.navigateTo = navigateTo;
window.initRouter = initRouter;
window.loadHomePage = renderHomePage;
window.loadSearchPage = renderSearchPage;
window.loadCategoriesTab = renderCategoriesPage;
window.navigateToCategory = openCategory;
window.executeSearchPageQuery = executeDiscoverySearch;
window.streamoraOpenCategory = openCategory;

function navigateToMovie(id) {
    const numId = Number(id);
    if (!numId) return;
    // Try to detect content type from cached home data
    let type = 'movie';
    try {
        const rows = document.getElementById('content-rows');
        if (rows) {
            const card = rows.querySelector(`[data-id="${numId}"]`);
            if (card) {
                const normalized = card.dataset.type;
                if (normalized === 'series' || normalized === 'tvseries' || normalized === 'tv') {
                    type = 'series';
                }
            }
        }
    } catch (_) { /* ignore */ }
    
    if (window.modalManager && typeof window.modalManager.open === 'function') {
        window.modalManager.open(numId, type, true);
    } else if (typeof window.fetchModalContent === 'function') {
        // Fallback: open modal overlay manually and fetch content
        const overlay = document.getElementById('movie-detail-modal');
        if (overlay) {
            overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
        window.fetchModalContent(numId, type, true);
    }
}

window.navigateToMovie = navigateToMovie;
