import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useDeviceDetails } from '../hooks/useDevices';
import deviceService from '../api/deviceService';

export default function DeviceDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { device, loading, error } = useDeviceDetails(id);
  const [deleting, setDeleting] = useState(false);
  const [postureHistory, setPostureHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const getStatusBadge = (status) => {
    const badges = {
      active: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      rejected: 'bg-red-100 text-red-800',
      inactive: 'bg-gray-100 text-gray-800',
    };
    return badges[status] || badges.inactive;
  };

  const getComplianceBadge = (isCompliant) => {
    return isCompliant
      ? 'bg-green-100 text-green-800'
      : 'bg-red-100 text-red-800';
  };

  useEffect(() => {
    if (device && device.id) {
      fetchPostureHistory();
    }
  }, [device]);

  const fetchPostureHistory = async () => {
    if (!device || !device.id) return;
    
    try {
      setLoadingHistory(true);
      const response = await deviceService.getDevicePostureHistory(device.id, 10);
      setPostureHistory(response.data || []);
    } catch (error) {
      console.error('Failed to fetch posture history:', error);
      setPostureHistory([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleDelete = async () => {
    if (!device) return;
    
    if (!window.confirm(`Are you sure you want to delete device "${device.device_name}"? This action cannot be undone.`)) {
      return;
    }

    setDeleting(true);
    try {
      await deviceService.deleteDevice(device.id);
      alert('Device deleted successfully');
      navigate('/devices');
    } catch (error) {
      console.error('Failed to delete device:', error);
      alert(error.response?.data?.detail || 'Failed to delete device');
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading device details...</div>
      </div>
    );
  }

  if (error || !device) {
    return (
      <div className="space-y-6">
        <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-red-700">
                {error || 'Device not found'}
              </p>
            </div>
          </div>
        </div>
        <Link
          to="/devices"
          className="text-blue-600 hover:text-blue-900"
        >
          ← Back to Devices
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link
            to="/devices"
            className="text-blue-600 hover:text-blue-900 mb-2 inline-block"
          >
            ← Back to Devices
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">
            Device Details
          </h1>
        </div>
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {deleting ? 'Deleting...' : 'Delete Device'}
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                {device.device_name || 'Unknown Device'}
              </h2>
              <p className="text-sm text-gray-500 font-mono mt-1">
                {device.device_unique_id}
              </p>
            </div>
            <div className="flex space-x-2">
              <span
                className={`px-3 py-1 text-sm font-semibold rounded-full ${getStatusBadge(
                  device.status
                )}`}
              >
                {device.status}
              </span>
              <span
                className={`px-3 py-1 text-sm font-semibold rounded-full ${getComplianceBadge(
                  device.is_compliant
                )}`}
              >
                {device.is_compliant ? 'Compliant' : 'Non-Compliant'}
              </span>
            </div>
          </div>
        </div>

        <div className="px-6 py-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Basic Information */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Basic Information
              </h3>
              <dl className="space-y-3">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Device ID</dt>
                  <dd className="mt-1 text-sm text-gray-900 font-mono">
                    {device.id}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Device Name</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {device.device_name || 'N/A'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Unique ID</dt>
                  <dd className="mt-1 text-sm text-gray-900 font-mono break-all">
                    {device.device_unique_id}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Status</dt>
                  <dd className="mt-1">
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(
                        device.status
                      )}`}
                    >
                      {device.status}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Enrolled At</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {device.enrolled_at
                      ? new Date(device.enrolled_at).toLocaleString()
                      : 'N/A'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Last Seen</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {device.last_seen_at
                      ? new Date(device.last_seen_at).toLocaleString()
                      : 'Never'}
                  </dd>
                </div>
              </dl>
            </div>

            {/* System Information */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                System Information
              </h3>
              <dl className="space-y-3">
                <div>
                  <dt className="text-sm font-medium text-gray-500">OS Type</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {device.os_type || 'N/A'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">OS Version</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {device.os_version || 'N/A'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Compliance Status</dt>
                  <dd className="mt-1">
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${getComplianceBadge(
                        device.is_compliant
                      )}`}
                    >
                      {device.is_compliant ? 'Compliant' : 'Non-Compliant'}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Last Posture Check</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {device.last_posture_check
                      ? new Date(device.last_posture_check).toLocaleString()
                      : 'Never'}
                  </dd>
                </div>
              </dl>
            </div>

            {/* User Assignment */}
            {device.user_id && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  User Assignment
                </h3>
                <dl className="space-y-3">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Assigned User ID</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {device.user_id}
                    </dd>
                  </div>
                </dl>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Posture History */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Posture History</h3>
        </div>
        <div className="px-6 py-4">
          {loadingHistory ? (
            <div className="text-center text-gray-500 py-4">Loading posture history...</div>
          ) : postureHistory.length === 0 ? (
            <div className="text-center text-gray-500 py-4">No posture history available</div>
          ) : (
            <div className="space-y-3">
              {postureHistory.map((entry, idx) => (
                <div
                  key={entry.id || idx}
                  className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${getComplianceBadge(
                          entry.is_compliant
                        )}`}
                      >
                        {entry.is_compliant ? 'Compliant' : 'Non-Compliant'}
                      </span>
                      {entry.compliance_score !== null && (
                        <span className="text-sm text-gray-600">
                          Score: {entry.compliance_score}%
                        </span>
                      )}
                    </div>
                    <span className="text-sm text-gray-500">
                      {new Date(entry.checked_at).toLocaleString()}
                    </span>
                  </div>
                  {entry.violations && entry.violations.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs font-medium text-red-600 mb-1">Violations:</p>
                      <ul className="list-disc list-inside text-xs text-red-600">
                        {entry.violations.map((violation, vIdx) => (
                          <li key={vIdx}>{violation}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {entry.signature_valid === false && (
                    <div className="mt-2">
                      <span className="text-xs text-red-600">⚠️ Invalid signature</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

