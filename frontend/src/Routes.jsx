import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';

import LoginPage from './pages/LoginPage';
import CallbackPage from './pages/CallbackPage';
import Dashboard from './pages/Dashboard';
import DevicesPage from './pages/DevicesPage';
import DeviceDetailPage from './pages/DeviceDetailPage';
import PendingDevicesPage from './pages/PendingDevicesPage';
import UsersPage from './pages/UsersPage';
import RolesPage from './pages/RolesPage';
import PoliciesPage from './pages/PoliciesPage';
import AuditLogsPage from './pages/AuditLogsPage';
import AccessLogsPage from './pages/AccessLogsPage';
import EnrollmentCodesPage from './pages/EnrollmentCodesPage';
import UserDashboard from './pages/UserDashboard';
import NotFoundPage from './pages/NotFoundPage';
import Layout from './components/Layout';

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
  const { hasRole, loading, isAuthenticated } = useAuth();

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!hasRole(requiredRole)) {
    // Non-admin users go to user dashboard
    return <Navigate to="/user-dashboard" replace />;
  }

  return children;
};

const RootRedirect = () => {
  const { isAuthenticated, hasRole, loading } = useAuth();

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Redirect based on role
  if (hasRole('admin')) {
    return <Navigate to="/dashboard" replace />;
  } else {
    return <Navigate to="/user-dashboard" replace />;
  }
};

export default function AppRoutes() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<RootRedirect />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/callback" element={<CallbackPage />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <RoleBasedRoute requiredRole="admin">
                <Layout>
                  <Dashboard />
                </Layout>
              </RoleBasedRoute>
            </ProtectedRoute>
          }
        />

        <Route
          path="/devices"
          element={
            <ProtectedRoute>
              <Layout>
                <DevicesPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/devices/pending"
          element={
            <ProtectedRoute>
              <RoleBasedRoute requiredRole="admin">
                <Layout>
                  <PendingDevicesPage />
                </Layout>
              </RoleBasedRoute>
            </ProtectedRoute>
          }
        />

        <Route
          path="/devices/:id"
          element={
            <ProtectedRoute>
              <Layout>
                <DeviceDetailPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/users"
          element={
            <ProtectedRoute>
              <RoleBasedRoute requiredRole="admin">
                <Layout>
                  <UsersPage />
                </Layout>
              </RoleBasedRoute>
            </ProtectedRoute>
          }
        />

        <Route
          path="/roles"
          element={
            <ProtectedRoute>
              <RoleBasedRoute requiredRole="admin">
                <Layout>
                  <RolesPage />
                </Layout>
              </RoleBasedRoute>
            </ProtectedRoute>
          }
        />

        <Route
          path="/policies"
          element={
            <ProtectedRoute>
              <Layout>
                <PoliciesPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/audit"
          element={
            <ProtectedRoute>
              <Layout>
                <AuditLogsPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/access"
          element={
            <ProtectedRoute>
              <Layout>
                <AccessLogsPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/enrollment"
          element={
            <ProtectedRoute>
              <RoleBasedRoute requiredRole="admin">
                <Layout>
                  <EnrollmentCodesPage />
                </Layout>
              </RoleBasedRoute>
            </ProtectedRoute>
          }
        />

        <Route
          path="/user-dashboard"
          element={
            <ProtectedRoute>
              <Layout>
                <UserDashboard />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Router>
  );
}