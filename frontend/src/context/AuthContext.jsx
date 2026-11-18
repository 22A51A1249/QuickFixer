import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    try {
      const stored = sessionStorage.getItem('quickfixer_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState(() => sessionStorage.getItem('quickfixer_token'));
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const verifyAuth = async () => {
      const storedToken = sessionStorage.getItem('quickfixer_token');
      if (storedToken) {
        try {
          const freshUser = await authService.getMe();
          setUser(freshUser);
          sessionStorage.setItem('quickfixer_user', JSON.stringify(freshUser));
        } catch (err) {
          console.warn('Session verification failed, logging out:', err);
          setUser(null);
          setToken(null);
          sessionStorage.removeItem('quickfixer_token');
          sessionStorage.removeItem('quickfixer_user');
        }
      }
      setIsLoading(false);
    };

    verifyAuth();
  }, []);

  const login = async (usernameOrEmail, password, role = null, customId = null) => {
    setIsLoading(true);
    try {
      const data = await authService.login(usernameOrEmail, password, role, customId);
      sessionStorage.setItem('quickfixer_token', data.token);
      sessionStorage.setItem('quickfixer_user', JSON.stringify(data.user));
      setToken(data.token);
      setUser(data.user);
      return data.user;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
    } finally {
      setUser(null);
      setToken(null);
      sessionStorage.removeItem('quickfixer_token');
      sessionStorage.removeItem('quickfixer_user');
    }
  };

  const value = {
    user,
    token,
    isAuthenticated: !!user && !!token,
    isLoading,
    login,
    logout,
    isAdmin: user?.role === 'admin',
    isTechnician: user?.role === 'technician',
    isEmployee: user?.role === 'employee',
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

