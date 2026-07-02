/* ======================================================================
   STREAMORA AI — 3D Spatial Cinematic Frontend
   Netflix × Apple TV × VisionOS Experience
   ====================================================================== */

// ── DOM References ────────────────────────────────────────────────────
const sidebar       = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebarNav    = document.getElementById('sidebar-nav');
const userIdInput   = document.getElementById('user-id-input');
const topbar        = document.getElementById('topbar');

const searchTrigger = document.getElementById('topbar-search-trigger') || document.getElementById('search-trigger');
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

// ── Progressive Image Loading & Error Handlers ───────────────────────
window.imageLoaded = function(img) {
    img.classList.add('loaded');
    const container = img.closest('.img-container');
    if (container) {
        const placeholder = container.querySelector('.img-placeholder');
        if (placeholder) {
            placeholder.style.opacity = '0';
            setTimeout(() => {
                if (placeholder.parentNode) {
                    placeholder.parentNode.removeChild(placeholder);
                }
            }, 400);
        }
    }
};

window.imageLoadError = function(img, title) {
    img.style.display = 'none';
    const card = img.closest('.card-wrap, .movie-card, .search-result-card');
    if (card) {
        card.style.display = 'none';
    } else {
        const container = img.closest('.img-container');
        if (container) {
            container.style.display = 'none';
        }
    }
};

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
            // Apply currentFormat filtering before scoring and ranking candidates
            const matchesFormat = window.currentFormat === 'all' ||
                                  (window.currentFormat === 'movie' && !window.isSeries(m)) ||
                                  (window.currentFormat === 'series' && window.isSeries(m));
            if (matchesFormat) {
                seen.add(m.item_id);
                uniquePool.push(m);
            }
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
            rating: 8.3,
            runtime: "176 min",
            director: "Matt Reeves",
            genres: ["Crime", "Mystery", "Thriller"],
            tags: ["Crime", "Mystery", "Thriller"],
            audience_type: "Adult",
            story_summary: "In his second year of fighting crime, Batman uncovers corruption in Gotham City that connects to his own family while facing a serial killer known as the Riddler.",
            why_recommended: "Recommended for its dark mystery detective elements and excellent atmospheric cinematography.",
            themes: ["Vengeance", "Corruption", "Justice", "Family Secrets"],
            moods: ["Gritty", "Dark", "Atmospheric"],
            pacing: "Slow Burn",
            complexity: "Medium",
            world_building: "Rich",
            action_level: "Medium",
            violence_level: "Moderate",
            language_severity: "Mild",
            adult: false,
            similar_movies: [
                { item_id: 1, title: "Spider-Man: No Way Home", poster_url: "https://image.tmdb.org/t/p/original/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg", score: 85 },
                { item_id: 3, title: "No Exit", poster_url: "https://image.tmdb.org/t/p/original/vDHsLnOWKlPGmWs0kGfuhNF4w5l.jpg", score: 80 }
            ]
        }
    },
    {
        item_id: 3,
        title: "No Exit",
        poster_url: "https://image.tmdb.org/t/p/w500/vDHsLnOWKlPGmWs0kGfuhNF4w5l.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/vDHsLnOWKlPGmWs0kGfuhNF4w5l.jpg",
        overview: "During a blizzard and stranded at a highway rest stop in the mountains, a college student discovers a kidnapped child hidden in a car belonging to one of the people inside.",
        rich_metadata: {
            title: "No Exit",
            year: "2022",
            match_percentage: 84,
            rating: 6.1,
            runtime: "95 min",
            director: "Damien Power",
            genres: ["Thriller"],
            tags: ["Thriller"],
            audience_type: "Adult",
            story_summary: "During a blizzard and stranded at a highway rest stop in the mountains, a college student discovers a kidnapped child hidden in a car belonging to one of the people inside.",
            why_recommended: "Recommended because it is a fast-paced mystery thriller with constant high stakes.",
            themes: ["Survival", "Trust", "Deception"],
            moods: ["Suspenseful", "Intense", "Claustrophobic"],
            pacing: "Fast-Paced",
            complexity: "Medium",
            world_building: "Standard",
            action_level: "High",
            violence_level: "High",
            language_severity: "Strong",
            adult: false,
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
        overview: "The tale of an extraordinary family, the Madrigals, who live hidden in the mountains of Colombia, in a magical house, in a vibrant town, in a wondrous, charmed place called an Encanto. The magic of the Encanto has blessed every child in the family with a unique gift from super strength to the power to heal—every child except one, Mirabel.",
        rich_metadata: {
            title: "Encanto",
            year: "2021",
            match_percentage: 90,
            rating: 7.2,
            runtime: "102 min",
            director: "Jared Bush",
            genres: ["Animation", "Comedy", "Family", "Fantasy"],
            tags: ["Animation", "Comedy", "Family", "Fantasy"],
            audience_type: "Family Friendly",
            story_summary: "The tale of an extraordinary family, the Madrigals, who live hidden in the mountains of Colombia, in a magical house, in a vibrant town, in a wondrous, charmed place called an Encanto. The magic of the Encanto has blessed every child in the family with a unique gift from super strength to the power to heal—every child except one, Mirabel.",
            why_recommended: "Recommended for its heartwarming family themes, gorgeous animation, and catchy musical numbers.",
            themes: ["Family Burden", "Self-Worth", "Identity", "Acceptance"],
            moods: ["Uplifting", "Emotional", "Joyful"],
            pacing: "Steady",
            complexity: "Medium",
            world_building: "Rich",
            action_level: "Medium",
            violence_level: "None",
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
        overview: "As a collection of history's worst tyrants and criminal masterminds gather to plot a war to wipe out millions, one man must race against time to stop them. Discover the origins of the very first independent intelligence agency in The King's Man.",
        rich_metadata: {
            title: "The King's Man",
            year: "2021",
            match_percentage: 85,
            rating: 6.3,
            runtime: "131 min",
            director: "Matthew Vaughn",
            genres: ["Action", "Adventure", "Thriller", "War"],
            tags: ["Action", "Adventure", "Thriller", "War"],
            audience_type: "Adult",
            story_summary: "As a collection of history's worst tyrants and criminal masterminds gather to plot a war to wipe out millions, one man must race against time to stop them. Discover the origins of the very first independent intelligence agency in The King's Man.",
            why_recommended: "Recommended for its high-octane action sequences and stylized historical references.",
            themes: ["Duty", "Legacy", "Origin Stories", "Espionage"],
            moods: ["Exciting", "Stylized", "Adventurous"],
            pacing: "Fast-Paced",
            complexity: "Medium",
            world_building: "Rich",
            action_level: "High",
            violence_level: "High",
            language_severity: "Strong",
            adult: false,
            similar_movies: [
                { item_id: 1, title: "Spider-Man: No Way Home", poster_url: "https://image.tmdb.org/t/p/original/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg", score: 82 }
            ]
        }
    },
    {
        item_id: 10,
        title: "Interstellar",
        poster_url: "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/xJHokMbljvjEVAle2OvwIeEXpN.jpg",
        overview: "The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel and conquer the vast distances involved in an interstellar voyage.",
        rich_metadata: {
            title: "Interstellar",
            year: "2014",
            match_percentage: 97,
            rating: 8.7,
            runtime: "169 min",
            director: "Christopher Nolan",
            genres: ["Science Fiction", "Drama", "Adventure"],
            tags: ["Science Fiction", "Drama", "Adventure"],
            audience_type: "General",
            story_summary: "The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel and conquer the vast distances involved in an interstellar voyage.",
            why_recommended: "Recommended because it is a mind-bending sci-fi epic with profound emotional core and stellar score.",
            themes: ["Survival", "Time & Space", "Parental Love", "Human Destiny"],
            moods: ["Epic", "Thought-Provoking", "Atmospheric", "Emotional"],
            pacing: "Steady",
            complexity: "High",
            world_building: "Exceptional",
            action_level: "Medium",
            violence_level: "Mild",
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
        poster_url: "https://image.tmdb.org/t/p/w500/49WJfeN0moxb9IPfGn8AIqMGskD.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/rcA17r9GKqd8OHsSHLDOwlziR5N.jpg",
        overview: "When a young boy vanishes, a small town uncovers a mystery involving secret experiments, terrifying supernatural forces and one strange little girl.",
        rich_metadata: {
            title: "Stranger Things",
            type: "series",
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
        poster_url: "https://image.tmdb.org/t/p/w500/9PFonBhy4cQy7Jz20NpMygczOkv.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/iHSwvRVsRyxpX7FE7GbviaDvgGZ.jpg",
        overview: "A sleuthing, supernaturally infused mystery charting Wednesday Addams' years as a student at Nevermore Academy.",
        rich_metadata: {
            title: "Wednesday",
            type: "series",
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
        poster_url: "https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/jYEW5xZkZk2WTrdbMGAPFuBqbDc.jpg",
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
        poster_url: "https://image.tmdb.org/t/p/w500/eWd26co59HRmzZoxbWYvJ7wjTBm.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/58QT4cPJ2u2TqWZkterDq9q4yT5.jpg",
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
    },
    {
        item_id: 20,
        title: "Breaking Bad",
        poster_url: "https://image.tmdb.org/t/p/w500/ggFHVNu6YYI5L9pCfOacjizRGt.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/tsRy63Mu5cu8etL1X7ZLyf7UP1M.jpg",
        overview: "A high school chemistry teacher diagnosed with inoperable lung cancer turns to manufacturing and selling methamphetamine with a former student.",
        rich_metadata: {
            title: "Breaking Bad",
            type: "series",
            year: "2008",
            match_percentage: 98,
            rating: 9.5,
            runtime: "Series",
            director: "Vince Gilligan",
            genres: ["Drama", "Crime", "Thriller"],
            tags: ["Drama", "Crime", "Thriller"],
            audience_type: "Adult",
            story_summary: "A high school chemistry teacher diagnosed with inoperable lung cancer turns to manufacturing and selling methamphetamine with a former student.",
            why_recommended: "Recommended as one of the highest-rated television dramas of all time.",
            themes: ["Morality", "Family", "Greed", "Crime"],
            moods: ["Intense", "Dark", "Captivating"],
            pacing: "Steady",
            complexity: "High",
            world_building: "Rich",
            action_level: "Medium",
            violence_level: "High",
            language_severity: "Strong",
            adult: false,
            similar_movies: [
                { item_id: 2, title: "The Batman", poster_url: "https://image.tmdb.org/t/p/original/74xTEgt7R36Fpooo50r9T25onhq.jpg", score: 85 }
            ]
        }
    },
    {
        item_id: 21,
        title: "Game of Thrones",
        poster_url: "https://image.tmdb.org/t/p/w500/u3bB5t7wQk576Gmg23sGF75agbE.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/2OMB0ynKlyIenMJWI2Dy9IWT4c.jpg",
        overview: "Nine noble families fight for control over the lands of Westeros, while an ancient enemy returns after being dormant for thousands of years.",
        rich_metadata: {
            title: "Game of Thrones",
            type: "series",
            year: "2011",
            match_percentage: 97,
            rating: 9.2,
            runtime: "Series",
            director: "David Benioff",
            genres: ["Drama", "Fantasy", "Action"],
            tags: ["Drama", "Fantasy", "Action"],
            audience_type: "Adult",
            story_summary: "Nine noble families fight for control over the lands of Westeros, while an ancient enemy returns after being dormant for thousands of years.",
            why_recommended: "Recommended for its epic fantasy world-building and political intrigue.",
            themes: ["Power", "Betrayal", "Survival", "Destiny"],
            moods: ["Epic", "Intense", "Dark"],
            pacing: "Steady",
            complexity: "High",
            world_building: "Exceptional",
            action_level: "High",
            violence_level: "High",
            language_severity: "Strong",
            adult: false,
            similar_movies: [
                { item_id: 13, title: "Dune", poster_url: "https://placehold.co/400x600/111/333?text=Dune", score: 90 }
            ]
        }
    },
    {
        item_id: 22,
        title: "Succession",
        poster_url: "https://image.tmdb.org/t/p/w500/e2X8MdMmLMBUB4G1YAjHMFhP5zy.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/3VNbPATrczBDxbLn3A4YdJpjEK.jpg",
        overview: "The Roy family is known for controlling the biggest media and entertainment company in the world. However, their world changes when their father steps down.",
        rich_metadata: {
            title: "Succession",
            type: "series",
            year: "2018",
            match_percentage: 94,
            rating: 8.9,
            runtime: "Series",
            director: "Jesse Armstrong",
            genres: ["Drama", "Comedy"],
            tags: ["Drama", "Comedy"],
            audience_type: "Adult",
            story_summary: "The Roy family is known for controlling the biggest media and entertainment company in the world. However, their world changes when their father steps down.",
            why_recommended: "Recommended for its sharp satire, incredible writing, and intense family drama.",
            themes: ["Power", "Family", "Corporate Greed"],
            moods: ["Cynical", "Intense", "Witty"],
            pacing: "Steady",
            complexity: "High",
            world_building: "Rich",
            action_level: "Low",
            violence_level: "Low",
            language_severity: "Strong",
            adult: false,
            similar_movies: [
                { item_id: 14, title: "The Grand Budapest Hotel", poster_url: "https://placehold.co/400x600/111/333?text=Budapest+Hotel", score: 80 }
            ]
        }
    },
    {
        item_id: 23,
        title: "The Crown",
        poster_url: "https://image.tmdb.org/t/p/w500/8E2nCaTM9aHkKjHPYDiHPq9JzLF.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/9cJETuLMc6R0bTWRA5i7ctY9bxk.jpg",
        overview: "Follows the political rivalries and romance of Queen Elizabeth II's reign and the events that shaped the second half of the twentieth century.",
        rich_metadata: {
            title: "The Crown",
            type: "series",
            year: "2016",
            match_percentage: 93,
            rating: 8.6,
            runtime: "Series",
            director: "Peter Morgan",
            genres: ["Drama", "History"],
            tags: ["Drama", "History"],
            audience_type: "General",
            story_summary: "Follows the political rivalries and romance of Queen Elizabeth II's reign and the events that shaped the second half of the twentieth century.",
            why_recommended: "Recommended for its historical accuracy, gorgeous cinematography, and dramatic depth.",
            themes: ["Duty", "Family", "Tradition", "Politics"],
            moods: ["Atmospheric", "Emotional", "Serious"],
            pacing: "Steady",
            complexity: "Medium",
            world_building: "Rich",
            action_level: "Low",
            violence_level: "Low",
            language_severity: "Mild",
            adult: false,
            similar_movies: [
                { item_id: 14, title: "The Grand Budapest Hotel", poster_url: "https://placehold.co/400x600/111/333?text=Budapest+Hotel", score: 75 }
            ]
        }
    },
    {
        item_id: 24,
        title: "Friends",
        poster_url: "https://image.tmdb.org/t/p/w500/f496cm9enuEsZkSPzCwnTESEK5s.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/l0qVZIpXtIo7km9KLbQTxFEKpnc.jpg",
        overview: "Follows the personal and professional lives of six twenty to thirty-something-year-old friends living in Manhattan.",
        rich_metadata: {
            title: "Friends",
            type: "series",
            year: "1994",
            match_percentage: 95,
            rating: 8.9,
            runtime: "Series",
            director: "David Crane",
            genres: ["Comedy", "Romance"],
            tags: ["Comedy", "Romance"],
            audience_type: "Family/General",
            story_summary: "Follows the personal and professional lives of six twenty to thirty-something-year-old friends living in Manhattan.",
            why_recommended: "Recommended for its nostalgic, lighthearted humor and iconic cast dynamics.",
            themes: ["Friendship", "Love", "Careers"],
            moods: ["Lighthearted", "Uplifting", "Funny"],
            pacing: "Fast-Paced",
            complexity: "Low",
            world_building: "Standard",
            action_level: "Low",
            violence_level: "None",
            language_severity: "Mild",
            adult: false,
            similar_movies: [
                { item_id: 4, title: "Encanto", poster_url: "https://image.tmdb.org/t/p/original/4j0PNHkMr5ax3IA8tjtxcmPU3QT.jpg", score: 78 }
            ]
        }
    },
    {
        item_id: 25,
        title: "The Office",
        poster_url: "https://image.tmdb.org/t/p/w500/qWnJzyZhyy74gjpSjIXWmuk0ifX.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/4j0PNHkMr5ax3IA8tjtxcmPU3QT.jpg",
        overview: "A mockumentary on a group of typical office workers, where the workday consists of ego clashes, inappropriate behavior, and tedium.",
        rich_metadata: {
            title: "The Office",
            type: "series",
            year: "2005",
            match_percentage: 96,
            rating: 9.0,
            runtime: "Series",
            director: "Greg Daniels",
            genres: ["Comedy"],
            tags: ["Comedy"],
            audience_type: "Family/General",
            story_summary: "A mockumentary on a group of typical office workers, where the workday consists of ego clashes, inappropriate behavior, and tedium.",
            why_recommended: "Recommended for its hilarious cringe comedy and beloved character relationships.",
            themes: ["Workplace", "Friendship", "Humor"],
            moods: ["Lighthearted", "Witty", "Funny"],
            pacing: "Fast-Paced",
            complexity: "Low",
            world_building: "Standard",
            action_level: "Low",
            violence_level: "None",
            language_severity: "Mild",
            adult: false,
            similar_movies: [
                { item_id: 4, title: "Encanto", poster_url: "https://image.tmdb.org/t/p/original/4j0PNHkMr5ax3IA8tjtxcmPU3QT.jpg", score: 76 }
            ]
        }
    },
    {
        item_id: 26,
        title: "Sherlock",
        poster_url: "https://image.tmdb.org/t/p/w500/7WTsnHkbA0FaG6R9twfFde0I9hn.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/oNuQqRjTdJhxT9GDGJf6e12ohls.jpg",
        overview: "A modern update finds the famous sleuth and his doctor partner solving crime in 21st century London.",
        rich_metadata: {
            title: "Sherlock",
            type: "series",
            year: "2010",
            match_percentage: 95,
            rating: 9.1,
            runtime: "Series",
            director: "Steven Moffat",
            genres: ["Drama", "Mystery", "Crime"],
            tags: ["Drama", "Mystery", "Crime"],
            audience_type: "General",
            story_summary: "A modern update finds the famous sleuth and his doctor partner solving crime in 21st century London.",
            why_recommended: "Recommended for its brilliant modern deduction and thrilling crime mysteries.",
            themes: ["Intellect", "Friendship", "Justice"],
            moods: ["Captivating", "Suspenseful", "Witty"],
            pacing: "Fast-Paced",
            complexity: "High",
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
        item_id: 27,
        title: "Black Mirror",
        poster_url: "https://image.tmdb.org/t/p/w500/7PRddO7z7mcPi21nZTCMGShAyy1.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/4pP8BWFD8wRFaejrqfO0bpQZgaX.jpg",
        overview: "An anthology series exploring a twisted, high-tech multiverse where humanity's greatest innovations and darkest instincts collide.",
        rich_metadata: {
            title: "Black Mirror",
            type: "series",
            year: "2011",
            match_percentage: 94,
            rating: 8.7,
            runtime: "Series",
            director: "Charlie Brooker",
            genres: ["Drama", "Science Fiction", "Thriller"],
            tags: ["Drama", "Science Fiction", "Thriller"],
            audience_type: "Adult",
            story_summary: "An anthology series exploring a twisted, high-tech multiverse where humanity's greatest innovations and darkest instincts collide.",
            why_recommended: "Recommended for its thought-provoking dark sci-fi themes and technological warnings.",
            themes: ["Technology", "Society", "Human Nature"],
            moods: ["Dark", "Thought-Provoking", "Atmospheric"],
            pacing: "Steady",
            complexity: "High",
            world_building: "Rich",
            action_level: "Low",
            violence_level: "Moderate",
            language_severity: "Strong",
            adult: false,
            similar_movies: [
                { item_id: 10, title: "Interstellar", poster_url: "https://placehold.co/400x600/111/333?text=Interstellar", score: 85 }
            ]
        }
    },
    {
        item_id: 28,
        title: "Better Call Saul",
        poster_url: "https://image.tmdb.org/t/p/w500/fC2HDm5t0kR9dtbuXZCXTeegEGq.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/vWTmiSMuqIJAJoVEJM17yNFNOcn.jpg",
        overview: "The trials and tribulations of criminal lawyer Jimmy McGill in the years leading up to his fateful run-in with Walter White and Jesse Pinkman.",
        rich_metadata: {
            title: "Better Call Saul",
            type: "series",
            year: "2015",
            match_percentage: 96,
            rating: 8.9,
            runtime: "Series",
            director: "Vince Gilligan",
            genres: ["Drama", "Crime"],
            tags: ["Drama", "Crime"],
            audience_type: "Adult",
            story_summary: "The trials and tribulations of criminal lawyer Jimmy McGill in the years leading up to his fateful run-in with Walter White and Jesse Pinkman.",
            why_recommended: "Recommended for its masterful character study, dark humor, and high-tension legal drama.",
            themes: ["Morality", "Identity", "Family", "Crime"],
            moods: ["Intense", "Dark", "Captivating"],
            pacing: "Slow Burn",
            complexity: "High",
            world_building: "Rich",
            action_level: "Low",
            violence_level: "Moderate",
            language_severity: "Strong",
            adult: false,
            similar_movies: [
                { item_id: 20, title: "Breaking Bad", poster_url: "https://placehold.co/400x600/111/333?text=Breaking+Bad", score: 98 }
            ]
        }
    },
    {
        item_id: 29,
        title: "The Last of Us",
        poster_url: "https://image.tmdb.org/t/p/w500/uKvVjHNqB5VmOrdxqAt2F7J78ED.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/lFiCNvBXUwlNfGjRkG05V3l3EQX.jpg",
        overview: "Twenty years after modern civilization has been destroyed, Joel, a hardened survivor, is hired to smuggle Ellie, a 14-year-old girl, out of an oppressive quarantine zone.",
        rich_metadata: {
            title: "The Last of Us",
            type: "series",
            year: "2023",
            match_percentage: 95,
            rating: 8.8,
            runtime: "Series",
            director: "Craig Mazin",
            genres: ["Drama", "Action", "Adventure", "Science Fiction"],
            tags: ["Drama", "Action", "Adventure", "Science Fiction"],
            audience_type: "Adult",
            story_summary: "Twenty years after modern civilization has been destroyed, Joel, a hardened survivor, is hired to smuggle Ellie, a 14-year-old girl, out of an oppressive quarantine zone.",
            why_recommended: "Recommended for its emotional depth, post-apocalyptic survival theme, and gripping narrative.",
            themes: ["Survival", "Fatherhood", "Loss", "Hope"],
            moods: ["Emotional", "Intense", "Atmospheric"],
            pacing: "Steady",
            complexity: "Medium",
            world_building: "Exceptional",
            action_level: "High",
            violence_level: "High",
            language_severity: "Strong",
            adult: false,
            similar_movies: [
                { item_id: 11, title: "Stranger Things", poster_url: "https://placehold.co/400x600/111/333?text=Stranger+Things", score: 87 }
            ]
        }
    },
    {
        item_id: 30,
        title: "The Mandalorian",
        poster_url: "https://image.tmdb.org/t/p/w500/sWgBv7LV2PRoQgkxwlibdGXKz1S.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/9rT3l5n0bC3hd0CfzB9MxbIlHPB.jpg",
        overview: "The travels of a lone bounty hunter in the outer reaches of the galaxy, far from the authority of the New Republic.",
        rich_metadata: {
            title: "The Mandalorian",
            type: "series",
            year: "2019",
            match_percentage: 92,
            rating: 8.7,
            runtime: "Series",
            director: "Jon Favreau",
            genres: ["Action", "Adventure", "Science Fiction"],
            tags: ["Action", "Adventure", "Science Fiction"],
            audience_type: "Family Friendly",
            story_summary: "The travels of a lone bounty hunter in the outer reaches of the galaxy, far from the authority of the New Republic.",
            why_recommended: "Recommended for its exciting space adventure, rich world-building, and strong protector themes.",
            themes: ["Honor", "Duty", "Fatherhood", "Journey"],
            moods: ["Exciting", "Adventurous", "Uplifting"],
            pacing: "Fast-Paced",
            complexity: "Medium",
            world_building: "Rich",
            action_level: "High",
            violence_level: "Moderate",
            language_severity: "None",
            adult: false,
            similar_movies: [
                { item_id: 1, title: "Spider-Man: No Way Home", poster_url: "https://image.tmdb.org/t/p/original/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg", score: 85 }
            ]
        }
    },
    {
        item_id: 31,
        title: "Rick and Morty",
        poster_url: "https://image.tmdb.org/t/p/w500/gdIrmf2DdY5mgN6ycVP0XlzKzbE.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/9oclGnOBgQ68WBQlJDy2jIJBwGF.jpg",
        overview: "An animated series that follows the exploits of a super scientist and his inherently timid grandson.",
        rich_metadata: {
            title: "Rick and Morty",
            type: "series",
            year: "2013",
            match_percentage: 97,
            rating: 9.1,
            runtime: "Series",
            director: "Dan Harmon",
            genres: ["Animation", "Comedy", "Science Fiction"],
            tags: ["Animation", "Comedy", "Science Fiction"],
            audience_type: "Adult",
            story_summary: "An animated series that follows the exploits of a super scientist and his inherently timid grandson.",
            why_recommended: "Recommended for its brilliant sci-fi concepts, dark absurdist humor, and mind-bending plots.",
            themes: ["Existentialism", "Family", "Multiverse", "Scientific Ethics"],
            moods: ["Witty", "Absurd", "Mind-Bending"],
            pacing: "Fast-Paced",
            complexity: "High",
            world_building: "Rich",
            action_level: "High",
            violence_level: "High",
            language_severity: "Strong",
            adult: false,
            similar_movies: [
                { item_id: 10, title: "Interstellar", poster_url: "https://placehold.co/400x600/111/333?text=Interstellar", score: 80 }
            ]
        }
    },
    {
        item_id: 32,
        title: "The Boys",
        poster_url: "https://image.tmdb.org/t/p/w500/stTEycfG9928HYGEiL6SFhi3xc0.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/mY7SeH4HFFxW1hiI6cWuwCRKptN.jpg",
        overview: "A fun and irreverent take on what happens when superheroes—who are as popular as celebrities—abuse their superpowers.",
        rich_metadata: {
            title: "The Boys",
            type: "series",
            year: "2019",
            match_percentage: 93,
            rating: 8.7,
            runtime: "Series",
            director: "Eric Kripke",
            genres: ["Action", "Comedy", "Science Fiction"],
            tags: ["Action", "Comedy", "Science Fiction"],
            audience_type: "Adult",
            story_summary: "A fun and irreverent take on what happens when superheroes—who are as popular as celebrities—abuse their superpowers.",
            why_recommended: "Recommended for its dark superhero satire, high stakes, and intense action scenes.",
            themes: ["Corruption", "Power", "Celebrity", "Revenge"],
            moods: ["Gritty", "Satirical", "Violent", "Intense"],
            pacing: "Fast-Paced",
            complexity: "Medium",
            world_building: "Rich",
            action_level: "High",
            violence_level: "High",
            language_severity: "Strong",
            adult: false,
            similar_movies: [
                { item_id: 2, title: "The Batman", poster_url: "https://image.tmdb.org/t/p/original/74xTEgt7R36Fpooo50r9T25onhq.jpg", score: 85 }
            ]
        }
    },
    {
        item_id: 33,
        title: "The Sopranos",
        poster_url: "https://image.tmdb.org/t/p/w500/rTc7ZXZRouPNNje52SApEEpgzRR.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/3O6xEHREW8PmhHnBl7HA4XZJGE7.jpg",
        overview: "New Jersey mob boss Tony Soprano deals with personal and professional issues in his home and business life that affect his mental state.",
        rich_metadata: {
            title: "The Sopranos",
            type: "series",
            year: "1999",
            match_percentage: 98,
            rating: 9.2,
            runtime: "Series",
            director: "David Chase",
            genres: ["Drama", "Crime"],
            tags: ["Drama", "Crime"],
            audience_type: "Adult",
            story_summary: "New Jersey mob boss Tony Soprano deals with personal and professional issues in his home and business life that affect his mental state.",
            why_recommended: "Recommended as a groundbreaking crime drama exploring morality, family conflicts, and psychological struggles.",
            themes: ["Family", "Crime", "Guilt", "Identity"],
            moods: ["Intense", "Dark", "Captivating"],
            pacing: "Steady",
            complexity: "High",
            world_building: "Rich",
            action_level: "Medium",
            violence_level: "High",
            language_severity: "Strong",
            adult: false,
            similar_movies: [
                { item_id: 2, title: "The Batman", poster_url: "https://image.tmdb.org/t/p/original/74xTEgt7R36Fpooo50r9T25onhq.jpg", score: 84 }
            ]
        }
    },
    {
        item_id: 34,
        title: "The Wire",
        poster_url: "https://image.tmdb.org/t/p/w500/4vZ3FeGmkVYos4yqTDU2MQw1hNQ.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/w1280/tRV2ChMuJQZ0hOXX4GqwK0MRJRP.jpg",
        overview: "This series looks at the Baltimore drug scene through the eyes of both law enforcement and drug dealers.",
        rich_metadata: {
            title: "The Wire",
            type: "series",
            year: "2002",
            match_percentage: 97,
            rating: 9.3,
            runtime: "Series",
            director: "David Simon",
            genres: ["Drama", "Crime", "Thriller"],
            tags: ["Drama", "Crime", "Thriller"],
            audience_type: "Adult",
            story_summary: "This series looks at the Baltimore drug scene through the eyes of both law enforcement and drug dealers.",
            why_recommended: "Recommended for its unmatched realism, complex characters, and profound examination of urban institutions.",
            themes: ["Corruption", "Bureaucracy", "Class", "Justice"],
            moods: ["Gritty", "Dark", "Realistic"],
            pacing: "Slow Burn",
            complexity: "High",
            world_building: "Exceptional",
            action_level: "Medium",
            violence_level: "High",
            language_severity: "Strong",
            adult: false,
            similar_movies: [
                { item_id: 2, title: "The Batman", poster_url: "https://image.tmdb.org/t/p/original/74xTEgt7R36Fpooo50r9T25onhq.jpg", score: 86 }
            ]
        }
    },
    {
        item_id: 35,
        title: "Ted Lasso",
        poster_url: "https://placehold.co/400x600/111/333?text=Ted+Lasso",
        backdrop_url: "https://placehold.co/800x450/111/333?text=Ted+Lasso",
        overview: "American college football coach Ted Lasso heads to London to manage AFC Richmond, a struggling English Premier League football team.",
        rich_metadata: {
            title: "Ted Lasso",
            type: "series",
            year: "2020",
            match_percentage: 94,
            rating: 8.8,
            runtime: "Series",
            director: "Bill Lawrence",
            genres: ["Comedy", "Drama"],
            tags: ["Comedy", "Drama"],
            audience_type: "General",
            story_summary: "American college football coach Ted Lasso heads to London to manage AFC Richmond, a struggling English Premier League football team.",
            why_recommended: "Recommended for its infectious optimism, heartwarming characters, and uplifting humor.",
            themes: ["Leadership", "Optimism", "Friendship", "Empathy"],
            moods: ["Uplifting", "Joyful", "Emotional"],
            pacing: "Steady",
            complexity: "Medium",
            world_building: "Rich",
            action_level: "Low",
            violence_level: "None",
            language_severity: "Mild",
            adult: false,
            similar_movies: [
                { item_id: 4, title: "Encanto", poster_url: "https://image.tmdb.org/t/p/original/4j0PNHkMr5ax3IA8tjtxcmPU3QT.jpg", score: 85 }
            ]
        }
    },
    {
        item_id: 36,
        title: "Fargo",
        poster_url: "https://placehold.co/400x600/111/333?text=Fargo",
        backdrop_url: "https://placehold.co/800x450/111/333?text=Fargo",
        overview: "Various chronicles of deception, intrigue, and murder in and around frozen Minnesota. Yet all of these tales mysteriously lead back to one place.",
        rich_metadata: {
            title: "Fargo",
            type: "series",
            year: "2014",
            match_percentage: 95,
            rating: 8.9,
            runtime: "Series",
            director: "Noah Hawley",
            genres: ["Crime", "Drama", "Thriller"],
            tags: ["Crime", "Drama", "Thriller"],
            audience_type: "Adult",
            story_summary: "Various chronicles of deception, intrigue, and murder in and around frozen Minnesota. Yet all of these tales mysteriously lead back to one place.",
            why_recommended: "Recommended for its dark absurdity, quirky characters, and high-tension crime plots.",
            themes: ["Morality", "Chance", "Greed", "Deception"],
            moods: ["Dark", "Intense", "Absurd"],
            pacing: "Steady",
            complexity: "High",
            world_building: "Rich",
            action_level: "Medium",
            violence_level: "High",
            language_severity: "Strong",
            adult: false,
            similar_movies: [
                { item_id: 2, title: "The Batman", poster_url: "https://image.tmdb.org/t/p/original/74xTEgt7R36Fpooo50r9T25onhq.jpg", score: 83 }
            ]
        }
    },
    {
        item_id: 37,
        title: "Dark",
        poster_url: "https://placehold.co/400x600/111/333?text=Dark",
        backdrop_url: "https://placehold.co/800x450/111/333?text=Dark",
        overview: "A family saga with a supernatural twist, set in a German town, where the disappearance of two young children exposes the relationships among four families.",
        rich_metadata: {
            title: "Dark",
            type: "series",
            year: "2017",
            match_percentage: 96,
            rating: 8.7,
            runtime: "Series",
            director: "Baran bo Odar",
            genres: ["Drama", "Mystery", "Science Fiction", "Thriller"],
            tags: ["Drama", "Mystery", "Science Fiction", "Thriller"],
            audience_type: "Adult",
            story_summary: "A family saga with a supernatural twist, set in a German town, where the disappearance of two young children exposes the relationships among four families.",
            why_recommended: "Recommended for its complex time-travel mythology, deep existential themes, and dark atmospheric suspense.",
            themes: ["Time Travel", "Fate", "Determinism", "Family Secrets"],
            moods: ["Atmospheric", "Dark", "Mind-Bending"],
            pacing: "Steady",
            complexity: "Exceptional",
            world_building: "Exceptional",
            action_level: "Low",
            violence_level: "Moderate",
            language_severity: "Moderate",
            adult: false,
            similar_movies: [
                { item_id: 10, title: "Interstellar", poster_url: "https://placehold.co/400x600/111/333?text=Interstellar", score: 92 }
            ]
        }
    }
];

// ── Format Discovery & Modulo Heuristic ─────────────────────────────────
window.currentFormat = 'all';

window.getMovieType = function(movie) {
    if (!movie) return 'unknown';
    
    // Explicit type properties if present
    if (movie.type) {
        const t = movie.type.toLowerCase();
        if (t === 'movie') return 'movie';
        if (t === 'series' || t === 'show' || t === 'tv') return 'series';
    }
    if (movie.rich_metadata && movie.rich_metadata.type) {
        const t = movie.rich_metadata.type.toLowerCase();
        if (t === 'movie') return 'movie';
        if (t === 'series' || t === 'show' || t === 'tv') return 'series';
    }

    const titleLower = (movie.title || '').toLowerCase();
    
    // Explicit movie titles that might contain series keywords
    if (titleLower.includes('spider-man') || 
        titleLower.includes('batman') || 
        titleLower.includes('interstellar') || 
        titleLower.includes('dune') || 
        titleLower.includes('grand budapest') || 
        titleLower.includes('no exit') || 
        titleLower.includes('encanto') || 
        titleLower.includes('king\'s man') ||
        titleLower.includes('truman show') ||
        titleLower.includes('showtime') ||
        titleLower.includes('movie')) {
        return 'movie';
    }
    
    // Explicit known TV Series
    if (titleLower.includes('stranger things') || 
        titleLower.includes('wednesday') || 
        titleLower.includes('breaking bad') || 
        titleLower.includes('game of thrones') || 
        titleLower.includes('succession') || 
        titleLower.includes('the crown') ||
        titleLower.includes('friends') ||
        titleLower.includes('the office') ||
        titleLower.includes('sherlock') ||
        titleLower.includes('black mirror') ||
        titleLower.includes('better call saul') ||
        titleLower.includes('last of us') ||
        titleLower.includes('mandalorian') ||
        titleLower.includes('rick and morty') ||
        titleLower.includes('the boys') ||
        titleLower.includes('sopranos') ||
        titleLower.includes('the wire') ||
        titleLower.includes('ted lasso') ||
        titleLower.includes('fargo') ||
        titleLower.includes('dark')) {
        return 'series';
    }
    
    // Check runtime format for TV episodes/seasons
    const runtime = (movie.runtime || (movie.rich_metadata && movie.rich_metadata.runtime) || '').toLowerCase();
    if (runtime.includes('season') || runtime.includes('seasons') || runtime.includes('episodes') || runtime.includes('episode')) {
        return 'series';
    }
    
    // Check genres/tags
    const m = movie.rich_metadata || {};
    const genres = (m.genres || m.tags || movie.genres || []).map(g => g.toLowerCase());
    const seriesKeywords = ['tv series', 'tv show', 'series', 'mini-series', 'docuseries', 'web series', 'anime series', 'show', 'shows', 'reality', 'limited-series'];
    // Avoid classifying "TV Movie" as a series by ensuring "tv" matches do not include "tv movie"
    if (genres.some(g => seriesKeywords.includes(g) || g.includes('series') || g.includes('show') || (g.includes('tv') && !g.includes('tv movie')) || g.includes('episode'))) {
        return 'series';
    }
    
    // Default fallback is movie (movies.csv has only movies, no series)
    return 'movie';
};

window.isSeries = function(movie) {
    return window.getMovieType(movie) === 'series';
};
const isSeries = window.isSeries;

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
    localStorage.setItem('streamora_theme', themeName);
};

window.updateFormatTabs = function() {
    const tabs = ['all', 'movie', 'series'];
    tabs.forEach(t => {
        const tabEl = document.getElementById(`format-tab-${t}`);
        if (tabEl) {
            tabEl.classList.toggle('active', window.currentFormat === t);
        }
    });
    // Also update dynamic tabs in content area
    const dynamicContainer = document.querySelector('#content-rows .format-filter-container');
    if (dynamicContainer) {
        const buttons = dynamicContainer.querySelectorAll('.format-tab');
        buttons.forEach(btn => {
            const onclickStr = btn.getAttribute('onclick') || '';
            const isActive = onclickStr.includes(`'${window.currentFormat}'`) || onclickStr.includes(`"${window.currentFormat}"`);
            btn.classList.toggle('active', isActive);
        });
    }
};

window.setDiscoveryFormat = function(format) {
    window.currentFormat = format;
    localStorage.setItem('streamora_current_format', format);
    window.updateFormatTabs();
    
    // Refresh modal recommendations if open
    const modalOverlay = document.getElementById('movie-detail-modal');
    if (modalOverlay && modalOverlay.classList.contains('active') && window.currentModalMovieData) {
        renderModalData(window.currentModalMovieData, window.currentModalMovieId);
    }

    if (window.isDisplayingAIResults && window.lastAIRawResults) {
        renderResults(window.lastAIRawResults, window.lastAIRowTitle, window.lastAIIsHome);
    } else if (currentPage === 'home') {
        loadHomePage();
    } else if (currentPage === 'categories') {
        loadCategoriesTab();
    } else if (currentPage === 'search') {
        const input = document.getElementById('search-page-input');
        const query = input ? input.value.trim() : '';
        if (query) {
            executeSearchPageQuery(query);
        } else {
            renderSearchEmptyState();
        }
    } else if (currentPage === 'favorites' || currentPage === 'my-list') {
        renderFavoritesTab();
    }
};

// ── State ─────────────────────────────────────────────────────────────
window.ragCache = {};
window.isDisplayingAIResults = false;
window.lastAIRawResults = null;
window.lastAIRowTitle = '';
window.lastAIIsHome = false;

let globalMovies = [];
let myList = JSON.parse(localStorage.getItem('streamora_mylist') || '[]');
let currentPage = 'home';
let token = localStorage.getItem('streamora_jwt') || null;
let userProfile = JSON.parse(localStorage.getItem('streamora_profile')) || null;
let userId = userProfile ? userProfile.id : null;
let isGuest = false;
let isAuthModeLogin = true;

async function authFetch(url, options = {}) {
    options.headers = options.headers || {};
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    const res = await fetch(url, options);
    return res;
}

// ══════════════════════════════════════════════════════════════════════

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
        toggleText.textContent = 'Don\'t have an account?';
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
            
            const regRes = await fetch('/register', {
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
        
        const res = await fetch('/token', {
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
        const res = await authFetch('/me/watchlist');
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
            await authFetch('/me/watchlist', {
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
        await authFetch('/me/watchlist', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(myList)
        });
    } catch(e) {}
}

//  INIT
// ══════════════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', async () => {
    const savedTheme = localStorage.getItem('streamora_theme') || 'neon';
    applyTheme(savedTheme);
    
    const savedFormat = localStorage.getItem('streamora_current_format') || 'all';
    window.currentFormat = savedFormat;
    window.updateFormatTabs();
    
    // Auth Check
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
    }
});

function initApp() {
    // Bind all logo click events for robust Home navigation
    document.querySelectorAll('.sidebar__logo, .topbar__logo, .drawer__logo, .site-footer__brand').forEach(logo => {
        logo.style.cursor = 'pointer';
        logo.addEventListener('click', (e) => {
            e.preventDefault();
            navigateTo('home');
            if (typeof closeDrawer === 'function') closeDrawer();
        });
    });

    // Bind Topbar Search input
    const topbarSearchInput = document.getElementById('topbar-search-input');
    if (topbarSearchInput) {
        topbarSearchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const query = topbarSearchInput.value.trim();
                if (query) {
                    navigateTo('search');
                    setTimeout(() => {
                        const searchPageInput = document.getElementById('search-page-input');
                        if (searchPageInput) {
                            searchPageInput.value = query;
                        }
                        executeSearchPageQuery(query);
                    }, 50);
                }
            }
        });
    }

    // Swipe-down gestures on mobile details modal
    let touchStartY = 0;
    let touchEndY = 0;
    const cinematicModal = document.querySelector('.cinematic-modal');
    if (cinematicModal) {
        cinematicModal.addEventListener('touchstart', (e) => {
            if (e.touches.length === 1) {
                touchStartY = e.touches[0].clientY;
            }
        }, { passive: true });

        cinematicModal.addEventListener('touchmove', (e) => {
            if (e.touches.length === 1) {
                touchEndY = e.touches[0].clientY;
            }
        }, { passive: true });

        cinematicModal.addEventListener('touchend', () => {
            const diffY = touchEndY - touchStartY;
            if (cinematicModal.scrollTop <= 0 && diffY > 80) {
                const modalOverlay = document.getElementById('movie-detail-modal');
                if (modalOverlay) {
                    modalOverlay.classList.remove('active');
                    document.body.style.overflow = '';
                }
            }
            touchStartY = 0;
            touchEndY = 0;
        }, { passive: true });
    }
    // Bind format selectors dynamically to bypass inline CSP blocks
    const allTab = document.getElementById('format-tab-all');
    const movieTab = document.getElementById('format-tab-movie');
    const seriesTab = document.getElementById('format-tab-series');
    if (allTab) {
        allTab.addEventListener('click', (e) => {
            e.preventDefault();
            window.setDiscoveryFormat('all');
        });
    }
    if (movieTab) {
        movieTab.addEventListener('click', (e) => {
            e.preventDefault();
            window.setDiscoveryFormat('movie');
        });
    }
    if (seriesTab) {
        seriesTab.addEventListener('click', (e) => {
            e.preventDefault();
            window.setDiscoveryFormat('series');
        });
    }
    
    // Also use event delegation for any dynamically created buttons with class 'format-tab'
    document.addEventListener('click', (e) => {
        const targetTab = e.target.closest('.format-tab');
        if (targetTab) {
            e.preventDefault();
            const id = targetTab.id;
            if (id === 'format-tab-all') {
                window.setDiscoveryFormat('all');
            } else if (id === 'format-tab-movie') {
                window.setDiscoveryFormat('movie');
            } else if (id === 'format-tab-series') {
                window.setDiscoveryFormat('series');
            } else {
                const onclickStr = targetTab.getAttribute('onclick') || '';
                const match = onclickStr.match(/setDiscoveryFormat\(['"](all|movie|series)['"]\)/);
                if (match && match[1]) {
                    window.setDiscoveryFormat(match[1]);
                }
            }
        }
    });

    navigateTo('home');
}

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
            const results = await r.json();
            if (results.length === 0) {
                searchResults.innerHTML = `<div style="text-align: center; padding: 20px; color: var(--text-muted);">No titles found matching "${q}"</div>`;
                return;
            }
            searchResults.innerHTML = results.map(m => {
                const genresText = m.genres.join(', ');
                const typeText = m.content_type === 'series' ? 'TV Series' : m.content_type.charAt(0).toUpperCase() + m.content_type.slice(1);
                return `
                    <div class="search-hit" onclick="openModal(${m.item_id}); closeSearch();" style="display: flex; align-items: center; gap: 16px; padding: 10px 16px;">
                        <img src="${m.poster_url}" alt="${m.title}" style="width: 45px; height: 65px; object-fit: cover; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1);">
                        <div style="flex: 1;">
                            <div class="search-hit__title" style="font-size: 1.05rem; margin-bottom: 2px;">${m.title}</div>
                            <div class="search-hit__sub" style="font-size: 0.8rem; color: var(--text-muted); display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                                <span style="background: rgba(0,240,255,0.15); color: var(--streamora-cyan); padding: 1px 6px; border-radius: 4px; font-weight: 600; font-size: 0.7rem; text-transform: uppercase;">${typeText}</span>
                                <span>${genresText}</span>
                                <span>•</span>
                                <span style="color: #ffb800; font-weight: 500;">★ ${m.rating.toFixed(1)}</span>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        } catch (e) { /* network error */ }
    }, 250);
});

searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        const firstHit = searchResults.querySelector('.search-hit');
        if (firstHit) {
            firstHit.click();
        }
    }
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

function getMovieCast(title) {
    const titleLower = (title || '').toLowerCase();
    if (titleLower.includes('spider-man')) return ['Tom Holland', 'Zendaya', 'Benedict Cumberbatch', 'Jacob Batalon', 'Jon Favreau'];
    if (titleLower.includes('batman')) return ['Robert Pattinson', 'Zoë Kravitz', 'Paul Dano', 'Jeffrey Wright', 'John Turturro'];
    if (titleLower.includes('no exit')) return ['Havana Rose Liu', 'Danny Ramirez', 'David Rysdahl', 'Mila Harris', 'Dennis Haysbert'];
    if (titleLower.includes('encanto')) return ['Stephanie Beatriz', 'María Cecilia Botero', 'John Leguizamo', 'Mauro Castillo', 'Jessica Darrow'];
    if (titleLower.includes('king\'s man')) return ['Ralph Fiennes', 'Gemma Arterton', 'Rhys Ifans', 'Matthew Goode', 'Tom Hollander'];
    if (titleLower.includes('interstellar')) return ['Matthew McConaughey', 'Anne Hathaway', 'Jessica Chastain', 'Bill Irwin', 'Ellen Burstyn'];
    if (titleLower.includes('stranger things')) return ['Winona Ryder', 'David Harbour', 'Millie Bobby Brown', 'Finn Wolfhard', 'Gaten Matarazzo'];
    if (titleLower.includes('wednesday')) return ['Jenna Ortega', 'Gwendoline Christie', 'Riki Lindhome', 'Jamie McShane', 'Hunter Doohan'];
    if (titleLower.includes('dune')) return ['Timothée Chalamet', 'Rebecca Ferguson', 'Oscar Isaac', 'Josh Brolin', 'Stellan Skarsgård'];
    if (titleLower.includes('budapest')) return ['Ralph Fiennes', 'F. Murray Abraham', 'Mathieu Amalric', 'Adrien Brody', 'Willem Dafoe'];
    if (titleLower.includes('scream')) return ['Neve Campbell', 'Courteney Cox', 'David Arquette', 'Melissa Barrera', 'Jenna Ortega'];
    if (titleLower.includes('eternals')) return ['Gemma Chan', 'Richard Madden', 'Kumail Nanjiani', 'Lia McHugh', 'Brian Tyree Henry'];
    if (titleLower.includes('uncharted')) return ['Tom Holland', 'Mark Wahlberg', 'Sophia Ali', 'Tati Gabrielle', 'Antonio Banderas'];
    if (titleLower.includes('red notice')) return ['Dwayne Johnson', 'Ryan Reynolds', 'Gal Gadot', 'Ritu Arya', 'Chris Diamantopoulos'];
    if (titleLower.includes('matrix')) return ['Keanu Reeves', 'Carrie-Anne Moss', 'Yahya Abdul-Mateen II', 'Jessica Henwick', 'Jonathan Groff'];
    if (titleLower.includes('shang-chi')) return ['Simu Liu', 'Awkwafina', 'Meng\'er Zhang', 'Fala Chen', 'Florian Munteanu'];
    if (titleLower.includes('venom')) return ['Tom Hardy', 'Michelle Williams', 'Naomie Harris', 'Reid Scott', 'Stephen Graham'];
    if (titleLower.includes('sing 2')) return ['Matthew McConaughey', 'Reese Witherspoon', 'Scarlett Johansson', 'Taron Egerton', 'Bobby Cannavale'];
    return null;
}


function getMovieLanguages(movie) {
    const m = movie.rich_metadata || {};
    if (m.languages) return m.languages;
    const titleLower = (movie.title || '').toLowerCase();
    if (titleLower.includes('encanto')) return 'English, Spanish';
    if (titleLower.includes('korean') || titleLower.includes('k-drama')) return 'Korean (English Subtitles)';
    return 'English, Spanish, French';
}

function createBotRecommendationHTML(movie) {
    const m = movie.rich_metadata || {};
    const title = movie.title || 'Unknown';
    const poster = movie.poster_url || placeholder(title);
    const score = m.match_percentage || randScore();
    const rating = m.rating || '8.0';
    const genres = (m.genres || m.tags || ['Drama']).slice(0, 3).join(', ');
    const runtime = m.runtime || '120 min';
    const reason = m.why_recommended || 'Highly matched to your interest and viewing behavior.';
    
    return `
        <div class="chat-rec-card" onclick="openModal(${movie.item_id})" style="display: flex; gap: 12px; background: rgba(255,255,255,0.05); border: 1px solid var(--glass-border); border-radius: var(--r-md); padding: 10px; margin-top: 10px; cursor: pointer; transition: transform var(--t-fast); align-items: flex-start;">
            <img src="${poster}" alt="${title}" style="width: 70px; aspect-ratio: 2/3; object-fit: cover; border-radius: var(--r-sm); border: 1px solid rgba(255,255,255,0.1); flex-shrink: 0;">
            <div style="flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px;">
                <div style="font-weight: 700; color: white; font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: left;">${title}</div>
                <div style="display: flex; gap: 8px; align-items: center; font-size: 0.75rem; flex-wrap: wrap;">
                    <span style="color: var(--match-green); font-weight: 700;">★ ${score}% Match</span>
                    <span style="color: #f5c518; font-weight: 700;">IMDb ${rating}</span>
                    <span style="color: var(--text-muted);">${runtime}</span>
                </div>
                <div style="font-size: 0.75rem; color: var(--streamora-cyan); text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${genres}</div>
                <div style="font-size: 0.75rem; color: var(--text-secondary); line-height: 1.3; margin-top: 2px; text-align: left;">
                    <strong>Reason:</strong> ${reason}
                </div>
            </div>
        </div>
    `;
}

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
    const currentUserId = (userIdInput && parseInt(userIdInput.value)) || userId || 32;

    addMsg(query, true);
    chatInput.value = '';
    acDropdown.style.display = 'none';

    showSkeletonRows();

    try {
        const resp = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUserId, query })
        });
        const data = await resp.json();

        if (data.intent === 'explanation') {
            addMsg(data.response, false);
            contentRows.innerHTML = '';
            return;
        }

        let movies = Array.isArray(data.response) ? data.response : (data.response && data.response.value);
        if (movies && movies.length > 0) {
            let rowTitle = 'Streamora Recommendations';
            if (data.intent === 'trending') rowTitle = 'Trending Now';
            else if (data.intent === 'similar_movies') rowTitle = 'Because You Searched';
            else if (data.intent === 'genre_search') rowTitle = 'Genre Discovery';

            renderResults(movies, rowTitle);
            
            let responseHTML = `Found ${movies.length} titles for you:<br>`;
            movies.slice(0, 3).forEach(m => {
                responseHTML += createBotRecommendationHTML(m);
            });
            addMsg(responseHTML, false);
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
    window.isDisplayingAIResults = false; 

    document.querySelectorAll('.sidebar__link').forEach(l => {
        l.classList.toggle('active', l.dataset.page === page);
    });
    document.querySelectorAll('.bottom-nav__item').forEach(l => {
        l.classList.toggle('active', l.dataset.page === page);
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Show persistent format filters ONLY on Home or Categories pages
    const homeFilter = document.getElementById('home-filter-section');
    if (homeFilter) {
        homeFilter.style.display = (page === 'home' || page === 'categories') ? 'block' : 'none';
        if (typeof window.updateFormatTabs === 'function') {
            window.updateFormatTabs();
        }
    }

    switch (page) {
        case 'home':
            loadHomePage();
            break;
        case 'categories':
            loadCategoriesTab();
            break;
        case 'search':
            loadSearchPage();
            break;
        case 'favorites':
        case 'my-list':
            renderFavoritesTab();
            break;
        case 'downloads':
            renderDownloadsTab();
            break;
        case 'account':
            renderAccountTab();
            break;
        case 'settings':
            renderSettingsTab();
            break;
        case 'assistant':
        case 'ai-assistant':
            if (aiPanel) aiPanel.classList.add('open');
            navigateTo('home');
            break;
    }
}

// ── Account & Settings Tab Pages ─────────────────────────────────────
function renderAccountTab() {
    heroSection.innerHTML = '';
    heroSection.style.display = 'none';
    
    const userEmail = localStorage.getItem('streamora_user_email') || 'guest@streamora.ai';
    const userName = localStorage.getItem('streamora_user_name') || 'Guest Explorer';
    const userAvatar = `https://ui-avatars.com/api/?name=${encodeURIComponent(userName)}&background=06B6D4&color=000&size=128&bold=true`;
    
    contentRows.innerHTML = `
        <div class="row-section" style="padding-top:80px; max-width:800px; margin:0 auto; padding-left: 24px; padding-right: 24px; color: white;">
            <h1 class="row-section__title" style="font-size:2.2rem;margin-bottom:12px; color: white;">👤 Account</h1>
            <p style="color:var(--text-muted);font-size:0.95rem;margin-bottom:32px;">Manage your membership, profile, and active devices.</p>
            
            <!-- Premium Profile Card -->
            <div style="background:rgba(255,255,255,0.03); border:1px solid var(--glass-border); border-radius:var(--r-lg); padding:30px; display:flex; gap:24px; align-items:center; margin-bottom:30px; backdrop-filter: blur(20px); flex-wrap: wrap;">
                <img src="${userAvatar}" alt="User Avatar" style="width: 80px; height: 80px; border-radius: 50%; border: 3px solid var(--streamora-cyan); box-shadow: 0 0 15px rgba(6, 182, 212, 0.4);">
                <div style="flex-grow: 1;">
                    <h2 style="font-size: 1.5rem; font-weight: 700; margin-bottom: 4px; color: white;">${userName}</h2>
                    <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 8px;">${userEmail}</p>
                    <span style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: var(--streamora-cyan); background: rgba(6, 182, 212, 0.15); border: 1px solid rgba(6, 182, 212, 0.3); padding: 4px 10px; border-radius: 4px;">Premium Member</span>
                </div>
                <div style="display:flex; flex-direction:column; gap:8px;">
                    <button onclick="editProfilePrompt()" style="background: rgba(255,255,255,0.08); border: 1px solid var(--glass-border); padding: 8px 16px; border-radius: var(--r-md); color: white; cursor: pointer; font-size: 0.85rem; font-weight: 600; transition: all var(--t-fast);" onmouseover="this.style.background='rgba(255,255,255,0.15)'" onmouseout="this.style.background='rgba(255,255,255,0.08)'">Edit Profile</button>
                </div>
            </div>

            <!-- Membership & Devices Section -->
            <div style="background:rgba(255,255,255,0.02); border:1px solid var(--glass-border); border-radius:var(--r-lg); padding:30px; display:flex; flex-direction:column; gap:20px; margin-bottom:30px; backdrop-filter: blur(20px);">
                <h3 style="font-size: 1.2rem; font-weight: 700; color: white; margin-bottom: 5px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 10px;">Membership & Devices</h3>
                <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:15px; flex-wrap:wrap; gap:10px;">
                    <span style="color:var(--text-muted); font-weight:500;">Membership Tier</span>
                    <span style="color:white; font-weight:700;">Streamora Cinematic Premium (4K UHD)</span>
                </div>
                <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:15px; flex-wrap:wrap; gap:10px;">
                    <span style="color:var(--text-muted); font-weight:500;">Next Renewal</span>
                    <span style="color:white; font-weight:700;">July 24, 2026 ($14.99/mo)</span>
                </div>
                <div style="display:flex; flex-direction:column; gap:12px;">
                    <span style="color:var(--text-muted); font-weight:500; margin-bottom: 4px;">Active Streaming Devices</span>
                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px;">
                        <div style="background: rgba(255,255,255,0.04); border: 1px solid var(--glass-border); padding: 12px; border-radius: var(--r-md); display:flex; gap:12px; align-items:center;">
                            <span style="font-size: 1.5rem;">📱</span>
                            <div>
                                <div style="font-weight:700; font-size: 0.9rem;">iPhone 15 Pro</div>
                                <div style="font-size: 0.75rem; color: var(--streamora-cyan); font-weight:600;">Active Now (Streaming)</div>
                            </div>
                        </div>
                        <div style="background: rgba(255,255,255,0.04); border: 1px solid var(--glass-border); padding: 12px; border-radius: var(--r-md); display:flex; gap:12px; align-items:center;">
                            <span style="font-size: 1.5rem;">💻</span>
                            <div>
                                <div style="font-weight:700; font-size: 0.9rem;">MacBook Pro</div>
                                <div style="font-size: 0.75rem; color: var(--text-muted);">Active 2 hours ago</div>
                            </div>
                        </div>
                        <div style="background: rgba(255,255,255,0.04); border: 1px solid var(--glass-border); padding: 12px; border-radius: var(--r-md); display:flex; gap:12px; align-items:center; opacity: 0.6;">
                            <span style="font-size: 1.5rem;">📺</span>
                            <div>
                                <div style="font-weight:700; font-size: 0.9rem;">Sony Bravia OLED</div>
                                <div style="font-size: 0.75rem; color: var(--text-muted);">Offline</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Quick Links -->
            <div style="background:rgba(255,255,255,0.02); border:1px solid var(--glass-border); border-radius:var(--r-lg); padding:30px; display:flex; flex-direction:column; gap:16px; backdrop-filter: blur(20px);">
                <h3 style="font-size: 1.2rem; font-weight: 700; color: white; margin-bottom: 5px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 10px;">Quick Discover Links</h3>
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                    <div onclick="navigateTo('favorites')" style="background: rgba(255,255,255,0.04); border: 1px solid var(--glass-border); padding: 16px; border-radius: var(--r-md); cursor: pointer; text-align: center; transition: all var(--t-fast);" onmouseover="this.style.background='rgba(255,255,255,0.08)'; this.style.borderColor='var(--streamora-cyan)';" onmouseout="this.style.background='rgba(255,255,255,0.04)'; this.style.borderColor='var(--glass-border)';">
                        <span style="font-size: 1.8rem; display:block; margin-bottom: 8px;">❤️</span>
                        <span style="font-weight:600; font-size: 0.95rem;">Watchlist & Favorites</span>
                    </div>
                    <div onclick="navigateTo('downloads')" style="background: rgba(255,255,255,0.04); border: 1px solid var(--glass-border); padding: 16px; border-radius: var(--r-md); cursor: pointer; text-align: center; transition: all var(--t-fast);" onmouseover="this.style.background='rgba(255,255,255,0.08)'; this.style.borderColor='var(--streamora-cyan)';" onmouseout="this.style.background='rgba(255,255,255,0.04)'; this.style.borderColor='var(--glass-border)';">
                        <span style="font-size: 1.8rem; display:block; margin-bottom: 8px;">📥</span>
                        <span style="font-weight:600; font-size: 0.95rem;">Downloads & Offline Hub</span>
                    </div>
                    <div onclick="navigateTo('settings')" style="background: rgba(255,255,255,0.04); border: 1px solid var(--glass-border); padding: 16px; border-radius: var(--r-md); cursor: pointer; text-align: center; transition: all var(--t-fast);" onmouseover="this.style.background='rgba(255,255,255,0.08)'; this.style.borderColor='var(--streamora-cyan)';" onmouseout="this.style.background='rgba(255,255,255,0.04)'; this.style.borderColor='var(--glass-border)';">
                        <span style="font-size: 1.8rem; display:block; margin-bottom: 8px;">⚙️</span>
                        <span style="font-weight:600; font-size: 0.95rem;">Application Settings</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

window.editProfilePrompt = function() {
    const currentName = localStorage.getItem('streamora_user_name') || 'Guest Explorer';
    const currentEmail = localStorage.getItem('streamora_user_email') || 'guest@streamora.ai';
    const newName = prompt("Enter new profile name:", currentName);
    if (newName === null) return;
    const newEmail = prompt("Enter new email address:", currentEmail);
    if (newEmail === null) return;
    
    localStorage.setItem('streamora_user_name', newName.trim() || 'Guest Explorer');
    localStorage.setItem('streamora_user_email', newEmail.trim() || 'guest@streamora.ai');
    renderAccountTab();
};

function renderSettingsTab() {
    heroSection.innerHTML = '';
    heroSection.style.display = 'none';
    
    const autoplay = localStorage.getItem('streamora_autoplay') !== 'false';
    const quality = localStorage.getItem('streamora_quality') || 'auto';
    const motion = localStorage.getItem('streamora_reduced_motion') === 'true';
    const theme = localStorage.getItem('streamora_theme') || 'neon';
    const language = localStorage.getItem('streamora_language') || 'en';
    
    const notifNew = localStorage.getItem('streamora_notif_new') !== 'false';
    const notifRec = localStorage.getItem('streamora_notif_rec') !== 'false';
    const notifDl = localStorage.getItem('streamora_notif_dl') !== 'false';
    
    contentRows.innerHTML = `
        <div class="row-section" style="padding-top:80px; max-width:800px; margin:0 auto; padding-left: 24px; padding-right: 24px;">
            <h1 class="row-section__title" style="font-size:2.2rem;margin-bottom:12px; color: white;">⚙️ Settings</h1>
            <p style="color:var(--text-muted);font-size:0.95rem;margin-bottom:32px;">Configure streaming quality, glass themes, accessibility, and notifications.</p>
            
            <div style="background:rgba(255,255,255,0.03); border:1px solid var(--glass-border); border-radius:var(--r-lg); padding:30px; display:flex; flex-direction:column; gap:24px; backdrop-filter: blur(20px);">
                
                <!-- Playback & Motion -->
                <div>
                    <h3 style="color:white; margin-bottom:12px; font-size:1.1rem; font-weight: 700;">Playback & Accessibility</h3>
                    <label style="display: flex; align-items: center; gap: 12px; cursor: pointer; margin-bottom: 12px; color:var(--text-secondary);">
                        <input type="checkbox" id="page-settings-autoplay" ${autoplay ? 'checked' : ''} style="width: 20px; height: 20px; cursor:pointer;" onchange="savePageSettings()">
                        <span>Autoplay Cinematic Trailers</span>
                    </label>
                    <label style="display: flex; align-items: center; gap: 12px; cursor: pointer; color:var(--text-secondary);">
                        <input type="checkbox" id="page-settings-motion" ${motion ? 'checked' : ''} style="width: 20px; height: 20px; cursor:pointer;" onchange="savePageSettings()">
                        <span>Reduced Motion (Disable 3D tilt & scaling)</span>
                    </label>
                </div>
                
                <hr style="border:0; border-top:1px solid rgba(255,255,255,0.08); margin:0;">
                
                <!-- Language selection -->
                <div>
                    <h3 style="color:white; margin-bottom:12px; font-size:1.1rem; font-weight: 700;">Interface Language</h3>
                    <select id="page-settings-language" onchange="savePageSettings()" style="width: 100%; max-width: 300px; padding: 10px 14px; border-radius: var(--r-md); background: rgba(0,0,0,0.4); border: 1px solid var(--glass-border); color: white; font-size: 0.95rem; outline: none; cursor: pointer;">
                        <option value="en" ${language === 'en' ? 'selected' : ''}>English</option>
                        <option value="es" ${language === 'es' ? 'selected' : ''}>Español (Spanish)</option>
                        <option value="fr" ${language === 'fr' ? 'selected' : ''}>Français (French)</option>
                        <option value="ja" ${language === 'ja' ? 'selected' : ''}>日本語 (Japanese)</option>
                        <option value="hi" ${language === 'hi' ? 'selected' : ''}>हिन्दी (Hindi)</option>
                    </select>
                </div>
                
                <hr style="border:0; border-top:1px solid rgba(255,255,255,0.08); margin:0;">
                
                <!-- Streaming Quality -->
                <div>
                    <h3 style="color:white; margin-bottom:12px; font-size:1.1rem; font-weight: 700;">Streaming Quality</h3>
                    <select id="page-settings-quality" onchange="savePageSettings()" style="width: 100%; max-width: 300px; padding: 10px 14px; border-radius: var(--r-md); background: rgba(0,0,0,0.4); border: 1px solid var(--glass-border); color: white; font-size: 0.95rem; outline: none; cursor: pointer;">
                        <option value="auto" ${quality === 'auto' ? 'selected' : ''}>Auto (Recommended)</option>
                        <option value="4k" ${quality === '4k' ? 'selected' : ''}>4K UHD (Highest Quality)</option>
                        <option value="1080p" ${quality === '1080p' ? 'selected' : ''}>1080p Full HD</option>
                        <option value="data" ${quality === 'data' ? 'selected' : ''}>Data Saver (SD)</option>
                    </select>
                </div>
                
                <hr style="border:0; border-top:1px solid rgba(255,255,255,0.08); margin:0;">
                
                <!-- Notifications -->
                <div>
                    <h3 style="color:white; margin-bottom:12px; font-size:1.1rem; font-weight: 700;">Notification Preferences</h3>
                    <label style="display: flex; align-items: center; gap: 12px; cursor: pointer; margin-bottom: 12px; color:var(--text-secondary);">
                        <input type="checkbox" id="page-settings-notif-new" ${notifNew ? 'checked' : ''} style="width: 20px; height: 20px; cursor:pointer;" onchange="savePageSettings()">
                        <span>Notify on New Content Releases</span>
                    </label>
                    <label style="display: flex; align-items: center; gap: 12px; cursor: pointer; margin-bottom: 12px; color:var(--text-secondary);">
                        <input type="checkbox" id="page-settings-notif-rec" ${notifRec ? 'checked' : ''} style="width: 20px; height: 20px; cursor:pointer;" onchange="savePageSettings()">
                        <span>Receive Weekly Personal Recommendations</span>
                    </label>
                    <label style="display: flex; align-items: center; gap: 12px; cursor: pointer; color:var(--text-secondary);">
                        <input type="checkbox" id="page-settings-notif-dl" ${notifDl ? 'checked' : ''} style="width: 20px; height: 20px; cursor:pointer;" onchange="savePageSettings()">
                        <span>Notify When Offline Download Completes</span>
                    </label>
                </div>
                
                <hr style="border:0; border-top:1px solid rgba(255,255,255,0.08); margin:0;">
                
                <!-- Theme Preferences -->
                <div>
                    <h3 style="color:white; margin-bottom:12px; font-size:1.1rem; font-weight: 700;">Theme Preferences</h3>
                    <div style="display:flex; flex-direction:column; gap:12px;">
                        <label style="display: flex; align-items: center; gap: 12px; cursor: pointer; color:var(--text-secondary);">
                            <input type="radio" name="page-theme-choice" value="neon" ${theme === 'neon' ? 'checked' : ''} style="width: 20px; height: 20px; cursor:pointer;" onchange="savePageTheme('neon')">
                            <span>Streamora Neon (Default Cyberpunk)</span>
                        </label>
                        <label style="display: flex; align-items: center; gap: 12px; cursor: pointer; color:var(--text-secondary);">
                            <input type="radio" name="page-theme-choice" value="slate" ${theme === 'slate' ? 'checked' : ''} style="width: 20px; height: 20px; cursor:pointer;" onchange="savePageTheme('slate')">
                            <span>Midnight Slate (Elegant Dark)</span>
                        </label>
                        <label style="display: flex; align-items: center; gap: 12px; cursor: pointer; color:var(--text-secondary);">
                            <input type="radio" name="page-theme-choice" value="oled" ${theme === 'oled' ? 'checked' : ''} style="width: 20px; height: 20px; cursor:pointer;" onchange="savePageTheme('oled')">
                            <span>OLED Black (Deep Contrast)</span>
                        </label>
                    </div>
                </div>
                
                <hr style="border:0; border-top:1px solid rgba(255,255,255,0.08); margin:0;">
                
                <!-- Clear Cache / Diagnostics -->
                <div>
                    <h3 style="color:white; margin-bottom:12px; font-size:1.1rem; font-weight: 700;">Storage & Cache</h3>
                    <button onclick="clearLocalStorageCache()" style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); padding: 10px 20px; border-radius: var(--r-md); color: #F87171; cursor: pointer; font-size: 0.95rem; font-weight: 600; transition: all var(--t-fast);" onmouseover="this.style.background='rgba(239, 68, 68, 0.25)'" onmouseout="this.style.background='rgba(239, 68, 68, 0.15)'">Clear Application Caches & Offline Data</button>
                    <p style="color:var(--text-muted); font-size:0.8rem; margin-top:8px;">This will remove all downloaded media, clear your local favorites lists, search history, and restore settings to their factory defaults.</p>
                </div>
                
            </div>
        </div>
    `;
}

window.clearLocalStorageCache = function() {
    if (confirm("Are you sure you want to clear all cache? This deletes downloads, favorites, history, and settings.")) {
        localStorage.clear();
        alert("Cache cleared successfully! Re-initializing...");
        window.location.reload();
    }
};

window.savePageSettings = function() {
    const autoplay = document.getElementById('page-settings-autoplay').checked;
    const motion = document.getElementById('page-settings-motion').checked;
    const quality = document.getElementById('page-settings-quality').value;
    const language = document.getElementById('page-settings-language').value;
    
    const notifNew = document.getElementById('page-settings-notif-new').checked;
    const notifRec = document.getElementById('page-settings-notif-rec').checked;
    const notifDl = document.getElementById('page-settings-notif-dl').checked;
    
    localStorage.setItem('streamora_autoplay', autoplay);
    localStorage.setItem('streamora_reduced_motion', motion);
    localStorage.setItem('streamora_quality', quality);
    localStorage.setItem('streamora_language', language);
    
    localStorage.setItem('streamora_notif_new', notifNew);
    localStorage.setItem('streamora_notif_rec', notifRec);
    localStorage.setItem('streamora_notif_dl', notifDl);
    
    if (motion) {
        document.body.classList.add('reduced-motion');
    } else {
        document.body.classList.remove('reduced-motion');
    }
};

window.savePageTheme = function(theme) {
    applyTheme(theme);
};

// ── Downloads Tab ────────────────────────────────────────────────────
window.simulateDownload = function(id) {
    const movie = globalMovies.find(m => parseInt(m.item_id) === parseInt(id)) || 
                  FALLBACK_MOVIES.find(m => parseInt(m.item_id) === parseInt(id));
    if (!movie) return;

    let downloads = JSON.parse(localStorage.getItem('streamora_downloads') || '[]');
    if (downloads.some(m => parseInt(m.item_id) === parseInt(id))) {
        alert("This title is already downloaded!");
        return;
    }

    let downloading = JSON.parse(localStorage.getItem('streamora_downloading') || '[]');
    if (downloading.some(d => parseInt(d.movie.item_id) === parseInt(id))) {
        alert("This title is already downloading!");
        return;
    }

    downloading.push({ movie, progress: 0 });
    localStorage.setItem('streamora_downloading', JSON.stringify(downloading));
    
    window.updateModalDownloadBtn(id);
    if (currentPage === 'downloads') renderDownloadsTab();

    const interval = setInterval(() => {
        let currentDownloading = JSON.parse(localStorage.getItem('streamora_downloading') || '[]');
        const itemIdx = currentDownloading.findIndex(d => parseInt(d.movie.item_id) === parseInt(id));
        if (itemIdx === -1) {
            clearInterval(interval);
            return;
        }

        currentDownloading[itemIdx].progress += 25;
        if (currentDownloading[itemIdx].progress >= 100) {
            clearInterval(interval);
            currentDownloading.splice(itemIdx, 1);
            localStorage.setItem('streamora_downloading', JSON.stringify(currentDownloading));

            let currentDownloaded = JSON.parse(localStorage.getItem('streamora_downloads') || '[]');
            currentDownloaded.push(movie);
            localStorage.setItem('streamora_downloads', JSON.stringify(currentDownloaded));
        } else {
            localStorage.setItem('streamora_downloading', JSON.stringify(currentDownloading));
        }

        if (currentPage === 'downloads') {
            renderDownloadsTab();
        }
        window.updateModalDownloadBtn(id);
    }, 1000);
};

window.removeDownload = function(id) {
    let downloads = JSON.parse(localStorage.getItem('streamora_downloads') || '[]');
    downloads = downloads.filter(m => parseInt(m.item_id) !== parseInt(id));
    localStorage.setItem('streamora_downloads', JSON.stringify(downloads));
    if (currentPage === 'downloads') {
        renderDownloadsTab();
    }
    window.updateModalDownloadBtn(id);
};

window.updateModalDownloadBtn = function(id) {
    const dBtn = document.getElementById('modal-download-btn');
    if (!dBtn) return;
    
    const downloads = JSON.parse(localStorage.getItem('streamora_downloads') || '[]');
    const downloading = JSON.parse(localStorage.getItem('streamora_downloading') || '[]');
    
    const isDownloaded = downloads.some(m => parseInt(m.item_id) === parseInt(id));
    const downloadingItem = downloading.find(d => parseInt(d.movie.item_id) === parseInt(id));
    
    if (isDownloaded) {
        dBtn.innerHTML = `🟢 Offline Ready (Remove)`;
        dBtn.onclick = () => window.removeDownload(id);
    } else if (downloadingItem) {
        dBtn.innerHTML = `⏳ Downloading ${downloadingItem.progress}%`;
        dBtn.onclick = null;
    } else {
        dBtn.innerHTML = `📥 Download`;
        dBtn.onclick = () => window.simulateDownload(id);
    }
};

async function renderDownloadsTab() {
    heroSection.innerHTML = '';
    heroSection.style.display = 'none';

    const downloaded = JSON.parse(localStorage.getItem('streamora_downloads') || '[]');
    const downloading = JSON.parse(localStorage.getItem('streamora_downloading') || '[]');

    const storageUsed = (downloaded.length * 1.8 + downloading.length * 0.9).toFixed(1);
    const storageFree = (64.0 - parseFloat(storageUsed)).toFixed(1);
    const storageUsedPct = (parseFloat(storageUsed) / 64.0 * 100).toFixed(0);

    contentRows.innerHTML = `
        <div class="row-section" style="padding-top:80px; padding-left: 5%; padding-right: 5%;">
            <h1 class="row-section__title" style="font-size:2.2rem;margin-bottom:12px;">Downloads</h1>
            <p style="color:var(--text-muted);font-size:0.95rem;margin-bottom:24px;">Offline media hub. Take your personal movie universe anywhere.</p>
            
            <!-- Storage Dashboard -->
            <div class="storage-dashboard">
                <div style="display:flex; justify-content:space-between; font-size:0.9rem; font-weight:600; color:white;">
                    <span>Storage Usage</span>
                    <span>${storageUsed} GB Used &nbsp;|&nbsp; ${storageFree} GB Free (Total: 64 GB)</span>
                </div>
                <div class="storage-bar-outer">
                    <div class="storage-bar-inner" style="width: ${storageUsedPct}%"></div>
                </div>
            </div>
        </div>
    `;

    // Render active downloading list
    if (downloading.length > 0) {
        const downloadingSec = document.createElement('div');
        downloadingSec.className = 'row-section';
        downloadingSec.style.paddingLeft = '5%';
        downloadingSec.style.paddingRight = '5%';
        downloadingSec.innerHTML = `
            <h3 style="color:white; margin-bottom:16px; font-weight:700;">Downloading (${downloading.length})</h3>
            <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:20px;">
                ${downloading.map(d => `
                    <div style="background:rgba(255,255,255,0.03); border:1px solid var(--glass-border); padding:12px; border-radius:var(--r-md); display:flex; gap:12px; align-items:center;">
                        <img src="${d.movie.poster_url}" style="width:50px; height:75px; object-fit:cover; border-radius:4px;">
                        <div style="flex:1; display:flex; flex-direction:column; gap:6px;">
                            <div style="color:white; font-weight:600; font-size:0.9rem;">${d.movie.title}</div>
                            <div style="font-size:0.75rem; color:var(--streamora-cyan);">Downloading... ${d.progress}%</div>
                            <div style="height:6px; background:rgba(255,255,255,0.1); border-radius:3px; overflow:hidden;">
                                <div style="height:100%; background:var(--streamora-cyan); width:${d.progress}%"></div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        contentRows.appendChild(downloadingSec);
    }

    if (downloaded.length > 0) {
        appendRow('Downloaded Offline', downloaded);
    }

    if (downloaded.length === 0 && downloading.length === 0) {
        const empty = document.createElement('div');
        empty.style.cssText = 'display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:35vh;text-align:center;padding:0 20px;';
        empty.innerHTML = `
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            <h2 style="font-size:1.8rem;color:var(--text-primary);margin:20px 0 10px;">No downloads yet</h2>
            <p style="color:var(--text-muted);max-width:400px;margin-bottom:24px;">Your downloaded movies and series will appear here for offline viewing.</p>
        `;
        contentRows.appendChild(empty);
        await fetchAndRender('Hidden Gems', 'Offline Curations (Offline Ready)');
    } else {
        await fetchAndRender('Trending Now', 'Offline Curations (Offline Ready)');
    }
}

// ── Home Page ─────────────────────────────────────────────────────────
async function loadHomePage() {
    heroSection.innerHTML = '';
    heroSection.style.display = 'none';
    contentRows.innerHTML = '';
    showSkeletonRows();

    window.shownItems = []; 

    const isMovie = window.currentFormat === 'movie';
    const isSeriesVal = window.currentFormat === 'series';

    // Hero banner and Top Picks Row
    let topPicksQuery = 'Top Picks For You';
    let topPicksTitle = 'Top Picks For You';
    if (isMovie) {
        topPicksQuery = 'Top Rated Movies';
        topPicksTitle = 'Top Movies';
    } else if (isSeriesVal) {
        topPicksQuery = 'Top Rated TV Shows';
        topPicksTitle = 'Today\'s Featured Series';
    }
    await fetchAndRender(topPicksQuery, topPicksTitle, true);

    // Continue Watching Row (if user has viewed history)
    const history = JSON.parse(localStorage.getItem('streamora_history') || '[]');
    const filteredHistory = history.filter(m => {
        return window.currentFormat === 'all' || 
               (isMovie && !window.isSeries(m)) ||
               (isSeriesVal && window.isSeries(m));
    });
    if (filteredHistory.length > 0) {
        appendRow(isSeriesVal ? 'Continue Watching Series' : 'Continue Watching', filteredHistory);
    }

    // Because You Watched dynamic recommendation row
    if (filteredHistory.length > 0) {
        const seed = filteredHistory[0];
        const recs = window.getSimilarRecommendations(seed)
            .map(r => r.movie)
            .filter(m => {
                return window.currentFormat === 'all' || 
                       (isMovie && !window.isSeries(m)) ||
                       (isSeriesVal && window.isSeries(m));
            });
        if (recs && recs.length > 0) {
            appendRow(`Because You Watched ${seed.title}`, recs.slice(0, 10));
        }
    }

    let trendingQuery = 'Trending Now';
    let trendingTitle = isMovie ? 'Trending Movies' : (isSeriesVal ? 'Trending Series' : 'Trending Now');
    await fetchAndRender(trendingQuery, trendingTitle, false);

    let scifiQuery = 'Mind-Bending Sci-Fi';
    let scifiTitle = isMovie ? 'Sci-Fi Movies' : (isSeriesVal ? 'Sci-Fi TV Shows' : 'Mind-Bending Sci-Fi');
    await fetchAndRender(scifiQuery, scifiTitle, false);

    // Curated rows pulling from FAISS index with specific semantic queries
    await fetchAndRender('Award Winners', 'Award Winners', false);
    await fetchAndRender('Anime', 'Top Rated Anime', false);
    await fetchAndRender('True Events', 'Based on True Events', false);

    const genres = [
        { q: 'Action', title: isMovie ? 'Action Movies' : (isSeriesVal ? 'Action Series' : 'Action Thrillers') },
        { q: 'Comedy', title: isMovie ? 'Comedy Movies' : (isSeriesVal ? 'Comedy Series' : 'Comedy Classics') },
        { q: 'Horror', title: isMovie ? 'Horror Movies' : (isSeriesVal ? 'Horror Series' : 'Horror & Supernatural') },
        { q: 'Drama', title: isMovie ? 'Drama Movies' : (isSeriesVal ? 'Drama Series' : 'Dramatic Masterpieces') },
        { q: 'Romance', title: isMovie ? 'Romance Movies' : (isSeriesVal ? 'Romance Series' : 'Romance & Love Stories') },
        { q: 'Thriller', title: isMovie ? 'Thriller Movies' : (isSeriesVal ? 'Thriller Series' : 'High-Stakes Thrillers') },
        { q: 'Anime', title: isMovie ? 'Animation Movies' : (isSeriesVal ? 'Anime Series' : 'Anime & Animation') },
        { q: 'Hidden Gems', title: isMovie ? 'Hidden Gem Movies' : (isSeriesVal ? 'Hidden Gem Series' : 'Hidden Gems') }
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
    
    // Check global RAG cache
    if (window.ragCache && window.ragCache[query]) {
        movies = [...window.ragCache[query]];
    } else {
        try {
            const resp = await authFetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, exclude_ids: [] }) // Fetch all so we cache the full dataset
            });
            if (resp.ok) {
                const data = await resp.json();
                movies = Array.isArray(data.response) ? data.response : (data.response && data.response.value);
                if (movies && movies.length > 0) {
                    window.ragCache = window.ragCache || {};
                    window.ragCache[query] = movies;
                }
            }
        } catch (e) {
            console.warn(`Failed to fetch for row '${rowTitle}', attempting fallback. Error:`, e);
        }
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

    // First: Filter by currentFormat (Movies vs TV Series)
    let filteredMovies = movies;
    if (window.currentFormat === 'movie') {
        filteredMovies = movies.filter(m => !window.isSeries(m));
    } else if (window.currentFormat === 'series') {
        filteredMovies = movies.filter(m => window.isSeries(m));
    }

    // Second: Filter out items already shown on the page to prevent duplicates
    // Relax deduplication for TV series since the TV series pool is very small (reusing is required)
    let dedupedMovies = filteredMovies.filter(m => {
        return window.currentFormat === 'series' ? true : !window.shownItems.includes(m.item_id);
    });

    // If format filtering & deduplication leaves us empty, fill with format-aligned fallbacks
    if (dedupedMovies.length === 0) {
        const qLower = query.toLowerCase();
        let fallbackList = FALLBACK_MOVIES.filter(m => {
            const matchesQuery = m.rich_metadata.genres.some(g => qLower.includes(g.toLowerCase()) || g.toLowerCase().includes(qLower)) ||
                                 m.overview.toLowerCase().includes(qLower) ||
                                 m.title.toLowerCase().includes(qLower);
            const matchesFormat = window.currentFormat === 'all' || 
                                  (window.currentFormat === 'movie' && !window.isSeries(m)) || 
                                  (window.currentFormat === 'series' && window.isSeries(m));
            return matchesQuery && matchesFormat && (window.currentFormat === 'series' ? true : !window.shownItems.includes(m.item_id));
        });
        
        if (fallbackList.length === 0) {
            fallbackList = FALLBACK_MOVIES.filter(m => {
                const matchesFormat = window.currentFormat === 'all' || 
                                      (window.currentFormat === 'movie' && !window.isSeries(m)) || 
                                      (window.currentFormat === 'series' && window.isSeries(m));
                return matchesFormat && (window.currentFormat === 'series' ? true : !window.shownItems.includes(m.item_id));
            }).sort(() => 0.5 - Math.random()).slice(0, 5);
        }
        dedupedMovies = fallbackList;
    }
    movies = dedupedMovies;

    if (movies && movies.length > 0) {
        movies.forEach(m => {
            if (!window.shownItems.includes(m.item_id)) {
                window.shownItems.push(m.item_id);
            }
        });
        globalMovies = [...globalMovies, ...movies];
        
        if (isHero) {
            const formatMatchedFallback = FALLBACK_MOVIES.find(m => {
                return window.currentFormat === 'all' ||
                       (window.currentFormat === 'movie' && !window.isSeries(m)) ||
                       (window.currentFormat === 'series' && window.isSeries(m));
            }) || FALLBACK_MOVIES[0];
            const heroMovie = movies[0] || formatMatchedFallback;
            renderHero(heroMovie);
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

    const activeFavorites = myList.filter(m => {
        return window.currentFormat === 'all' ||
               (window.currentFormat === 'movie' && !window.isSeries(m)) ||
               (window.currentFormat === 'series' && window.isSeries(m));
    });

    const headerSec = document.createElement('div');
    headerSec.className = 'row-section';
    headerSec.style.paddingTop = '80px';
    headerSec.style.marginBottom = '20px';
    headerSec.style.paddingLeft = '5%';
    headerSec.style.paddingRight = '5%';
    headerSec.innerHTML = `
        <h1 class="row-section__title" style="font-size:2.2rem;margin-bottom:12px; color: white;">Favorites & Watchlist</h1>
        <p style="color:var(--text-muted);font-size:0.95rem;">All your saved movies, TV series, and collections in one place.</p>
    `;
    contentRows.appendChild(headerSec);

    if (activeFavorites.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'empty-favorites';
        empty.style.cssText = 'display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:40vh;text-align:center;padding:0 20px;';
        empty.innerHTML = `
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#E50914" stroke-width="1.5" style="margin-bottom: 20px; filter: drop-shadow(0 0 8px rgba(229,9,20,0.4)); animation: pulse-mic 1.6s infinite;"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
            <h2 style="font-size:1.8rem;color:var(--text-primary);margin:0 0 10px;">No favorites yet.</h2>
            <p style="color:var(--text-muted);max-width:450px;margin-bottom:30px; font-size: 1rem;">Tap the heart icon on any ${window.currentFormat === 'series' ? 'TV series' : 'movie'} to save it.</p>
            <div style="display: flex; gap: 15px; flex-wrap: wrap; justify-content: center;">
                <button onclick="navigateTo('home')" style="padding:12px 24px; border-radius: var(--r-pill); background: var(--streamora-cyan); border: none; color: black; font-weight: 700; font-size: 0.95rem; cursor: pointer; transition: transform var(--t-fast);" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">Browse Home</button>
                <button onclick="navigateTo('categories')" style="padding:12px 24px; border-radius: var(--r-pill); background: rgba(255,255,255,0.08); border: 1px solid var(--glass-border); color: white; font-weight: 700; font-size: 0.95rem; cursor: pointer; transition: transform var(--t-fast);" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">Browse Categories</button>
            </div>
        `;
        contentRows.appendChild(empty);
        return;
    }

    const savedMovies = activeFavorites.filter(m => !window.isSeries(m));
    const savedSeries = activeFavorites.filter(m => window.isSeries(m));

    if (savedMovies.length > 0) {
        appendRow('Saved Movies', savedMovies);
    }
    if (savedSeries.length > 0) {
        appendRow('Saved TV Series', savedSeries);
    }

    // CURATED COLLECTIONS FROM SAVED ITEMS
    const scifiFavs = activeFavorites.filter(m => {
        const genres = (m.rich_metadata && (m.rich_metadata.genres || m.rich_metadata.tags || []) || []).map(g => g.toLowerCase());
        return genres.includes('sci-fi') || genres.includes('science fiction');
    });
    if (scifiFavs.length > 0) {
        appendRow('Sci-Fi Favorites Collection', scifiFavs);
    }

    const actionFavs = activeFavorites.filter(m => {
        const genres = (m.rich_metadata && (m.rich_metadata.genres || m.rich_metadata.tags || []) || []).map(g => g.toLowerCase());
        return genres.includes('action') || genres.includes('thriller');
    });
    if (actionFavs.length > 0) {
        appendRow('Action & Thriller Collection', actionFavs);
    }
    
    const rawHistory = JSON.parse(localStorage.getItem('streamora_history') || '[]');
    const history = rawHistory.filter(m => {
        return window.currentFormat === 'all' ||
               (window.currentFormat === 'movie' && !window.isSeries(m)) ||
               (window.currentFormat === 'series' && window.isSeries(m));
    });
    if (history.length > 0) {
        appendRow('Recently Viewed & Liked', history);
    }
};

function renderMyList() {
    renderFavoritesTab();
}

function toggleMyList(movie) {
    const idNum = parseInt(movie.item_id);
    const idx = myList.findIndex(m => parseInt(m.item_id) === idNum);
    if (idx >= 0) {
        myList.splice(idx, 1);
    } else {
        myList.push(movie);
    }
    localStorage.setItem('streamora_mylist', JSON.stringify(myList));
}

function isInMyList(id) {
    const idNum = parseInt(id);
    return myList.some(m => parseInt(m.item_id) === idNum);
}

// ── Click History Tracking ───────────────────────────────────────────
function addToHistory(movie) {
    if (!movie) return;
    let history = JSON.parse(localStorage.getItem('streamora_history') || '[]');
    history = history.filter(m => m.item_id !== movie.item_id);
    history.unshift(movie);
    if (history.length > 10) history.pop();
    localStorage.setItem('streamora_history', JSON.stringify(history));
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
        { name: 'Action', color: 'rgba(239, 68, 68, 0.5)', icon: '🎬', type: 'both' },
        { name: 'Adventure', color: 'rgba(245, 158, 11, 0.5)', icon: '🧭', type: 'both' },
        { name: 'Animation', color: 'rgba(59, 130, 246, 0.5)', icon: '🧸', type: 'both' },
        { name: 'Anime', color: 'rgba(236, 72, 153, 0.5)', icon: '🌸', type: 'both' },
        { name: 'Biography', color: 'rgba(16, 185, 129, 0.5)', icon: '📜', type: 'movie' },
        { name: 'Comedy', color: 'rgba(236, 72, 153, 0.5)', icon: '😂', type: 'both' },
        { name: 'Crime', color: 'rgba(107, 114, 128, 0.5)', icon: '🕵️', type: 'both' },
        { name: 'Dark Comedy', color: 'rgba(17, 24, 39, 0.8)', icon: '💀', type: 'movie' },
        { name: 'Disaster', color: 'rgba(220, 38, 38, 0.5)', icon: '🌋', type: 'movie' },
        { name: 'Documentary', color: 'rgba(6, 182, 212, 0.5)', icon: '📹', type: 'both' },
        { name: 'Drama', color: 'rgba(139, 92, 246, 0.5)', icon: '🎭', type: 'both' },
        { name: 'Family', color: 'rgba(16, 185, 12 emerald, 0.5)', icon: '👨‍👩‍👧‍👦', type: 'both' },
        { name: 'Fantasy', color: 'rgba(236, 72, 153, 0.5)', icon: '🐉', type: 'both' },
        { name: 'Historical', color: 'rgba(202, 138, 4, 0.5)', icon: '🏰', type: 'both' },
        { name: 'History', color: 'rgba(120, 53, 15, 0.5)', icon: '🏛️', type: 'movie' },
        { name: 'Holiday', color: 'rgba(239, 68, 68, 0.5)', icon: '🎄', type: 'movie' },
        { name: 'Horror', color: 'rgba(17, 24, 39, 0.8)', icon: '👻', type: 'both' },
        { name: 'Independent', color: 'rgba(107, 114, 128, 0.5)', icon: '🎥', type: 'movie' },
        { name: 'Kids', color: 'rgba(245, 158, 11, 0.5)', icon: '🎈', type: 'both' },
        { name: 'Martial Arts', color: 'rgba(185, 28, 28, 0.5)', icon: '🥋', type: 'movie' },
        { name: 'Medical', color: 'rgba(13, 148, 136, 0.5)', icon: '🩺', type: 'both' },
        { name: 'Military', color: 'rgba(63, 73, 61, 0.5)', icon: '🪖', type: 'movie' },
        { name: 'Music', color: 'rgba(139, 92, 246, 0.5)', icon: '🎵', type: 'both' },
        { name: 'Musical', color: 'rgba(236, 72, 153, 0.5)', icon: '🎹', type: 'movie' },
        { name: 'Mystery', color: 'rgba(79, 70, 229, 0.5)', icon: '🔍', type: 'both' },
        { name: 'Neo-Noir', color: 'rgba(15, 23, 42, 0.8)', icon: '🕶️', type: 'movie' },
        { name: 'Political', color: 'rgba(71, 85, 105, 0.5)', icon: '🏛️', type: 'both' },
        { name: 'Psychological', color: 'rgba(99, 102, 241, 0.5)', icon: '🧠', type: 'both' },
        { name: 'Reality', color: 'rgba(234, 179, 8, 0.5)', icon: '🌟', type: 'series' },
        { name: 'Romance', color: 'rgba(244, 63, 94, 0.5)', icon: '💖', type: 'both' },
        { name: 'Road Movie', color: 'rgba(217, 119, 6, 0.5)', icon: '🚗', type: 'movie' },
        { name: 'Satire', color: 'rgba(236, 72, 153, 0.5)', icon: '🤡', type: 'movie' },
        { name: 'Sci-Fi', color: 'rgba(139, 92, 246, 0.5)', icon: '🚀', type: 'both' },
        { name: 'Short Films', color: 'rgba(6, 182, 212, 0.5)', icon: '🎞️', type: 'movie' },
        { name: 'Sitcom', color: 'rgba(245, 158, 11, 0.5)', icon: '🛋️', type: 'series' },
        { name: 'Slice of Life', color: 'rgba(16, 185, 129, 0.5)', icon: '🍃', type: 'series' },
        { name: 'Sports', color: 'rgba(16, 185, 129, 0.5)', icon: '⚽', type: 'movie' },
        { name: 'Spy', color: 'rgba(30, 41, 59, 0.5)', icon: '🕶️', type: 'both' },
        { name: 'Superhero', color: 'rgba(2, 132, 199, 0.5)', icon: '🦸', type: 'both' },
        { name: 'Supernatural', color: 'rgba(139, 92, 246, 0.5)', icon: '🔮', type: 'both' },
        { name: 'Survival', color: 'rgba(21, 128, 61, 0.5)', icon: '🏕️', type: 'movie' },
        { name: 'Suspense', color: 'rgba(153, 27, 27, 0.5)', icon: '🤫', type: 'both' },
        { name: 'Teen', color: 'rgba(236, 72, 153, 0.5)', icon: '🎒', type: 'both' },
        { name: 'Thriller', color: 'rgba(153, 27, 27, 0.5)', icon: '🔪', type: 'both' },
        { name: 'Time Travel', color: 'rgba(234, 88, 12, 0.5)', icon: '⏳', type: 'both' },
        { name: 'True Crime', color: 'rgba(107, 114, 128, 0.5)', icon: '🔎', type: 'both' },
        { name: 'War', color: 'rgba(120, 53, 15, 0.5)', icon: '🪖', type: 'movie' },
        { name: 'Western', color: 'rgba(180, 83, 9, 0.5)', icon: '🤠', type: 'movie' },
        { name: 'Zombie', color: 'rgba(21, 128, 61, 0.5)', icon: '🧟', type: 'both' },
        { name: 'Noir', color: 'rgba(2, 6, 23, 0.8)', icon: '🕶️', type: 'movie' },
        { name: 'Cyberpunk', color: 'rgba(217, 70, 239, 0.5)', icon: '🌆', type: 'both' },
        { name: 'Steampunk', color: 'rgba(202, 138, 4, 0.5)', icon: '⚙️', type: 'both' },
        { name: 'Space Opera', color: 'rgba(37, 99, 235, 0.5)', icon: '🌌', type: 'both' },
        { name: 'Coming of Age', color: 'rgba(22, 163, 74, 0.5)', icon: '🌱', type: 'movie' },
        { name: 'Courtroom', color: 'rgba(13, 148, 136, 0.5)', icon: '⚖️', type: 'movie' },
        { name: 'Heist', color: 'rgba(30, 41, 59, 0.5)', icon: '💰', type: 'movie' },
        { name: 'Found Footage', color: 'rgba(55, 65, 81, 0.5)', icon: '📹', type: 'movie' },
        { name: 'Monster', color: 'rgba(153, 27, 27, 0.5)', icon: '👹', type: 'movie' },
        { name: 'Post-Apocalyptic', color: 'rgba(124, 45, 18, 0.5)', icon: '☣️', type: 'both' },
        { name: 'Dystopian', color: 'rgba(30, 41, 59, 0.5)', icon: '👁️', type: 'both' },
        { name: 'Mythology', color: 'rgba(245, 158, 11, 0.5)', icon: '🏛️', type: 'movie' },
        { name: 'Epic', color: 'rgba(217, 119, 6, 0.5)', icon: '⚔️', type: 'both' },
        { name: 'Classic', color: 'rgba(202, 138, 4, 0.5)', icon: '🎞️', type: 'movie' },
        { name: 'Cult Classics', color: 'rgba(139, 92, 246, 0.5)', icon: '🍿', type: 'movie' },
        { name: 'Experimental', color: 'rgba(6, 182, 212, 0.5)', icon: '🌀', type: 'movie' },
        { name: 'Global Cinema', color: 'rgba(37, 99, 235, 0.5)', icon: '🌍', type: 'both' },
        { name: 'Bollywood', color: 'rgba(245, 197, 24, 0.5)', icon: '🇮🇳', type: 'both' },
        { name: 'Hollywood', color: 'rgba(59, 130, 246, 0.5)', icon: '🇺🇸', type: 'both' },
        { name: 'Korean', color: 'rgba(236, 72, 153, 0.5)', icon: '🇰🇷', type: 'both' },
        { name: 'Japanese', color: 'rgba(239, 68, 68, 0.5)', icon: '🇯🇵', type: 'both' },
        { name: 'Chinese', color: 'rgba(239, 68, 68, 0.5)', icon: '🇨🇳', type: 'both' },
        { name: 'Indian Regional', color: 'rgba(16, 185, 129, 0.5)', icon: '🇮🇳', type: 'both' },
        { name: 'French', color: 'rgba(59, 130, 246, 0.5)', icon: '🇫🇷', type: 'both' },
        { name: 'Spanish', color: 'rgba(239, 68, 68, 0.5)', icon: '🇪🇸', type: 'both' },
        { name: 'Italian', color: 'rgba(16, 185, 129, 0.5)', icon: '🇮🇹', type: 'both' },
        { name: 'German', color: 'rgba(245, 158, 11, 0.5)', icon: '🇩🇪', type: 'both' },
        { name: 'Nordic', color: 'rgba(6, 182, 212, 0.5)', icon: '❄️', type: 'both' },
        { name: 'Middle Eastern', color: 'rgba(217, 119, 6, 0.5)', icon: '🕌', type: 'both' },
        { name: 'African Cinema', color: 'rgba(16, 185, 129, 0.5)', icon: '🌍', type: 'both' },
        { name: 'Latin American', color: 'rgba(244, 63, 94, 0.5)', icon: '💃', type: 'both' },
        { name: 'Australian', color: 'rgba(21, 128, 61, 0.5)', icon: '🦘', type: 'both' }
    ];

    const filteredCategories = categoriesData.filter(c => {
        if (currentFormat === 'all') return true;
        if (currentFormat === 'movie' && c.type !== 'series') return true;
        if (currentFormat === 'series' && c.type !== 'movie') return true;
        return false;
    });

    contentRows.innerHTML = prepend + `
        <div class="category-selection-container" style="padding: 0 24px 40px;">
            <div id="categories-grid-container">
                <h3 style="font-size: 1.15rem; color: white; margin-bottom: 16px;">All Categories</h3>
                <div class="genre-bubble-grid" id="category-cards-grid">
                    ${filteredCategories.map(c => `
                        <div class="genre-bubble category-card" data-name="${c.name.toLowerCase()}" onclick="selectCategory('${c.name}')" 
                             style="--glow-color: ${c.color || 'rgba(6, 182, 212, 0.4)'};">
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
    if (window.ragCache && window.ragCache[`category_${categoryName}`]) {
        movies = [...window.ragCache[`category_${categoryName}`]];
    } else {
        try {
            const resp = await authFetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: categoryName, exclude_ids: [] })
            });
            if (resp.ok) {
                const data = await resp.json();
                movies = Array.isArray(data.response) ? data.response : (data.response && data.response.value);
                if (movies && movies.length > 0) {
                    window.ragCache = window.ragCache || {};
                    window.ragCache[`category_${categoryName}`] = movies;
                }
            }
        } catch(e) {
            console.warn(`Category detail API error, utilizing fallbacks for '${categoryName}':`, e);
        }
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

    // Escape title to prevent breaks in onerror handler
    const escapedTitle = t.replace(/'/g, "\\'").replace(/"/g, '&quot;');

    return `
    <div class="card-wrap" style="cursor: pointer;" onclick="openModal(${movie.item_id})">
        <div class="card-3d" data-id="${movie.item_id}" tabindex="0">
            <div class="img-container">
                <div class="img-placeholder"><div class="blur-skeleton"></div></div>
                <img src="${poster}" alt="${t}" loading="lazy" onload="window.imageLoaded(this)" onerror="window.imageLoadError(this, '${escapedTitle}')">
            </div>
            <div class="card-3d__badge">${score}%</div>
            <button class="card-heart-btn" data-id="${movie.item_id}" onclick="event.stopPropagation(); window.toggleFavorite(${movie.item_id});" aria-label="${saved ? 'Remove from favorites' : 'Add to favorites'}" style="position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.6); border: 1px solid rgba(255,255,255,0.15); border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; color: ${saved ? 'var(--streamora-cyan)' : 'white'}; cursor: pointer; z-index: 5; transition: all var(--t-fast);" onmouseover="this.style.transform='scale(1.15)'" onmouseout="this.style.transform='scale(1)'">
                ${saved 
                    ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="var(--streamora-cyan)" stroke="var(--streamora-cyan)" stroke-width="1.5"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>`
                    : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`
                }
            </button>
            <div class="card-3d__glare"></div>
        </div>
        <div class="card-expand">
            <div class="img-container">
                <div class="img-placeholder"><div class="blur-skeleton"></div></div>
                <img src="${backdrop}" class="card-expand__img" alt="" loading="lazy" onload="window.imageLoaded(this)" onerror="window.imageLoadError(this, '${escapedTitle}')">
            </div>
            <div class="card-expand__body">
                <div class="card-expand__title">${t}</div>
                <div class="card-expand__meta">
                    <span class="card-expand__pct">${score}% Match</span>
                    <span class="card-expand__type" style="color: var(--streamora-cyan); font-weight: 600; margin: 0 4px;">${isSeries(movie) ? 'TV Series' : 'Movie'}</span>
                    ${m.year ? `<span>${m.year}</span>` : ''}
                    ${m.runtime ? `<span>${m.runtime}</span>` : ''}
                </div>
                <div class="card-expand__genres">${genres}</div>
                <div class="card-expand__ai">
                    <div class="card-expand__ai-label">Why Streamora Picked This</div>
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
    
    const history = JSON.parse(localStorage.getItem('streamora_history') || '[]');
    const watchlist = JSON.parse(localStorage.getItem('streamora_mylist') || '[]');
    
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
window.startVoiceSearch = function() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        alert("Speech recognition is not supported in this browser. Please try typing your search.");
        return;
    }

    const overlay = document.getElementById('voice-search-overlay');
    const statusText = document.getElementById('voice-status-text');
    const transcriptText = document.getElementById('voice-transcript-text');
    if (!overlay || !statusText || !transcriptText) return;

    overlay.classList.add('active');
    statusText.textContent = "Listening...";
    transcriptText.textContent = 'Try saying "Suggest some dark sci-fi thrillers"';

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        transcriptText.textContent = `"${transcript}"`;
        statusText.textContent = "Searching...";
        setTimeout(() => {
            overlay.classList.remove('active');
            window.executeSearchPageQuery(transcript);
        }, 1000);
    };

    recognition.onerror = function(event) {
        console.error("Speech recognition error:", event.error);
        statusText.textContent = "Error occurred";
        transcriptText.textContent = `Error: ${event.error}. Please try again.`;
        setTimeout(() => {
            overlay.classList.remove('active');
        }, 2000);
    };

    recognition.onend = function() {
        setTimeout(() => {
            if (overlay.classList.contains('active') && statusText.textContent === "Listening...") {
                overlay.classList.remove('active');
            }
        }, 6000);
    };

    recognition.start();
};

window.closeVoiceSearch = function() {
    const overlay = document.getElementById('voice-search-overlay');
    if (overlay) overlay.classList.remove('active');
};

function loadSearchPage() {
    heroSection.innerHTML = '';
    heroSection.style.display = 'none';
    
    contentRows.innerHTML = `
        <div class="search-page-container" style="padding: 80px 5% 40px; min-height: 80vh; max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 32px;">
            
            <!-- 1. Search Field Header -->
            <div class="search-page-header" style="display: flex; flex-direction: column; gap: 16px;">
                <h1 style="font-size: 2.2rem; font-weight: 800; color: white;">Search & Discovery</h1>
                <div class="search-input-wrapper" style="position: relative; display: flex; align-items: center; width: 100%;">
                    <span style="position: absolute; left: 24px; color: var(--text-muted); font-size: 1.2rem;">🔍</span>
                    <input type="text" id="search-page-input" placeholder="Search movies, TV series, actors, directors, genres..." 
                           style="width: 100%; padding: 18px 60px; border-radius: var(--r-pill); background: rgba(255,255,255,0.04); border: 1px solid var(--glass-border); color: white; font-size: 1.1rem; outline: none; transition: border-color var(--t-fast), box-shadow var(--t-fast);"
                           autocomplete="off">
                    <button id="search-voice-placeholder" onclick="window.startVoiceSearch()" style="position: absolute; right: 24px; background: transparent; border: none; color: var(--text-muted); cursor: pointer; font-size: 1.2rem;" title="Voice Search">🎙️</button>
                </div>
            </div>
            
            <!-- 2. Suggestions Dropdown / Live Results Box -->
            <div id="search-page-suggestions" style="background: rgba(15,15,15,0.9); border: 1px solid var(--glass-border); border-radius: var(--r-md); padding: 15px; display: none; flex-direction: column; gap: 16px; z-index: 100;">
            </div>
            
            <!-- 3. Main Search content area -->
            <div id="search-page-content" style="display: flex; flex-direction: column; gap: 40px;">
                 <!-- Empty state or Results grid gets rendered here -->
            </div>
        </div>
    `;
    
    const input = document.getElementById('search-page-input');
    if (input) {
        input.addEventListener('input', handleLiveSearch);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                executeSearchPageQuery(input.value.trim());
            }
        });
    }
    
    renderSearchEmptyState();
}

window.renderSearchEmptyState = function() {
    const container = document.getElementById('search-page-content');
    if (!container) return;
    
    const trendingMovies = FALLBACK_MOVIES.filter(m => !window.isSeries(m)).slice(0, 4);
    const popularSeries = FALLBACK_MOVIES.filter(m => window.isSeries(m)).slice(0, 4);
    
    const recentSearches = JSON.parse(localStorage.getItem('streamora_recent_searches') || '[]');
    
    const suggestedSearches = [
        "Mind-bending sci-fi",
        "Dark psychological dramas",
        "Action comedy thrillers",
        "Gothic mystery",
        "Dystopian future"
    ];
    
    const searchCategories = {
        "Genres": ["Action", "Sci-Fi", "Horror", "Comedy", "Drama", "Thriller", "Romance", "Mystery", "Anime", "Documentary"],
        "Actors": ["Tom Hanks", "Leonardo DiCaprio", "Scarlett Johansson", "Cillian Murphy", "Zendaya", "Robert Downey Jr.", "Brad Pitt"],
        "Directors": ["Christopher Nolan", "Quentin Tarantino", "Denis Villeneuve", "Martin Scorsese", "Greta Gerwig", "Steven Spielberg"],
        "Release Year": ["2026", "2025", "2024", "2023", "2022", "2020s", "2010s", "2000s"],
        "Language": ["English", "Spanish", "Japanese", "Korean", "French", "German"],
        "Mood & Tone": ["Mind-bending", "Dark", "Uplifting", "Suspenseful", "Atmospheric", "Emotional", "Heartwarming"]
    };
    
    let recentHTML = '';
    if (recentSearches.length > 0) {
        recentHTML = `
            <div style="margin-top: 20px;">
                <h3 style="color: white; font-size: 1.1rem; margin-bottom: 12px; text-align: left; font-weight: 700;">Recent Searches</h3>
                <div style="display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-start;">
                    ${recentSearches.map(q => `
                        <button onclick="executeSearchPageQuery('${esc(q)}')" style="padding: 8px 16px; border-radius: var(--r-pill); background: rgba(6,182,212,0.06); border: 1px solid rgba(6,182,212,0.2); color: var(--streamora-cyan); cursor: pointer; transition: all var(--t-fast); font-size: 0.85rem;" onmouseover="this.style.background='rgba(6,182,212,0.12)'" onmouseout="this.style.background='rgba(6,182,212,0.06)'">${q}</button>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    let categoriesHTML = '';
    for (const [title, list] of Object.entries(searchCategories)) {
        categoriesHTML += `
            <div style="display: flex; flex-direction: column; gap: 10px;">
                <h4 style="color: rgba(255,255,255,0.7); font-size: 0.95rem; text-align: left; margin: 0; font-weight: 700;">Search by ${title}</h4>
                <div style="display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-start;">
                    ${list.map(item => `
                        <button onclick="executeSearchPageQuery('${item}')" style="padding: 8px 14px; border-radius: var(--r-pill); background: rgba(255,255,255,0.03); border: 1px solid var(--glass-border); color: rgba(255,255,255,0.85); cursor: pointer; transition: all var(--t-fast); font-size: 0.82rem;" onmouseover="this.style.background='rgba(255,255,255,0.08)'; this.style.color='white';" onmouseout="this.style.background='rgba(255,255,255,0.03)'; this.style.color='rgba(255,255,255,0.85)';">${item}</button>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    const showMovies = window.currentFormat === 'all' || window.currentFormat === 'movie';
    const showSeries = window.currentFormat === 'all' || window.currentFormat === 'series';
    
    container.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 32px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 30px;">
            <div>
                <h3 style="color: white; font-size: 1.1rem; margin-bottom: 16px; text-align: left; font-weight: 700;">Suggested Searches</h3>
                <div style="display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-start;">
                    ${suggestedSearches.map(q => `
                        <button onclick="executeSearchPageQuery('${q}')" style="padding: 10px 18px; border-radius: var(--r-pill); background: rgba(255,255,255,0.04); border: 1px solid var(--glass-border); color: white; cursor: pointer; transition: all var(--t-fast); font-size: 0.85rem;" onmouseover="this.style.background='rgba(255,255,255,0.08)'" onmouseout="this.style.background='rgba(255,255,255,0.04)'">${q}</button>
                    `).join('')}
                </div>
                ${recentHTML}
            </div>
            
            <div style="display: flex; flex-direction: column; gap: 20px;">
                ${categoriesHTML}
            </div>
        </div>
        
        ${showMovies ? `
        <div>
            <h3 style="color: white; font-size: 1.2rem; margin-bottom: 16px; text-align: left; font-weight: 700;">Trending Movies</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 20px;">
                ${trendingMovies.map(movie => {
                    const m = movie.rich_metadata || {};
                    const score = m.match_percentage || 92;
                    return `
                        <div onclick="openModal(${movie.item_id})" style="cursor: pointer; transition: transform var(--t-fast);" onmouseover="this.style.transform='scale(1.03)'" onmouseout="this.style.transform='scale(1)'">
                            <div style="position: relative; border-radius: var(--r-sm); overflow: hidden; aspect-ratio: 2/3; border: 1px solid var(--glass-border);">
                                <img src="${movie.poster_url}" alt="${movie.title}" style="width: 100%; height: 100%; object-fit: cover;">
                                <div style="position: absolute; top: 8px; left: 8px; background: rgba(0,0,0,0.7); color: var(--match-green); font-size: 0.75rem; font-weight: 700; padding: 2px 6px; border-radius: 4px;">${score}%</div>
                            </div>
                            <div style="font-size: 0.8rem; font-weight: 600; color: white; margin-top: 8px; text-align: center; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">${movie.title}</div>
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
        ` : ''}

        ${showSeries ? `
        <div>
            <h3 style="color: white; font-size: 1.2rem; margin-bottom: 16px; text-align: left; font-weight: 700;">Popular TV Series</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 20px;">
                ${popularSeries.map(movie => {
                    const m = movie.rich_metadata || {};
                    const score = m.match_percentage || 88;
                    return `
                        <div onclick="openModal(${movie.item_id})" style="cursor: pointer; transition: transform var(--t-fast);" onmouseover="this.style.transform='scale(1.03)'" onmouseout="this.style.transform='scale(1)'">
                            <div style="position: relative; border-radius: var(--r-sm); overflow: hidden; aspect-ratio: 2/3; border: 1px solid var(--glass-border);">
                                <img src="${movie.poster_url}" alt="${movie.title}" style="width: 100%; height: 100%; object-fit: cover;">
                                <div style="position: absolute; top: 8px; left: 8px; background: rgba(0,0,0,0.7); color: var(--match-green); font-size: 0.75rem; font-weight: 700; padding: 2px 6px; border-radius: 4px;">${score}%</div>
                            </div>
                            <div style="font-size: 0.8rem; font-weight: 600; color: white; margin-top: 8px; text-align: center; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">${movie.title}</div>
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
        ` : ''}
    `;
};;

window.handleLiveSearch = function() {
    const input = document.getElementById('search-page-input');
    const suggestionsBox = document.getElementById('search-page-suggestions');
    if (!input || !suggestionsBox) return;
    
    const query = input.value.trim().toLowerCase();
    if (query.length < 2) {
        suggestionsBox.style.display = 'none';
        return;
    }
    
    const matchedMovies = FALLBACK_MOVIES.filter(m => !isSeries(m) && m.title.toLowerCase().includes(query)).slice(0, 3);
    const matchedSeries = FALLBACK_MOVIES.filter(m => isSeries(m) && m.title.toLowerCase().includes(query)).slice(0, 3);
    
    const allGenres = [...new Set(FALLBACK_MOVIES.flatMap(m => m.rich_metadata.genres || []))];
    const matchedGenres = allGenres.filter(g => g.toLowerCase().includes(query)).slice(0, 3);
    
    const allDirectors = [...new Set(FALLBACK_MOVIES.map(m => m.rich_metadata.director).filter(Boolean))];
    const matchedDirectors = allDirectors.filter(d => d.toLowerCase().includes(query)).slice(0, 3);
    
    const allThemes = [...new Set(FALLBACK_MOVIES.flatMap(m => m.rich_metadata.themes || []))];
    const matchedThemes = allThemes.filter(t => t.toLowerCase().includes(query)).slice(0, 3);
    
    let html = '';
    
    if (matchedMovies.length > 0) {
        html += `<div style="text-align: left; padding: 4px 8px;"><strong style="color:var(--streamora-cyan); font-size:0.8rem; text-transform:uppercase;">Movies</strong>`;
        html += matchedMovies.map(m => `<div style="padding:6px 12px; cursor:pointer;" onclick="openModal(${m.item_id})">🎬 ${m.title}</div>`).join('');
        html += `</div>`;
    }
    
    if (matchedSeries.length > 0) {
        html += `<div style="text-align: left; padding: 4px 8px;"><strong style="color:var(--streamora-cyan); font-size:0.8rem; text-transform:uppercase;">Series</strong>`;
        html += matchedSeries.map(m => `<div style="padding:6px 12px; cursor:pointer;" onclick="openModal(${m.item_id})">📺 ${m.title}</div>`).join('');
        html += `</div>`;
    }
    
    if (matchedGenres.length > 0) {
        html += `<div style="text-align: left; padding: 4px 8px;"><strong style="color:var(--streamora-cyan); font-size:0.8rem; text-transform:uppercase;">Genres</strong>`;
        html += matchedGenres.map(g => `<div style="padding:6px 12px; cursor:pointer;" onclick="executeSearchPageQuery('${g}')">🎭 ${g}</div>`).join('');
        html += `</div>`;
    }
    
    if (matchedDirectors.length > 0) {
        html += `<div style="text-align: left; padding: 4px 8px;"><strong style="color:var(--streamora-cyan); font-size:0.8rem; text-transform:uppercase;">Directors</strong>`;
        html += matchedDirectors.map(d => `<div style="padding:6px 12px; cursor:pointer;" onclick="executeSearchPageQuery('${d}')">🎥 ${d}</div>`).join('');
        html += `</div>`;
    }
    
    if (matchedThemes.length > 0) {
        html += `<div style="text-align: left; padding: 4px 8px;"><strong style="color:var(--streamora-cyan); font-size:0.8rem; text-transform:uppercase;">Themes</strong>`;
        html += matchedThemes.map(t => `<div style="padding:6px 12px; cursor:pointer;" onclick="executeSearchPageQuery('${t}')">🌀 ${t}</div>`).join('');
        html += `</div>`;
    }
    
    if (html === '') {
        suggestionsBox.style.display = 'none';
    } else {
        suggestionsBox.innerHTML = html;
        suggestionsBox.style.display = 'flex';
        suggestionsBox.style.flexDirection = 'column';
    }
};

window.executeSearchPageQuery = async function(query) {
    if (!query) return;
    
    // Save to recent searches
    try {
        let recent = JSON.parse(localStorage.getItem('streamora_recent_searches') || '[]');
        recent = recent.filter(q => q.toLowerCase() !== query.toLowerCase());
        recent.unshift(query);
        if (recent.length > 5) recent.pop();
        localStorage.setItem('streamora_recent_searches', JSON.stringify(recent));
    } catch(e) {
        console.warn("Could not save recent search:", e);
    }

    const suggestionsBox = document.getElementById('search-page-suggestions');
    if (suggestionsBox) suggestionsBox.style.display = 'none';
    
    const input = document.getElementById('search-page-input');
    if (input) input.value = query;
    
    const topbarInput = document.getElementById('topbar-search-input');
    if (topbarInput) topbarInput.value = query;
    
    const container = document.getElementById('search-page-content');
    if (!container) return;
    
    container.innerHTML = `<div style="text-align:center; padding:40px;"><div class="skeleton" style="width:50px; height:50px; border-radius:50%; margin:0 auto 15px;"></div>Searching for "${query}"...</div>`;
    
    let movies = [];
    if (window.ragCache && window.ragCache[`search_${query}`]) {
        movies = [...window.ragCache[`search_${query}`]];
    } else {
        try {
            const resp = await fetch('/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ query, top_k: 20 })
            });
            if (resp.ok) {
                movies = await resp.json();
                if (movies && movies.length > 0) {
                    window.ragCache = window.ragCache || {};
                    window.ragCache[`search_${query}`] = movies;
                }
            }
        } catch(err) {
            console.warn("Search page query error, resorting to local search:", err);
        }
    }
    
    if (!movies || !Array.isArray(movies) || movies.length === 0) {
        const q = query.toLowerCase();
        movies = FALLBACK_MOVIES.filter(m => {
            return m.title.toLowerCase().includes(q) ||
                   m.overview.toLowerCase().includes(q) ||
                   (m.rich_metadata.genres || []).some(g => g.toLowerCase().includes(q)) ||
                   (m.rich_metadata.themes || []).some(t => t.toLowerCase().includes(q)) ||
                   (m.rich_metadata.director || '').toLowerCase().includes(q);
        });
    }
    
    // Filter search results by active format mode
    let filteredMovies = (movies || []).filter(m => {
        return window.currentFormat === 'all' ||
               (window.currentFormat === 'movie' && !window.isSeries(m)) ||
               (window.currentFormat === 'series' && window.isSeries(m));
    });
    
    // If format filtering leaves us empty, fill with format-aligned fallbacks matching the query
    if (filteredMovies.length === 0) {
        const q = query.toLowerCase();
        filteredMovies = FALLBACK_MOVIES.filter(m => {
            const matchesFormat = window.currentFormat === 'all' ||
                                  (window.currentFormat === 'movie' && !window.isSeries(m)) ||
                                  (window.currentFormat === 'series' && window.isSeries(m));
            const matchesQuery = m.title.toLowerCase().includes(q) ||
                                 m.overview.toLowerCase().includes(q) ||
                                 (m.rich_metadata.genres || []).some(g => g.toLowerCase().includes(q)) ||
                                 (m.rich_metadata.themes || []).some(t => t.toLowerCase().includes(q)) ||
                                 (m.rich_metadata.director || '').toLowerCase().includes(q);
            return matchesFormat && matchesQuery;
        });
        
        // If still empty, return any format-aligned fallbacks
        if (filteredMovies.length === 0) {
            filteredMovies = FALLBACK_MOVIES.filter(m => {
                return window.currentFormat === 'all' ||
                       (window.currentFormat === 'movie' && !window.isSeries(m)) ||
                       (window.currentFormat === 'series' && window.isSeries(m));
            }).slice(0, 4);
        }
    }
    movies = filteredMovies;
    
    if (movies && movies.length > 0) {
        container.innerHTML = `
            <h3 style="color:white; font-size:1.2rem; margin-bottom:16px; text-align: left;">Results for "${query}"</h3>
            <div class="search-results-grid" style="display:grid; grid-template-columns:repeat(auto-fill, minmax(200px, 1fr)); gap:24px;">
                ${movies.map(movie => {
                    const m = movie.rich_metadata || {};
                    const poster = movie.poster_url || placeholder(movie.title);
                    const score = m.match_percentage || randScore();
                    const rating = m.rating || '8.0';
                    const genres = (m.genres || m.tags || ['Drama']).slice(0, 2).join(', ');
                    const runtime = m.runtime || '120 min';
                    
                    return `
                        <div onclick="openModal(${movie.item_id})" style="cursor:pointer; background:rgba(255,255,255,0.02); border:1px solid var(--glass-border); border-radius:var(--r-md); overflow:hidden; transition:transform var(--t-fast); text-align: left;" onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
                            <div style="position:relative; aspect-ratio:2/3;">
                                <img src="${poster}" alt="${movie.title}" style="width:100%; height:100%; object-fit:cover;">
                                <div style="position:absolute; top:8px; left:8px; background:rgba(0,0,0,0.8); color:var(--match-green); font-size:0.75rem; font-weight:700; padding:3px 6px; border-radius:4px;">${score}% Match</div>
                                <div style="position:absolute; top:8px; right:8px; background:rgba(0,0,0,0.8); color:#f5c518; font-size:0.75rem; font-weight:700; padding:3px 6px; border-radius:4px;">★ ${rating}</div>
                            </div>
                            <div style="padding:12px; display:flex; flex-direction:column; gap:4px;">
                                <div style="font-weight:700; color:white; font-size:0.95rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${movie.title}</div>
                                <div style="font-size:0.8rem; color:var(--streamora-cyan);">${genres}</div>
                                <div style="font-size:0.8rem; color:var(--text-muted);">${runtime}</div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    } else {
        container.innerHTML = `
            <div style="text-align:center; padding:60px; color:var(--text-muted);">
                <div style="font-size:3rem; margin-bottom:15px;">🔍</div>
                <h3>No results found for "${query}"</h3>
                <p>Try searching for a different movie, genre, director, or click one of the suggestions below.</p>
                <button onclick="renderSearchEmptyState()" style="margin-top:20px; padding:10px 20px; border-radius:var(--r-pill); background:var(--streamora-cyan); border:none; color:black; font-weight:700; cursor:pointer;">Reset Search</button>
            </div>
        `;
    }
};

// ══════════════════════════════════════════════════════════════════════
//  RENDER ENGINE
// ══════════════════════════════════════════════════════════════════════

function renderResults(movies, mainTitle, isHome = false) {
    window.isDisplayingAIResults = true;
    window.lastAIRawResults = movies;
    window.lastAIRowTitle = mainTitle;
    window.lastAIIsHome = isHome;

    let filteredMovies = movies || [];
    if (window.currentFormat === 'movie') {
        filteredMovies = movies.filter(m => !window.isSeries(m));
    } else if (window.currentFormat === 'series') {
        filteredMovies = movies.filter(m => window.isSeries(m));
    }

    if (filteredMovies.length === 0) {
        filteredMovies = FALLBACK_MOVIES.filter(m => {
            return window.currentFormat === 'all' || 
                   (window.currentFormat === 'movie' && !window.isSeries(m)) || 
                   (window.currentFormat === 'series' && window.isSeries(m));
        }).slice(0, 5);
    }

    globalMovies = filteredMovies;
    contentRows.innerHTML = '';

    const sorted = [...filteredMovies].sort((a, b) => {
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
    const poster = movie.poster_url || placeholder(title);
    const score = m.match_percentage || randScore();
    const rating = m.rating || '8.2';
    const synopsis = m.story_summary || movie.overview || 'A cinematic masterpiece recommended by Streamora AI.';
    const genres = (m.genres || m.tags || ['Drama']).slice(0, 4).map(g => `<span class="gpill">${g}</span>`).join('');
    const castString = getMovieCast(title) || 'Cast details unavailable';
    const languages = getMovieLanguages(movie);
    const saved = isInMyList(movie.item_id);
    const tUrl = movie.trailer_url || m.trailer_url || '';
    const tUrlEscaped = tUrl ? `'${tUrl.replace(/'/g, "\\'")}'` : 'null';

    window.updateAmbientBackground(bg);

    heroSection.style.display = 'flex';
    heroSection.innerHTML = `
        <div class="hero__bg backdrop-loading"></div>
        <div class="hero__overlay"></div>
        <div class="hero__inner">
            <div class="hero__layout">
                <!-- Left Column: Details -->
                <div class="hero__left">
                    <div style="display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 12px; justify-content: flex-start;">
                        <span class="hero__match" style="margin-bottom: 0; box-shadow: 0 4px 12px rgba(6,182,212,0.25);">★ ${score}% Streamora Match</span>
                        <span style="color: #f5c518; font-weight: 700; font-size: 0.95rem; background: rgba(0,0,0,0.6); padding: 4px 10px; border-radius: var(--r-sm); border: 1px solid rgba(255,255,255,0.1);">IMDb ${rating}</span>
                    </div>
                    <h1 class="hero__title" onclick="openModal(${movie.item_id})" style="cursor: pointer;">${title}</h1>
                    <div class="hero__meta" style="justify-content: flex-start;">
                        ${m.year ? `<span>${m.year}</span><span class="hero__meta-dot"></span>` : ''}
                        ${m.runtime ? `<span>${m.runtime}</span><span class="hero__meta-dot"></span>` : ''}
                        <span>Languages: ${languages}</span>
                    </div>
                    <div class="hero__genres" style="justify-content: flex-start;">${genres}</div>
                    
                    <!-- Glass Container for Synopsis -->
                    <div class="hero__desc-container">
                        <p class="hero__desc">${synopsis}</p>
                    </div>
                    
                    <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 20px; display: flex; flex-direction: column; gap: 4px; background: rgba(0,0,0,0.3); padding: 10px 14px; border-radius: var(--r-sm); max-width: 600px; border: 1px solid rgba(255,255,255,0.04); text-align: left; width: 100%; box-sizing: border-box;">
                        <div><span style="color: white; font-weight: 600;">Director:</span> ${m.director || "Unknown Director"}</div>
                        <div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"><span style="color: white; font-weight: 600;">Cast:</span> ${Array.isArray(castString) ? castString.join(', ') : castString}</div>
                    </div>
                    
                    <div class="hero__btns" style="justify-content: flex-start; width: 100%;">
                        <button class="hero-btn hero-btn--play" onclick="event.stopPropagation(); if (${tUrlEscaped}) { window.openTrailerLightbox(${tUrlEscaped}, '${title.replace(/'/g, "\\'")}'); } else { openModal(${movie.item_id}); }" style="cursor: pointer;">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> Watch Trailer
                        </button>
                        <button class="hero-btn hero-btn--info" onclick="event.stopPropagation(); openModal(${movie.item_id})" style="cursor: pointer;">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg> View Details
                        </button>
                        
                        <button class="hero-fav-btn" data-id="${movie.item_id}" onclick="event.stopPropagation(); toggleFavorite(${movie.item_id})" style="background: rgba(255,255,255,0.08); border: 1px solid var(--glass-border); border-radius: var(--r-md); width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; color: ${saved ? 'var(--streamora-cyan)' : 'white'}; cursor: pointer; transition: all var(--t-fast);" title="${saved ? 'Remove from Favorites' : 'Add to Favorites'}" onmouseover="this.style.background='rgba(255,255,255,0.15)'" onmouseout="this.style.background='rgba(255,255,255,0.08)'">
                            ${saved 
                                ? `<svg width="22" height="22" viewBox="0 0 24 24" fill="var(--streamora-cyan)" stroke="var(--streamora-cyan)" stroke-width="1.5"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>`
                                : `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`
                            }
                        </button>
                        
                        <button class="hero-watchlist-btn" data-id="${movie.item_id}" onclick="event.stopPropagation(); toggleFavorite(${movie.item_id})" style="background: rgba(255,255,255,0.08); border: 1px solid var(--glass-border); border-radius: var(--r-md); width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; color: ${saved ? 'var(--streamora-cyan)' : 'white'}; cursor: pointer; transition: all var(--t-fast);" title="${saved ? 'Remove from Watchlist' : 'Add to Watchlist'}" onmouseover="this.style.background='rgba(255,255,255,0.15)'" onmouseout="this.style.background='rgba(255,255,255,0.08)'">
                            ${saved 
                                ? `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--streamora-cyan)" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`
                                : `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`
                            }
                        </button>
                    </div>
                </div>
                
                <!-- Right Column: Poster with 3D Hover & Play Overlay -->
                <div class="hero__right">
                    <div class="hero__poster-wrapper" onclick="event.stopPropagation(); if (${tUrlEscaped}) { window.openTrailerLightbox(${tUrlEscaped}, '${title.replace(/'/g, "\\'")}'); } else { openModal(${movie.item_id}); }">
                        <div class="img-container" style="border-radius: var(--r-md); aspect-ratio: 2/3; height: auto;">
                            <div class="img-placeholder"><div class="blur-skeleton"></div></div>
                            <img src="${poster}" alt="${title}" loading="lazy" onload="window.imageLoaded(this)" onerror="window.imageLoadError(this, '${title.replace(/'/g, "\\'")}')">
                        </div>
                        <div class="hero__play-overlay">
                            <div class="hero__play-btn-circle">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="white"><path d="M8 5v14l11-7z"/></svg>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Progressive Hero Backdrop Loader
    setTimeout(() => {
        const heroBg = heroSection.querySelector('.hero__bg');
        if (heroBg) {
            const tempImg = new Image();
            tempImg.onload = () => {
                heroBg.style.backgroundImage = `url('${bg}')`;
                heroBg.classList.remove('backdrop-loading');
                heroBg.classList.add('backdrop-loaded');
            };
            tempImg.onerror = () => {
                heroBg.style.backgroundImage = 'linear-gradient(to bottom, rgba(15, 23, 42, 0.7), rgba(15, 23, 42, 1))';
                heroBg.classList.remove('backdrop-loading');
            };
            tempImg.src = bg;
        }
    }, 50);
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
        const tUrl = movie.trailer_url || m.trailer_url || '';
        const tUrlEscaped = tUrl ? `'${tUrl.replace(/'/g, "\\'")}'` : 'null';

        return `
        <div class="card-wrap" data-idx="${i}" style="cursor: pointer;">
            <div class="card-3d" data-id="${movie.item_id}" tabindex="0">
                <img src="${poster}" alt="${t}" loading="lazy" onerror="this.src='${placeholder(t)}'">
                <div class="card-3d__badge">${score}%</div>
                <button class="card-heart-btn" data-id="${movie.item_id}" onclick="event.stopPropagation(); window.toggleFavorite(${movie.item_id});" aria-label="${saved ? 'Remove from favorites' : 'Add to favorites'}" style="position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.6); border: 1px solid rgba(255,255,255,0.15); border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; color: ${saved ? 'var(--streamora-cyan)' : 'white'}; cursor: pointer; z-index: 5; transition: all var(--t-fast);" onmouseover="this.style.transform='scale(1.15)'" onmouseout="this.style.transform='scale(1)'">
                    ${saved 
                        ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="var(--streamora-cyan)" stroke="var(--streamora-cyan)" stroke-width="1.5"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>`
                        : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`
                    }
                </button>
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
                        <div class="card-expand__ai-label">Why Streamora Picked This</div>
                        <ul>
                            <li>Matches your preferred genres</li>
                            <li>High thematic similarity</li>
                            <li>Popular among similar viewers</li>
                        </ul>
                    </div>
                    <div class="card-expand__btns">
                        <button class="card-expand__btn card-expand__btn--play" onclick="event.stopPropagation(); if (${tUrlEscaped}) { window.openTrailerLightbox(${tUrlEscaped}, '${t.replace(/'/g, "\\'")}'); } else { openModal(${movie.item_id}); }" aria-label="Play">
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
function generateAudienceMatch(movie) {
    const segments = new Set();
    const m = movie.rich_metadata || {};
    
    // Add mapping based on audience_type
    if (m.audience_type) {
        segments.add(`${m.audience_type} Viewers`);
    }

    // Map genres
    const genres = m.genres || m.tags || movie.genres || [];
    genres.forEach(g => {
        const gLower = g.toLowerCase();
        if (gLower.includes('sci-fi') || gLower.includes('science fiction')) {
            segments.add('Sci-Fi Fans');
        } else if (gLower.includes('action')) {
            segments.add('Action Lovers');
        } else if (gLower.includes('adventure')) {
            segments.add('Adventure Seekers');
        } else if (gLower.includes('thriller')) {
            segments.add('Thriller Enthusiasts');
        } else if (gLower.includes('drama')) {
            segments.add('Drama Enthusiasts');
        } else if (gLower.includes('comedy')) {
            segments.add('Comedy Lovers');
        } else if (gLower.includes('horror')) {
            segments.add('Horror Buffs');
        } else if (gLower.includes('romance')) {
            segments.add('Romance Fans');
        } else if (gLower.includes('mystery')) {
            segments.add('Mystery Solvers');
        } else if (gLower.includes('fantasy')) {
            segments.add('Fantasy Fans');
        } else if (gLower.includes('crime')) {
            segments.add('Crime Buffs');
        } else if (gLower.includes('documentary')) {
            segments.add('Doc Lovers');
        } else {
            segments.add(`${g} Fans`);
        }
    });

    // Map themes
    const themes = m.themes || [];
    themes.forEach(t => {
        const tLower = t.toLowerCase();
        if (tLower.includes('heroism') || tLower.includes('identity')) {
            segments.add('Superhero Fanatics');
        } else if (tLower.includes('space') || tLower.includes('multiverse') || tLower.includes('future') || tLower.includes('cyber')) {
            segments.add('Futurism Geeks');
        } else if (tLower.includes('survival') || tLower.includes('danger')) {
            segments.add('Survivalists');
        } else if (tLower.includes('family') || tLower.includes('friendship')) {
            segments.add('Family Audience');
        } else if (tLower.includes('crime') || tLower.includes('mystery') || tLower.includes('conspiracy')) {
            segments.add('Mystery Buffs');
        }
    });

    // Map moods
    const moods = m.moods || [];
    moods.forEach(md => {
        const mdLower = md.toLowerCase();
        if (mdLower.includes('exciting') || mdLower.includes('thrilling')) {
            segments.add('Adrenaline Junkies');
        } else if (mdLower.includes('emotional') || mdLower.includes('moving') || mdLower.includes('tear')) {
            segments.add('Melodrama Lovers');
        } else if (mdLower.includes('cerebral') || mdLower.includes('thought') || mdLower.includes('mind-bending')) {
            segments.add('Deep Thinkers');
        } else if (mdLower.includes('dark') || mdLower.includes('suspense')) {
            segments.add('Suspense Lovers');
        } else if (mdLower.includes('light') || mdLower.includes('feel-good')) {
            segments.add('Feel-Good Seekers');
        }
    });

    let result = Array.from(segments);

    // Safe genre-based fallback
    if (result.length < 3) {
        const fallbacks = ['Cinema Buffs', 'Storytelling Enthusiasts', 'Streamora Recommendation Seekers', 'Cinematic Experience Lovers'];
        genres.forEach(g => {
            const tag = `${g} Fans`;
            if (!result.includes(tag)) {
                result.push(tag);
            }
        });
        
        for (let f of fallbacks) {
            if (result.length >= 3) break;
            if (!result.includes(f)) {
                result.push(f);
            }
        }
    }

    return result.slice(0, 5);
}

function renderModalData(m, id) {
    // Cache title for history breadcrumbs
    window.modalMovieTitleCache = window.modalMovieTitleCache || {};
    window.modalMovieTitleCache[id] = m.title || 'Unknown';

    document.getElementById('modal-title').textContent = m.title || 'Unknown';
    
    const posterUrl = m.poster_url || placeholder(m.title);
    const bgUrl = m.backdrop_url || posterUrl;
    const posterImg = document.getElementById('modal-poster');
    const backdropEl = document.getElementById('modal-backdrop');
    
    // Hide until imageLoaded fires
    posterImg.style.display = 'none';
    
    // Add placeholder back to the container if it was removed in previous opens
    const posterContainer = posterImg.closest('.img-container');
    if (posterContainer && !posterContainer.querySelector('.img-placeholder')) {
        const placeholderDiv = document.createElement('div');
        placeholderDiv.className = 'img-placeholder';
        placeholderDiv.innerHTML = '<div class="blur-skeleton"></div>';
        posterContainer.insertBefore(placeholderDiv, posterImg);
    }
    
    posterImg.onerror = () => {
        posterImg.style.display = 'none';
        window.imageLoadError(posterImg, m.title || 'Poster');
    };
    posterImg.src = posterUrl;

    // Progressive Backdrop Loader
    backdropEl.classList.add('backdrop-loading');
    const tempImg = new Image();
    tempImg.onload = () => {
        backdropEl.style.backgroundImage = `url('${bgUrl}')`;
        backdropEl.classList.remove('backdrop-loading');
        backdropEl.classList.add('backdrop-loaded');
    };
    tempImg.onerror = () => {
        backdropEl.style.backgroundImage = 'linear-gradient(to bottom, rgba(15, 23, 42, 0.5), rgba(15, 23, 42, 1))';
        backdropEl.classList.remove('backdrop-loading');
    };
    tempImg.src = bgUrl;
    
    const typeLabel = isSeries({ item_id: id, rich_metadata: m, title: m.title }) ? 'TV Series' : 'Movie';
    document.getElementById('modal-match').innerHTML = `${m.match_percentage || 85}% Match <span style="margin-left: 8px; padding: 2px 6px; background: rgba(6, 182, 212, 0.15); border: 1px solid rgba(6, 182, 212, 0.3); border-radius: 4px; color: var(--streamora-cyan); font-size: 0.8rem; font-weight: 700; display: inline-block;">${typeLabel}</span>`;
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
    
    // Populate metadata grid and bottom details panel
    document.getElementById('modal-director').textContent = m.director || 'Unknown';
    document.getElementById('modal-writers').textContent = m.writer || m.writers || 'Unknown';
    document.getElementById('modal-producers').textContent = m.producer || m.producers || 'Unknown';
    document.getElementById('modal-studios').textContent = m.studio || m.studios || 'Unknown';
    document.getElementById('modal-countries').textContent = m.countries || 'Unknown';
    document.getElementById('modal-languages').textContent = m.languages || 'English';

    // Content-type adaptive metadata: show movie fields for movies, series fields for TV/anime/docs
    const isTVContent = ['series', 'anime', 'documentary'].includes((m.content_type || '').toLowerCase());
    document.querySelectorAll('.modal-movie-only').forEach(el => el.style.display = isTVContent ? 'none' : '');
    document.querySelectorAll('.modal-series-only').forEach(el => el.style.display = isTVContent ? '' : 'none');

    if (isTVContent) {
        // Series-specific fields
        const networkEl = document.getElementById('modal-network');
        const seasonsEl = document.getElementById('modal-seasons');
        const episodesEl = document.getElementById('modal-episodes');
        const statusEl = document.getElementById('modal-series-status');
        if (networkEl) networkEl.textContent = m.network || 'Unknown';
        if (seasonsEl) seasonsEl.textContent = m.seasons ? `${m.seasons} Season${m.seasons !== 1 ? 's' : ''}` : 'Unknown';
        if (episodesEl) episodesEl.textContent = m.episodes ? `${m.episodes} Episodes` : 'Unknown';
        if (statusEl) statusEl.textContent = m.series_status || 'Unknown';
    } else {
        // Movie-specific fields
        document.getElementById('modal-budget').textContent = m.budget || 'Undisclosed';
        document.getElementById('modal-revenue').textContent = m.revenue || 'Undisclosed';
        document.getElementById('modal-boxoffice').textContent = m.box_office || 'Undisclosed';
        document.getElementById('modal-franchise').textContent = m.franchise || 'Standalone';
    }

    document.getElementById('modal-awards').textContent = m.awards || 'None';
    document.getElementById('modal-availability').textContent = m.availability || 'Available on Streamora';

    const seedMovie = globalMovies.find(item => item.item_id === id) || FALLBACK_MOVIES.find(item => item.item_id === id) || { item_id: id, rich_metadata: m, title: m.title };

    // Render Audience Match Tags
    const audienceMatchContainer = document.getElementById('modal-audience-match');
    if (audienceMatchContainer) {
        const tags = generateAudienceMatch(seedMovie);
        audienceMatchContainer.innerHTML = tags.map(tag => `<span class="audience-tag">${tag}</span>`).join('');
    }

    // Render Cast Cards (from DB or fallback)
    const castContainer = document.getElementById('modal-cast');
    if (castContainer) {
        const castList = (m.cast && m.cast.length > 0) ? m.cast : getMovieCast(m.title);
        if (castList && castList.length > 0) {
            castContainer.innerHTML = castList.map(name => {
                const avatarUrl = `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=0D8ABC&color=fff&size=128&bold=true`;
                return `
                    <div class="cast-card">
                        <img src="${avatarUrl}" alt="${name}" class="cast-avatar">
                        <span class="cast-name">${name}</span>
                    </div>
                `;
            }).join('');
        } else {
            castContainer.innerHTML = `<div style="color: var(--text-muted); font-style: italic; font-size: 0.9rem; padding: 10px 0;">Cast information currently unavailable.</div>`;
        }
    }

    // Render responsive YouTube trailer
    const trailerWrapper = document.getElementById('modal-trailer-wrapper');
    if (trailerWrapper) {
        if (m.trailer_url) {
            trailerWrapper.innerHTML = `
                <iframe src="${m.trailer_url}" 
                        title="${m.title || 'Movie'} Official Trailer" 
                        frameborder="0" 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                        allowfullscreen>
                </iframe>
            `;
        } else {
            trailerWrapper.innerHTML = `
                <div class="modal-trailer-placeholder">
                    <svg viewBox="0 0 24 24" fill="currentColor" width="48" height="48"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                    <div style="margin-top: 10px; color: var(--text-muted); font-size: 0.9rem;">Trailer unavailable</div>
                </div>
            `;
        }
    }

    // Bind "Watch Trailer" button click
    const btnWatch = document.querySelector('.btn-watch');
    if (btnWatch) {
        // remove old listeners
        const newBtnWatch = btnWatch.cloneNode(true);
        btnWatch.parentNode.replaceChild(newBtnWatch, btnWatch);
        newBtnWatch.addEventListener('click', () => {
            if (m.trailer_url) {
                window.openTrailerLightbox(m.trailer_url, m.title);
            } else {
                alert("Trailer is currently unavailable.");
            }
        });
    }

    const simContainer = document.getElementById('modal-similar');
    if (simContainer) {
        // Initialize state for infinite recommendation traversal
        window.modalRenderedIds = new Set([parseInt(id)]);
        window.modalPendingRecs = [];
        window.modalExpandedSeedIds = new Set([parseInt(id)]);

        const recs = getSimilarRecommendations(seedMovie);
        if (recs && recs.length > 0) {
            window.modalPendingRecs = [...recs];
        }

        // Take the first 10 items
        const initialBatch = window.modalPendingRecs.splice(0, 10);
        if (initialBatch.length > 0) {
            simContainer.innerHTML = initialBatch.map(r => {
                const sm = r.movie;
                window.modalRenderedIds.add(parseInt(sm.item_id));
                const poster = sm.poster_url || placeholder(sm.title);
                const meta = sm.rich_metadata || {};
                const rating = meta.rating || '7.5';
                const year = meta.year || '2022';
                const genresList = (meta.genres || meta.tags || ['Drama']).slice(0, 2).join(' • ');
                const typeLabel = isSeries(sm) ? 'TV Series' : 'Movie';

                return `
                    <div class="sim-card" tabindex="0" onclick="openModal(${sm.item_id})" aria-label="${sm.title}, ${typeLabel}, Match ${r.score} percent, Rating ${rating}">
                        <img src="${poster}" alt="" class="sim-poster" loading="lazy" onerror="this.src='${placeholder(sm.title)}'">
                        <div class="sim-title">${sm.title}</div>
                        <div class="sim-meta-row" style="display:flex; justify-content:space-between; align-items:center; font-size:0.8rem; margin-top:2px;">
                            <span class="sim-match" style="color:var(--match-green); font-weight:700;">${r.score}% Match</span>
                            <span class="sim-type" style="color:var(--streamora-cyan); font-weight:600; font-size:0.75rem;">${typeLabel}</span>
                            <span class="sim-rating-imdb" style="color:#fbbf24;">★ ${rating}</span>
                        </div>
                        <div class="sim-genres-text" style="font-size:0.72rem; color:var(--text-muted); margin-top:2px;">${genresList} (${year})</div>
                        <div class="sim-reason" style="font-size: 0.68rem; color: var(--text-muted); text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding: 0 4px; margin-top:2px;" title="${r.reasoning}">${r.reasoning}</div>
                    </div>
                `;
            }).join('');

            // Attach infinite scroll loader and arrow state updater
            simContainer.addEventListener('scroll', () => {
                if (simContainer.scrollWidth - simContainer.scrollLeft - simContainer.clientWidth < 300) {
                    if (typeof window.loadMoreModalSimilar === 'function') {
                        window.loadMoreModalSimilar();
                    }
                }
                if (typeof window.updateCarouselArrows === 'function') {
                    window.updateCarouselArrows();
                }
            }, { passive: true });

            // Attach horizontal scrolling / dragging
            if (typeof window.setupHorizontalScroll === 'function') {
                window.setupHorizontalScroll(simContainer);
            }
            
            // Initial call to set arrow state
            setTimeout(() => {
                if (typeof window.updateCarouselArrows === 'function') {
                    window.updateCarouselArrows();
                }
            }, 100);
        } else {
            simContainer.innerHTML = '<p>No similar titles found.</p>';
        }
    }

    const addBtn = document.getElementById('modal-add-list');
    const saved = isInMyList(id);
    addBtn.innerHTML = saved ? `✓ Added` : `+ Add to List`;
    addBtn.onclick = () => {
        toggleSave(id);
        addBtn.innerHTML = isInMyList(id) ? `✓ Added` : `+ Add to List`;
    };

    if (typeof window.updateModalDownloadBtn === 'function') {
        window.updateModalDownloadBtn(id);
    }

    addToHistory({
        item_id: id,
        title: m.title || 'Unknown',
        poster_url: posterUrl,
        backdrop_url: bgUrl,
        rich_metadata: m
    });

    // Update navigation buttons and breadcrumbs
    window.updateBreadcrumbs();
    window.updateModalNavButtons();

    // Trigger fade in animation by removing transitioning class
    const cinematicModal = document.querySelector('.cinematic-modal');
    if (cinematicModal) {
        setTimeout(() => {
            cinematicModal.classList.remove('transitioning');
            const savedScroll = window.modalHistoryScrollPositions[window.modalHistoryIndex];
            if (savedScroll !== undefined) {
                cinematicModal.scrollTop = savedScroll;
            } else {
                cinematicModal.scrollTop = 0;
            }
        }, 50);
    }
}

// ── Modal History & Exploration Stack ──────────────────────────────────
window.modalHistory = [];
window.modalHistoryIndex = -1;
window.modalMovieTitleCache = {};

window.updateModalNavButtons = function() {
    const backBtn = document.getElementById('modal-back-btn');
    const forwardBtn = document.getElementById('modal-forward-btn');
    if (backBtn) {
        backBtn.disabled = window.modalHistoryIndex <= 0;
    }
    if (forwardBtn) {
        forwardBtn.disabled = window.modalHistoryIndex >= window.modalHistory.length - 1;
    }
};

window.updateBreadcrumbs = function() {
    const breadcrumbsContainer = document.getElementById('modal-breadcrumbs');
    if (!breadcrumbsContainer) return;
    
    if (!window.modalHistory || window.modalHistory.length <= 1) {
        breadcrumbsContainer.style.display = 'none';
        return;
    }
    
    breadcrumbsContainer.style.display = 'flex';
    
    const trail = window.modalHistory.map((histId, idx) => {
        const cachedTitle = window.modalMovieTitleCache[histId];
        const item = globalMovies.find(m => m.item_id === histId) || FALLBACK_MOVIES.find(m => m.item_id === histId);
        const title = cachedTitle || (item ? (item.title || item.rich_metadata?.title) : 'Loading...');
        
        const isActive = idx === window.modalHistoryIndex;
        if (isActive) {
            return `<span style="color: var(--streamora-cyan); font-weight: 600;">${title}</span>`;
        } else {
            return `<span style="cursor: pointer; text-decoration: none;" onclick="navigateModalHistory(${idx})">${title}</span>`;
        }
    }).join('<span style="color: rgba(255,255,255,0.2); margin: 0 4px;">&gt;</span>');
    
    breadcrumbsContainer.innerHTML = trail;
};

window.modalHistoryScrollPositions = {};

window.navigateModalHistory = function(index) {
    if (index >= 0 && index < window.modalHistory.length) {
        // Save current scroll position before leaving
        const cinematicModal = document.querySelector('.cinematic-modal');
        if (cinematicModal && window.modalHistoryIndex >= 0) {
            window.modalHistoryScrollPositions[window.modalHistoryIndex] = cinematicModal.scrollTop;
        }

        window.modalHistoryIndex = index;
        const id = window.modalHistory[index];
        openModalInternal(id, false);
    }
};

window.modalHistoryBack = function() {
    if (window.modalHistoryIndex > 0) {
        window.navigateModalHistory(window.modalHistoryIndex - 1);
    }
};

window.modalHistoryForward = function() {
    if (window.modalHistoryIndex < window.modalHistory.length - 1) {
        window.navigateModalHistory(window.modalHistoryIndex + 1);
    }
};

async function openModalInternal(id, appendToHistory = true) {
    // Save current scroll position before leaving
    const cinematicModal = document.querySelector('.cinematic-modal');
    if (cinematicModal && window.modalHistoryIndex >= 0) {
        window.modalHistoryScrollPositions[window.modalHistoryIndex] = cinematicModal.scrollTop;
    }

    if (appendToHistory) {
        const isModalAlreadyOpen = modalOverlay.classList.contains('active');
        if (!isModalAlreadyOpen) {
            window.modalHistory = [id];
            window.modalHistoryIndex = 0;
            window.modalHistoryScrollPositions = {}; // reset scroll positions on new open
        } else {
            if (window.modalHistory[window.modalHistoryIndex] !== id) {
                // Truncate forward history
                window.modalHistory = window.modalHistory.slice(0, window.modalHistoryIndex + 1);
                window.modalHistory.push(id);
                window.modalHistoryIndex = window.modalHistory.length - 1;
            }
        }
    }

    modalOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';

    // Update navigation controls
    window.updateModalNavButtons();
    window.updateBreadcrumbs();

    // Trigger transition fade-out
    if (cinematicModal) {
        cinematicModal.classList.add('transitioning');
        cinematicModal.scrollTop = 0;
    }

    // Set loading skeletons/placeholders in modal
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
        window.currentModalMovieData = m;
        window.currentModalMovieId = id;
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
            window.currentModalMovieData = fallbackDetails;
            window.currentModalMovieId = id;
            renderModalData(fallbackDetails, id);
        } else {
            document.getElementById('modal-title').textContent = 'Error loading details.';
            document.getElementById('modal-synopsis').textContent = 'Could not fetch data.';
        }
    }
}

async function openModal(id) {
    if (window.modalIsDragging) return;
    authFetch('/events/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_type: "click", item_id: id })
    }).catch(e => console.error("Event ingest failed:", e));
    
    openModalInternal(id, true);
}

window.toggleFavorite = function(id) {
    const idNum = parseInt(id);
    const movie = globalMovies.find(m => parseInt(m.item_id) === idNum) || 
                  FALLBACK_MOVIES.find(m => parseInt(m.item_id) === idNum) || 
                  myList.find(m => parseInt(m.item_id) === idNum);
    if (!movie) return;
    
    toggleMyList(movie);
    
    window.updateCardHearts(idNum);
    window.updateHeroSaveBtn(idNum);
    window.updateModalSaveBtn(idNum);
    
    if (currentPage === 'favorites' || currentPage === 'my-list') {
        renderFavoritesTab();
    }
};

window.updateCardHearts = function(id) {
    const isFav = isInMyList(id);
    const heartBtns = document.querySelectorAll(`.card-heart-btn[data-id="${id}"]`);
    heartBtns.forEach(btn => {
        btn.classList.toggle('favorited', isFav);
        btn.setAttribute('aria-label', isFav ? 'Remove from favorites' : 'Add to favorites');
        btn.style.color = isFav ? 'var(--streamora-cyan)' : 'white';
        btn.innerHTML = isFav 
            ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="var(--streamora-cyan)" stroke="var(--streamora-cyan)" stroke-width="1.5"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>`
            : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`;
    });
};

window.updateHeroSaveBtn = function(id) {
    const favBtn = document.querySelector(`.hero-fav-btn[data-id="${id}"]`);
    const watchlistBtn = document.querySelector(`.hero-watchlist-btn[data-id="${id}"]`);
    const isFav = isInMyList(id);
    
    if (favBtn) {
        favBtn.style.color = isFav ? 'var(--streamora-cyan)' : 'white';
        favBtn.innerHTML = isFav 
            ? `<svg width="22" height="22" viewBox="0 0 24 24" fill="var(--streamora-cyan)" stroke="var(--streamora-cyan)" stroke-width="1.5"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>`
            : `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`;
    }
    
    if (watchlistBtn) {
        watchlistBtn.style.color = isFav ? 'var(--streamora-cyan)' : 'white';
        watchlistBtn.innerHTML = isFav 
            ? `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--streamora-cyan)" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`
            : `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`;
    }
};

window.updateModalSaveBtn = function(id) {
    const addBtn = document.getElementById('modal-add-list');
    if (addBtn) {
        const isFav = isInMyList(id);
        addBtn.innerHTML = isFav ? `✓ Added` : `+ Add to List`;
    }
};

function toggleSave(id) {
    window.toggleFavorite(id);
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
    
    contentRows.innerHTML = skeletonRow;
}

function emptyStateHTML() {
    const cats = ['Sci-Fi','Action','Comedy','Drama','Thriller','Horror','Romance','Animation','Mystery'];
    return `
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:60vh;text-align:center;padding:0 20px;">
            <h2 style="font-size:2.2rem;font-weight:700;color:var(--text-primary);margin-bottom:12px;">What would you like to watch?</h2>
            <p style="color:var(--text-muted);margin-bottom:40px;max-width:500px;">Explore categories or ask Streamora AI for personalized recommendations.</p>
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
                    <span class="modal-info-value">Streamora Cinematic Premium (4K UHD)</span>
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
            const autoplay = localStorage.getItem('streamora_autoplay') !== 'false';
            const quality = localStorage.getItem('streamora_quality') || 'auto';
            const motion = localStorage.getItem('streamora_reduced_motion') === 'true';
            
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
            const currentTheme = localStorage.getItem('streamora_theme') || 'neon';
            html = `
                <h2>🎨 Theme Preferences</h2>
                <div class="modal-form-row">
                    <label style="display: flex; align-items: center; gap: 10px; cursor: pointer;">
                        <input type="radio" name="theme-choice" value="neon" ${currentTheme === 'neon' ? 'checked' : ''} style="width: 20px; height: 20px;">
                        <span>Streamora Neon (Default Cyberpunk)</span>
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
                        <h4 style="color:white; margin-bottom:6px;">Q: How does Streamora AI recommend movies?</h4>
                        <p style="font-size:0.9rem; line-height:1.4; color:var(--text-secondary)">A: Streamora uses vector embeddings to understand movie themes and match them to your taste based on click signals.</p>
                    </div>
                    <div>
                        <h4 style="color:white; margin-bottom:6px;">Q: How do I save items to my watchlist?</h4>
                        <p style="font-size:0.9rem; line-height:1.4; color:var(--text-secondary)">A: Tap the "+" button on any movie card or details panel. It saves instantly.</p>
                    </div>
                    <div>
                        <h4 style="color:white; margin-bottom:6px;">Q: Can I use conversational search?</h4>
                        <p style="font-size:0.9rem; line-height:1.4; color:var(--text-secondary)">A: Yes! Open the Search tab to chat directly with the Streamora Assistant, e.g. "Suggest some dark thrillers".</p>
                    </div>
                </div>
                <button class="modal-submit-btn" onclick="closeDrawerModalDirect()">Done</button>
            `;
            break;
        case 'logout':
            html = `
                <h2>🚪 Log Out</h2>
                <p style="color:var(--text-secondary); margin-bottom:24px; line-height:1.5;">Are you sure you want to log out of Streamora AI?</p>
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
    
    localStorage.setItem('streamora_autoplay', autoplay);
    localStorage.setItem('streamora_quality', quality);
    localStorage.setItem('streamora_reduced_motion', motion);
    
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
    token = null;
    userId = null;
    userProfile = null;
    isGuest = false;
    localStorage.removeItem('streamora_jwt');
    localStorage.removeItem('streamora_profile');
    showAuthScreen();
};

// ══════════════════════════════════════════════════════════════════════
//  EDGE-AWARE DYNAMIC CARD EXPANSION
// ══════════════════════════════════════════════════════════════════════
document.addEventListener('mouseenter', (e) => {
    const cardWrap = e.target.closest('.card-wrap');
    if (!cardWrap) return;
    
    const cardExpand = cardWrap.querySelector('.card-expand');
    if (!cardExpand) return;
    
    cardExpand.classList.remove('expand-left-edge', 'expand-right-edge', 'expand-center');
    
    const cardRect = cardWrap.getBoundingClientRect();
    const expandWidth = 340; // width of expanded card in CSS
    const overflowLeft = cardRect.left - (expandWidth - cardRect.width) / 2;
    const overflowRight = cardRect.right + (expandWidth - cardRect.width) / 2;
    
    if (overflowLeft < 15) {
        cardExpand.classList.add('expand-left-edge');
    } else if (overflowRight > window.innerWidth - 15) {
        cardExpand.classList.add('expand-right-edge');
    } else {
        cardExpand.classList.add('expand-center');
    }
}, true);

document.addEventListener('mouseleave', (e) => {
    const cardWrap = e.target.closest('.card-wrap');
    if (!cardWrap) return;
    
    const cardExpand = cardWrap.querySelector('.card-expand');
    if (cardExpand) {
        cardExpand.classList.remove('expand-left-edge', 'expand-right-edge', 'expand-center');
    }
}, true);

// ══════════════════════════════════════════════════════════════════════
//  DRAG-TO-SCROLL, WHEEL SCROLL, & MOMENTUM PHYSICS
// ══════════════════════════════════════════════════════════════════════
window.modalIsDragging = false;

window.setupHorizontalScroll = function(el) {
    if (!el) return;
    
    // 1. Mouse wheel horizontal scrolling
    el.addEventListener('wheel', (e) => {
        if (e.deltaY !== 0) {
            e.preventDefault();
            el.scrollLeft += e.deltaY;
        }
    }, { passive: false });
    
    // 2. Drag-to-scroll with momentum physics
    let isDown = false;
    let startX;
    let scrollLeft;
    let velocity = 0;
    let lastTime = 0;
    let lastX = 0;
    let animationFrameId = null;
    let isMoving = false;

    el.addEventListener('mousedown', (e) => {
        // Only trigger drag on left-click and if not clicking a link/button directly
        if (e.button !== 0) return;
        if (e.target.closest('button') || e.target.closest('a')) return;
        
        isDown = true;
        isMoving = false;
        el.classList.add('dragging');
        startX = e.pageX - el.offsetLeft;
        scrollLeft = el.scrollLeft;
        lastX = e.pageX;
        lastTime = Date.now();
        velocity = 0;
        if (animationFrameId) cancelAnimationFrame(animationFrameId);
    });

    el.addEventListener('mouseleave', () => {
        if (!isDown) return;
        isDown = false;
        el.classList.remove('dragging');
        applyMomentum();
    });

    el.addEventListener('mouseup', () => {
        if (!isDown) return;
        isDown = false;
        el.classList.remove('dragging');
        if (isMoving) {
            window.modalIsDragging = true;
            setTimeout(() => { window.modalIsDragging = false; }, 50);
        }
        applyMomentum();
    });

    el.addEventListener('mousemove', (e) => {
        if (!isDown) return;
        e.preventDefault();
        const x = e.pageX - el.offsetLeft;
        const walk = (x - startX) * 1.5;
        const diff = Math.abs(x - lastX);
        if (diff > 4) {
            isMoving = true;
        }
        el.scrollLeft = scrollLeft - walk;
        
        // Calculate instantaneous velocity
        const now = Date.now();
        const dt = now - lastTime;
        if (dt > 0) {
            velocity = (e.pageX - lastX) / dt;
            lastX = e.pageX;
            lastTime = now;
        }
    });

    function applyMomentum() {
        if (Math.abs(velocity) < 0.1) return;
        el.scrollLeft -= velocity * 15;
        velocity *= 0.92; // friction deceleration factor
        animationFrameId = requestAnimationFrame(applyMomentum);
    }
};

// ══════════════════════════════════════════════════════════════════════
//  INFINITE SIMILAR TITLES Discovery Traversal
// ══════════════════════════════════════════════════════════════════════
window.modalLoadingMore = false;

window.loadMoreModalSimilar = function() {
    if (window.modalLoadingMore) return;
    window.modalLoadingMore = true;
    
    // If we are running low on pending scored recommendations, query similar movies of already rendered movies
    if (window.modalPendingRecs.length < 5) {
        const renderedIdsArr = Array.from(window.modalRenderedIds);
        let newSeedFound = false;
        
        for (let rId of renderedIdsArr) {
            if (!window.modalExpandedSeedIds.has(rId)) {
                // Find this movie item in global database
                const nextSeed = globalMovies.find(m => parseInt(m.item_id) === rId) || 
                                 FALLBACK_MOVIES.find(m => parseInt(m.item_id) === rId);
                if (nextSeed) {
                    window.modalExpandedSeedIds.add(rId);
                    const newRecs = window.getSimilarRecommendations(nextSeed);
                    // Filter out duplicates (already rendered in this rail)
                    const filtered = newRecs.filter(r => !window.modalRenderedIds.has(parseInt(r.movie.item_id)));
                    window.modalPendingRecs.push(...filtered);
                    newSeedFound = true;
                    break;
                }
            }
        }
        
        // Fallback to random global movies if similarity traversal is completely exhausted
        if (!newSeedFound && window.modalPendingRecs.length === 0) {
            const allMovies = [...(globalMovies || []), ...FALLBACK_MOVIES];
            const fallbackRecs = allMovies
                .filter(m => !window.modalRenderedIds.has(parseInt(m.item_id)))
                .slice(0, 10)
                .map(m => ({
                    movie: m,
                    score: 72,
                    reasoning: "Trending discovery recommendation"
                }));
            window.modalPendingRecs.push(...fallbackRecs);
        }
    }
    
    // Take the next 5 items and append to the rail
    const nextBatch = window.modalPendingRecs.splice(0, 5);
    if (nextBatch.length > 0) {
        const simContainer = document.getElementById('modal-similar');
        if (simContainer) {
            nextBatch.forEach(r => {
                const sm = r.movie;
                const rId = parseInt(sm.item_id);
                if (window.modalRenderedIds.has(rId)) return;
                window.modalRenderedIds.add(rId);
                
                const poster = sm.poster_url || placeholder(sm.title);
                const meta = sm.rich_metadata || {};
                const rating = meta.rating || '7.5';
                const year = meta.year || '2022';
                const genresList = (meta.genres || meta.tags || ['Drama']).slice(0, 2).join(' • ');
                const typeLabel = isSeries(sm) ? 'TV Series' : 'Movie';
                
                const cardHtml = `
                    <div class="sim-card" tabindex="0" onclick="openModal(${sm.item_id})" aria-label="${sm.title}, ${typeLabel}, Match ${r.score} percent, Rating ${rating}">
                        <img src="${poster}" alt="" class="sim-poster" loading="lazy" onerror="this.src='${placeholder(sm.title)}'">
                        <div class="sim-title">${sm.title}</div>
                        <div class="sim-meta-row" style="display:flex; justify-content:space-between; align-items:center; font-size:0.8rem; margin-top:2px;">
                            <span class="sim-match" style="color:var(--match-green); font-weight:700;">${r.score}% Match</span>
                            <span class="sim-type" style="color:var(--streamora-cyan); font-weight:600; font-size:0.75rem;">${typeLabel}</span>
                            <span class="sim-rating-imdb" style="color:#fbbf24;">★ ${rating}</span>
                        </div>
                        <div class="sim-genres-text" style="font-size:0.72rem; color:var(--text-muted); margin-top:2px;">${genresList} (${year})</div>
                        <div class="sim-reason" style="font-size: 0.68rem; color: var(--text-muted); text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding: 0 4px; margin-top:2px;" title="${r.reasoning}">${r.reasoning}</div>
                    </div>
                `;
                
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = cardHtml;
                simContainer.appendChild(tempDiv.firstElementChild);
            });
            if (typeof window.updateCarouselArrows === 'function') {
                window.updateCarouselArrows();
            }
        }
    }
    
    window.modalLoadingMore = false;
};

// ══════════════════════════════════════════════════════════════════════
//  CAROUSEL UPGRADES: Navigation, Edge Fades & Accessibility
// ══════════════════════════════════════════════════════════════════════

/**
 * Scroll the recommendation carousel by direction (1 for right, -1 for left)
 * Scrolls by approximately 2 recommendation card widths (~320px)
 */
window.scrollSimilarCarousel = function(direction) {
    const simContainer = document.getElementById('modal-similar');
    if (simContainer) {
        const scrollAmount = 320 * direction;
        simContainer.scrollBy({
            left: scrollAmount,
            behavior: 'smooth'
        });
    }
};

/**
 * Update the visibility of Left/Right scroll arrows and side gradient overlays
 * based on the container's current scrollLeft offset.
 */
window.updateCarouselArrows = function() {
    const simContainer = document.getElementById('modal-similar');
    const containerWrapper = document.getElementById('modal-similar-container');
    
    if (simContainer && containerWrapper) {
        const leftArrow = containerWrapper.querySelector('.carousel-arrow--left');
        const rightArrow = containerWrapper.querySelector('.carousel-arrow--right');
        
        const scrollLeft = simContainer.scrollLeft;
        const scrollWidth = simContainer.scrollWidth;
        const clientWidth = simContainer.clientWidth;
        
        // Left scroll status
        if (scrollLeft > 4) {
            if (leftArrow) leftArrow.style.display = 'flex';
            containerWrapper.classList.add('has-left-scroll');
        } else {
            if (leftArrow) leftArrow.style.display = 'none';
            containerWrapper.classList.remove('has-left-scroll');
        }
        
        // Right scroll status (use buffer for subpixels / rounding)
        if (scrollLeft + clientWidth < scrollWidth - 4) {
            if (rightArrow) rightArrow.style.display = 'flex';
            containerWrapper.classList.add('has-right-scroll');
        } else {
            if (rightArrow) rightArrow.style.display = 'none';
            containerWrapper.classList.remove('has-right-scroll');
        }
    }
};

// Edge-Awareness Hover Scaling: Determine transform-origin dynamically on hover / focus
const updateTransformOrigin = (e) => {
    const card = e.target.closest('.sim-card');
    if (!card) return;
    
    const container = document.getElementById('modal-similar');
    if (!container) return;
    
    const containerRect = container.getBoundingClientRect();
    const cardRect = card.getBoundingClientRect();
    
    const leftDist = cardRect.left - containerRect.left;
    const rightDist = containerRect.right - cardRect.right;
    
    // Threshold to switch transform-origins (in pixels)
    const edgeThreshold = 40;
    
    if (leftDist < edgeThreshold) {
        card.style.transformOrigin = 'left center';
    } else if (rightDist < edgeThreshold) {
        card.style.transformOrigin = 'right center';
    } else {
        card.style.transformOrigin = 'center center';
    }
};

// Capture-phase listeners to support dynamic recommendations loading
document.addEventListener('mouseenter', updateTransformOrigin, true);
document.addEventListener('focusin', updateTransformOrigin, true);

// Accessibility Keyboard Navigation: Arrow Keys to traverse, Enter/Space to select
document.addEventListener('keydown', (e) => {
    const card = e.target.closest('.sim-card');
    if (!card) return;
    
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        e.preventDefault();
        const cards = Array.from(document.querySelectorAll('#modal-similar .sim-card'));
        const index = cards.indexOf(card);
        if (index !== -1) {
            const nextIndex = index + (e.key === 'ArrowRight' ? 1 : -1);
            if (nextIndex >= 0 && nextIndex < cards.length) {
                const nextCard = cards[nextIndex];
                nextCard.focus();
                nextCard.scrollIntoView({
                    behavior: 'smooth',
                    block: 'nearest',
                    inline: 'nearest'
                });
            }
        }
    } else if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        card.click();
    }
});

