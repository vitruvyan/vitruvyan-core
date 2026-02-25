# Keycloak Integration Plan - Vitruvyan UI
**Data**: 24 Gennaio 2026  
**Status**: ⚠️ IMPLEMENTATION REQUIRED

---

## 🎯 Obiettivo

Passare da **mock users** (`user_1`, `beta_user_01`) a **utenti reali autenticati via Keycloak SSO**.

---

## ✅ Situazione Attuale

### Backend Status: ✅ READY
- Keycloak container: **UP** (porta 8080)
- Realm: `vitruvyan`
- Admin URL: `https://user.vitruvyan.com`
- Admin credentials: `admin / @Caravaggio971`
- Client ID existing: `vitruvyan-ui` (già configurato)
- PostgreSQL keycloak DB: ✅ CONNECTED

### Frontend Status: ❌ NOT INTEGRATED
- Mock user hardcoded: `user_1` in tutti i componenti
- NO Keycloak SDK installato
- NO login UI
- NO token management
- NO protected routes

---

## 📋 Implementation Roadmap (8 ore)

### MILESTONE 1: Keycloak Client Setup (30 min)

**Task 1.1**: Verifica configurazione Keycloak Admin Console
```bash
# 1. Vai su https://user.vitruvyan.com
# 2. Login: admin / @Caravaggio971
# 3. Vai a Realm "vitruvyan" → Clients → vitruvyan-ui
# 4. Verifica settings:
#    - Access Type: public
#    - Valid Redirect URIs: http://localhost:3001/*, https://www.vitruvyan.com/*
#    - Web Origins: http://localhost:3001, https://www.vitruvyan.com
#    - Direct Access Grants: Enabled
```

**Task 1.2**: Crea users di test (se non esistono)
```bash
# Keycloak Admin Console
# Realm vitruvyan → Users → Add User
# Username: caravaggio
# Email: caravaggio@vitruvyan.com
# Email Verified: ON
# Set Password: @Caravaggio971 (temporary: OFF)
```

---

### MILESTONE 2: Frontend SDK Installation (1 ora)

**Task 2.1**: Install keycloak-js SDK
```bash
cd /home/caravaggio/vitruvyan/vitruvyan-ui
npm install keycloak-js
# or pnpm add keycloak-js
```

**Task 2.2**: Create Keycloak config file
**File**: `vitruvyan-ui/lib/keycloak.js`
```javascript
import Keycloak from 'keycloak-js';

const keycloak = new Keycloak({
  url: 'https://user.vitruvyan.com',
  realm: 'vitruvyan',
  clientId: 'vitruvyan-ui'
});

export default keycloak;
```

**Task 2.3**: Create Auth Context Provider
**File**: `vitruvyan-ui/contexts/AuthContext.jsx`
```javascript
'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import keycloak from '@/lib/keycloak';

const AuthContext = createContext({});

export const AuthProvider = ({ children }) => {
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(null);

  useEffect(() => {
    keycloak.init({
      onLoad: 'check-sso', // Don't force login immediately
      pkceMethod: 'S256',
      checkLoginIframe: false,
      silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html'
    }).then(authenticated => {
      setAuthenticated(authenticated);
      setLoading(false);
      
      if (authenticated) {
        setUser({
          id: keycloak.tokenParsed.sub,
          username: keycloak.tokenParsed.preferred_username,
          email: keycloak.tokenParsed.email,
          name: keycloak.tokenParsed.name || keycloak.tokenParsed.preferred_username
        });
        setToken(keycloak.token);
        
        console.log('[Keycloak] User authenticated:', keycloak.tokenParsed);
      } else {
        console.log('[Keycloak] User not authenticated');
      }
    }).catch(err => {
      console.error('[Keycloak] Init error:', err);
      setLoading(false);
    });

    // Auto refresh token before expiry
    keycloak.onTokenExpired = () => {
      console.log('[Keycloak] Token expired, refreshing...');
      keycloak.updateToken(30).then(refreshed => {
        if (refreshed) {
          setToken(keycloak.token);
          console.log('[Keycloak] Token refreshed');
        }
      }).catch(() => {
        console.error('[Keycloak] Token refresh failed, logging out');
        keycloak.logout();
      });
    };
  }, []);

  const login = () => keycloak.login();
  const logout = () => keycloak.logout();
  const register = () => keycloak.register();

  return (
    <AuthContext.Provider value={{ 
      authenticated, 
      user, 
      loading, 
      token, 
      login, 
      logout, 
      register,
      keycloak 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
```

