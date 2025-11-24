import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Layout({ children }) {
  const { user, logout, hasRole } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const navigation = [
    { name: 'Dashboard', path: '/dashboard', icon: '📊', role: 'admin' },
    { name: 'Resources', path: '/user-dashboard', icon: '📁', hideIfAdmin: true },
    { name: 'Devices', path: '/devices', icon: '💻', role: 'admin' },
    { name: 'Pending Devices', path: '/devices/pending', icon: '⏳', role: 'admin' },
    { name: 'Enrollment Codes', path: '/enrollment', icon: '🔑', role: 'admin' },
    { name: 'Users', path: '/users', icon: '👥', role: 'admin' },
    { name: 'Roles', path: '/roles', icon: '🎭', role: 'admin' },
    { name: 'Policies', path: '/policies', icon: '📋', role: 'admin' },
    { name: 'Audit Logs', path: '/audit', icon: '📝', role: 'admin' },
    { name: 'Access Logs', path: '/access', icon: '🔐', role: 'admin' },
  ];

  const handleLogout = async () => {
    // logout() will handle Keycloak logout and redirect to /login
    // No need to navigate manually as Keycloak will redirect
    await logout();
  };

  const isActive = (path) => {
    return location.pathname === path;
  };

  const filteredNavigation = navigation.filter((item) => {
    // Hide admin-only items if user doesn't have admin role
    if (item.role && !hasRole(item.role)) {
      return false;
    }
    // Hide user dashboard if user is admin
    if (item.hideIfAdmin && hasRole('admin')) {
      return false;
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-gray-900 text-white transition-transform duration-300 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-6 border-b border-gray-800">
            <div className="flex items-center space-x-2">
              <div className="text-2xl">🔒</div>
              <span className="text-xl font-bold">ZTNA</span>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
            {filteredNavigation.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive(item.path)
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`}
              >
                <span className="text-xl">{item.icon}</span>
                <span className="font-medium">{item.name}</span>
              </Link>
            ))}
          </nav>

          {/* User Info */}
          <div className="border-t border-gray-800 p-4">
            <div className="flex items-center space-x-3 mb-3">
              <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                {user?.preferred_username?.charAt(0).toUpperCase() || 'U'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">
                  {user?.preferred_username || user?.name || 'User'}
                </p>
                <p className="text-xs text-gray-400 truncate">
                  {user?.email || ''}
                </p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="w-full bg-gray-800 hover:bg-gray-700 text-white py-2 px-4 rounded-lg transition-colors text-sm font-medium"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Content */}
      <div className="lg:pl-64">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-30">
          <div className="flex items-center justify-between h-16 px-6">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden text-gray-600 hover:text-gray-900"
            >
              ☰
            </button>
            <div className="flex-1" />
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                {user?.preferred_username || 'User'}
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}

