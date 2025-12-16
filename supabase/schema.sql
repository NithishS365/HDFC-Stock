-- =============================================================================
-- HDFC Stock Prediction Platform - Supabase Schema
-- Production-grade database schema with RLS policies
-- =============================================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- =============================================================================
-- 1. RAW MARKET DATA
-- =============================================================================

-- Raw price data for HDFC and related stocks
CREATE TABLE IF NOT EXISTS market_data_raw (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open DECIMAL(12, 4) NOT NULL,
    high DECIMAL(12, 4) NOT NULL,
    low DECIMAL(12, 4) NOT NULL,
    close DECIMAL(12, 4) NOT NULL,
    volume BIGINT NOT NULL,
    adjusted_close DECIMAL(12, 4),
    source VARCHAR(50) DEFAULT 'yfinance',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, timestamp)
);

CREATE INDEX idx_market_data_symbol_timestamp ON market_data_raw(symbol, timestamp DESC);
CREATE INDEX idx_market_data_timestamp ON market_data_raw(timestamp DESC);

-- =============================================================================
-- 2. ENGINEERED FEATURES
-- =============================================================================

-- Feature store with versioning
CREATE TABLE IF NOT EXISTS features_store (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    feature_version VARCHAR(20) NOT NULL DEFAULT 'v1',
    
    -- Technical Indicators
    sma_5 DECIMAL(12, 4),
    sma_20 DECIMAL(12, 4),
    sma_50 DECIMAL(12, 4),
    ema_12 DECIMAL(12, 4),
    ema_26 DECIMAL(12, 4),
    rsi_14 DECIMAL(8, 4),
    macd DECIMAL(12, 4),
    macd_signal DECIMAL(12, 4),
    macd_histogram DECIMAL(12, 4),
    bollinger_upper DECIMAL(12, 4),
    bollinger_middle DECIMAL(12, 4),
    bollinger_lower DECIMAL(12, 4),
    atr_14 DECIMAL(12, 4),
    obv BIGINT,
    
    -- Price-based features
    returns_1d DECIMAL(10, 6),
    returns_5d DECIMAL(10, 6),
    returns_20d DECIMAL(10, 6),
    volatility_20d DECIMAL(10, 6),
    
    -- Volume features
    volume_sma_20 BIGINT,
    volume_ratio DECIMAL(10, 4),
    
    -- Sector correlation features
    correlation_nifty_bank DECIMAL(6, 4),
    correlation_banking_peers DECIMAL(6, 4),
    relative_strength_sector DECIMAL(10, 4),
    
    -- Regime features
    regime_classification VARCHAR(20),
    trend_strength DECIMAL(6, 4),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, timestamp, feature_version)
);

CREATE INDEX idx_features_symbol_timestamp ON features_store(symbol, timestamp DESC);
CREATE INDEX idx_features_version ON features_store(feature_version, timestamp DESC);

-- =============================================================================
-- 3. PREDICTIONS
-- =============================================================================

-- Prediction results with metadata
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    prediction_timestamp TIMESTAMPTZ NOT NULL,
    target_timestamp TIMESTAMPTZ NOT NULL,  -- When this prediction is for
    
    -- Prediction values
    predicted_price DECIMAL(12, 4) NOT NULL,
    confidence_lower DECIMAL(12, 4),
    confidence_upper DECIMAL(12, 4),
    confidence_level DECIMAL(4, 2) DEFAULT 0.95,
    
    -- Prediction metadata
    model_name VARCHAR(50) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    feature_version VARCHAR(20) NOT NULL,
    
    -- Direction prediction
    predicted_direction VARCHAR(10),  -- 'UP', 'DOWN', 'NEUTRAL'
    direction_probability DECIMAL(5, 4),
    
    -- Actual outcome (filled after target_timestamp)
    actual_price DECIMAL(12, 4),
    prediction_error DECIMAL(12, 4),
    direction_correct BOOLEAN,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_predictions_symbol_target ON predictions(symbol, target_timestamp DESC);
