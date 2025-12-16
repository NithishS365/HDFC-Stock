import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, Activity } from 'lucide-react'
import { api } from '../lib/api'

export default function RegimeClassification() {
  const [regime, setRegime] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadRegime()
  }, [])

  const loadRegime = async () => {
    try {
      const data = await api.getCurrentRegime('HDFCBANK.NS')
      setRegime(data)
    } catch (error) {
      console.error('Error loading regime:', error)
    } finally {
      setLoading(false)
    }
  }

  const getRegimeInfo = (regimeType) => {
    const regimes = {
      'trending_up': {
        icon: TrendingUp,
        color: 'text-green-600',
        bgColor: 'bg-green-50',
        borderColor: 'border-green-200',
        label: 'Uptrend',
        description: 'Strong upward momentum'
      },
      'trending_down': {
        icon: TrendingDown,
        color: 'text-red-600',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-200',
        label: 'Downtrend',
        description: 'Strong downward momentum'
      },
      'high_volatility': {
        icon: Activity,
        color: 'text-orange-600',
        bgColor: 'bg-orange-50',
        borderColor: 'border-orange-200',
        label: 'High Volatility',
        description: 'Increased market uncertainty'
      },
      'ranging': {
        icon: Activity,
        color: 'text-blue-600',
        bgColor: 'bg-blue-50',
        borderColor: 'border-blue-200',
        label: 'Ranging',
        description: 'Sideways movement'
      }
    }
    return regimes[regimeType] || regimes['ranging']
  }

  if (loading) {
    return (
      <div className="card">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-200 rounded w-1/2 mb-4"></div>
          <div className="h-32 bg-slate-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (!regime) {
    return null
  }

  const currentRegimeInfo = getRegimeInfo(regime.current_regime)
  const RegimeIcon = currentRegimeInfo.icon

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-slate-900 mb-4">
        Market Regime Classification
      </h3>

      {/* Current Regime */}
      <div className={`${currentRegimeInfo.bgColor} ${currentRegimeInfo.borderColor} border rounded-lg p-4 mb-4`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${currentRegimeInfo.color} bg-white`}>
              <RegimeIcon className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-slate-600">Current Regime</p>
              <p className={`text-xl font-bold ${currentRegimeInfo.color}`}>
                {currentRegimeInfo.label}
              </p>
            </div>
          </div>
        </div>
        <p className="text-sm text-slate-700">
          {currentRegimeInfo.description}
        </p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-slate-50 rounded-lg p-3">
          <p className="text-xs text-slate-500 mb-1">Trend Strength</p>
          <p className="text-lg font-semibold text-slate-900">
            {(regime.trend_strength * 100).toFixed(1)}%
          </p>
          <div className="w-full bg-slate-200 rounded-full h-2 mt-2">
            <div
              className="bg-primary-600 h-2 rounded-full"
              style={{ width: `${Math.min(regime.trend_strength * 100, 100)}%` }}
            ></div>
          </div>
        </div>
        <div className="bg-slate-50 rounded-lg p-3">
          <p className="text-xs text-slate-500 mb-1">Volatility (20d)</p>
          <p className="text-lg font-semibold text-slate-900">
            {(regime.volatility * 100).toFixed(2)}%
          </p>
        </div>
      </div>

      {/* Historical Distribution */}
      <div className="border-t border-slate-200 pt-4">
        <h4 className="text-sm font-semibold text-slate-700 mb-3">
          30-Day Regime Distribution
        </h4>
        <div className="space-y-2">
          {Object.entries(regime.regime_distribution_30d || {}).map(([regimeType, count]) => {
            const info = getRegimeInfo(regimeType)
            const percentage = (count / Object.values(regime.regime_distribution_30d).reduce((a, b) => a + b, 0)) * 100
            
            return (
              <div key={regimeType}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-700">{info.label}</span>
                  <span className="text-slate-500">{count} days ({percentage.toFixed(0)}%)</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${info.color === 'text-green-600' ? 'bg-green-500' : 
                      info.color === 'text-red-600' ? 'bg-red-500' :
                      info.color === 'text-orange-600' ? 'bg-orange-500' : 'bg-blue-500'}`}
                    style={{ width: `${percentage}%` }}
                  ></div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <p className="text-xs text-slate-500 mt-4">
        Updated: {new Date(regime.as_of).toLocaleString()}
      </p>
    </div>
  )
}
