// frontend/modal/animation.js

class ModalAnimation {
    onOpen(overlayElement, containerElement) {
        if (overlayElement) {
            overlayElement.classList.add('active');
        }
        
        if (containerElement) {
            // Trigger transition fade-out/fade-in if re-rendering
            containerElement.classList.add('transitioning');
            containerElement.scrollTop = 0;
            
            // Allow CSS transition to finish, then remove class
            // This is primarily for the content changing animation
            setTimeout(() => {
                containerElement.classList.remove('transitioning');
            }, 300);
        }
    }

    onClose(overlayElement) {
        if (overlayElement) {
            overlayElement.classList.remove('active');
        }
    }
}

window.ModalAnimation = new ModalAnimation();
