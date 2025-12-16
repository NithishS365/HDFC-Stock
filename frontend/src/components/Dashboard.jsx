import { useState, useEffect } from 'react'
import PriceChart from './charts/PriceChart'
import PredictionsTable from './PredictionsTable'
import PerformanceMetrics from './PerformanceMetrics'
import TechnicalIndicators from './TechnicalIndicators'
import RegimeClassification from './RegimeClassification'
import SectorCorrelation from './SectorCorrelation'
import { api } from '../lib/api'
import { supabase } from '../lib/supabase'
import { RefreshCw } from 'lucide-react'

export default function Dashboard() {
  const [marketData, setMarketData] = useState([])
  const [predictions, setPredictions] = useState([])
  const [currentPrice, setCurrentPrice] = useState(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(new Date())

  useEffect(() => {
    loadData()
    setupRealtimeSubscription()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      // Load market data
      const ohlcvResponse = await api.getOHLCVData('HDFCBANK.NS', 90)
      setMarketData(ohlcvResponse.data)

      // Load predictions
      const predResponse = await api.getLatestPredictions('HDFCBANK.NS', 'advanced_xgboost')
      setPredictions(predResponse.predictions)
      setCurrentPrice(predResponse.current_price)

      setLastUpdate(new Date())
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  const setupRealtimeSubscription = () => {
    // Subscribe to new predictions
    const predictionSubscription = supabase
      .channel('predictions_changes')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'predictions'
        },
        (payload) => {
          console.log('New prediction:', payload.new)
          loadData() // Reload data when new prediction arrives
        }
      )
      .subscribe()

    // Subscribe to market data updates
    const marketDataSubscription = supabase
      .channel('market_data_changes')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'market_data_raw',
          filter: 'symbol=eq.HDFCBANK.NS'
        },
        (payload) => {
          console.log('New market data:', payload.new)
          loadData() // Reload data when new market data arrives
        }
      )
      .subscribe()

    return () => {
      predictionSubscription.unsubscribe()
      marketDataSubscription.unsubscribe()
    }
  }

  if (loading && marketData.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p className="text-slate-600">Loading dashboard...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header with refresh button */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Live Dashboard</h2>
          <p className="text-sm text-slate-500 mt-1">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="btn btn-secondary flex items-center space-x-2"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Main Price Chart */}
      <div className="mb-8">
        <PriceChart
          marketData={marketData}
          predictions={predictions}
          currentPrice={currentPrice}
        />
      </div>

      {/* Predictions Table */}
      <div className="mb-8">
        <PredictionsTable predictions={predictions} currentPrice={currentPrice} />
      </div>

      {/* Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <RegimeClassification />
        <SectorCorrelation />
      </div>

      {/* Technical Indicators */}
      <div className="mb-8">
        <TechnicalIndicators />
      </div>

      {/* Performance Metrics */}
      <div>
        <PerformanceMetrics />
      </div>
    </div>
  )
}
