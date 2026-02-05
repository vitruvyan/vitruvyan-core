# Plasticity Admin UI — Implementation Specification
**Version**: 1.0  
**Date**: January 26, 2026  
**Status**: FUTURE IMPLEMENTATION  
**Priority**: P2 (Post-MVP)  
**Estimated Effort**: 30-40 hours

---

## 1. Executive Summary

This document specifies the Plasticity Admin UI, an internal administration panel for monitoring and managing Vitruvyan's bounded learning system. The UI will be integrated into the existing Next.js frontend (`vitruvyan-ui`) as protected `/admin` routes, leveraging Keycloak SSO for authentication and role-based access control.

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Framework | Next.js (existing) | Unified stack, component reuse |
| Auth | Keycloak (existing) | SSO already implemented |
| Metrics | Prometheus + Grafana | Already deployed |
| State | React Query + SWR | Real-time updates |
| Charts | Recharts (existing) | Already in vitruvyan-ui |

---

## 2. Architecture

### 2.1 Route Structure

```
vitruvyan-ui/
├── app/
│   ├── (public)/                    # Existing public routes
│   │   └── ...
│   │
│   └── (admin)/                     # NEW: Protected admin routes
│       ├── layout.jsx               # Admin shell (sidebar, header)
│       ├── page.jsx                 # Dashboard overview
│       │
│       ├── plasticity/              # Plasticity Admin
│       │   ├── page.jsx             # Health dashboard
│       │   ├── consumers/
│       │   │   ├── page.jsx         # Consumer list
│       │   │   └── [id]/page.jsx    # Consumer detail
│       │   ├── parameters/
│       │   │   ├── page.jsx         # Parameter list
│       │   │   └── [id]/page.jsx    # Parameter detail + override
│       │   ├── anomalies/
│       │   │   ├── page.jsx         # Anomaly timeline
│       │   │   └── [id]/page.jsx    # Anomaly detail
│       │   └── trajectories/
│       │       └── page.jsx         # Parameter trajectories
│       │
│       ├── cognitive-bus/           # FUTURE: Bus monitoring
│       │   └── page.jsx
│       │
│       └── sacred-orders/           # FUTURE: Sacred Orders status
│           └── page.jsx
│
├── components/
│   ├── admin/                       # NEW: Admin-specific components
│   │   ├── AdminLayout.jsx          # Shell with sidebar
│   │   ├── AdminSidebar.jsx         # Navigation
│   │   ├── HealthGauge.jsx          # Circular health indicator
│   │   ├── MetricBar.jsx            # Horizontal metric bar
│   │   ├── ParameterChart.jsx       # Time-series trajectory
│   │   ├── AnomalyCard.jsx          # Anomaly display card
│   │   ├── ConsumerCard.jsx         # Consumer summary card
│   │   └── OverrideModal.jsx        # Parameter override dialog
│   │
│   └── ...                          # Existing components
│
└── lib/
    └── admin/                       # NEW: Admin utilities
        ├── plasticityApi.js         # API client for plasticity
        └── hooks/
            ├── usePlasticityHealth.js
            ├── useConsumers.js
            ├── useAnomalies.js
            └── useParameterTrajectory.js
```

### 2.2 Backend API Endpoints

New endpoints to be added to `vitruvyan_api_graph` or dedicated admin service:

```
GET  /admin/plasticity/health
     → { health_score, overall_health, metrics, anomaly_count }

GET  /admin/plasticity/consumers
     → [{ name, parameters, health, last_adjustment }]

GET  /admin/plasticity/consumers/:id
     → { name, parameters: [{ name, value, bounds, trajectory }] }

GET  /admin/plasticity/parameters
     → [{ consumer, name, value, bounds, adjustments_7d }]

GET  /admin/plasticity/parameters/:consumer/:name
     → { value, bounds, trajectory: [{ timestamp, value }] }

POST /admin/plasticity/parameters/:consumer/:name/override
     → { success, previous_value, new_value }
     Body: { value: 0.65, reason: "Manual adjustment" }

POST /admin/plasticity/parameters/:consumer/:name/lock
     → { success, locked: true/false }

POST /admin/plasticity/parameters/:consumer/:name/reset
     → { success, new_value: default_value }

GET  /admin/plasticity/anomalies
     → [{ id, type, consumer, parameter, severity, timestamp, status }]

POST /admin/plasticity/anomalies/:id/acknowledge
     → { success }

GET  /admin/plasticity/trajectories/:consumer/:parameter
     → { values: [{ timestamp, value }], bounds: { min, max } }
```

