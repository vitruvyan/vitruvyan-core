/**
 * BASE CARD COMPONENT
 * Foundation component for all card variants
 * All other cards extend this base pattern
 * 
 * @component BaseCard
 * @created Dec 11, 2025
 * @usage import { BaseCard } from '@/components/cards/CardLibrary'
 */

'use client'
import { tokens } from '../theme/tokens'

export default function BaseCard({ 
  children,
  variant = 'default',  // default | elevated | bordered | flat
  padding = 'md',       // none | sm | md | lg | xl
  className = '',
  onClick,
  hover = false,
  ...props 
}) {
  const variantClass = tokens.cards.variants[variant] || tokens.cards.variants.default
  const paddingClass = tokens.cards.padding[padding] || tokens.cards.padding.md
  const hoverClass = hover ? 'cursor-pointer hover:shadow-md' : ''
  const darkClass = tokens.cards.dark[variant] || tokens.cards.dark.default
  
  return (
    <div 
      className={`${tokens.cards.base} ${variantClass} ${paddingClass} ${hoverClass} ${darkClass} ${className}`}
      onClick={onClick}
      {...props}
    >
      {children}
    </div>
  )
}
