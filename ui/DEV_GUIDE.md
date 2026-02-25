# 🚀 Guida Rapida Sviluppo Locale

## ⚡ Quick Start (Metodo Rapido)

```bash
./dev-local.sh
```

Oppure:
```bash
npm run dev
```

Apri: **http://localhost:3000**

---

## 📋 Workflow di Sviluppo

### 1️⃣ Modifica in Locale (Hot Reload Istantaneo)
```bash
# Terminal 1: Server di sviluppo (lascia attivo)
./dev-local.sh

# Terminal 2: Modifica codice
nano components/header.jsx    # Le modifiche si vedono subito nel browser!
```

**✨ Hot Reload**: Next.js aggiorna il browser automaticamente ad ogni salvataggio.

### 2️⃣ Testa le Modifiche
- **Frontend**: http://localhost:3000
- **Backend**: https://graph.vitruvyan.com (già configurato)
- **Keycloak**: https://user.vitruvyan.com (SSO attivo)

### 3️⃣ Pubblica in Produzione (quando sei soddisfatto)
```bash
# Ctrl+C per fermare il server locale

# Commit & Push
git add .
git commit -m "feat: Descrizione modifiche"
git push origin main

# Deploy automatico su Vercel (oppure manuale)
vercel --prod --yes
```

---

## 🎨 Vantaggi Sviluppo Locale

✅ **Hot Reload**: Modifiche istantanee senza rebuild  
✅ **Zero costi**: Sviluppo gratuito, paghi solo il deploy  
✅ **Debug completo**: Console, DevTools, Stack trace  
✅ **Test veloce**: Prova 100 volte in 10 minuti  
✅ **Rollback sicuro**: In locale non rompi produzione  

---

## 🔧 Comandi Utili

```bash
# Sviluppo locale (porta 3000)
npm run dev

# Build di produzione locale (testa prima del deploy)
npm run build
npm run start  # Serve la build su porta 3000

# Linting (trova errori nel codice)
npm run lint

# Deploy manuale su Vercel
vercel --prod --yes

# Deploy automatico (push su main)
git push origin main  # Vercel rileva e deploya automaticamente
```

---

## 🌐 URLs

| Ambiente | URL | Uso |
|----------|-----|-----|
| **Locale** | http://localhost:3000 | Sviluppo e test |
| **Produzione** | https://mercator.vitruvyan.com | Utenti finali |
| **Backend** | https://graph.vitruvyan.com | API (condiviso) |
| **Keycloak** | https://user.vitruvyan.com | SSO (condiviso) |

---

## 🐛 Troubleshooting

**Porta 3000 occupata?**
```bash
PORT=3001 npm run dev
```

**Cache corrotta?**
```bash
rm -rf .next
npm run dev
```

**Dipendenze mancanti?**
```bash
npm install
```

**Backend non risponde?**
```bash
# Verifica che graph.vitruvyan.com sia up
curl https://graph.vitruvyan.com/health
```

---

## 💡 Best Practice

1. **Sviluppa SEMPRE in locale prima** → Testa → Poi deploya
2. **Usa feature branch** per modifiche grandi: `git checkout -b feature/nuovo-logo`
3. **Commit frequenti** con messaggi chiari: `feat:`, `fix:`, `refactor:`
4. **Testa con Keycloak disabilitato** (`.env.local`: `NEXT_PUBLIC_ENABLE_KEYCLOAK=0`) per sviluppo veloce

---

**Made with ❤️ by Vitruvyan Team**
