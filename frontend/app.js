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

// ── Ambient Blur Backdrop ─────────────────────────────────────────────
window.updateAmbientBackground = function(imageUrl) {
    const backdrop = document.getElementById('ambient-backdrop');
    if (!backdrop) return;
    if (imageUrl) {
        backdrop.style.backgroundImage = `url('${imageUrl}')`;
        backdrop.classList.add('active');
    } else {
        backdrop.classList.remove('active');
    }
};

// ── 3D Spatial Cover Flow Calculator ──────────────────────────────────
window.updateSpatialCarousel = function(rowScroll) {
    if (!rowScroll) return;
    const rect = rowScroll.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const cards = rowScroll.querySelectorAll('.card-wrap');
    
    cards.forEach(card => {
        const cardRect = card.getBoundingClientRect();
        const cardCenterX = cardRect.left + cardRect.width / 2;
        const offset = cardCenterX - centerX;
        const maxOffset = rect.width / 2 || 1;
        const normalized = Math.max(-1, Math.min(1, offset / maxOffset));
        
        // Compute 3D transformations
        const scale = 1 - Math.abs(normalized) * 0.15; // center 1.0, edge 0.85
        const rotateY = normalized * -30; // rotate outwards
        const translateZ = Math.abs(normalized) * -80; // push depth back
        
        card.style.transform = `scale(${scale}) rotateY(${rotateY}deg) translateZ(${translateZ}px)`;
        card.style.opacity = 1 - Math.abs(normalized) * 0.25;
    });
};

window.addEventListener('resize', () => {
    document.querySelectorAll('.row-scroll').forEach(window.updateSpatialCarousel);
}, { passive: true });

// ── Client-side Similarity scoring engine (up to 25 items) ─────────────
window.getSimilarRecommendations = function(seedMovie) {
    if (!seedMovie) return [];
    
    let uniquePool = [];
    const seen = new Set();
    
    // Combine all discovered movie datasets
    const combinedPool = [...(globalMovies || []), ...FALLBACK_MOVIES];
    combinedPool.forEach(m => {
        if (m && m.item_id && m.item_id !== seedMovie.item_id && !seen.has(m.item_id)) {
            seen.add(m.item_id);
            uniquePool.push(m);
        }
    });
    
    const seedMeta = seedMovie.rich_metadata || {};
    const seedGenres = seedMeta.genres || seedMeta.tags || [];
    const seedThemes = seedMeta.themes || [];
    const seedMoods = seedMeta.moods || [];
    const seedDirector = seedMeta.director || '';
    
    const scored = uniquePool.map(m => {
        const meta = m.rich_metadata || {};
        const genres = meta.genres || meta.tags || [];
        const themes = meta.themes || [];
        const moods = meta.moods || [];
        const director = meta.director || '';
        
        let score = 0;
        let reasons = [];
        
        // Compare genres
        const commonGenres = genres.filter(g => seedGenres.includes(g));
        if (commonGenres.length > 0) {
            score += commonGenres.length * 15;
            reasons.push(commonGenres[0]);
        }
        
        // Compare themes
        const commonThemes = themes.filter(t => seedThemes.includes(t));
        if (commonThemes.length > 0) {
            score += commonThemes.length * 20;
            reasons.push(commonThemes[0]);
        }
        
        // Compare moods
        const commonMoods = moods.filter(md => seedMoods.includes(md));
        if (commonMoods.length > 0) {
            score += commonMoods.length * 10;
            reasons.push(commonMoods[0]);
        }
        
        // Compare director
        if (director && director === seedDirector) {
            score += 40;
            reasons.push(`Directed by ${director}`);
        }
        
        score += (m.item_id % 7); // deterministic tie breaker
        
        let reasoning = reasons.join(' • ') || 'Recommended for you';
        
        return {
            movie: m,
            score: Math.min(99, Math.max(70, 75 + Math.floor(score))),
            reasoning: reasoning
        };
    });
    
    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, 25);
};

