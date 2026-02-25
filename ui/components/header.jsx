"use client"
import { forwardRef, useState, useEffect } from "react"
import { usePathname } from 'next/navigation'
import Link from "next/link"
import { useKeycloak } from "@/contexts/KeycloakContext" // ✅ ENABLED (Jan 25, 2026)
import { register } from "@/utils/keycloak"
import { usePortfolioCanvas } from '@/hooks/usePortfolioCanvas'
import PortfolioBanner from './portfolio/PortfolioBanner'

// 🌸 SVG Component del Giglio di Firenze - Rosso Bordeaux
const GiglioSVG = ({ className = "" }) => (
  <svg className={className} viewBox="60 300 200 240" xmlns="http://www.w3.org/2000/svg" fill="currentColor">
    <g>
      <path
        fill="currentColor"
        d="m 183.79238,386.66472 c 5.69276,-7.22638 12.6741,-12.22968 21.84305,-13.45702 14.37471,-1.92417 25.36049,5.47606 27.73993,19.15175 1.74592,10.03442 -3.21497,19.88769 -12.56828,25.03364 -1.65733,0.91183 -3.37091,1.70694 -5.1666,2.31054 -0.5371,0.18057 -1.07387,0.53309 -1.86433,0.0295 1.55077,-2.29835 2.75449,-4.75823 3.3647,-7.48323 1.64987,-7.36771 -1.98978,-13.21918 -8.95196,-14.13701 -4.52283,-0.59623 -8.6454,0.76761 -12.49126,3.05109 -6.37866,3.78732 -10.56462,9.47954 -13.79758,15.99174 -1.73779,3.50044 -3.07481,7.15685 -4.17498,10.89545 -0.37923,1.28882 -1.01954,1.84849 -2.37957,1.79531 -1.94565,-0.0761 -3.89685,-0.005 -5.84567,-0.007 -0.91306,-10e-4 -1.41382,-0.28196 -1.25008,-1.38614 2.0788,-14.01829 5.72885,-27.48122 13.79206,-39.40121 0.5289,-0.78189 1.11299,-1.52645 1.75057,-2.38707 z"
      />
      <path
        fill="currentColor"
        d="m 142.99107,427.99737 c -2.30985,-7.66341 -5.37399,-14.79169 -10.65047,-20.75637 -4.05421,-4.58298 -8.94944,-7.82377 -15.05383,-9.03736 -7.29509,-1.4503 -13.27818,2.44559 -14.11016,9.43504 -0.43134,3.62374 0.83404,6.97761 2.53564,10.14548 0.35705,0.66469 0.76197,1.30365 1.10436,1.88569 -0.2946,0.60245 -0.70327,0.4165 -0.98902,0.31625 -9.535613,-3.34575 -16.630724,-9.18597 -18.362409,-19.62582 -2.530824,-15.25771 7.720112,-27.068 22.196089,-27.38903 11.6257,-0.25783 20.38893,4.97124 27.27994,13.86436 6.51737,8.41089 10.26494,18.11544 12.87004,28.32082 0.99093,3.88201 1.74847,7.81278 2.39543,11.76538 0.45021,2.75057 0.30854,2.91099 -2.5119,2.89513 -1.4763,-0.008 -2.9551,-0.0665 -4.42815,4e-5 -1.26511,0.0572 -2.0438,-0.38334 -2.27556,-1.81961 z"
      />
      <path
        fill="currentColor"
        d="m 160.70276,448.49917 c 2.18281,-0.002 4.19239,0.0713 6.19279,-0.0322 1.53187,-0.0793 2.08475,0.45216 2.0644,2.01401 -0.0505,3.88287 -0.12403,7.77236 0.60745,11.624 1.15496,6.08134 3.80205,11.12755 9.52984,14.11127 0.19495,0.10156 0.33765,0.30338 0.7577,0.69337 -9.82781,3.57925 -15.94047,10.56478 -19.50332,20.27115 -3.40314,-9.73202 -9.61628,-16.66742 -19.25899,-20.11785 0.10787,-0.64039 0.4432,-0.7878 0.74971,-0.95111 6.31825,-3.36628 8.71256,-9.08852 9.5549,-15.78445 0.41404,-3.29132 0.42029,-6.59092 0.32322,-9.88752 -0.0477,-1.62019 0.5963,-2.03137 2.08139,-1.96824 2.2376,0.0952 4.48215,0.0266 6.90091,0.0275 z"
      />
      <path
        fill="currentColor"
        d="m 177.74707,434.61922 c 2.2369,1.56299 3.03413,3.55781 2.44768,5.87179 -0.52594,2.07517 -2.16371,3.39833 -4.62402,3.72281 -0.30814,-0.9272 -0.19021,-1.67427 0.46615,-2.43991 2.07409,-2.41942 4.1195,-4.86484 6.11945,-7.34581 0.87691,-1.08781 1.52703,-1.22851 2.46918,-0.0271 1.89313,2.414 3.88737,4.74985 5.87625,7.08697 0.75867,0.89149 0.91834,1.71976 0.54354,2.89952 -2.11297,6.65067 -3.42204,13.47359 -3.97682,20.42993 -0.0914,1.14537 -0.57134,1.58008 -1.6375,1.57763 -1.41668,-0.003 -2.83339,0.01 -4.25009,0.0177 -0.88566,0.005 -1.39877,-0.28488 -1.48004,-1.31127 -0.1813,-2.28974 -0.48671,-4.56965 -0.77435,-7.00552 z"
      />
      <path
        fill="currentColor"
        d="m 168.81001,401.59508 c -0.1841,-0.20617 -1.55649,-1.83673 -3.04976,-3.62348 -4.26406,-5.10212 -4.94159,-5.85897 -5.3328,-5.95716 -0.31365,-0.0787 -0.62386,0.10275 -1.10625,0.64714 -0.4067,0.45896 -5.35154,6.29121 -6.87505,8.10884 -0.89031,1.06219 -0.92777,1.09586 -1.22143,1.09801 -0.27653,0.002 -0.4618,-0.23117 -0.71353,-0.89809 -0.11412,-0.30237 -1.57832,-4.0358 -3.25377,-8.29651 -5.14768,-13.09066 -5.49828,-14.0656 -6.21872,-17.29273 -0.67518,-3.02435 -0.94899,-5.51808 -0.94937,-8.64636 -3.6e-4,-3.8948 0.49043,-7.29234 1.60382,-11.09989 1.70561,-5.83278 4.0035,-10.10312 14.05138,-26.11277 2.33652,-3.72286 4.28605,-6.80716 4.33229,-6.85402 0.15369,-0.15571 0.67651,0.34771 1.16405,1.12086 0.26483,0.41997 1.55924,2.42787 2.87646,4.46202 6.45222,9.96399 8.70823,13.74992 11.25766,18.89205 2.95599,5.96216 4.36503,10.33089 5.06156,15.6934 0.24053,1.8518 0.24105,5.99138 10e-4,7.94665 -0.56855,4.63103 -1.62473,8.36893 -4.29311,15.19361 -2.33795,5.97956 -6.24224,15.69176 -6.36989,15.84557 -0.22014,0.26524 -0.60599,0.17438 -0.96454,-0.22714 z"
      />
    </g>
  </svg>
)

