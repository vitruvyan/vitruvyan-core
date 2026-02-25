// Keycloak configuration utility for Vitruvyan multi-domain auth
// utils/keycloak.js

let keycloakInstance = null;
let tokenRefreshTimer = null;

// Determine if we're in production based on hostname
const isProduction = () => {
  if (typeof window === 'undefined') return false;
  return window.location.hostname.includes('vitruvyan.com');
};

export const getKeycloakConfig = () => {
  // Always use env vars if available (production or dev on VPS)
  const baseUrl = process.env.NEXT_PUBLIC_KEYCLOAK_URL || process.env.VITE_KEYCLOAK_URL || 'http://localhost:8080';
  
  return {
    url: baseUrl,
    realm: process.env.NEXT_PUBLIC_KEYCLOAK_REALM || process.env.VITE_KEYCLOAK_REALM || 'vitruvyan',
    clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID || process.env.VITE_KEYCLOAK_CLIENT_ID || 'vitruvyan-ui'
  };
};

// Auto-refresh token before expiration
const setupTokenRefresh = () => {
  if (!keycloakInstance) return;
  
  // Clear existing timer
  if (tokenRefreshTimer) {
    clearInterval(tokenRefreshTimer);
  }
  
  // Refresh token 30 seconds before expiration
  const refreshInterval = (keycloakInstance.tokenParsed?.exp || 300) - 30;
  
  tokenRefreshTimer = setInterval(async () => {
    try {
      const refreshed = await keycloakInstance.updateToken(30);
      if (refreshed) {
        console.log('Token refreshed successfully');
        updateStoredUserInfo();
        
        // ✅ Update cookie with fresh token (Feb 4, 2026)
        document.cookie = `keycloak_token=${keycloakInstance.token}; path=/; max-age=3600; SameSite=Lax`;
      }
    } catch (error) {
      console.error('Failed to refresh token:', error);
      // Token refresh failed, user needs to re-authenticate
      logout();
    }
  }, refreshInterval * 1000);
};

// Update stored user info with fresh token
const updateStoredUserInfo = async () => {
  if (!keycloakInstance?.authenticated) return;
  
  try {
    const userInfo = await keycloakInstance.loadUserProfile();
    const userData = {
      id: userInfo.id,
      sub: keycloakInstance.tokenParsed?.sub, // ✅ FIX (Feb 14, 2026): UUID for portfolio lookup
      username: userInfo.username,
      email: userInfo.email,
      name: `${userInfo.firstName || ''} ${userInfo.lastName || ''}`.trim(),
      preferred_username: keycloakInstance.tokenParsed?.preferred_username, // For display
      token: keycloakInstance.token,
      refreshToken: keycloakInstance.refreshToken,
      roles: keycloakInstance.tokenParsed?.realm_access?.roles || [],
      isPremium: keycloakInstance.tokenParsed?.realm_access?.roles?.includes('premium') || false
    };
    localStorage.setItem('keycloak_user', JSON.stringify(userData));
    
    // ✅ CRITICAL (Feb 4, 2026): Save token to cookie for API routes
    // Next.js API routes can read cookies server-side for auth
    document.cookie = `keycloak_token=${keycloakInstance.token}; path=/; max-age=3600; SameSite=Lax`;
    console.log('[Keycloak] Token saved to cookie');
  } catch (error) {
    console.error('Failed to update user info:', error);
  }
};

export const initKeycloak = async (onAuthSuccess, onAuthError) => {
  if (typeof window === 'undefined') return null; // SSR protection
  
  try {
    // Dynamic import for client-side only
    const Keycloak = (await import('keycloak-js')).default;
    
    if (!keycloakInstance) {
      const config = getKeycloakConfig();
      console.log('Initializing Keycloak with config:', { ...config, url: config.url });
      
      keycloakInstance = new Keycloak(config);
      
      const authenticated = await keycloakInstance.init({
        onLoad: 'check-sso',
        checkLoginIframe: false, // Disable iframe checks (avoid timeout issues)
        pkceMethod: 'S256', // Use PKCE for public clients
        enableLogging: !isProduction(),
      });
      
      if (authenticated) {
        console.log('User authenticated successfully');
        await updateStoredUserInfo();
        setupTokenRefresh();
        
        if (onAuthSuccess) {
          onAuthSuccess(keycloakInstance);
        }
      } else {
        console.log('User not authenticated');
      }
      
      // Setup event listeners
      keycloakInstance.onTokenExpired = () => {
        console.log('Token expired, refreshing...');
        keycloakInstance.updateToken(30).catch(() => {
          console.error('Failed to refresh expired token');
          logout();
        });
      };
      
      keycloakInstance.onAuthRefreshError = () => {
        console.error('Auth refresh error');
        if (onAuthError) {
          onAuthError();
        }
      };
    }
    
    return keycloakInstance;
  } catch (error) {
    console.error('Keycloak initialization error:', error);
    if (onAuthError) {
      onAuthError(error);
    }
    return null;
  }
};

export const getKeycloakInstance = () => keycloakInstance;

export const login = () => {
  if (keycloakInstance) {
    console.log('[Keycloak] Attempting login...');
    const redirectUri = window.location.origin + window.location.pathname;
    keycloakInstance.login({
      redirectUri: redirectUri
    }).catch(error => {
      console.error('[Keycloak] Login error:', error);
    });
  } else {
    console.error('[Keycloak] Instance not initialized, cannot login');
  }
};

export const register = () => {
  if (keycloakInstance) {
    console.log('[Keycloak] Attempting registration...');
    const redirectUri = window.location.origin + window.location.pathname;
    keycloakInstance.register({
      redirectUri: redirectUri
    }).catch(error => {
      console.error('[Keycloak] Registration error:', error);
    });
  } else {
    console.error('[Keycloak] Instance not initialized, cannot register');
  }
};

export const logout = async () => {
  if (keycloakInstance) {
    // Clear token refresh timer
    if (tokenRefreshTimer) {
      clearInterval(tokenRefreshTimer);
      tokenRefreshTimer = null;
    }
    
    // Clear local storage
    localStorage.removeItem('keycloak_user');
    
    // ✅ Clear token cookie (Feb 4, 2026)
    document.cookie = 'keycloak_token=; path=/; max-age=0';
    
    // Use current full URL as redirect (includes port)
    const redirectUri = window.location.origin + window.location.pathname;
    
    console.log('[Keycloak] Logging out, redirect to:', redirectUri);
    
    try {
      await keycloakInstance.logout({ redirectUri });
    } catch (error) {
      console.error('[Keycloak] Logout error:', error);
      // Force logout by redirecting manually
      window.location.href = redirectUri;
    }
  }
};

export const getToken = () => {
  return keycloakInstance?.token || null;
};

export const isAuthenticated = () => {
  return keycloakInstance?.authenticated || false;
};

export const getUserInfo = () => {
  const stored = localStorage.getItem('keycloak_user');
  return stored ? JSON.parse(stored) : null;
};

export const hasRole = (role) => {
  const userInfo = getUserInfo();
  return userInfo?.roles?.includes(role) || false;
};

export const isPremiumUser = () => {
  return hasRole('premium');
};

export const isAdmin = () => {
  return hasRole('admin');
};

// Get fresh token (will refresh if needed)
export const getFreshToken = async () => {
  if (!keycloakInstance) return null;
  
  try {
    await keycloakInstance.updateToken(30);
    return keycloakInstance.token;
  } catch (error) {
    console.error('Failed to get fresh token:', error);
    return null;
  }
};

// Account management
export const manageAccount = () => {
  if (keycloakInstance) {
    keycloakInstance.accountManagement();
  }
};