// ── Fallback Database ──────────────────────────────────────────────────
const FALLBACK_MOVIES = [
    {
        item_id: 1,
        title: "Spider-Man: No Way Home",
        poster_url: "https://image.tmdb.org/t/p/original/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/original/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg",
        overview: "Peter Parker is unmasked and no longer able to separate his normal life from the high-stakes of being a super-hero. When he asks for help from Doctor Strange the stakes become even more dangerous, forcing him to discover what it truly means to be Spider-Man.",
        rich_metadata: {
            title: "Spider-Man: No Way Home",
            year: "2021",
            match_percentage: 95,
            rating: 8.3,
            runtime: "148 min",
            director: "Jon Watts",
            genres: ["Action", "Adventure", "Science Fiction"],
            tags: ["Action", "Adventure", "Science Fiction"],
            audience_type: "Family/General",
            story_summary: "Peter Parker is unmasked and no longer able to separate his normal life from the high-stakes of being a super-hero. When he asks for help from Doctor Strange the stakes become even more dangerous, forcing him to discover what it truly means to be Spider-Man.",
            why_recommended: "Recommended because it matches your preferred genres of action and adventure with high thematic similarity.",
            themes: ["Identity", "Heroism", "Multiverse", "Sacrifice"],
            moods: ["Exciting", "Emotional", "Adventurous"],
            pacing: "Fast-Paced",
            complexity: "Medium",
            world_building: "Rich",
            action_level: "High",
            violence_level: "Moderate",
            language_severity: "Mild",
            adult: false,
            similar_movies: [
                { item_id: 2, title: "The Batman", poster_url: "https://image.tmdb.org/t/p/original/74xTEgt7R36Fpooo50r9T25onhq.jpg", score: 88 },
                { item_id: 5, title: "The King's Man", poster_url: "https://image.tmdb.org/t/p/original/aq4Pwv5Xeuvj6HZKtxyd23e6bE9.jpg", score: 82 }
            ]
        }
    },
    {
        item_id: 2,
        title: "The Batman",
        poster_url: "https://image.tmdb.org/t/p/original/74xTEgt7R36Fpooo50r9T25onhq.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/original/74xTEgt7R36Fpooo50r9T25onhq.jpg",
        overview: "In his second year of fighting crime, Batman uncovers corruption in Gotham City that connects to his own family while facing a serial killer known as the Riddler.",
        rich_metadata: {
            title: "The Batman",
            year: "2022",
            match_percentage: 92,
            rating: 8.1,
            runtime: "176 min",
            director: "Matt Reeves",
            genres: ["Crime", "Mystery", "Thriller"],
            tags: ["Crime", "Mystery", "Thriller"],
            audience_type: "Adult",
            story_summary: "In his second year of fighting crime, Batman uncovers corruption in Gotham City that connects to his own family while facing a serial killer known as the Riddler.",
            why_recommended: "Recommended because it aligns with your interest in gritty crime thrillers and mystery-solving arcs.",
            themes: ["Vengeance", "Corruption", "Justice", "Secrets"],
            moods: ["Gritty", "Dark", "Suspenseful", "Intense"],
            pacing: "Steady",
            complexity: "High",
            world_building: "Exceptional",
            action_level: "Medium",
            violence_level: "High",
            language_severity: "Strong",
            adult: true,
            similar_movies: [
                { item_id: 1, title: "Spider-Man: No Way Home", poster_url: "https://image.tmdb.org/t/p/original/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg", score: 85 },
                { item_id: 3, title: "No Exit", poster_url: "https://image.tmdb.org/t/p/original/vDHsLnOWKlPGmWs0kGfuhNF4w5l.jpg", score: 80 }
            ]
        }
    },
    {
        item_id: 3,
        title: "No Exit",
        poster_url: "https://image.tmdb.org/t/p/original/vDHsLnOWKlPGmWs0kGfuhNF4w5l.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/original/vDHsLnOWKlPGmWs0kGfuhNF4w5l.jpg",
        overview: "Stranded at a rest stop in the mountains during a blizzard, a recovering addict discovers a kidnapped child hidden in a car belonging to one of the people inside the building.",
        rich_metadata: {
            title: "No Exit",
            year: "2022",
            match_percentage: 88,
            rating: 6.3,
            runtime: "95 min",
            director: "Damien Power",
            genres: ["Thriller"],
            tags: ["Thriller"],
            audience_type: "Adult",
            story_summary: "Stranded at a rest stop in the mountains during a blizzard, a recovering addict discovers a kidnapped child hidden in a car belonging to one of the people inside the building.",
            why_recommended: "Recommended because it fits your preference for high-stakes suspense thrillers.",
            themes: ["Survival", "Deception", "Trust"],
            moods: ["Suspenseful", "Intense", "Gritty"],
            pacing: "Fast-Paced",
            complexity: "Medium",
            world_building: "Standard",
            action_level: "Medium",
            violence_level: "High",
            language_severity: "Strong",
            adult: true,
            similar_movies: [
                { item_id: 2, title: "The Batman", poster_url: "https://image.tmdb.org/t/p/original/74xTEgt7R36Fpooo50r9T25onhq.jpg", score: 79 }
            ]
        }
    },
    {
        item_id: 4,
        title: "Encanto",
        poster_url: "https://image.tmdb.org/t/p/original/4j0PNHkMr5ax3IA8tjtxcmPU3QT.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/original/4j0PNHkMr5ax3IA8tjtxcmPU3QT.jpg",
        overview: "The tale of an extraordinary family, the Madrigals, who live hidden in the mountains of Colombia, in a magical house, in a vibrant town, in a wondrous, charmed place.",
        rich_metadata: {
            title: "Encanto",
            year: "2021",
            match_percentage: 94,
            rating: 7.7,
            runtime: "102 min",
            director: "Jared Bush",
            genres: ["Animation", "Comedy", "Family", "Fantasy"],
            tags: ["Animation", "Comedy", "Family", "Fantasy"],
            audience_type: "Family Friendly",
            story_summary: "The tale of an extraordinary family, the Madrigals, who live hidden in the mountains of Colombia, in a magical house, in a vibrant town, in a wondrous, charmed place.",
            why_recommended: "Recommended because you enjoy heartwarming, magical family animations.",
            themes: ["Family", "Destiny", "Identity", "Acceptance"],
            moods: ["Lighthearted", "Emotional", "Captivating"],
            pacing: "Steady",
            complexity: "Low",
            world_building: "Rich",
            action_level: "Low",
            violence_level: "Low",
            language_severity: "None",
            adult: false,
            similar_movies: [
                { item_id: 1, title: "Spider-Man: No Way Home", poster_url: "https://image.tmdb.org/t/p/original/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg", score: 83 }
            ]
        }
    },
    {
        item_id: 5,
        title: "The King's Man",
        poster_url: "https://image.tmdb.org/t/p/original/aq4Pwv5Xeuvj6HZKtxyd23e6bE9.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/original/aq4Pwv5Xeuvj6HZKtxyd23e6bE9.jpg",
        overview: "As a collection of history's worst tyrants and criminal masterminds gather to plot a war to wipe out millions, one man must race against time to stop them.",
        rich_metadata: {
            title: "The King's Man",
            year: "2021",
            match_percentage: 85,
            rating: 7.0,
            runtime: "131 min",
            director: "Matthew Vaughn",
            genres: ["Action", "Adventure", "Thriller", "War"],
            tags: ["Action", "Adventure", "Thriller", "War"],
            audience_type: "Adult",
            story_summary: "As a collection of history's worst tyrants and criminal masterminds gather to plot a war to wipe out millions, one man must race against time to stop them.",
            why_recommended: "Recommended because of its historical context and high-octane spy adventure themes.",
            themes: ["War & Peace", "Duty", "Honor", "Survival"],
            moods: ["Epic", "Exciting", "Intense"],
            pacing: "Fast-Paced",
            complexity: "Medium",
            world_building: "Rich",
            action_level: "High",
            violence_level: "High",
            language_severity: "Moderate",
            adult: true,
            similar_movies: [
                { item_id: 1, title: "Spider-Man: No Way Home", poster_url: "https://image.tmdb.org/t/p/original/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg", score: 82 }
            ]
        }
    },
    {
        item_id: 10,
        title: "Interstellar",
        poster_url: "https://placehold.co/400x600/111/333?text=Interstellar",
        backdrop_url: "https://placehold.co/800x450/111/333?text=Interstellar",
        overview: "The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel and conquer the vast distances involved in an interstellar voyage.",
        rich_metadata: {
            title: "Interstellar",
            year: "2014",
            match_percentage: 98,
            rating: 8.6,
            runtime: "169 min",
            director: "Christopher Nolan",
            genres: ["Science Fiction", "Drama", "Adventure"],
            tags: ["Science Fiction", "Drama", "Adventure"],
            audience_type: "General",
            story_summary: "The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel and conquer the vast distances involved in an interstellar voyage.",
            why_recommended: "Recommended by Aurora AI as a top pick for its breathtaking visual world and deep psychological concepts.",
            themes: ["Space Exploration", "Survival", "Time", "Humanity", "Sacrifice"],
            moods: ["Thought-provoking", "Epic", "Emotional"],
            pacing: "Steady",
            complexity: "High",
            world_building: "Exceptional",
            action_level: "Medium",
            violence_level: "Low",
            language_severity: "Mild",
            adult: false,
            similar_movies: [
                { item_id: 1, title: "Spider-Man: No Way Home", poster_url: "https://image.tmdb.org/t/p/original/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg", score: 87 }
            ]
        }
    },
    {
        item_id: 11,
        title: "Stranger Things",
        poster_url: "https://placehold.co/400x600/111/333?text=Stranger+Things",
        backdrop_url: "https://placehold.co/800x450/111/333?text=Stranger+Things",
        overview: "When a young boy vanishes, a small town uncovers a mystery involving secret experiments, terrifying supernatural forces and one strange little girl.",
        rich_metadata: {
            title: "Stranger Things",
            year: "2016",
            match_percentage: 96,
            rating: 8.8,
            runtime: "Series",
            director: "The Duffer Brothers",
            genres: ["Drama", "Science Fiction", "Mystery"],
            tags: ["Drama", "Science Fiction", "Mystery"],
            audience_type: "General",
            story_summary: "When a young boy vanishes, a small town uncovers a mystery involving secret experiments, terrifying supernatural forces and one strange little girl.",
            why_recommended: "Recommended for its thrilling nostalgia and suspenseful supernatural mystery.",
            themes: ["Friendship", "Good vs Evil", "Mystery", "Survival"],
            moods: ["Atmospheric", "Suspenseful", "Captivating"],
            pacing: "Fast-Paced",
            complexity: "Medium",
            world_building: "Rich",
            action_level: "Medium",
            violence_level: "Moderate",
            language_severity: "Mild",
            adult: false,
            similar_movies: [
                { item_id: 2, title: "The Batman", poster_url: "https://image.tmdb.org/t/p/original/74xTEgt7R36Fpooo50r9T25onhq.jpg", score: 88 }
            ]
        }
    },
    {
        item_id: 12,
        title: "Wednesday",
        poster_url: "https://placehold.co/400x600/111/333?text=Wednesday",
        backdrop_url: "https://placehold.co/800x450/111/333?text=Wednesday",
        overview: "A sleuthing, supernaturally infused mystery charting Wednesday Addams' years as a student at Nevermore Academy.",
        rich_metadata: {
            title: "Wednesday",
            year: "2022",
            match_percentage: 91,
            rating: 8.2,
            runtime: "Series",
            director: "Tim Burton",
            genres: ["Comedy", "Fantasy", "Mystery"],
            tags: ["Comedy", "Fantasy", "Mystery"],
            audience_type: "General",
            story_summary: "A sleuthing, supernaturally infused mystery charting Wednesday Addams' years as a student at Nevermore Academy.",
            why_recommended: "Recommended for its dark wit and gothic mystery themes.",
            themes: ["Mystery", "Good vs Evil", "Destiny"],
            moods: ["Dark", "Lighthearted", "Atmospheric"],
            pacing: "Steady",
            complexity: "Medium",
            world_building: "Rich",
            action_level: "Medium",
            violence_level: "Moderate",
            language_severity: "Mild",
            adult: false,
            similar_movies: [
                { item_id: 4, title: "Encanto", poster_url: "https://image.tmdb.org/t/p/original/4j0PNHkMr5ax3IA8tjtxcmPU3QT.jpg", score: 80 }
            ]
        }
    },
    {
        item_id: 13,
        title: "Dune",
        poster_url: "https://placehold.co/400x600/111/333?text=Dune",
        backdrop_url: "https://placehold.co/800x450/111/333?text=Dune",
        overview: "Paul Atreides, a brilliant and gifted young man born into a great destiny beyond his understanding, must travel to the most dangerous planet in the universe to ensure the future of his family and his people.",
        rich_metadata: {
            title: "Dune",
            year: "2021",
            match_percentage: 95,
            rating: 8.0,
            runtime: "155 min",
            director: "Denis Villeneuve",
            genres: ["Science Fiction", "Adventure", "Drama"],
            tags: ["Science Fiction", "Adventure", "Drama"],
            audience_type: "General",
            story_summary: "Paul Atreides, a brilliant and gifted young man born into a great destiny beyond his understanding, must travel to the most dangerous planet in the universe to ensure the future of his family and his people.",
            why_recommended: "Recommended for its massive epic scale, complex political intrigue, and stellar sound design.",
            themes: ["Destiny", "Survival", "War & Peace", "Humanity"],
            moods: ["Epic", "Atmospheric", "Thought-Provoking"],
            pacing: "Slow Burn",
            complexity: "High",
            world_building: "Exceptional",
            action_level: "High",
            violence_level: "Moderate",
            language_severity: "Mild",
            adult: false,
            similar_movies: [
                { item_id: 10, title: "Interstellar", poster_url: "https://placehold.co/400x600/111/333?text=Interstellar", score: 92 }
            ]
        }
    },
    {
        item_id: 14,
        title: "The Grand Budapest Hotel",
        poster_url: "https://placehold.co/400x600/111/333?text=Budapest+Hotel",
        backdrop_url: "https://placehold.co/800x450/111/333?text=Budapest+Hotel",
        overview: "The writer relates his adventures at a renowned European resort hotel between the first and second World Wars with a concierge who is wrongly framed for murder.",
        rich_metadata: {
            title: "The Grand Budapest Hotel",
            year: "2014",
            match_percentage: 89,
            rating: 8.0,
            runtime: "99 min",
            director: "Wes Anderson",
            genres: ["Comedy", "Drama"],
            tags: ["Comedy", "Drama"],
            audience_type: "General",
            story_summary: "The writer relates his adventures at a renowned European resort hotel between the first and second World Wars with a concierge who is wrongly framed for murder.",
            why_recommended: "Recommended for its distinct visual style, quirky humor, and stellar ensemble cast.",
            themes: ["Friendship", "Loyalty", "Mystery"],
            moods: ["Lighthearted", "Captivating", "Stylized"],
            pacing: "Fast-Paced",
            complexity: "Medium",
            world_building: "Rich",
            action_level: "Low",
            violence_level: "Mild",
            language_severity: "Moderate",
            adult: false,
            similar_movies: [
                { item_id: 4, title: "Encanto", poster_url: "https://image.tmdb.org/t/p/original/4j0PNHkMr5ax3IA8tjtxcmPU3QT.jpg", score: 81 }
            ]
        }
    }
];

