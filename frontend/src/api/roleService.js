import apiClient from './apiClient';

export const getRoles = () => {
  return apiClient.get('/roles');
};

export const getRole = (roleName) => {
  return apiClient.get(`/roles/${roleName}`);
};

export const createRole = (roleData) => {
  return apiClient.post('/roles', roleData);
};

export const updateRole = (roleName, roleData) => {
  return apiClient.put(`/roles/${roleName}`, roleData);
};

export const deleteRole = (roleName) => {
  return apiClient.delete(`/roles/${roleName}`);
};

const roleService = {
  getRoles,
  getRole,
  createRole,
  updateRole,
  deleteRole,
};

export default roleService;

