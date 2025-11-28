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
  const redirectCheckIntervalRef = useRef(null);
  const timeoutIdRef = useRef(null);

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
    
    // If already processed, check for session and redirect immediately
    // This handles the case where processing completed but redirect didn't happen
    if (processedRef.current) {
      console.log('Callback already processed, checking for session');
      if (hasToken && hasUserInfo) {
        console.log('Session exists, checking role for redirect');
        try {
          const user = JSON.parse(hasUserInfo);
          const roles = user.realm_access?.roles || [];
          const isAdmin = roles.includes('admin');
          const redirectPath = isAdmin ? '/dashboard' : '/user-dashboard';
          console.log(`Redirecting to: ${redirectPath} (from processed check)`);
          window.location.replace(redirectPath);
        } catch (e) {
          console.error('Failed to parse user info, redirecting to login');
          window.location.replace('/login');
        }
      } else {
        console.log('No session found, redirecting to login');
        window.location.replace('/login');
      }
      return;
    }
    
    // Prevent duplicate processing - use refs to persist across renders
    if (processingRef.current) {
      console.log('Callback already processing, skipping');
      // But still check if processing completed in the meantime
      // This handles race conditions where processing finished between renders
      setTimeout(() => {
        if (hasToken && hasUserInfo && !processedRef.current) {
          // Processing might have completed, check again
          const checkToken = localStorage.getItem('access_token');
          const checkUser = localStorage.getItem('user_info');
          if (checkToken && checkUser) {
            console.log('Processing completed, redirecting now');
            try {
              const user = JSON.parse(checkUser);
              const roles = user.realm_access?.roles || [];
              const isAdmin = roles.includes('admin');
              const redirectPath = isAdmin ? '/dashboard' : '/user-dashboard';
              processedRef.current = true;
              processingRef.current = false;
              window.location.replace(redirectPath);
            } catch (e) {
              window.location.replace('/login');
            }
          }
        }
      }, 100);
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
      
      // Set up a polling mechanism to check if authentication completed
      // This ensures redirect happens even if promise handler doesn't execute
      redirectCheckIntervalRef.current = setInterval(() => {
        if (!isMounted) {
          if (redirectCheckIntervalRef.current) {
            clearInterval(redirectCheckIntervalRef.current);
            redirectCheckIntervalRef.current = null;
          }
          return;
        }
        
        // If processing is complete but we're still on callback page, redirect
        const checkToken = localStorage.getItem('access_token');
        const checkUser = localStorage.getItem('user_info');
        if (checkToken && checkUser && processedRef.current) {
          console.log('Polling check: Authentication complete, redirecting now');
          if (redirectCheckIntervalRef.current) {
            clearInterval(redirectCheckIntervalRef.current);
            redirectCheckIntervalRef.current = null;
          }
          try {
            const user = JSON.parse(checkUser);
            const roles = user.realm_access?.roles || [];
            const isAdmin = roles.includes('admin');
            const redirectPath = isAdmin ? '/dashboard' : '/user-dashboard';
            window.location.replace(redirectPath);
          } catch (e) {
            console.error('Polling check: Failed to parse user info');
            window.location.replace('/login');
          }
        }
      }, 500); // Check every 500ms
      
      // Set a timeout to prevent infinite hanging
      timeoutIdRef.current = setTimeout(() => {
        if (isMounted && !processedRef.current) {
          console.error('Callback processing timeout after 15 seconds');
          if (redirectCheckIntervalRef.current) {
            clearInterval(redirectCheckIntervalRef.current);
            redirectCheckIntervalRef.current = null;
          }
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
          console.log('🔵 handleCallback result received:', result ? 'result exists' : 'result is null');
          console.log('🔵 Result structure:', result ? Object.keys(result) : 'no result');
          
          if (timeoutIdRef.current) {
            clearTimeout(timeoutIdRef.current);
            timeoutIdRef.current = null;
          }
          if (redirectCheckIntervalRef.current) {
            clearInterval(redirectCheckIntervalRef.current);
            redirectCheckIntervalRef.current = null;
          }
          
          if (processedRef.current) {
            console.log('🔵 Already processed, skipping');
            return;
          }
          
          // Handle null result (code was used but no tokens)
          if (result === null || !result) {
            console.log('🔵 Code was used or no result, checking for existing session');
            const hasToken = localStorage.getItem('access_token');
            const storedUser = localStorage.getItem('user_info');
            if (hasToken && storedUser) {
              console.log('🔵 Found existing session, checking role for redirect');
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
            console.log('🔵 No valid session found, redirecting to login');
            setError('Session expired. Please log in again.');
            setTimeout(() => {
              window.location.replace('/login');
            }, 2000);
            return;
          }
          
          // Result should have both access_token and userInfo
          console.log('🔵 Checking result structure:', {
            hasResult: !!result,
            hasUserInfo: !!result?.userInfo,
            hasAccessToken: !!result?.access_token
          });
          
          if (result && result.userInfo && result.access_token) {
            console.log('✅ Authentication successful, enforcing single session');
            
            // CRITICAL: Enforce session BEFORE marking as processed or redirecting
            // This ensures it runs even if component unmounts
            const apiUrl = process.env.REACT_APP_API_URL || window.location.origin + '/api';
            const token = result.access_token;
            
            // Remove trailing /api if present to avoid double /api/api
            const baseUrl = apiUrl.endsWith('/api') ? apiUrl : apiUrl + '/api';
            const enforceUrl = `${baseUrl}/session/enforce-single`;
            
            console.log('📞 Calling enforce-single endpoint:', enforceUrl);
            
            // Start the session enforcement immediately (fire and forget)
            // Don't await - let it run in background while we redirect
            // Use keepalive: true to ensure request completes even after page navigation
            fetch(enforceUrl, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              },
              keepalive: true  // Allow request to complete even after page navigation
            })
            .then((enforceResponse) => {
              console.log('📞 Enforce-single response status:', enforceResponse.status);
              if (enforceResponse.ok) {
                return enforceResponse.json();
              } else {
                return enforceResponse.text().then(text => {
                  throw new Error(`HTTP ${enforceResponse.status}: ${text}`);
                });
              }
            })
            .then((sessionInfo) => {
              console.log('✅ Session enforcement result:', sessionInfo);
              if (sessionInfo.logged_out_count > 0) {
                console.log(`✅ Enforced single session: logged out ${sessionInfo.logged_out_count} other session(s)`);
              } else {
                console.log('ℹ️ User already has only one active session');
              }
            })
            .catch((enforceError) => {
              console.error('❌ Error enforcing single session:', enforceError);
              // Continue with login even if session enforcement fails
            });
            
            // Mark as processed and redirect
            processedRef.current = true;
            processingRef.current = false;
            
            // Check user role and redirect accordingly
            const userRoles = result.userInfo.realm_access?.roles || [];
            const isAdmin = userRoles.includes('admin');
            const redirectPath = isAdmin ? '/dashboard' : '/user-dashboard';
            console.log(`🔄 User roles: [${userRoles.join(', ')}], redirecting to: ${redirectPath}`);
            
            // Use window.location.replace to prevent back button issues
            // Execute redirect immediately
            window.location.replace(redirectPath);
            return; // Exit early to prevent any further execution
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
          if (timeoutIdRef.current) {
            clearTimeout(timeoutIdRef.current);
            timeoutIdRef.current = null;
          }
          if (redirectCheckIntervalRef.current) {
            clearInterval(redirectCheckIntervalRef.current);
            redirectCheckIntervalRef.current = null;
          }
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
      if (timeoutIdRef.current) {
        clearTimeout(timeoutIdRef.current);
        timeoutIdRef.current = null;
      }
      if (redirectCheckIntervalRef.current) {
        clearInterval(redirectCheckIntervalRef.current);
        redirectCheckIntervalRef.current = null;
      }
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

