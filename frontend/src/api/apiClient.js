import axios from 'axios';
import oidcService from '../services/oidcService';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  async (config) => {
    let token = oidcService.getAccessToken();
    
    // If token is expired or about to expire, try to refresh
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const exp = payload.exp * 1000;
        const now = Date.now();
        
        // Refresh if token expires in less than 1 minute
        if (exp - now < 60 * 1000) {
          token = await oidcService.refreshToken();
        }
      } catch (e) {
        // If parsing fails, try to refresh
        try {
          token = await oidcService.refreshToken();
        } catch (refreshError) {
          oidcService.logout();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }
    }
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      try {
        // Try to refresh token
        await oidcService.refreshToken();
        // Retry the original request
        return apiClient.request(error.config);
      } catch (refreshError) {
        oidcService.logout();
        window.location.href = '/login';
      }
    }
    if (error.response?.status === 403) {
      console.error('Access denied: Insufficient permissions');
    }
    return Promise.reject(error);
  }
);

export default apiClient;