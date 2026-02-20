# Stack Web UI — Tecnologie & Strumenti

> **Ultimo aggiornamento**: 20 Feb 2026 21:30 UTC  
> **Scopo**: Analisi tecnologie completa per Vitruvyan Web UI  
> **Stato**: ✅ Stack produzione (Feb 2026)

---

## Panoramica

La Web UI di Vitruvyan è costruita su uno stack moderno e production-grade ottimizzato per:

- **Developer experience** — TypeScript, hot reload, default intelligenti
- **Performance** — Server-side rendering, code splitting, deployment edge
- **Accessibilità** — Componenti conformi WCAG 2.1 AA
- **Manutenibilità** — Tipizzazione forte, enforcement contratti, architettura modulare

---

## Stack Core

### Framework

| Tecnologia | Versione | Scopo |
|------------|----------|-------|
| **Next.js** | 15.1.7 | Meta-framework React (App Router) |
| **React** | 18.3.1 | Libreria UI (funzionalità concurrent) |
| **TypeScript** | 5.x | Sistema tipi (strict mode) |

**Perché Next.js 15?**
- **App Router** — Routing basato su file con layout, server component
- **Server Components** — Zero JS per contenuto statico (caricamenti veloci)
- **Turbopack** — Bundler basato su Rust (7x più veloce di Webpack)
- **Incremental Static Regeneration (ISR)** — Ibrido statico + dinamico
- **Edge Functions** — Deploy logica backend globalmente (bassa latenza)

**Perché TypeScript?**
- Enforcement contratti a compile time
- IntelliSense per adapter, contratti, componenti
- Sicurezza refactoring (rinomina, sposta, estrai)
- Codice auto-documentato (interfacce come specifiche)

---

## Componenti UI

### Libreria Componenti

| Tecnologia | Versione | Scopo |
|------------|----------|-------|
| **Radix UI** | Latest | Primitive accessibili senza stile |
| **lucide-react** | Latest | Libreria icone (1000+ icone) |
| **Tailwind CSS** | 3.4.x | Framework CSS utility-first |

**Primitive Radix UI Utilizzate**:
- `Accordion` — Sezioni evidenze richiudibili
- `Dialog` — Modal per conferma/dettagli
- `Tooltip` — Annotazioni VEE, spiegazioni metriche
- `Tabs` — Cambio multi-vista (es. tipi grafici)
- `Select` — Dropdown per filtri
- `Checkbox`, `RadioGroup` — Input form

**Perché Radix UI?**
- **Accessibilità integrata** — Label ARIA, navigazione tastiera, gestione focus
- **Senza stile** — Controllo Tailwind completo (nessun conflitto CSS)
- **Headless** — Componi la tua UX (allineamento perfetto con pattern adapter)
- **Type-safe** — Definizioni TypeScript incluse

**Configurazione Tailwind**:
```javascript
// tailwind.config.js
module.exports = {
  content: [
    './components/**/*.{js,ts,jsx,tsx}',
    './app/**/*.{js,ts,jsx,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        vitruvyan: {
          primary: '#000000',
          accent: '#3b82f6'
        },
        metrics: {
          positive: '#10b981',
          negative: '#ef4444',
          neutral: '#6b7280'
        }
      },
      fontFamily: {
        mono: ['Inconsolata', 'monospace']
      }
    }
  }
};
```

---

## Data Fetching & Stato

### Client HTTP

| Tecnologia | Versione | Scopo |
|------------|----------|-------|
| **API Fetch Nativa** | Integrata | Richieste HTTP (browser moderni) |
| **SWR** | Latest (opzionale) | Data fetching client-side con cache |

**Perché Fetch Nativo?**
- Next.js 15 estende `fetch()` con caching, revalidation
- Nessuna dipendenza esterna
- TypeScript-friendly

**SWR per Client-Side** (opzionale):
```typescript
import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then(r => r.json());

function MyComponent() {
  const { data, error } = useSWR('/api/graph/query', fetcher);
  
  if (error) return <div>Caricamento fallito</div>;
  if (!data) return <div>Caricamento...</div>;
  
  return <div>{data.result}</div>;
}
```