// ── Format Discovery & Modulo Heuristic ─────────────────────────────────
window.currentFormat = 'all';
window.isSeries = function(movie) {
    if (!movie) return false;
    return movie.item_id % 3 === 0;
};

window.applyTheme = function(themeName) {
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
    localStorage.setItem('aurora_theme', themeName);
};

window.setDiscoveryFormat = function(format) {
    window.currentFormat = format;
    if (currentPage === 'home') {
        loadHomePage();
    } else if (currentPage === 'categories') {
        loadCategoriesTab();
    }
};

// ── State ─────────────────────────────────────────────────────────────
let globalMovies = [];
let myList = JSON.parse(localStorage.getItem('aurora_mylist') || '[]');
let currentPage = 'home';
let token = 'guest-token';
let userId = 32;

async function authFetch(url, options = {}) {
    options.headers = options.headers || {};
    options.headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(url, options);
    return res;
}

// ══════════════════════════════════════════════════════════════════════
//  INIT
// ══════════════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    const logoutBtn = document.getElementById('logout-btn');
    const adminLink = document.getElementById('admin-link');
    const userDisplay = document.getElementById('current-user-display');

    if (userDisplay) userDisplay.textContent = 'User: Guest';
    if (logoutBtn) logoutBtn.style.display = 'none';
    if (adminLink) adminLink.style.display = 'none';
    
    const savedTheme = localStorage.getItem('aurora_theme') || 'neon';
    applyTheme(savedTheme);
    
    navigateTo('home');
});

// ══════════════════════════════════════════════════════════════════════
//  SIDEBAR & MOBILE SLIDING DRAWER MENU
// ══════════════════════════════════════════════════════════════════════
const mobileMenuBtn = document.getElementById('mobile-menu-btn');
const sidebarBackdrop = document.getElementById('sidebar-backdrop');
const topbarProfileTrig = document.getElementById('topbar-profile-trigger');

