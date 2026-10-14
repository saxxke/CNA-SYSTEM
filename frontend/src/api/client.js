import axios from 'axios';

const TOKEN_KEY = 'anweshan_intel_token';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor: attach bearer token if available
api.interceptors.request.use(
  (config) => {
    try {
      const token = localStorage.getItem(TOKEN_KEY);
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch {
      // localStorage may fail in restricted environments
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401 Unauthorized globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Exclude initial login attempts so login error displays to user
      const isLoginRequest = error.config?.url?.includes('/api/auth/login');
      if (!isLoginRequest) {
        try {
          localStorage.removeItem(TOKEN_KEY);
        } catch {
          // ignore
        }
        window.dispatchEvent(new CustomEvent('auth:session_expired'));
      }
    }
    return Promise.reject(error);
  }
);

export default api;
