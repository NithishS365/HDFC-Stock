import { format } from 'date-fns'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

export default function PredictionsTable({ predictions, currentPrice }) {
  const getDirectionIcon = (direction) => {
    if (direction === 'UP') return <TrendingUp className="w-4 h-4 text-green-600" />
    if (direction === 'DOWN') return <TrendingDown className="w-4 h-4 text-red-600" />
    return <Minus className="w-4 h-4 text-slate-400" />
  }

  const getDirectionColor = (direction) => {
    if (direction === 'UP') return 'text-green-600 bg-green-50'
    if (direction === 'DOWN') return 'text-red-600 bg-red-50'
    return 'text-slate-600 bg-slate-50'
  }

  const calculateChange = (predicted) => {
    if (!currentPrice) return { value: 0, percent: 0 }
    const value = predicted - currentPrice
    const percent = (value / currentPrice) * 100
    return { value, percent }
  }

  if (!predictions || predictions.length === 0) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">
          Upcoming Predictions
        </h3>
        <p className="text-slate-500 text-center py-8">
          No predictions available yet
        </p>
      </div>
    )
  }

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-slate-900 mb-4">
        Upcoming Predictions (Next 5 Days)
      </h3>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-200">
              <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">
                Date
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">
                Predicted Price
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">
                Confidence Range
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">
                Change
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">
                Direction
              </th>
            </tr>
          </thead>
          <tbody>
            {predictions.map((pred, index) => {
              const change = calculateChange(pred.predicted_price)
              return (
                <tr key={pred.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-3 px-4 text-sm text-slate-900">
                    {format(new Date(pred.target_timestamp), 'MMM dd, yyyy')}
                  </td>
                  <td className="py-3 px-4 text-sm font-semibold text-slate-900">
                    ₹{pred.predicted_price.toFixed(2)}
                  </td>
                  <td className="py-3 px-4 text-sm text-slate-600">
                    {pred.confidence_lower && pred.confidence_upper ? (
                      <span className="font-mono">
                        ₹{pred.confidence_lower.toFixed(2)} - ₹{pred.confidence_upper.toFixed(2)}
                      </span>
                    ) : (
                      <span className="text-slate-400">N/A</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-sm">
                    <span className={change.value >= 0 ? 'text-green-600' : 'text-red-600'}>
                      {change.value >= 0 ? '+' : ''}₹{change.value.toFixed(2)}
                      {' '}({change.percent >= 0 ? '+' : ''}{change.percent.toFixed(2)}%)
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${
                      getDirectionColor(pred.predicted_direction)
                    }`}>
                      {getDirectionIcon(pred.predicted_direction)}
                      <span>{pred.predicted_direction || 'N/A'}</span>
                      {pred.direction_probability && (
                        <span className="ml-1 opacity-75">
                          ({(pred.direction_probability * 100).toFixed(0)}%)
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-4 text-xs text-slate-500">
        <p>
          Model: <span className="font-medium">Advanced XGBoost v1.0</span> | 
          Confidence Level: <span className="font-medium">95%</span>
        </p>
      </div>
    </div>
  )
}
