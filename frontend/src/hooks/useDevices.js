import { useState, useEffect } from 'react';
import * as deviceService from '../api/deviceService';

export const useDevices = (status = null, autoRefresh = false, refreshInterval = 5000) => {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDevices = async () => {
    try {
      setLoading(true);
      const response = await deviceService.getDevices(status);
      setDevices(response.data || []);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to fetch devices');
      setDevices([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();

    if (autoRefresh) {
      const interval = setInterval(fetchDevices, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [status, autoRefresh, refreshInterval]);

  return { devices, loading, error, refetch: fetchDevices };
};

export const usePendingDevices = (autoRefresh = true, refreshInterval = 3000) => {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPendingDevices = async () => {
    try {
      setLoading(true);
      const response = await deviceService.getPendingDevices();
      setDevices(response.data || []);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to fetch pending devices');
      setDevices([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPendingDevices();

    if (autoRefresh) {
      const interval = setInterval(fetchPendingDevices, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  return { devices, loading, error, refetch: fetchPendingDevices };
};

export const useDeviceDetails = (deviceId) => {
  const [device, setDevice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!deviceId) return;

    const fetchDeviceDetails = async () => {
      try {
        setLoading(true);
        const response = await deviceService.getDeviceDetails(deviceId);
        setDevice(response.data);
        setError(null);
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to fetch device details');
        setDevice(null);
      } finally {
        setLoading(false);
      }
    };

    fetchDeviceDetails();
  }, [deviceId]);

  return { device, loading, error };
};