### 2.3 Authentication & Authorization

```javascript
// middleware.js - Keycloak role-based protection

import { getToken } from "next-auth/jwt";
import { NextResponse } from "next/server";

export async function middleware(req) {
  const token = await getToken({ req });
  const { pathname } = req.nextUrl;

  // Admin routes require "admin" role
  if (pathname.startsWith("/admin")) {
    if (!token) {
      return NextResponse.redirect(new URL("/auth/signin", req.url));
    }
    
    const roles = token.realm_access?.roles || [];
    if (!roles.includes("admin") && !roles.includes("vitruvyan-admin")) {
      return NextResponse.redirect(new URL("/unauthorized", req.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/admin/:path*"],
};
```

---

## 3. UI Components Specification

### 3.1 Health Dashboard (`/admin/plasticity`)

```
┌────────────────────────────────────────────────────────────────────┐
│  PLASTICITY HEALTH DASHBOARD                        [Refresh] [⚙]  │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   HEALTH     │  │  STABILITY   │  │   SUCCESS    │             │
│  │              │  │              │  │              │             │
│  │     76%      │  │    100%      │  │     35%      │             │
│  │   DEGRADED   │  │   STABLE     │  │   ⚠️ LOW     │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  METRICS OVERVIEW                                            │  │
│  │                                                               │  │
│  │  Stability Index    [██████████████████████████████] 100%    │  │
│  │  Success Rate       [███████░░░░░░░░░░░░░░░░░░░░░░]  35%    │  │
│  │  Coverage           [██████████████████████████████] 100%    │  │
│  │  Consumer Diversity [████████████████████░░░░░░░░░░]  75%    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  RECENT ANOMALIES                              [View All →]  │  │
│  │                                                               │  │
│  │  🔄 OSCILLATION  NarrativeEngine/confidence    2h ago  0.6  │  │
│  │  ➡️ DRIFT        RiskGuardian/threshold        1d ago  0.4  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  CONSUMER HEALTH                               [View All →]  │  │
│  │                                                               │  │
│  │  NarrativeEngine   ████████░░  78%   3 params   ↓ trending  │  │
│  │  RiskGuardian      ██████████  95%   2 params   → stable    │  │
│  │  OrthodoxyWarden   █████████░  91%   1 param    ↑ improving │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 3.2 Consumer Detail (`/admin/plasticity/consumers/[id]`)

```
┌────────────────────────────────────────────────────────────────────┐
│  ← Back    NARRATIVEENGINE                              DEGRADED   │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Health: 78%    Adjustments (7d): 8    Success Rate: 42%          │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  PARAMETERS                                                  │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │                                                               │  │
│  │  confidence_threshold                                         │  │
│  │  ┌─────────────────────────────────────────────────────────┐ │  │
│  │  │  Current: 0.55    Bounds: [0.30 - 0.90]    Default: 0.60│ │  │
│  │  │                                                          │ │  │
│  │  │  0.9 ┤ - - - - - - - - - - - - - - MAX                  │ │  │
│  │  │  0.7 ┤      ╭─╮                                          │ │  │
│  │  │  0.6 ┤─────╱   ╲─────╭─╮────────                        │ │  │
│  │  │  0.5 ┤              ╲╱   ╲──────  ← CURRENT             │ │  │
│  │  │  0.3 ┤ - - - - - - - - - - - - - - MIN                  │ │  │
│  │  │      └────────────────────────────────────              │ │  │
│  │  │        Jan 20   Jan 22   Jan 24   Jan 26                │ │  │
│  │  │                                                          │ │  │
│  │  │  [Override Value] [Lock Parameter] [Reset to Default]   │ │  │
│  │  └─────────────────────────────────────────────────────────┘ │  │
│  │                                                               │  │
│  │  min_response_length                                          │  │
│  │  ┌─────────────────────────────────────────────────────────┐ │  │
│  │  │  Current: 50    Bounds: [20 - 200]    Default: 50       │ │  │
│  │  │  Status: LOCKED 🔒                                       │ │  │
│  │  │  [Unlock]                                                │ │  │
│  │  └─────────────────────────────────────────────────────────┘ │  │
│  │                                                               │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  RECENT ADJUSTMENTS                                          │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │  Jan 26 15:30  confidence_threshold  0.60 → 0.55  (auto)    │  │
│  │  Jan 25 08:15  confidence_threshold  0.55 → 0.60  (auto)    │  │
│  │  Jan 24 22:00  confidence_threshold  0.60 → 0.55  (auto)    │  │
│  │  Jan 23 10:30  min_response_length   50 → 50      (locked)  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 3.3 Parameter Override Modal