const CompassIcon = ({ className = "" }) => (
  <svg className={className} viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" fill="none">
    {/* Outer circle with much thicker stroke */}
    <circle cx="50" cy="50" r="40" stroke="currentColor" strokeWidth="10" fill="none" />
    
    {/* Arrow pointing up-right (northeast) inside the circle to indicate upward trend */}
    <path
      d="M 42 58 L 62 38"
      stroke="currentColor"
      strokeWidth="5"
      strokeLinecap="round"
    />
    
    {/* Arrow head pointing up-right */}
    <path
      d="M 62 38 L 57 43 M 62 38 L 57 33"
      stroke="currentColor"
      strokeWidth="5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    
    {/* Small center dot */}
    <circle cx="50" cy="50" r="3" fill="currentColor" />
  </svg>
)

const Header = forwardRef((props, ref) => {
  const pathname = usePathname()
  const { authenticated, loading, userInfo, login, logout } = useKeycloak()
  
  console.log('[Header] Component render - authenticated:', authenticated, 'userInfo:', !!userInfo)
  
  // Extract userId from localStorage (Feb 9, 2026 - Fix userId null issue)
  // Same pattern as usePortfolioCanvas token extraction
  const [userId, setUserId] = useState(null)
  
  console.log('[Header] Current userId state:', userId)
  
  useEffect(() => {
    console.log('[Header] useEffect triggered - authenticated:', authenticated, 'userInfo?.sub:', userInfo?.sub)
    
    if (typeof window !== 'undefined') {
      try {
        const keycloakUserStr = localStorage.getItem('keycloak_user')
        console.log('[Header] localStorage keycloak_user:', keycloakUserStr ? 'exists' : 'null')
        
        if (keycloakUserStr) {
          const keycloakUser = JSON.parse(keycloakUserStr)
          console.log('[Header] Parsed keycloak_user keys:', Object.keys(keycloakUser))
          
          // FIX: localStorage uses "id" field, not "sub" (Feb 9, 2026)
          const extractedUserId = keycloakUser.id || keycloakUser.sub || keycloakUser.userId || null
          setUserId(extractedUserId)
          console.log('[Header] User ID from localStorage:', { 
            userId: extractedUserId, 
            hasToken: !!keycloakUser.token,
            hasId: !!keycloakUser.id,
            hasSub: !!keycloakUser.sub,
            hasUserId: !!keycloakUser.userId
          })
        } else if (authenticated && userInfo?.sub) {
          // Fallback to useKeycloak if localStorage not available
          setUserId(userInfo.sub)
          console.log('[Header] User ID from Keycloak hook:', { userId: userInfo.sub })
        } else {
          setUserId(null)
          console.log('[Header] No user ID available', { authenticated, hasUserInfo: !!userInfo })
        }
      } catch (err) {
        console.error('[Header] Error extracting userId:', err)
        setUserId(null)
      }
    }
  }, [authenticated, userInfo])
  
  const {
    isOpen: isPortfolioOpen,
    portfolioData,
    loading: portfolioLoading,
    error: portfolioError,
    openCanvas,
    closeCanvas
  } = usePortfolioCanvas(userId)

  const handleSignUp = () => {
    if (!loading) {
      register()
    }
  }

  const handleLogin = () => {
    if (!loading) {
      login()
    }
  }

  const handleLogout = () => {
    if (!loading) {
      logout()
    }
  }

  // Navigation links (always visible)
  const publicLinks = [
    { href: '/manifesto', label: 'Manifesto' },
    { href: '/pricing', label: 'Pricing' }
  ]

  // Protected links (only when authenticated)
  const protectedLinks = authenticated ? [
    { href: '/portfolio', label: 'Portfolio' }
  ] : []

  const allNavLinks = [...publicLinks, ...protectedLinks]

  return (
    <header ref={ref} className="sticky top-0 z-30 border-b-2 border-gray-300 bg-white shadow-sm">
      <div className="flex h-16 sm:h-20 items-center justify-between px-3 sm:px-6 lg:px-8 mx-auto max-w-7xl">
        {/* Logo - sinistra */}
        <Link href="/" className="flex items-center gap-3 flex-shrink-0">
          <img 
            src="/mercator_logo.png" 
            alt="Mercator Logo" 
            className="h-10 sm:h-12 w-auto"
          />
        </Link>

        {/* Navigation + Auth - destra con stili più ricchi */}
        <div className="flex items-center gap-4 sm:gap-8">
          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            {allNavLinks.map(link => {
              const isActive = pathname === link.href
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${
                    isActive 
                      ? 'bg-vitruvyan-accent text-white shadow-md' 
                      : 'text-gray-700 hover:bg-gray-100 hover:text-vitruvyan-accent'
                  }`}
                >
                  {link.label}
                </Link>
              )
            })}
          </nav>

          {/* Auth Buttons */}
          <div className="flex items-center gap-3">
          {authenticated && userInfo ? (
            <>
              {/* Avatar Bubble - Clickable to open Portfolio (Feb 9, 2026) */}
              <button
                onClick={openCanvas}
                className="hidden sm:flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-100 border border-gray-300 hover:bg-gray-200 hover:border-gray-400 transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-vitruvyan-accent"
                title="View Portfolio"
              >
                <div className="w-8 h-8 rounded-full bg-vitruvyan-accent flex items-center justify-center text-white font-bold text-sm">
                  {(userInfo.name || userInfo.email || 'U').charAt(0).toUpperCase()}
                </div>
                <span className="text-sm font-medium text-gray-700">
                  {userInfo.name || userInfo.email}
                </span>
              </button>
              <button
                onClick={handleLogout}
                disabled={loading}
                className="rounded-lg border-2 border-gray-400 bg-white px-4 py-2.5 text-sm font-semibold text-gray-700 transition-all hover:bg-gray-50 hover:border-gray-500 focus:outline-none focus:ring-2 focus:ring-vitruvyan-accent focus:ring-offset-2 disabled:opacity-50 shadow-sm"
              >
                {loading ? "Loading..." : "Logout"}
              </button>
            </>
          ) : (
            <>
              <button
                onClick={handleLogin}
                disabled={loading}
                className="hidden sm:inline-flex rounded-lg border-2 border-gray-400 bg-white px-4 py-2.5 text-sm font-semibold text-gray-700 transition-all hover:bg-gray-50 hover:border-gray-500 focus:outline-none focus:ring-2 focus:ring-vitruvyan-accent focus:ring-offset-2 disabled:opacity-50 shadow-sm"
              >
                {loading ? "..." : "Login"}
              </button>
              <button
                onClick={handleSignUp}
                disabled={loading}
                className="rounded-lg bg-vitruvyan-accent px-5 py-2.5 text-sm font-bold text-white transition-all hover:bg-vitruvyan-accent-dark focus:bg-vitruvyan-accent-dark focus:outline-none focus:ring-2 focus:ring-vitruvyan-accent focus:ring-offset-2 disabled:opacity-50 shadow-md hover:shadow-lg"
              >
                {loading ? "..." : "Sign Up"}
              </button>
            </>
          )}
          </div>
        </div>
      </div>
      
      {/* Portfolio Banner Overlay (Feb 9, 2026 - Global UX) */}
      {authenticated && isPortfolioOpen && (
        <div className="fixed inset-0 bg-black/20 z-40 backdrop-blur-sm" onClick={closeCanvas}>
          <div className="absolute top-16 left-0 right-0 z-50" onClick={(e) => e.stopPropagation()}>
            <div className="max-w-7xl mx-auto px-4">
              <PortfolioBanner
                isOpen={isPortfolioOpen}
                onClose={closeCanvas}
                portfolioData={portfolioData}
                loading={portfolioLoading}
                error={portfolioError}
                currentTicker={null}
                onTickerClick={(ticker) => {
                  // Navigate to chat with ticker analysis
                  window.location.href = `/?ticker=${ticker}`
                }}
              />
            </div>
          </div>
        </div>
      )}
    </header>
  )
})

Header.displayName = "Header"
export default Header
