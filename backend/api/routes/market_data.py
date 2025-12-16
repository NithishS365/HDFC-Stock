"""
Market Data API Routes
Endpoints for retrieving market data
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from config.supabase_config import get_supabase_client

router = APIRouter()


class MarketDataPoint(BaseModel):
    """Market data point model"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float]


class MarketDataResponse(BaseModel):
    """Market data response"""
    symbol: str
    data_points: int
    start_date: datetime
    end_date: datetime
    data: List[MarketDataPoint]


@router.get("/market-data/ohlcv", response_model=MarketDataResponse)
async def get_ohlcv_data(
    symbol: str = Query("HDFCBANK.NS"),
    days_back: int = Query(30, ge=1, le=3650),
    interval: str = Query("1d", description="Data interval (only 1d supported currently)")
):
    """Get OHLCV market data"""
    try:
        client = get_supabase_client(service_role=False)
        
        start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        response = client.table('market_data_raw') \
            .select('timestamp, open, high, low, close, volume, adjusted_close') \
            .eq('symbol', symbol) \
            .gte('timestamp', start_date) \
            .order('timestamp', desc=False) \
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        data_points = [MarketDataPoint(**dp) for dp in response.data]
        
        return MarketDataResponse(
            symbol=symbol,
            data_points=len(data_points),
            start_date=data_points[0].timestamp,
            end_date=data_points[-1].timestamp,
            data=data_points
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-data/latest")
async def get_latest_price(symbol: str = Query("HDFCBANK.NS")):
    """Get latest price for a symbol"""
    try:
        client = get_supabase_client(service_role=False)
        
        response = client.table('market_data_raw') \
            .select('*') \
            .eq('symbol', symbol) \
            .order('timestamp', desc=True) \
            .limit(1) \
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        return {
            "symbol": symbol,
            "latest_data": response.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-data/symbols")
async def get_available_symbols():
    """Get list of available symbols"""
    try:
        client = get_supabase_client(service_role=False)
        
        response = client.table('reference_symbols') \
            .select('symbol, name, category') \
            .eq('is_active', True) \
            .execute()
        
        return {
            "symbols": response.data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