// ── Cinematic Trailer Lightbox Overlay Controller ────────────────────
window.openTrailerLightbox = function(url, title) {
    if (!url) return;
    
    let embedUrl = url;
    if (embedUrl.includes('youtube.com/embed/')) {
        if (!embedUrl.includes('?')) {
            embedUrl += '?autoplay=1&mute=0';
        } else if (!embedUrl.includes('autoplay=')) {
            embedUrl += '&autoplay=1&mute=0';
        }
    }
    
    const lightbox = document.getElementById('trailer-lightbox');
    const wrapper = document.getElementById('lightbox-video-wrapper');
    if (lightbox && wrapper) {
        wrapper.innerHTML = `
            <iframe src="${embedUrl}" 
                    title="${title || 'Trailer'}" 
                    frameborder="0" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                    allowfullscreen>
            </iframe>
        `;
        lightbox.style.display = 'flex';
        lightbox.offsetHeight; // force reflow
        lightbox.classList.add('active');
    }
};

window.closeTrailerLightbox = function() {
    const lightbox = document.getElementById('trailer-lightbox');
    const wrapper = document.getElementById('lightbox-video-wrapper');
    if (lightbox) {
        lightbox.classList.remove('active');
        setTimeout(() => {
            lightbox.style.display = 'none';
            if (wrapper) wrapper.innerHTML = '';
        }, 300);
    }
};
