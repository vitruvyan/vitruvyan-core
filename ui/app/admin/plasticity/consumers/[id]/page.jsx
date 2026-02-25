'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Lock, Unlock, TrendingUp, AlertTriangle, RefreshCw } from 'lucide-react'
import AdminSidebar from '../../../../../components/admin/AdminSidebar'
import MetricBar from '../../../../../components/admin/MetricBar'
import ParameterChart from '../../../../../components/admin/ParameterChart'
import OverrideModal from '../../../../../components/admin/OverrideModal'

export default function ConsumerDetailPage() {
  const params = useParams()
  const router = useRouter()
  const consumerId = params.id

  const [consumerData, setConsumerData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedParameter, setSelectedParameter] = useState(null)
  const [showOverrideModal, setShowOverrideModal] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    fetchConsumerDetail()
  }, [consumerId])

  const fetchConsumerDetail = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/admin/plasticity/consumers/${consumerId}`)
      const data = await response.json()
      setConsumerData(data)
    } catch (error) {
      console.error('Failed to fetch consumer detail:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchConsumerDetail()
    setTimeout(() => setRefreshing(false), 500)
  }

  const handleToggleLock = async (parameterName) => {
    try {
      const response = await fetch(`/api/admin/plasticity/parameters/${consumerId}/${parameterName}/lock`, {
        method: 'POST'
      })
      const result = await response.json()
      if (result.success) {
        await fetchConsumerDetail() // Refresh data
      }
    } catch (error) {
      console.error('Failed to toggle lock:', error)
    }
  }

  const handleOverride = (parameter) => {
    setSelectedParameter(parameter)
    setShowOverrideModal(true)
  }

  const handleOverrideSubmit = async (newValue, reason, lock) => {
    try {
      const response = await fetch(`/api/admin/plasticity/parameters/${consumerId}/${selectedParameter.name}/override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: newValue, reason, lock })
      })
      const result = await response.json()
      if (result.success) {
        setShowOverrideModal(false)
        await fetchConsumerDetail() // Refresh data
      }
    } catch (error) {
      console.error('Failed to override parameter:', error)
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <AdminSidebar />
        <div className="flex-1 p-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="h-32 bg-gray-200 rounded mb-4"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  if (!consumerData) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <AdminSidebar />
        <div className="flex-1 p-8">
          <div className="text-center py-12">
            <AlertTriangle className="mx-auto h-12 w-12 text-orange-500 mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Consumer Not Found</h2>
            <p className="text-gray-600 mb-6">Consumer &quot;{consumerId}&quot; does not exist or is unavailable.</p>
            <button 
              onClick={() => router.push('/admin/plasticity')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <AdminSidebar />
      
      <div className="flex-1 p-8">
        {/* Header */}
        <div className="mb-6">
          <button 
            onClick={() => router.push('/admin/plasticity')}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4 transition-colors"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Health Dashboard
          </button>
          
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{consumerData.name}</h1>
              <p className="text-gray-600 mt-1">Consumer Detail & Parameter Management</p>
            </div>
            
            <button 
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        {/* Health Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Health Score</span>
              <TrendingUp className="h-4 w-4 text-green-600" />
            </div>
            <div className="text-3xl font-bold text-gray-900">{(consumerData.health * 100).toFixed(1)}%</div>
            <MetricBar 
              label="Health" 
              value={consumerData.health} 
              color={consumerData.health >= 0.8 ? 'green' : consumerData.health >= 0.5 ? 'yellow' : 'red'}
            />
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Active Parameters</span>
            </div>
            <div className="text-3xl font-bold text-gray-900">{consumerData.parameters.length}</div>
            <p className="text-sm text-gray-600 mt-2">{consumerData.parameters.filter(p => p.locked).length} locked</p>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Last Adjustment</span>
            </div>
            <div className="text-lg font-semibold text-gray-900">
              {consumerData.last_adjustment 
                ? new Date(consumerData.last_adjustment).toLocaleString() 
                : 'Never'}
            </div>
          </div>
        </div>

        {/* Parameters Table */}
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden mb-8">
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <h2 className="text-lg font-semibold text-gray-900">Parameters</h2>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">Parameter</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">Current Value</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">Bounds</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {consumerData.parameters.map((param, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{param.name}</div>
                      <div className="text-xs text-gray-500">{param.description || 'No description'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-semibold text-gray-900">{param.value.toFixed(3)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-600">
                        [{param.bounds.min.toFixed(2)}, {param.bounds.max.toFixed(2)}]
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {param.locked ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          <Lock className="h-3 w-3 mr-1" />
                          Locked
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          <Unlock className="h-3 w-3 mr-1" />
                          Active
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex space-x-2">
                        <button 
                          onClick={() => handleOverride(param)}
                          className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-xs"
                        >
                          Override
                        </button>
                        <button 
                          onClick={() => handleToggleLock(param.name)}
                          className="px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors text-xs"
                        >
                          {param.locked ? 'Unlock' : 'Lock'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Parameter Trajectories */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Parameter Trajectories (Last 7 Days)</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {consumerData.parameters.slice(0, 4).map((param, idx) => (
              <ParameterChart 
                key={idx}
                parameter={param}
                consumerId={consumerId}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Override Modal */}
      {showOverrideModal && selectedParameter && (
        <OverrideModal
          parameter={selectedParameter}
          onClose={() => setShowOverrideModal(false)}
          onSubmit={handleOverrideSubmit}
        />
      )}
    </div>
  )
}