window.openDrawer = function() {
    const drawer = document.getElementById('drawer');
    const backdrop = document.getElementById('drawer-backdrop');
    if (drawer && backdrop) {
        drawer.classList.add('open');
        backdrop.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
};

window.closeDrawer = function() {
    const drawer = document.getElementById('drawer');
    const backdrop = document.getElementById('drawer-backdrop');
    if (drawer && backdrop) {
        drawer.classList.remove('open');
        backdrop.classList.remove('active');
        document.body.style.overflow = '';
    }
};

window.closeDrawerModalDirect = function() {
    const modalOverlay = document.getElementById('drawer-modal-overlay');
    if (modalOverlay) {
        modalOverlay.classList.remove('active');
    }
};

window.closeDrawerModal = function(e) {
    const modalOverlay = document.getElementById('drawer-modal-overlay');
    if (modalOverlay && e.target === modalOverlay) {
        modalOverlay.classList.remove('active');
    }
};

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

if(mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', (e) => {
        e.preventDefault();
        openDrawer();
    });
}
if(sidebarBackdrop) sidebarBackdrop.addEventListener('click', closeMobileSidebar);

if(topbarProfileTrig) {
    topbarProfileTrig.addEventListener('click', (e) => {
        e.preventDefault();
        openDrawer();
    });
}

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
    if (window.innerWidth > 1024) return;
    const swipeDist = touchEndX - touchStartX;
    if (swipeDist > 50 && touchStartX < 30) {
        // Swipe Right from edge -> Open mobile drawer
        openDrawer();
    } else if (swipeDist < -50) {
        // Swipe Left -> Close mobile drawer
        closeDrawer();
    }
}

// Accessibility: Close on Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        if (sidebar.classList.contains('open')) {
            closeMobileSidebar();
        }
        closeDrawer();
        closeDrawerModalDirect();
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
        case 'downloads':
            renderDownloadsTab();
            break;
        case 'favorites':
        case 'my-list':
            renderFavoritesTab();
            break;
    }
}

// ── Downloads Tab ────────────────────────────────────────────────────
async function renderDownloadsTab() {
    heroSection.innerHTML = '';
    heroSection.style.display = 'none';
    contentRows.innerHTML = `
        <div class="row-section" style="padding-top:80px;">
            <h1 class="row-section__title" style="font-size:2.2rem;margin-bottom:12px;">Downloads</h1>
            <p style="color:var(--text-muted);font-size:0.95rem;margin-bottom:32px;">Offline media hub. Take your personal movie universe anywhere.</p>
        </div>
    `;
    
    const downloaded = JSON.parse(localStorage.getItem('aurora_downloads') || '[]');
    if (downloaded.length > 0) {
        appendRow('Available Offline', downloaded);
    } else {
        contentRows.innerHTML += `
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:40vh;text-align:center;padding:0 20px;">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                <h2 style="font-size:1.8rem;color:var(--text-primary);margin:20px 0 10px;">No Downloads Yet</h2>
                <p style="color:var(--text-muted);max-width:400px;margin-bottom:24px;">Your downloaded movies and series will appear here for offline viewing.</p>
            </div>
        `;
        await fetchAndRender('Hidden Gems', 'Recommended For Download');
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
    let movies = [];
    try {
        const resp = await authFetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, exclude_ids: window.shownItems || [] })
        });
        if (resp.ok) {
            const data = await resp.json();
            movies = Array.isArray(data.response) ? data.response : (data.response && data.response.value);
        }
    } catch (e) {
        console.warn(`Failed to fetch for row '${rowTitle}', attempting fallback. Error:`, e);
    }

    // Fallback logic if we have no movies or empty results
    if (!movies || !Array.isArray(movies) || movies.length === 0) {
        const qLower = query.toLowerCase();
        let filtered = FALLBACK_MOVIES.filter(m => {
            return m.rich_metadata.genres.some(g => qLower.includes(g.toLowerCase()) || g.toLowerCase().includes(qLower)) ||
                   m.overview.toLowerCase().includes(qLower) ||
                   m.title.toLowerCase().includes(qLower);
        });
        
        if (filtered.length === 0) {
            filtered = FALLBACK_MOVIES.sort(() => 0.5 - Math.random()).slice(0, 5);
        }
        movies = filtered;
    }

    // Format Heuristic Filter (Movies vs TV Series)
    let filteredMovies = movies;
    if (currentFormat === 'movie') {
        filteredMovies = movies.filter(m => !isSeries(m));
    } else if (currentFormat === 'series') {
        filteredMovies = movies.filter(m => isSeries(m));
    }

    // If format filtering leaves us empty, fill with format-aligned fallbacks
    if (filteredMovies.length === 0) {
        const qLower = query.toLowerCase();
        let fallbackList = FALLBACK_MOVIES.filter(m => {
            const matchesQuery = m.rich_metadata.genres.some(g => qLower.includes(g.toLowerCase()) || g.toLowerCase().includes(qLower)) ||
                                 m.overview.toLowerCase().includes(qLower) ||
                                 m.title.toLowerCase().includes(qLower);
            const matchesFormat = currentFormat === 'all' || 
                                  (currentFormat === 'movie' && !isSeries(m)) || 
                                  (currentFormat === 'series' && isSeries(m));
            return matchesQuery && matchesFormat;
        });
        
        if (fallbackList.length === 0) {
            fallbackList = FALLBACK_MOVIES.filter(m => {
                return currentFormat === 'all' || 
                       (currentFormat === 'movie' && !isSeries(m)) || 
                       (currentFormat === 'series' && isSeries(m));
            }).sort(() => 0.5 - Math.random()).slice(0, 5);
        }
        filteredMovies = fallbackList;
    }
    movies = filteredMovies;

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

// ── Favorites & Watchlist ──────────────────────────────────────────────
window.renderFavoritesTab = function() {
    heroSection.innerHTML = '';
    heroSection.style.display = 'none';
    contentRows.innerHTML = '';

    const savedMovies = myList.filter(m => !isSeries(m));
    const savedSeries = myList.filter(m => isSeries(m));

    const headerSec = document.createElement('div');
    headerSec.className = 'row-section';
    headerSec.style.paddingTop = '80px';
    headerSec.style.marginBottom = '20px';
    headerSec.innerHTML = `
        <h1 class="row-section__title" style="font-size:2.2rem;margin-bottom:12px;">Favorites & Watchlist</h1>
        <p style="color:var(--text-muted);font-size:0.95rem;">All your saved movies, TV series, and collections in one place.</p>
    `;
    contentRows.appendChild(headerSec);

    if (myList.length === 0) {
        const empty = document.createElement('div');
        empty.style.cssText = 'display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:40vh;text-align:center;padding:0 20px;';
        empty.innerHTML = `
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
            <h2 style="font-size:1.8rem;color:var(--text-primary);margin:20px 0 10px;">Your Watchlist is Empty</h2>
            <p style="color:var(--text-muted);max-width:400px;margin-bottom:24px;">Browse movies and series and add them to your watchlist to see them here.</p>
        `;
        contentRows.appendChild(empty);
        
        fetchAndRender('Hidden Gems', 'Recommended For You');
        return;
    }

    if (savedMovies.length > 0) {
        appendRow('Saved Movies', savedMovies);
    }
    if (savedSeries.length > 0) {
        appendRow('Saved TV Series', savedSeries);
    }
    
    const history = JSON.parse(localStorage.getItem('aurora_history') || '[]');
    if (history.length > 0) {
        appendRow('Recently Viewed & Liked', history);
    }
};

