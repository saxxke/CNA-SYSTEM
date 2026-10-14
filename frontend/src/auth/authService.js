import api from '../api/client';

const TOKEN_KEY = 'anweshan_intel_token';

/**
 * Encapsulated auth storage and API service.
 * Follows strict MVP browser-session approach:
 * - Stores bearer token in localStorage.
 * - Never stores plaintext password or password_hash.
 * - Role and user identity are always verified via backend GET /api/auth/me.
 */
export const authService = {
  getToken() {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },

  setToken(token) {
    try {
      if (token) {
        localStorage.setItem(TOKEN_KEY, token);
      }
    } catch (e) {
      console.error('Failed to persist authentication token', e);
    }
  },

  removeToken() {
    try {
      localStorage.removeItem(TOKEN_KEY);
    } catch (e) {
      console.error('Failed to remove authentication token', e);
    }
  },

  /**
   * Authenticates user credentials against POST /api/auth/login
   * @param {string} username
   * @param {string} password
   * @returns {Promise<{token: string, token_type: string, user: object}>}
   */
  async login(username, password) {
    const response = await api.post('/api/auth/login', {
      username: username.trim(),
      password: password
    });

    const data = response.data;
    if (data && data.token) {
      this.setToken(data.token);
    }
    return data;
  },

  /**
   * Rehydrates and verifies current user identity via GET /api/auth/me
   * The backend remains the authoritative source of the user's role and identity.
   * @returns {Promise<object>} UserPublic
   */
  async getMe() {
    const response = await api.get('/api/auth/me');
    return response.data;
  },

  /**
   * Logs out user by revoking server session and clearing local state.
   */
  async logout() {
    try {
      await api.post('/api/auth/logout');
    } catch {
      // If server session is already expired/invalid, proceed with local cleanup
    } finally {
      this.removeToken();
    }
  }
};

export default authService;
