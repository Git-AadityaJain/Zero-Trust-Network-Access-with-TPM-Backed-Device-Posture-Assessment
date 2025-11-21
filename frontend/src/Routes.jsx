import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';

import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import PendingDevicesPage from './pages/PendingDevicesPage';
import NotFoundPage from './pages/NotFoundPage';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

const RoleBasedRoute = ({ children, requiredRole }) => {
  const { hasRole, loading } = useAuth();

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  if (!hasRole(requiredRole)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

export default function AppRoutes() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/devices/pending"
          element={
            <ProtectedRoute>
              <RoleBasedRoute requiredRole="admin">
                <PendingDevicesPage />
              </RoleBasedRoute>
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Router>
  );
}