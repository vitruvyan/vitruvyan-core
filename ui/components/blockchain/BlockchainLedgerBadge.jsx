/**
 * BLOCKCHAIN LEDGER BADGE COMPONENT
 * 
 * Displays blockchain registration status for epistemic integrity
 * Shows that analysis has been anchored on Tron blockchain for transparency
 * 
 * @component BlockchainLedgerBadge
 * @created Dec 14, 2025
 * @blockchain Tron Network (Nile Testnet → Mainnet Q1 2026)
 * @purpose Epistemic transparency & immutable audit trail
 * 
 * Features:
 * - Visual indicator of blockchain registration
 * - Tooltip with detailed explanation
 * - Optional TX hash link to block explorer
 * - Compact design for chat interface
 */

'use client'

import { Shield, ExternalLink } from 'lucide-react'
import { DarkTooltip } from '../explainability/tooltips/TooltipLibrary'

/**
 * Get blockchain explorer URL for transaction
 */
function getExplorerUrl(txHash, network = 'nile') {
  if (!txHash) return null
  
  const explorers = {
    nile: 'https://nile.tronscan.org/#/transaction/',
    mainnet: 'https://tronscan.org/#/transaction/'
  }
  
  return `${explorers[network] || explorers.nile}${txHash}`
}

/**
 * Format transaction hash (short version)
 */
function formatTxHash(txHash) {
  if (!txHash || txHash.length < 16) return txHash
  return `${txHash.slice(0, 6)}...${txHash.slice(-6)}`
}

export default function BlockchainLedgerBadge({
  txHash = null,
  batchId = null,
  network = 'nile',
  timestamp = null,
  variant = 'compact', // 'compact' | 'detailed'
  className = ''
}) {
  
  const explorerUrl = getExplorerUrl(txHash, network)
  
  const tooltipContent = (
    <div className="space-y-2">
      <p className="text-sm font-bold text-gray-900">
        🔒 Blockchain-Anchored Analysis
      </p>
      <p className="text-xs text-gray-700 leading-relaxed">
        This analysis has been registered on the <strong>Tron blockchain</strong> for epistemic transparency. 
        All Vitruvyan insights are cryptographically anchored to ensure immutability and auditability.
      </p>
      {txHash && (
        <div className="pt-2 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            <strong>TX Hash:</strong> {formatTxHash(txHash)}
          </p>
          {batchId && (
            <p className="text-xs text-gray-500">
              <strong>Batch ID:</strong> #{batchId}
            </p>
          )}
          {timestamp && (
            <p className="text-xs text-gray-500">
              <strong>Anchored:</strong> {new Date(timestamp).toLocaleString()}
            </p>
          )}
        </div>
      )}
      {explorerUrl && (
        <div className="pt-2 border-t border-gray-200">
          <a 
            href={explorerUrl} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
          >
            View on Tronscan <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      )}
      <div className="pt-2 border-t border-gray-200">
        <p className="text-xs text-gray-400 italic">
          Network: {network === 'nile' ? 'Nile Testnet' : 'Mainnet'} | 
          Cost: ~$0.0000000009 per event
        </p>
      </div>
    </div>
  )

  if (variant === 'detailed') {
    return (
      <DarkTooltip content={tooltipContent}>
        <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-green-200 bg-green-50 hover:bg-green-100 transition-colors cursor-help ${className}`}>
          <Shield className="w-4 h-4 text-green-600" />
          <span className="text-xs font-medium text-green-800">
            Blockchain Verified
          </span>
          {txHash && (
            <span className="text-xs text-green-600 font-mono">
              {formatTxHash(txHash)}
            </span>
          )}
        </div>
      </DarkTooltip>
    )
  }

  // Compact variant (default - for chat interface)
  return (
    <div className="group relative inline-block">
      <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-md border border-green-200 bg-green-50 hover:bg-green-100 transition-colors cursor-help ${className}`}>
        <Shield className="w-3 h-3 text-green-600" />
        <span className="text-xs font-medium text-green-700">
          Blockchain
        </span>
        {txHash && explorerUrl && (
          <a 
            href={explorerUrl} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-green-600 hover:text-green-800"
            onClick={(e) => e.stopPropagation()}
          >
            <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>
      
      {/* Tooltip with z-index 999 to appear above everything */}
      <div className="absolute hidden group-hover:block z-[999] w-80 p-4 bg-white border border-gray-300 rounded-lg shadow-2xl bottom-full right-0 mb-2 pointer-events-none">
        {tooltipContent}
        {/* Arrow pointing down */}
        <div className="absolute top-full right-6 transform -mt-1">
          <div className="border-8 border-transparent border-t-white"></div>
        </div>
      </div>
    </div>
  )
}
