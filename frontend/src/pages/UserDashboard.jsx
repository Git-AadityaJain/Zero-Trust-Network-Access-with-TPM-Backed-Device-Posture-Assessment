import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

export default function UserDashboard() {
  const { user, hasRole } = useAuth();
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);

  // Mock resources - in production, this would come from an API
  useEffect(() => {
    const loadResources = () => {
      setLoading(true);
      
      // Get user roles
      const userRoles = user?.realm_access?.roles || [];
      const isAdmin = hasRole('admin');
      
      // Mock resource list - in production, fetch from API based on role
      const allResources = [
        { id: 1, name: 'Company Policy Document.pdf', type: 'document', role: 'admin', size: '2.5 MB' },
        { id: 2, name: 'Employee Handbook.pdf', type: 'document', role: 'user', size: '1.8 MB' },
        { id: 3, name: 'Training Materials.zip', type: 'archive', role: 'user', size: '45 MB' },
        { id: 4, name: 'Confidential Report.docx', type: 'document', role: 'admin', size: '850 KB' },
        { id: 5, name: 'Public Resources/', type: 'folder', role: 'public', size: '-' },
        { id: 6, name: 'Internal Documents/', type: 'folder', role: 'user', size: '-' },
        { id: 7, name: 'Admin Only Files/', type: 'folder', role: 'admin', size: '-' },
      ];
      
      // Filter resources based on user role
      const accessibleResources = allResources.filter(resource => {
        if (resource.role === 'public') return true; // Public resources for everyone
        if (isAdmin) return true; // Admin has access to everything
        if (resource.role === 'user' && userRoles.length > 0) return true; // Regular users can access user resources
        return userRoles.includes(resource.role); // Check if user has the specific role
      });
      
      setResources(accessibleResources);
      setLoading(false);
    };
    
    if (user) {
      loadResources();
    } else {
      setLoading(false);
    }
  }, [user, hasRole]);

  const handleDownload = (resource) => {
    // In production, this would trigger actual file download from server
    alert(`Downloading ${resource.name}...\n\nNote: This is a placeholder. File download functionality will be implemented after testing.`);
  };

  const getFileIcon = (type) => {
    switch (type) {
      case 'document':
        return '📄';
      case 'archive':
        return '📦';
      case 'folder':
        return '📁';
      default:
        return '📎';
    }
  };

  const getRoleBadge = (role) => {
    if (role === 'admin') {
      return <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">Admin Only</span>;
    } else if (role === 'user') {
      return <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">User Access</span>;
    } else {
      return <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">Public</span>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Resources</h1>
        {hasRole('admin') && (
          <span className="px-3 py-1 text-sm bg-purple-100 text-purple-800 rounded-full font-medium">
            Admin Access - Full Access
          </span>
        )}
      </div>

      {loading ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading resources...</p>
        </div>
      ) : resources.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <div className="text-4xl mb-4">📂</div>
          <p className="text-gray-600">No resources available for your role.</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <h2 className="text-lg font-semibold text-gray-900">Available Resources</h2>
            <p className="text-sm text-gray-500 mt-1">
              Files and folders accessible based on your role
            </p>
          </div>
          
          <div className="divide-y divide-gray-200">
            {resources.map((resource) => (
              <div
                key={resource.id}
                className="px-6 py-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 flex-1">
                    <div className="text-3xl">{getFileIcon(resource.type)}</div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h3 className="text-sm font-medium text-gray-900">
                          {resource.name}
                        </h3>
                        {getRoleBadge(resource.role)}
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {resource.type.charAt(0).toUpperCase() + resource.type.slice(1)}
                        {resource.size !== '-' && ` • ${resource.size}`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    {resource.type !== 'folder' && (
                      <button
                        onClick={() => handleDownload(resource)}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
                      >
                        Download
                      </button>
                    )}
                    {resource.type === 'folder' && (
                      <button
                        onClick={() => alert('Folder browsing will be implemented after testing.')}
                        className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded-lg transition-colors"
                      >
                        Open
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <div className="text-2xl mr-3">ℹ️</div>
          <div>
            <h3 className="text-sm font-semibold text-blue-900 mb-1">Resource Access Information</h3>
            <p className="text-sm text-blue-800">
              Resources are filtered based on your assigned roles. Admin users have access to all resources.
              File download functionality will be implemented after completing all system tests.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
