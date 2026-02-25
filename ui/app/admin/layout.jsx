"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useKeycloak } from "@/contexts/KeycloakContext"
import AdminSidebar from "@/components/admin/AdminSidebar"
import { AlertCircle } from "lucide-react"

/**
 * Admin Layout
 * 
 * Protected layout for admin-only pages (Plasticity, Cognitive Bus, Sacred Orders).
 * Requires Keycloak admin role ('admin' or 'vitruvyan-admin').
 * 
 * Phase 2: Admin UI Shell (Jan 27, 2026)
 */
export default function AdminLayout({ children }) {
  const router = useRouter()
  const { authenticated, loading, hasRole, login, userInfo } = useKeycloak()
  const [isAuthorized, setIsAuthorized] = useState(false)

  useEffect(() => {
    if (loading) return

    // Not authenticated - redirect to login
    if (!authenticated) {
      console.log("[AdminLayout] Not authenticated, redirecting to login")
      login() // Trigger Keycloak login
      return
    }

    // Check admin role
    const isAdmin = hasRole("admin") || hasRole("vitruvyan-admin")
    
    // ⚠️ DEV BYPASS: Accept any authenticated user (REMOVE IN PRODUCTION)
    const isDev = process.env.NODE_ENV === 'development' || window.location.port === '3001'
    
    if (!isAdmin && !isDev) {
      console.log("[AdminLayout] User authenticated but not admin")
      setIsAuthorized(false)
      return
    }

    if (isDev && !isAdmin) {
      console.log("[AdminLayout] ⚠️ DEV MODE: Bypassing admin role check")
    }

    console.log("[AdminLayout] Admin access granted")
    setIsAuthorized(true)
  }, [authenticated, loading, hasRole, login])

  // Loading state
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950">
        <div className="text-center">
          <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-cyan-500 border-r-transparent"></div>
          <p className="font-mono text-sm text-slate-400">Verifying admin access...</p>
        </div>
      </div>
    )
  }

  // Unauthorized state
  if (!isAuthorized) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950">
        <div className="max-w-md rounded-lg border border-red-900/50 bg-red-950/20 p-8 text-center">
          <AlertCircle className="mx-auto mb-4 h-12 w-12 text-red-500" />
          <h1 className="mb-2 font-mono text-xl font-bold text-red-400">Access Denied</h1>
          <p className="mb-4 font-mono text-sm text-slate-400">
            You need admin role to access this area.
          </p>
          <p className="font-mono text-xs text-slate-500">
            Contact system administrator for access.
          </p>
          <button
            onClick={() => router.push("/")}
            className="mt-6 rounded-md bg-slate-800 px-4 py-2 font-mono text-sm text-slate-200 hover:bg-slate-700"
          >
            Return to Home
          </button>
        </div>
      </div>
    )
  }

  // Authorized layout
  return (
    <div className="flex h-screen bg-slate-950">
      {/* Sidebar */}
      <AdminSidebar userRole={userInfo?.preferred_username || "admin"} />
      
      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-7xl p-6">
          {children}
        </div>
      </main>
    </div>
  )
}