function renderMyList() {
    renderFavoritesTab();
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
    let prepend = `
        <div class="row-section" style="padding-top: 80px; padding-left: 24px; padding-right: 24px; margin-bottom: 20px;">
            <h1 style="font-size: 2.2rem; font-weight: 800; color: var(--text-primary); margin-bottom: 12px;">Explore Hub</h1>
            <p style="color: var(--text-muted); font-size: 0.95rem; margin-bottom: 24px;">Discover content by genres, themes, moods, and curated AI collections.</p>
            
            <div class="format-filter-container">
                <button class="format-tab ${currentFormat === 'all' ? 'active' : ''}" onclick="setDiscoveryFormat('all')">🔮 Combined Discovery</button>
                <button class="format-tab ${currentFormat === 'movie' ? 'active' : ''}" onclick="setDiscoveryFormat('movie')">🎬 Movies Only</button>
                <button class="format-tab ${currentFormat === 'series' ? 'active' : ''}" onclick="setDiscoveryFormat('series')">📺 TV Series Only</button>
            </div>
            
            <!-- Category Search Bar -->
            <div style="position: relative; margin-bottom: 28px;">
                <input type="text" id="category-search-input" placeholder="Search categories (e.g. Sci-Fi, Dystopian, Dark...)" 
                       style="width: 100%; padding: 14px 20px; border-radius: var(--r-pill); background: rgba(255,255,255,0.04); border: 1px solid var(--glass-border); color: white; font-size: 0.95rem; outline: none; transition: border-color 0.2s;"
                       oninput="filterCategoriesList(this.value)">
                <span style="position: absolute; right: 20px; top: 50%; transform: translateY(-50%); color: var(--text-muted);">🔍</span>
            </div>
        </div>
    `;
    
    const categoriesData = [
        // Genres
        { name: 'Action', grad: 'linear-gradient(135deg, #EF4444, #B91C1C)', icon: '🎬', type: 'genre' },
        { name: 'Comedy', grad: 'linear-gradient(135deg, #F59E0B, #D97706)', icon: '😂', type: 'genre' },
        { name: 'Sci-Fi', grad: 'linear-gradient(135deg, #8B5CF6, #4C1D95)', icon: '🚀', type: 'genre' },
        { name: 'Horror', grad: 'linear-gradient(135deg, #374151, #111827)', icon: '👻', type: 'genre' },
        { name: 'Drama', grad: 'linear-gradient(135deg, #3B82F6, #1D4ED8)', icon: '🎭', type: 'genre' },
        { name: 'Romance', grad: 'linear-gradient(135deg, #EC4899, #BE185D)', icon: '💖', type: 'genre' },
        { name: 'Thriller', grad: 'linear-gradient(135deg, #10B981, #047857)', icon: '🕵️', type: 'genre' },
        { name: 'Anime', grad: 'linear-gradient(135deg, #06B6D4, #0891B2)', icon: '🌸', type: 'genre' },
        { name: 'Mystery', grad: 'linear-gradient(135deg, #EC4899, #8B5CF6)', icon: '🔍', type: 'genre' },
        
        // Themes
        { name: 'Space Exploration', grad: 'linear-gradient(135deg, #4F46E5, #312E81)', icon: '🌌', type: 'theme' },
        { name: 'Time Travel', grad: 'linear-gradient(135deg, #D97706, #78350F)', icon: '⏳', type: 'theme' },
        { name: 'Artificial Intelligence', grad: 'linear-gradient(135deg, #0891B2, #0F766E)', icon: '🤖', type: 'theme' },
        { name: 'Cyberpunk', grad: 'linear-gradient(135deg, #C084FC, #581C87)', icon: '🌆', type: 'theme' },
        { name: 'Survival', grad: 'linear-gradient(135deg, #059669, #064E3B)', icon: '⛺', type: 'theme' },
        
        // Moods
        { name: 'Mind-Bending', grad: 'linear-gradient(135deg, #EC4899, #8B5CF6)', icon: '🌀', type: 'mood' },
        { name: 'Dark & Gritty', grad: 'linear-gradient(135deg, #1E293B, #0F172A)', icon: '🖤', type: 'mood' },
        { name: 'Heartwarming', grad: 'linear-gradient(135deg, #F43F5E, #9F1239)', icon: '❤️', type: 'mood' },
        { name: 'Thought-Provoking', grad: 'linear-gradient(135deg, #10B981, #115E59)', icon: '💭', type: 'mood' },
        
        // AI & Awards
        { name: 'Hidden Gems', grad: 'linear-gradient(135deg, #14B8A6, #0F766E)', icon: '💎', type: 'ai' },
        { name: 'Oscar Winners', grad: 'linear-gradient(135deg, #F59E0B, #78350F)', icon: '🏆', type: 'award' }
    ];

    contentRows.innerHTML = prepend + `
        <div class="category-selection-container" style="padding: 0 24px 40px;">
            <div id="categories-grid-container">
                <h3 style="font-size: 1.15rem; color: white; margin-bottom: 16px;">All Categories</h3>
                <div class="genre-bubble-grid" id="category-cards-grid">
                    ${categoriesData.map(c => `
                        <div class="genre-bubble category-card" data-name="${c.name.toLowerCase()}" onclick="selectCategory('${c.name}')" 
                             style="background: ${c.grad};">
                            <span class="genre-bubble__icon">${c.icon}</span>
                            <span class="genre-bubble__name">${c.name}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
}

