// OIDC Service for Keycloak integration
import axios from 'axios';

const KEYCLOAK_URL = process.env.REACT_APP_KEYCLOAK_URL || 'http://localhost:8080';
const REALM = process.env.REACT_APP_KEYCLOAK_REALM || 'master';
const CLIENT_ID = process.env.REACT_APP_KEYCLOAK_CLIENT_ID || 'admin-frontend';

class OIDCService {
  constructor() {
    this.config = null;
    this.codeVerifier = null;
    this.codeChallenge = null;
  }

  async initialize() {
    if (!this.config) {
      try {
        const response = await axios.get(
          `${KEYCLOAK_URL}/realms/${REALM}/.well-known/openid-configuration`
        );
        this.config = response.data;
      } catch (error) {
        console.error('Failed to fetch OIDC configuration:', error);
        throw error;
      }
    }
    return this.config;
  }

  generateCodeVerifier() {
    const array = new Uint32Array(56 / 2);
    crypto.getRandomValues(array);
    this.codeVerifier = Array.from(array, dec => ('0' + dec.toString(16)).substr(-2)).join('');
    return this.codeVerifier;
  }

  async generateCodeChallenge(verifier) {
    const encoder = new TextEncoder();
    const data = encoder.encode(verifier);
    const digest = await crypto.subtle.digest('SHA-256', data);
    const base64 = btoa(String.fromCharCode(...new Uint8Array(digest)))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
    this.codeChallenge = base64;
    return base64;
  }

  async login() {
    await this.initialize();
    const verifier = this.generateCodeVerifier();
    const challenge = await this.generateCodeChallenge(verifier);
    
    localStorage.setItem('code_verifier', verifier);
    
    const params = new URLSearchParams({
      client_id: CLIENT_ID,
      redirect_uri: window.location.origin + '/callback',
      response_type: 'code',
      scope: 'openid profile email roles',
      code_challenge: challenge,
      code_challenge_method: 'S256',
    });

    window.location.href = `${this.config.authorization_endpoint}?${params.toString()}`;
  }

