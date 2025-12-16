# 🚀 Quick Start Guide - HDFC Stock Prediction Platform

This guide will help you set up and run the entire platform in under 30 minutes.

## ✅ Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Python 3.11+** installed ([Download](https://www.python.org/downloads/))
- [ ] **Node.js 18+** and npm installed ([Download](https://nodejs.org/))
- [ ] **Supabase account** (free tier) ([Sign up](https://supabase.com))
- [ ] **Git** installed ([Download](https://git-scm.com/))
- [ ] Code editor (VS Code recommended)

## 📋 Step-by-Step Setup

### Step 1: Create Supabase Project (5 minutes)

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Wait for project to be ready (~2 minutes)
3. Go to **SQL Editor** in the left sidebar
4. Open the file `supabase/schema.sql` from this repository
5. Copy the entire contents and paste into the SQL Editor
6. Click **Run** to execute the schema
7. Go to **Settings** → **API** and copy:
   - `Project URL` (your SUPABASE_URL)
   - `anon public` key (your SUPABASE_ANON_KEY)
   - `service_role` key (your SUPABASE_SERVICE_KEY) - **Keep this secret!**

### Step 2: Configure Environment Variables (2 minutes)

#### Backend Configuration

Create `backend/.env`:

```bash
# Navigate to backend directory
cd backend

# Copy example file
cp ../.env.example .env
```

Edit `backend/.env` and add your Supabase credentials:

```env
# Supabase Configuration
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Backend Configuration
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:5173
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

#### Frontend Configuration

Create `frontend/.env`:

```bash
cd ../frontend
cp .env.example .env
```

Edit `frontend/.env`:

```env
VITE_SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
VITE_API_URL=http://localhost:8000/api/v1
```

### Step 3: Install Dependencies (5 minutes)

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

#### Frontend

```bash
cd ../frontend

# Install Node packages
npm install
```

### Step 4: Bootstrap Data & Train Models (10-15 minutes)

This is the most important step! Run these commands in order:

```bash
cd backend


# 1. Fetch 10 years of historical data (~5 minutes)
python -m services.data_ingestion.historical_bootstrap

# 2. Engineer features from raw data (~3 minutes)
python -m services.feature_engineering.feature_engineer

# 3. Train baseline ARIMA model (~1 minute)
python -m models.baseline_model

# 4. Train advanced XGBoost model (~3 minutes)
python -m models.advanced_model

# 5. Generate initial predictions (~1 minute)
python -m services.prediction_service
```

**What to expect:**
- Step 1: Fetches ~2,500 records per symbol (7 symbols)
- Step 2: Creates 30+ technical indicators
- Step 3-4: Trains models and saves them to `models/saved_models/`
- Step 5: Creates predictions for next 5 days

### Step 5: Start the Application (2 minutes)

Open **TWO terminal windows**:

#### Terminal 1: Backend

```bash
cd backend

# Activate venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Start FastAPI server
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### Terminal 2: Frontend

```bash
cd frontend

# Start React dev server
npm run dev
```

You should see:
```
  VITE v5.0.8  ready in 1234 ms

  ➜  Local:   http://localhost:5173/
```

### Step 6: Open the Dashboard! 🎉

Open your browser and go to: **http://localhost:5173**

You should see:
- ✅ Live price chart with predictions
- ✅ Predictions table with confidence intervals
- ✅ Performance metrics
- ✅ Technical indicators
- ✅ Market regime classification
- ✅ Sector correlation analysis

## 🔄 Keeping Data Fresh

To continuously update data and predictions, run the scheduler:

```bash
cd backend

# In a third terminal
python -m services.scheduler
```

This will:
- Fetch new market data daily at 4 PM IST
- Update features automatically
- Generate fresh predictions
- Update actual outcomes

## 🧪 Testing the API

Visit the interactive API docs: **http://localhost:8000/docs**

Try these endpoints:
- `GET /api/v1/predictions/latest` - Get latest predictions
- `GET /api/v1/analytics/technical-indicators` - Technical indicators
- `GET /api/v1/market-data/ohlcv?days_back=30` - Price history

## 🐛 Troubleshooting

### "Module not found" errors

```bash
# Make sure you're in the backend directory with venv activated
cd backend
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend shows "Backend Connection Failed"

1. Verify backend is running on port 8000
2. Check `frontend/.env` has correct `VITE_API_URL`
3. Open http://localhost:8000/api/v1/health in browser
4. Should return: `{"status": "healthy"}`

### No predictions showing

1. Make sure you ran all bootstrap steps
2. Check Supabase dashboard → Table Editor → `predictions` table
3. Verify environment variables are correct

### Supabase connection errors

1. Double-check your `.env` files
2. Verify Supabase project is active (check dashboard)
3. Test connection: 
   ```python
   from config.supabase_config import get_supabase_client
   client = get_supabase_client()
   print(client.table('market_data_raw').select('*').limit(1).execute())
   ```

### Python version issues

```bash
# Check Python version
python --version

# If < 3.11, install Python 3.11+
# Then create new venv:
python3.11 -m venv venv
```

## 📊 Verifying Everything Works

### Backend Health Check

```bash
curl http://localhost:8000/api/v1/health/detailed
```

Should return:
```json
{
  "status": "healthy",
  "components": {
    "database": {"status": "healthy"},
    "models": {"status": "healthy"}
  }
}
```

### Check Data in Supabase

Go to Supabase Dashboard → Table Editor:

1. **market_data_raw**: Should have ~17,500 rows
2. **features_store**: Should have ~2,500 rows for HDFCBANK.NS
3. **predictions**: Should have 5 rows (next 5 days)
4. **model_metadata**: Should have 2 rows (baseline + advanced)

### Frontend Real-time Updates

1. Open browser DevTools (F12)
2. Go to Console tab
3. You should see WebSocket connection messages
4. Any new predictions will trigger: "New prediction: ..."

## 🎯 Next Steps

Now that everything is running:

1. **Explore the Dashboard**: Navigate through all sections
2. **Check API Docs**: http://localhost:8000/docs
3. **Monitor Logs**: Check `backend/logs/` for detailed execution logs
4. **Schedule Jobs**: Set up the scheduler for continuous updates
5. **Customize Models**: Experiment with different hyperparameters

## 💡 Pro Tips

### Run in Background (Production)

Use Docker Compose for production:

```bash
# Build and start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop
docker-compose down
```

### Daily Data Updates

Set up a cron job (Linux/Mac) or Task Scheduler (Windows):

```bash
# Example cron (daily at 4:30 PM IST)
30 16 * * * cd /path/to/backend && /path/to/venv/bin/python -m services.scheduler
```

### Monitor Performance

Watch real-time accuracy metrics in the dashboard's **Performance Metrics** section.

## 📚 Additional Resources

- [Full Documentation](README.md)
- [API Reference](http://localhost:8000/docs)
- [Supabase Docs](https://supabase.com/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)

## 🆘 Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#-troubleshooting) section above
2. Review logs in `backend/logs/`
3. Open an issue on GitHub
4. Check Supabase dashboard for errors

## ✨ Success!

If you can see the dashboard with live predictions, congratulations! 🎉

You now have a production-grade stock prediction platform running locally.

---

**Time to complete**: ~30 minutes  
**Difficulty**: Intermediate  
**Next**: Explore model customization and deployment options
