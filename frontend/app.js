const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const chatHistory = document.getElementById('chat-history');
const movieGrid = document.getElementById('movie-grid');
const emptySearchState = document.getElementById('empty-search-state');
const autocompleteDropdown = document.getElementById('autocomplete-dropdown');
const userIdInput = document.getElementById('user-id-input');

// Modal Elements
const modalOverlay = document.getElementById('movie-detail-modal');
const modalBody = document.getElementById('modal-body');
const closeModalBtn = document.getElementById('close-modal-btn');

closeModalBtn.addEventListener('click', () => {
    modalOverlay.style.display = 'none';
});

function addMessage(text, type) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', type);
    msgDiv.innerHTML = text;
    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function openCinematicModal(movie) {
    const encodedTitle = encodeURIComponent((movie.title || 'Unknown Title').split(' (')[0]);
    const posterUrl = movie.poster_url || `https://placehold.co/300x450/111111/66fcf1?text=${encodedTitle}`;
    const backdropUrl = movie.backdrop_url || posterUrl;
    const meta = movie.rich_metadata || {};
    
    let tagsHtml = (meta.tags || ['Trending', 'Must Watch']).map(t => `<span class="tag">${t}</span>`).join('');
    
    modalBody.innerHTML = `
        <div class="modal-hero" style="background-image: url('${backdropUrl}');">
            <div class="modal-hero-overlay">
                <img src="${posterUrl}" class="modal-poster" alt="${movie.title}">
                <div class="modal-hero-text">
                    <h2 class="modal-title">${movie.title}</h2>
                    <p class="modal-tagline">${meta.tagline || ''}</p>
                    <div class="hero-meta">
                        <span>${meta.year || '2024'}</span>
                        <span>${meta.content_rating || 'PG-13'}</span>
                        <span>${meta.runtime || '120 min'}</span>
                        <span class="match-score">${meta.match_percentage || Math.floor(Math.random() * 20 + 80)}% Match</span>
                    </div>
                    <div class="tags-container" style="margin-bottom: 0;">${tagsHtml}</div>
                </div>
            </div>
        </div>
        <div class="modal-body-content">
            <div class="modal-main-col">
                <div class="modal-section">
                    <h3>Story</h3>
                    <p>${meta.story_summary || movie.overview || 'A captivating cinematic experience.'}</p>
                </div>
                <div class="modal-section">
                    <h3>Why Aurora Recommended This</h3>
                    <p style="color: var(--primary); font-style: italic;">
                        ${movie.explanation || meta.why_recommended || 'Because it strongly aligns with your recent viewing patterns and genre preferences.'}
                    </p>
                </div>
            </div>
            <div class="modal-side-col">
                <div class="modal-section">
                    <h3>Cast & Crew</h3>
                    <p><strong>Director:</strong> ${meta.director || 'Unknown'}</p>
                    <p style="margin-top: 10px;"><strong>Starring:</strong><br>${meta.main_cast || 'Various Artists'}</p>
                </div>
            </div>
        </div>
    `;
    modalOverlay.style.display = 'flex';
}

function renderMovies(movies) {
    emptySearchState.style.display = 'none';
    movieGrid.style.display = 'flex';
    movieGrid.innerHTML = '';
    
    if (!movies || movies.length === 0) {
        movieGrid.innerHTML = '<p>No matching content found.</p>';
        return;
    }

    movies.forEach((movie, index) => {
        const card = document.createElement('div');
        
        // Render #1 as Hero Card
        if (index === 0) {
            card.classList.add('hero-card');
        } else {
            card.classList.add('movie-card');
        }
        
        card.onclick = () => {
            openCinematicModal(movie);
            // Fire feedback in background
            fetch('http://127.0.0.1:8001/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: parseInt(userIdInput.value),
                    item_id: movie.item_id || 0,
                    label: 1.0
                })
            }).catch(console.error);
        };

        const encodedTitle = encodeURIComponent((movie.title || 'Unknown Title').split(' (')[0]);
        const posterUrl = movie.poster_url || `https://placehold.co/300x450/111111/66fcf1?text=${encodedTitle}`;
        const backdropUrl = movie.backdrop_url || posterUrl;
        const meta = movie.rich_metadata || {};
        let tagsHtml = (meta.tags || ['Trending', 'Must Watch']).map(t => `<span class="tag">${t}</span>`).join('');
        
        if (index === 0) {
            // Hero Card UI
            card.style.backgroundImage = `url('${backdropUrl}')`;
            card.innerHTML = `
                <div class="hero-overlay">
                    <h3 class="hero-title">${movie.title}</h3>
                    <div class="hero-meta">
                        <span class="match-score" style="margin-left: 0;">${meta.match_percentage || 98}% Match</span>
                        <span>${meta.year || '2024'}</span>
                        <span>${meta.runtime || '120m'}</span>
                    </div>
                    <div class="tags-container" style="margin-bottom: 15px;">${tagsHtml}</div>
                    <p class="hero-synopsis">${meta.story_summary || movie.overview || 'An exceptional recommendation tailored to your exact tastes.'}</p>
                    <div class="why-recommended" style="max-width: 600px;">
                        <strong>Why Aurora Recommended This:</strong>
                        <p>${movie.explanation || meta.why_recommended || 'This is your absolute best match right now.'}</p>
                    </div>
                </div>
            `;
        } else {
            // Standard Hover Card UI
            let hoverHtml = `
                <div class="hover-overlay">
                    <div class="hover-backdrop" style="background-image: url('${backdropUrl}'); height: 80px; background-size: cover; border-radius: 4px; margin-bottom: 8px;"></div>
                    <div class="hover-content">
                        <div class="hover-header">
                            <h4>${meta.title || movie.title}</h4>
                            <span class="match-score">${meta.match_percentage || Math.floor(Math.random() * 20 + 70)}% Match</span>
                        </div>
                        <div class="hover-meta">
                            <span>${meta.year || '2024'}</span>
                            <span>${meta.runtime || '120 min'}</span>
                        </div>
                        <div class="tags-container">${tagsHtml}</div>
                        <p class="story-summary">${meta.story_summary || movie.overview || 'A captivating journey through new worlds.'}</p>
                        <div class="why-recommended">
                            <strong>Why we recommend this:</strong>
                            <p>${movie.explanation || meta.why_recommended || 'High thematic similarity to your preferences.'}</p>
                        </div>
                    </div>
                </div>`;

            card.innerHTML = `
                <img src="${posterUrl}" class="movie-poster" alt="${movie.title}" onerror="this.src='https://placehold.co/300x450/111111/66fcf1?text=No+Poster'">
                <div class="movie-info">
                    <h3>${movie.title || 'Unknown Title'}</h3>
                    <p>Rank #${index + 1}</p>
                </div>
                ${hoverHtml}
            `;
        }
        movieGrid.appendChild(card);
    });
}

