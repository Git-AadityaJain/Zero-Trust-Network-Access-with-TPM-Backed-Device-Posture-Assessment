import React, { useState } from 'react';
import apiClient from '../../api/apiClient';

export default function RejectModal({ device, onClose, onSuccess }) {
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await apiClient.patch(`/devices/${device.id}/reject`, {
        rejection_reason: reason || undefined,
      });
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reject device');
    } finally {
      setLoading(false);
    }
  };

  const rejectionReasons = [
    'Device posture not compliant',
    'Firewall disabled',
    'Encryption not enabled',
    'Antivirus not installed',
    'Outdated OS version',
    'Hardware mismatch',
    'Policy violation',
    'Other',
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-2xl max-w-md w-full p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Reject Device</h2>
        <p className="text-gray-600 text-sm mb-6">
          Decline device enrollment: <code className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">{device.device_name}</code>
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Reason for Rejection (Optional)
            </label>
            <div className="max-h-40 overflow-y-auto space-y-2 border border-gray-200 rounded-lg p-3 bg-gray-50">
              {rejectionReasons.map((reasonOption) => (
                <label key={reasonOption} className="flex items-center">
                  <input
                    type="radio"
                    name="reason"
                    value={reasonOption}
                    checked={reason === reasonOption}
                    onChange={(e) => setReason(e.target.value)}
                    disabled={loading}
                    className="w-4 h-4 text-red-600 cursor-pointer"
                  />
                  <span className="ml-2 text-sm text-gray-700">{reasonOption}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Custom Reason
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Enter custom reason for rejection..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent outline-none resize-none"
              rows="3"
              disabled={loading}
            />
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
            <p className="text-xs text-yellow-900">
              <strong>Note:</strong> The device will be notified of the rejection. The user can
              re-submit with changes.
            </p>
          </div>

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
              className="flex-1 bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition disabled:opacity-50"
            >
              {loading ? 'Rejecting...' : 'Reject Device'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
