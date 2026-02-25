'use client'

import { useState } from 'react'
import { X, AlertTriangle, Lock } from 'lucide-react'

export default function OverrideModal({ parameter, onClose, onSubmit }) {
  const [newValue, setNewValue] = useState(parameter.value)
  const [reason, setReason] = useState('')
  const [lockAfterOverride, setLockAfterOverride] = useState(false)
  const [error, setError] = useState('')

  const handleSliderChange = (e) => {
    const value = parseFloat(e.target.value)
    setNewValue(value)
    setError('')
  }

  const handleInputChange = (e) => {
    const value = parseFloat(e.target.value)
    if (isNaN(value)) {
      setError('Please enter a valid number')
      return
    }
    if (value < parameter.bounds.min || value > parameter.bounds.max) {
      setError(`Value must be between ${parameter.bounds.min} and ${parameter.bounds.max}`)
      return
    }
    setNewValue(value)
    setError('')
  }

  const handleSubmit = () => {
    if (!reason.trim()) {
      setError('Please provide a reason for this override')
      return
    }
    if (newValue < parameter.bounds.min || newValue > parameter.bounds.max) {
      setError(`Value must be within bounds [${parameter.bounds.min}, ${parameter.bounds.max}]`)
      return
    }
    onSubmit(newValue, reason, lockAfterOverride)
  }

  const valueDelta = newValue - parameter.value
  const valueDeltaPercent = ((valueDelta / parameter.value) * 100).toFixed(1)

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Override Parameter</h2>
            <p className="text-sm text-gray-600 mt-1">{parameter.name}</p>
          </div>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          {/* Warning */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex">
            <AlertTriangle className="h-5 w-5 text-yellow-600 mr-3 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-yellow-800">
              <p className="font-medium mb-1">Manual Override</p>
              <p>This will bypass the Plasticity System&apos;s autonomous adaptation. Use with caution.</p>
            </div>
          </div>

          {/* Current Value */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Current Value:</span>
                <span className="font-semibold text-gray-900 ml-2">{parameter.value.toFixed(4)}</span>
              </div>
              <div>
                <span className="text-gray-600">Bounds:</span>
                <span className="font-semibold text-gray-900 ml-2">
                  [{parameter.bounds.min.toFixed(2)}, {parameter.bounds.max.toFixed(2)}]
                </span>
              </div>
            </div>
          </div>

          {/* Slider */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              New Value: <span className="font-semibold text-blue-600">{newValue.toFixed(4)}</span>
            </label>
            <input 
              type="range"
              min={parameter.bounds.min}
              max={parameter.bounds.max}
              step={(parameter.bounds.max - parameter.bounds.min) / 100}
              value={newValue}
              onChange={handleSliderChange}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>{parameter.bounds.min.toFixed(2)}</span>
              <span>{parameter.bounds.max.toFixed(2)}</span>
            </div>
          </div>

          {/* Manual Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Or enter precise value:
            </label>
            <input 
              type="number"
              value={newValue}
              onChange={handleInputChange}
              step="0.0001"
              min={parameter.bounds.min}
              max={parameter.bounds.max}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Preview */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="text-sm space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-700">Change:</span>
                <span className={`font-semibold ${valueDelta >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {valueDelta >= 0 ? '+' : ''}{valueDelta.toFixed(4)} ({valueDeltaPercent}%)
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-700">New Value:</span>
                <span className="font-semibold text-blue-600">{newValue.toFixed(4)}</span>
              </div>
            </div>
          </div>

          {/* Reason */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Reason <span className="text-red-500">*</span>
            </label>
            <textarea 
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explain why you're overriding this parameter..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            />
            <p className="text-xs text-gray-500 mt-1">This will be logged for audit purposes.</p>
          </div>

          {/* Lock Checkbox */}
          <div className="flex items-center">
            <input 
              type="checkbox"
              id="lock-after-override"
              checked={lockAfterOverride}
              onChange={(e) => setLockAfterOverride(e.target.checked)}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="lock-after-override" className="ml-2 text-sm text-gray-700 flex items-center">
              <Lock className="h-4 w-4 mr-1" />
              Lock parameter after override
            </label>
          </div>
          <p className="text-xs text-gray-500 ml-6">Prevents the Plasticity System from adjusting this parameter.</p>

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800">
              {error}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end space-x-3 p-6 border-t border-gray-200 bg-gray-50">
          <button 
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
          >
            Cancel
          </button>
          <button 
            onClick={handleSubmit}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Apply Override
          </button>
        </div>
      </div>
    </div>
  )
}
