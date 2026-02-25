"use client"

import { useEffect } from "react"
import "./globals.css"
import Header from "@/components/header"
import Footer from "@/components/footer"
import { Barlow_Condensed } from "next/font/google"
import { TooltipProvider } from "@/contexts/TooltipContext"
import { KeycloakProvider } from "@/contexts/KeycloakContext" // ✅ ENABLED (Jan 25, 2026)

const barlowCondensed = Barlow_Condensed({
  subsets: ["latin"],
  variable: "--font-barlow-condensed",
  weight: ["600"],
})

export default function ClientLayout({ children }) {
  useEffect(() => {
    console.log("[Mercator] MINIMAL Landing + Keycloak SSO - v2025-11-25")
  }, [])

  return (
    <html lang="en" suppressHydrationWarning>
      <head>{/* Inter is loaded via CSS @import */}</head>
      <body className={`${barlowCondensed.variable} bg-gray-50 text-gray-900 flex flex-col min-h-screen antialiased`} suppressHydrationWarning>
        {/* ✅ KeycloakProvider ENABLED (Jan 25, 2026) */}
        <KeycloakProvider>
          <TooltipProvider>
            <Header />
            <div className="flex-1 flex flex-col">{children}</div>
            <Footer />
          </TooltipProvider>
        </KeycloakProvider>
      </body>
    </html>
  )
}
