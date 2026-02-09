// ===================================
// AUTHENTICATION MANAGER (COOKIE-BASED)
// ===================================

const AUTH_CONFIG = {
    LOGIN_URL: '/auth/login',
    API_PREFIX: '/auth/api'
};

// ===================================
// STATE MANAGEMENT
// ===================================

const AuthState = {
    user: null,
    isAuthenticated: false,
    isRefreshing: false,
    refreshSubscribers: []
};

// ===================================
// CORE FUNCTIONS
// ===================================

/**
 * Check if the user is currently authenticated by asking the server.
 * Since we use HTTP-only cookies, we can't check localStorage.
 */
async function checkAuthStatus() {
    try {
        const response = await fetch(`${AUTH_CONFIG.API_PREFIX}/check-auth`);
        const data = await response.json();

        if (data.authenticated) {
            AuthState.isAuthenticated = true;
            AuthState.user = data.user;
            console.log('✅ User is authenticated:', data.user.username);
            updateUI(true);
        } else {
            AuthState.isAuthenticated = false;
            AuthState.user = null;
            console.log('ℹ️ User is not authenticated');
            updateUI(false);
        }
        return data.authenticated;
    } catch (error) {
        console.error('❌ Failed to check auth status:', error);
        AuthState.isAuthenticated = false;
        return false;
    }
}

/**
 * Update UI elements based on auth state
 */
function updateUI(isAuthenticated) {
    const guestElements = document.querySelectorAll('.auth-guest-only');
    const userElements = document.querySelectorAll('.auth-user-only');

    if (isAuthenticated) {
        guestElements.forEach(el => el.classList.add('d-none'));
        userElements.forEach(el => el.classList.remove('d-none'));

        // Update username displays
        document.querySelectorAll('.auth-username').forEach(el => {
            if (AuthState.user) el.textContent = AuthState.user.username;
        });
    } else {
        guestElements.forEach(el => el.classList.remove('d-none'));
        userElements.forEach(el => el.classList.add('d-none'));
    }
}

// ===================================
// REFRESH LOGIC
// ===================================

function onTokenRefreshed(success) {
    AuthState.refreshSubscribers.forEach(callback => callback(success));
    AuthState.refreshSubscribers = [];
}

async function refreshAccessToken() {
    if (AuthState.isRefreshing) {
        return new Promise((resolve) => {
            AuthState.refreshSubscribers.push(resolve);
        });
    }

    AuthState.isRefreshing = true;

    try {
        console.log('🔄 Attempting to refresh access token...');
        // The refresh token is in an HTTP-only cookie, sent automatically
        const response = await fetch(`${AUTH_CONFIG.API_PREFIX}/refresh`, {
            method: 'POST'
        });

        if (response.ok) {
            console.log('✅ Token refresh successful');
            onTokenRefreshed(true);
            AuthState.isRefreshing = false;
            return true;
        } else {
            console.error('❌ Token refresh failed');
            onTokenRefreshed(false);
            AuthState.isRefreshing = false;
            return false;
        }
    } catch (error) {
        console.error('❌ Error during token refresh:', error);
        onTokenRefreshed(false);
        AuthState.isRefreshing = false;
        return false;
    }
}

// ===================================
// AUTHENTICATED FETCH
// ===================================

/**
 * Wrapper around fetch that handles 401 errors by attempting to refresh the token.
 */
async function authenticatedFetch(url, options = {}) {
    options.headers = options.headers || {};
    options.headers['Content-Type'] = 'application/json';

    // Note: No need to add Authorization header manually, cookies are sent automatically
    // Ensure credentials are sent (important for CORS if applicable, but good practice)
    options.credentials = 'same-origin';

    try {
        let response = await fetch(url, options);

        if (response.status === 401) {
            console.log('⚠️ Request failed with 401, attempting refresh...');

            const refreshSuccess = await refreshAccessToken();

            if (refreshSuccess) {
                console.log('🔄 Retrying original request...');
                response = await fetch(url, options);
            } else {
                console.log('⛔ Refresh failed, redirecting to login');
                window.location.href = `${AUTH_CONFIG.LOGIN_URL}?next=${encodeURIComponent(window.location.pathname)}`;
                return null;
            }
        }

        return response;
    } catch (error) {
        console.error('❌ Fetch error:', error);
        throw error;
    }
}

// ===================================
// LOGOUT
// ===================================

async function logout() {
    try {
        await fetch(`${AUTH_CONFIG.API_PREFIX}/logout`, {
            method: 'POST'
        });
    } catch (error) {
        console.error('Logout error:', error);
    }

    AuthState.user = null;
    AuthState.isAuthenticated = false;
    window.location.href = AUTH_CONFIG.LOGIN_URL;
}

// ===================================
// INITIALIZATION
// ===================================

document.addEventListener('DOMContentLoaded', () => {
    // Only check auth if we are NOT on the login/register page
    if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
        checkAuthStatus();
    }
});

// ===================================
// EXPORTS
// ===================================

window.authenticatedFetch = authenticatedFetch;
window.logout = logout;
window.checkAuthStatus = checkAuthStatus;