import apiClient from './apiClient';

/**
 * Get current device state for the authenticated user
 * This checks if the user has a DPA agent, TPM key match, and compliant device
 */
export const getCurrentDeviceState = () => {
  return apiClient.get('/users/me/current-device-state');
};

const deviceStateService = {
  getCurrentDeviceState,
};

export default deviceStateService;

