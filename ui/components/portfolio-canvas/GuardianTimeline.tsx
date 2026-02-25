/**
 * GuardianTimeline - Real-Time Portfolio Guardian Insights Timeline
 * 
 * Task 26.3: Guardian Timeline UI (Jan 26, 2026)
 * 
 * Features:
 * - 3-category tabs: PROTECT (risk_alert), IMPROVE (opportunity), UNDERSTAND (rebalance)
 * - Real-time insight insertion with smooth animations
 * - InsightCard components with VEE explanations
 * - Severity-based visual hierarchy (critical/high/medium/low)
 * - Desktop-optimized layout (min-width 1000px, 2-column grid)
 * - Empty state handling
 * - Automatic scroll to latest insight
 * 
 * Integration:
 * ```tsx
 * import { usePortfolioWebSocket } from '@/hooks/usePortfolioWebSocket'
 * import { GuardianTimeline } from '@/components/portfolio-canvas/GuardianTimeline'
 * 
 * export default function PortfolioCanvasPage() {
 *   const { insights } = usePortfolioWebSocket('user_123')
 *   return <GuardianTimeline insights={insights} />
 * }
 * ```
 */

'use client'

import { useState, useEffect, useRef } from 'react'
import { GuardianInsight } from '@/hooks/usePortfolioWebSocket'
import { InsightCard } from './InsightCard'
import { Shield, TrendingUp, BookOpen } from 'lucide-react'

export interface GuardianTimelineProps {
  insights: GuardianInsight[]
  className?: string
}

type CategoryFilter = 'all' | 'PROTECT' | 'IMPROVE' | 'UNDERSTAND'

interface CategoryTab {
  id: CategoryFilter
  label: string
  icon: React.ComponentType<any>
  description: string
  color: string
  hoverColor: string
  activeColor: string
  activeBg: string
  insightTypes: string[]
}

const CATEGORY_TABS: CategoryTab[] = [
  {
    id: 'all',
    label: 'All Insights',
    icon: Shield,
    description: 'View all Guardian insights',
    color: 'text-gray-600',
    hoverColor: 'hover:text-gray-900',
    activeColor: 'text-indigo-600',
    activeBg: 'bg-indigo-50',
    insightTypes: []
  },
  {
    id: 'PROTECT',
    label: 'Protect',
    icon: Shield,
    description: 'Risk alerts and portfolio protection',
    color: 'text-red-600',
    hoverColor: 'hover:text-red-700',
    activeColor: 'text-red-700',
    activeBg: 'bg-red-50',
    insightTypes: ['risk_alert', 'concentration']
  },
  {
    id: 'IMPROVE',
    label: 'Improve',
    icon: TrendingUp,
    description: 'Growth opportunities and optimization',
    color: 'text-green-600',
    hoverColor: 'hover:text-green-700',
    activeColor: 'text-green-700',
    activeBg: 'bg-green-50',
    insightTypes: ['opportunity']
  },
  {
    id: 'UNDERSTAND',
    label: 'Understand',
    icon: BookOpen,
    description: 'Portfolio rebalancing and correlation insights',
    color: 'text-blue-600',
    hoverColor: 'hover:text-blue-700',
    activeColor: 'text-blue-700',
    activeBg: 'bg-blue-50',
    insightTypes: ['rebalance', 'correlation']
  }
]

