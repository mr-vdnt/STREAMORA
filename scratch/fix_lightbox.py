import os

app_path = r'c:\Users\vedan\OneDrive\Attachments\Documents\GitHub\aurora-ai\frontend\app.js'

with open(app_path, 'r', encoding='utf-8') as f:
    app_code = f.read()

lightbox_functions = """
// -----------------------------------------------------------------------------
// Cinematic Trailer Lightbox
// -----------------------------------------------------------------------------
window.openTrailerLightbox = function(url, title) {
    const lightbox = document.getElementById('trailer-lightbox');
    const wrapper = document.getElementById('lightbox-video-wrapper');
    if (!lightbox || !wrapper || !url) {
        alert("Trailer is currently unavailable.");
        return;
    }
    
    // Auto-play the YouTube video and ensure high quality
    let embedUrl = url;
    if (embedUrl.includes('?')) {
        embedUrl += '&autoplay=1&rel=0&modestbranding=1&vq=hd1080';
    } else {
        embedUrl += '?autoplay=1&rel=0&modestbranding=1&vq=hd1080';
    }
    
    wrapper.innerHTML = `
        <iframe src="${embedUrl}"
                title="${title} Official Trailer"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen
                style="width: 100%; height: 100%; position: absolute; top: 0; left: 0;">
        </iframe>
    `;
    
    lightbox.classList.add('active');
    document.body.style.overflow = 'hidden';
};

window.closeTrailerLightbox = function() {
    const lightbox = document.getElementById('trailer-lightbox');
    const wrapper = document.getElementById('lightbox-video-wrapper');
    if (lightbox) {
        lightbox.classList.remove('active');
    }
    if (wrapper) {
        // Clear iframe to stop playback immediately
        wrapper.innerHTML = '';
    }
    document.body.style.overflow = '';
};
"""

if 'window.openTrailerLightbox = function' not in app_code:
    with open(app_path, 'a', encoding='utf-8') as f:
        f.write(lightbox_functions)
    print("Added openTrailerLightbox and closeTrailerLightbox to app.js")
else:
    print("window.openTrailerLightbox = function already exists in app.js")