  async handleCallback(code) {
    await this.initialize();
    
    // Prevent code reuse - check if this code was already used
    const usedCode = localStorage.getItem('used_code');
    if (usedCode === code) {
      console.warn('Authorization code already used, checking if user is already authenticated');
      // If code was used but we have tokens, user might already be logged in
      const existingToken = localStorage.getItem('access_token');
      if (existingToken) {
        // Try to get user info from storage first
        const storedUser = localStorage.getItem('user_info');
        if (storedUser) {
          try {
            const userInfo = JSON.parse(storedUser);
            console.log('Using stored user info for reused code');
            return { access_token: existingToken, userInfo };
          } catch (e) {
            console.warn('Failed to parse stored user info, will try to get from token');
          }
        }
        
        // If no stored user info, try to decode from token
        try {
          const payload = JSON.parse(atob(existingToken.split('.')[1]));
          // Check if token is expired
          const exp = payload.exp * 1000;
          if (exp < Date.now()) {
            console.warn('Existing token is expired, clearing and forcing re-login');
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('id_token');
            localStorage.removeItem('user_info');
            localStorage.removeItem('used_code');
            throw new Error('Token expired. Please try logging in again.');
          }
          
          const userInfo = {
            sub: payload.sub,
            email: payload.email,
            preferred_username: payload.preferred_username || payload.sub,
            name: payload.name,
            realm_access: payload.realm_access || { roles: [] }
          };
          localStorage.setItem('user_info', JSON.stringify(userInfo));
          console.log('Decoded user info from existing token for reused code');
          return { access_token: existingToken, userInfo };
        } catch (decodeError) {
          console.error('Failed to decode existing token:', decodeError);
          // If decode fails, token might be invalid, clear and force re-login
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('id_token');
          localStorage.removeItem('user_info');
          localStorage.removeItem('used_code');
          throw new Error('Invalid token. Please try logging in again.');
        }
      }
      
      // If we get here, code was used but we don't have valid tokens
      // This is OK - just return null and let the callback page handle it
      console.warn('Code was used but no valid tokens found');
      return null;
    }
    
    const verifier = localStorage.getItem('code_verifier');
    
    if (!verifier) {
      throw new Error('Code verifier not found. Please try logging in again.');
    }

    const params = new URLSearchParams({
      grant_type: 'authorization_code',
      code: code,
      redirect_uri: window.location.origin + '/callback',
      client_id: CLIENT_ID,
      code_verifier: verifier,
    });

    try {
      const response = await axios.post(
        this.config.token_endpoint,
        params.toString(),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );

      if (!response.data || !response.data.access_token) {
        throw new Error('Invalid response from token endpoint');
      }

      const { access_token, refresh_token, id_token } = response.data;
      
      // Validate tokens exist
      if (!access_token) {
        throw new Error('No access token received from Keycloak');
      }
      
      // Mark code as used FIRST to prevent duplicate processing
      localStorage.setItem('used_code', code);
      
      localStorage.setItem('access_token', access_token);
      if (refresh_token) {
        localStorage.setItem('refresh_token', refresh_token);
      }
      if (id_token) {
        localStorage.setItem('id_token', id_token);
      }
      localStorage.removeItem('code_verifier');

      // Decode and store user info
      // Always try to decode from token first (more reliable)
      let userInfo = null;
      try {
        const payload = JSON.parse(atob(access_token.split('.')[1]));
        userInfo = {
          sub: payload.sub,
          email: payload.email || payload.preferred_username || payload.sub,
          preferred_username: payload.preferred_username || payload.sub,
          name: payload.name || payload.preferred_username || payload.sub,
          realm_access: payload.realm_access || { roles: payload.realm_access?.roles || [] }
        };
        console.log('Decoded user info from token:', userInfo);
      } catch (decodeError) {
        console.error('Failed to decode token:', decodeError);
        // If token decode fails, try getUserInfo endpoint
        try {
          console.log('Trying getUserInfo endpoint as fallback');
          userInfo = await this.getUserInfo(access_token);
          if (!userInfo) {
            throw new Error('getUserInfo returned null');
          }
          console.log('Got user info from endpoint:', userInfo);
        } catch (userInfoError) {
          console.error('Failed to get user info from endpoint:', userInfoError);
          // Last resort: create minimal user info from token sub
          try {
            const payload = JSON.parse(atob(access_token.split('.')[0] + '.' + access_token.split('.')[1] + '.'));
            userInfo = {
              sub: payload.sub || 'unknown',
              email: payload.email || payload.preferred_username || 'unknown@example.com',
              preferred_username: payload.preferred_username || payload.sub || 'unknown',
              name: payload.name || payload.preferred_username || 'Unknown User',
              realm_access: payload.realm_access || { roles: [] }
            };
            console.log('Created minimal user info from token payload');
          } catch (finalError) {
            console.error('All user info extraction methods failed:', finalError);
            throw new Error('Failed to get user information from token or endpoint');
          }
        }
      }
      
      // Store user info
      if (userInfo) {
        localStorage.setItem('user_info', JSON.stringify(userInfo));
        console.log('User info stored successfully');
        return { access_token, userInfo };
      } else {
        throw new Error('User info is null after all attempts');
      }
    } catch (error) {
      console.error('Token exchange failed:', error);
      
      // Clear any partial state
      localStorage.removeItem('code_verifier');
      localStorage.removeItem('used_code');
      
      // Provide more helpful error messages
      if (error.response) {
        const status = error.response.status;
        const errorData = error.response.data;
        console.error('Token exchange error:', status, errorData);
        
        if (status === 400) {
          const errorDesc = errorData?.error_description || errorData?.error || 'Invalid authorization code';
          // If code was already used, return null instead of throwing
          if (errorDesc.includes('already used') || errorDesc.includes('invalid_code')) {
            console.warn('Code already used, returning null');
            return null;
          }
          throw new Error(errorDesc + '. Please try logging in again.');
        } else if (status === 401) {
          throw new Error('Authentication failed. Please try logging in again.');
        } else {
          throw new Error(`Authentication error: ${errorData?.error || error.message}`);
        }
      } else if (error.request) {
        console.error('Network error during token exchange:', error.request);
        throw new Error('Cannot connect to authentication server. Please check your connection.');
      } else {
        console.error('Token exchange error:', error.message);
        throw new Error(`Authentication failed: ${error.message}`);
      }
    }
  }

