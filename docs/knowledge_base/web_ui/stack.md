---
tags:
  - web-ui
  - installation
---

# Web UI Stack — Technology & Tools

> **Last updated**: Feb 20, 2026 21:30 UTC  
> **Purpose**: Complete technology breakdown for Vitruvyan Web UI  
> **Status**: ✅ Production stack (Feb 2026)

---

## Overview

The Vitruvyan Web UI is built on a modern, production-grade stack optimized for:

- **Developer experience** — TypeScript, hot reload, smart defaults
- **Performance** — Server-side rendering, code splitting, edge deployment
- **Accessibility** — WCAG 2.1 AA compliant components
- **Maintainability** — Strong typing, contract enforcement, modular architecture

---

## Core Stack

### Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 15.1.7 | React meta-framework (App Router) |
| **React** | 18.3.1 | UI library (concurrent features) |
| **TypeScript** | 5.x | Type system (strict mode) |

**Why Next.js 15?**
- **App Router** — File-based routing with layouts, server components
- **Server Components** — Zero JS for static content (faster loads)
- **Turbopack** — Rust-based bundler (7x faster than Webpack)
- **Incremental Static Regeneration (ISR)** — Static + dynamic hybrid
- **Edge Functions** — Deploy backend logic globally (low latency)

**Why TypeScript?**
- Contract enforcement at compile time
- IntelliSense for adapters, contracts, components
- Refactoring safety (rename, move, extract)
- Self-documenting code (interfaces as specs)

---

## UI Components

### Component Library

| Technology | Version | Purpose |
|------------|---------|---------|
| **Radix UI** | Latest | Unstyled, accessible primitives |
| **lucide-react** | Latest | Icon library (1000+ icons) |
| **Tailwind CSS** | 3.4.x | Utility-first CSS framework |

**Radix UI Primitives Used**:
- `Accordion` — Collapsible evidence sections
- `Dialog` — Modals for confirmation/details
- `Tooltip` — VEE annotations, metric explanations
- `Tabs` — Multi-view switching (e.g., chart types)
- `Select` — Dropdowns for filters
- `Checkbox`, `RadioGroup` — Form inputs

**Why Radix UI?**
- **Accessibility built-in** — ARIA labels, keyboard navigation, focus management
- **Unstyled** — Full Tailwind control (no CSS fights)
- **Headless** — Compose your own UX (adapter pattern aligns perfectly)
- **Type-safe** — TypeScript definitions included

**Tailwind Configuration**:
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

## Data Fetching & State

### HTTP Client

| Technology | Version | Purpose |
|------------|---------|---------|
| **Native Fetch API** | Built-in | HTTP requests (modern browsers) |
| **SWR** | Latest (optional) | Client-side data fetching with cache |

**Why Native Fetch?**
- Next.js 15 extends `fetch()` with caching, revalidation
- No external dependencies
- TypeScript-friendly

**SWR for Client-Side** (optional):
```typescript
import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then(r => r.json());

function MyComponent() {
  const { data, error } = useSWR('/api/graph/query', fetcher);
  
  if (error) return <div>Failed to load</div>;
  if (!data) return <div>Loading...</div>;
  
  return <div>{data.result}</div>;
}
```

---

### State Management

**No Redux/Zustand** — React Server Components + Context API sufficient.

| Pattern | Use Case |
|---------|----------|
| **React Server Components** | Static data fetching (server-side) |
| **React Context** | Global state (auth, theme, domain) |
| **useState/useReducer** | Local component state (accordions, forms) |
| **URL State** | Filters, pagination (shareable links) |

**Auth Context Example**:
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
  // Implementation
  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
