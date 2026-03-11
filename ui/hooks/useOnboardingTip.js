// hooks/useOnboardingTip.js
// Dismissable onboarding tips — shows tooltip N times then auto-hides
// Last updated: Mar 11, 2026
'use client'

import { useState, useEffect, useCallback } from 'react'

const STORAGE_PREFIX = 'vit_tip_'

/**
 * useOnboardingTip — shows an educational tooltip for up to `maxViews` times,
 * then permanently dismisses it. Uses localStorage for persistence.
 *
 * @param {string} tipId - Unique identifier for the tip (e.g. 'feedback_thumbs')
 * @param {number} maxViews - Number of times to show before auto-dismiss (default: 15)
 * @returns {{ shouldShow: boolean, dismiss: () => void }}
 */
export function useOnboardingTip(tipId, maxViews = 15) {
  const key = `${STORAGE_PREFIX}${tipId}`
  const [shouldShow, setShouldShow] = useState(false)

  useEffect(() => {
    try {
      const raw = localStorage.getItem(key)
      const count = raw ? parseInt(raw, 10) : 0
      if (count < maxViews) {
        setShouldShow(true)
        localStorage.setItem(key, String(count + 1))
      }
    } catch {
      // localStorage unavailable (SSR, private mode) — show tooltip
      setShouldShow(true)
    }
  }, [key, maxViews])

  const dismiss = useCallback(() => {
    setShouldShow(false)
    try {
      localStorage.setItem(key, String(maxViews))
    } catch { /* ignore */ }
  }, [key, maxViews])

  return { shouldShow, dismiss }
}

/**
 * Bilingual tip text — picks EN or IT based on navigator.language.
 *
 * @param {{ en: string, it: string }} texts
 * @returns {string}
 */
export function localizedTip(texts) {
  if (typeof navigator === 'undefined') return texts.en
  const lang = navigator.language?.toLowerCase() || ''
  return lang.startsWith('it') ? texts.it : texts.en
}
