import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import Header from './components/Header'
import { api } from './lib/api'

function App() {
  const [isHealthy, setIsHealthy] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    checkHealth()
  }, [])

  const checkHealth = async () => {
    try {
      await api.getHealth()
      setIsHealthy(true)
    } catch (error) {
      console.error('Health check failed:', error)
      setIsHealthy(false)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isHealthy) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="card max-w-md">
          <h2 className="text-xl font-semibold text-red-600 mb-2">Backend Connection Failed</h2>
          <p className="text-slate-600 mb-4">
            Unable to connect to the API server. Please ensure the backend is running.
          </p>
          <button onClick={checkHealth} className="btn btn-primary">
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      <Dashboard />
    </div>
  )
}

export default App
