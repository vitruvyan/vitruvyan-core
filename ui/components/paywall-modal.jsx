"use client"

import { X, Sparkles, TrendingUp, Shield } from "lucide-react"
import { useRouter } from "next/navigation"

export default function PaywallModal({ isOpen, onClose, queriesUsed = 5 }) {
  const router = useRouter()

  if (!isOpen) return null

  const handleSeePlans = () => {
    router.push("/pricing")
    onClose()
  }

  const handleMaybeLater = () => {
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-lg w-full p-8 animate-in fade-in zoom-in duration-200">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Icon */}
        <div className="flex justify-center mb-6">
          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center">
            <Sparkles className="w-10 h-10 text-gray-900" />
          </div>
        </div>

        {/* Title */}
        <h2 className="font-vollkorn-sc text-3xl font-bold text-center text-gray-900 mb-4">
          You've Experienced the Power of Mercator
        </h2>

        {/* Description */}
        <p className="font-nunito text-center text-gray-600 mb-6">
          You've used <strong>{queriesUsed} demo queries</strong> and seen how Mercator's AI agents analyze stocks.
          Ready to unlock real-time data and manage your actual portfolio?
        </p>

        {/* Benefits */}
        <div className="space-y-3 mb-8">
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
              <TrendingUp className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <div className="font-nunito font-semibold text-gray-900 text-sm">Real-Time Market Data</div>
              <div className="font-nunito text-xs text-gray-600">Live prices, instant analysis</div>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
              <Shield className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <div className="font-nunito font-semibold text-gray-900 text-sm">Full Portfolio Tracking</div>
              <div className="font-nunito text-xs text-gray-600">Monitor all your investments</div>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <div className="font-nunito font-semibold text-gray-900 text-sm">Unlimited Queries</div>
              <div className="font-nunito text-xs text-gray-600">Ask Mercator anything, anytime</div>
            </div>
          </div>
        </div>

        {/* CTAs */}
        <div className="space-y-3">
          <button
            onClick={handleSeePlans}
            className="w-full bg-gray-900 hover:bg-gray-800 text-white font-nunito font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            See Pricing Plans
            <TrendingUp className="h-4 w-4" />
          </button>

          <button
            onClick={handleMaybeLater}
            className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-nunito font-medium py-3 px-6 rounded-lg transition-colors"
          >
            Maybe Later
          </button>
        </div>

        {/* Fine print */}
        <p className="font-nunito text-xs text-center text-gray-500 mt-6">
          14-day free trial • No credit card required • Cancel anytime
        </p>
      </div>
    </div>
  )
}
