import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Activity } from 'lucide-react'
import { api } from '../lib/api'

export default function TechnicalIndicators() {
  const [indicators, setIndicators] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadIndicators()
  }, [])

  const loadIndicators = async () => {
    try {
      const data = await api.getTechnicalIndicators('HDFCBANK.NS', 30)
      setIndicators(data)
    } catch (error) {
      console.error('Error loading indicators:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="card">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-200 rounded w-1/3 mb-4"></div>
          <div className="h-48 bg-slate-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (!indicators || !indicators.latest_indicators) {
    return null
  }

  const latest = indicators.latest_indicators
  const currentPrice = indicators.current_price

  const getSignalColor = (signal) => {
    if (signal === 'bullish' || signal === 'oversold') return 'text-green-600 bg-green-50'
    if (signal === 'bearish' || signal === 'overbought') return 'text-red-600 bg-red-50'
    return 'text-slate-600 bg-slate-50'
  }

  return (
    <div className="card">
      <div className="flex items-center space-x-2 mb-6">
        <Activity className="w-5 h-5 text-primary-600" />
        <h3 className="text-lg font-semibold text-slate-900">
          Technical Indicators Breakdown
        </h3>
      </div>

      {/* Moving Averages */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-slate-700 mb-3">Moving Averages</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-50 rounded-lg p-3">
            <p className="text-xs text-slate-500 mb-1">SMA 5</p>
            <p className="text-lg font-semibold text-slate-900">₹{latest.sma_5?.toFixed(2)}</p>
            <p className={`text-xs ${currentPrice > latest.sma_5 ? 'text-green-600' : 'text-red-600'}`}>
              {currentPrice > latest.sma_5 ? 'Above' : 'Below'} price
            </p>
          </div>
          <div className="bg-slate-50 rounded-lg p-3">
            <p className="text-xs text-slate-500 mb-1">SMA 20</p>
            <p className="text-lg font-semibold text-slate-900">₹{latest.sma_20?.toFixed(2)}</p>
            <p className={`text-xs ${currentPrice > latest.sma_20 ? 'text-green-600' : 'text-red-600'}`}>
              {currentPrice > latest.sma_20 ? 'Above' : 'Below'} price
            </p>
          </div>
          <div className="bg-slate-50 rounded-lg p-3">
            <p className="text-xs text-slate-500 mb-1">SMA 50</p>
            <p className="text-lg font-semibold text-slate-900">₹{latest.sma_50?.toFixed(2)}</p>
            <p className={`text-xs ${currentPrice > latest.sma_50 ? 'text-green-600' : 'text-red-600'}`}>
              {currentPrice > latest.sma_50 ? 'Above' : 'Below'} price
            </p>
          </div>
          <div className="bg-slate-50 rounded-lg p-3">
            <p className="text-xs text-slate-500 mb-1">EMA 12</p>
            <p className="text-lg font-semibold text-slate-900">₹{latest.ema_12?.toFixed(2)}</p>
          </div>
        </div>
      </div>

      {/* Momentum Indicators */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-slate-700 mb-3">Momentum Indicators</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* RSI */}
          <div className="bg-slate-50 rounded-lg p-4">
            <div className="flex justify-between items-start mb-2">
              <div>
                <p className="text-xs text-slate-500">RSI (14)</p>
                <p className="text-2xl font-bold text-slate-900">{latest.rsi_14?.toFixed(2)}</p>
              </div>
              {indicators.signals?.rsi && (
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  getSignalColor(indicators.signals.rsi)
                }`}>
                  {indicators.signals.rsi}
                </span>
              )}
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2 mt-2">
              <div
                className={`h-2 rounded-full ${
                  latest.rsi_14 > 70 ? 'bg-red-500' : latest.rsi_14 < 30 ? 'bg-green-500' : 'bg-blue-500'
                }`}
                style={{ width: `${latest.rsi_14}%` }}
              ></div>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Overbought &gt;70 | Oversold &lt;30
            </p>
          </div>

          {/* MACD */}
          <div className="bg-slate-50 rounded-lg p-4">
            <div className="flex justify-between items-start mb-2">
              <div>
                <p className="text-xs text-slate-500">MACD</p>
                <p className="text-lg font-bold text-slate-900">{latest.macd?.toFixed(2)}</p>
              </div>
              {indicators.signals?.macd && (
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  getSignalColor(indicators.signals.macd)
                }`}>
                  {indicators.signals.macd}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500">Signal: {latest.macd_signal?.toFixed(2)}</p>
            <p className="text-xs text-slate-500">Histogram: {latest.macd_histogram?.toFixed(2)}</p>
          </div>

          {/* Bollinger Bands */}
          <div className="bg-slate-50 rounded-lg p-4">
            <div className="flex justify-between items-start mb-2">
              <div>
                <p className="text-xs text-slate-500">Bollinger Bands</p>
              </div>
              {indicators.signals?.bollinger && (
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  getSignalColor(indicators.signals.bollinger)
                }`}>
                  {indicators.signals.bollinger}
                </span>
              )}
            </div>
            <div className="space-y-1 text-xs">
              <p className="text-slate-600">Upper: ₹{latest.bollinger_upper?.toFixed(2)}</p>
              <p className="text-slate-900 font-semibold">Middle: ₹{latest.bollinger_middle?.toFixed(2)}</p>
              <p className="text-slate-600">Lower: ₹{latest.bollinger_lower?.toFixed(2)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Signals Summary */}
      <div className="border-t border-slate-200 pt-4">
        <h4 className="text-sm font-semibold text-slate-700 mb-3">Overall Signals</h4>
        <div className="flex flex-wrap gap-2">
          {Object.entries(indicators.signals || {}).map(([indicator, signal]) => (
            <div key={indicator} className="flex items-center space-x-2">
              <span className="text-xs font-medium text-slate-600 uppercase">{indicator}:</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSignalColor(signal)}`}>
                {signal}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
