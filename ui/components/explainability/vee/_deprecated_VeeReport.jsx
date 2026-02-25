"use client"

import { useState } from "react"
import { ChevronDown, TrendingUp, Wrench, Search } from "lucide-react"
import NeuralEngineUI from "@/components/nodes/NeuralEngineUI"
import FactorRadarChart from "@/components/analytics/charts/FactorRadarChart"
import RiskBreakdownChart from "@/components/analytics/charts/RiskBreakdownChart"
import CandlestickChart from "@/components/analytics/charts/CandlestickChart"
import CompositeScoreGauge from "@/components/analytics/charts/CompositeScoreGauge"

const VEESection = ({ icon: Icon, title, children, defaultOpen = false }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className="mb-4 border border-gray-200 rounded-lg overflow-hidden bg-white shadow-sm hover:shadow-md transition-shadow">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gray-100 rounded-lg">
            <Icon className="h-5 w-5 text-gray-700" />
          </div>
          <h3 className="font-ibm-plex-sans text-base font-semibold text-gray-900">{title}</h3>
        </div>
        <ChevronDown
          className={`h-5 w-5 text-gray-500 transition-transform duration-300 ${isOpen ? "rotate-180" : ""}`}
        />
      </button>

      <div
        className={`transition-all duration-300 ease-in-out ${
          isOpen ? "max-h-[2000px] opacity-100" : "max-h-0 opacity-0"
        } overflow-hidden`}
      >
        <div className="p-4 pt-0 border-t border-gray-100">
          <div className="prose prose-sm max-w-none">{children}</div>
        </div>
      </div>
    </div>
  )
}

const renderMarkdownText = (text) => {
  if (!text || typeof text !== "string") return ""

  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-2 py-0.5 rounded text-sm font-mono">$1</code>')
    .replace(/### (.*?)(\n|$)/g, '<h3 class="text-base font-semibold mt-4 mb-2">$1</h3>')
    .replace(/## (.*?)(\n|$)/g, '<h2 class="text-lg font-semibold mt-4 mb-2">$1</h2>')
    .replace(/# (.*?)(\n|$)/g, '<h1 class="text-xl font-bold mt-4 mb-2">$1</h1>')
    .replace(/\n/g, "<br>")
}

export default function VEEReport({ data }) {
  const [activeTab, setActiveTab] = useState("summary")

  const simple = data?.explainability?.simple || data?.narrative || "No executive summary available."
  const technical = data?.explainability?.technical || "No technical details available."
  const detailed = data?.explainability?.detailed || "No deep analysis available."

  const hasSingleTicker = data?.tickers?.length === 1
  const ticker = data?.tickers?.[0]
  const numericalPanel = data?.numerical_panel
  const finalVerdict = data?.final_verdict
  const gauge = data?.gauge

  const factors = hasSingleTicker ? data?.explainability?.detailed?.ranking?.stocks?.[0]?.factors : null
  const risk = hasSingleTicker ? data?.explainability?.detailed?.ranking?.stocks?.[0]?.risk : null
  const compositeScore = hasSingleTicker && numericalPanel?.[0]?.composite_score

  return (
    <div className="flex-1 bg-white p-6 overflow-y-auto animate-slideUpFadeIn">
      {/* Header */}
      <div className="mb-6">
        <h2 className="font-vollkorn-sc text-3xl font-bold text-gray-900 mb-2">VEE® Analysis Report</h2>
        <p className="text-sm text-gray-600">Vitruvyan Explainability Engine® • Multi-layer Analysis</p>
        {ticker && <p className="text-sm text-gray-900 font-semibold mt-2">Ticker: {ticker}</p>}
      </div>

      {hasSingleTicker && (
        <div className="mb-8 space-y-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Visual Analysis</h3>

          {/* Neural Engine */}
          {numericalPanel && numericalPanel.length > 0 && (
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <NeuralEngineUI numericalPanel={numericalPanel} finalVerdict={finalVerdict} gauge={gauge} />
            </div>
          )}

          {/* Row 1: Radar + Risk */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {factors && <FactorRadarChart factors={factors} explainability={data.explainability} />}

            {risk && <RiskBreakdownChart risk={risk} explainability={data.explainability} />}
          </div>

          {/* Row 2: Candlestick */}
          {ticker && <CandlestickChart ticker={ticker} days={90} explainability={data.explainability} />}

          {/* Row 3: Composite Gauge */}
          {compositeScore !== undefined && <CompositeScoreGauge score={compositeScore} verdict={finalVerdict} />}
        </div>
      )}

      {/* Tabs Navigation */}
      <div className="flex gap-2 mb-6 border-b border-gray-200">
        <button
          onClick={() => setActiveTab("summary")}
          className={`px-4 py-2 font-nunito text-sm font-medium transition-colors relative ${
            activeTab === "summary" ? "text-gray-900 border-b-2 border-gray-900" : "text-gray-500 hover:text-gray-700"
          }`}
        >
          Executive Summary
        </button>
        <button
          onClick={() => setActiveTab("layers")}
          className={`px-4 py-2 font-nunito text-sm font-medium transition-colors relative ${
            activeTab === "layers" ? "text-gray-900 border-b-2 border-gray-900" : "text-gray-500 hover:text-gray-700"
          }`}
        >
          Deep Layers
        </button>
      </div>

      {/* Tab Content */}
      <div className="space-y-4">
        {activeTab === "summary" && (
          <div className="animate-fadeIn">
            {/* Executive Summary - Always Visible */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-gray-100 rounded-lg">
                  <TrendingUp className="h-6 w-6 text-gray-700" />
                </div>
                <div>
                  <h3 className="font-ibm-plex-sans text-lg font-semibold text-gray-900">What You Need to Know</h3>
                  <p className="text-xs text-gray-500">Clear, actionable insights</p>
                </div>
              </div>
              <div
                className="font-nunito text-sm leading-relaxed text-gray-700"
                dangerouslySetInnerHTML={{ __html: renderMarkdownText(simple) }}
              />
            </div>
          </div>
        )}

        {activeTab === "layers" && (
          <div className="space-y-4 animate-fadeIn">
            {/* Technical Breakdown */}
            <VEESection icon={Wrench} title="Technical Breakdown" defaultOpen={true}>
              <div
                className="font-nunito text-sm text-gray-700"
                dangerouslySetInnerHTML={{ __html: renderMarkdownText(technical) }}
              />
            </VEESection>

            {/* Deep Dive Analysis */}
            <VEESection icon={Search} title="Deep Dive Analysis">
              <div
                className="font-nunito text-sm text-gray-700"
                dangerouslySetInnerHTML={{ __html: renderMarkdownText(detailed) }}
              />
            </VEESection>
          </div>
        )}
      </div>
    </div>
  )
}
