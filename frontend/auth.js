const Auth = (() => {
    const TOKEN_KEY = "nook_token";
    
    // Automatically detect if running locally or on a production host
    const API_BASE = window.location.origin.includes("127.0.0.1") || window.location.origin.includes("localhost")
        ? "http://127.0.0.1:5000"
        : window.location.origin;

    console.log("ðŸ” AUTH MODULE LOADED");
    console.log("   API Base:", API_BASE);

    function getToken() {
        return localStorage.getItem(TOKEN_KEY);
    }

    function setToken(token) {
        localStorage.setItem(TOKEN_KEY, token);
        console.log("âœ… Token saved");
    }

    function clearToken() {
        localStorage.removeItem(TOKEN_KEY);
        console.log("ðŸ—‘ï¸ Token cleared");
    }

    function isAuthenticated() {
        const hasToken = !!getToken();
        console.log("ðŸ” Is Authenticated:", hasToken);
        return hasToken;
    }

    async function apiCall(url, options = {}) {
        const fullUrl = url.startsWith("/") ? `${API_BASE}${url}` : url;

        console.log("ðŸ“¡ API Call:", fullUrl, options.method || 'GET');

        const headers = {
            "Content-Type": "application/json",
            ...(options.headers || {})
        };

        const token = getToken();
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        try {
            const res = await fetch(fullUrl, { ...options, headers });
            
            console.log("ðŸ“¥ Response:", res.status, res.statusText);

            if (res.status === 401 || res.status === 403) {
                console.warn("ðŸš« Unauthorized - clearing token");
                if (!window.location.pathname.includes("login.html")) {
                    clearToken();
                    window.location.href = "login.html";
                }
            }

            return res;
        } catch (error) {
            console.error("âŒ API Call Failed:", error.message);
            throw error;
        }
    }

    async function getCurrentUser() {
        if (!isAuthenticated()) {
            console.log("ðŸ‘¤ No token - not authenticated");
            return null;
        }
        
        try {
            console.log("ðŸ‘¤ Fetching current user...");
            const res = await apiCall("/api/auth/me");
            if (!res.ok) {
                console.warn("âš ï¸ Failed to get user:", res.status);
                return null;
            }
            const user = await res.json();
            console.log("âœ… User loaded:", user.alias || user.email);
            return user;
        } catch (error) {
            console.error("âŒ Error getting user:", error);
            return null;
        }
    }

    function loginSuccess(token) {
        console.log("ðŸŽ‰ Login successful - redirecting to homepage");
        setToken(token);
        setTimeout(() => {
            window.location.href = "nook_homepage_final.html";
        }, 100);
    }

    function logout() {
        console.log("ðŸ‘‹ Logging out - redirecting to homepage");
        clearToken();
        setTimeout(() => {
            window.location.href = "nook_homepage_final.html";
        }, 100);
    }

    return {
        isAuthenticated,
        apiCall,
        getCurrentUser,
        loginSuccess,
        logout
    };
})();

/**
 * Updates UI elements (names and login/logout buttons) based on current user
 */
async function bootstrapAuth({ requireAuth = false } = {}) {
    console.log("ðŸš€ Bootstrap Auth - requireAuth:", requireAuth);
    
    // Check authentication
    const isAuth = Auth.isAuthenticated();
    console.log("   Authenticated:", isAuth);
    
    if (requireAuth && !isAuth) {
        console.log("ðŸ”’ Auth required but not logged in - redirecting to login");
        window.location.href = "login.html";
        return;
    }

    // Get current user data
    const user = await Auth.getCurrentUser();
    window.currentUser = user;
    
    console.log("   Current user:", user ? (user.alias || user.email) : "Guest");

    // Update all elements with data-user-name
    document.querySelectorAll("[data-user-name]").forEach(el => {
        const displayName = user ? (user.alias || user.full_name || "Explorer") : "Guest";
        el.textContent = displayName;
        console.log("   Updated user name display:", displayName);
    });

    // Update all auth action buttons
    document.querySelectorAll("[data-auth-action]").forEach(btn => {
        if (user) {
            btn.textContent = "Logout";
            btn.onclick = (e) => { 
                e.preventDefault(); 
                console.log("ðŸšª Logout button clicked");
                Auth.logout(); 
            };
        } else {
            btn.textContent = "Login";
            btn.onclick = (e) => { 
                e.preventDefault(); 
                console.log("ðŸ”‘ Login button clicked");
                window.location.href = "login.html"; 
            };
        }
    });
    
    console.log("âœ… Bootstrap complete");
}

export { bootstrapAuth };
export default Auth;