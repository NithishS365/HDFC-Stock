const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

class APIClient {
  constructor(baseURL) {
    this.baseURL = baseURL
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'API request failed')
      }

      return await response.json()
    } catch (error) {
      console.error(`API Error (${endpoint}):`, error)
      throw error
    }
  }

  // Predictions
  async getLatestPredictions(symbol = 'HDFCBANK.NS', modelName = 'advanced_xgboost') {
    return this.request(`/predictions/latest?symbol=${symbol}&model_name=${modelName}`)
  }

  async getHistoricalPredictions(symbol = 'HDFCBANK.NS', daysBack = 30) {
    return this.request(`/predictions/historical?symbol=${symbol}&days_back=${daysBack}`)
  }

  async getPredictionAccuracy(symbol = 'HDFCBANK.NS', modelName = 'advanced_xgboost', daysBack = 30) {
    return this.request(`/predictions/accuracy?symbol=${symbol}&model_name=${modelName}&days_back=${daysBack}`)
  }

  // Analytics
  async getPatterns(symbol = 'HDFCBANK.NS', daysBack = 30) {
    return this.request(`/analytics/patterns?symbol=${symbol}&days_back=${daysBack}`)
  }

  async getCurrentRegime(symbol = 'HDFCBANK.NS') {
    return this.request(`/analytics/regime?symbol=${symbol}`)
  }

  async getPerformanceMetrics(modelName = 'advanced_xgboost', daysBack = 30) {
    return this.request(`/analytics/performance?model_name=${modelName}&days_back=${daysBack}`)
  }

  async getFeatureImportance(modelName = 'advanced_xgboost', modelVersion = 'v1.0') {
    return this.request(`/analytics/feature-importance?model_name=${modelName}&model_version=${modelVersion}`)
  }

  async getSectorCorrelation(symbol = 'HDFCBANK.NS', daysBack = 90) {
    return this.request(`/analytics/sector-correlation?symbol=${symbol}&days_back=${daysBack}`)
  }

  async getTechnicalIndicators(symbol = 'HDFCBANK.NS', daysBack = 30) {
    return this.request(`/analytics/technical-indicators?symbol=${symbol}&days_back=${daysBack}`)
  }

  // Market Data
  async getOHLCVData(symbol = 'HDFCBANK.NS', daysBack = 30) {
    return this.request(`/market-data/ohlcv?symbol=${symbol}&days_back=${daysBack}`)
  }

  async getLatestPrice(symbol = 'HDFCBANK.NS') {
    return this.request(`/market-data/latest?symbol=${symbol}`)
  }

  // Health
  async getHealth() {
    return this.request('/health')
  }
}

export const api = new APIClient(API_BASE_URL)
