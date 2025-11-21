import apiClient from './apiClient';

export const getDevices = (status = null) => {
  const params = status ? { status } : {};
  return apiClient.get('/api/device', { params });
};

export const getPendingDevices = () => {
  return apiClient.get('/api/device/pending');
};

export const getDeviceDetails = (deviceId) => {
  return apiClient.get(`/api/device/${deviceId}`);
};

export const getDeviceStatus = (deviceId) => {
  return apiClient.get(`/api/device/${deviceId}/status`);
};

export const approveDevice = (deviceId, userData) => {
  return apiClient.patch(`/api/device/${deviceId}/approve`, userData);
};

export const rejectDevice = (deviceId, reason = '') => {
  return apiClient.patch(`/api/device/${deviceId}/reject`, { reason });
};

export const assignDeviceToUser = (deviceId, userId) => {
  return apiClient.patch(`/api/device/${deviceId}/assign`, { user_id: userId });
};

export default {
  getDevices,
  getPendingDevices,
  getDeviceDetails,
  getDeviceStatus,
  approveDevice,
  rejectDevice,
  assignDeviceToUser,
};