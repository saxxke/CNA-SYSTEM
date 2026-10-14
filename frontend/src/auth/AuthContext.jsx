import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import authService from './authService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Initialize and rehydrate user session from stored token
  const rehydrateSession = useCallback(async () => {
    const token = authService.getToken();
    if (!token) {
      setCurrentUser(null);
      setLoading(false);
      return;
    }

    try {
      // Backend /api/auth/me is the authoritative source of role & identity
      const user = await authService.getMe();
      if (user && user.active) {
        setCurrentUser(user);
      } else {
        authService.removeToken();
        setCurrentUser(null);
      }
    } catch {
      // Expired, invalid, or revoked token
      authService.removeToken();
      setCurrentUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    rehydrateSession();

    // Listen to custom session expired event from axios interceptor
    const handleSessionExpired = () => {
      authService.removeToken();
      setCurrentUser(null);
    };

    window.addEventListener('auth:session_expired', handleSessionExpired);
    return () => {
      window.removeEventListener('auth:session_expired', handleSessionExpired);
    };
  }, [rehydrateSession]);

  const login = async (username, password) => {
    // 1. Authenticate credentials via POST /api/auth/login
    const loginData = await authService.login(username, password);
    
    // 2. Authoritative identity verification via GET /api/auth/me
    const verifiedUser = await authService.getMe();
    setCurrentUser(verifiedUser);
    return verifiedUser;
  };

  const logout = async () => {
    try {
      await authService.logout();
    } finally {
      setCurrentUser(null);
    }
  };

  const role = currentUser?.role || null;
  const isAuthenticated = Boolean(currentUser && currentUser.active);

  const value = {
    currentUser,
    role,
    isAuthenticated,
    loading,
    login,
    logout,
    rehydrateSession
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
