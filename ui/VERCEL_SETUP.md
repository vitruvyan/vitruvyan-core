# Vitruvyan UI - Vercel Deployment Setup
**Date**: October 29, 2025  
**Status**: Ready for Testing

---

## 📋 Deployment Configuration

### Environment Variables (Vercel)

Configure these in **Vercel Dashboard → Settings → Environment Variables**:

\`\`\`bash
# Backend API Configuration
NEXT_PUBLIC_API_URL=http://161.97.140.157:8004
VITE_API_URL=http://161.97.140.157:8004

# Keycloak Authentication (if enabled)
NEXT_PUBLIC_KEYCLOAK_URL=http://161.97.140.157:8080
NEXT_PUBLIC_KEYCLOAK_REALM=vitruvyan
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=vitruvyan-ui

# Database (legacy, not used in frontend)
# DATABASE_URL=postgresql://vitruvyan_user:%40Caravaggio971@161.97.140.157:5432/vitruvyan?schema=auth
\`\`\`

### Build Settings

- **Framework Preset**: Next.js
- **Build Command**: `npm run build` or `pnpm build`
- **Output Directory**: `.next`
- **Install Command**: `npm install` or `pnpm install`
- **Node Version**: 18.x or 20.x

---

## 🔧 Backend CORS Configuration

**Status**: ✅ ENABLED (Oct 29, 2025)

The backend API (`vitruvyan_api_graph:8004`) has been configured to accept requests from Vercel:

\`\`\`python
# docker/services/api_graph/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",           # Local development
        "https://*.vercel.app",             # All Vercel deployments
        "https://vitruvyan-ui.vercel.app",  # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
\`\`\`

---

## 🧪 Testing Checklist

### 1. Health Check Endpoint
\`\`\`bash
curl http://161.97.140.157:8004/health
\`\`\`
**Expected Response**:
\`\`\`json
{
  "status": "healthy",
  "service": "graph_orchestrator",
  "version": "1.0.5"
}
\`\`\`

### 2. Test Query from Browser Console
Open Vercel deployment → Browser DevTools → Console:
\`\`\`javascript
// Test basic API connection
fetch('http://161.97.140.157:8004/health')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error)

// Test actual query
fetch('http://161.97.140.157:8004/run', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    input_text: "analizza AAPL breve termine",
    user_id: "test_vercel"
  })
})
  .then(r => r.json())
  .then(console.log)
  .catch(console.error)
\`\`\`

### 3. Verify CORS Headers
Check Network tab for OPTIONS preflight request:
\`\`\`
Access-Control-Allow-Origin: https://your-app.vercel.app
Access-Control-Allow-Methods: *
Access-Control-Allow-Headers: *
Access-Control-Allow-Credentials: true
\`\`\`

---

## 🎯 UI Components Integration

### New Components Added (Oct 2025)

1. **VEE Report** (`components/vee-report.jsx`)
   - Multi-layer explainability visualization
   - Collapsible sections for Simple/Technical/Detailed layers
   - Markdown rendering for formatted text

2. **Agent Sidebar** (`components/agent-sidebar.jsx`)
   - Sacred Orders agent visualization
   - Real-time status indicators

3. **Agents Grid** (`components/agents-grid.jsx`)
   - Agent ecosystem overview
   - Interactive agent cards

4. **Dev Nav** (`components/dev-nav.jsx`)
   - Development navigation bar
   - Quick access to API endpoints

5. **Paywall Modal** (`components/paywall-modal.jsx`)
   - Demo limitations handling
   - Upgrade prompts

### API Integration Points

**Chat Component** (`components/chat.jsx`):
\`\`\`javascript
// POST /run endpoint
const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/run`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    input_text: userMessage,
    user_id: userId || 'demo'
  })
})