---

### Gestione Stato

**No Redux/Zustand** — React Server Components + Context API sufficienti.

| Pattern | Caso d'Uso |
|---------|------------|
| **React Server Components** | Fetching dati statico (server-side) |
| **React Context** | Stato globale (auth, theme, domain) |
| **useState/useReducer** | Stato componente locale (accordion, form) |
| **URL State** | Filtri, paginazione (link condivisibili) |

**Esempio Context Auth**:
```typescript
// contexts/AuthContext.tsx
import { createContext, useContext, ReactNode } from 'react';

interface AuthContextType {
  user: User | null;
  login: (credentials: Credentials) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  // Implementazione
  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth deve essere usato dentro AuthProvider");
  return context;
}
```

---

## Styling & Token Design

### Framework CSS

| Tecnologia | Versione | Scopo |
|------------|----------|-------|
| **Tailwind CSS** | 3.4.x | CSS utility-first |
| **PostCSS** | Latest | Elaborazione CSS |
| **Autoprefixer** | Latest | Compatibilità browser |

**Token Design** (`components/theme/tokens.js`):
```javascript
export const tokens = {
  colors: {
    vitruvyan: {
      bg: 'bg-white dark:bg-gray-900',
      border: 'border-gray-200 dark:border-gray-700',
      text: 'text-gray-900 dark:text-gray-100'
    },
    metrics: {
      blue: 'bg-blue-50 border-blue-200 text-blue-900',
      green: 'bg-green-50 border-green-200 text-green-900',
      orange: 'bg-orange-50 border-orange-200 text-orange-900',
      red: 'bg-red-50 border-red-200 text-red-900'
    }
  },
  spacing: {
    card: { gap: '1rem', padding: '1.25rem' },
    section: { gap: '1.25rem' },
    metric: { gap: '0.75rem', padding: '1rem' }
  },
  radius: {
    card: '0.75rem',
    metric: '0.5rem',
    chip: '9999px'
  }
};
```

**Supporto Dark Mode**:
```typescript
// app/layout.tsx
export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
        {children}
      </body>
    </html>
  );
}
```

---

## Markdown & Testo Ricco

### Rendering Markdown

| Tecnologia | Versione | Scopo |
|------------|----------|-------|
| **react-markdown** | Latest | Markdown → Componenti React |
| **remark-gfm** | Latest | GitHub Flavored Markdown (tabelle, barrato) |
| **remark-math** | Latest | Equazioni matematiche (supporto KaTeX) |

**Utilizzo**:
```typescript
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function NarrativeBlock({ text }: { text: string }) {
  return (
    <Markdown remarkPlugins={[remarkGfm]}>
      {text}
    </Markdown>
  );
}
```

---

## Strumenti Sviluppo

### Package Manager

| Tecnologia | Versione | Scopo |
|------------|----------|-------|
| **pnpm** | Latest (raccomandato) | Package manager veloce, efficiente su disco |
| **npm** | 10.x (alternativa) | Package manager standard Node.js |

**Perché pnpm?**
- **3x più veloce** installazioni rispetto a npm
- **Cache disco condivisa** — Copia singola dipendenze tra progetti
- **Strict** — Nessuna sorpresa hoisting (migliore riproducibilità)

**Installazione**:
```bash
npm install -g pnpm
pnpm install
pnpm dev
```

---

### Linting & Formattazione

| Tecnologia | Versione | Scopo |
|------------|---------|-------|
| **ESLint** | Latest | Linting TypeScript/React |
| **Prettier** | Latest | Formattazione codice |
| **eslint-config-next** | Latest | Regole ottimizzate Next.js |

**Config ESLint** (`.eslintrc.json`):
```json
{
  "extends": [
    "next/core-web-vitals",
    "prettier"
  ],
  "rules": {
    "no-console": "warn",
    "prefer-const": "error",
    "@typescript-eslint/no-unused-vars": "error"
  }
}
```

