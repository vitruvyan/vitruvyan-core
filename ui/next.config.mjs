/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_KEYCLOAK_AUTH_URL: process.env.KEYCLOAK_AUTH_URL,
    NEXT_PUBLIC_KEYCLOAK_CLIENT_ID: process.env.KEYCLOAK_CLIENT_ID,
    NEXT_PUBLIC_KEYCLOAK_REDIRECT_URI: process.env.KEYCLOAK_REDIRECT_URI,
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  // Proxy API requests to avoid CORS issues in development
  async rewrites() {
    return [
      {
        source: '/api/neural-engine',
        destination: 'http://161.97.140.157:8003/neural-engine',
      },
      // Portfolio API is handled locally (app/api/portfolio/...)
      // Other /api/* routes proxy to backend
      {
        source: '/api/:path((?!portfolio).*)*',
        destination: 'http://161.97.140.157:8004/api/:path*',
      },
    ]
  },
}

export default nextConfig
