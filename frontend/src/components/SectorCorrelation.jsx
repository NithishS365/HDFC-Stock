import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { GitBranch } from 'lucide-react'
import { api } from '../lib/api'
import { format } from 'date-fns'

export default function SectorCorrelation() {
  const [correlation, setCorrelation] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadCorrelation()
  }, [])

  const loadCorrelation = async () => {
    try {
      const data = await api.getSectorCorrelation('HDFCBANK.NS', 90)
      setCorrelation(data)
    } catch (error) {
      console.error('Error loading correlation:', error)
    } finally {
      setLoading(false)
    }
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

  if (!correlation) {
    return null
  }

  const CorrelationBar = ({ label, value, color }) => (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-slate-700">{label}</span>
        <span className="font-semibold text-slate-900">{value.toFixed(3)}</span>
      </div>
      <div className="w-full bg-slate-200 rounded-full h-3">
        <div
          className={`h-3 rounded-full ${color}`}
          style={{ width: `${Math.abs(value) * 100}%` }}
        ></div>
      </div>
      <p className="text-xs text-slate-500 mt-1">
        {Math.abs(value) > 0.7 ? 'Strong' : Math.abs(value) > 0.4 ? 'Moderate' : 'Weak'} 
        {value > 0 ? ' positive' : ' negative'} correlation
      </p>
    </div>
  )

  return (
    <div className="card">
      <div className="flex items-center space-x-2 mb-4">
        <GitBranch className="w-5 h-5 text-primary-600" />
        <h3 className="text-lg font-semibold text-slate-900">
          Sector Correlation & Influence
        </h3>
      </div>

      {/* Current Correlations */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-slate-700 mb-3">Current Correlations</h4>
        
        <CorrelationBar
          label="Nifty Bank Index"
          value={correlation.current.correlation_nifty_bank || 0}
          color="bg-blue-500"
        />
        
        <CorrelationBar
          label="Banking Peers (Avg)"
          value={correlation.current.correlation_banking_peers || 0}
          color="bg-purple-500"
        />
      </div>

      {/* Relative Strength */}
      <div className="bg-slate-50 rounded-lg p-4 mb-4">
        <p className="text-sm text-slate-600 mb-2">Relative Strength vs Sector</p>
        <p className="text-2xl font-bold text-slate-900">
          {correlation.current.relative_strength_sector?.toFixed(4)}
        </p>
        <p className="text-xs text-slate-500 mt-1">
          {correlation.current.relative_strength_sector > correlation.average.relative_strength_sector
            ? 'Outperforming sector average'
            : 'Underperforming sector average'}
        </p>
      </div>

      {/* Average Correlations */}
      <div className="border-t border-slate-200 pt-4">
        <h4 className="text-sm font-semibold text-slate-700 mb-3">
          {correlation.period_days}-Day Averages
        </h4>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-blue-50 rounded-lg p-3">
            <p className="text-xs text-blue-600 mb-1">Nifty Bank</p>
            <p className="text-lg font-semibold text-blue-900">
              {correlation.average.correlation_nifty_bank.toFixed(3)}
            </p>
          </div>
          <div className="bg-purple-50 rounded-lg p-3">
            <p className="text-xs text-purple-600 mb-1">Banking Peers</p>
            <p className="text-lg font-semibold text-purple-900">
              {correlation.average.correlation_banking_peers.toFixed(3)}
            </p>
          </div>
        </div>
      </div>

      {/* Interpretation */}
      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-xs text-blue-800">
          <strong>Interpretation:</strong> Higher correlation (closer to 1.0) indicates HDFC Bank 
          moves in sync with the sector. Lower correlation suggests independent movement patterns.
        </p>
      </div>
    </div>
  )
}
