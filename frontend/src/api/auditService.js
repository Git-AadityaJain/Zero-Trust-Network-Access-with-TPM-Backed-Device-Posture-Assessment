import apiClient from './apiClient';

export const getAuditLogs = (filters = {}) => {
  const params = {};
  
  if (filters.deviceId) {
    params.device_id = filters.deviceId;
  }
  if (filters.action) {
    params.action = filters.action;
  }
  if (filters.actor) {
    params.actor = filters.actor;
  }
  if (filters.startDate) {
    params.start_date = filters.startDate;
  }
  if (filters.endDate) {
    params.end_date = filters.endDate;
  }
  
  return apiClient.get('/audit/devices', { params });
};

export default {
  getAuditLogs,
};