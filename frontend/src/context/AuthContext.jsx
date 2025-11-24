import React, { createContext, useState, useEffect } from 'react';
import oidcService from '../services/oidcService';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        if (oidcService.isAuthenticated()) {
          const storedUser = localStorage.getItem('user_info');
          if (storedUser) {
            const userData = JSON.parse(storedUser);
            setUser(userData);
            setIsAuthenticated(true);
          } else {
            // Try to get user info from token
            const token = oidcService.getAccessToken();
            if (token) {
              const userInfo = await oidcService.getUserInfo(token);
              setUser(userInfo);
              setIsAuthenticated(true);
              localStorage.setItem('user_info', JSON.stringify(userInfo));
            }
          }
        } else {
          // Try to refresh token
          try {
            await oidcService.refreshToken();
            const storedUser = localStorage.getItem('user_info');
            if (storedUser) {
              setUser(JSON.parse(storedUser));
              setIsAuthenticated(true);
            }
          } catch (e) {
            setIsAuthenticated(false);
          }
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();

    // Set up token refresh interval
    const interval = setInterval(async () => {
      if (oidcService.isAuthenticated()) {
        try {
          await oidcService.refreshToken();
        } catch (e) {
          console.error('Token refresh failed:', e);
        }
      }
    }, 5 * 60 * 1000); // Refresh every 5 minutes

    return () => clearInterval(interval);
  }, []);

  const login = async () => {
    try {
      await oidcService.login();
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const handleCallback = async (code) => {
    try {
      const result = await oidcService.handleCallback(code);
      if (result && result.userInfo && result.access_token) {
        setUser(result.userInfo);
        setIsAuthenticated(true);
        return result; // Return full result, not just userInfo
      } else {
        throw new Error('Invalid result from authentication service');
      }
    } catch (error) {
      console.error('Callback handling failed:', error);
      setIsAuthenticated(false);
      setUser(null);
      throw error;
    }
  };

  const logout = async () => {
    // Clear local state first
    setUser(null);
    setIsAuthenticated(false);
    // Then call Keycloak logout (which will redirect)
    await oidcService.logout();
  };

  const hasRole = (role) => {
    const roles = oidcService.getRoles();
    const hasAccess = roles.includes(role) || false;
    
    // Debug logging (remove in production)
    if (!hasAccess) {
      console.log(`Access denied: User roles [${roles.join(', ')}] do not include required role: ${role}`);
    }
    
    return hasAccess;
  };

  const getAccessToken = () => {
    return oidcService.getAccessToken();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated,
        login,
        logout,
        hasRole,
        handleCallback,
        getAccessToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};