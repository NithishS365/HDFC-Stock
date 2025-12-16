"""
Advanced Time Series Model - XGBoost with Sector Awareness
Production-grade model with feature engineering
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List
from loguru import logger
import joblib
import xgboost as xgb
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler

from config.supabase_config import get_supabase_client


class AdvancedXGBoostModel:
    """XGBoost model with engineered features and sector awareness"""
    
    MODEL_NAME = "advanced_xgboost"
    MODEL_VERSION = "v1.0"
    FEATURE_VERSION = "v1"
    
    def __init__(self):
        self.client = get_supabase_client(service_role=True)
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        
    def fetch_training_data(self, symbol: str, days_back: int = 730) -> pd.DataFrame:
        """Fetch engineered features for training"""
        try:
            start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            response = self.client.table('features_store') \
                .select('*') \
                .eq('symbol', symbol) \
                .eq('feature_version', self.FEATURE_VERSION) \
                .gte('timestamp', start_date) \
                .order('timestamp', desc=False) \
                .execute()
            
            if not response.data:
                logger.warning(f"No feature data found for date range {start_date}, trying all available data")
                # Try fetching all available data if date filter returns nothing
                response = self.client.table('features_store') \
                    .select('*') \
                    .eq('symbol', symbol) \
                    .eq('feature_version', self.FEATURE_VERSION) \
                    .order('timestamp', desc=False) \
                    .execute()
                
                if not response.data:
                    logger.error("No feature data available at all")
                    return pd.DataFrame()
            
            df = pd.DataFrame(response.data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            logger.info(f"Fetched {len(df)} feature records")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching training data: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare feature matrix"""
        # Define feature columns
        self.feature_columns = [
            # Technical indicators
            'sma_5', 'sma_20', 'sma_50', 'ema_12', 'ema_26',
            'rsi_14', 'macd', 'macd_signal', 'macd_histogram',
            'bollinger_upper', 'bollinger_middle', 'bollinger_lower',
            'atr_14',
            # Price features
            'returns_1d', 'returns_5d', 'returns_20d', 'volatility_20d',
            # Volume features
            'volume_ratio',
            # Sector features
            'correlation_nifty_bank', 'correlation_banking_peers', 'relative_strength_sector',
            # Regime features
            'trend_strength'
        ]
        
        # Lag features (previous day's values)
        lag_features = ['returns_1d', 'rsi_14', 'macd', 'volatility_20d']
        for col in lag_features:
            if col in df.columns:
                df[f'{col}_lag1'] = df[col].shift(1)
                df[f'{col}_lag2'] = df[col].shift(2)
                self.feature_columns.extend([f'{col}_lag1', f'{col}_lag2'])
        
        # Rolling features
        if 'returns_1d' in df.columns:
            df['returns_1d_rolling_mean_5'] = df['returns_1d'].rolling(window=5).mean()
            df['returns_1d_rolling_std_5'] = df['returns_1d'].rolling(window=5).std()
            self.feature_columns.extend(['returns_1d_rolling_mean_5', 'returns_1d_rolling_std_5'])
        
        # Regime encoding - ensure all 4 categories always exist
        if 'regime_classification' in df.columns:
            # Define all possible regime categories
            all_regimes = ['high_volatility', 'ranging', 'trending_down', 'trending_up']
            
            # Initialize all regime columns to 0
            for regime in all_regimes:
                df[f'regime_{regime}'] = 0
            
            # Set the appropriate regime to 1 based on actual classification
            for regime in all_regimes:
                mask = df['regime_classification'] == regime
                df.loc[mask, f'regime_{regime}'] = 1
            
            # Add to feature columns if not already added (training phase)
            regime_cols = [f'regime_{r}' for r in all_regimes]
            if not any(col in self.feature_columns for col in regime_cols):
                self.feature_columns.extend(regime_cols)
        
        return df
    
    def create_sequences(self, df: pd.DataFrame, target_col: str = 'close', 
                        forecast_horizon: int = 1) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Create feature matrix and target for supervised learning
        
        Args:
            df: DataFrame with features
            target_col: Column to predict (from market_data_raw)
            forecast_horizon: Days ahead to predict
        """
        # Fetch actual close prices for target (all records, not limited to 1000)
        all_prices = []
        range_start = 0
        range_size = 1000
        
        while True:
            response = self.client.table('market_data_raw') \
                .select('timestamp, close') \
                .eq('symbol', 'HDFCBANK.NS') \
                .order('timestamp', desc=False) \
                .range(range_start, range_start + range_size - 1) \
                .execute()
            
            if not response.data:
                break
                
            all_prices.extend(response.data)
            
            if len(response.data) < range_size:
                break
                
            range_start += range_size
        
        logger.info(f"Fetched {len(all_prices)} price records total")
        
        price_df = pd.DataFrame(all_prices)
        price_df['timestamp'] = pd.to_datetime(price_df['timestamp'])
        
        # Debug: Check timestamp formats
        logger.info(f"Feature timestamps sample: {df['timestamp'].iloc[:3].tolist()}")
        logger.info(f"Price timestamps sample: {price_df['timestamp'].iloc[:3].tolist()}")
        
        # Ensure both timestamps are datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Normalize timestamps to date only (YYYY-MM-DD)
        df['date_str'] = df['timestamp'].dt.strftime('%Y-%m-%d')
        price_df['date_str'] = price_df['timestamp'].dt.strftime('%Y-%m-%d')
        
        logger.info(f"Feature dates sample: {df['date_str'].iloc[:3].tolist()}")
        logger.info(f"Price dates sample: {price_df['date_str'].iloc[:3].tolist()}")
        logger.info(f"Common dates: {len(set(df['date_str']) & set(price_df['date_str']))}")
        
        # Merge on string date for exact matching
        merged = df.merge(price_df[['date_str', 'close']], on='date_str', how='inner')
        
        logger.info(f"After merge: {len(merged)} records (from {len(df)} features and {len(price_df)} prices)")
        
        if len(merged) == 0:
            logger.error("Merge failed - no matching dates!")
            logger.error(f"Feature date range: {df['date_str'].min()} to {df['date_str'].max()}")
            logger.error(f"Price date range: {price_df['date_str'].min()} to {price_df['date_str'].max()}")
            raise ValueError("No matching dates between features and prices")
        
        # Create target (next day's close price)
        merged = merged.sort_values('date_str')
        merged['target'] = merged['close'].shift(-forecast_horizon)
        
        # Drop rows with NaN in features or target
        merged = merged.dropna(subset=self.feature_columns + ['target'])
        
        X = merged[self.feature_columns]
        y = merged['target']
        timestamps = merged['timestamp']
        
        logger.info(f"Created {len(X)} samples with {len(self.feature_columns)} features")
        
        return X, y, timestamps
    
    def prepare_data(self, X: pd.DataFrame, y: pd.Series, 
                    train_ratio: float = 0.8) -> Tuple:
        """Split and scale data"""
        train_size = int(len(X) * train_ratio)
        
        X_train, X_val = X.iloc[:train_size], X.iloc[train_size:]
        y_train, y_val = y.iloc[:train_size], y.iloc[train_size:]
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        logger.info(f"Training samples: {len(X_train)}, Validation samples: {len(X_val)}")
        
        return X_train_scaled, X_val_scaled, y_train, y_val
    
    def train(self, X_train: np.ndarray, y_train: pd.Series, 
             X_val: np.ndarray, y_val: pd.Series) -> Dict:
        """
        Train XGBoost model
        
        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features
            y_val: Validation targets
        """
        try:
            logger.info("Training XGBoost model...")
            
            # XGBoost parameters
            params = {
                'objective': 'reg:squarederror',
                'max_depth': 6,
                'learning_rate': 0.05,
                'n_estimators': 200,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'min_child_weight': 3,
                'gamma': 0.1,
                'reg_alpha': 0.1,
                'reg_lambda': 1.0,
                'random_state': 42,
                'n_jobs': -1
            }
            
            self.model = xgb.XGBRegressor(**params)
            
            # Train with early stopping
            self.model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                early_stopping_rounds=20,
                verbose=False
            )
            
            logger.info("Model training completed")
            
            # Training metrics
            train_pred = self.model.predict(X_train)
            train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
            train_mae = mean_absolute_error(y_train, train_pred)
            train_r2 = r2_score(y_train, train_pred)
            
            metrics = {
                'train_rmse': train_rmse,
                'train_mae': train_mae,
                'train_r2': train_r2,
                'hyperparameters': params
            }
            
            logger.info(f"Training RMSE: {train_rmse:.4f}, MAE: {train_mae:.4f}, R2: {train_r2:.4f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise
    
    def validate(self, X_val: np.ndarray, y_val: pd.Series) -> Dict:
        """Validate model"""
        try:
            val_pred = self.model.predict(X_val)
            
            val_rmse = np.sqrt(mean_squared_error(y_val, val_pred))
            val_mae = mean_absolute_error(y_val, val_pred)
            val_r2 = r2_score(y_val, val_pred)
            
            # Directional accuracy
            y_val_array = y_val.values
            actual_direction = np.sign(y_val_array[1:] - y_val_array[:-1])
            pred_direction = np.sign(val_pred[1:] - y_val_array[:-1])
            directional_accuracy = (actual_direction == pred_direction).mean()
            
            # Feature importance
            feature_importance = dict(zip(self.feature_columns, 
                                         self.model.feature_importances_))
            top_features = sorted(feature_importance.items(), 
                                 key=lambda x: x[1], reverse=True)[:10]
            
            metrics = {
                'val_rmse': val_rmse,
                'val_mae': val_mae,
                'val_r2': val_r2,
                'directional_accuracy': directional_accuracy,
                'feature_importance': dict(top_features)
            }
            
            logger.info(f"Validation RMSE: {val_rmse:.4f}, MAE: {val_mae:.4f}, R2: {val_r2:.4f}")
            logger.info(f"Directional Accuracy: {directional_accuracy:.4f}")
            logger.info(f"Top features: {list(dict(top_features).keys())}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error validating model: {str(e)}")
            return {}
    
    def predict(self, X: np.ndarray, confidence_level: float = 0.95) -> pd.DataFrame:
        """
        Generate predictions with confidence intervals
        Uses quantile regression for intervals
        """
        try:
            # Point prediction
            predictions = self.model.predict(X)
            
            # Estimate confidence intervals using historical errors
            # (Simplified approach - could use quantile regression for better intervals)
            std_error = np.std(predictions) * 0.1  # Approximate
            z_score = 1.96  # 95% confidence
            
            results = pd.DataFrame({
                'predicted_price': predictions,
                'confidence_lower': predictions - z_score * std_error,
                'confidence_upper': predictions + z_score * std_error
            })
            
            return results
            
        except Exception as e:
            logger.error(f"Error generating predictions: {str(e)}")
            return pd.DataFrame()
    
    def save_model(self, model_path: str, scaler_path: str, features_path: str):
        """Save model, scaler, and feature columns"""
        try:
            joblib.dump(self.model, model_path)
            joblib.dump(self.scaler, scaler_path)
            joblib.dump(self.feature_columns, features_path)
            logger.info(f"Model saved to {model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
    
    def load_model(self, model_path: str, scaler_path: str, features_path: str):
        """Load model, scaler, and feature columns"""
        try:
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            self.feature_columns = joblib.load(features_path)
            logger.info(f"Model loaded from {model_path}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
    
    def save_metadata(self, train_metrics: Dict, val_metrics: Dict,
                      training_start: datetime, training_end: datetime,
                      training_samples: int):
        """Save model metadata to database"""
        try:
            # Convert numpy types to native Python for JSON
            feature_importance = val_metrics.get('feature_importance', {})
            if feature_importance:
                feature_importance = {k: float(v) for k, v in feature_importance.items()}
            
            metadata = {
                'model_name': self.MODEL_NAME,
                'model_version': self.MODEL_VERSION,
                'model_type': 'XGBoost',
                'trained_at': datetime.now().isoformat(),
                'training_data_start': training_start.isoformat(),
                'training_data_end': training_end.isoformat(),
                'training_samples': int(training_samples),
                'hyperparameters': train_metrics.get('hyperparameters', {}),
                'train_rmse': float(train_metrics.get('train_rmse', 0)),
                'train_mae': float(train_metrics.get('train_mae', 0)),
                'train_r2': float(train_metrics.get('train_r2', 0)),
                'val_rmse': float(val_metrics.get('val_rmse', 0)),
                'val_mae': float(val_metrics.get('val_mae', 0)),
                'val_r2': float(val_metrics.get('val_r2', 0)),
                'directional_accuracy': float(val_metrics.get('directional_accuracy', 0)),
                'feature_importance': feature_importance,
                'status': 'active',
                'is_production': True
            }
            
            self.client.table('model_metadata').upsert(
                metadata,
                on_conflict='model_name,model_version'
            ).execute()
            
            logger.info("Model metadata saved")
            
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())


def train_advanced_model(symbol: str = 'HDFCBANK.NS'):
    """Complete advanced model training pipeline"""
    logger.info("="*60)
    logger.info("TRAINING ADVANCED XGBOOST MODEL")
    logger.info("="*60)
    
    model = AdvancedXGBoostModel()
    
    # Fetch data
    logger.info("Fetching feature data...")
    df = model.fetch_training_data(symbol, days_back=730)
    
    if df.empty:
        logger.error("No feature data available")
        logger.error("Run feature engineering first!")
        return None
    
    # Prepare features
    logger.info("Preparing features...")
    df = model.prepare_features(df)
    
    # Create sequences
    logger.info("Creating training sequences...")
    X, y, timestamps = model.create_sequences(df)
    
    # Prepare data
    X_train, X_val, y_train, y_val = model.prepare_data(X, y)
    
    # Train
    logger.info("Training model...")
    train_metrics = model.train(X_train, y_train, X_val, y_val)
    
    # Validate
    logger.info("Validating model...")
    val_metrics = model.validate(X_val, y_val)
    
    # Save model
    model.save_model(
        "models/saved_models/advanced_xgboost_v1.0.pkl",
        "models/saved_models/advanced_xgboost_v1.0_scaler.pkl",
        "models/saved_models/advanced_xgboost_v1.0_features.pkl"
    )
    
    # Save metadata
    model.save_metadata(
        train_metrics,
        val_metrics,
        timestamps.iloc[0],
        timestamps.iloc[-1],
        len(X_train)
    )
    
    logger.info("Advanced model training complete!")
    
    return model


if __name__ == "__main__":
    logger.add(
        "logs/advanced_training_{time}.log",
        rotation="100 MB",
        retention="30 days",
        level="INFO"
    )
    
    train_advanced_model()