```
┌────────────────────────────────────────────────────────────────────┐
│  OVERRIDE PARAMETER                                           [X]  │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Consumer:    NarrativeEngine                                      │
│  Parameter:   confidence_threshold                                 │
│                                                                    │
│  Current Value:  0.55                                              │
│  Bounds:         [0.30 - 0.90]                                     │
│  Default:        0.60                                              │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  New Value:  [0.65_____________]                             │  │
│  │              ◀──────────●──────────▶                         │  │
│  │              0.30      0.65      0.90                        │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  Reason (required):                                          │  │
│  │  [Manual adjustment based on user feedback analysis______]   │  │
│  │  [__________________________________________________________]│  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ☐ Lock parameter after override (prevent auto-adjustment)        │
│                                                                    │
│  ⚠️ This will immediately affect system behavior.                  │
│                                                                    │
│                              [Cancel]  [Apply Override]            │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 3.4 Anomaly Timeline (`/admin/plasticity/anomalies`)

```
┌────────────────────────────────────────────────────────────────────┐
│  ANOMALY TIMELINE                    [Filter: All ▼]  [7 days ▼]  │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  TODAY                                                       │  │
│  │                                                               │  │
│  │  🔄 OSCILLATION                                    15:30     │  │
│  │  ┌─────────────────────────────────────────────────────────┐│  │
│  │  │  Consumer:   NarrativeEngine                            ││  │
│  │  │  Parameter:  confidence_threshold                       ││  │
│  │  │  Severity:   ████████░░ 0.6/1.0                        ││  │
│  │  │                                                          ││  │
│  │  │  "Parameter oscillating between 0.55 and 0.60 over      ││  │
│  │  │   past 4 adjustments. Consider increasing step_size."   ││  │
│  │  │                                                          ││  │
│  │  │  [Acknowledge] [Investigate] [Auto-fix: Increase Step]  ││  │
│  │  └─────────────────────────────────────────────────────────┘│  │
│  │                                                               │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  YESTERDAY                                                   │  │
│  │                                                               │  │
│  │  ➡️ DRIFT                                          08:15     │  │
│  │  ┌─────────────────────────────────────────────────────────┐│  │
│  │  │  Consumer:   RiskGuardian                               ││  │
│  │  │  Parameter:  risk_threshold                             ││  │
│  │  │  Severity:   ████░░░░░░ 0.4/1.0                        ││  │
│  │  │  Status:     ✓ Resolved                                 ││  │
│  │  │                                                          ││  │
│  │  │  "Consistent upward drift over 5 adjustments.           ││  │
│  │  │   Parameter moved from 0.65 to 0.70."                   ││  │
│  │  └─────────────────────────────────────────────────────────┘│  │
│  │                                                               │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 4. React Components

### 4.1 HealthGauge Component

