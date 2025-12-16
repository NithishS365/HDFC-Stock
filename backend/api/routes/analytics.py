"""
Analytics API Routes
Advanced analytics endpoints for patterns, regimes, and performance
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import pandas as pd
import numpy as np

from config.supabase_config import get_supabase_client

router = APIRouter()


class PatternResponse(BaseModel):
    """Pattern discovery response"""
    id: str
    symbol: str
    detected_at: datetime
    pattern_type: str
    pattern_start: datetime
    pattern_end: Optional[datetime]
    confidence: Optional[float]
    signal: Optional[str]
    strength: Optional[float]
    description: Optional[str]


class PerformanceMetricsResponse(BaseModel):
    """Model performance metrics"""
    model_config = {"protected_namespaces": ()}
    
    model_name: str
    model_version: str
    period_start: datetime
    period_end: datetime
    rmse: Optional[float]
    mae: Optional[float]
    mape: Optional[float]
    directional_accuracy: Optional[float]
    paper_pnl: Optional[float]
    sharpe_ratio: Optional[float]


@router.get("/analytics/patterns", response_model=List[PatternResponse])
async def get_discovered_patterns(
    symbol: str = Query("HDFCBANK.NS"),
    days_back: int = Query(30, ge=1, le=365),
    pattern_type: Optional[str] = None
):
    """Get discovered chart patterns and regimes"""
    try:
        client = get_supabase_client(service_role=False)
        
        start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        query = client.table('pattern_discovery') \
            .select('*') \
            .eq('symbol', symbol) \
            .gte('detected_at', start_date)
        
        if pattern_type:
            query = query.eq('pattern_type', pattern_type)
        
        response = query.order('detected_at', desc=True).execute()
        
        patterns = [PatternResponse(**p) for p in response.data]
        
        return patterns
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/regime")
async def get_current_regime(symbol: str = Query("HDFCBANK.NS")):
    """Get current market regime classification"""
    try:
        client = get_supabase_client(service_role=False)
        
        # Get latest features with regime info
        response = client.table('features_store') \
            .select('timestamp, regime_classification, trend_strength, volatility_20d') \
            .eq('symbol', symbol) \
            .order('timestamp', desc=True) \
            .limit(1) \
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="No regime data available")
        
        latest = response.data[0]
        
        # Get regime history (last 30 days)
        start_date = (datetime.now() - timedelta(days=30)).isoformat()
        history_response = client.table('features_store') \
            .select('timestamp, regime_classification') \
            .eq('symbol', symbol) \
            .gte('timestamp', start_date) \
            .order('timestamp', desc=False) \
            .execute()
        
        regime_history = pd.DataFrame(history_response.data)
        regime_distribution = regime_history['regime_classification'].value_counts().to_dict()
        
        return {
            "symbol": symbol,
            "current_regime": latest['regime_classification'],
            "trend_strength": latest['trend_strength'],
            "volatility": latest['volatility_20d'],
            "as_of": latest['timestamp'],
            "regime_distribution_30d": regime_distribution
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/performance", response_model=List[PerformanceMetricsResponse])
async def get_model_performance(
    model_name: Optional[str] = None,
    days_back: int = Query(30, ge=7, le=365)
):
    """Get model performance metrics over time"""
    try:
        client = get_supabase_client(service_role=False)
        
        start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        query = client.table('performance_metrics') \
            .select('*') \
            .gte('calculated_at', start_date)
        
        if model_name:
            query = query.eq('model_name', model_name)
        
        response = query.order('calculated_at', desc=True).execute()
        
        metrics = [PerformanceMetricsResponse(**m) for m in response.data]
        
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/feature-importance")
async def get_feature_importance(
    model_name: str = Query("advanced_xgboost"),
    model_version: str = Query("v1.0")
):
    """Get feature importance from model metadata"""
    try:
        client = get_supabase_client(service_role=False)
        
        response = client.table('model_metadata') \
            .select('feature_importance, trained_at') \
            .eq('model_name', model_name) \
            .eq('model_version', model_version) \
            .single() \
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return {
            "model_name": model_name,
            "model_version": model_version,
            "trained_at": response.data['trained_at'],
            "feature_importance": response.data['feature_importance']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/sector-correlation")
async def get_sector_correlation(
    symbol: str = Query("HDFCBANK.NS"),
    days_back: int = Query(90, ge=30, le=365)
):
    """Get correlation with sector indices and banking peers"""
    try:
        client = get_supabase_client(service_role=False)
        
        start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        response = client.table('features_store') \
            .select('timestamp, correlation_nifty_bank, correlation_banking_peers, relative_strength_sector') \
            .eq('symbol', symbol) \
            .gte('timestamp', start_date) \
            .order('timestamp', desc=False) \
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="No correlation data available")
        
        df = pd.DataFrame(response.data)
        
        # Calculate average correlations
        avg_nifty_corr = df['correlation_nifty_bank'].mean()
        avg_peers_corr = df['correlation_banking_peers'].mean()
        avg_rel_strength = df['relative_strength_sector'].mean()
        
        # Get latest values
        latest = df.iloc[-1]
        
        return {
            "symbol": symbol,
            "period_days": days_back,
            "current": {
                "correlation_nifty_bank": latest['correlation_nifty_bank'],
                "correlation_banking_peers": latest['correlation_banking_peers'],
                "relative_strength_sector": latest['relative_strength_sector']
            },
            "average": {
                "correlation_nifty_bank": float(avg_nifty_corr),
                "correlation_banking_peers": float(avg_peers_corr),
                "relative_strength_sector": float(avg_rel_strength)
            },
            "time_series": response.data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/technical-indicators")
async def get_technical_indicators(
    symbol: str = Query("HDFCBANK.NS"),
    days_back: int = Query(30, ge=1, le=365)
):
    """Get technical indicators breakdown"""
    try:
        client = get_supabase_client(service_role=False)
        
        start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        response = client.table('features_store') \
            .select('timestamp, sma_5, sma_20, sma_50, rsi_14, macd, macd_signal, bollinger_upper, bollinger_middle, bollinger_lower') \
            .eq('symbol', symbol) \
            .gte('timestamp', start_date) \
            .order('timestamp', desc=False) \
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="No indicator data available")
        
        # Get current price for context
        price_response = client.table('market_data_raw') \
            .select('close') \
            .eq('symbol', symbol) \
            .order('timestamp', desc=True) \
            .limit(1) \
            .execute()
        
        current_price = float(price_response.data[0]['close']) if price_response.data else None
        
        # Get latest indicators
        latest = response.data[-1]
        
        # Determine signals
        signals = {}
        if latest['rsi_14']:
            if latest['rsi_14'] > 70:
                signals['rsi'] = 'overbought'
            elif latest['rsi_14'] < 30:
                signals['rsi'] = 'oversold'
            else:
                signals['rsi'] = 'neutral'
        
        if latest['macd'] and latest['macd_signal']:
            signals['macd'] = 'bullish' if latest['macd'] > latest['macd_signal'] else 'bearish'
        
        if current_price and latest['bollinger_upper'] and latest['bollinger_lower']:
            if current_price > latest['bollinger_upper']:
                signals['bollinger'] = 'overbought'
            elif current_price < latest['bollinger_lower']:
                signals['bollinger'] = 'oversold'
            else:
                signals['bollinger'] = 'neutral'
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "latest_indicators": latest,
            "signals": signals,
            "time_series": response.data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
