import apiClient from './apiClient';

export const getUsers = () => {
  return apiClient.get('/api/users');
};

export const getUserDetails = (userId) => {
  return apiClient.get(`/api/users/${userId}`);
};

export const getUserDevices = (userId) => {
  return apiClient.get(`/api/user/${userId}/devices`);
};

export const createUser = (userData) => {
  return apiClient.post('/api/users', userData);
};

export const updateUser = (userId, userData) => {
  return apiClient.put(`/api/users/${userId}`, userData);
};

export const deleteUser = (userId) => {
  return apiClient.delete(`/api/users/${userId}`);
};

export default {
  getUsers,
  getUserDetails,
  getUserDevices,
  createUser,
  updateUser,
  deleteUser,
};