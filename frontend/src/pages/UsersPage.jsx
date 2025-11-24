import React, { useState, useEffect } from 'react';
import userService from '../api/userService';
import roleService from '../api/roleService';

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userRoles, setUserRoles] = useState([]);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    password: '',
    assign_roles: [],
  });

  useEffect(() => {
    fetchUsers();
    fetchRoles();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await userService.getUsers();
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to fetch users:', error);
      alert('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const fetchRoles = async () => {
    try {
      const response = await roleService.getRoles();
      setRoles(response.data);
    } catch (error) {
      console.error('Failed to fetch roles:', error);
    }
  };

  const fetchUserRoles = async (user) => {
    try {
      // Get user details which includes roles
      const response = await userService.getUserDetails(user.id);
      if (response.data.keycloak_roles) {
        setUserRoles(response.data.keycloak_roles);
      } else {
        setUserRoles([]);
      }
    } catch (error) {
      console.error('Failed to fetch user roles:', error);
      setUserRoles([]);
    }
  };

  const handleCreate = () => {
    setEditingUser(null);
    setFormData({ 
      username: '', 
      email: '', 
      first_name: '', 
      last_name: '', 
      password: '',
      assign_roles: []
    });
    setShowModal(true);
  };

  const handleEdit = (user) => {
    setEditingUser(user);
    setFormData({
      username: user.username || '',
      email: user.email || '',
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      password: '',
      assign_roles: user.keycloak_roles || []
    });
    setShowModal(true);
  };

  const handleManageRoles = async (user) => {
    setSelectedUser(user);
    await fetchUserRoles(user);
    setShowRoleModal(true);
  };

  const handleUpdateRoles = async () => {
    try {
      await userService.updateUserRoles(selectedUser.id, userRoles);
      alert('Roles updated successfully');
      setShowRoleModal(false);
      fetchUsers(); // Refresh to get updated roles
    } catch (error) {
      console.error('Failed to update roles:', error);
      alert(error.response?.data?.detail || 'Failed to update roles');
    }
  };

  const handleDelete = async (userId) => {
    if (!window.confirm('Are you sure you want to delete this user?')) {
      return;
    }
    try {
      await userService.deleteUser(userId);
      fetchUsers();
      alert('User deleted successfully');
    } catch (error) {
      console.error('Failed to delete user:', error);
      alert('Failed to delete user');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingUser) {
        const updateData = { ...formData };
        if (!updateData.password) {
          delete updateData.password;
        }
        // Don't send assign_roles for updates (use separate role management)
        delete updateData.assign_roles;
        await userService.updateUser(editingUser.id, updateData);
        alert('User updated successfully');
      } else {
        // For creation, include assign_roles if provided
        const createData = { ...formData };
        if (createData.assign_roles && createData.assign_roles.length === 0) {
          delete createData.assign_roles; // Don't send empty array
        }
        await userService.createUser(createData);
        alert('User created successfully');
      }
      setShowModal(false);
      // Refresh both users and roles to ensure latest data
      await Promise.all([fetchUsers(), fetchRoles()]);
    } catch (error) {
      console.error('Failed to save user:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to save user';
      alert(errorMessage);
    }
  };

  const toggleRole = (roleName) => {
    if (userRoles.includes(roleName)) {
      setUserRoles(userRoles.filter(r => r !== roleName));
    } else {
      setUserRoles([...userRoles, roleName]);
    }
  };

  const toggleCreateRole = (roleName) => {
    const currentRoles = formData.assign_roles || [];
    if (currentRoles.includes(roleName)) {
      setFormData({
        ...formData,
        assign_roles: currentRoles.filter(r => r !== roleName)
      });
    } else {
      setFormData({
        ...formData,
        assign_roles: [...currentRoles, roleName]
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Users</h1>
        <button
          onClick={handleCreate}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition"
        >
          + Create User
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading users...</div>
        ) : users.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No users found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Username
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Roles
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {user.username}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{user.email}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {user.first_name} {user.last_name}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1">
                        {(user.keycloak_roles || []).slice(0, 2).map((role) => (
                          <span
                            key={role}
                            className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
                          >
                            {role}
                          </span>
                        ))}
                        {(user.keycloak_roles || []).length > 2 && (
                          <span className="px-2 py-1 text-xs text-gray-500">
                            +{(user.keycloak_roles || []).length - 2} more
                          </span>
                        )}
                        {(!user.keycloak_roles || user.keycloak_roles.length === 0) && (
                          <span className="text-xs text-gray-400">No roles</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          user.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => handleEdit(user)}
                        className="text-blue-600 hover:text-blue-900 mr-4"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleManageRoles(user)}
                        className="text-purple-600 hover:text-purple-900 mr-4"
                      >
                        Roles
                      </button>
                      <button
                        onClick={() => handleDelete(user.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create/Edit User Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-4">
              {editingUser ? 'Edit User' : 'Create User'}
            </h2>
            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Username *
                  </label>
                  <input
                    type="text"
                    required
                    disabled={!!editingUser}
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email *
                  </label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      First Name
                    </label>
                    <input
                      type="text"
                      value={formData.first_name}
                      onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Last Name
                    </label>
                    <input
                      type="text"
                      value={formData.last_name}
                      onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Password {editingUser ? '(leave blank to keep current)' : '*'}
                  </label>
                  <input
                    type="password"
                    required={!editingUser}
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
                {!editingUser && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Assign Roles (Optional)
                    </label>
                    <div className="border border-gray-300 rounded-lg p-3 max-h-48 overflow-y-auto">
                      {roles.length === 0 ? (
                        <p className="text-sm text-gray-500">No roles available</p>
                      ) : (
                        <div className="space-y-2">
                          {roles.map((role) => (
                            <label key={role.name} className="flex items-center">
                              <input
                                type="checkbox"
                                checked={(formData.assign_roles || []).includes(role.name)}
                                onChange={() => toggleCreateRole(role.name)}
                                className="mr-2"
                              />
                              <span className="text-sm text-gray-700">{role.name}</span>
                              {role.description && (
                                <span className="ml-2 text-xs text-gray-500">- {role.description}</span>
                              )}
                            </label>
                          ))}
                        </div>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-gray-500">
                      Selected roles will be assigned when the user is created
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
                  {editingUser ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Manage Roles Modal */}
      {showRoleModal && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-4">
              Manage Roles for {selectedUser.username}
            </h2>
            <div className="space-y-4">
              <div className="border border-gray-300 rounded-lg p-4 max-h-64 overflow-y-auto">
                {roles.length === 0 ? (
                  <p className="text-sm text-gray-500">No roles available</p>
                ) : (
                  <div className="space-y-2">
                    {roles.map((role) => (
                      <label key={role.name} className="flex items-start">
                        <input
                          type="checkbox"
                          checked={userRoles.includes(role.name)}
                          onChange={() => toggleRole(role.name)}
                          className="mt-1 mr-2"
                        />
                        <div className="flex-1">
                          <span className="text-sm font-medium text-gray-700">{role.name}</span>
                          {role.description && (
                            <p className="text-xs text-gray-500 mt-0.5">{role.description}</p>
                          )}
                        </div>
                      </label>
                    ))}
                  </div>
                )}
              </div>
              <div className="mt-4">
                <p className="text-sm text-gray-600">
                  Selected roles: {userRoles.length > 0 ? userRoles.join(', ') : 'None'}
                </p>
              </div>
            </div>
            <div className="mt-6 flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => {
                  setShowRoleModal(false);
                  setSelectedUser(null);
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleUpdateRoles}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                Update Roles
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
