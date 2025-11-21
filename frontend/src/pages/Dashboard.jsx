import React from 'react';
import { useDevices, usePendingDevices } from '../hooks/useDevices';
import { useUsers } from '../hooks/useUsers';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const { user } = useAuth();
  const { devices: allDevices, loading: devicesLoading } = useDevices();
  const { devices: pendingDevices } = usePendingDevices(true, 5000);
  const { users, loading: usersLoading } = useUsers();

  const approvedDevices = allDevices.filter((d) => d.status === 'approved').length;
  const compliantDevices = allDevices.filter((d) => d.compliance_status === 'compliant').length;
  const nonCompliantDevices = allDevices.filter((d) => d.compliance_status === 'noncompliant').length;

  const stats = [
    {
      label: 'Total Devices',
      value: allDevices.length,
      color: 'bg-blue-500',
      icon: '💻',
    },
    {
      label: 'Pending Approval',
      value: pendingDevices.length,
      color: 'bg-yellow-500',
      icon: '⏳',
      action: '/devices/pending',
    },
    {
      label: 'Compliant',
      value: compliantDevices,
      color: 'bg-green-500',
      icon: '✓',
    },
    {
      label: 'Non-Compliant',
      value: nonCompliantDevices,
      color: 'bg-red-500',
      icon: '⚠️',
    },
  ];

  return (
    <div className="space-y-6 p-6">
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-8 rounded-lg shadow-lg">
        <h1 className="text-4xl font-bold">Welcome back, {user?.username || 'Admin'}!</h1>
        <p className="text-blue-100 mt-2">
          ZTNA Device Management System - Device Posture Assessment Dashboard
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, idx) => (
          <Link key={idx} to={stat.action || '#'} className="no-underline">
            <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition cursor-pointer">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500 text-sm font-semibold">{stat.label}</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</p>
                </div>
                <div className={`${stat.color} text-white p-4 rounded-full text-2xl`}>
                  {stat.icon}
                </div>
              </div>
              {stat.action && (
                <p className="text-blue-600 text-sm mt-4 font-medium">View →</p>
              )}
            </div>
          </Link>
        ))}
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/devices/pending"
            className="bg-yellow-50 border-2 border-yellow-200 rounded-lg p-4 hover:bg-yellow-100 transition no-underline"
          >
            <p className="text-lg font-semibold text-yellow-900">Review Pending Enrollments</p>
            <p className="text-yellow-700 text-sm mt-1">
              {pendingDevices.length} device{pendingDevices.length !== 1 ? 's' : ''} awaiting approval
            </p>
          </Link>

          <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4 hover:bg-blue-100 transition no-underline">
            <p className="text-lg font-semibold text-blue-900">View All Devices</p>
            <p className="text-blue-700 text-sm mt-1">Manage and monitor device posture</p>
          </div>

          <div className="bg-purple-50 border-2 border-purple-200 rounded-lg p-4 hover:bg-purple-100 transition no-underline">
            <p className="text-lg font-semibold text-purple-900">Audit Logs</p>
            <p className="text-purple-700 text-sm mt-1">Track all admin actions and changes</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Recent Pending Devices</h2>
        {devicesLoading ? (
          <p className="text-gray-500">Loading devices...</p>
        ) : pendingDevices.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No pending devices - all good! ✓</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b-2 border-gray-200">
                <tr>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Device ID</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Device Name</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">OS</th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">Action</th>
                </tr>
              </thead>
              <tbody>
                {pendingDevices.slice(0, 5).map((device) => (
                  <tr key={device.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 font-mono text-xs text-gray-600">
                      {device.id.substring(0, 8)}...
                    </td>
                    <td className="py-3 px-4 text-gray-900">{device.device_name || 'Unknown'}</td>
                    <td className="py-3 px-4 text-gray-700">
                      {device.os_info?.system || 'N/A'}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <Link
                        to={`/devices/${device.id}`}
                        className="text-blue-600 font-medium hover:text-blue-800"
                      >
                        Review
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {pendingDevices.length > 5 && (
              <div className="text-center mt-4 pt-4 border-t">
                <Link
                  to="/devices/pending"
                  className="text-blue-600 font-medium hover:text-blue-800"
                >
                  View all {pendingDevices.length} pending devices →
                </Link>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}