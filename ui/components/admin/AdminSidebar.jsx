"use client"

import { usePathname } from "next/navigation"
import Link from "next/link"
import { 
  Activity, 
  Brain, 
  Shield, 
  Settings, 
  LogOut,
  Home,
  BarChart3
} from "lucide-react"

/**
 * Admin Sidebar Navigation
 * 
 * Sacred Orders admin navigation:
 * - Plasticity System (bounded learning)
 * - Cognitive Bus (event monitoring)
 * - Sacred Orders (service health)
 * 
 * Phase 2: Admin UI Shell (Jan 27, 2026)
 */
export default function AdminSidebar({ userRole }) {
  const pathname = usePathname()
  
  const navItems = [
    {
      section: "Overview",
      items: [
        { href: "/admin/plasticity", label: "Dashboard", icon: Home, active: true }
      ]
    },
    {
      section: "Plasticity",
      items: [
        { href: "/admin/plasticity", label: "Health", icon: Activity },
        { href: "/admin/plasticity/consumers", label: "Consumers", icon: Brain },
        { href: "/admin/plasticity/parameters", label: "Parameters", icon: Settings },
        { href: "/admin/plasticity/anomalies", label: "Anomalies", icon: Shield }
      ]
    },
    {
      section: "System",
      items: [
        { href: "/admin/cognitive-bus", label: "Cognitive Bus", icon: BarChart3, disabled: true },
        { href: "/admin/sacred-orders", label: "Sacred Orders", icon: Shield, disabled: true }
      ]
    }
  ]
  
  return (
    <aside className="flex w-64 flex-col border-r border-slate-800 bg-slate-900">
      {/* Header */}
      <div className="border-b border-slate-800 p-6">
        <h1 className="mb-1 font-mono text-lg font-bold text-cyan-400">
          Vitruvyan Admin
        </h1>
        <p className="font-mono text-xs text-slate-500">
          Role: <span className="text-cyan-500">{userRole}</span>
        </p>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-4">
        {navItems.map((section, idx) => (
          <div key={idx} className="mb-6">
            <h2 className="mb-2 px-3 font-mono text-xs font-semibold uppercase tracking-wider text-slate-500">
              {section.section}
            </h2>
            <ul className="space-y-1">
              {section.items.map((item) => {
                const isActive = pathname === item.href
                const Icon = item.icon
                
                return (
                  <li key={item.href}>
                    <Link
                      href={item.disabled ? "#" : item.href}
                      className={`
                        flex items-center gap-3 rounded-md px-3 py-2 font-mono text-sm transition-colors
                        ${isActive 
                          ? "bg-cyan-500/10 text-cyan-400" 
                          : item.disabled
                          ? "cursor-not-allowed text-slate-600"
                          : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                        }
                      `}
                      onClick={(e) => item.disabled && e.preventDefault()}
                    >
                      <Icon className="h-4 w-4" />
                      {item.label}
                      {item.disabled && (
                        <span className="ml-auto rounded bg-slate-800 px-1.5 py-0.5 text-xs text-slate-600">
                          Soon
                        </span>
                      )}
                    </Link>
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
      </nav>
      
      {/* Footer */}
      <div className="border-t border-slate-800 p-4">
        <Link
          href="/"
          className="flex items-center gap-3 rounded-md px-3 py-2 font-mono text-sm text-slate-400 transition-colors hover:bg-slate-800 hover:text-slate-200"
        >
          <LogOut className="h-4 w-4" />
          Exit Admin
        </Link>
      </div>
    </aside>
  )
}
