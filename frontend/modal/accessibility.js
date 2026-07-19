// frontend/modal/accessibility.js

class ModalAccessibility {
    constructor() {
        this.lastActiveElement = null;
        this.init();
    }

    init() {
        // Global escape listener
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const modalOverlay = document.getElementById('modal-overlay');
                if (modalOverlay && modalOverlay.classList.contains('active')) {
                    if (window.modalManager) {
                        window.modalManager.close();
                    } else if (window.closeModal) {
                        window.closeModal();
                    }
                } else {
                    if (window.closeSearch) window.closeSearch();
                    const aiPanel = document.getElementById('ai-panel');
                    if (aiPanel) aiPanel.classList.remove('open');
                }
            }
        });
    }

    onOpen(containerElement) {
        this.lastActiveElement = document.activeElement;
        document.body.classList.add('modal-open');
        document.body.style.overflow = 'hidden';
        
        if (containerElement) {
            containerElement.focus();
        }
    }

    onClose() {
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        
        if (this.lastActiveElement) {
            this.lastActiveElement.focus();
            this.lastActiveElement = null;
        }
    }
}

window.ModalAccessibility = new ModalAccessibility();
