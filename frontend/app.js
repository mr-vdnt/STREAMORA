const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const chatHistory = document.getElementById('chat-history');
const movieGrid = document.getElementById('movie-grid');
const userIdInput = document.getElementById('user-id-input');

function addMessage(text, type) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', type);
    msgDiv.innerHTML = text;
    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function renderMovies(movies) {
    movieGrid.innerHTML = '';
    if (!movies || movies.length === 0) {
        movieGrid.innerHTML = '<p>No matching content found.</p>';
        return;
    }

    movies.forEach(movie => {
        const card = document.createElement('div');
        card.classList.add('movie-card');
        
        card.onclick = () => {
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

        let subtitle = movie.score ? `Score: ${movie.score.toFixed(2)}` : 
                      (movie.ranking_score ? `Rank: ${movie.ranking_score.toFixed(2)}` : '');
                      
        const encodedTitle = encodeURIComponent((movie.title || 'Unknown Title').split(' (')[0]);
        const posterUrl = movie.poster_url || `https://placehold.co/300x450/111111/66fcf1?text=${encodedTitle}`;
        const backdropUrl = movie.backdrop_url || posterUrl;
        
        let hoverHtml = '';
        if (movie.rich_metadata || movie.title) {
            const meta = movie.rich_metadata || {};
            let tagsHtml = (meta.tags || ['Trending', 'Must Watch']).map(t => `<span class="tag">${t}</span>`).join('');
            
            hoverHtml = `
            <div class="hover-overlay">
                <div class="hover-backdrop" style="background-image: url('${backdropUrl}'); height: 80px; background-size: cover; border-radius: 4px; margin-bottom: 8px;"></div>
                <div class="hover-content">
                    <div class="hover-header">
                        <h4>${meta.title || movie.title}</h4>
                        <span class="match-score">${meta.match_percentage || Math.floor(Math.random() * 20 + 80)}% Match</span>
                    </div>
                    <div class="hover-meta">
                        <span>${meta.year || '2024'}</span>
                        <span>${meta.content_rating || 'PG-13'}</span>
                        <span>${meta.runtime || '120 min'}</span>
                        <span>${meta.language || 'EN'}</span>
                    </div>
                    <div class="tags-container">
                        ${tagsHtml}
                    </div>
                    <p class="story-summary">${meta.story_summary || movie.overview || 'A captivating journey through new worlds.'}</p>
                    <div class="bottom-meta" style="margin-top: 5px; font-size: 0.75rem;">
                        <div><span style="color:#fff">Cast:</span> ${meta.main_cast || 'Various Artists'}</div>
                        <div><span style="color:#fff">Dir:</span> ${meta.director || 'Unknown'}</div>
                    </div>
                    <div class="why-recommended" style="margin-top: 5px;">
                        <strong>Why we recommend this:</strong>
                        <p>${movie.explanation || meta.why_recommended || 'Because you enjoy engaging stories and high-quality production.'}</p>
                    </div>
                </div>
            </div>`;
        }

        card.innerHTML = `
            <img src="${posterUrl}" class="movie-poster" alt="${movie.title}" onerror="this.src='https://placehold.co/300x450/111111/66fcf1?text=No+Poster'">
            <h3>${movie.title || 'Unknown Title'}</h3>
            <p>${subtitle}</p>
            ${hoverHtml}
        `;
        movieGrid.appendChild(card);
    });
}

async function handleSend() {
    const query = chatInput.value.trim();
    if (!query) return;

    const userId = parseInt(userIdInput.value) || 32;

    addMessage(query, 'user-msg');
    chatInput.value = '';
    
    // Show loading state
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
            // REMOVED 'Intent detected:' logging
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

sendBtn.addEventListener('click', handleSend);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSend();
});

// Load trending on startup
window.onload = () => {
    chatInput.value = "What is trending?";
    handleSend();
};
