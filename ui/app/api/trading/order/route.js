// app/api/trading/order/route.js
// Feb 1, 2026 - Trading Order API Route
// Proxy to Shadow Trading API (:8025/shadow/buy or /shadow/sell)
//
// Philosophy: Chat-first trading (accessibile a tutti)
// - Solo Market orders (instant execution)
// - Minimal validation (backend gestisce logica)
// - Keycloak auth check required

import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'

export async function POST(request) {
  try {
    // Extract Keycloak token from cookies
    const cookieStore = cookies()
    const keycloakToken = cookieStore.get('keycloak_token')?.value || 
                         cookieStore.get('access_token')?.value ||
                         request.headers.get('authorization')?.replace('Bearer ', '')
    
    console.log('[Trading API] Token check:', {
      hasCookie: !!cookieStore.get('keycloak_token'),
      hasAccessToken: !!cookieStore.get('access_token'),
      hasAuthHeader: !!request.headers.get('authorization'),
      tokenLength: keycloakToken?.length
    })
    
    if (!keycloakToken) {
      return NextResponse.json(
        { error: 'Unauthorized. Please login with Keycloak.' },
        { status: 401 }
      )
    }

    const { ticker, side, quantity, user_id } = await request.json()

    // Validation
    if (!ticker || !side || !quantity) {
      return NextResponse.json(
        { error: 'Missing required fields: ticker, side, quantity' },
        { status: 400 }
      )
    }

    if (!['buy', 'sell'].includes(side)) {
      return NextResponse.json(
        { error: 'Invalid side. Must be "buy" or "sell"' },
        { status: 400 }
      )
    }

    if (quantity <= 0 || !Number.isInteger(quantity)) {
      return NextResponse.json(
        { error: 'Quantity must be a positive integer' },
        { status: 400 }
      )
    }

    // Shadow Trading API endpoint (external host port :8025, Next.js runs on host not Docker)
    const SHADOW_TRADING_URL = process.env.SHADOW_TRADING_API_URL || 'http://161.97.140.157:8025'
    const endpoint = side === 'buy' ? '/shadow/buy' : '/shadow/sell'

    console.log('[Trading API] Calling Shadow Trading:', {
      url: `${SHADOW_TRADING_URL}${endpoint}`,
      ticker,
      quantity,
      user_id,
      hasToken: !!keycloakToken,
      tokenPreview: keycloakToken?.substring(0, 20) + '...'
    })

    // Forward request to Shadow Trading API with Keycloak token
    const response = await fetch(`${SHADOW_TRADING_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${keycloakToken}`
      },
      body: JSON.stringify({
        ticker,
        quantity,
        user_id: user_id || 'dbaldoni', // Default to dbaldoni (extracted from token in backend)
        order_type: 'market' // MVP: Solo Market orders
      })
    })

    console.log('[Trading API] Shadow Trading response:', {
      status: response.status,
      ok: response.ok
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      console.error('[Trading API] Shadow Trading error:', errorData)
      return NextResponse.json(
        { 
          error: errorData.error || 'Shadow Trading API error',
          details: errorData
        },
        { status: response.status }
      )
    }

    const data = await response.json()

    return NextResponse.json({
      success: true,
      order: data,
      message: `${side === 'buy' ? 'Bought' : 'Sold'} ${quantity} ${ticker}`
    })

  } catch (error) {
    console.error('[Trading API] Error:', error)
    return NextResponse.json(
      { error: 'Internal server error', details: error.message },
      { status: 500 }
    )
  }
}
