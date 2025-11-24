import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();

  const handleLogin = async () => {
    setError('');
    setLoading(true);

    try {
      await login();
    } catch (err) {
      setError('Login failed. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-blue-700 to-blue-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="text-6xl mb-4">🔐</div>
          <h1 className="text-4xl font-bold text-white mb-2">ZTNA</h1>
          <p className="text-blue-100">Device Enrollment & Management System</p>
        </div>

        <div className="bg-white rounded-lg shadow-2xl p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            Administrator Login
          </h2>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          <button
            onClick={handleLogin}
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Redirecting to Keycloak...' : 'Login with Keycloak'}
          </button>

          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-900">
              <strong>OIDC Authentication:</strong>
              <br />
              You will be redirected to Keycloak for secure authentication.
              <br />
              <span className="text-xs text-blue-700 mt-2 block">
                Using PKCE flow for enhanced security
              </span>
            </p>
          </div>
        </div>

        <div className="text-center mt-8">
          <p className="text-blue-100 text-sm">
            Secure Zero-Trust Network Access
          </p>
          <p className="text-blue-200 text-xs mt-2">
            Keycloak Integration Ready • Device Posture Assessment
          </p>
        </div>
      </div>
    </div>
  );
}