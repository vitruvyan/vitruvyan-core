// Demo query limiter utilities
const DEMO_LIMIT = 5
const STORAGE_KEY = "vitruvyan_demo_count"

export const getDemoQueryCount = () => {
  if (typeof window === "undefined") return 0
  const count = localStorage.getItem(STORAGE_KEY)
  return count ? Number.parseInt(count, 10) : 0
}

export const incrementDemoCount = () => {
  if (typeof window === "undefined") return 0
  const count = getDemoQueryCount()
  const newCount = count + 1
  localStorage.setItem(STORAGE_KEY, newCount.toString())
  return newCount
}

export const isDemoLimitReached = () => {
  return getDemoQueryCount() >= DEMO_LIMIT
}

export const getRemainingDemoQueries = () => {
  return Math.max(0, DEMO_LIMIT - getDemoQueryCount())
}

export const resetDemoCount = () => {
  if (typeof window === "undefined") return
  localStorage.removeItem(STORAGE_KEY)
}
