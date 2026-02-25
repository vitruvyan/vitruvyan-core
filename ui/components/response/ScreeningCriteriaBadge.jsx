// components/response/ScreeningCriteriaBadge.jsx
import React from 'react'

const ScreeningCriteriaBadge = ({ criteriaDescription }) => {
  if (!criteriaDescription) return null

  return (
    <div className="flex items-center justify-center py-3 px-4 bg-gray-50 border border-gray-200 rounded-lg">
      <div className="flex items-center gap-2 text-sm text-gray-700">
        <span className="text-gray-500">📋</span>
        <span className="font-medium">{criteriaDescription}</span>
      </div>
    </div>
  )
}

export default ScreeningCriteriaBadge
