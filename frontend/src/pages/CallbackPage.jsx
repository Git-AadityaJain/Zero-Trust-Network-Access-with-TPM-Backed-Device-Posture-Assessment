import React, { useEffect, useState, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function CallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { handleCallback } = useAuth();
  const [error, setError] = useState(null);
  const processingRef = useRef(false);
  const processedRef = useRef(false);

  useEffect(() => {
    const code = searchParams.get('code');
    const errorParam = searchParams.get('error');
    let isMounted = true;
    
    // Check if we already have a valid session - if so, redirect immediately
    const hasToken = localStorage.getItem('access_token');
    const hasUserInfo = localStorage.getItem('user_info');
    if (hasToken && hasUserInfo && !code) {
      console.log('Valid session found, checking role for redirect');
      try {
        const user = JSON.parse(hasUserInfo);
        const roles = user.realm_access?.roles || [];
        const isAdmin = roles.includes('admin');
        const redirectPath = isAdmin ? '/dashboard' : '/user-dashboard';
        console.log(`Redirecting to: ${redirectPath}`);
        window.location.replace(redirectPath);
      } catch (e) {
        console.error('Failed to parse user info, redirecting to login');
        window.location.replace('/login');
      }
      return;
    }
    
    // Prevent duplicate processing - use refs to persist across renders
    if (processingRef.current) {
      console.log('Callback already processing, skipping');
      return;
    }
    
    if (processedRef.current) {
      console.log('Callback already processed, checking for session');
      // If already processed, check for session and redirect
      if (hasToken && hasUserInfo) {
        console.log('Session exists, checking role for redirect');
        try {
          const user = JSON.parse(hasUserInfo);
          const roles = user.realm_access?.roles || [];
          const isAdmin = roles.includes('admin');
          const redirectPath = isAdmin ? '/dashboard' : '/user-dashboard';
          window.location.replace(redirectPath);
        } catch (e) {
          window.location.replace('/login');
        }
      } else {
        console.log('No session found, redirecting to login');
        window.location.replace('/login');
      }
      return;
    }

    if (errorParam) {
      if (isMounted) {
        setError(`Authentication failed: ${errorParam}`);
        setTimeout(() => navigate('/login'), 3000);
      }
      return;
    }

    if (code) {
      processingRef.current = true;
      console.log('Processing callback with code:', code.substring(0, 8) + '...');
      console.log('Full callback URL:', window.location.href);
      
      // Set a timeout to prevent infinite hanging
      const timeoutId = setTimeout(() => {
        if (isMounted && !processedRef.current) {
          console.error('Callback processing timeout after 15 seconds');
          processedRef.current = true;
          processingRef.current = false;
          setError('Authentication timeout. Please try again.');
          setTimeout(() => {
            window.location.replace('/login');
          }, 2000);
        }
      }, 15000); // 15 second timeout
      
      handleCallback(code)
        .then((result) => {
          clearTimeout(timeoutId);
          if (!isMounted) return;
          
          if (processedRef.current) {
            console.log('Already processed, skipping');
            return;
          }
          
          processedRef.current = true;
          processingRef.current = false;
          
          // Handle null result (code was used but no tokens)
          if (result === null || !result) {
            console.log('Code was used or no result, checking for existing session');
            const hasToken = localStorage.getItem('access_token');
            const storedUser = localStorage.getItem('user_info');
            if (hasToken && storedUser) {
              console.log('Found existing session, checking role for redirect');
              try {
                const user = JSON.parse(storedUser);
                const roles = user.realm_access?.roles || [];
                const isAdmin = roles.includes('admin');
                const redirectPath = isAdmin ? '/dashboard' : '/user-dashboard';
                window.location.replace(redirectPath);
              } catch (e) {
                window.location.replace('/login');
              }
              return;
            }
            // No valid session, redirect to login
            console.log('No valid session found, redirecting to login');
            setError('Session expired. Please log in again.');
            setTimeout(() => {
              window.location.replace('/login');
            }, 2000);
            return;
          }
          
          // Result should have both access_token and userInfo
          if (result && result.userInfo && result.access_token) {
            console.log('Authentication successful, checking user role for redirect');
            // Check user role and redirect accordingly
            const userRoles = result.userInfo.realm_access?.roles || [];
            const isAdmin = userRoles.includes('admin');
            const redirectPath = isAdmin ? '/dashboard' : '/user-dashboard';
            console.log(`User roles: [${userRoles.join(', ')}], redirecting to: ${redirectPath}`);
            // Use window.location.replace to prevent back button issues
            window.location.replace(redirectPath);
          } else {
            console.error('Invalid result from handleCallback:', result);
            // Check if tokens exist anyway (might have been stored)
            const token = localStorage.getItem('access_token');
            const user = localStorage.getItem('user_info');
            if (token && user) {
              console.log('Tokens exist in storage, checking role for redirect');
              try {
                const userData = JSON.parse(user);
                const roles = userData.realm_access?.roles || [];
                const isAdmin = roles.includes('admin');
                const redirectPath = isAdmin ? '/dashboard' : '/user-dashboard';
                window.location.replace(redirectPath);
              } catch (e) {
                window.location.replace('/login');
              }
            } else {
              setError('Authentication completed but user info not available');
              setTimeout(() => {
                window.location.replace('/login');
              }, 2000);
            }
          }
        })
        .catch((err) => {
          clearTimeout(timeoutId);
          if (!isMounted) return;
          
          if (processedRef.current) {
            console.log('Already processed, skipping error handling');
            return;
          }
          
          processedRef.current = true;
          processingRef.current = false;
          
          const errorMessage = err?.message || err?.toString() || 'Failed to complete authentication';
          console.error('Callback error:', err);
          console.error('Error details:', {
            message: errorMessage,
            stack: err?.stack,
            response: err?.response?.data
          });
          
          // If code was already used but we might have tokens, try to go to dashboard
          if (errorMessage.includes('already used') || errorMessage.includes('invalid_code') || errorMessage.includes('expired')) {
            const hasToken = localStorage.getItem('access_token');
            const storedUser = localStorage.getItem('user_info');
            if (hasToken && storedUser) {
              console.log('Code was used but token exists, checking role for redirect');
              try {
                const user = JSON.parse(storedUser);
                const roles = user.realm_access?.roles || [];
                const isAdmin = roles.includes('admin');
                const redirectPath = isAdmin ? '/dashboard' : '/user-dashboard';
                window.location.replace(redirectPath);
              } catch (e) {
                window.location.replace('/login');
              }
              return;
            }
          }
          
          // Show error and redirect
          setError(`Authentication failed: ${errorMessage}`);
          console.log('Redirecting to login due to error');
          setTimeout(() => {
            window.location.replace('/login');
          }, 3000);
        });
    } else {
      if (isMounted) {
        setError('No authorization code received');
        setTimeout(() => navigate('/login'), 3000);
      }
    }

    return () => {
      isMounted = false;
    };
  }, [searchParams, handleCallback, navigate]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
          <div className="text-red-600 text-center">
            <div className="text-4xl mb-4">❌</div>
            <h2 className="text-xl font-bold mb-2">Authentication Error</h2>
            <p>{error}</p>
            <p className="text-sm text-gray-500 mt-4">Redirecting to login...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Completing authentication...</p>
      </div>
    </div>
  );
}

