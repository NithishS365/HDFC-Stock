"""
Baseline Time Series Model - ARIMA/SARIMAX
Provides baseline predictions for comparison
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from loguru import logger
import joblib
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from config.supabase_config import get_supabase_client


class BaselineARIMAModel:
    """SARIMAX baseline model for time series prediction"""
    
    MODEL_NAME = "baseline_arima"
    MODEL_VERSION = "v1.0"
    
    def __init__(self):
        self.client = get_supabase_client(service_role=True)
        self.model = None
        self.model_fit = None
        
    def fetch_training_data(self, symbol: str, days_back: int = 730) -> pd.DataFrame:
        """Fetch data for training"""
        try:
            start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            response = self.client.table('market_data_raw') \
                .select('timestamp, close') \
                .eq('symbol', symbol) \
                .gte('timestamp', start_date) \
                .order('timestamp', desc=False) \
                .execute()
            
            df = pd.DataFrame(response.data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching training data: {str(e)}")
            return pd.DataFrame()
    
    def prepare_data(self, df: pd.DataFrame, train_ratio: float = 0.8) -> Tuple[pd.Series, pd.Series]:
        """Split data into train and validation sets"""
        train_size = int(len(df) * train_ratio)
        
        train = df.iloc[:train_size]['close']
        val = df.iloc[train_size:]['close']
        
        logger.info(f"Training samples: {len(train)}, Validation samples: {len(val)}")
        
        return train, val
    
    def train(self, train_data: pd.Series, order: Tuple[int, int, int] = (2, 1, 2),
              seasonal_order: Tuple[int, int, int, int] = (1, 1, 1, 5)) -> Dict:
        """
        Train SARIMAX model
        
        Args:
            train_data: Training time series
            order: (p, d, q) ARIMA order
            seasonal_order: (P, D, Q, s) seasonal order
        """
        try:
            logger.info(f"Training SARIMAX model with order={order}, seasonal_order={seasonal_order}")
            
            # Fit model
            self.model = SARIMAX(
                train_data,
                order=order,
                seasonal_order=seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            
            self.model_fit = self.model.fit(disp=False)
            
            logger.info("Model training completed")
            
            # Training metrics
            train_pred = self.model_fit.fittedvalues
            train_rmse = np.sqrt(mean_squared_error(train_data, train_pred))
            train_mae = mean_absolute_error(train_data, train_pred)
            
            metrics = {
                'train_rmse': train_rmse,
                'train_mae': train_mae
            }
            
            logger.info(f"Training RMSE: {train_rmse:.4f}, MAE: {train_mae:.4f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise
    
    def validate(self, val_data: pd.Series) -> Dict:
        """Validate model on validation set"""
        try:
            # Forecast
            forecast = self.model_fit.forecast(steps=len(val_data))
            
            # Metrics
            val_rmse = np.sqrt(mean_squared_error(val_data, forecast))
            val_mae = mean_absolute_error(val_data, forecast)
            val_r2 = r2_score(val_data, forecast)
            
            # Directional accuracy
            actual_direction = (val_data.diff() > 0).astype(int)
            pred_direction = (pd.Series(forecast, index=val_data.index).diff() > 0).astype(int)
            directional_accuracy = (actual_direction == pred_direction).mean()
            
            metrics = {
                'val_rmse': val_rmse,
                'val_mae': val_mae,
                'val_r2': val_r2,
                'directional_accuracy': directional_accuracy
            }
            
            logger.info(f"Validation RMSE: {val_rmse:.4f}, MAE: {val_mae:.4f}, R2: {val_r2:.4f}")
            logger.info(f"Directional Accuracy: {directional_accuracy:.4f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error validating model: {str(e)}")
            return {}
    
    def predict(self, steps: int = 5, confidence_level: float = 0.95) -> pd.DataFrame:
        """
        Generate predictions with confidence intervals
        
        Args:
            steps: Number of days to predict ahead
            confidence_level: Confidence level for intervals
        """
        try:
            # Get forecast with confidence intervals
            forecast_result = self.model_fit.get_forecast(steps=steps)
            forecast = forecast_result.predicted_mean
            conf_int = forecast_result.conf_int(alpha=1 - confidence_level)
            
            # Create DataFrame
            predictions = pd.DataFrame({
                'predicted_price': forecast.values,
                'confidence_lower': conf_int.iloc[:, 0].values,
                'confidence_upper': conf_int.iloc[:, 1].values
            }, index=forecast.index)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error generating predictions: {str(e)}")
            return pd.DataFrame()
    
    def save_model(self, filepath: str):
        """Save model to disk"""
        try:
            joblib.dump(self.model_fit, filepath)
            logger.info(f"Model saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
    
    def load_model(self, filepath: str):
        """Load model from disk"""
        try:
            self.model_fit = joblib.load(filepath)
            logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
    
    def save_metadata(self, train_metrics: Dict, val_metrics: Dict, 
                      training_start: datetime, training_end: datetime, 
                      training_samples: int):
        """Save model metadata to database"""
        try:
            metadata = {
                'model_name': self.MODEL_NAME,
                'model_version': self.MODEL_VERSION,
                'model_type': 'SARIMAX',
                'trained_at': datetime.now().isoformat(),
                'training_data_start': training_start.isoformat(),
                'training_data_end': training_end.isoformat(),
                'training_samples': training_samples,
                'hyperparameters': {
                    'order': [2, 1, 2],
                    'seasonal_order': [1, 1, 1, 5]
                },
                'train_rmse': float(train_metrics.get('train_rmse', 0)),
                'train_mae': float(train_metrics.get('train_mae', 0)),
                'train_r2': None,
                'val_rmse': float(val_metrics.get('val_rmse', 0)),
                'val_mae': float(val_metrics.get('val_mae', 0)),
                'val_r2': float(val_metrics.get('val_r2', 0)),
                'directional_accuracy': float(val_metrics.get('directional_accuracy', 0)),
                'status': 'active',
                'is_production': False
            }
            
            self.client.table('model_metadata').upsert(
                metadata,
                on_conflict='model_name,model_version'
            ).execute()
            
            logger.info("Model metadata saved")
            
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}")


def train_baseline_model(symbol: str = 'HDFCBANK.NS'):
    """Complete baseline model training pipeline"""
    logger.info("="*60)
    logger.info("TRAINING BASELINE ARIMA MODEL")
    logger.info("="*60)
    
    model = BaselineARIMAModel()
    
    # Fetch data
    logger.info("Fetching training data...")
    df = model.fetch_training_data(symbol, days_back=730)
    
    if df.empty:
        logger.error("No training data available")
        return None
    
    # Prepare data
    train, val = model.prepare_data(df)
    
    # Train
    logger.info("Training model...")
    train_metrics = model.train(train)
    
    # Validate
    logger.info("Validating model...")
    val_metrics = model.validate(val)
    
    # Save model
    model_path = "models/saved_models/baseline_arima_v1.0.pkl"
    model.save_model(model_path)
    
    # Save metadata
    model.save_metadata(
        train_metrics,
        val_metrics,
        train.index[0],
        train.index[-1],
        len(train)
    )
    
    logger.info("Baseline model training complete!")
    
    return model


if __name__ == "__main__":
    logger.add(
        "logs/baseline_training_{time}.log",
        rotation="100 MB",
        retention="30 days",
        level="INFO"
    )
    
    train_baseline_model()
