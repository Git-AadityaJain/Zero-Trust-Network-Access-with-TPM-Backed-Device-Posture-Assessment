import React, { createContext, useState, useEffect } from 'react';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem('auth_token');
      const storedUser = localStorage.getItem('user_info');

      if (token && storedUser) {
        setUser(JSON.parse(storedUser));
        setIsAuthenticated(true);
      } else {
        setIsAuthenticated(false);
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = (username, password) => {
    const mockUser = {
      id: 'user-123',
      username,
      email: `${username}@company.com`,
      roles: ['admin', 'user'],
    };
    localStorage.setItem('auth_token', 'mock-token-' + Date.now());
    localStorage.setItem('user_info', JSON.stringify(mockUser));
    setUser(mockUser);
    setIsAuthenticated(true);
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
    setUser(null);
    setIsAuthenticated(false);
  };

  const hasRole = (role) => {
    return user?.roles?.includes(role) || false;
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