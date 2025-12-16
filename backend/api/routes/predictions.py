"""
Predictions API Routes
Endpoints for getting and managing predictions
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import pandas as pd

from config.supabase_config import get_supabase_client

router = APIRouter()


class PredictionResponse(BaseModel):
    """Prediction response model"""
    model_config = {"protected_namespaces": ()}
    
    id: str
    symbol: str
    prediction_timestamp: datetime
    target_timestamp: datetime
    predicted_price: float
    confidence_lower: Optional[float]
    confidence_upper: Optional[float]
    model_name: str
    model_version: str
    predicted_direction: Optional[str]
    direction_probability: Optional[float]
    actual_price: Optional[float]
    prediction_error: Optional[float]


class LatestPredictionsResponse(BaseModel):
    """Latest predictions with multiple horizons"""
    symbol: str
    current_price: float
    predictions: List[PredictionResponse]
    generated_at: datetime


@router.get("/predictions/latest", response_model=LatestPredictionsResponse)
async def get_latest_predictions(
    symbol: str = Query("HDFCBANK.NS", description="Stock symbol"),
    model_name: str = Query("advanced_xgboost", description="Model name")
):
    """
    Get latest predictions for a symbol
    Returns predictions for next 1-5 days
    """
    try:
        client = get_supabase_client(service_role=False)  # Read-only
        
        # Get current price
        current_price_response = client.table('market_data_raw') \
            .select('close') \
            .eq('symbol', symbol) \
            .order('timestamp', desc=True) \
            .limit(1) \
            .execute()
        
        if not current_price_response.data:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        current_price = float(current_price_response.data[0]['close'])
        
        # Get latest predictions
        predictions_response = client.table('predictions') \
            .select('*') \
            .eq('symbol', symbol) \
            .eq('model_name', model_name) \
            .gte('target_timestamp', datetime.now().isoformat()) \
            .order('target_timestamp', desc=False) \
            .limit(5) \
            .execute()
        
        predictions = [PredictionResponse(**pred) for pred in predictions_response.data]
        
        return LatestPredictionsResponse(
            symbol=symbol,
            current_price=current_price,
            predictions=predictions,
            generated_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions/historical")
async def get_historical_predictions(
    symbol: str = Query("HDFCBANK.NS"),
    days_back: int = Query(30, ge=1, le=365),
    model_name: Optional[str] = None
):
    """
    Get historical predictions with actual outcomes
    Useful for performance visualization
    """
    try:
        client = get_supabase_client(service_role=False)
        
        start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        query = client.table('predictions') \
            .select('*') \
            .eq('symbol', symbol) \
            .gte('target_timestamp', start_date) \
            .not_.is_('actual_price', 'null')  # Only predictions with actual outcomes
        
        if model_name:
            query = query.eq('model_name', model_name)
        
        response = query.order('target_timestamp', desc=False).execute()
        
        return {
            "symbol": symbol,
            "period_days": days_back,
            "predictions_count": len(response.data),
            "predictions": response.data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions/comparison")
async def compare_models(
    symbol: str = Query("HDFCBANK.NS"),
    days_ahead: int = Query(1, ge=1, le=5)
):
    """
    Compare predictions from different models for same target date
    """
    try:
        client = get_supabase_client(service_role=False)
        
        target_date = (datetime.now() + timedelta(days=days_ahead)).date().isoformat()
        
        response = client.table('predictions') \
            .select('*') \
            .eq('symbol', symbol) \
            .gte('target_timestamp', target_date) \
            .lt('target_timestamp', f"{target_date}T23:59:59") \
            .order('model_name', desc=False) \
            .execute()
        
        # Group by model
        models_predictions = {}
        for pred in response.data:
            model = pred['model_name']
            if model not in models_predictions:
                models_predictions[model] = []
            models_predictions[model].append(pred)
        
        return {
            "symbol": symbol,
            "target_date": target_date,
            "models": models_predictions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions/accuracy")
async def get_prediction_accuracy(
    symbol: str = Query("HDFCBANK.NS"),
    model_name: str = Query("advanced_xgboost"),
    days_back: int = Query(30, ge=7, le=365)
):
    """
    Calculate prediction accuracy metrics for a model
    """
    try:
        client = get_supabase_client(service_role=False)
        
        start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        response = client.table('predictions') \
            .select('predicted_price, actual_price, prediction_error, direction_correct') \
            .eq('symbol', symbol) \
            .eq('model_name', model_name) \
            .gte('target_timestamp', start_date) \
            .not_.is_('actual_price', 'null') \
            .execute()
        
        if not response.data:
            # Return empty metrics instead of 404
            return {
                "symbol": symbol,
                "model_name": model_name,
                "period_days": days_back,
                "sample_size": 0,
                "metrics": {
                    "rmse": None,
                    "mae": None,
                    "mape": None,
                    "directional_accuracy": None
                },
                "message": "No predictions with actual outcomes found yet. Predictions are available for future dates."
            }
        
        df = pd.DataFrame(response.data)
        
        # Calculate metrics
        rmse = (df['prediction_error'] ** 2).mean() ** 0.5
        mae = df['prediction_error'].abs().mean()
        mape = (df['prediction_error'].abs() / df['actual_price']).mean() * 100
        directional_accuracy = df['direction_correct'].mean() if 'direction_correct' in df.columns else None
        
        return {
            "symbol": symbol,
            "model_name": model_name,
            "period_days": days_back,
            "sample_size": len(df),
            "metrics": {
                "rmse": float(rmse),
                "mae": float(mae),
                "mape": float(mape),
                "directional_accuracy": float(directional_accuracy) if directional_accuracy is not None else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
