import apiClient from './apiClient';

/**
 * Request a challenge for TPM-based device attestation
 * The challenge must be signed by the device's TPM before requesting a token
 */
export const requestChallenge = (deviceId) => {
  return apiClient.post('/tokens/challenge', {
    device_id: deviceId
  });
};

/**
 * Sign a challenge using the DPA agent
 * Calls the DPA's local API to sign the challenge with TPM
 * 
 * The DPA API server should be running on http://localhost:8081
 * Start it with: python dpa/start_api_server.py
 */
export const signChallengeWithDPA = async (challenge) => {
  const dpaApiUrl = process.env.REACT_APP_DPA_API_URL || 'http://localhost:8081/sign-challenge';
  
  try {
    const response = await fetch(dpaApiUrl, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ challenge })
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || `DPA API error: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    
    if (!data.signature) {
      throw new Error('DPA API did not return a signature');
    }
    
    return data.signature;
  } catch (error) {
    if (error.message.includes('fetch')) {
      throw new Error(
        'Failed to connect to DPA API. ' +
        'Please ensure the DPA agent is running: python dpa/start_api_server.py'
      );
    }
    throw error;
  }
};

/**
 * Issue a device access token after TPM attestation
 * Requires a challenge and its TPM signature
 */
export const issueToken = async (deviceId, challenge, challengeSignature, resource = '*', expiresInMinutes = 15) => {
  return apiClient.post('/tokens/issue', {
    device_id: deviceId,
    challenge: challenge,
    challenge_signature: challengeSignature,
    resource: resource,
    expires_in_minutes: expiresInMinutes
  });
};

/**
 * Legacy method for backward compatibility
 * Now requires challenge and signature - use requestChallenge and signChallengeWithDPA first
 */
export const issueTokenLegacy = (deviceId, resource = '*', expiresInMinutes = 15) => {
  console.warn('issueTokenLegacy is deprecated. Use requestChallenge + signChallengeWithDPA + issueToken instead.');
  return apiClient.post('/tokens/issue', {
    device_id: deviceId,
    resource: resource,
    expires_in_minutes: expiresInMinutes
  });
};

export const refreshToken = (token) => {
  return apiClient.post('/tokens/refresh', {
    token: token
  });
};

export const verifyToken = (token) => {
  return apiClient.post('/tokens/verify', {
    token: token
  });
};

const tokenService = {
  requestChallenge,
  signChallengeWithDPA,
  issueToken,
  issueTokenLegacy,
  refreshToken,
  verifyToken,
};

export default tokenService;

