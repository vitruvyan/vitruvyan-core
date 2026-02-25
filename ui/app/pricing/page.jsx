"use client"

import { useState } from "react"
import { Check, Zap, TrendingUp, Shield, Crown, ArrowRight } from "lucide-react"
import { useRouter } from "next/navigation"

export default function PricingPage() {
  const [billingCycle, setBillingCycle] = useState("monthly") // monthly | annual
  const router = useRouter()

  const plans = [
    {
      id: "basic",
      name: "Basic",
      icon: Zap,
      price: { monthly: 49, annual: 490 },
      description: "Perfect for beginners exploring algorithmic trading",
      features: [
        "VEE (Mercator Explainable Engine)",
        "Clear, human-readable explanations",
        "Basic portfolio tracking",
        "5 stock analyses per day",
        "Email support",
        "Mobile app access",
      ],
      limitations: ["No advanced optimization", "Limited risk management", "Standard priority"],
      popular: false,
      color: "blue",
    },
    {
      id: "pro",
      name: "Pro",
      icon: TrendingUp,
      price: { monthly: 149, annual: 1490 },
      description: "For serious traders who want optimization and risk control",
      features: [
        "Everything in Basic",
        "VMLE (Multi-Level Explainability)",
        "Portfolio optimization engine",
        "VARE risk management system",
        "Unlimited stock analyses",
        "Real-time market alerts",
        "Advanced technical indicators",
        "Priority email support",
      ],
      limitations: ["Limited to 3 portfolios", "Standard Sacred Five access"],
      popular: true,
      color: "vitruvyan-accent",
    },
    {
      id: "elite",
      name: "Elite",
      icon: Crown,
      price: { monthly: 299, annual: 2990 },
      description: "Complete Sacred Five system with white-glove support",
      features: [
        "Everything in Pro",
        "Full Sacred Five AI agents",
        "Unlimited portfolios",
        "Custom risk parameters",
        "Dedicated account manager",
        "Priority chat + phone support",
        "Early access to new features",
        "Quarterly strategy review calls",
        "API access for automation",
      ],
      limitations: [],
      popular: false,
      color: "purple",
    },
  ]

  const handleSelectPlan = (planId) => {
    // Redirect to registration with selected plan
    router.push(`/register?plan=${planId}&billing=${billingCycle}`)
  }

  const getColorClasses = (color, type = "bg") => {
    const colorMap = {
      blue: {
        bg: "bg-blue-500",
        bgLight: "bg-blue-50",
        border: "border-blue-500",
        text: "text-blue-600",
        hover: "hover:bg-blue-600",
      },
      "vitruvyan-accent": {
        bg: "bg-vitruvyan-accent",
        bgLight: "bg-vitruvyan-accent/5",
        border: "border-vitruvyan-accent",
        text: "text-vitruvyan-accent",
        hover: "hover:bg-vitruvyan-accent-dark",
      },
      purple: {
        bg: "bg-purple-600",
        bgLight: "bg-purple-50",
        border: "border-purple-600",
        text: "text-purple-600",
        hover: "hover:bg-purple-700",
      },
    }
    return colorMap[color]?.[type] || colorMap.blue[type]
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white py-12 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="font-vollkorn-sc text-4xl font-bold text-gray-900 lg:text-5xl mb-4">
            Choose Your Trading Journey
          </h1>
          <p className="font-nunito text-xl text-gray-600 max-w-3xl mx-auto">
            All plans include Leonardo, your AI trading assistant. Start with demo data, upgrade anytime.
          </p>
        </div>

        {/* Billing Toggle */}
        <div className="flex justify-center mb-12">
          <div className="bg-gray-100 rounded-lg p-1 inline-flex">
            <button
              onClick={() => setBillingCycle("monthly")}
              className={`px-6 py-2 rounded-md font-nunito text-sm font-medium transition-colors ${
                billingCycle === "monthly" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingCycle("annual")}
              className={`px-6 py-2 rounded-md font-nunito text-sm font-medium transition-colors relative ${
                billingCycle === "annual" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Annual
              <span className="absolute -top-2 -right-2 bg-green-500 text-white text-xs px-2 py-0.5 rounded-full">
                Save 17%
              </span>
            </button>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3 lg:gap-6">
          {plans.map((plan) => {
            const PlanIcon = plan.icon
            const price = billingCycle === "monthly" ? plan.price.monthly : plan.price.annual

            return (
              <div
                key={plan.id}
                className={`relative rounded-2xl border-2 bg-white p-8 shadow-sm transition-all hover:shadow-xl ${
                  plan.popular
                    ? `${getColorClasses(plan.color, "border")} ring-4 ring-opacity-10 ${getColorClasses(plan.color, "bgLight")}`
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                {/* Popular Badge */}
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <span
                      className={`inline-flex items-center gap-1 ${getColorClasses(plan.color, "bg")} px-4 py-1 rounded-full text-white text-xs font-semibold shadow-lg`}
                    >
                      <Zap className="h-3 w-3" />
                      MOST POPULAR
                    </span>
                  </div>
                )}

                {/* Icon */}
                <div className="flex justify-center mb-4">
                  <div
                    className={`w-16 h-16 rounded-full ${getColorClasses(plan.color, "bgLight")} flex items-center justify-center`}
                  >
                    <PlanIcon className={`w-8 h-8 ${getColorClasses(plan.color, "text")}`} />
                  </div>
                </div>

                {/* Plan Name */}
                <h3 className="font-ibm-plex-sans text-2xl font-bold text-center text-gray-900 mb-2">{plan.name}</h3>

                {/* Price */}
                <div className="text-center mb-4">
                  <span className="font-vollkorn-sc text-5xl font-bold text-gray-900">${price}</span>
                  <span className="text-gray-600 ml-2">/{billingCycle === "monthly" ? "mo" : "yr"}</span>
                  {billingCycle === "annual" && (
                    <div className="text-sm text-gray-500 mt-1">${(price / 12).toFixed(0)}/mo billed annually</div>
                  )}
                </div>

                {/* Description */}
                <p className="font-nunito text-sm text-gray-600 text-center mb-6 min-h-[3rem]">{plan.description}</p>

                {/* CTA Button */}
                <button
                  onClick={() => handleSelectPlan(plan.id)}
                  className={`w-full ${getColorClasses(plan.color, "bg")} ${getColorClasses(plan.color, "hover")} text-white font-nunito font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2 mb-6`}
                >
                  Get Started
                  <ArrowRight className="h-4 w-4" />
                </button>

                {/* Features */}
                <div className="space-y-3">
                  <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
                    What's included:
                  </div>
                  {plan.features.map((feature, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <Check className={`h-5 w-5 flex-shrink-0 ${getColorClasses(plan.color, "text")} mt-0.5`} />
                      <span className="font-nunito text-sm text-gray-700">{feature}</span>
                    </div>
                  ))}

                  {/* Limitations */}
                  {plan.limitations.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-100">
                      <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                        Not included:
                      </div>
                      {plan.limitations.map((limitation, index) => (
                        <div key={index} className="flex items-start gap-3">
                          <span className="text-gray-400">−</span>
                          <span className="font-nunito text-sm text-gray-400">{limitation}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* FAQ / Additional Info */}
        <div className="mt-16 text-center">
          <div className="bg-gray-50 rounded-2xl p-8 max-w-4xl mx-auto">
            <h3 className="font-ibm-plex-sans text-2xl font-semibold text-gray-900 mb-4">
              All Plans Include 14-Day Free Trial
            </h3>
            <p className="font-nunito text-gray-600 mb-6">
              No credit card required to start. Experience Leonardo's AI-powered analysis risk-free. Cancel anytime.
            </p>
            <div className="flex flex-wrap justify-center gap-8 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-green-600" />
                <span>Secure & Encrypted</span>
              </div>
              <div className="flex items-center gap-2">
                <Check className="h-5 w-5 text-green-600" />
                <span>Cancel Anytime</span>
              </div>
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-green-600" />
                <span>Upgrade/Downgrade Anytime</span>
              </div>
            </div>
          </div>
        </div>

        {/* Back to Home */}
        <div className="mt-8 text-center">
          <button
            onClick={() => router.push("/")}
            className="font-nunito text-gray-600 hover:text-vitruvyan-accent transition-colors"
          >
            ← Back to Home
          </button>
        </div>
      </div>
    </div>
  )
}