CREATE INDEX idx_predictions_symbol_pred ON predictions(symbol, prediction_timestamp DESC);
CREATE INDEX idx_predictions_model ON predictions(model_name, model_version);

-- =============================================================================
-- 4. MODEL METADATA
-- =============================================================================

-- Model training history and performance
CREATE TABLE IF NOT EXISTS model_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(50) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    model_type VARCHAR(50) NOT NULL,  -- 'baseline_arima', 'xgboost', 'lstm', etc.
    
    -- Training metadata
    trained_at TIMESTAMPTZ NOT NULL,
    training_data_start TIMESTAMPTZ NOT NULL,
    training_data_end TIMESTAMPTZ NOT NULL,
    training_samples INTEGER NOT NULL,
    
    -- Hyperparameters (stored as JSONB)
    hyperparameters JSONB,
    
    -- Performance metrics
    train_rmse DECIMAL(12, 6),
    train_mae DECIMAL(12, 6),
    train_r2 DECIMAL(6, 4),
    val_rmse DECIMAL(12, 6),
    val_mae DECIMAL(12, 6),
    val_r2 DECIMAL(6, 4),
    directional_accuracy DECIMAL(5, 4),
    
    -- Feature importance (stored as JSONB)
    feature_importance JSONB,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'archived', 'testing'
    is_production BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(model_name, model_version)
);

CREATE INDEX idx_model_metadata_status ON model_metadata(status, is_production);
CREATE INDEX idx_model_metadata_trained_at ON model_metadata(trained_at DESC);

-- =============================================================================
-- 5. PATTERN DISCOVERY
-- =============================================================================

