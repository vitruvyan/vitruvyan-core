// theme/tokens.js - Unified Design Tokens for Vitruvyan UI
// Consolidated from cardTokens.js and existing tokens
// Grammar: Semantic colors for trading signals and UI states

export const tokens = {
  colors: {
    // Semantic Trading Signals
    positive: {
      light: 'bg-green-50',
      base: 'bg-green-100',
      dark: 'bg-green-600',
      text: 'text-green-800'
    },
    negative: {
      light: 'bg-red-50',
      base: 'bg-red-100',
      dark: 'bg-red-600',
      text: 'text-red-800'
    },
    neutral: {
      light: 'bg-gray-50',
      base: 'bg-gray-100',
      dark: 'bg-gray-600',
      text: 'text-gray-800'
    },
    attention: {
      light: 'bg-yellow-50',
      base: 'bg-yellow-100',
      dark: 'bg-yellow-600',
      text: 'text-yellow-800'
    },
    vitruvyan: {
      light: 'bg-emerald-50',
      base: 'bg-emerald-100',
      dark: 'bg-emerald-600',
      text: 'text-emerald-800'
    },
    info: {
      light: 'bg-blue-50',
      base: 'bg-blue-100',
      dark: 'bg-blue-600',
      text: 'text-blue-800'
    },

    // Z-Score Levels (Trading Performance)
    zScore: {
      exceptional: 'text-green-700 bg-green-50 border-green-200',   // z > 1.5
      strong: 'text-green-500 bg-green-50 border-green-200',       // z > 1.0
      aboveAverage: 'text-yellow-500 bg-yellow-50 border-yellow-200', // z > 0.5
      average: 'text-blue-500 bg-blue-50 border-blue-200',          // z > -0.5
      belowAverage: 'text-orange-500 bg-orange-50 border-orange-200', // z > -1.0
      poor: 'text-red-500 bg-red-50 border-red-200',                // z < -1.0
      null: 'text-gray-400 bg-gray-50 border-gray-200'              // null/undefined
    },

    // Metric Colors (General UI)
    metricColors: {
      blue: 'bg-blue-50 border-blue-200 text-blue-900',
      purple: 'bg-purple-50 border-purple-200 text-purple-900',
      green: 'bg-green-50 border-green-200 text-green-900',
      orange: 'bg-orange-50 border-orange-200 text-orange-900',
      red: 'bg-red-50 border-red-200 text-red-900',
      gray: 'bg-gray-50 border-gray-200 text-gray-900',
      yellow: 'bg-yellow-50 border-yellow-200 text-yellow-900',
      indigo: 'bg-indigo-50 border-indigo-200 text-indigo-900'
    },

    // Legacy User/Chat Colors
    user: {
      bg: 'bg-gray-900',
      text: 'text-white'
    }
  },

  // Card Styles (from cardTokens.js)
  cards: {
    base: 'rounded-lg transition-all',
    variants: {
      default: 'bg-white border border-gray-200',
      elevated: 'bg-white border border-gray-200 shadow-sm hover:shadow-md',
      bordered: 'bg-white border-2 border-gray-300',
      flat: 'bg-gray-50 border border-gray-200',
      vitruvyan: 'bg-emerald-50 border border-emerald-200'
    },
    padding: {
      none: '',
      sm: 'p-2',
      md: 'p-3',
      lg: 'p-4',
      xl: 'p-6'
    },
    dark: {
      default: 'dark:bg-gray-800 dark:border-gray-700',
      elevated: 'dark:bg-gray-800 dark:border-gray-700 dark:shadow-gray-900/20',
      bordered: 'dark:bg-gray-800 dark:border-gray-600',
      flat: 'dark:bg-gray-900 dark:border-gray-700',
      vitruvyan: 'dark:bg-emerald-900/30 dark:border-emerald-700'
    }
  },

  typography: {
    narrative: 'text-base leading-relaxed',
    heading: 'text-lg font-semibold',
    caption: 'text-xs text-gray-500',
    mono: 'font-mono text-sm'
  },

  spacing: {
    card: 'p-4',
    section: 'py-3',
    gap: 'gap-3'
  },

  radius: {
    card: 'rounded-lg',
    badge: 'rounded-full',
    button: 'rounded-md'
  }
}