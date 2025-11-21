import React, { useState } from 'react';
import { usePendingDevices } from '../hooks/useDevices';

export default function PendingDevicesPage() {
  const { devices, loading, error, refetch } = usePendingDevices(true, 3000);

  return (
    <div className="space-y-6 p-6">
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
                        <p className="text-gray-500 text-xs font-mono">{device.id.substring(0, 12)}...</p>
                      </div>
                    </td>

                    <td className="py-4 px-6">
                      <span className="px-3 py-1 bg-blue-100 text-blue-900 text-xs rounded-full font-medium">
                        {device.os_info?.system || 'N/A'} {device.os_info?.release}
                      </span>
                    </td>

                    <td className="py-4 px-6">
                      <span className={`px-3 py-1 text-xs rounded-full font-medium ${
                        device.firewall?.firewall_enabled
                          ? 'bg-green-100 text-green-900'
                          : 'bg-red-100 text-red-900'
                      }`}>
                        {device.firewall?.firewall_enabled ? '✓ Enabled' : '✗ Disabled'}
                      </span>
                    </td>

                    <td className="py-4 px-6">
                      <span className={`px-3 py-1 text-xs rounded-full font-medium ${
                        device.disk_encryption?.encryption_enabled
                          ? 'bg-green-100 text-green-900'
                          : 'bg-red-100 text-red-900'
                      }`}>
                        {device.disk_encryption?.encryption_enabled ? '✓ Enabled' : '✗ Disabled'}
                      </span>
                    </td>

                    <td className="py-4 px-6">
                      <span className={`px-3 py-1 text-xs rounded-full font-medium ${
                        device.antivirus?.running
                          ? 'bg-green-100 text-green-900'
                          : 'bg-red-100 text-red-900'
                      }`}>
                        {device.antivirus?.running ? '✓ Running' : '✗ Not Running'}
                      </span>
                    </td>

                    <td className="py-4 px-6 text-center">
                      <div className="flex justify-center gap-2">
                        <button className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded transition font-medium text-sm">
                          Approve
                        </button>
                        <button className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded transition font-medium text-sm">
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
    </div>
  );
}