// Expected response structure
{
  "response": {
    "text": "...",
    "numerical_panel": {
      "tickers": ["AAPL", "TSLA"],
      "momentum_z": [1.23, 0.85],
      "trend_z": [0.92, 1.15],
      // ... other z-scores
    },
    "explainability": {
      "simple": "Executive summary...",
      "technical": "Technical details...",
      "detailed": "Deep analysis..."
    },
    "proactive_suggestions": [...]  // If UX features active
  },
  "intent": "ranking",
  "route": "ne_valid"
}
\`\`\`

---

## 🚨 Known Issues & Limitations

### 1. HTTP (Not HTTPS)
**Issue**: Backend API uses HTTP (not HTTPS)  
**Impact**: Modern browsers may block mixed content (HTTPS → HTTP)  
**Workaround**: 
- Deploy Vercel UI with HTTP backend URL (works in Chrome/Firefox with warnings)
- Future: Add nginx reverse proxy with SSL certificate

### 2. CORS Wildcard for Vercel
**Issue**: `https://*.vercel.app` may not work for all subdomains  
**Current**: Explicitly added `vitruvyan-ui.vercel.app`  
**Solution**: If deployment uses different subdomain, add to CORS origins and rebuild API

### 3. Demo Limiter
**Issue**: `utils/demoLimiter.js` limits free queries  
**Status**: Active in UI (5 queries per session)  
**Bypass**: Premium users need authentication system (Keycloak not yet integrated)

---

## 🔄 Deployment Workflow

### Deploy to Vercel

1. **Initial Setup** (first time):
   \`\`\`bash
   cd vitruvyan-ui
   vercel login
   vercel link  # Link to existing Vercel project
   \`\`\`

2. **Deploy**:
   \`\`\`bash
   # Production deployment
   vercel --prod
   
   # Preview deployment (for testing)
   vercel
   \`\`\`

3. **Verify Deployment**:
   - Check Vercel dashboard for build logs
   - Test health endpoint from browser
   - Send test query via UI chat

### Update Environment Variables

\`\`\`bash
# Via Vercel CLI
vercel env add NEXT_PUBLIC_API_URL production
# Enter value: http://161.97.140.157:8004

# Or via Vercel Dashboard:
# Settings → Environment Variables → Add New
\`\`\`

### Rollback (if needed)

\`\`\`bash
# List deployments
vercel ls

# Promote previous deployment to production
vercel promote [deployment-url]
\`\`\`

---

## 📊 Monitoring & Debugging

### Backend Logs
\`\`\`bash
# On VPS
docker logs vitruvyan_api_graph --tail 100 -f

# Filter for Vercel requests
docker logs vitruvyan_api_graph | grep "vercel.app"
\`\`\`

### Vercel Logs
\`\`\`bash
# Via CLI
vercel logs [deployment-url]

# Via Dashboard
# Deployments → [Select Deployment] → Logs
\`\`\`

### Common Errors

**Error**: `Failed to fetch` or `NetworkError`  
**Cause**: CORS not configured or API unreachable  
**Fix**: Check CORS origins in `main.py`, verify API is up

**Error**: `502 Bad Gateway`  
**Cause**: API container down or nginx misconfiguration  
**Fix**: `docker ps` to verify containers, restart if needed

**Error**: `TypeError: Cannot read property 'response' of undefined`  
**Cause**: API response format mismatch  
**Fix**: Check API response structure, update UI parsing logic

---

## 🎯 Next Steps

### Immediate
1. ✅ **DONE**: Enable CORS in backend API
2. ⏳ **TODO**: Deploy to Vercel with updated env vars
3. ⏳ **TODO**: Test full query flow (chat → backend → response)
4. ⏳ **TODO**: Verify VEE report rendering

### Short-term
1. Add HTTPS support (nginx reverse proxy + Let's Encrypt)
2. Implement proper authentication (Keycloak integration)
3. Add error boundary components for graceful error handling
4. Implement loading states and skeleton screens

### Medium-term
1. Add real-time updates via WebSocket
2. Implement conversation history persistence
3. Add portfolio management UI (connect to `portfolio` table)
4. Create admin dashboard for system monitoring

---

## 📚 References

- **Vercel Docs**: https://vercel.com/docs
- **Next.js Docs**: https://nextjs.org/docs
- **Backend API**: http://161.97.140.157:8004 (VPS)
- **Qdrant Dashboard**: http://161.97.140.157:6333/dashboard
- **Prometheus Metrics**: http://161.97.140.157:8004/metrics

---

**Status**: ✅ Ready for Testing  
**Last Updated**: October 29, 2025  
**Maintainer**: Vitruvyan Engineering Team
