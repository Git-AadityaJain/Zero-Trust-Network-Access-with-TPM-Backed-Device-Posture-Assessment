import React, { useState, useEffect } from 'react';
import apiClient from '../api/apiClient';

export default function EnrollmentCodesPage() {
  const [codes, setCodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    description: '',
    max_uses: 1,
    expires_in_hours: 24,
  });
  const [error, setError] = useState('');

  useEffect(() => {
    fetchCodes();
  }, []);

  const fetchCodes = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/enrollment/codes');
      setCodes(response.data);
    } catch (error) {
      console.error('Failed to fetch enrollment codes:', error);
      alert('Failed to load enrollment codes');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'max_uses' || name === 'expires_in_hours' ? parseInt(value) || 0 : value,
    }));
  };

  const handleCreate = () => {
    setError('');
    setFormData({
      description: '',
      max_uses: 1,
      expires_in_hours: 24,
    });
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.max_uses < 1) {
      setError('Max uses must be at least 1');
      return;
    }

    if (formData.expires_in_hours < 1) {
      setError('Expiration must be at least 1 hour');
      return;
    }

    try {
      // Calculate expires_at from expires_in_hours
      const expiresAt = new Date();
      expiresAt.setHours(expiresAt.getHours() + formData.expires_in_hours);
      
      const payload = {
        description: formData.description || null,
        max_uses: formData.max_uses,
        expires_at: expiresAt.toISOString(),
      };

      const response = await apiClient.post('/enrollment/codes', payload);
      setShowModal(false);
      await fetchCodes();
      alert(`Enrollment code created successfully!\nCode: ${response.data.code}`);
    } catch (error) {
      console.error('Failed to create enrollment code:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to create enrollment code';
      setError(errorMessage);
    }
  };

  const handleDeactivate = async (codeId) => {
    if (!window.confirm('Are you sure you want to deactivate this enrollment code?')) {
      return;
    }

    try {
      await apiClient.post(`/enrollment/codes/${codeId}/deactivate`);
      await fetchCodes();
      alert('Enrollment code deactivated successfully');
    } catch (error) {
      console.error('Failed to deactivate enrollment code:', error);
      alert('Failed to deactivate enrollment code');
    }
  };

  const getStatusBadge = (code) => {
    if (!code.is_active) {
      return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">Inactive</span>;
    }
    if (code.uses_count >= code.max_uses) {
      return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">Exhausted</span>;
    }
    if (new Date(code.expires_at) < new Date()) {
      return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">Expired</span>;
    }
    return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Active</span>;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Enrollment Codes</h1>
        <button
          onClick={handleCreate}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition"
        >
          + Create Enrollment Code
        </button>
      </div>

      {/* Create Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Create Enrollment Code</h2>
            
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                  <p className="text-sm text-blue-800">
                    <strong>Note:</strong> The enrollment code will be automatically generated after creation.
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <input
                    type="text"
                    name="description"
                    value={formData.description}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Optional description (e.g., Test enrollment code)"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Uses *
                  </label>
                  <input
                    type="number"
                    name="max_uses"
                    value={formData.max_uses}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    min="1"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Expires In (Hours) *
                  </label>
                  <input
                    type="number"
                    name="expires_in_hours"
                    value={formData.expires_in_hours}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    min="1"
                    required
                  />
                </div>
              </div>

              <div className="flex space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-2 px-4 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Codes List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="text-gray-500">Loading enrollment codes...</div>
        </div>
      ) : codes.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="text-gray-500 text-lg mb-4">No enrollment codes found</div>
          <button
            onClick={handleCreate}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition"
          >
            Create First Enrollment Code
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Code
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Uses
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Expires At
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {codes.map((code) => (
                <tr key={code.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900 font-mono">{code.code}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900">{code.description || '-'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {code.current_uses} / {code.max_uses}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{formatDate(code.expires_at)}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">{getStatusBadge(code)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {code.is_active && (
                      <button
                        onClick={() => handleDeactivate(code.id)}
                        className="text-red-600 hover:text-red-800 font-medium"
                      >
                        Deactivate
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
  );
}