```jsx
// components/admin/HealthGauge.jsx

import { cn } from "@/lib/utils";

const healthColors = {
  healthy: "text-green-500",
  degraded: "text-yellow-500",
  critical: "text-red-500",
  stalled: "text-gray-400",
};

const healthLabels = {
  healthy: "Healthy",
  degraded: "Degraded",
  critical: "Critical",
  stalled: "Stalled",
};

export function HealthGauge({ score, health, size = "lg" }) {
  const percentage = Math.round(score * 100);
  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;
  
  const sizeClasses = {
    sm: "w-20 h-20",
    md: "w-28 h-28",
    lg: "w-36 h-36",
  };

  return (
    <div className={cn("relative", sizeClasses[size])}>
      <svg className="w-full h-full transform -rotate-90">
        {/* Background circle */}
        <circle
          cx="50%"
          cy="50%"
          r="45%"
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          className="text-gray-200"
        />
        {/* Progress circle */}
        <circle
          cx="50%"
          cy="50%"
          r="45%"
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className={healthColors[health]}
        />
      </svg>
      
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold">{percentage}%</span>
        <span className={cn("text-sm font-medium", healthColors[health])}>
          {healthLabels[health]}
        </span>
      </div>
    </div>
  );
}
```

### 4.2 ParameterChart Component

```jsx
// components/admin/ParameterChart.jsx

import { LineChart, Line, XAxis, YAxis, ReferenceLine, Tooltip, ResponsiveContainer } from "recharts";
import { format } from "date-fns";

export function ParameterChart({ trajectory, bounds, currentValue }) {
  const data = trajectory.map(({ timestamp, value }) => ({
    timestamp: new Date(timestamp).getTime(),
    value,
  }));

  return (
    <div className="h-48 w-full">
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <XAxis
            dataKey="timestamp"
            type="number"
            domain={["dataMin", "dataMax"]}
            tickFormatter={(ts) => format(new Date(ts), "MMM d")}
            tick={{ fontSize: 11 }}
          />
          <YAxis
            domain={[bounds.min - 0.05, bounds.max + 0.05]}
            tick={{ fontSize: 11 }}
            width={40}
          />
          
          {/* Bounds reference lines */}
          <ReferenceLine
            y={bounds.max}
            stroke="#f59e0b"
            strokeDasharray="5 5"
            label={{ value: "MAX", position: "right", fontSize: 10 }}
          />
          <ReferenceLine
            y={bounds.min}
            stroke="#f59e0b"
            strokeDasharray="5 5"
            label={{ value: "MIN", position: "right", fontSize: 10 }}
          />
          
          {/* Default reference line */}
          {bounds.default && (
            <ReferenceLine
              y={bounds.default}
              stroke="#94a3b8"
              strokeDasharray="3 3"
            />
          )}
          
          {/* Value line */}
          <Line
            type="stepAfter"
            dataKey="value"
            stroke="#6366f1"
            strokeWidth={2}
            dot={{ fill: "#6366f1", r: 3 }}
            activeDot={{ r: 5 }}
          />
          
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const { timestamp, value } = payload[0].payload;
              return (
                <div className="bg-white border rounded-lg shadow-lg p-2 text-sm">
                  <p className="font-medium">{format(new Date(timestamp), "MMM d, HH:mm")}</p>
                  <p className="text-indigo-600">Value: {value.toFixed(3)}</p>
                </div>
              );
            }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
```

### 4.3 AnomalyCard Component

