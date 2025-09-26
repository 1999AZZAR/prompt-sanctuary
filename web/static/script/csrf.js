/**
 * CSRF Token Utility
 * Provides consistent CSRF token retrieval across all JavaScript files
 */

(function() {
    'use strict';

    // Global CSRF utility object
    window.CSRF = window.CSRF || {};

    /**
     * Get CSRF token from cookie
     * @returns {string|null} The CSRF token or null if not found
     */
    window.CSRF.getToken = function() {
        try {
            const match = document.cookie.match(/(?:^|; )csrf_token=([^;]+)/);
            if (match) {
                return decodeURIComponent(match[1]);
            }
            return null;
        } catch (error) {
            console.warn('Error getting CSRF token:', error);
            return null;
        }
    };

    /**
     * Get CSRF token from cookie with fallback methods
     * @returns {string} The CSRF token or empty string if not found
     */
    window.CSRF.getTokenSafe = function() {
        try {
            const token = window.CSRF.getToken();
            return token || '';
        } catch (error) {
            console.warn('Error getting CSRF token safely:', error);
            return '';
        }
    };

    /**
     * Create headers object with CSRF token
     * @param {Object} additionalHeaders - Additional headers to include
     * @returns {Object} Headers object with CSRF token
     */
    window.CSRF.getHeaders = function(additionalHeaders = {}) {
        const headers = {
            'X-CSRFToken': window.CSRF.getTokenSafe(),
            ...additionalHeaders
        };
        return headers;
    };

    /**
     * Create headers object for JSON requests with CSRF token
     * @returns {Object} Headers object for JSON requests
     */
    window.CSRF.getJsonHeaders = function() {
        return window.CSRF.getHeaders({
            'Content-Type': 'application/json'
        });
    };

    /**
     * Create headers object for form data requests with CSRF token
     * @returns {Object} Headers object for form data requests
     */
    window.CSRF.getFormHeaders = function() {
        return window.CSRF.getHeaders();
    };

    /**
     * Check if CSRF token exists
     * @returns {boolean} True if CSRF token exists
     */
    window.CSRF.hasToken = function() {
        return window.CSRF.getToken() !== null;
    };

    /**
     * Legacy function for backward compatibility
     * @returns {string|null} The CSRF token or null if not found
     */
    function getCsrfTokenFromCookie() {
        return window.CSRF.getToken();
    }

    // Expose legacy function for backward compatibility
    window.getCsrfTokenFromCookie = getCsrfTokenFromCookie;

    // Debug logging in development
    if (typeof console !== 'undefined' && console.log) {
        const token = window.CSRF.getToken();
        if (token) {
            console.debug('CSRF token loaded:', token.substring(0, 10) + '...');
        } else {
            console.warn('No CSRF token found in cookies');
        }
    }

})();
