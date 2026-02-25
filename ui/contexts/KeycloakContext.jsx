"use client"

import { createContext, useContext, useEffect, useState } from 'react';
import { initKeycloak, login, logout, getKeycloakInstance, getUserInfo, hasRole } from '@/utils/keycloak';

const KeycloakContext = createContext(null);

export const useKeycloak = () => {
  const context = useContext(KeycloakContext);
  if (!context) {
    throw new Error('useKeycloak must be used within KeycloakProvider');
  }
  return context;
};

export const KeycloakProvider = ({ children }) => {
  const [keycloak, setKeycloak] = useState(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [userInfo, setUserInfo] = useState(null);

  useEffect(() => {
    // Feature flag: Check if Keycloak is enabled
    const keycloakEnabled = process.env.NEXT_PUBLIC_ENABLE_KEYCLOAK === '1';

    if (!keycloakEnabled) {
      // Development mode: No authentication
      console.log('[Keycloak] Disabled (NEXT_PUBLIC_ENABLE_KEYCLOAK=0)');
      setLoading(false);
      setAuthenticated(false);
      return;
    }

    // Keycloak enabled: Initialize SSO
    console.log('[Keycloak] Enabled (NEXT_PUBLIC_ENABLE_KEYCLOAK=1)');
    const initialize = async () => {
      try {
        const kc = await initKeycloak(
          // onAuthSuccess
          (kcInstance) => {
            console.log('[Keycloak] Authentication successful');
            setKeycloak(kcInstance);
            setAuthenticated(true);
            setUserInfo(getUserInfo());
            setLoading(false);
          },
          // onAuthError
          (error) => {
            console.error('[Keycloak] Auth error:', error);
            setAuthenticated(false);
            setLoading(false);
          }
        );

        if (kc && !kc.authenticated) {
          console.log('[Keycloak] Not authenticated, ready for login');
          setKeycloak(kc);
          setAuthenticated(false);
          setLoading(false);
        }
      } catch (error) {
        console.error('[Keycloak] Initialization failed:', error);
        setLoading(false);
      }
    };

    initialize();
  }, []);

  const handleLogin = () => {
    console.log('[KeycloakContext] handleLogin called', { 
      keycloak: !!keycloak, 
      authenticated, 
      loading 
    });
    
    if (!keycloak) {
      console.error('[KeycloakContext] Keycloak instance is null, cannot login');
      console.log('[KeycloakContext] Attempting to re-initialize...');
      
      // Try to re-initialize if instance is null
      initKeycloak(
        (kcInstance) => {
          console.log('[Keycloak] Re-initialized successfully');
          setKeycloak(kcInstance);
          setLoading(false);
          // Now try login again
          kcInstance.login().catch(err => {
            console.error('[Keycloak] Login error after re-init:', err);
          });
        },
        (error) => {
          console.error('[Keycloak] Re-init failed:', error);
          setLoading(false);
        }
      );
      return;
    }
    
    login();
  };

  const handleLogout = () => {
    logout();
    setAuthenticated(false);
    setUserInfo(null);
  };

  const value = {
    keycloak,
    authenticated,
    loading,
    userInfo,
    login: handleLogin,
    logout: handleLogout,
    hasRole: (role) => hasRole(role),
    getToken: () => keycloak?.token,
  };

  return (
    <KeycloakContext.Provider value={value}>
      {children}
    </KeycloakContext.Provider>
  );
};