window.filterCategoriesList = function(val) {
    const query = val.toLowerCase().trim();
    const cards = document.querySelectorAll('.category-card');
    const synonymMap = {
        'sci-fi': ['science fiction', 'space', 'ai', 'robot', 'dystopian', 'cyberpunk', 'time travel'],
        'drama': ['tragedy', 'relationships', 'emotional'],
        'thriller': ['crime', 'suspense', 'detective', 'mystery'],
        'animation': ['anime', 'cartoons', 'kids']
    };
    
    cards.forEach(card => {
        const name = card.dataset.name;
        let isMatch = name.includes(query);
        for (const [key, list] of Object.entries(synonymMap)) {
            if (query.includes(key) || key.includes(query)) {
                if (list.some(syn => name.includes(syn))) {
                    isMatch = true;
                }
            }
        }
        card.style.display = isMatch ? 'flex' : 'none';
    });
};

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
    
    let movies = [];
    try {
        const resp = await authFetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: categoryName, exclude_ids: [] })
        });
        if (resp.ok) {
            const data = await resp.json();
            movies = Array.isArray(data.response) ? data.response : (data.response && data.response.value);
        }
    } catch(e) {
        console.warn(`Category detail API error, utilizing fallbacks for '${categoryName}':`, e);
    }
    
    if (!movies || !Array.isArray(movies) || movies.length === 0) {
        const catLower = categoryName.toLowerCase();
        movies = FALLBACK_MOVIES.filter(m => {
            return m.rich_metadata.genres.some(g => g.toLowerCase().includes(catLower) || catLower.includes(g.toLowerCase())) ||
                   m.title.toLowerCase().includes(catLower) ||
                   m.overview.toLowerCase().includes(catLower);
        });
        
        if (movies.length === 0) {
            movies = FALLBACK_MOVIES.slice(0, 6);
        }
    }

    // Apply Movies/Series Heuristic Filtering!
    let filtered = movies;
    if (currentFormat === 'movie') {
        filtered = movies.filter(m => !isSeries(m));
    } else if (currentFormat === 'series') {
        filtered = movies.filter(m => isSeries(m));
    }
    
    // If the filtered list is empty, let's load generic fallback items of that type
    if (filtered.length === 0) {
        filtered = FALLBACK_MOVIES.filter(m => {
            return currentFormat === 'all' || 
                   (currentFormat === 'movie' && !isSeries(m)) || 
                   (currentFormat === 'series' && isSeries(m));
        }).slice(0, 6);
    }
    movies = filtered;
    
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
            <div class="card-3d__glare"></div>
        </div>
        <div class="card-expand">
            <img src="${backdrop}" class="card-expand__img" alt="" loading="lazy" onerror="this.src='${placeholder(t)}'">
            <div class="card-expand__body">
                <div class="card-expand__title">${t}</div>
                <div class="card-expand__meta">
                    <span class="card-expand__pct">${score}% Match</span>
                    <span class="card-expand__type" style="color: var(--aurora-cyan); font-weight: 600; margin: 0 4px;">${isSeries(movie) ? 'TV Series' : 'Movie'}</span>
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

    window.updateAmbientBackground(bg);

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

    clearSkeletons();

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
                <div class="card-3d__glare"></div>
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

    // Cover flow scroll physics & spatial transformation
    const rowScroll = sec.querySelector('.row-scroll');
    if (rowScroll) {
        rowScroll.addEventListener('scroll', () => {
            window.updateSpatialCarousel(rowScroll);
        }, { passive: true });
        
        setTimeout(() => {
            window.updateSpatialCarousel(rowScroll);
        }, 150);
    }
}