**Config Prettier** (`.prettierrc`):
```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

---

### Testing

| Tecnologia | Versione | Scopo |
|------------|----------|-------|
| **Jest** | Latest | Test runner unit |
| **React Testing Library** | Latest | Test componenti |
| **Playwright** | Latest (opzionale) | Test E2E |

**Config Jest** (`jest.config.js`):
```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1'
  }
};
```

**Esempio Test Adapter**:
```typescript
import { ConversationalAdapter } from '@/components/adapters/ConversationalAdapter';

describe('ConversationalAdapter', () => {
  it('dovrebbe corrispondere intent conversational', () => {
    const adapter = new ConversationalAdapter();
    expect(adapter.match({ intent: 'conversational' })).toBe(true);
  });

  it('dovrebbe produrre UIResponsePayload valido', () => {
    const adapter = new ConversationalAdapter();
    const state = { summary: 'Test', intent: 'conversational' };
    const payload = adapter.map(state);
    
    expect(payload.narrative).toBeDefined();
    expect(payload.narrative.text).toBe('Test');
  });
});
```

---

## Build & Deployment

### Sistema Build

| Tecnologia | Versione | Scopo |
|------------|----------|-------|
| **Turbopack** | Integrato Next.js 15 | Bundler sviluppo |
| **SWC** | Integrato Next.js 15 | Compilatore TypeScript/JSX (Rust) |

**Comandi Build**:
```bash
pnpm dev       # Server sviluppo (http://localhost:3000)
pnpm build     # Build produzione (ottimizzato)
pnpm start     # Server produzione
pnpm lint      # Check ESLint
pnpm test      # Esegui test
```

**Output Build**:
```
.next/
├── static/           # Asset statici (immagini, font)
├── server/           # Codice server-side
└── cache/            # Cache build
```

---

### Target Deployment

| Piattaforma | Configurazione | Note |
|-------------|----------------|------|
| **Vercel** | Zero-config | Host ufficiale Next.js (Edge Functions, ISR) |
| **Docker** | `Dockerfile` incluso | Self-hosted (Kubernetes, VPS) |
| **Export Statico** | `output: 'export'` | Deployment CDN (no SSR) |

**Deployment Docker**:
```dockerfile
# Dockerfile
FROM node:20-alpine AS base
WORKDIR /app

# Dipendenze
FROM base AS deps
COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# Build
FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Produzione
FROM base AS runner
ENV NODE_ENV production
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
```

**Comando Build**:
```bash
docker build -t vitruvyan-ui .
docker run -p 3000:3000 vitruvyan-ui
```

---

## Configurazione Ambiente

### Variabili Ambiente

| Variabile | Esempio | Scopo |
|-----------|---------|-------|
| `NEXT_PUBLIC_API_GRAPH_URL` | `http://localhost:8420` | Endpoint API LangGraph |
| `NEXT_PUBLIC_API_CONCLAVE_URL` | `http://localhost:8200` | API Synaptic Conclave |
| `NEXT_PUBLIC_ENV` | `production` | Nome ambiente |

**`.env.local` (sviluppo)**:
```env
NEXT_PUBLIC_API_GRAPH_URL=http://localhost:8420
NEXT_PUBLIC_API_CONCLAVE_URL=http://localhost:8200
NEXT_PUBLIC_ENV=development
```

**Accesso nel codice**:
```typescript
const apiUrl = process.env.NEXT_PUBLIC_API_GRAPH_URL;
```

---

## Ottimizzazioni Performance

### Code Splitting

Next.js effettua code splitting automatico per route:
- Ogni route = bundle JavaScript separato
- Codice condiviso estratto in chunk `_app`
- Import dinamici per componenti pesanti

**Esempio Import Dinamico**:
```typescript
import dynamic from 'next/dynamic';

const HeavyChart = dynamic(() => import('@/components/HeavyChart'), {
  loading: () => <p>Caricamento grafico...</p>,
  ssr: false // Disabilita server-side rendering
});
```

---

### Ottimizzazione Immagini

Componente Next.js `<Image>`:
- Conversione WebP automatica
- Lazy loading (immagini fuori schermo)
- Dimensioni responsive

