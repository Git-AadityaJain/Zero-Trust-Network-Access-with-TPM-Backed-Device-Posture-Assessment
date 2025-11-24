import React, { useState, useEffect } from 'react';
import policyService from '../api/policyService';

export default function PoliciesPage() {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [editingPolicy, setEditingPolicy] = useState(null);
  const [filters, setFilters] = useState({
    active_only: false,
    policy_type: '',
  });
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    policy_type: 'compliance',
    rules: {},
    priority: 100,
    enforce_mode: 'enforce',
  });
  const [rulesText, setRulesText] = useState('{}');

  useEffect(() => {
    fetchPolicies();
  }, [filters]);

  const fetchPolicies = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filters.active_only) {
        params.active_only = true;
      }
      if (filters.policy_type) {
        params.policy_type = filters.policy_type;
      }
      const response = await policyService.getPolicies(params);
      setPolicies(response.data);
    } catch (error) {
      console.error('Failed to fetch policies:', error);
      alert('Failed to load policies');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingPolicy(null);
    setFormData({ name: '', description: '', policy_type: 'compliance', rules: {}, priority: 100, enforce_mode: 'enforce' });
    setRulesText('{}');
    setShowModal(true);
  };

  const handleEdit = (policy) => {
    setEditingPolicy(policy);
    const rules = policy.rules || {};
    setFormData({
      name: policy.name || '',
      description: policy.description || '',
      policy_type: policy.policy_type || 'compliance',
      rules: rules,
      priority: policy.priority || 100,
      enforce_mode: policy.enforce_mode || 'enforce',
    });
    setRulesText(JSON.stringify(rules, null, 2));
    setShowModal(true);
  };

  const handleViewDetails = async (policyId) => {
    try {
      const response = await policyService.getPolicyDetails(policyId);
      setSelectedPolicy(response.data);
      setShowDetailsModal(true);
    } catch (error) {
      console.error('Failed to fetch policy details:', error);
      alert('Failed to load policy details');
    }
  };

  const handleDelete = async (policyId) => {
    if (!window.confirm('Are you sure you want to delete this policy?')) {
      return;
    }
    try {
      await policyService.deletePolicy(policyId);
      fetchPolicies();
      alert('Policy deleted successfully');
    } catch (error) {
      console.error('Failed to delete policy:', error);
      alert('Failed to delete policy');
    }
  };

  const handleToggleActive = async (policy) => {
    try {
      if (policy.is_active) {
        await policyService.deactivatePolicy(policy.id);
      } else {
        await policyService.activatePolicy(policy.id);
      }
      fetchPolicies();
    } catch (error) {
      console.error('Failed to toggle policy status:', error);
      alert('Failed to update policy status');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Parse rules JSON before submitting
      let parsedRules = {};
      try {
        parsedRules = JSON.parse(rulesText);
      } catch (parseError) {
        alert('Invalid JSON in Rules field. Please check the format.');
        return;
      }
      
      const submitData = {
        ...formData,
        rules: parsedRules
      };
      
      if (editingPolicy) {
        await policyService.updatePolicy(editingPolicy.id, submitData);
        alert('Policy updated successfully');
      } else {
        await policyService.createPolicy(submitData);
        alert('Policy created successfully');
      }
      setShowModal(false);
      // Refresh policies to show updated data
      await fetchPolicies();
    } catch (error) {
      console.error('Failed to save policy:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to save policy';
      alert(errorMessage);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Policies</h1>
        <button
          onClick={handleCreate}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition"
        >
          + Create Policy
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center space-x-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="active-only"
              checked={filters.active_only}
              onChange={(e) => setFilters({ ...filters, active_only: e.target.checked })}
              className="mr-2"
            />
            <label htmlFor="active-only" className="text-sm text-gray-700">
              Active Only
            </label>
          </div>
          <div>
            <label htmlFor="policy-type" className="text-sm text-gray-700 mr-2">
              Type:
            </label>
            <select
              id="policy-type"
              value={filters.policy_type}
              onChange={(e) => setFilters({ ...filters, policy_type: e.target.value })}
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">All Types</option>
              <option value="compliance">Compliance</option>
              <option value="access">Access</option>
              <option value="security">Security</option>
            </select>
          </div>
          {(filters.active_only || filters.policy_type) && (
            <button
              onClick={() => setFilters({ active_only: false, policy_type: '' })}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Clear Filters
            </button>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading policies...</div>
        ) : policies.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No policies found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Priority
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
                {policies.map((policy) => (
                  <tr key={policy.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {policy.name}
                      </div>
                      {policy.description && (
                        <div className="text-sm text-gray-500">
                          {policy.description}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900">
                        {policy.policy_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          policy.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {policy.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900">
                        {policy.priority}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(policy.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => handleViewDetails(policy.id)}
                        className="text-purple-600 hover:text-purple-900 mr-4"
                        title="View Details"
                      >
                        View
                      </button>
                      <button
                        onClick={() => handleToggleActive(policy)}
                        className={`mr-4 ${
                          policy.is_active
                            ? 'text-yellow-600 hover:text-yellow-900'
                            : 'text-green-600 hover:text-green-900'
                        }`}
                      >
                        {policy.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                      <button
                        onClick={() => handleEdit(policy)}
                        className="text-blue-600 hover:text-blue-900 mr-4"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(policy.id)}
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

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-4">
              {editingPolicy ? 'Edit Policy' : 'Create Policy'}
            </h2>
            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
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
                  />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Type *
                    </label>
                    <select
                      value={formData.policy_type}
                      onChange={(e) => setFormData({ ...formData, policy_type: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="compliance">Compliance</option>
                      <option value="access">Access</option>
                      <option value="security">Security</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Priority *
                    </label>
                    <input
                      type="number"
                      required
                      value={formData.priority}
                      onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      min="1"
                      max="1000"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Enforce Mode *
                    </label>
                    <select
                      value={formData.enforce_mode}
                      onChange={(e) => setFormData({ ...formData, enforce_mode: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="enforce">Enforce</option>
                      <option value="monitor">Monitor</option>
                      <option value="disabled">Disabled</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Rules (JSON) *
                  </label>
                  <textarea
                    value={rulesText}
                    onChange={(e) => {
                      setRulesText(e.target.value);
                      // Try to parse and update formData if valid (for preview)
                      try {
                        const parsed = JSON.parse(e.target.value);
                        setFormData({ ...formData, rules: parsed });
                      } catch (err) {
                        // Invalid JSON - that's OK, user is still typing
                        // Don't update formData, just keep the text
                      }
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm"
                    rows="8"
                    placeholder='{"condition": "device_compliant", "value": true}'
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Enter valid JSON. The rules will be validated on submit.
                  </p>
                </div>
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
                  {editingPolicy ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Policy Details Modal */}
      {showDetailsModal && selectedPolicy && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold">Policy Details</h2>
              <button
                onClick={() => setShowDetailsModal(false)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ×
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <p className="text-gray-900 font-semibold">{selectedPolicy.name}</p>
              </div>
              {selectedPolicy.description && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <p className="text-gray-900">{selectedPolicy.description}</p>
                </div>
              )}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                  <p className="text-gray-900">{selectedPolicy.policy_type}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                  <p className="text-gray-900">{selectedPolicy.priority}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Enforce Mode</label>
                  <p className="text-gray-900 capitalize">{selectedPolicy.enforce_mode || 'enforce'}</p>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <span
                  className={`px-3 py-1 text-sm font-semibold rounded-full ${
                    selectedPolicy.is_active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {selectedPolicy.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rules (JSON)</label>
                <pre className="bg-gray-50 p-4 rounded-lg border border-gray-200 overflow-x-auto text-sm font-mono">
                  {JSON.stringify(selectedPolicy.rules, null, 2)}
                </pre>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Created</label>
                  <p>{new Date(selectedPolicy.created_at).toLocaleString()}</p>
                  {selectedPolicy.created_by && (
                    <p className="text-xs text-gray-500">by {selectedPolicy.created_by}</p>
                  )}
                </div>
                {selectedPolicy.updated_at && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Last Updated</label>
                    <p>{new Date(selectedPolicy.updated_at).toLocaleString()}</p>
                    {selectedPolicy.last_modified_by && (
                      <p className="text-xs text-gray-500">by {selectedPolicy.last_modified_by}</p>
                    )}
                  </div>
                )}
              </div>
            </div>
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setShowDetailsModal(false)}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

