import apiClient from './apiClient';

export const getUsers = () => {
  return apiClient.get('/users');
};

export const getUserDetails = (userId) => {
  return apiClient.get(`/users/${userId}`);
};

export const getUserDevices = (userId) => {
  return apiClient.get(`/users/${userId}/devices`);
};

export const createUser = (userData) => {
  return apiClient.post('/users', userData);
};

export const updateUser = (userId, userData) => {
  return apiClient.put(`/users/${userId}`, userData);
};

export const deleteUser = (userId) => {
  return apiClient.delete(`/users/${userId}`);
};

export const getUserRoles = (userId) => {
  return apiClient.get(`/users/${userId}/roles`);
};

export const updateUserRoles = (userId, roles) => {
  return apiClient.patch(`/users/${userId}/roles`, { roles });
};

const userService = {
  getUsers,
  getUserDetails,
  getUserDevices,
  createUser,
  updateUser,
  deleteUser,
  getUserRoles,
  updateUserRoles,
};

export default userService;