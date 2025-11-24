import React, { useState, useEffect } from 'react';
import apiClient from '../api/apiClient';
import ApprovalModal from '../components/Modals/ApprovalModal';
import RejectModal from '../components/Modals/RejectModal';

export default function PendingDevicesPage() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);

  useEffect(() => {
    fetchPendingDevices();
    const interval = setInterval(fetchPendingDevices, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchPendingDevices = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/devices/pending');
      setDevices(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch pending devices');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = (device) => {
    setSelectedDevice(device);
    setShowApprovalModal(true);
  };

  const handleReject = (device) => {
    setSelectedDevice(device);
    setShowRejectModal(true);
  };

  const handleApprovalSuccess = () => {
    setShowApprovalModal(false);
    setSelectedDevice(null);
    fetchPendingDevices();
  };

  const handleRejectionSuccess = () => {
    setShowRejectModal(false);
    setSelectedDevice(null);
    fetchPendingDevices();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-4xl font-bold text-gray-900">Pending Device Enrollments</h1>
        <p className="text-gray-600 mt-2">
          Review and approve or reject devices awaiting enrollment
        </p>
      </div>

      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
        <p className="text-yellow-900 font-semibold">
          {devices.length} device{devices.length !== 1 ? 's' : ''} awaiting approval
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Error: {error}
        </div>
      )}

      {loading ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-500">Loading pending devices...</p>
        </div>
      ) : devices.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-500 text-lg">✓ No pending devices!</p>
          <p className="text-gray-400 mt-2">All devices have been reviewed.</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b-2 border-gray-200">
                <tr>
                  <th className="text-left py-4 px-6 font-semibold text-gray-700">Device Info</th>
                  <th className="text-left py-4 px-6 font-semibold text-gray-700">OS</th>
                  <th className="text-left py-4 px-6 font-semibold text-gray-700">Firewall</th>
                  <th className="text-left py-4 px-6 font-semibold text-gray-700">Encryption</th>
                  <th className="text-left py-4 px-6 font-semibold text-gray-700">Antivirus</th>
                  <th className="text-center py-4 px-6 font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody>
                {devices.map((device) => (
                  <tr key={device.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-4 px-6">
                      <div>
                        <p className="font-medium text-gray-900">{device.device_name || 'Unknown'}</p>
                        <p className="text-gray-500 text-xs font-mono">
                          {device.device_unique_id ? device.device_unique_id.substring(0, 12) + '...' : `ID: ${device.id}`}
                        </p>
                      </div>
                    </td>

                    <td className="py-4 px-6">
                      <span className="px-3 py-1 bg-blue-100 text-blue-900 text-xs rounded-full font-medium">
                        {device.os_type || 'N/A'} {device.os_version || ''}
                      </span>
                    </td>

                    <td className="py-4 px-6">
                      <span className={`px-3 py-1 text-xs rounded-full font-medium ${
                        device.initial_posture?.firewall_enabled
                          ? 'bg-green-100 text-green-900'
                          : 'bg-red-100 text-red-900'
                      }`}>
                        {device.initial_posture?.firewall_enabled ? '✓ Enabled' : '✗ Disabled'}
                      </span>
                    </td>

                    <td className="py-4 px-6">
                      <span className={`px-3 py-1 text-xs rounded-full font-medium ${
                        device.initial_posture?.disk_encrypted
                          ? 'bg-green-100 text-green-900'
                          : 'bg-red-100 text-red-900'
                      }`}>
                        {device.initial_posture?.disk_encrypted ? '✓ Enabled' : '✗ Disabled'}
                      </span>
                    </td>

                    <td className="py-4 px-6">
                      <span className={`px-3 py-1 text-xs rounded-full font-medium ${
                        device.initial_posture?.antivirus_enabled
                          ? 'bg-green-100 text-green-900'
                          : 'bg-red-100 text-red-900'
                      }`}>
                        {device.initial_posture?.antivirus_enabled ? '✓ Running' : '✗ Not Running'}
                      </span>
                    </td>

                    <td className="py-4 px-6 text-center">
                      <div className="flex justify-center gap-2">
                        <button
                          onClick={() => handleApprove(device)}
                          className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded transition font-medium text-sm"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => handleReject(device)}
                          className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded transition font-medium text-sm"
                        >
                          Reject
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showApprovalModal && selectedDevice && (
        <ApprovalModal
          device={selectedDevice}
          onClose={() => setShowApprovalModal(false)}
          onSuccess={handleApprovalSuccess}
        />
      )}

      {showRejectModal && selectedDevice && (
        <RejectModal
          device={selectedDevice}
          onClose={() => setShowRejectModal(false)}
          onSuccess={handleRejectionSuccess}
        />
      )}
    </div>
  );
}