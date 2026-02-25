import { NextResponse } from "next/server"

/**
 * Admin Plasticity Health API Route
 * 
 * Proxies requests to vitruvyan_api_graph backend:
 * GET /api/admin/plasticity/health → http://vitruvyan_api_graph:8004/admin/plasticity/health
 * 
 * Phase 2: Admin UI Shell (Jan 27, 2026)
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8004"

export async function GET(request) {
  try {
    // Extract query params (e.g., ?days=7)
    const { searchParams } = new URL(request.url)
    const days = searchParams.get("days") || "7"
    
    // Call backend API
    const response = await fetch(
      `${API_BASE_URL}/admin/plasticity/health?days=${days}`,
      {
        headers: {
          "Content-Type": "application/json",
          // TODO: Add JWT token from request headers (Keycloak integration Phase 3)
          // "Authorization": request.headers.get("authorization") || ""
        }
      }
    )
    
    if (!response.ok) {
      const error = await response.text()
      console.error("Backend API error:", error)
      
      return NextResponse.json(
        { error: "Failed to fetch health data", details: error },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data)
    
  } catch (error) {
    console.error("API route error:", error)
    
    return NextResponse.json(
      { error: "Internal server error", details: error.message },
      { status: 500 }
    )
  }
}
