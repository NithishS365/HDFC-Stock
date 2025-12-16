import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Target, TrendingUp, Award } from 'lucide-react'
import { api } from '../lib/api'

export default function PerformanceMetrics() {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadMetrics()
  }, [])

  const loadMetrics = async () => {
    try {
      const accuracy = await api.getPredictionAccuracy('HDFCBANK.NS', 'advanced_xgboost', 30)
      setMetrics(accuracy)
    } catch (error) {
      console.error('Error loading metrics:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="card">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-200 rounded w-1/3 mb-4"></div>
          <div className="h-32 bg-slate-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (!metrics || metrics.sample_size === 0) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">
          Model Performance Metrics
        </h3>
        <div className="text-center py-8">
          <p className="text-slate-600 mb-2">
            No performance data available yet
          </p>
          <p className="text-sm text-slate-500">
            {metrics?.message || "Predictions are available for future dates. Metrics will be calculated once actual outcomes are available."}
          </p>
        </div>
      </div>
    )
  }

  const MetricCard = ({ icon: Icon, label, value, unit, color }) => (
    <div className="bg-slate-50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-slate-600">{label}</span>
        <Icon className={`w-5 h-5 ${color}`} />
      </div>
      <div className="text-2xl font-bold text-slate-900">
        {value}
        <span className="text-sm font-normal text-slate-500 ml-1">{unit}</span>
      </div>
    </div>
  )

  return (
    <div className="card">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 mb-1">
            Model Performance Metrics
          </h3>
          <p className="text-sm text-slate-500">
            Last {metrics.period_days} days • {metrics.sample_size} predictions
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <MetricCard
          icon={Target}
          label="RMSE"
          value={metrics.metrics.rmse?.toFixed(2) || 'N/A'}
          unit="₹"
          color="text-blue-600"
        />
        <MetricCard
          icon={Target}
          label="MAE"
          value={metrics.metrics.mae?.toFixed(2) || 'N/A'}
          unit="₹"
          color="text-purple-600"
        />
        <MetricCard
          icon={TrendingUp}
          label="MAPE"
          value={metrics.metrics.mape?.toFixed(2) || 'N/A'}
          unit="%"
          color="text-orange-600"
        />
        <MetricCard
          icon={Award}
          label="Direction Accuracy"
          value={metrics.metrics.directional_accuracy ? (metrics.metrics.directional_accuracy * 100).toFixed(1) : 'N/A'}
          unit="%"
          color="text-green-600"
        />
      </div>

      <div className="border-t border-slate-200 pt-4">
        <h4 className="text-sm font-semibold text-slate-700 mb-3">
          Error Distribution
        </h4>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-xs text-slate-500 mb-1">Root Mean Square Error</p>
            <p className="text-lg font-semibold text-slate-900">
              ₹{metrics.metrics.rmse.toFixed(2)}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">Mean Absolute Error</p>
            <p className="text-lg font-semibold text-slate-900">
              ₹{metrics.metrics.mae.toFixed(2)}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">Avg Error %</p>
            <p className="text-lg font-semibold text-slate-900">
              {metrics.metrics.mape.toFixed(2)}%
            </p>
          </div>
        </div>
      </div>

      <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
        <p className="text-sm text-green-800">
          <strong>Strong Performance:</strong> The model correctly predicts price direction in{' '}
          <strong>{(metrics.metrics.directional_accuracy * 100).toFixed(1)}%</strong> of cases,
          with an average price error of <strong>₹{metrics.metrics.mae.toFixed(2)}</strong>.
        </p>
      </div>
    </div>
  )
}
