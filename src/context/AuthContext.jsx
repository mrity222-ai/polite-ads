import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi } from '../api/auth';
const AuthContext = createContext(null);
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isCheckingSession, setIsCheckingSession] = useState(true);
  const [authError, setAuthError] = useState(null);
  const checkSession = useCallback(async () => {
    setIsCheckingSession(true);
    try { const current = await authApi.getMe(); setUser(current); setAuthError(null); return current; }
    catch (error) {
      if ([401, 403].includes(error.status)) { setUser(null); setAuthError(null); }
      else setAuthError(error.message);
      return null;
    } finally { setIsCheckingSession(false); }
  }, []);
  useEffect(() => {
    void Promise.resolve().then(checkSession);
    const invalid = (event) => { setUser(null); setAuthError(event.detail || 'Session unavailable. Please log in again.'); };
    window.addEventListener('politiads:session-invalid', invalid);
    return () => window.removeEventListener('politiads:session-invalid', invalid);
  }, [checkSession]);
  const login = async (data) => { const result = await authApi.login(data); setUser(result.user); setAuthError(null); return result.user; };
  const superAdminLogin = async (data) => { const result = await authApi.superAdminLogin(data); setUser(result.user); setAuthError(null); return result.user; };
  const register = async (data) => { const result = await authApi.register(data); setUser(result.user); setAuthError(null); return result.user; };
  const logout = async () => { await authApi.logout(); setUser(null); setAuthError(null); };
  return <AuthContext.Provider value={{ user, setUser, isCheckingSession, authError, setAuthError, login, superAdminLogin, register, logout, checkSession, isAuthenticated: !!user, isAdmin: user?.role === 'admin', isCandidate: user?.role === 'candidate' }}>{children}</AuthContext.Provider>;
}
// Context hook intentionally lives alongside its provider.
// eslint-disable-next-line react/only-export-components
export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth requires AuthProvider');
  return value;
}
