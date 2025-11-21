# src/components/Modals/RejectModal.jsx

```javascript
import React, { useState } from 'react';
import * as deviceService from '../../api/deviceService';

/**
 * RejectModal
 * Modal for admin to reject a pending device enrollment
 */
export default function RejectModal({ device, onClose }) {
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Call API to reject device
      await deviceService.rejectDevice(device.id, reason);
      setSuccess(true);
      setTimeout(() => onClose(), 1500);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to reject device');
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
    'User request',
    'Other',
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-2xl max-w-md w-full p-6">
        {/* Header */}
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Reject Device</h2>
        <p className="text-gray-600 text-sm mb-6">
          Decline device enrollment: <code className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">{device.device_name}</code>
        </p>

        {success ? (
          <div className="text-center py-6">
            <div className="text-4xl mb-3">✗</div>
            <p className="text-red-600 font-semibold">Device rejected successfully!</p>
            <p className="text-gray-600 text-sm mt-2">Device enrollment has been declined.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
                {error}
              </div>
            )}

            {/* Reason Selection */}
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

            {/* Custom Reason */}
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

            {/* Info Box */}
            <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
              <p className="text-xs text-yellow-900">
                <strong>Note:</strong> The device will be notified of the rejection. The user can re-submit with changes.
              </p>
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
                className="flex-1 bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition disabled:opacity-50"
              >
                {loading ? 'Rejecting...' : 'Reject Device'}
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
The `RejectModal.jsx` provides a **dialog for rejecting device enrollments**:
- Admin selects or enters reason for rejection
- Submits rejection to backend
- Device is notified and can re-enroll with changes

## Features
- **Predefined reasons**: Common rejection reasons (posture not compliant, firewall disabled, etc.)
- **Custom reason**: Free-text field for other reasons
- **Info message**: Explains device will be notified
- **Loading state**: Disables inputs during submission
- **Success feedback**: Shows confirmation

## API Call
Calls `deviceService.rejectDevice(deviceId, reason)` which:
- Endpoint: `PATCH /api/device/{device_id}/reject`
- Request: `{reason}`
- Response: Confirmation

## UX Considerations
- Non-punitive UI (not aggressive red, informative yellow warnings)
- Reason helps with compliance auditing
- Allows device to retry after addressing issues