export function GuardianTimeline({ insights, className = '' }: GuardianTimelineProps) {
  // ========== State ==========
  const [activeTab, setActiveTab] = useState<CategoryFilter>('all')
  const [animatingInsights, setAnimatingInsights] = useState<Set<number>>(new Set())
  
  // ========== Refs ==========
  const timelineRef = useRef<HTMLDivElement>(null)
  const prevInsightsLengthRef = useRef<number>(0)
  
  // ========== Filter Insights by Category ==========
  const filteredInsights = activeTab === 'all' 
    ? insights 
    : insights.filter(insight => insight.category === activeTab)
  
  // ========== Count Insights per Category ==========
  const insightCounts = {
    all: insights.length,
    PROTECT: insights.filter(i => i.category === 'PROTECT').length,
    IMPROVE: insights.filter(i => i.category === 'IMPROVE').length,
    UNDERSTAND: insights.filter(i => i.category === 'UNDERSTAND').length
  }
  
  // ========== Detect New Insights (Task 26.3.2 - Real-Time Insertion) ==========
  useEffect(() => {
    if (insights.length > prevInsightsLengthRef.current) {
      // New insights added
      const newInsights = insights.slice(0, insights.length - prevInsightsLengthRef.current)
      
      // Trigger animation for new insights
      const newInsightIds = new Set(newInsights.map(i => i.insight_id))
      setAnimatingInsights(newInsightIds)
      
      // Remove animation class after 500ms
      setTimeout(() => {
        setAnimatingInsights(new Set())
      }, 500)
      
      // Scroll to top (newest insight)
      if (timelineRef.current) {
        timelineRef.current.scrollTo({ top: 0, behavior: 'smooth' })
      }
    }
    
    prevInsightsLengthRef.current = insights.length
  }, [insights])
  
  // ========== Empty State ==========
  const renderEmptyState = () => {
    const activeTabData = CATEGORY_TABS.find(tab => tab.id === activeTab)
    const Icon = activeTabData?.icon || Shield
    
    return (
      <div className="flex flex-col items-center justify-center py-20 px-6 text-center">
        <div className={`w-20 h-20 rounded-full ${activeTabData?.activeBg} flex items-center justify-center mb-6`}>
          <Icon className={`w-10 h-10 ${activeTabData?.color}`} />
        </div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          {activeTab === 'all' ? 'No Insights Yet' : `No ${activeTab} Insights`}
        </h3>
        <p className="text-sm text-gray-500 max-w-md">
          {activeTab === 'all' 
            ? 'Guardian is monitoring your portfolio. New insights will appear here as market conditions change.'
            : `No ${activeTab.toLowerCase()} insights at the moment. Guardian will notify you when relevant opportunities or risks are detected.`
          }
        </p>
      </div>
    )
  }
  
  return (
    <div className={`guardian-timeline w-full ${className}`}>
      {/* ========== Category Tabs (Task 26.3.1) ========== */}
      <div className="border-b border-gray-200 bg-white sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-6">
          <nav className="flex space-x-8 py-4" aria-label="Guardian Categories">
            {CATEGORY_TABS.map(tab => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              const count = insightCounts[tab.id as keyof typeof insightCounts]
              
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    group flex items-center space-x-3 pb-3 px-1 border-b-2 transition-all duration-200
                    ${isActive 
                      ? `border-current ${tab.activeColor}` 
                      : `border-transparent ${tab.color} ${tab.hoverColor}`
                    }
                  `}
                  aria-label={tab.description}
                  aria-current={isActive ? 'page' : undefined}
                >
                  {/* Icon */}
                  <Icon 
                    className={`
                      w-5 h-5 transition-transform duration-200
                      ${isActive ? 'scale-110' : 'group-hover:scale-105'}
                    `} 
                  />
                  
                  {/* Label */}
                  <span className="font-medium text-sm">
                    {tab.label}
                  </span>
                  
                  {/* Count Badge */}
                  {count > 0 && (
                    <span 
                      className={`
                        px-2 py-0.5 rounded-full text-xs font-semibold
                        ${isActive 
                          ? `${tab.activeBg} ${tab.activeColor}` 
                          : 'bg-gray-100 text-gray-600'
                        }
                      `}
                    >
                      {count}
                    </span>
                  )}
                </button>
              )
            })}
          </nav>
        </div>
      </div>
      
      {/* ========== Insights Grid (Task 26.3.2 + 26.3.3) ========== */}
      <div 
        ref={timelineRef}
        className="insights-grid max-w-7xl mx-auto px-6 py-6 overflow-y-auto"
        style={{ maxHeight: 'calc(100vh - 200px)' }}
      >
        {filteredInsights.length === 0 ? (
          renderEmptyState()
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredInsights.map(insight => (
              <div
                key={insight.insight_id}
                className={`
                  transition-all duration-500 ease-out
                  ${animatingInsights.has(insight.insight_id) 
                    ? 'animate-slide-in-top opacity-0' 
                    : 'opacity-100'
                  }
                `}
              >
                <InsightCard 
                  insight={insight}
                  isNew={animatingInsights.has(insight.insight_id)}
                />
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* ========== Custom CSS Animations ========== */}
      <style jsx>{`
        @keyframes slideInTop {
          0% {
            transform: translateY(-20px);
            opacity: 0;
          }
          100% {
            transform: translateY(0);
            opacity: 1;
          }
        }
        
        .animate-slide-in-top {
          animation: slideInTop 0.5s ease-out forwards;
        }
      `}</style>
    </div>
  )
}