-- Discovered patterns and regimes
CREATE TABLE IF NOT EXISTS pattern_discovery (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL,
    
    -- Pattern details
    pattern_type VARCHAR(50) NOT NULL,  -- 'head_and_shoulders', 'double_top', 'regime_change', etc.
    pattern_start TIMESTAMPTZ NOT NULL,
    pattern_end TIMESTAMPTZ,
    confidence DECIMAL(5, 4),
    
    -- Pattern metadata
    description TEXT,
    parameters JSONB,
    
    -- Trading implications
    signal VARCHAR(20),  -- 'bullish', 'bearish', 'neutral'
    strength DECIMAL(5, 4),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pattern_symbol_detected ON pattern_discovery(symbol, detected_at DESC);
CREATE INDEX idx_pattern_type ON pattern_discovery(pattern_type);

-- =============================================================================
-- 6. PERFORMANCE TRACKING
-- =============================================================================

-- Real-time performance metrics and paper trading
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    calculated_at TIMESTAMPTZ NOT NULL,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    
    -- Model performance
    model_name VARCHAR(50) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    
    -- Error metrics
    rmse DECIMAL(12, 6),
    mae DECIMAL(12, 6),
    mape DECIMAL(8, 4),
    
    -- Directional accuracy
    total_predictions INTEGER,
    correct_direction INTEGER,
    directional_accuracy DECIMAL(5, 4),
    
    -- Paper trading PnL
    paper_trades INTEGER DEFAULT 0,
    paper_pnl DECIMAL(15, 4) DEFAULT 0,
    win_rate DECIMAL(5, 4),
    sharpe_ratio DECIMAL(8, 4),
    max_drawdown DECIMAL(8, 4),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_performance_model ON performance_metrics(model_name, model_version);
CREATE INDEX idx_performance_calculated_at ON performance_metrics(calculated_at DESC);

-- =============================================================================
-- 7. SYSTEM LOGS
-- =============================================================================

-- Ingestion and prediction job logs
CREATE TABLE IF NOT EXISTS system_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    job_type VARCHAR(50) NOT NULL,  -- 'ingestion', 'feature_engineering', 'prediction', 'training'
    job_id UUID,
    
    status VARCHAR(20) NOT NULL,  -- 'started', 'completed', 'failed'
    message TEXT,
    details JSONB,
    
    execution_time_ms INTEGER,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_system_logs_timestamp ON system_logs(timestamp DESC);
CREATE INDEX idx_system_logs_job_type ON system_logs(job_type, status);

-- =============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE market_data_raw ENABLE ROW LEVEL SECURITY;
ALTER TABLE features_store ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE pattern_discovery ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_logs ENABLE ROW LEVEL SECURITY;

-- Service role (backend) has full access
-- Anon key (frontend) has read-only access

-- Market Data Policies
CREATE POLICY "Service role full access to market_data_raw"
    ON market_data_raw
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Anon read access to market_data_raw"
    ON market_data_raw
    FOR SELECT
    TO anon
    USING (true);

-- Features Store Policies
CREATE POLICY "Service role full access to features_store"
    ON features_store
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Anon read access to features_store"
    ON features_store
    FOR SELECT
    TO anon
    USING (true);

-- Predictions Policies
CREATE POLICY "Service role full access to predictions"
    ON predictions
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Anon read access to predictions"
    ON predictions
    FOR SELECT
    TO anon
    USING (true);

-- Model Metadata Policies
CREATE POLICY "Service role full access to model_metadata"
    ON model_metadata
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Anon read access to model_metadata"
    ON model_metadata
    FOR SELECT
    TO anon
    USING (true);

-- Pattern Discovery Policies
CREATE POLICY "Service role full access to pattern_discovery"
    ON pattern_discovery
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Anon read access to pattern_discovery"
    ON pattern_discovery
    FOR SELECT
    TO anon
    USING (true);

-- Performance Metrics Policies
CREATE POLICY "Service role full access to performance_metrics"
    ON performance_metrics
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Anon read access to performance_metrics"
    ON performance_metrics
    FOR SELECT
    TO anon
    USING (true);

-- System Logs Policies
CREATE POLICY "Service role full access to system_logs"
    ON system_logs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Anon read access to system_logs"
    ON system_logs
    FOR SELECT
    TO anon
    USING (timestamp > NOW() - INTERVAL '7 days');  -- Only recent logs

-- =============================================================================
-- REALTIME SUBSCRIPTIONS
-- =============================================================================

-- Enable realtime for frontend subscriptions
ALTER PUBLICATION supabase_realtime ADD TABLE predictions;
ALTER PUBLICATION supabase_realtime ADD TABLE market_data_raw;
ALTER PUBLICATION supabase_realtime ADD TABLE pattern_discovery;
ALTER PUBLICATION supabase_realtime ADD TABLE performance_metrics;

-- =============================================================================
-- FUNCTIONS AND TRIGGERS
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for predictions table
CREATE TRIGGER update_predictions_updated_at
    BEFORE UPDATE ON predictions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate prediction error when actual price is added
CREATE OR REPLACE FUNCTION calculate_prediction_error()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.actual_price IS NOT NULL AND OLD.actual_price IS NULL THEN
        NEW.prediction_error = NEW.actual_price - NEW.predicted_price;
        NEW.direction_correct = (
            (NEW.predicted_direction = 'UP' AND NEW.actual_price > (SELECT close FROM market_data_raw WHERE symbol = NEW.symbol AND timestamp < NEW.target_timestamp ORDER BY timestamp DESC LIMIT 1))
            OR
            (NEW.predicted_direction = 'DOWN' AND NEW.actual_price < (SELECT close FROM market_data_raw WHERE symbol = NEW.symbol AND timestamp < NEW.target_timestamp ORDER BY timestamp DESC LIMIT 1))
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_prediction_error_trigger
    BEFORE UPDATE ON predictions
    FOR EACH ROW
    EXECUTE FUNCTION calculate_prediction_error();

-- =============================================================================
-- INITIAL DATA / REFERENCE DATA
-- =============================================================================

-- Insert reference symbols
CREATE TABLE IF NOT EXISTS reference_symbols (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,  -- 'primary', 'banking_peer', 'sector_index'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO reference_symbols (symbol, name, category) VALUES
    ('HDFCBANK.NS', 'HDFC Bank Ltd', 'primary'),
    ('ICICIBANK.NS', 'ICICI Bank Ltd', 'banking_peer'),
    ('KOTAKBANK.NS', 'Kotak Mahindra Bank', 'banking_peer'),
    ('AXISBANK.NS', 'Axis Bank Ltd', 'banking_peer'),
    ('SBIN.NS', 'State Bank of India', 'banking_peer'),
    ('^NSEBANK', 'Nifty Bank Index', 'sector_index'),
    ('^NSEI', 'Nifty 50 Index', 'sector_index')
ON CONFLICT (symbol) DO NOTHING;

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Latest predictions view
CREATE OR REPLACE VIEW latest_predictions AS
SELECT DISTINCT ON (symbol, target_timestamp)
    id,
    symbol,
    prediction_timestamp,
    target_timestamp,
    predicted_price,
    confidence_lower,
    confidence_upper,
    model_name,
    model_version,
    predicted_direction,
    direction_probability,
    actual_price,
    prediction_error,
    direction_correct,
    created_at
FROM predictions
ORDER BY symbol, target_timestamp DESC, prediction_timestamp DESC;

-- Latest market data view
CREATE OR REPLACE VIEW latest_market_data AS
SELECT DISTINCT ON (symbol)
    symbol,
    timestamp,
    open,
    high,
    low,
    close,
    volume,
    adjusted_close
FROM market_data_raw
ORDER BY symbol, timestamp DESC;

-- Performance summary view
CREATE OR REPLACE VIEW performance_summary AS
SELECT
    model_name,
    model_version,
    AVG(rmse) as avg_rmse,
    AVG(mae) as avg_mae,
    AVG(directional_accuracy) as avg_directional_accuracy,
    AVG(paper_pnl) as avg_paper_pnl,
    AVG(sharpe_ratio) as avg_sharpe_ratio,
    COUNT(*) as measurement_count
FROM performance_metrics
WHERE calculated_at > NOW() - INTERVAL '30 days'
GROUP BY model_name, model_version;

-- Grant access to views
GRANT SELECT ON latest_predictions TO anon, service_role;
GRANT SELECT ON latest_market_data TO anon, service_role;
GRANT SELECT ON performance_summary TO anon, service_role;

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE market_data_raw IS 'Raw OHLCV data for HDFC Bank and related stocks/indices';
COMMENT ON TABLE features_store IS 'Engineered features with versioning for ML models';
COMMENT ON TABLE predictions IS 'Model predictions with confidence intervals and actual outcomes';
COMMENT ON TABLE model_metadata IS 'Model training history, hyperparameters, and performance metrics';
COMMENT ON TABLE pattern_discovery IS 'Detected chart patterns and regime changes';
COMMENT ON TABLE performance_metrics IS 'Real-time model performance and paper trading results';
COMMENT ON TABLE system_logs IS 'System job execution logs';

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Additional composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_predictions_model_target 
    ON predictions(model_name, model_version, target_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_features_symbol_version_timestamp 
    ON features_store(symbol, feature_version, timestamp DESC);

-- Index for date-based queries (without cast to avoid syntax issues)
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_date 
    ON market_data_raw(symbol, timestamp);

-- Partial indexes for active models
CREATE INDEX IF NOT EXISTS idx_model_metadata_active 
    ON model_metadata(model_name, model_version) 
    WHERE is_production = TRUE;

-- =============================================================================
-- MAINTENANCE
-- =============================================================================

-- Function to cleanup old logs (call periodically)
CREATE OR REPLACE FUNCTION cleanup_old_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM system_logs WHERE timestamp < NOW() - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;

-- Function to archive old predictions
CREATE OR REPLACE FUNCTION archive_old_predictions()
RETURNS void AS $$
BEGIN
    -- Move predictions older than 1 year to archive table
    -- (Archive table creation not shown, but would be similar structure)
    DELETE FROM predictions 
    WHERE target_timestamp < NOW() - INTERVAL '1 year'
    AND actual_price IS NOT NULL;
END;
$$ LANGUAGE plpgsql;