```jsx
// components/admin/AnomalyCard.jsx

import { cn } from "@/lib/utils";
import { AlertCircle, TrendingUp, Clock, RefreshCw } from "lucide-react";

const anomalyIcons = {
  oscillation: RefreshCw,
  drift: TrendingUp,
  stagnation: Clock,
  feedback_lag: AlertCircle,
};

const anomalyColors = {
  oscillation: "border-purple-200 bg-purple-50",
  drift: "border-blue-200 bg-blue-50",
  stagnation: "border-gray-200 bg-gray-50",
  feedback_lag: "border-orange-200 bg-orange-50",
};

export function AnomalyCard({ anomaly, onAcknowledge, onInvestigate }) {
  const Icon = anomalyIcons[anomaly.type] || AlertCircle;
  
  return (
    <div className={cn(
      "border rounded-lg p-4",
      anomalyColors[anomaly.type]
    )}>
      <div className="flex items-start gap-3">
        <Icon className="w-5 h-5 mt-0.5 text-gray-600" />
        
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <span className="font-medium text-sm uppercase">
              {anomaly.type}
            </span>
            <span className="text-xs text-gray-500">
              {anomaly.timestamp}
            </span>
          </div>
          
          <p className="text-sm text-gray-700 mt-1">
            {anomaly.consumer}/{anomaly.parameter}
          </p>
          
          <p className="text-sm text-gray-600 mt-2">
            {anomaly.description}
          </p>
          
          <div className="flex items-center gap-2 mt-3">
            <div className="flex-1 bg-gray-200 rounded-full h-1.5">
              <div
                className="bg-gray-600 h-1.5 rounded-full"
                style={{ width: `${anomaly.severity * 100}%` }}
              />
            </div>
            <span className="text-xs text-gray-500">
              {anomaly.severity.toFixed(1)}
            </span>
          </div>
          
          {anomaly.status !== "resolved" && (
            <div className="flex gap-2 mt-3">
              <button
                onClick={onAcknowledge}
                className="text-xs px-2 py-1 bg-white border rounded hover:bg-gray-50"
              >
                Acknowledge
              </button>
              <button
                onClick={onInvestigate}
                className="text-xs px-2 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700"
              >
                Investigate
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

---

## 5. Backend Implementation

### 5.1 Admin API Service

Create new file: `core/api/admin/plasticity_admin.py`

```python
# core/api/admin/plasticity_admin.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from core.cognitive_bus.plasticity import PlasticityObserver
from core.cognitive_bus.plasticity.manager import PlasticityManager
from core.leo.postgres_agent import PostgresAgent
from core.api.auth import require_admin_role

router = APIRouter(prefix="/admin/plasticity", tags=["admin-plasticity"])


class HealthResponse(BaseModel):
    health_score: float
    overall_health: str
    consumers_analyzed: int
    parameters_tracked: int
    adjustments_24h: int
    adjustments_7d: int
    anomaly_count: int
    metrics: dict


class ConsumerSummary(BaseModel):
    name: str
    health: str
    parameter_count: int
    adjustments_7d: int
    success_rate: float
    trend: str


class ParameterDetail(BaseModel):
    consumer: str
    name: str
    current_value: float
    bounds: dict
    default_value: float
    is_locked: bool
    adjustments_7d: int


class ParameterOverride(BaseModel):
    value: float
    reason: str
    lock_after: bool = False


class AnomalySummary(BaseModel):
    id: str
    type: str
    consumer: str
    parameter: str
    severity: float
    timestamp: datetime
    status: str
    description: str


@router.get("/health", response_model=HealthResponse)
async def get_plasticity_health(
    days: int = 7,
    _: dict = Depends(require_admin_role)
):
    """Get overall plasticity system health."""
    pg = PostgresAgent()
    try:
        observer = PlasticityObserver(pg.connection)
        report = await observer.analyze(days=days)
        
        return HealthResponse(
            health_score=report.health_score,
            overall_health=report.overall_health.value,
            consumers_analyzed=report.consumers_analyzed,
            parameters_tracked=report.parameters_tracked,
            adjustments_24h=report.adjustments_24h,
            adjustments_7d=report.adjustments_7d,
            anomaly_count=len(report.anomalies),
            metrics=report.metrics
        )
    finally:
        pg.connection.close()