**Task 2.4**: Wrap App with AuthProvider
**File**: `vitruvyan-ui/app/layout.jsx`
```javascript
import { AuthProvider } from '@/contexts/AuthContext';

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
```

---

### MILESTONE 3: Update API Client (2 ore)

**Task 3.1**: Update apiClient to use Keycloak token
**File**: `vitruvyan-ui/lib/apiClient.js`

**BEFORE** (mock user):
```javascript
const userId = 'user_1'; // Hardcoded mock
```

**AFTER** (Keycloak user):
```javascript
import keycloak from '@/lib/keycloak';

export async function sendMessage(userInput, userId = null) {
  // Use Keycloak user ID if authenticated
  const effectiveUserId = userId || keycloak.tokenParsed?.sub || 'anonymous';
  
  const requestBody = {
    input_text: userInput,
    user_id: effectiveUserId,
    validated_tickers: tickersFromPills || []
  };

  const headers = {
    'Content-Type': 'application/json'
  };

  // Add Authorization header if authenticated
  if (keycloak.authenticated && keycloak.token) {
    headers['Authorization'] = `Bearer ${keycloak.token}`;
  }

  const response = await fetch(`${API_URL}/run`, {
    method: 'POST',
    headers,
    body: JSON.stringify(requestBody)
  });

  return response.json();
}
```

**Task 3.2**: Update all API calls (portfolio, shadow trading, etc.)
```javascript
// Pattern for all API calls
const makeAuthenticatedRequest = async (endpoint, options = {}) => {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };

  if (keycloak.authenticated && keycloak.token) {
    headers['Authorization'] = `Bearer ${keycloak.token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers
  });

  return response.json();
};
```

---

### MILESTONE 4: Shadow Trading Integration (2 ore)

**Problem**: Shadow trading currently uses mock `user_1` → no real cash account

**Solution**: Initialize cash account on first Keycloak login

**Task 4.1**: Create cash account initialization endpoint
**File**: `docker/services/api_shadow_traders/main.py`

Add endpoint:
```python
@app.post("/shadow/initialize_account")
async def initialize_shadow_account(request: InitializeAccountRequest):
    """
    Initialize shadow trading account for new user.
    Creates cash account with initial $50,000 virtual cash.
    """
    user_id = request.user_id
    initial_cash = request.initial_cash or 50000.0
    
    # Check if account already exists
    existing = await shadow_broker.get_cash_account(user_id)
    if existing:
        return {"status": "already_exists", "cash_balance": existing.balance}
    
    # Create new account
    account = await shadow_broker.create_cash_account(
        user_id=user_id,
        initial_balance=initial_cash
    )
    
    return {
        "status": "created",
        "user_id": user_id,
        "cash_balance": account.balance,
        "message": f"Shadow trading account initialized with ${initial_cash:,.2f}"
    }
