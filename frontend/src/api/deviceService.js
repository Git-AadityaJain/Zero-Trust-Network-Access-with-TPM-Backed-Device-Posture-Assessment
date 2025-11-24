import apiClient from './apiClient';

export const getDevices = (status = null) => {
  const params = status ? { status_filter: status } : {};
  return apiClient.get('/devices', { params });
};

export const getPendingDevices = () => {
  return apiClient.get('/devices/pending');
};

export const getDeviceDetails = (deviceId) => {
  return apiClient.get(`/devices/${deviceId}`);
};

export const getDeviceStatus = (deviceId) => {
  return apiClient.get(`/devices/status/${deviceId}`);
};

export const approveDevice = (deviceId, userData) => {
  return apiClient.patch(`/devices/${deviceId}/approve`, userData);
};

export const rejectDevice = (deviceId, rejectionData) => {
  return apiClient.patch(`/devices/${deviceId}/reject`, rejectionData);
};

export const assignDeviceToUser = (deviceId, userId) => {
  return apiClient.patch(`/devices/${deviceId}/assign`, { user_id: userId });
};

export const deleteDevice = (deviceId) => {
  return apiClient.delete(`/devices/${deviceId}`);
};

export const getDevicePostureHistory = (deviceId, limit = 10) => {
  return apiClient.get(`/posture/device/${deviceId}/history`, {
    params: { limit },
  });
};

const deviceService = {
  getDevices,
  getPendingDevices,
  getDeviceDetails,
  getDeviceStatus,
  approveDevice,
  rejectDevice,
  assignDeviceToUser,
  deleteDevice,
  getDevicePostureHistory,
};

export default deviceService;