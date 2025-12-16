import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { format } from 'date-fns'
import { TrendingUp, AlertCircle } from 'lucide-react'

export default function PriceChart({ marketData, predictions, currentPrice }) {
  // Prepare combined data for the chart
  const prepareChartData = () => {
    if (!marketData || marketData.length === 0) return []

    // Convert market data to chart format
    const historicalData = marketData.map(item => ({
      timestamp: new Date(item.timestamp),
      actual: parseFloat(item.close),
      predicted: null,
      lower: null,
      upper: null,
    }))

    // Add predictions
    const predictionData = predictions.map(pred => ({
      timestamp: new Date(pred.target_timestamp),
      actual: pred.actual_price ? parseFloat(pred.actual_price) : null,
      predicted: parseFloat(pred.predicted_price),
      lower: pred.confidence_lower ? parseFloat(pred.confidence_lower) : null,
      upper: pred.confidence_upper ? parseFloat(pred.confidence_upper) : null,
    }))

    // Combine and sort
    const combined = [...historicalData, ...predictionData]
    combined.sort((a, b) => a.timestamp - b.timestamp)

    return combined
  }

  const chartData = prepareChartData()

  // Calculate price change
  const priceChange = currentPrice && marketData.length > 0
    ? currentPrice - parseFloat(marketData[marketData.length - 1].close)
    : 0
  const priceChangePercent = currentPrice && marketData.length > 0
    ? (priceChange / parseFloat(marketData[marketData.length - 1].close)) * 100
    : 0

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 rounded-lg shadow-lg border border-slate-200">
          <p className="font-medium text-slate-900 mb-2">
            {format(new Date(payload[0].payload.timestamp), 'MMM dd, yyyy HH:mm')}
          </p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              <span className="font-medium">{entry.name}:</span> ₹{entry.value?.toFixed(2)}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  return (
    <div className="card">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 mb-1">
            HDFC Bank Stock Price & Predictions
          </h3>
          <p className="text-sm text-slate-500">
            Real-time price with AI-generated forecasts
          </p>
        </div>
        
        {currentPrice && (
          <div className="text-right">
            <div className="text-2xl font-bold text-slate-900">
              ₹{currentPrice.toFixed(2)}
            </div>
            <div className={`flex items-center justify-end space-x-1 text-sm font-medium ${
              priceChange >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              <TrendingUp className={`w-4 h-4 ${priceChange < 0 ? 'rotate-180' : ''}`} />
              <span>
                {priceChange >= 0 ? '+' : ''}₹{priceChange.toFixed(2)} ({priceChangePercent.toFixed(2)}%)
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Chart Legend */}
      <div className="flex flex-wrap gap-4 mb-4 text-sm">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-primary-600 rounded"></div>
          <span className="text-slate-600">Actual Price (Solid)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 border-2 border-orange-500 border-dashed rounded"></div>
          <span className="text-slate-600">Predicted Price (Dashed)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-orange-200 rounded"></div>
          <span className="text-slate-600">95% Confidence Band</span>
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 flex items-start space-x-2">
        <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
        <div className="text-sm text-blue-800">
          <p className="font-medium mb-1">How to Read This Chart</p>
          <p>
            The <strong>solid blue line</strong> shows actual historical prices. 
            The <strong>dashed orange line</strong> represents AI model predictions for future dates.
            The <strong>shaded area</strong> indicates the 95% confidence interval.
          </p>
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={400}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#2563eb" stopOpacity={0.1}/>
              <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f97316" stopOpacity={0.1}/>
              <stop offset="95%" stopColor="#f97316" stopOpacity={0}/>
            </linearGradient>
          </defs>
          
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          
          <XAxis
            dataKey="timestamp"
            tickFormatter={(timestamp) => format(new Date(timestamp), 'MMM dd')}
            stroke="#64748b"
            style={{ fontSize: '12px' }}
          />
          
          <YAxis
            domain={['auto', 'auto']}
            tickFormatter={(value) => `₹${value.toFixed(0)}`}
            stroke="#64748b"
            style={{ fontSize: '12px' }}
          />
          
          <Tooltip content={<CustomTooltip />} />
          
          <Legend />

          {/* Confidence band */}
          <Area
            type="monotone"
            dataKey="upper"
            stroke="none"
            fill="#fed7aa"
            fillOpacity={0.3}
            name="Confidence Upper"
          />
          <Area
            type="monotone"
            dataKey="lower"
            stroke="none"
            fill="#fed7aa"
            fillOpacity={0.3}
            name="Confidence Lower"
          />

          {/* Actual price line */}
          <Line
            type="monotone"
            dataKey="actual"
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
            name="Actual Price"
            connectNulls={false}
          />

          {/* Predicted price line */}
          <Line
            type="monotone"
            dataKey="predicted"
            stroke="#f97316"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={{ fill: '#f97316', r: 4 }}
            name="Predicted Price"
            connectNulls={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