  async getUserInfo(accessToken) {
    await this.initialize();
    try {
      const response = await axios.get(this.config.userinfo_endpoint, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
      return response.data;
    } catch (error) {
      console.error('Failed to get user info:', error);
      throw error;
    }
  }

  async refreshToken() {
    await this.initialize();
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const params = new URLSearchParams({
      grant_type: 'refresh_token',
      refresh_token: refreshToken,
      client_id: CLIENT_ID,
    });

    try {
      const response = await axios.post(
        this.config.token_endpoint,
        params.toString(),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );

      const { access_token, refresh_token } = response.data;
      localStorage.setItem('access_token', access_token);
      if (refresh_token) {
        localStorage.setItem('refresh_token', refresh_token);
      }

      return access_token;
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.logout();
      throw error;
    }
  }

  getAccessToken() {
    return localStorage.getItem('access_token');
  }

  async logout() {
    // Get tokens BEFORE clearing storage
    const idToken = localStorage.getItem('id_token');
    
    // Initialize config if not already done
    if (!this.config) {
      try {
        await this.initialize();
      } catch (error) {
        console.error('Failed to initialize OIDC config for logout:', error);
        // Continue with logout anyway - construct URL manually
      }
    }
    
    // Construct logout URL
    let logoutUrl;
    if (this.config && this.config.end_session_endpoint) {
      logoutUrl = this.config.end_session_endpoint;
    } else {
      // Fallback: construct logout URL manually
      logoutUrl = `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/logout`;
    }
    
    // Build logout parameters - order matters for Keycloak
    const params = new URLSearchParams();
    
    // Add id_token_hint FIRST if available (helps Keycloak identify the session)
    if (idToken) {
      params.append('id_token_hint', idToken);
    }
    
    // Add post_logout_redirect_uri - must match exactly what's in Keycloak config
    const redirectUri = window.location.origin + '/login';
    params.append('post_logout_redirect_uri', redirectUri);
    
    // Add client_id - REQUIRED when using post_logout_redirect_uri
    // Ensure CLIENT_ID is defined and not empty
    const clientId = CLIENT_ID || 'admin-frontend';
    if (clientId) {
      params.append('client_id', clientId);
    }
    
    console.log('Logging out with params:', {
      logoutUrl,
      redirectUri,
      clientId,
      hasIdToken: !!idToken
    });
    
    // Clear all local storage BEFORE redirect
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('id_token');
    localStorage.removeItem('user_info');
    localStorage.removeItem('code_verifier');
    localStorage.removeItem('used_code');
    
    // Redirect to Keycloak logout - this will end the Keycloak session
    // Use replace to prevent back button from going back to logout page
    window.location.replace(`${logoutUrl}?${params.toString()}`);
  }

  isAuthenticated() {
    const token = this.getAccessToken();
    if (!token) return false;

    // Check if token is expired (basic check)
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const exp = payload.exp * 1000;
      if (Date.now() >= exp) {
        return false;
      }
    } catch (e) {
      return false;
    }

    return true;
  }

  getRoles() {
    const userInfo = localStorage.getItem('user_info');
    if (!userInfo) {
      console.log('No user_info in localStorage');
      return [];
    }
    
    try {
      const user = JSON.parse(userInfo);
      const roles = user.realm_access?.roles || [];
      console.log('Extracted roles from user_info:', roles);
      return roles;
    } catch (e) {
      console.error('Failed to parse user_info or extract roles:', e);
      return [];
    }
  }
}

const oidcService = new OIDCService();
export default oidcService;