```

**Task 4.2**: Call initialization on first login
**File**: `vitruvyan-ui/contexts/AuthContext.jsx`

Add in useEffect after authentication:
```javascript
if (authenticated && user) {
  // Initialize shadow trading account
  fetch('http://localhost:8011/shadow/initialize_account', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${keycloak.token}`
    },
    body: JSON.stringify({
      user_id: user.id,
      initial_cash: 50000
    })
  }).then(res => res.json()).then(data => {
    console.log('[Shadow Trading] Account initialized:', data);
  }).catch(err => {
    console.error('[Shadow Trading] Initialization failed:', err);
  });
}
```

---

### MILESTONE 5: UI Update - Login/Logout (1 ora)

**Task 5.1**: Create Login Button
**File**: `vitruvyan-ui/components/auth/LoginButton.jsx`
```javascript
'use client';

import { useAuth } from '@/contexts/AuthContext';

export default function LoginButton() {
  const { login } = useAuth();
  
  return (
    <button 
      onClick={login}
      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
    >
      Login with Vitruvyan SSO
    </button>
  );
}
```

**Task 5.2**: Create User Menu (Profile + Logout)
**File**: `vitruvyan-ui/components/auth/UserMenu.jsx`
```javascript
'use client';

import { useAuth } from '@/contexts/AuthContext';

export default function UserMenu() {
  const { user, logout } = useAuth();
  
  if (!user) return null;
  
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-gray-700">
        👤 {user.name || user.username}
      </span>
      <button 
        onClick={logout}
        className="px-3 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300"
      >
        Logout
      </button>
    </div>
  );
}
```

**Task 5.3**: Update Header/Navigation
**File**: `vitruvyan-ui/components/Header.jsx` (or wherever navigation is)
```javascript
import { useAuth } from '@/contexts/AuthContext';
import LoginButton from '@/components/auth/LoginButton';
import UserMenu from '@/components/auth/UserMenu';

export default function Header() {
  const { authenticated, loading } = useAuth();
  
  if (loading) {
    return <div>Loading...</div>;
  }
  
  return (
    <header>
      <nav>
        {/* ... existing nav ... */}
        <div className="flex items-center gap-4">
          {authenticated ? <UserMenu /> : <LoginButton />}
        </div>
      </nav>
    </header>
  );
}
```

---

### MILESTONE 6: Protected Routes (1 ora)

**Task 6.1**: Create Protected Route Component
**File**: `vitruvyan-ui/components/auth/ProtectedRoute.jsx`
```javascript
'use client';

import { useAuth } from '@/contexts/AuthContext';
import LoginButton from './LoginButton';

export default function ProtectedRoute({ children, fallback = null }) {
  const { authenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading authentication...</p>
        </div>
      </div>
    );
  }
  
  if (!authenticated) {
    return fallback || (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <h2 className="text-2xl font-bold mb-4">Authentication Required</h2>
        <p className="text-gray-600 mb-6">Please login to access this page</p>
        <LoginButton />
      </div>
    );
  }
  
  return children;
}
```

**Task 6.2**: Wrap protected pages
**File**: `vitruvyan-ui/app/portfolio/page.jsx`
```javascript
import ProtectedRoute from '@/components/auth/ProtectedRoute';

export default function PortfolioPage() {
  return (
    <ProtectedRoute>
      {/* ... existing portfolio content ... */}
    </ProtectedRoute>
  );
}
```

Apply to:
- `/portfolio` → Protected ✅
- `/shadow-trading` (when created) → Protected ✅
- `/` (chat) → Optional (allow anonymous with limited features)

---

### MILESTONE 7: Backend Token Validation (1.5 ore)

**Task 7.1**: Install PyJWT + python-keycloak in backend
```bash
# In backend containers
pip install pyjwt python-keycloak requests
```

**Task 7.2**: Create JWT validation middleware
**File**: `core/auth/keycloak_validator.py` (NEW)
```python
import jwt
import requests
from functools import wraps
from fastapi import HTTPException, Request

KEYCLOAK_URL = "https://user.vitruvyan.com"
REALM = "vitruvyan"
CLIENT_ID = "vitruvyan-ui"

# Cache public key (fetch once, reuse)
_public_key_cache = None

def get_keycloak_public_key():
    global _public_key_cache
    if _public_key_cache:
        return _public_key_cache
    
    url = f"{KEYCLOAK_URL}/realms/{REALM}"
    resp = requests.get(url)
    resp.raise_for_status()
    realm_data = resp.json()
    public_key = f"-----BEGIN PUBLIC KEY-----\n{realm_data['public_key']}\n-----END PUBLIC KEY-----"
    _public_key_cache = public_key
    return public_key

def validate_token(token: str) -> dict:
    """
    Validate JWT token from Keycloak.
    Returns decoded token payload if valid.
    Raises HTTPException if invalid.
    """
    try:
        public_key = get_keycloak_public_key()
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=CLIENT_ID,
            options={"verify_aud": False}  # Keycloak doesn't always include aud
        )
        return decoded
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

def require_auth(func):
    """
    Decorator for FastAPI endpoints requiring authentication.
    Extracts user_id from JWT token.
    """
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
        
        token = auth_header.split(' ')[1]
        user_data = validate_token(token)
        
        # Inject user_id into request state
        request.state.user_id = user_data['sub']
        request.state.user_email = user_data.get('email')
        request.state.user_name = user_data.get('preferred_username')
        
        return await func(request, *args, **kwargs)
    
    return wrapper
```

**Task 7.3**: Apply to LangGraph API
**File**: `docker/services/api_graph/main.py`
```python
from core.auth.keycloak_validator import require_auth

@app.post("/run")
@require_auth  # Add this decorator
async def run_graph(request: Request, payload: dict):
    user_id = request.state.user_id  # Use real user ID from JWT
    input_text = payload.get("input_text", "")
    
    # ... rest of existing logic ...
```

**Task 7.4**: Apply to Shadow Trading API
**File**: `docker/services/api_shadow_traders/main.py`
```python
from core.auth.keycloak_validator import require_auth

@app.post("/shadow/buy")
@require_auth
async def shadow_buy(request: Request, payload: ShadowTradeRequest):
    user_id = request.state.user_id  # Real user ID from JWT
    # ... existing logic ...

@app.get("/portfolio/{user_id}")
@require_auth
async def get_portfolio(request: Request, user_id: str):
    # Verify user can only access their own portfolio
    if request.state.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    # ... existing logic ...
```

---

## 🧪 Testing Plan (30 min)

### Test 1: Login Flow
```bash
# 1. Vai su http://localhost:3001
# 2. Clicca "Login with Vitruvyan SSO"
# 3. Login con caravaggio / @Caravaggio971
# 4. Verifica redirect a dashboard
# 5. Verifica user menu mostra nome utente
```

### Test 2: Shadow Trading with Real User
```bash
# 1. Login on frontend
# 2. Open browser console
# 3. Send query: "compra 100 AAPL"
# 4. Verify logs show real user_id (NOT user_1)
# 5. Verify shadow trading API creates cash account
# 6. Verify order executed successfully
```

### Test 3: Token Refresh
```bash
# 1. Login
# 2. Wait 5+ minutes (token expiry)
# 3. Make API call
# 4. Verify token auto-refreshes (no logout)
```

### Test 4: Protected Routes
```bash
# 1. Logout
# 2. Navigate to /portfolio
# 3. Verify redirect to login
# 4. Login
# 5. Verify redirect back to /portfolio
```

---

## 🔑 Environment Variables (Required)

**File**: `vitruvyan-ui/.env.local`
```bash
NEXT_PUBLIC_KEYCLOAK_URL=https://user.vitruvyan.com
NEXT_PUBLIC_KEYCLOAK_REALM=vitruvyan
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=vitruvyan-ui
```

**File**: `docker/.env` (backend)
```bash
KEYCLOAK_URL=https://user.vitruvyan.com
KEYCLOAK_REALM=vitruvyan
KEYCLOAK_CLIENT_ID=vitruvyan-ui
```

---

## 📊 Migration Strategy

### Phase 1: Soft Launch (1 week)
- Deploy Keycloak integration
- Keep mock users functional (fallback)
- New users get real accounts
- Old sessions continue with mock

### Phase 2: Full Migration (Week 2)
- Force re-authentication for all users
- Migrate existing shadow portfolios to real users
- Deprecate mock user logic

### Phase 3: Cleanup (Week 3)
- Remove all mock user references
- Clean up test data
- Full production mode

---

## 🚨 Rollback Plan

If Keycloak integration fails:
```bash
# 1. Revert frontend to mock user
git revert <keycloak-commit>

# 2. Restart frontend
cd vitruvyan-ui && npm run build && pm2 restart vitruvyan-ui

# 3. Backend continues working (no changes needed if @require_auth not deployed)
```

---

## ✅ Success Criteria

- [ ] Users can login with Keycloak
- [ ] JWT tokens validated on backend
- [ ] Real user_id used in all API calls
- [ ] Shadow trading accounts created automatically
- [ ] Protected routes work (portfolio, shadow-trading)
- [ ] Token auto-refresh works
- [ ] Logout clears session
- [ ] No more hardcoded `user_1` in codebase

---

## 🎯 Post-Integration Enhancements

### 1. User Profile Page
- Display Keycloak user info
- Shadow portfolio value
- Trading history
- Settings

### 2. Role-Based Access Control (RBAC)
- Admin users: Access to Grafana, Prometheus
- Premium users: Advanced features
- Free users: Basic analysis only

### 3. Multi-Realm Support
- Separate realms for dev/staging/prod
- Different user bases per environment

---

**Estimated Total Time**: 8 hours  
**Priority**: P0 (Blocking shadow trading MVP)  
**Owner**: Caravaggio  
**Status**: Ready to implement
