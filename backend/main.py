"""
Main FastAPI Application
Production-grade API for HDFC stock prediction platform
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import List, Optional
import os
from dotenv import load_dotenv

from api.routes import predictions, analytics, health, market_data
from api.middleware.security import verify_api_key

load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="HDFC Stock Prediction API",
    description="Production-grade stock prediction platform with real-time updates",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(predictions.router, prefix="/api/v1", tags=["Predictions"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])
app.include_router(market_data.router, prefix="/api/v1", tags=["Market Data"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "HDFC Stock Prediction API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