```typescript
import Image from 'next/image';

<Image
  src="/logo.png"
  alt="Logo Vitruvyan"
  width={200}
  height={50}
  priority // Immagini above-the-fold
/>
```

---

### Ottimizzazione Font

Next.js `next/font` (integrato):
```typescript
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'] });

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={inter.className}>
      <body>{children}</body>
    </html>
  );
}
```

**Perché next/font?**
- Zero layout shift (metriche font pre-calcolate)
- Font self-hosted (nessuna richiesta CDN Google)
- Selezione subset automatica

---

## Accessibilità (WCAG 2.1 AA)

### Strumenti

| Tecnologia | Versione | Scopo |
|------------|----------|-------|
| **axe DevTools** | Estensione browser | Audit accessibilità |
| **eslint-plugin-jsx-a11y** | Latest | Linting accessibilità |

**Requisiti Chiave**:
- Navigazione tastiera (Tab, Enter, Escape, Frecce)
- Label screen reader (`aria-label`, `aria-describedby`)
- Contrasto colore ≥ 4.5:1 (testo), ≥ 3:1 (UI)
- Indicatori focus visibili

**Esempio**:
```typescript
<button
  onClick={handleClick}
  aria-label="Chiudi dialog"
  className="focus:outline-none focus:ring-2 focus:ring-blue-500"
>
  <X size={20} aria-hidden="true" />
</button>
```

---

## Monitoring & Analytics

### Error Tracking

| Tecnologia | Opzionale | Scopo |
|------------|-----------|-------|
| **Sentry** | Sì | Error tracking, monitoring performance |

**Setup** (opzionale):
```bash
pnpm add @sentry/nextjs
npx @sentry/wizard -i nextjs
```

---

### Web Vitals

Integrato in Next.js:
```typescript
// app/layout.tsx
export function reportWebVitals(metric) {
  console.log(metric); // { id, name, value, label }
  // Invia a endpoint analytics
}
```

**Metriche Tracciate**:
- **TTFB** — Time to First Byte
- **FCP** — First Contentful Paint
- **LCP** — Largest Contentful Paint
- **CLS** — Cumulative Layout Shift
- **FID** — First Input Delay

---

## Matrice Versioni

| Tecnologia | Versione | Rilascio | Stato |
|------------|----------|----------|-------|
| Next.js | 15.1.7 | Gen 2026 | ✅ Produzione |
| React | 18.3.1 | Apr 2024 | ✅ Stabile |
| TypeScript | 5.7.2 | Gen 2026 | ✅ Produzione |
| Tailwind CSS | 3.4.16 | Dic 2024 | ✅ Produzione |
| Radix UI | 1.2.x | In corso | ✅ Stabile |
| pnpm | 9.15.2 | Feb 2026 | ✅ Raccomandato |

---

## Strategia Upgrade

### Upgrade Versione Minor (Sicuri)

```bash
pnpm update --latest --interactive
```

Rivedi changelog:
- Next.js: https://github.com/vercel/next.js/releases
- React: https://react.dev/blog
- Tailwind: https://tailwindcss.com/blog

---

### Upgrade Versione Major (Breaking Change)

1. **Leggi guida migrazione** (documentazione ufficiale)
2. **Testa in ambiente staging**
3. **Esegui check compatibilità**:
   ```bash
   pnpm build
   pnpm test
   pnpm lint
   ```
4. **Rollout incrementale** (feature flag, canary deployment)

---

## Riferimenti

- [Filosofia](philosophy.it.md) — Principi architetturali
- [Contratti](contracts.it.md) — Documentazione interfacce TypeScript
- [Panoramica](index.it.md) — Riepilogo architettura UI
- [Next.js Docs](https://nextjs.org/docs) — Documentazione ufficiale Next.js
- [Radix UI](https://www.radix-ui.com/) — Primitive componenti
- [Tailwind CSS](https://tailwindcss.com/) — Framework styling

---

**Ultimo aggiornamento**: 20 Feb 2026 21:30 UTC
