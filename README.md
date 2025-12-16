# 🏦 HDFC Bank Stock Prediction Platform

A production-grade, full-stack AI-powered stock prediction platform specifically designed for HDFC Bank. Built with React + Vite, FastAPI, and Supabase, featuring advanced time-series forecasting with XGBoost and ARIMA models.

![Platform Status](https://img.shields.io/badge/status-production-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![React](https://img.shields.io/badge/react-18.2-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 🌟 Features

### 📊 **Intelligent Forecasting**
- **Dual-Model Architecture**: Baseline ARIMA + Advanced XGBoost for robust predictions
- **Sector-Aware Analysis**: Incorporates NIFTY Bank index and peer bank correlations
- **30+ Technical Indicators**: RSI, MACD, Bollinger Bands, ATR, and custom features
- **5-Day Forecast Horizon**: Next-day to 5-day ahead predictions with confidence intervals

### 🎨 **Modern Dashboard**
- **Real-time Data Updates**: Live price feeds and prediction updates
- **Interactive Charts**: Overlapping time-series with Recharts visualization
- **Performance Metrics**: RMSE, MAE, MAPE, and directional accuracy tracking
- **Regime Classification**: Market regime detection (trending/ranging/volatile)

### 🔧 **Production-Ready Architecture**
- **Automated Data Pipeline**: Historical bootstrap + continuous ingestion
- **Feature Engineering**: Lag features, rolling statistics, regime encoding
- **Model Versioning**: Track model performance and metadata
- **RESTful API**: FastAPI with auto-generated documentation
- **Real-time Database**: Supabase PostgreSQL with WebSocket support

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ ([Download](https://www.python.org/downloads/))
- Node.js 18+ ([Download](https://nodejs.org/))
- Supabase account ([Sign up](https://supabase.com) - free tier)

### 1. Clone Repository

```bash
git clone https://github.com/NithishS365/HDFC-Stock.git
cd HDFC-Stock
```

### 2. Setup Supabase

1. Create a new Supabase project
2. Run the schema: Copy contents of `supabase/schema.sql` into SQL Editor
3. Get your credentials from Settings → API

### 3. Configure Environment

**Backend** (`backend/.env`):
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:5173
```

**Frontend** (`frontend/.env`):
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_URL=http://localhost:8000/api/v1
```

### 4. Install Dependencies

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 5. Bootstrap Data & Train Models

```bash
cd backend
python -m services.data_ingestion.historical_bootstrap  # ~5 min
python -m services.feature_engineering.feature_engineer  # ~3 min
python -m models.baseline_model  # ~1 min
python -m models.advanced_model  # ~3 min
python -m services.prediction_service  # ~1 min
```

### 6. Launch Application

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
# Server runs on http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# Dashboard runs on http://localhost:5173
```

### 7. Access Dashboard

Open [http://localhost:5173](http://localhost:5173) in your browser! 🎉

## 📁 Project Structure

```
HDFC-Stock/
├── backend/
│   ├── api/
│   │   └── routes/           # API endpoints
│   ├── models/
│   │   ├── baseline_model.py # ARIMA model
│   │   └── advanced_model.py # XGBoost model
│   ├── services/
│   │   ├── data_ingestion/   # Yahoo Finance data fetcher
│   │   ├── feature_engineering/ # Technical indicators
│   │   └── prediction_service.py
│   ├── config/               # Supabase configuration
│   └── main.py              # FastAPI application
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── lib/            # API client & Supabase
│   │   └── App.jsx         # Main application
│   └── index.html
├── supabase/
│   └── schema.sql          # Database schema (7 tables)
└── docker-compose.yml      # Production deployment
```

## 🔌 API Endpoints

### Predictions
- `GET /api/v1/predictions/latest` - Get next 5-day predictions
- `GET /api/v1/predictions/accuracy` - Model accuracy metrics
- `GET /api/v1/predictions/historical` - Historical predictions vs actuals

### Market Data
- `GET /api/v1/market-data/ohlcv` - OHLCV price data
- `GET /api/v1/market-data/latest` - Latest market price

### Analytics
- `GET /api/v1/analytics/technical-indicators` - Technical analysis
- `GET /api/v1/analytics/feature-importance` - XGBoost feature rankings
- `GET /api/v1/analytics/sector-correlation` - Bank sector correlations

**Interactive Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

## 🧠 Model Architecture

### Baseline Model: SARIMAX
- **Configuration**: SARIMAX(2,1,2)×(1,1,1,5)
- **Use Case**: Simple trend forecasting baseline
- **Performance**: RMSE ~52, Directional Accuracy ~52%

### Advanced Model: XGBoost
- **Features**: 36 engineered features (technical + regime + sector)
- **Architecture**: Gradient boosting with sequence windows
- **Performance**: Training R² 0.996, Validation R² 0.25
- **Top Features**: EMA-12, SMA-5, Bollinger Bands, Sector Strength

## 📊 Database Schema

**7 Tables** in Supabase PostgreSQL:
1. `market_data_raw` - OHLCV historical data (~17K records)
2. `features_store` - Engineered features (~2.5K records)
3. `predictions` - Model predictions with confidence intervals
4. `model_metadata` - Training history and performance
5. `pattern_discovery` - Chart patterns and regimes
6. `performance_metrics` - Real-time accuracy tracking
7. `system_logs` - Job execution logs

## 🐳 Docker Deployment

```bash
docker-compose up -d
```

Services:
- Backend API: http://localhost:8000
- Frontend: http://localhost:5173
- Persistent volumes for models and logs

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI 0.104.1
- **ML/AI**: XGBoost 2.0.2, scikit-learn 1.3.2, statsmodels 0.14.0
- **Data**: yfinance 0.2.48+, pandas, numpy
- **Database**: Supabase Python Client 2.9.0

### Frontend
- **Framework**: React 18.2 + Vite 5.0
- **Styling**: Tailwind CSS 3.3
- **Charts**: Recharts 2.10
- **Icons**: Lucide React

### Infrastructure
- **Database**: Supabase (PostgreSQL + Realtime)
- **Deployment**: Docker + Docker Compose
- **CI/CD**: GitHub Actions ready

## 📈 Data Sources

- **Primary**: Yahoo Finance via yfinance
- **Symbols**: HDFCBANK.NS, ICICIBANK.NS, KOTAKBANK.NS, AXISBANK.NS, SBIN.NS
- **Indices**: ^NSEBANK (NIFTY Bank), ^NSEI (NIFTY 50)
- **Frequency**: Daily OHLCV data
- **History**: 10 years of historical data

## 🔄 Continuous Updates

Run the scheduler for automated daily updates:

```bash
cd backend
python -m services.scheduler
```

Schedule:
- **4:00 PM IST**: Fetch latest market data
- **4:15 PM IST**: Generate new features
- **4:30 PM IST**: Create fresh predictions
- **Daily**: Update actual prices in predictions

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/

# API health check
curl http://localhost:8000/api/v1/health/detailed
```

## 📝 Configuration

### Model Hyperparameters

Edit `backend/models/advanced_model.py`:
```python
params = {
    'max_depth': 6,
    'learning_rate': 0.1,
    'n_estimators': 100,
    'objective': 'reg:squarederror'
}
```

### Prediction Horizon

Edit `backend/services/prediction_service.py`:
```python
forecast_days = 5  # Change to 1-30 days
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Data**: Yahoo Finance for market data API
- **Supabase**: For real-time database infrastructure
- **Recharts**: For beautiful React charting components
- **FastAPI**: For the incredible Python web framework

## 📧 Contact

**Nithish S** - [@NithishS365](https://github.com/NithishS365)

Project Link: [https://github.com/NithishS365/HDFC-Stock](https://github.com/NithishS365/HDFC-Stock)

---

⭐ **Star this repo** if you find it useful!

Built with ❤️ for financial market analysis and AI-powered forecasting.