function renderEmptyState() {
    movieGrid.style.display = 'none';
    emptySearchState.style.display = 'flex';
    emptySearchState.innerHTML = `
        <h2 style="margin-bottom: 20px;">Explore Aurora</h2>
        <div style="display: flex; gap: 15px; flex-wrap: wrap;">
            <div class="category-pill" onclick="chatInput.value='What is trending?'; handleSend();">🔥 Trending Now</div>
            <div class="category-pill" onclick="chatInput.value='Recommend me some action movies'; handleSend();">💥 Action Picks</div>
            <div class="category-pill" onclick="chatInput.value='Show me psychological thrillers'; handleSend();">🧠 Psychological Thrillers</div>
            <div class="category-pill" onclick="chatInput.value='Recommend me some comedies'; handleSend();">😂 Comedies</div>
            <div class="category-pill" onclick="chatInput.value='Movies for the family'; handleSend();">👨‍👩‍👧 Family Favorites</div>
        </div>
    `;
}

async function handleSend() {
    const query = chatInput.value.trim();
    if (!query) return;

    const userId = parseInt(userIdInput.value) || 32;

    addMessage(query, 'user-msg');
    chatInput.value = '';
    autocompleteDropdown.style.display = 'none';
    
    movieGrid.style.display = 'block';
    emptySearchState.style.display = 'none';
    movieGrid.innerHTML = '<div class="loading-spinner"></div>';

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_id: userId, query: query })
        });

        const data = await response.json();
        
        if (data.intent === 'explanation') {
            addMessage(`<b>Explanation:</b><br>${data.response}`, 'system-msg');
            movieGrid.innerHTML = '';
        } else {
            if (Array.isArray(data.response)) {
                renderMovies(data.response);
            } else if (data.response && Array.isArray(data.response.value)) {
                 renderMovies(data.response.value);
            } else {
                movieGrid.innerHTML = '';
                addMessage(typeof data.response === 'string' ? data.response : JSON.stringify(data.response), 'system-msg');
            }
        }

    } catch (error) {
        addMessage(`We're having trouble loading recommendations right now. Please try again shortly.`, 'system-msg');
        movieGrid.innerHTML = '';
        console.error(error);
    }
}

// Autocomplete Logic
let autocompleteTimeout;
chatInput.addEventListener('input', (e) => {
    const q = e.target.value.trim();
    if (q.length < 2) {
        autocompleteDropdown.style.display = 'none';
        return;
    }
    
    clearTimeout(autocompleteTimeout);
    autocompleteTimeout = setTimeout(async () => {
        try {
            const resp = await fetch(`/autocomplete?q=${encodeURIComponent(q)}`);
            if (resp.ok) {
                const results = await resp.json();
                if (results.length > 0) {
                    autocompleteDropdown.innerHTML = results.map(r => `
                        <div class="autocomplete-item" onclick="chatInput.value='Similar to ${r}'; autocompleteDropdown.style.display='none'; handleSend();">
                            ${r}
                        </div>
                    `).join('');
                    autocompleteDropdown.style.display = 'block';
                } else {
                    autocompleteDropdown.style.display = 'none';
                }
            }
        } catch (err) {
            console.error("Autocomplete error", err);
        }
    }, 300);
});

sendBtn.addEventListener('click', handleSend);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSend();
});

// Load empty state on startup
window.onload = () => {
    renderEmptyState();
};
