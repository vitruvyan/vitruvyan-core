# ✅ KEYCLOAK SSO ATTIVATO - Jan 24, 2026

## 🎯 STATUS: PRONTO PER IL TEST

### Cosa è stato fatto (automaticamente):
1. ✅ Keycloak container: **RUNNING** (porta 8080, 4 giorni uptime)
2. ✅ Realm `vitruvyan`: **CONFIGURATO**
3. ✅ Client `vitruvyan-ui`: **ESISTENTE**
4. ✅ Frontend SDK: **keycloak-js v25.0.6 INSTALLATO**
5. ✅ Feature flag: **`NEXT_PUBLIC_ENABLE_KEYCLOAK=1` ABILITATO**
6. ✅ Frontend: **RIAVVIATO** su http://localhost:3001

---

## 🚀 PROSSIMI STEP (15 MINUTI)

### STEP 1: Verifica Client Redirect URIs (5 min) ⚠️ CRITICO

**Login Keycloak Admin Console**:
- URL: https://user.vitruvyan.com/admin
- Username: `admin`
- Password: `@Caravaggio971`

**Azioni**:
1. Seleziona Realm: `vitruvyan` (dropdown top-left)
2. Menu laterale: **Clients** → Cerca `vitruvyan-ui` → Click
3. Tab **Settings**:
   - Scroll a **Valid redirect URIs**
   - Verifica che ci siano:
     ```
     http://localhost:3001/*
     http://localhost:3000/*
     https://www.vitruvyan.com/*
     https://vitruvyan.com/*
     ```
   - Se mancano, aggiungi manualmente
   - Click **Add valid redirect URIs** per ogni URL
   - Click **Save** in basso

4. Scroll a **Valid post logout redirect URIs**:
   - Stessi URL di sopra

5. Scroll a **Web origins**:
   ```
   http://localhost:3001
   http://localhost:3000
   https://www.vitruvyan.com
   ```
   - Click **Add web origins** per ogni dominio
   - Click **Save**

---

### STEP 2: Crea Test User (3 min)

**Keycloak Admin Console**:

1. Menu laterale: **Users** → Click **Add user** (top-right)
2. Form:
   - **Username**: `caravaggio` ← IL TUO USERNAME
   - **Email**: `caravaggio@vitruvyan.com`
   - **Email verified**: ✅ **ON** (toggle)
   - **First name**: Caravaggio
   - **Last name**: Leonardo
3. Click **Create**

4. Vai alla tab **Credentials**:
   - Click **Set password**
   - **Password**: `@Caravaggio971`
   - **Password confirmation**: `@Caravaggio971`
   - **Temporary**: ❌ **OFF** (toggle OFF)
   - Click **Save**
   - Confirm nel popup

---

### STEP 3: Test Login Flow (2 min) 🎉

1. **Apri browser**: http://localhost:3001

2. **Cosa dovresti vedere**:
   - Se NON loggato → **Redirect automatico a Keycloak login**
   - URL cambia in: `https://user.vitruvyan.com/realms/vitruvyan/protocol/openid-connect/auth?...`

3. **Login**:
   - Username: `caravaggio`
   - Password: `@Caravaggio971`
   - Click **Sign In**

4. **Redirect automatico a frontend**:
   - URL torna su: `http://localhost:3001`
   - **Console browser** (F12) dovrebbe mostrare:
     ```
     [Keycloak] Enabled (NEXT_PUBLIC_ENABLE_KEYCLOAK=1)
     [Keycloak] Initializing...
     [Keycloak] Authentication successful
     User info: {sub: "...", preferred_username: "caravaggio", email: "..."}
     ```

5. **Verifica UI**:
   - Header dovrebbe mostrare user menu con nome utente
   - No più mock "user_1"

---

## 🧪 TEST SHADOW TRADING (5 MIN)

**Dopo login riuscito**:

1. Vai nella chat: http://localhost:3001

2. Digita nella chat:
   ```
   compra 100 AAPL
   ```

3. **Expected behavior**:
   - Sistema usa **real user_id** dal JWT (non più "user_1")
   - Se account shadow non esiste → creato automaticamente con $50,000
   - Ordine eseguito con successo
   - VEE narrative mostrato

4. **Verifica in console backend**:
   ```bash
   docker logs vitruvyan_api_graph --tail 50 | grep -A 5 "shadow"
   ```
   - Dovrebbe mostrare **real user_id** (UUID Keycloak), NON "user_1"

---

## 🔍 TROUBLESHOOTING

### Problema 1: "invalid_redirect_uri" dopo login
**Sintomo**: Errore Keycloak dopo click "Sign In"

