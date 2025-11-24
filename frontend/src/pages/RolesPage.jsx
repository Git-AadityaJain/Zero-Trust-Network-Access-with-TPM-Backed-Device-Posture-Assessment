import React, { useState, useEffect } from 'react';
import roleService from '../api/roleService';

export default function RolesPage() {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingRole, setEditingRole] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    composite: false,
  });

  useEffect(() => {
    fetchRoles();
  }, []);

  const fetchRoles = async () => {
    try {
      setLoading(true);
      const response = await roleService.getRoles();
      setRoles(response.data);
    } catch (error) {
      console.error('Failed to fetch roles:', error);
      alert('Failed to load roles');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingRole(null);
    setFormData({ name: '', description: '', composite: false });
    setShowModal(true);
  };

  const handleEdit = (role) => {
    setEditingRole(role);
    setFormData({
      name: role.name,
      description: role.description || '',
      composite: role.composite || false,
    });
    setShowModal(true);
  };

  const handleDelete = async (roleName) => {
    if (!window.confirm(`Are you sure you want to delete the role "${roleName}"?`)) {
      return;
    }
    try {
      await roleService.deleteRole(roleName);
      fetchRoles();
      alert('Role deleted successfully');
    } catch (error) {
      console.error('Failed to delete role:', error);
      alert(error.response?.data?.detail || 'Failed to delete role');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Validate role name
      if (!formData.name || !formData.name.trim()) {
        alert('Role name is required');
        return;
      }
      
      // Normalize role name (remove extra spaces, convert to lowercase for consistency)
      const normalizedName = formData.name.trim().toLowerCase().replace(/\s+/g, '-');
      
      if (editingRole) {
        await roleService.updateRole(editingRole.name, {
          description: formData.description,
        });
        alert('Role updated successfully');
        setShowModal(false);
        await fetchRoles();
      } else {
        // Use normalized name for creation
        try {
          await roleService.createRole({
            ...formData,
            name: normalizedName
          });
          alert('Role created successfully');
          setShowModal(false);
          await fetchRoles();
        } catch (createError) {
          // If role already exists (409), refresh list and show message
          if (createError.response?.status === 409) {
            await fetchRoles();
            alert('Role already exists. Refreshing list...');
            setShowModal(false);
          } else {
            throw createError; // Re-throw other errors
          }
        }
      }
    } catch (error) {
      console.error('Failed to save role:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to save role';
      alert(errorMessage);
    }
  };

  // Filter out default/system roles that shouldn't be deleted
  const isProtectedRole = (roleName) => {
    const protectedRoles = ['admin', 'default-roles-master', 'offline_access', 'uma_authorization', 'create-realm'];
    return protectedRoles.includes(roleName);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Roles</h1>
        <button
          onClick={handleCreate}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition"
        >
          + Create Role
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading roles...</div>
        ) : roles.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No roles found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {roles.map((role) => (
                  <tr key={role.name} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {role.name}
                        {isProtectedRole(role.name) && (
                          <span className="ml-2 px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded">
                            System
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900">
                        {role.description || <span className="text-gray-400">No description</span>}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {role.composite ? (
                          <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">Composite</span>
                        ) : (
                          <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">Simple</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => handleEdit(role)}
                        className="text-blue-600 hover:text-blue-900 mr-4"
                      >
                        Edit
                      </button>
                      {!isProtectedRole(role.name) && (
                        <button
                          onClick={() => handleDelete(role.name)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Delete
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h2 className="text-2xl font-bold mb-4">
              {editingRole ? 'Edit Role' : 'Create Role'}
            </h2>
            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Role Name *
                  </label>
                  <input
                    type="text"
                    required
                    disabled={!!editingRole}
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100"
                    placeholder="e.g., editor, viewer, manager"
                  />
                  {editingRole && (
                    <p className="mt-1 text-xs text-gray-500">Role name cannot be changed</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    rows="3"
                    placeholder="Describe what this role allows users to do"
                  />
                </div>
                {!editingRole && (
                  <div>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={formData.composite}
                        onChange={(e) => setFormData({ ...formData, composite: e.target.checked })}
                        className="mr-2"
                      />
                      <span className="text-sm text-gray-700">Composite Role</span>
                    </label>
                    <p className="mt-1 text-xs text-gray-500">
                      Composite roles can contain other roles
                    </p>
                  </div>
                )}
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  {editingRole ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