```

---

## Styling & Design Tokens

### CSS Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| **Tailwind CSS** | 3.4.x | Utility-first CSS |
| **PostCSS** | Latest | CSS processing |
| **Autoprefixer** | Latest | Browser compatibility |

**Design Tokens** (`components/theme/tokens.js`):
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

**Dark Mode Support**:
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

## Markdown & Rich Text

### Markdown Rendering

| Technology | Version | Purpose |
|------------|---------|---------|
| **react-markdown** | Latest | Markdown → React components |
| **remark-gfm** | Latest | GitHub Flavored Markdown (tables, strikethrough) |
| **remark-math** | Latest | Math equations (KaTeX support) |

**Usage**:
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

## Development Tools

### Package Manager

| Technology | Version | Purpose |
|------------|---------|---------|
| **pnpm** | Latest (recommended) | Fast, disk-efficient package manager |
| **npm** | 10.x (alternative) | Standard Node.js package manager |

**Why pnpm?**
- **3x faster** installs than npm
- **Shared disk cache** — Single copy of dependencies across projects
- **Strict** — No hoisting surprises (better reproducibility)

**Installation**:
```bash
npm install -g pnpm
pnpm install
pnpm dev
```

---

### Linting & Formatting

| Technology | Version | Purpose |
|------------|---------|---------|
| **ESLint** | Latest | TypeScript/React linting |
| **Prettier** | Latest | Code formatting |
| **eslint-config-next** | Latest | Next.js-optimized rules |

**ESLint Config** (`.eslintrc.json`):
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

**Prettier Config** (`.prettierrc`):
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

| Technology | Version | Purpose |
|------------|---------|---------|
| **Jest** | Latest | Unit test runner |
| **React Testing Library** | Latest | Component testing |
| **Playwright** | Latest (optional) | E2E testing |

**Jest Config** (`jest.config.js`):
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

**Example Adapter Test**:
```typescript
import { ConversationalAdapter } from '@/components/adapters/ConversationalAdapter';

