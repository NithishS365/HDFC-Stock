"""
Health Check Routes
System health and status endpoints
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
import os

from config.supabase_config import get_supabase_client

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "HDFC Stock Prediction API"
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with database connectivity"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # Check database connectivity
    try:
        client = get_supabase_client(service_role=False)
        response = client.table('system_logs').select('id').limit(1).execute()
        health_status["components"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "message": str(e)
        }
    
    # Check if models directory exists
    models_path = "models/saved_models"
    if os.path.exists(models_path):
        model_files = os.listdir(models_path)
        health_status["components"]["models"] = {
            "status": "healthy",
            "models_count": len([f for f in model_files if f.endswith('.pkl')])
        }
    else:
        health_status["components"]["models"] = {
            "status": "warning",
            "message": "Models directory not found"
        }
    
    return health_status


@router.get("/health/models")
async def models_health():
    """Check status of trained models"""
    try:
        client = get_supabase_client(service_role=False)
        
        response = client.table('model_metadata') \
            .select('model_name, model_version, status, is_production, trained_at') \
            .eq('status', 'active') \
            .execute()
        
        return {
            "total_models": len(response.data),
            "production_models": len([m for m in response.data if m['is_production']]),
            "models": response.data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/data-freshness")
async def data_freshness():
    """Check data freshness"""
    try:
        client = get_supabase_client(service_role=False)
        
        # Check latest market data
        market_response = client.table('market_data_raw') \
            .select('timestamp') \
            .eq('symbol', 'HDFCBANK.NS') \
            .order('timestamp', desc=True) \
            .limit(1) \
            .execute()
        
        # Check latest features
        features_response = client.table('features_store') \
            .select('timestamp') \
            .eq('symbol', 'HDFCBANK.NS') \
            .order('timestamp', desc=True) \
            .limit(1) \
            .execute()
        
        # Check latest predictions
        predictions_response = client.table('predictions') \
            .select('created_at') \
            .order('created_at', desc=True) \
            .limit(1) \
            .execute()
        
        return {
            "market_data_latest": market_response.data[0] if market_response.data else None,
            "features_latest": features_response.data[0] if features_response.data else None,
            "predictions_latest": predictions_response.data[0] if predictions_response.data else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