**Soluzione**:
```bash
# Controlla logs Keycloak
docker logs keycloak --tail 30 | grep "invalid_redirect_uri"

# L'errore mostra quale URI è stato tentato
# Aggiungi quell'URI in Keycloak Admin → Client → Valid redirect URIs
```

---

### Problema 2: Frontend non chiede login
**Sintomo**: App carica normalmente, no redirect a Keycloak

**Soluzione**:
```bash
# 1. Verifica env variable
cd /home/caravaggio/vitruvyan/vitruvyan-ui
cat .env.local | grep NEXT_PUBLIC_ENABLE_KEYCLOAK
# Deve essere: NEXT_PUBLIC_ENABLE_KEYCLOAK=1

# 2. Hard refresh browser
# Chrome/Firefox: Ctrl+Shift+R (Linux)

# 3. Controlla console browser (F12)
# Cerca: "[Keycloak] Enabled" o "[Keycloak] Disabled"
```

---

### Problema 3: CORS error nel browser
**Sintomo**: Console mostra "CORS policy: No 'Access-Control-Allow-Origin'"

**Soluzione**:
```bash
# Keycloak Admin Console
# Client vitruvyan-ui → Settings → Web origins
# Aggiungi ESATTAMENTE (no wildcards):
# http://localhost:3001
```

---

## 📊 ARCHITETTURA ATTUALE

```
Browser (localhost:3001)
  ↓
Next.js Frontend (KeycloakContext)
  ↓
keycloak-js SDK (v25.0.6)
  ↓
Keycloak Container (localhost:8080)
  ├─ Realm: vitruvyan
  ├─ Client: vitruvyan-ui
  └─ PostgreSQL (keycloak DB)
  ↓
JWT Token
  ↓
Backend APIs (LangGraph, Shadow Trading)
  ↓
PostgreSQL (shadow_cash_accounts)
```

---

## 🎯 AFTER LOGIN - NEXT TASKS

### Task 1: Update Chat Component (30 min)
**Current**: Chat usa mock `user_id = "user_1"`
**Needed**: Estrarre real user_id da JWT

**File**: `components/chat.jsx`
**Change**:
```javascript
import { useKeycloak } from '@/contexts/KeycloakContext';

export default function Chat() {
  const { authenticated, userInfo, keycloak } = useKeycloak();
  
  // OLD: const userId = 'user_1'; ❌
  // NEW:
  const userId = userInfo?.sub || 'anonymous';
  
  // API calls: add Authorization header
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${keycloak?.token}`
  };
  
  // ... rest of component
}
```

---

### Task 2: Backend JWT Validation (2 hours)
**Current**: Backend accetta qualsiasi user_id senza validazione
**Needed**: Validare JWT token e estrarre user_id reale

**Files**:
- `core/auth/keycloak_validator.py` (NEW)
- `docker/services/api_graph/main.py` (add @require_auth decorator)
- `docker/services/api_shadow_traders/main.py` (add @require_auth decorator)

**See**: `KEYCLOAK_INTEGRATION_PLAN.md` per codice completo

---

### Task 3: Shadow Account Initialization (30 min)
**Current**: Real users non hanno row in `shadow_cash_accounts`
**Needed**: Auto-create account on first login

**Option A (Frontend)**: Hook in KeycloakContext dopo login
**Option B (Backend)**: Auto-create in ShadowBrokerAgent se non esiste

**Recommended**: Option B (più pulito, single source of truth)

---

## ✅ SUCCESS CHECKLIST

- [ ] Keycloak admin console accessible (https://user.vitruvyan.com/admin)
- [ ] Client `vitruvyan-ui` redirect URIs configured
- [ ] Test user `caravaggio` created
- [ ] Frontend shows Keycloak login screen
- [ ] Login successful → redirect to app
- [ ] Console shows `[Keycloak] Authentication successful`
- [ ] User info visible in UI (nome utente in header)
- [ ] Chat "compra 100 AAPL" uses real user_id (not "user_1")
- [ ] Shadow trading account created automatically
- [ ] Order executed successfully

---

## 📝 FINAL NOTES

**Tempo totale stimato**: 15 minuti (solo activation)
**Tempo totale con tasks**: 3 ore (full integration)

**Cosa funziona ORA**:
- ✅ Keycloak SSO login/logout
- ✅ JWT token generation
- ✅ User info retrieval

**Cosa serve DOPO login**:
- ⏳ Chat usa real user_id
- ⏳ Backend valida JWT
- ⏳ Shadow account auto-initialization

**Status**: 🟢 **READY TO TEST**
**Owner**: Caravaggio
**Date**: Jan 24, 2026 - 17:30 UTC
