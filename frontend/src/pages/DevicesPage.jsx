import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api/apiClient';
import ApprovalModal from '../components/Modals/ApprovalModal';
import RejectModal from '../components/Modals/RejectModal';
import deviceService from '../api/deviceService';

export default function DevicesPage() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);

  useEffect(() => {
    fetchDevices();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  const fetchDevices = async () => {
    try {
      setLoading(true);
      const params = filter !== 'all' ? { status_filter: filter } : {};
      const response = await apiClient.get('/devices', { params });
      setDevices(response.data);
    } catch (error) {
      console.error('Failed to fetch devices:', error);
    } finally {
      setLoading(false);
    }
  };

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
    fetchDevices();
  };

  const handleRejectionSuccess = () => {
    setShowRejectModal(false);
    setSelectedDevice(null);
    fetchDevices();
  };

  const handleDelete = async (device) => {
    if (!window.confirm(`Are you sure you want to delete device "${device.device_name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await deviceService.deleteDevice(device.id);
      alert('Device deleted successfully');
      fetchDevices();
    } catch (error) {
      console.error('Failed to delete device:', error);
      alert(error.response?.data?.detail || 'Failed to delete device');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Devices</h1>
        <Link
          to="/devices/pending"
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition"
        >
          View Pending
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex space-x-2">
          {['all', 'active', 'pending', 'rejected', 'inactive'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg transition ${
                filter === status
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Devices Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading devices...</div>
        ) : devices.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No devices found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Device Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    OS
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Compliance
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Seen
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {devices.map((device) => (
                  <tr key={device.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {device.device_name}
                      </div>
                      <div className="text-sm text-gray-500 font-mono text-xs">
                        {device.device_unique_id.substring(0, 8)}...
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {device.os_type || 'N/A'}
                      </div>
                      <div className="text-sm text-gray-500">
                        {device.os_version || ''}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(
                          device.status
                        )}`}
                      >
                        {device.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${getComplianceBadge(
                          device.is_compliant
                        )}`}
                      >
                        {device.is_compliant ? 'Compliant' : 'Non-Compliant'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {device.last_seen_at
                        ? new Date(device.last_seen_at).toLocaleDateString()
                        : 'Never'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <Link
                        to={`/devices/${device.id}`}
                        className="text-blue-600 hover:text-blue-900 mr-4"
                      >
                        View
                      </Link>
                      {device.status === 'pending' && (
                        <>
                          <button
                            onClick={() => handleApprove(device)}
                            className="text-green-600 hover:text-green-900 mr-4"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => handleReject(device)}
                            className="text-red-600 hover:text-red-900 mr-4"
                          >
                            Reject
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => handleDelete(device)}
                        className="text-red-600 hover:text-red-900"
                        title="Delete device"
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