// ══════════════════════════════════════════════════════════════════════
//  3D TILT & GLARE EFFECT
// ══════════════════════════════════════════════════════════════════════
function attachTilt(card) {
    const glare = card.querySelector('.card-3d__glare');
    
    card.addEventListener('mouseenter', () => {
        const id = parseInt(card.dataset.id);
        const movie = globalMovies.find(m => m.item_id === id) || FALLBACK_MOVIES.find(m => m.item_id === id);
        if (movie) {
            window.updateAmbientBackground(movie.backdrop_url || movie.poster_url);
        }
    });

    card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const cx = rect.width / 2;
        const cy = rect.height / 2;
        const rotX = ((y - cy) / cy) * -8;
        const rotY = ((x - cx) / cx) * 8;
        card.style.transform = `perspective(800px) rotateX(${rotX}deg) rotateY(${rotY}deg) scale3d(1.04,1.04,1.04)`;
        
        if (glare) {
            const pctX = (x / rect.width) * 100;
            const pctY = (y / rect.height) * 100;
            glare.style.setProperty('--glare-x', `${pctX}%`);
            glare.style.setProperty('--glare-y', `${pctY}%`);
        }
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
function renderModalData(m, id) {
    document.getElementById('modal-title').textContent = m.title || 'Unknown';
    
    const posterUrl = m.poster_url || placeholder(m.title);
    const bgUrl = m.backdrop_url || posterUrl;
    document.getElementById('modal-poster').src = posterUrl;
    document.getElementById('modal-backdrop').style.backgroundImage = `url('${bgUrl}')`;
    
    const typeLabel = (id % 3 === 0) ? 'TV Series' : 'Movie';
    document.getElementById('modal-match').innerHTML = `${m.match_percentage || 85}% Match <span style="margin-left: 8px; padding: 2px 6px; background: rgba(6, 182, 212, 0.15); border: 1px solid rgba(6, 182, 212, 0.3); border-radius: 4px; color: var(--aurora-cyan); font-size: 0.8rem; font-weight: 700; display: inline-block;">${typeLabel}</span>`;
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
    
    // Render "This Movie Is" characteristics
    const characteristics = [];
    if (m.pacing) characteristics.push(m.pacing);
    if (m.complexity && m.complexity !== 'Medium') characteristics.push(`${m.complexity} Complexity`);
    if (m.world_building && m.world_building !== 'Standard') characteristics.push(`${m.world_building} World`);
    if (m.action_level && m.action_level !== 'Medium') characteristics.push(`${m.action_level} Action`);
    if (m.audience_type) characteristics.push(m.audience_type);
    if (m.moods && m.moods.length > 0) characteristics.push(...m.moods.slice(0, 2));
    
    const characteristicsContainer = document.getElementById('modal-characteristics');
    if (characteristicsContainer) {
        if (characteristics.length > 0) {
            characteristicsContainer.innerHTML = [...new Set(characteristics)].map(c => `<span>${c}</span>`).join('');
        } else {
            characteristicsContainer.innerHTML = '<span>Cinematic</span><span>Immersive</span>';
        }
    }
    
    document.getElementById('modal-pacing').textContent = m.pacing || 'Steady';
    document.getElementById('modal-complexity').textContent = m.complexity || 'Medium';
    document.getElementById('modal-world').textContent = m.world_building || 'Standard';
    document.getElementById('modal-action').textContent = m.action_level || 'Medium';
    
    document.getElementById('adv-violence').textContent = m.violence_level || 'Low';
    document.getElementById('adv-language').textContent = m.language_severity || 'Mild';
    document.getElementById('adv-adult').textContent = m.adult ? 'Yes' : 'No';
    
    // Populate bottom details panel
    let writers = m.writers || '';
    if (!writers) {
        writers = m.director ? `${m.director}, Jonathan Nolan` : 'Christopher Nolan, Jonathan Nolan';
    }
    document.getElementById('modal-writers').textContent = writers;
    
    let producers = m.producers || 'Emma Thomas, Kevin Feige';
    document.getElementById('modal-producers').textContent = producers;
    
    let studios = m.studios || 'Warner Bros. Pictures, Legendary Entertainment';
    document.getElementById('modal-studios').textContent = studios;
    
    let awards = m.awards || 'Nominated for multiple prestigious Academy Awards.';
    if (m.title && m.title.includes("Spider-Man")) {
        awards = "Academy Award nominee for Best Visual Effects";
    } else if (m.title && m.title.includes("Batman")) {
        awards = "Nominated for 3 Academy Awards, including Best Sound";
    } else if (m.title && m.title.includes("Interstellar")) {
        awards = "Oscar Winner for Best Visual Effects, nominated for 5 Oscars";
    } else if (m.title && m.title.includes("Dune")) {
        awards = "Winner of 6 Academy Awards, including Best Cinematography";
    }
    document.getElementById('modal-awards').textContent = awards;
    
    let availability = m.availability || 'Available on Aurora Premium streaming (4K UHD)';
    document.getElementById('modal-availability').textContent = availability;

    const simContainer = document.getElementById('modal-similar');
    const seedMovie = globalMovies.find(item => item.item_id === id) || FALLBACK_MOVIES.find(item => item.item_id === id) || { item_id: id, rich_metadata: m, title: m.title };
    
    const recs = getSimilarRecommendations(seedMovie);
    if (recs && recs.length > 0) {
        simContainer.innerHTML = recs.map(r => {
            const sm = r.movie;
            const poster = sm.poster_url || placeholder(sm.title);
            return `
                <div class="sim-card" onclick="openModal(${sm.item_id})">
                    <img src="${poster}" alt="${sm.title}" class="sim-poster" loading="lazy" onerror="this.src='${placeholder(sm.title)}'">
                    <div class="sim-title">${sm.title}</div>
                    <div class="sim-match">${r.score}% Match</div>
                    <div class="sim-reason" style="font-size: 0.68rem; color: var(--text-muted); text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding: 0 4px;" title="${r.reasoning}">${r.reasoning}</div>
                </div>
            `;
        }).join('');
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
}

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
        let m;
        if (resp.ok) {
            m = await resp.json();
        }
        if (!m || m.error) {
            throw new Error((m && m.error) || 'Failed to fetch details');
        }
        renderModalData(m, id);
    } catch (err) {
        console.warn(`Movie detail API failed for ID ${id}, using local fallback:`, err);
        const movie = globalMovies.find(item => item.item_id === id) || FALLBACK_MOVIES.find(item => item.item_id === id);
        if (movie) {
            const m = movie.rich_metadata || {};
            const fallbackDetails = {
                title: movie.title || m.title || "Unknown",
                poster_url: movie.poster_url || m.poster_url || placeholder(movie.title),
                backdrop_url: movie.backdrop_url || m.backdrop_url || movie.poster_url,
                match_percentage: m.match_percentage || 85,
                year: m.year || "2022",
                rating: m.rating || 8.0,
                runtime: m.runtime || "120 min",
                genres: m.genres || m.tags || ["Drama"],
                audience_type: m.audience_type || "General",
                story_summary: movie.overview || m.story_summary || "Cinematic details served from local cache.",
                why_recommended: m.why_recommended || "Highly correlated with your preferences.",
                director: m.director || "Unknown Director",
                themes: m.themes || ["Cinema"],
                moods: m.moods || ["Captivating"],
                pacing: m.pacing || "Steady",
                complexity: m.complexity || "Medium",
                world_building: m.world_building || "Standard",
                action_level: m.action_level || "Medium",
                violence_level: m.violence_level || "Low",
                language_severity: m.language_severity || "Mild",
                adult: m.adult || false,
                similar_movies: m.similar_movies || [
                    { item_id: 1, title: "Spider-Man: No Way Home", poster_url: "https://image.tmdb.org/t/p/original/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg", score: 85 }
                ]
            };
            renderModalData(fallbackDetails, id);
        } else {
            document.getElementById('modal-title').textContent = 'Error loading details.';
            document.getElementById('modal-synopsis').textContent = 'Could not fetch data.';
        }
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

function clearSkeletons() {
    const skeletonSections = contentRows.querySelectorAll('section');
    skeletonSections.forEach(sec => {
        if (sec.querySelector('.skeleton') || sec.classList.contains('skeleton') || sec.id === 'skeleton-row-section') {
            sec.remove();
        }
    });
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
        <section class="row-section" id="skeleton-row-section" style="${withHero ? '' : 'padding-top:0;'}">
            <div class="skeleton" style="width:200px;height:22px;margin-bottom:16px;"></div>
            <div class="row-scroll">${skeletonCards}</div>
        </section>
    `;
    
    let prepend = '';
    if (currentPage === 'home') {
        prepend = `
            <div class="row-section" style="padding-top: 20px; margin-bottom: 0;">
                <div class="format-filter-container">
                    <button class="format-tab ${currentFormat === 'all' ? 'active' : ''}" onclick="setDiscoveryFormat('all')">🔮 Combined Discovery</button>
                    <button class="format-tab ${currentFormat === 'movie' ? 'active' : ''}" onclick="setDiscoveryFormat('movie')">🎬 Movies Only</button>
                    <button class="format-tab ${currentFormat === 'series' ? 'active' : ''}" onclick="setDiscoveryFormat('series')">📺 TV Series Only</button>
                </div>
            </div>
        `;
    }
    
    contentRows.innerHTML = prepend + skeletonRow;
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

// ══════════════════════════════════════════════════════════════════════
//  DRAWER FLOATING MODAL LOGIC
// ══════════════════════════════════════════════════════════════════════
window.openDrawerOption = function(option) {
    closeDrawer();
    
    const modalOverlay = document.getElementById('drawer-modal-overlay');
    const modalContent = document.getElementById('drawer-modal-content');
    if (!modalOverlay || !modalContent) return;
    
    let html = '';
    switch (option) {
        case 'account':
            html = `
                <h2>👤 Account Details</h2>
                <div class="modal-info-group">
                    <span class="modal-info-label">Membership Tier</span>
                    <span class="modal-info-value">Aurora Cinematic Premium (4K UHD)</span>
                </div>
                <div class="modal-info-group">
                    <span class="modal-info-label">Current User</span>
                    <span class="modal-info-value">Guest User (ID: ${userId})</span>
                </div>
                <div class="modal-info-group">
                    <span class="modal-info-label">Devices Online</span>
                    <span class="modal-info-value">2 Active Devices (1 Mobile, 1 Laptop)</span>
                </div>
                <div class="modal-info-group">
                    <span class="modal-info-label">Next Renewal</span>
                    <span class="modal-info-value">July 24, 2026 ($14.99/mo)</span>
                </div>
                <button class="modal-submit-btn" onclick="closeDrawerModalDirect()">Done</button>
            `;
            break;
        case 'settings':
            const autoplay = localStorage.getItem('aurora_autoplay') !== 'false';
            const quality = localStorage.getItem('aurora_quality') || 'auto';
            const motion = localStorage.getItem('aurora_reduced_motion') === 'true';
            
            html = `
                <h2>⚙️ Settings</h2>
                <div class="modal-form-row">
                    <label style="display: flex; align-items: center; gap: 10px; cursor: pointer;">
                        <input type="checkbox" id="settings-autoplay" ${autoplay ? 'checked' : ''} style="width: 20px; height: 20px;">
                        <span>Autoplay Cinematic Trailers</span>
                    </label>
                </div>
                <div class="modal-form-row">
                    <label for="settings-quality">Streaming Quality</label>
                    <select id="settings-quality">
                        <option value="auto" ${quality === 'auto' ? 'selected' : ''}>Auto (Recommended)</option>
                        <option value="4k" ${quality === '4k' ? 'selected' : ''}>4K UHD (Highest Quality)</option>
                        <option value="1080p" ${quality === '1080p' ? 'selected' : ''}>1080p Full HD</option>
                        <option value="data" ${quality === 'data' ? 'selected' : ''}>Data Saver (SD)</option>
                    </select>
                </div>
                <div class="modal-form-row">
                    <label style="display: flex; align-items: center; gap: 10px; cursor: pointer;">
                        <input type="checkbox" id="settings-motion" ${motion ? 'checked' : ''} style="width: 20px; height: 20px;">
                        <span>Reduced Motion (Disable 3D tilt & scaling)</span>
                    </label>
                </div>
                <button class="modal-submit-btn" onclick="saveSettings()">Save Changes</button>
            `;
            break;
        case 'theme':
            const currentTheme = localStorage.getItem('aurora_theme') || 'neon';
            html = `
                <h2>🎨 Theme Preferences</h2>
                <div class="modal-form-row">
                    <label style="display: flex; align-items: center; gap: 10px; cursor: pointer;">
                        <input type="radio" name="theme-choice" value="neon" ${currentTheme === 'neon' ? 'checked' : ''} style="width: 20px; height: 20px;">
                        <span>Aurora Neon (Default Cyberpunk)</span>
                    </label>
                </div>
                <div class="modal-form-row">
                    <label style="display: flex; align-items: center; gap: 10px; cursor: pointer;">
                        <input type="radio" name="theme-choice" value="slate" ${currentTheme === 'slate' ? 'checked' : ''} style="width: 20px; height: 20px;">
                        <span>Midnight Slate (Elegant Dark)</span>
                    </label>
                </div>
                <div class="modal-form-row">
                    <label style="display: flex; align-items: center; gap: 10px; cursor: pointer;">
                        <input type="radio" name="theme-choice" value="oled" ${currentTheme === 'oled' ? 'checked' : ''} style="width: 20px; height: 20px;">
                        <span>OLED Black (Deep Contrast)</span>
                    </label>
                </div>
                <button class="modal-submit-btn" onclick="saveThemeChoice()">Apply Theme</button>
            `;
            break;
        case 'feedback':
            html = `
                <h2>💬 App Feedback</h2>
                <div class="modal-form-row">
                    <label for="feedback-stars">Rate your experience</label>
                    <select id="feedback-stars">
                        <option value="5">⭐⭐⭐⭐⭐ Excellent</option>
                        <option value="4">⭐⭐⭐⭐ Very Good</option>
                        <option value="3">⭐⭐⭐ Good</option>
                        <option value="2">⭐⭐ Fair</option>
                        <option value="1">⭐ Poor</option>
                    </select>
                </div>
                <div class="modal-form-row">
                    <label for="feedback-text">Tell us what we can improve</label>
                    <textarea id="feedback-text" rows="4" placeholder="Enter your thoughts..." style="resize: none;"></textarea>
                </div>
                <button class="modal-submit-btn" onclick="submitFeedback()">Submit Feedback</button>
            `;
            break;
        case 'info':
            html = `
                <h2>ℹ️ App Information</h2>
                <div class="modal-info-group">
                    <span class="modal-info-label">App Version</span>
                    <span class="modal-info-value">2.1.0-neon</span>
                </div>
                <div class="modal-info-group">
                    <span class="modal-info-label">Build Date</span>
                    <span class="modal-info-value">2026.06.24.1</span>
                </div>
                <div class="modal-info-group">
                    <span class="modal-info-label">Platform Core</span>
                    <span class="modal-info-value">FastAPI / RAG Vector search / Embedding similarity</span>
                </div>
                <div class="modal-info-group">
                    <span class="modal-info-label">System Integrity</span>
                    <span class="modal-info-value" style="color:var(--match-green)">All services online</span>
                </div>
                <button class="modal-submit-btn" onclick="closeDrawerModalDirect()">Done</button>
            `;
            break;
        case 'help':
            html = `
                <h2>❓ Help Centre</h2>
                <div style="display:flex; flex-direction:column; gap:16px; max-height: 40vh; overflow-y:auto; margin-bottom:20px; padding-right:8px;">
                    <div>
                        <h4 style="color:white; margin-bottom:6px;">Q: How does Aurora AI recommend movies?</h4>
                        <p style="font-size:0.9rem; line-height:1.4; color:var(--text-secondary)">A: Aurora uses vector embeddings to understand movie themes and match them to your taste based on click signals.</p>
                    </div>
                    <div>
                        <h4 style="color:white; margin-bottom:6px;">Q: How do I save items to my watchlist?</h4>
                        <p style="font-size:0.9rem; line-height:1.4; color:var(--text-secondary)">A: Tap the "+" button on any movie card or details panel. It saves instantly.</p>
                    </div>
                    <div>
                        <h4 style="color:white; margin-bottom:6px;">Q: Can I use conversational search?</h4>
                        <p style="font-size:0.9rem; line-height:1.4; color:var(--text-secondary)">A: Yes! Open the Search tab to chat directly with the Aurora Assistant, e.g. "Suggest some dark thrillers".</p>
                    </div>
                </div>
                <button class="modal-submit-btn" onclick="closeDrawerModalDirect()">Done</button>
            `;
            break;
        case 'logout':
            html = `
                <h2>🚪 Log Out</h2>
                <p style="color:var(--text-secondary); margin-bottom:24px; line-height:1.5;">Are you sure you want to log out of Aurora AI?</p>
                <div style="display:flex; gap:12px;">
                    <button class="modal-submit-btn" onclick="performLogOut()" style="background:#ef4444; color:white; margin-top:0;">Log Out</button>
                    <button class="modal-submit-btn" onclick="closeDrawerModalDirect()" style="background:rgba(255,255,255,0.08); color:white; margin-top:0;">Cancel</button>
                </div>
            `;
            break;
    }
    
    modalContent.innerHTML = html;
    modalOverlay.classList.add('active');
};

window.saveSettings = function() {
    const autoplay = document.getElementById('settings-autoplay').checked;
    const quality = document.getElementById('settings-quality').value;
    const motion = document.getElementById('settings-motion').checked;
    
    localStorage.setItem('aurora_autoplay', autoplay);
    localStorage.setItem('aurora_quality', quality);
    localStorage.setItem('aurora_reduced_motion', motion);
    
    if (motion) {
        document.body.classList.add('reduced-motion');
    } else {
        document.body.classList.remove('reduced-motion');
    }
    
    closeDrawerModalDirect();
    alert('Settings saved successfully!');
};

window.saveThemeChoice = function() {
    const choice = document.querySelector('input[name="theme-choice"]:checked').value;
    applyTheme(choice);
    closeDrawerModalDirect();
};

window.submitFeedback = function() {
    const stars = document.getElementById('feedback-stars').value;
    const text = document.getElementById('feedback-text').value;
    alert(`Thank you for your rating of ${stars} stars! Your feedback has been received.`);
    closeDrawerModalDirect();
};

window.performLogOut = function() {
    closeDrawerModalDirect();
    alert('You have logged out of Aurora AI.');
};
