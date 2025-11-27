import apiClient from './apiClient';

/**
 * List available resources
 * Uses OIDC token from apiClient (automatically added by interceptor)
 * Backend verifies device state from latest posture reports
 */
export const listResources = () => {
  return apiClient.get('/resources/list');
};

/**
 * Download a resource
 * Uses OIDC token from apiClient (automatically added by interceptor)
 * Backend verifies device state before allowing download
 */
export const downloadResource = (resourceId) => {
  return apiClient.get(`/resources/download/${resourceId}`, {
    responseType: 'blob' // For file downloads
  });
};

const resourceService = {
  listResources,
  downloadResource,
};

export default resourceService;

