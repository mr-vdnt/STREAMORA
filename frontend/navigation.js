// navigation.js
// Handles HTML5 History API routing and centralized navigation

const ROUTES = {
    HOME: '/',
    MOVIE: '/movie/',
    TV: '/tv/',
    CATEGORY: '/category/'
};

/**
 * Initializes routing and popstate listener.
 */
function initRouter() {
    window.addEventListener('popstate', handlePopState);
    
    // Check initial route on load
    handleRoute(window.location.pathname);
}

/**
 * Parses the current path and triggers appropriate UI updates.
 */
function handleRoute(path) {
    if (path.startsWith(ROUTES.MOVIE)) {
        const id = path.replace(ROUTES.MOVIE, '');
        if (id) {
            window.modalManager.open(parseInt(id, 10), 'movie', false); // false = do not push state again
        }
    } else if (path.startsWith(ROUTES.TV)) {
        const id = path.replace(ROUTES.TV, '');
        if (id) {
            window.modalManager.open(parseInt(id, 10), 'tv', false);
        }
    } else if (path.startsWith(ROUTES.CATEGORY)) {
        const id = path.replace(ROUTES.CATEGORY, '');
        if (id) {
            // Un-escape URL path
            const categoryName = decodeURIComponent(id);
            if (window.loadSingleCategoryPage) {
                window.loadSingleCategoryPage(categoryName, false);
            }
        }
    } else if (path === ROUTES.HOME || path === '') {
        window.modalManager.closeInternal(false);
        if (window.selectedCategory) {
            window.selectedCategory = null;
            if (window.loadCategoriesTab) window.loadCategoriesTab();
        }
    }
}

/**
 * Handles the browser's back/forward buttons.
 */
function handlePopState(event) {
    handleRoute(window.location.pathname);
}

/**
 * Centralized navigation function to go to an item's detail view.
 */
function navigateToItem(type, id) {
    const route = type === 'tv' ? `${ROUTES.TV}${id}` : `${ROUTES.MOVIE}${id}`;
    
    if (window.location.pathname !== route) {
        history.pushState({ type, id }, '', route);
    }
    
    window.modalManager.open(id, type, false);
}

/**
 * Navigates back to the home view.
 */
function navigateHome() {
    if (window.location.pathname !== ROUTES.HOME) {
        history.pushState(null, '', ROUTES.HOME);
    }
    window.modalManager.closeInternal(false);
    if (window.selectedCategory) {
        window.selectedCategory = null;
        if (window.loadCategoriesTab) window.loadCategoriesTab();
    }
}

/**
 * Navigates to a category discovery page
 */
function navigateToCategory(categoryName) {
    const route = `${ROUTES.CATEGORY}${encodeURIComponent(categoryName)}`;
    if (window.location.pathname !== route) {
        history.pushState({ category: categoryName }, '', route);
    }
    if (window.loadSingleCategoryPage) {
        window.loadSingleCategoryPage(categoryName, false);
    }
}

/**
 * Temporary wrapper for backward compatibility inside existing components if needed.
 * But we should update all onclick handlers to use navigateToItem directly.
 */
function navigateToMovie(id) {
    navigateToItem('movie', id);
}

// Attach to window
window.initRouter = initRouter;
window.navigateToItem = navigateToItem;
window.navigateHome = navigateHome;
window.navigateToMovie = navigateToMovie;
window.navigateToCategory = navigateToCategory;
