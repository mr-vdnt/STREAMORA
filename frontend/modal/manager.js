// frontend/modal/manager.js

class ModalManager {
    constructor() {
        this.overlay = document.getElementById('modal-overlay');
        this.container = document.querySelector('.cinematic-modal');
        this.closeBtn = document.getElementById('close-modal-btn');
        this.isOpen = false;

        this.init();
    }

    init() {
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => {
                this.close();
            });
        }
        
        // Ensure global functions proxy to the manager
        window.closeModal = () => this.close();
        
        // Important: app.js contains the fetchModalContent logic inside the old openModal. 
        // So we will redefine it later in app.js or here. We will just expose our logic.
        window.modalManager = this;
    }

    open(id, type = 'movie', pushState = false) {
        if (window.modalIsDragging) return;
        this.isOpen = true;
        
        if (window.DEBUG_MODE) {
            console.log(`[Diagnostic] Requested ID: ${id}`);
        }
        window.activeModalRequest = id;
        
        if (window.authFetch) {
            window.authFetch('/events/ingest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ event_type: "click", item_id: id })
            }).catch(e => console.error("Event ingest failed:", e));
        }

        if (window.ModalAccessibility) {
            window.ModalAccessibility.onOpen(this.container);
        }

        if (window.ModalAnimation) {
            window.ModalAnimation.onOpen(this.overlay, this.container);
        }
    }

    close() {
        this.isOpen = false;
        
        if (window.ModalAccessibility) {
            window.ModalAccessibility.onClose();
        }

        if (window.ModalAnimation) {
            window.ModalAnimation.onClose(this.overlay);
        }

        if (window.history.state && window.history.state.page === 'movie') {
            history.back();
        } else {
            if (window.navigateHome) window.navigateHome();
        }
    }
    
    closeInternal(pushState = false) {
        this.isOpen = false;
        if (window.ModalAccessibility) window.ModalAccessibility.onClose();
        if (window.ModalAnimation) window.ModalAnimation.onClose(this.overlay);
        
        if (pushState && window.navigateHome) {
            window.navigateHome();
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.modalManager = new ModalManager();
    window.closeModalInternal = (pushState) => window.modalManager.closeInternal(pushState);
});
