import apiClient from './apiClient';

export const getPolicies = (params = {}) => {
  return apiClient.get('/policies', { params });
};

export const getPolicyDetails = (policyId) => {
  return apiClient.get(`/policies/${policyId}`);
};

export const createPolicy = (policyData) => {
  return apiClient.post('/policies', policyData);
};

export const updatePolicy = (policyId, policyData) => {
  return apiClient.put(`/policies/${policyId}`, policyData);
};

export const deletePolicy = (policyId) => {
  return apiClient.delete(`/policies/${policyId}`);
};

export const activatePolicy = (policyId) => {
  return apiClient.post(`/policies/${policyId}/activate`);
};

export const deactivatePolicy = (policyId) => {
  return apiClient.post(`/policies/${policyId}/deactivate`);
};

const policyService = {
  getPolicies,
  getPolicyDetails,
  createPolicy,
  updatePolicy,
  deletePolicy,
  activatePolicy,
  deactivatePolicy,
};

export default policyService;

