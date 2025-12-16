"""
Prediction Service
Generates and stores predictions for HDFC Bank stock
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict
from loguru import logger
import joblib

from config.supabase_config import get_supabase_client
from models.advanced_model import AdvancedXGBoostModel


class PredictionService:
    """Service for generating and managing predictions"""
    
    def __init__(self):
        self.client = get_supabase_client(service_role=True)
        self.model = None
        self.symbol = 'HDFCBANK.NS'
        
    def load_model(self):
        """Load trained model"""
        try:
            self.model = AdvancedXGBoostModel()
            self.model.load_model(
                "models/saved_models/advanced_xgboost_v1.0.pkl",
                "models/saved_models/advanced_xgboost_v1.0_scaler.pkl",
                "models/saved_models/advanced_xgboost_v1.0_features.pkl"
            )
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def fetch_latest_features(self, days_back: int = 100) -> pd.DataFrame:
        """Fetch latest features for prediction"""
        try:
            start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            response = self.client.table('features_store') \
                .select('*') \
                .eq('symbol', self.symbol) \
                .eq('feature_version', 'v1') \
                .gte('timestamp', start_date) \
                .order('timestamp', desc=False) \
                .execute()
            
            df = pd.DataFrame(response.data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching features: {str(e)}")
            return pd.DataFrame()
    
    def generate_predictions(self, forecast_days: int = 5) -> List[Dict]:
        """
        Generate predictions for next N days
        
        Args:
            forecast_days: Number of days to forecast
        """
        try:
            if self.model is None:
                self.load_model()
            
            # Fetch latest features
            df = self.fetch_latest_features()
            if df.empty:
                logger.error("No features available for prediction")
                return []
            
            # Prepare features (this adds lag features, rolling features, and regime dummies)
            df = self.model.prepare_features(df)
            
            # Get latest feature row
            latest_features = df.iloc[-1:][self.model.feature_columns]
            
            # Scale features
            latest_scaled = self.model.scaler.transform(latest_features)
            
            predictions = []
            current_date = datetime.now()
            
            for day in range(1, forecast_days + 1):
                target_date = current_date + timedelta(days=day)
                
                # Predict
                pred_result = self.model.predict(latest_scaled)
                predicted_price = pred_result['predicted_price'].iloc[0]
                conf_lower = pred_result['confidence_lower'].iloc[0]
                conf_upper = pred_result['confidence_upper'].iloc[0]
                
                # Get current price for direction
                current_price_response = self.client.table('market_data_raw') \
                    .select('close') \
                    .eq('symbol', self.symbol) \
                    .order('timestamp', desc=True) \
                    .limit(1) \
                    .execute()
                
                current_price = float(current_price_response.data[0]['close']) if current_price_response.data else None
                
                # Determine direction
                if current_price:
                    if predicted_price > current_price * 1.001:  # >0.1% change
                        direction = 'UP'
                        probability = 0.65
                    elif predicted_price < current_price * 0.999:  # <-0.1% change
                        direction = 'DOWN'
                        probability = 0.65
                    else:
                        direction = 'NEUTRAL'
                        probability = 0.5
                else:
                    direction = None
                    probability = None
                
                # Create prediction record
                prediction = {
                    'symbol': self.symbol,
                    'prediction_timestamp': datetime.now().isoformat(),
                    'target_timestamp': target_date.isoformat(),
                    'predicted_price': float(predicted_price),
                    'confidence_lower': float(conf_lower),
                    'confidence_upper': float(conf_upper),
                    'confidence_level': 0.95,
                    'model_name': self.model.MODEL_NAME,
                    'model_version': self.model.MODEL_VERSION,
                    'feature_version': self.model.FEATURE_VERSION,
                    'predicted_direction': direction,
                    'direction_probability': float(probability) if probability else None
                }
                
                predictions.append(prediction)
                
                logger.info(f"Day {day}: Predicted ₹{predicted_price:.2f} for {target_date.date()}")
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error generating predictions: {str(e)}")
            return []
    
    def store_predictions(self, predictions: List[Dict]) -> bool:
        """Store predictions in database"""
        try:
            if not predictions:
                logger.warning("No predictions to store")
                return False
            
            # Check for existing predictions and delete them
            for pred in predictions:
                # Delete any existing predictions for same symbol, target_timestamp, and model
                self.client.table('predictions') \
                    .delete() \
                    .eq('symbol', pred['symbol']) \
                    .eq('target_timestamp', pred['target_timestamp']) \
                    .eq('model_name', pred['model_name']) \
                    .eq('model_version', pred['model_version']) \
                    .execute()
            
            # Insert new predictions
            response = self.client.table('predictions').insert(predictions).execute()
            
            logger.info(f"Stored {len(predictions)} predictions")
            return True
            
        except Exception as e:
            logger.error(f"Error storing predictions: {str(e)}")
            return False
    
    def update_actual_prices(self):
        """Update predictions with actual prices once available"""
        try:
            # Get predictions without actual prices where target date has passed
            response = self.client.table('predictions') \
                .select('id, symbol, target_timestamp, predicted_price') \
                .is_('actual_price', 'null') \
                .lt('target_timestamp', datetime.now().isoformat()) \
                .execute()
            
            if not response.data:
                logger.info("No predictions to update")
                return
            
            logger.info(f"Updating {len(response.data)} predictions with actual prices")
            
            for pred in response.data:
                # Get actual price for target date
                target_date = pd.to_datetime(pred['target_timestamp']).date()
                
                price_response = self.client.table('market_data_raw') \
                    .select('close') \
                    .eq('symbol', pred['symbol']) \
                    .gte('timestamp', target_date.isoformat()) \
                    .lt('timestamp', (target_date + timedelta(days=1)).isoformat()) \
                    .execute()
                
                if price_response.data:
                    actual_price = float(price_response.data[0]['close'])
                    
                    # Update prediction
                    self.client.table('predictions').update({
                        'actual_price': actual_price
                    }).eq('id', pred['id']).execute()
                    
                    logger.debug(f"Updated prediction {pred['id']} with actual price ₹{actual_price:.2f}")
            
            logger.info("Actual prices updated")
            
        except Exception as e:
            logger.error(f"Error updating actual prices: {str(e)}")
    
    def run(self):
        """Main prediction workflow"""
        logger.info("="*60)
        logger.info("PREDICTION SERVICE")
        logger.info("="*60)
        
        # Generate predictions
        logger.info("Generating predictions...")
        predictions = self.generate_predictions(forecast_days=5)
        
        if predictions:
            # Store predictions
            success = self.store_predictions(predictions)
            
            if success:
                logger.info("Predictions stored successfully")
            else:
                logger.error("Failed to store predictions")
        else:
            logger.error("No predictions generated")
        
        # Update actual prices
        logger.info("Updating actual prices...")
        self.update_actual_prices()
        
        logger.info("Prediction service complete!")


def run_prediction_service():
    """Run prediction service"""
    service = PredictionService()
    service.run()


if __name__ == "__main__":
    logger.add(
        "logs/prediction_service_{time}.log",
        rotation="100 MB",
        retention="30 days",
        level="INFO"
    )
    
    run_prediction_service()
