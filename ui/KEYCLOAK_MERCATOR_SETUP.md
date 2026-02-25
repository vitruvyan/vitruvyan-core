# Keycloak SSO Implementation - Mercator

## ✅ Completato

### Files modificati/creati:

1. **`contexts/KeycloakContext.jsx`** - Context React per gestire stato auth
2. **`utils/keycloak.js`** - Aggiornato con URL corretto (user.vitruvyan.com)
3. **`app/clientLayout.jsx`** - Wrapper KeycloakProvider aggiunto
4. **`components/header.jsx`** - Login/Logout con Keycloak
5. **`.env.local`** - Variabili ambiente Keycloak
6. **`public/silent-check-sso.html`** - Già esistente per SSO silenzioso

### Configurazione Keycloak

\`\`\`env
NEXT_PUBLIC_KEYCLOAK_URL=https://user.vitruvyan.com
NEXT_PUBLIC_KEYCLOAK_REALM=vitruvyan
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=vitruvyan-ui
\`\`\`

### Client Keycloak

- **Client ID**: `vitruvyan-ui`
- **Type**: Public (PKCE enabled)
- **Valid Redirect URIs**: `https://mercator.vitruvyan.com/*`
- **Web Origins**: `https://mercator.vitruvyan.com`

## 🚀 Testing

### 1. Development locale:

\`\`\`bash
cd /home/caravaggio/vitruvyan/vitruvyan-ui
pnpm dev
# Oppure
npm run dev
\`\`\`

Vai su http://localhost:5173 (o 3000) e clicca "Login"

### 2. Production (mercator.vitruvyan.com):

\`\`\`bash
# Build
pnpm build

# Start
pnpm start
\`\`\`

Vai su https://mercator.vitruvyan.com e clicca "Login"

## 📦 Utilizzo nell'applicazione

### Accedere allo stato auth:

\`\`\`jsx
import { useKeycloak } from '@/contexts/KeycloakContext';

function MyComponent() {
  const { authenticated, loading, userInfo, login, logout, getToken } = useKeycloak();
  
  if (loading) {
    return <div>Loading...</div>;
  }
  
  if (!authenticated) {
    return <button onClick={login}>Login</button>;
  }
  
  return (
    <div>
      <p>Welcome {userInfo.name}!</p>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
\`\`\`

### Chiamare API protette:

\`\`\`jsx
const { getToken } = useKeycloak();

const fetchData = async () => {
  const token = await getToken();
  
  const response = await fetch('https://api.vitruvyan.com/data', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return response.json();
};
\`\`\`

### Proteggere route:

\`\`\`jsx
'use client';
import { useKeycloak } from '@/contexts/KeycloakContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function ProtectedPage() {
  const { authenticated, loading, login } = useKeycloak();
  const router = useRouter();
  
  useEffect(() => {
    if (!loading && !authenticated) {
      login();
    }
  }, [authenticated, loading]);
  
  if (loading) {
    return <div>Loading...</div>;
  }
  
  if (!authenticated) {
    return null;
  }
  
  return <div>Protected Content</div>;
}
\`\`\`

### Verificare ruoli:

\`\`\`jsx
const { hasRole } = useKeycloak();

if (hasRole('premium')) {
  // Show premium features
}

if (hasRole('admin')) {
  // Show admin panel
}
\`\`\`

## 🔍 Debug

### Console logs:

Keycloak logga automaticamente:
- Initialization
- Authentication success/failure
- Token refresh
- Logout

### Verificare token:

\`\`\`javascript
// In browser console
const kc = JSON.parse(localStorage.getItem('keycloak_user'));
console.log('Token:', kc.token);
console.log('User:', kc);
\`\`\`

### Test SSO cross-domain:

1. Login su https://mercator.vitruvyan.com
2. Apri https://dash.vitruvyan.com (Grafana)
3. Dovresti essere già autenticato (SSO)

## 🐛 Troubleshooting

### "Invalid redirect_uri"

Verifica che `https://mercator.vitruvyan.com/*` sia nei Valid Redirect URIs del client in Keycloak Admin.

### CORS errors

Verifica Web Origins in Keycloak:
\`\`\`
Clients > vitruvyan-ui > Settings > Web Origins
+ https://mercator.vitruvyan.com
\`\`\`

### Token non refreshed

Il token si auto-refresh 30 secondi prima della scadenza. Verifica:
\`\`\`
Realm Settings > Tokens > Access Token Lifespan
Default: 15 minuti
\`\`\`

### Cookie non condiviso

Verifica che il cookie domain sia `.vitruvyan.com`:
\`\`\`
Realm Settings > Sessions > Cookie SameSite: Lax
\`\`\`

## 📋 Next Steps

- [ ] Test login/logout su mercator
- [ ] Test SSO da mercator a dash (Grafana)
- [ ] Implementare route protette
- [ ] Aggiungere role-based access
- [ ] Integrare API calls con token
- [ ] Deploy su production

## 🔗 Links

- **Keycloak Admin**: https://user.vitruvyan.com/admin
- **Realm**: vitruvyan
- **Mercator**: https://mercator.vitruvyan.com
- **Docs**: /home/caravaggio/vitruvyan/KEYCLOAK_SSO_SETUP.md
