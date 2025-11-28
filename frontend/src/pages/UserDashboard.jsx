import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/apiClient';
import resourceService from '../api/resourceService';
import deviceStateService from '../api/deviceStateService';
import accessService from '../api/accessService';

export default function UserDashboard() {
  const { user, hasRole } = useAuth();
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deviceState, setDeviceState] = useState(null);
  const [policyDecision, setPolicyDecision] = useState(null);
  const [error, setError] = useState(null);
  const [downloading, setDownloading] = useState({});

  // Check device state and policy decision after login
  useEffect(() => {
    const loadUserResources = async () => {
      if (!user) {
        setLoading(false);
        return;
      }

      // Check if user has dpa-device role - required for access
      if (!hasRole('dpa-device') && !hasRole('admin')) {
        setLoading(false);
        setError('Access denied. You must have the dpa-device role to access resources. Please ensure your device is enrolled and compliant.');
        return;
      }

      try {
        setLoading(true);
        setError(null);

        // Step 1: Request policy decision (login-time verification)
        // This verifies user + device + context before allowing access
        let decision;
        try {
          const decisionResponse = await accessService.requestPolicyDecision('*', {
            time: new Date().toISOString(),
            source: 'webapp'
          });
          decision = decisionResponse.data;
          setPolicyDecision(decision);
          
          if (!decision.allowed) {
            // Access denied by policy
            setLoading(false);
            let errorMsg = decision.reason || 'Access denied by policy.';
            
            if (decision.risk_level === 'critical') {
              errorMsg = '⚠️ CRITICAL: TPM key verification failed. Device may have been compromised.';
            } else if (decision.risk_level === 'high') {
              errorMsg = `⚠️ HIGH RISK: ${decision.reason || 'Access denied.'}`;
            } else if (decision.requires_step_up) {
              errorMsg = `${decision.reason || 'Access denied.'} Additional authentication may be required.`;
            }
            
            setError(errorMsg);
            return;
          }
        } catch (err) {
          console.error('Policy decision failed:', err);
          // Continue to device state check even if policy decision fails
          // (for backward compatibility)
        }

        // Step 2: Check device state from backend (proper ZTNA flow)
        const stateResponse = await deviceStateService.getCurrentDeviceState();
        const state = stateResponse.data;
        
        setDeviceState(state);

        // Step 3: Verify device is ready for resource access
        if (state.has_dpa && state.tpm_key_match && state.is_compliant && state.is_enrolled) {
          // Device is verified - load resources using OIDC token
          await loadResources();
        } else {
          // Device not ready - show appropriate message
          setLoading(false);
          if (!state.has_dpa) {
            setError('DPA agent not reporting. Please ensure the DPA agent is running on your device.');
          } else if (!state.tpm_key_match) {
            setError('TPM key verification failed. Device may have been compromised.');
          } else if (!state.is_compliant) {
            setError(`Device is not compliant: ${state.violations?.join(', ') || 'Unknown violations'}`);
          } else {
            setError(state.message || 'Device is not ready for resource access.');
          }
        }
      } catch (err) {
        console.error('Failed to check device state:', err);
        if (err.response?.status === 403) {
          setError('Access denied. Your device must be enrolled, compliant, and have valid TPM key.');
        } else {
          setError('Failed to check device state. Please try again.');
        }
        setLoading(false);
      }
    };

    loadUserResources();
  }, [user]);

  const loadResources = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch resources using OIDC token (already in apiClient interceptor)
      // Backend will verify device state based on latest posture reports
      const response = await resourceService.listResources();
      setResources(response.data.resources || []);
      setLoading(false);
    } catch (err) {
      console.error('Failed to load resources:', err);
      if (err.response?.status === 401 || err.response?.status === 403) {
        setError('Access denied. Your device must be enrolled, compliant, and have valid TPM key to access resources.');
      } else {
        setError('Failed to load resources. Please try again.');
      }
      setLoading(false);
    }
  };

  const handleDownload = async (resource) => {
    if (!deviceState || !deviceState.has_dpa || !deviceState.tpm_key_match || !deviceState.is_compliant) {
      alert('Device not ready. Please ensure your device is enrolled, compliant, and TPM key matches.');
      return;
    }

    try {
      setDownloading({ ...downloading, [resource.id]: true });
      
      // Download resource using OIDC token (already in apiClient)
      const response = await resourceService.downloadResource(resource.id);
      
      // Handle response (could be JSON for demo or blob for actual file)
      if (response.data instanceof Blob) {
        // Create download link
        const url = window.URL.createObjectURL(response.data);
        const a = document.createElement('a');
        a.href = url;
        a.download = resource.name;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        // Demo response
        alert(`Download initiated for ${resource.name}\n\n${JSON.stringify(response.data, null, 2)}`);
      }
    } catch (err) {
      console.error('Download failed:', err);
      if (err.response?.status === 401 || err.response?.status === 403) {
        alert('Access denied. Your device must be enrolled and compliant to download resources.');
      } else {
        alert(`Failed to download ${resource.name}. Please try again.`);
      }
    } finally {
      setDownloading({ ...downloading, [resource.id]: false });
    }
  };

  const getFileIcon = (type) => {
    switch (type) {
      case 'document':
        return '📄';
      case 'archive':
        return '📦';
      case 'folder':
        return '📁';
      default:
        return '📎';
    }
  };

  const getRoleBadge = (role) => {
    if (role === 'admin') {
      return <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">Admin Only</span>;
    } else if (role === 'user') {
      return <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">User Access</span>;
    } else {
      return <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">Public</span>;
    }
  };


  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Resources</h1>
        <div className="flex items-center space-x-3">
          {deviceState?.has_dpa && (
            <span className="px-3 py-1 text-sm bg-green-100 text-green-800 rounded-full font-medium">
              ✓ DPA Active
            </span>
          )}
          {deviceState?.tpm_key_match && (
            <span className="px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-full font-medium">
              ✓ TPM Verified
            </span>
          )}
          {deviceState?.is_compliant && (
            <span className="px-3 py-1 text-sm bg-green-100 text-green-800 rounded-full font-medium">
              ✓ Compliant
            </span>
          )}
          {hasRole('admin') && (
            <span className="px-3 py-1 text-sm bg-purple-100 text-purple-800 rounded-full font-medium">
              Admin Access
            </span>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border-2 border-red-300 rounded-lg p-6">
          <div className="flex items-start">
            <div className="text-3xl mr-4">🚫</div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-red-900 mb-2">Access Denied</h3>
              <p className="text-sm text-red-800 mb-3">{error}</p>
              {error.includes('dpa-device role') && (
                <div className="bg-white border border-red-200 rounded p-3 mt-3">
                  <p className="text-xs text-gray-700">
                    <strong>What you need to do:</strong>
                  </p>
                  <ul className="text-xs text-gray-600 mt-2 list-disc list-inside space-y-1">
                    <li>Ensure your device is enrolled in the system</li>
                    <li>Make sure your device is compliant with security policies</li>
                    <li>Contact your administrator if you believe you should have access</li>
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading resources...</p>
        </div>
      ) : resources.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <div className="text-4xl mb-4">📂</div>
          <p className="text-gray-600">No resources available.</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <h2 className="text-lg font-semibold text-gray-900">Available Resources</h2>
            <p className="text-sm text-gray-500 mt-1">
              Protected resources - Access requires device attestation
            </p>
          </div>
          
          <div className="divide-y divide-gray-200">
            {resources.map((resource) => (
              <div
                key={resource.id}
                className="px-6 py-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 flex-1">
                    <div className="text-3xl">{getFileIcon(resource.type)}</div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h3 className="text-sm font-medium text-gray-900">
                          {resource.name}
                        </h3>
                        {getRoleBadge(resource.role)}
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {resource.type.charAt(0).toUpperCase() + resource.type.slice(1)}
                        {resource.size !== '-' && ` • ${resource.size}`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    {resource.type !== 'folder' && (
                      <button
                        onClick={() => handleDownload(resource)}
                        disabled={downloading[resource.id] || !deviceState?.has_dpa || !deviceState?.tpm_key_match || !deviceState?.is_compliant}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white text-sm rounded-lg transition-colors"
                      >
                        {downloading[resource.id] ? 'Downloading...' : 'Download'}
                      </button>
                    )}
                    {resource.type === 'folder' && (
                      <button
                        onClick={() => alert('Folder browsing will be implemented after testing.')}
                        className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded-lg transition-colors"
                      >
                        Open
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {policyDecision && (
        <div className={`border rounded-lg p-4 mb-4 ${
          policyDecision.allowed && policyDecision.risk_level === 'low'
            ? 'bg-green-50 border-green-200'
            : policyDecision.risk_level === 'critical'
            ? 'bg-red-50 border-red-200'
            : 'bg-yellow-50 border-yellow-200'
        }`}>
          <div className="flex items-start">
            <div className="text-2xl mr-3">
              {policyDecision.allowed && policyDecision.risk_level === 'low' ? '✅' : '⚠️'}
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-semibold mb-1">
                Policy Decision: {policyDecision.allowed ? 'Access Granted' : 'Access Denied'}
                {policyDecision.risk_level !== 'low' && (
                  <span className={`ml-2 px-2 py-0.5 rounded text-xs ${
                    policyDecision.risk_level === 'critical' ? 'bg-red-200 text-red-800' :
                    policyDecision.risk_level === 'high' ? 'bg-orange-200 text-orange-800' :
                    'bg-yellow-200 text-yellow-800'
                  }`}>
                    Risk: {policyDecision.risk_level.toUpperCase()}
                  </span>
                )}
              </h3>
              <p className="text-sm mb-2">{policyDecision.reason}</p>
              {policyDecision.device_name && (
                <div className="text-xs text-gray-600 mt-2">
                  <strong>Device:</strong> {policyDecision.device_name}
                  {policyDecision.requires_step_up && (
                    <span className="ml-4 text-orange-600">
                      ⚠️ Step-up authentication may be required
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
      {deviceState && (
        <div className={`border rounded-lg p-4 ${
          deviceState.has_dpa && deviceState.tpm_key_match && deviceState.is_compliant
            ? 'bg-green-50 border-green-200'
            : 'bg-yellow-50 border-yellow-200'
        }`}>
          <div className="flex items-start">
            <div className="text-2xl mr-3">
              {deviceState.has_dpa && deviceState.tpm_key_match && deviceState.is_compliant ? '✅' : '⚠️'}
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-semibold mb-1">
                {deviceState.has_dpa && deviceState.tpm_key_match && deviceState.is_compliant
                  ? 'Device Status: Ready'
                  : 'Device Status: Not Ready'}
              </h3>
              <p className="text-sm mb-2">{deviceState.message}</p>
              {deviceState.device_name && (
                <div className="text-xs text-gray-600 mt-2">
                  <strong>Device:</strong> {deviceState.device_name}
                  {deviceState.last_posture_time && (
                    <span className="ml-4">
                      <strong>Last Posture:</strong> {new Date(deviceState.last_posture_time).toLocaleString()}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