describe('ConversationalAdapter', () => {
  it('should match conversational intent', () => {
    const adapter = new ConversationalAdapter();
    expect(adapter.match({ intent: 'conversational' })).toBe(true);
  });

  it('should produce valid UIResponsePayload', () => {
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

### Build System

| Technology | Version | Purpose |
|------------|---------|---------|
| **Turbopack** | Built-in Next.js 15 | Development bundler |
| **SWC** | Built-in Next.js 15 | TypeScript/JSX compiler (Rust) |

**Build Commands**:
```bash
pnpm dev       # Development server (http://localhost:3000)
pnpm build     # Production build (optimized)
pnpm start     # Production server
pnpm lint      # ESLint check
pnpm test      # Run tests
```

**Build Output**:
```
.next/
├── static/           # Static assets (images, fonts)
├── server/           # Server-side code
└── cache/            # Build cache
```

---

### Deployment Targets

| Platform | Configuration | Notes |
|----------|---------------|-------|
| **Vercel** | Zero-config | Official Next.js host (Edge Functions, ISR) |
| **Docker** | `Dockerfile` included | Self-hosted (Kubernetes, VPS) |
| **Static Export** | `output: 'export'` | CDN deployment (no SSR) |

**Docker Deployment**:
```dockerfile
# Dockerfile
FROM node:20-alpine AS base
WORKDIR /app

# Dependencies
FROM base AS deps
COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# Build
FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Production
FROM base AS runner
ENV NODE_ENV production
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
```

**Build Command**:
```bash
docker build -t vitruvyan-ui .
docker run -p 3000:3000 vitruvyan-ui
```

---

## Environment Configuration

### Environment Variables

| Variable | Example | Purpose |
|----------|---------|---------|
| `NEXT_PUBLIC_API_GRAPH_URL` | `http://localhost:8420` | LangGraph API endpoint |
| `NEXT_PUBLIC_API_CONCLAVE_URL` | `http://localhost:8200` | Synaptic Conclave API |
| `NEXT_PUBLIC_ENV` | `production` | Environment name |

**`.env.local` (development)**:
```env
NEXT_PUBLIC_API_GRAPH_URL=http://localhost:8420
NEXT_PUBLIC_API_CONCLAVE_URL=http://localhost:8200
NEXT_PUBLIC_ENV=development
```

**Access in code**:
```typescript
const apiUrl = process.env.NEXT_PUBLIC_API_GRAPH_URL;
```

---

## Performance Optimizations

### Code Splitting

Next.js automatically code-splits by route:
- Each route = separate JavaScript bundle
- Shared code extracts to `_app` chunk
- Dynamic imports for heavy components

**Dynamic Import Example**:
```typescript
import dynamic from 'next/dynamic';

const HeavyChart = dynamic(() => import('@/components/HeavyChart'), {
  loading: () => <p>Loading chart...</p>,
  ssr: false // Disable server-side rendering
});
```

---

### Image Optimization

Next.js `<Image>` component:
- Automatic WebP conversion
- Lazy loading (off-screen images)
- Responsive sizes

```typescript
import Image from 'next/image';

<Image
  src="/logo.png"
  alt="Vitruvyan Logo"
  width={200}
  height={50}
  priority // Above-the-fold images
/>
```

---

### Font Optimization

Next.js `next/font` (built-in):
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

**Why next/font?**
- Zero layout shift (font metrics precomputed)
- Self-hosted fonts (no Google CDN request)
- Automatic subset selection

---

## Accessibility (WCAG 2.1 AA)

### Tools

| Technology | Version | Purpose |
|------------|---------|---------|
| **axe DevTools** | Browser extension | Accessibility auditing |
| **eslint-plugin-jsx-a11y** | Latest | Accessibility linting |

**Key Requirements**:
- Keyboard navigation (Tab, Enter, Escape, Arrow keys)
- Screen reader labels (`aria-label`, `aria-describedby`)
- Color contrast ≥ 4.5:1 (text), ≥ 3:1 (UI)
- Focus indicators visible

**Example**:
```typescript
<button
  onClick={handleClick}
  aria-label="Close dialog"
  className="focus:outline-none focus:ring-2 focus:ring-blue-500"
>
  <X size={20} aria-hidden="true" />
</button>
```

---

## Monitoring & Analytics

### Error Tracking

| Technology | Optional | Purpose |
|------------|----------|---------|
| **Sentry** | Yes | Error tracking, performance monitoring |

**Setup** (optional):
```bash
pnpm add @sentry/nextjs
npx @sentry/wizard -i nextjs
```

---

### Web Vitals

Built-in to Next.js:
```typescript
// app/layout.tsx
export function reportWebVitals(metric) {
  console.log(metric); // { id, name, value, label }
  // Send to analytics endpoint
}
```

**Tracked Metrics**:
- **TTFB** — Time to First Byte
- **FCP** — First Contentful Paint
- **LCP** — Largest Contentful Paint
- **CLS** — Cumulative Layout Shift
- **FID** — First Input Delay

---

## Version Matrix

| Technology | Version | Release | Status |
|------------|---------|---------|--------|
| Next.js | 15.1.7 | Jan 2026 | ✅ Production |
| React | 18.3.1 | Apr 2024 | ✅ Stable |
| TypeScript | 5.7.2 | Jan 2026 | ✅ Production |
| Tailwind CSS | 3.4.16 | Dec 2024 | ✅ Production |
| Radix UI | 1.2.x | Ongoing | ✅ Stable |
| pnpm | 9.15.2 | Feb 2026 | ✅ Recommended |

---

## Upgrade Strategy

### Minor Version Upgrades (Safe)

```bash
pnpm update --latest --interactive
```

Review changelogs:
- Next.js: https://github.com/vercel/next.js/releases
- React: https://react.dev/blog
- Tailwind: https://tailwindcss.com/blog

---

### Major Version Upgrades (Breaking Changes)

1. **Read migration guide** (official docs)
2. **Test in staging** environment
3. **Run compatibility checks**:
   ```bash
   pnpm build
   pnpm test
   pnpm lint
   ```
4. **Incremental rollout** (feature flags, canary deployment)

---

## References

- [Philosophy](philosophy.md) — Architectural principles
- [Contracts](contracts.md) — TypeScript interface documentation
- [Overview](index.md) — UI architecture summary
- [Next.js Docs](https://nextjs.org/docs) — Official Next.js documentation
- [Radix UI](https://www.radix-ui.com/) — Component primitives
- [Tailwind CSS](https://tailwindcss.com/) — Styling framework

---

**Last updated**: Feb 20, 2026 21:30 UTC
