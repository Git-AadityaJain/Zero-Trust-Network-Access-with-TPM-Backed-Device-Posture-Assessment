import apiClient from './apiClient';

/**
 * Request policy decision for access
 * Called after login to verify user + device + context
 */
export const requestPolicyDecision = (resource = '*', context = {}) => {
  return apiClient.post('/access/decision', {
    resource,
    context
  });
};

const accessService = {
  requestPolicyDecision,
};

export default accessService;