@router.get("/consumers", response_model=List[ConsumerSummary])
async def list_consumers(_: dict = Depends(require_admin_role)):
    """List all consumers with plasticity enabled."""
    pg = PostgresAgent()
    try:
        with pg.connection.cursor() as cur:
            cur.execute("""
                SELECT 
                    consumer_name,
                    COUNT(DISTINCT parameter_name) as param_count,
                    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as adj_7d,
                    AVG(CASE WHEN outcome_value IS NOT NULL THEN outcome_value ELSE 0.5 END) as avg_success
                FROM plasticity_adjustments pa
                LEFT JOIN plasticity_outcomes po USING (consumer_name, parameter_name)
                GROUP BY consumer_name
                ORDER BY consumer_name
            """)
            rows = cur.fetchall()
        
        return [
            ConsumerSummary(
                name=row[0],
                health="healthy" if row[3] > 0.6 else "degraded" if row[3] > 0.4 else "critical",
                parameter_count=row[1],
                adjustments_7d=row[2],
                success_rate=row[3] or 0.5,
                trend="stable"  # TODO: compute from trajectory
            )
            for row in rows
        ]
    finally:
        pg.connection.close()


@router.get("/parameters/{consumer}/{parameter}", response_model=ParameterDetail)
async def get_parameter_detail(
    consumer: str,
    parameter: str,
    _: dict = Depends(require_admin_role)
):
    """Get detailed parameter information including trajectory."""
    pg = PostgresAgent()
    try:
        with pg.connection.cursor() as cur:
            # Get latest value
            cur.execute("""
                SELECT new_value, created_at
                FROM plasticity_adjustments
                WHERE consumer_name = %s AND parameter_name = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (consumer, parameter))
            row = cur.fetchone()
            
            if not row:
                raise HTTPException(404, "Parameter not found")
            
            # Get bounds from consumer config (simplified)
            bounds = {"min": 0.3, "max": 0.9}  # TODO: load from consumer
            
            return ParameterDetail(
                consumer=consumer,
                name=parameter,
                current_value=row[0],
                bounds=bounds,
                default_value=0.6,  # TODO: load from consumer
                is_locked=False,  # TODO: implement locking
                adjustments_7d=0  # TODO: count
            )
    finally:
        pg.connection.close()


@router.post("/parameters/{consumer}/{parameter}/override")
async def override_parameter(
    consumer: str,
    parameter: str,
    override: ParameterOverride,
    _: dict = Depends(require_admin_role)
):
    """Manually override a parameter value."""
    pg = PostgresAgent()
    try:
        with pg.connection.cursor() as cur:
            # Get current value
            cur.execute("""
                SELECT new_value FROM plasticity_adjustments
                WHERE consumer_name = %s AND parameter_name = %s
                ORDER BY created_at DESC LIMIT 1
            """, (consumer, parameter))
            row = cur.fetchone()
            previous_value = row[0] if row else None
            
            # Insert override as adjustment
            cur.execute("""
                INSERT INTO plasticity_adjustments 
                (consumer_name, parameter_name, old_value, new_value, adjustment_reason, is_manual)
                VALUES (%s, %s, %s, %s, %s, TRUE)
            """, (consumer, parameter, previous_value, override.value, override.reason))
            
            pg.connection.commit()
        
        return {
            "success": True,
            "previous_value": previous_value,
            "new_value": override.value,
            "locked": override.lock_after
        }
    finally:
        pg.connection.close()


@router.get("/anomalies", response_model=List[AnomalySummary])
async def list_anomalies(
    days: int = 7,
    type: Optional[str] = None,
    _: dict = Depends(require_admin_role)
):
    """List detected anomalies."""
    pg = PostgresAgent()
    try:
        observer = PlasticityObserver(pg.connection)
        report = await observer.analyze(days=days)
        
        anomalies = report.anomalies
        if type:
            anomalies = [a for a in anomalies if a.anomaly_type.value == type]
        
        return [
            AnomalySummary(
                id=f"{a.consumer_name}_{a.parameter_name}_{a.detected_at.isoformat()}",
                type=a.anomaly_type.value,
                consumer=a.consumer_name,
                parameter=a.parameter_name,
                severity=a.severity,
                timestamp=a.detected_at,
                status="open",  # TODO: track acknowledgment
                description=a.description
            )
            for a in anomalies
        ]
    finally:
        pg.connection.close()
```

### 5.2 Prometheus Metrics (Already Exists)

File: `core/cognitive_bus/plasticity/metrics.py`

Metrics to expose for Grafana:

```python
# Existing metrics (verify implementation)
plasticity_health_score = Gauge(
    'plasticity_health_score',
    'Overall plasticity system health score',
    ['consumer']
)

plasticity_adjustments_total = Counter(
    'plasticity_adjustments_total',
    'Total parameter adjustments',
    ['consumer', 'parameter', 'direction']
)

plasticity_anomalies_total = Counter(
    'plasticity_anomalies_total',
    'Total anomalies detected',
    ['type', 'consumer']
)

plasticity_parameter_value = Gauge(
    'plasticity_parameter_value',
    'Current parameter value',
    ['consumer', 'parameter']
)

plasticity_success_rate = Gauge(
    'plasticity_success_rate',
    'Current success rate',
    ['consumer', 'parameter']
)
```

---

## 6. User-Facing UX (Chat UI)

### 6.1 Learning Indicator Component

```jsx
// components/chat/LearningIndicator.jsx

import { Brain, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

export function LearningIndicator({ plasticityData, className }) {
  const { adaptation_level, health_score, recent_improvement } = plasticityData;
  
  // Only show if there's meaningful data
  if (health_score < 0.1 || !recent_improvement) return null;
  
  const levels = {
    learning: { label: "Learning", color: "text-purple-600", bg: "bg-purple-50" },
    adapted: { label: "Adapted", color: "text-green-600", bg: "bg-green-50" },
    uncertain: { label: "Exploring", color: "text-amber-600", bg: "bg-amber-50" },
  };
  
  const level = levels[adaptation_level] || levels.learning;

  return (
    <div className={cn(
      "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs",
      level.bg,
      className
    )}>
      <Brain className={cn("w-3.5 h-3.5", level.color)} />
      <span className={level.color}>{level.label}</span>
      
      {/* Progress bar */}
      <div className="w-12 bg-gray-200 rounded-full h-1">
        <div
          className={cn("h-1 rounded-full transition-all duration-500", {
            "bg-purple-500": adaptation_level === "learning",
            "bg-green-500": adaptation_level === "adapted",
            "bg-amber-500": adaptation_level === "uncertain",
          })}
          style={{ width: `${health_score * 100}%` }}
        />
      </div>
      
      <span className="text-gray-500">{Math.round(health_score * 100)}%</span>
    </div>
  );
}
```

### 6.2 Feedback Impact Toast

```jsx
// components/chat/FeedbackImpactToast.jsx

import { Sparkles } from "lucide-react";

export function FeedbackImpactToast({ improvement, onDismiss }) {
  return (
    <div className="fixed bottom-4 right-4 bg-white border border-purple-200 rounded-lg shadow-lg p-4 max-w-sm animate-in slide-in-from-bottom-5">
      <div className="flex items-start gap-3">
        <div className="p-2 bg-purple-100 rounded-full">
          <Sparkles className="w-4 h-4 text-purple-600" />
        </div>
        
        <div className="flex-1">
          <p className="font-medium text-sm text-gray-900">
            Your feedback helped!
          </p>
          <p className="text-sm text-gray-600 mt-1">
            {improvement}
          </p>
        </div>
        
        <button
          onClick={onDismiss}
          className="text-gray-400 hover:text-gray-600"
        >
          ×
        </button>
      </div>
    </div>
  );
}
```

### 6.3 User-Facing API Endpoint

```python
# core/api/plasticity_user.py

@router.get("/plasticity/user-summary")
async def get_user_plasticity_summary(user_id: str):
    """
    Returns user-friendly plasticity metrics for chat UI.
    """
    # Simplified metrics for user consumption
    return {
        "adaptation_level": "learning",  # learning | adapted | uncertain
        "health_score": 0.76,
        "recent_improvement": "Tech sector predictions improved +12%",
        "feedback_impact": {
            "total_feedback": 15,
            "incorporated": 12,
            "last_impact": "Your feedback on NVDA helped improve momentum analysis"
        },
        "show_indicator": True  # Whether to show learning indicator
    }
```

---

## 7. Implementation Phases

### Phase 1: Backend Foundation (8h)
- [ ] Create `/admin/plasticity/*` API endpoints
- [ ] Add `require_admin_role` middleware
- [ ] Verify Prometheus metrics exposure
- [ ] Add `is_manual` and `is_locked` columns to plasticity tables

### Phase 2: Admin UI Shell (6h)
- [ ] Create `/admin` layout with sidebar
- [ ] Implement Keycloak role protection
- [ ] Create HealthGauge, MetricBar components
- [ ] Build health dashboard page

### Phase 3: Consumer & Parameter Management (8h)
- [ ] Consumer list page
- [ ] Consumer detail page with trajectory chart
- [ ] Parameter override modal
- [ ] Lock/unlock functionality

### Phase 4: Anomaly Management (4h)
- [ ] Anomaly timeline page
- [ ] Anomaly detail view
- [ ] Acknowledge/resolve actions

### Phase 5: User-Facing UX (4h)
- [ ] LearningIndicator component
- [ ] FeedbackImpactToast component
- [ ] `/plasticity/user-summary` endpoint
- [ ] Integration in chat UI

### Phase 6: Grafana Dashboard (4h)
- [ ] Complete plasticity_system.json dashboard
- [ ] Alert rules for anomalies
- [ ] Integration with existing monitoring

---

## 8. Database Schema Additions

```sql
-- Add manual override tracking
ALTER TABLE plasticity_adjustments 
ADD COLUMN is_manual BOOLEAN DEFAULT FALSE,
ADD COLUMN override_reason TEXT,
ADD COLUMN overridden_by VARCHAR(100);

-- Add parameter locking
CREATE TABLE plasticity_parameter_locks (
    consumer_name VARCHAR(100) NOT NULL,
    parameter_name VARCHAR(100) NOT NULL,
    locked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    locked_by VARCHAR(100) NOT NULL,
    reason TEXT,
    PRIMARY KEY (consumer_name, parameter_name)
);

-- Add anomaly acknowledgment
CREATE TABLE plasticity_anomaly_actions (
    id SERIAL PRIMARY KEY,
    anomaly_id VARCHAR(200) NOT NULL,
    action VARCHAR(50) NOT NULL,  -- 'acknowledge', 'resolve', 'ignore'
    action_by VARCHAR(100) NOT NULL,
    action_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT
);

-- Index for admin queries
CREATE INDEX idx_adjustments_manual ON plasticity_adjustments(is_manual) WHERE is_manual = TRUE;
```

---

## 9. Security Considerations

1. **Role-Based Access**: Only users with `admin` or `vitruvyan-admin` Keycloak role can access `/admin/*`
2. **Audit Trail**: All manual overrides logged with user ID and reason
3. **Rate Limiting**: Admin API endpoints should have stricter rate limits
4. **Parameter Bounds**: Even manual overrides must respect bounds (server-side validation)
5. **Sensitive Data**: No PII exposed in plasticity logs

---

## 10. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Admin UI Load Time | <2s | Performance monitoring |
| Anomaly Detection Accuracy | >90% | Manual review |
| Override Success Rate | >99% | API logs |
| Time to Acknowledge Anomaly | <1h | MTTA tracking |
| User Learning Indicator Engagement | >20% click-through | Analytics |

---

## 11. References

- PlasticityObserver: `core/cognitive_bus/plasticity/observer.py`
- PlasticityManager: `core/cognitive_bus/plasticity/manager.py`
- Existing Metrics: `core/cognitive_bus/plasticity/metrics.py`
- Keycloak Config: `docker/services/keycloak/`
- Grafana Dashboards: `monitoring/grafana/dashboards/`

---

**Document Status**: APPROVED FOR FUTURE IMPLEMENTATION  
**Estimated Start**: Q2 2026 (Post-MVP)  
**Owner**: TBD
