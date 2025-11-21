# src/components/Modals/ApprovalModal.jsx

```javascript
import React, { useState } from 'react';
import * as deviceService from '../../api/deviceService';

/**
 * ApprovalModal
 * Modal for admin to approve a pending device enrollment
 * Creates a new user and associates the device
 */
export default function ApprovalModal({ device, onClose }) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    roles: ['user'],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleRoleChange = (role) => {
    setFormData((prev) => {
      const roles = prev.roles.includes(role)
        ? prev.roles.filter((r) => r !== role)
        : [...prev.roles, role];
      return { ...prev, roles };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Validate inputs
      if (!formData.username.trim()) {
        setError('Username is required');
        return;
      }
      if (!formData.email.trim()) {
        setError('Email is required');
        return;
      }
      if (formData.roles.length === 0) {
        setError('At least one role must be selected');
        return;
      }

      // Call API to approve device
      await deviceService.approveDevice(device.id, {
        username: formData.username,
        email: formData.email,
        roles: formData.roles,
      });

      setSuccess(true);
      setTimeout(() => onClose(), 1500);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to approve device');
    } finally {
      setLoading(false);
    }
  };

  const availableRoles = ['user', 'device-admin', 'audit-viewer', 'super-admin'];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-2xl max-w-md w-full p-6">
        {/* Header */}
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Approve Device</h2>
        <p className="text-gray-600 text-sm mb-6">
          Create a new user account for device: <code className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">{device.device_name}</code>
        </p>

        {success ? (
          <div className="text-center py-6">
            <div className="text-4xl mb-3">✓</div>
            <p className="text-green-600 font-semibold">Device approved successfully!</p>
            <p className="text-gray-600 text-sm mt-2">User created and device linked.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
                {error}
              </div>
            )}

            {/* Username */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Username <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                placeholder="john.doe"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                disabled={loading}
              />
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email <span className="text-red-500">*</span>
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="john.doe@company.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                disabled={loading}
              />
            </div>

            {/* Roles */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Roles <span className="text-red-500">*</span>
              </label>
              <div className="space-y-2">
                {availableRoles.map((role) => (
                  <label key={role} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.roles.includes(role)}
                      onChange={() => handleRoleChange(role)}
                      disabled={loading}
                      className="w-4 h-4 rounded border-gray-300 text-blue-600 cursor-pointer"
                    />
                    <span className="ml-2 text-sm text-gray-700 capitalize">{role.replace('-', ' ')}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Buttons */}
            <div className="flex gap-3 mt-6">
              <button
                type="button"
                onClick={onClose}
                disabled={loading}
                className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-900 font-medium py-2 px-4 rounded-lg transition disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition disabled:opacity-50"
              >
                {loading ? 'Approving...' : 'Approve'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
```

## Purpose
The `ApprovalModal.jsx` provides a **dialog for approving devices**:
- Admin enters username, email, and roles
- Creates Keycloak user account
- Associates device with newly created user
- Shows success/error feedback

## Form Fields
- **Username**: Unique identifier for Keycloak user
- **Email**: User contact email
- **Roles**: Checkboxes for assigning roles (user, device-admin, audit-viewer, super-admin)

## API Call
Calls `deviceService.approveDevice(deviceId, userData)` which:
- Endpoint: `PATCH /api/device/{device_id}/approve`
- Request: `{username, email, roles}`
- Response: User ID and confirmation

## UX Features
- Form validation before submission
- Loading state disables inputs/buttons
- Success message with auto-close
- Error display with retry capability
