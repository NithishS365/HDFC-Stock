"""
Feature Engineering Service
Generates technical indicators and sector-aware features
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger
import ta  # Technical Analysis library

from config.supabase_config import get_supabase_client


class FeatureEngineer:
    """Handles feature engineering for time-series models"""
    
    FEATURE_VERSION = "v1"
    
    def __init__(self):
        self.client = get_supabase_client(service_role=True)
    
    def fetch_market_data(self, symbol: str, days_back: int = 365) -> pd.DataFrame:
        """Fetch market data for feature engineering"""
        try:
            start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            response = self.client.table('market_data_raw') \
                .select('*') \
                .eq('symbol', symbol) \
                .gte('timestamp', start_date) \
                .order('timestamp', desc=False) \
                .execute()
            
            if not response.data:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()
            
            df = pd.DataFrame(response.data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        try:
            # Moving Averages
            df['sma_5'] = ta.trend.sma_indicator(df['close'], window=5)
            df['sma_20'] = ta.trend.sma_indicator(df['close'], window=20)
            df['sma_50'] = ta.trend.sma_indicator(df['close'], window=50)
            df['ema_12'] = ta.trend.ema_indicator(df['close'], window=12)
            df['ema_26'] = ta.trend.ema_indicator(df['close'], window=26)
            
            # RSI
            df['rsi_14'] = ta.momentum.rsi(df['close'], window=14)
            
            # MACD
            macd = ta.trend.MACD(df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_histogram'] = macd.macd_diff()
            
            # Bollinger Bands
            bollinger = ta.volatility.BollingerBands(df['close'])
            df['bollinger_upper'] = bollinger.bollinger_hband()
            df['bollinger_middle'] = bollinger.bollinger_mavg()
            df['bollinger_lower'] = bollinger.bollinger_lband()
            
            # ATR (Average True Range)
            df['atr_14'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
            
            # OBV (On-Balance Volume)
            df['obv'] = ta.volume.on_balance_volume(df['close'], df['volume'])
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {str(e)}")
            return df
    
    def calculate_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate price-based features"""
        try:
            # Returns
            df['returns_1d'] = df['close'].pct_change(1)
            df['returns_5d'] = df['close'].pct_change(5)
            df['returns_20d'] = df['close'].pct_change(20)
            
            # Volatility (rolling standard deviation of returns)
            df['volatility_20d'] = df['returns_1d'].rolling(window=20).std()
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating price features: {str(e)}")
            return df
    
    def calculate_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate volume-based features"""
        try:
            # Volume moving average
            df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
            
            # Volume ratio (current volume vs average)
            df['volume_ratio'] = df['volume'] / df['volume_sma_20']
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating volume features: {str(e)}")
            return df
    
    def calculate_sector_features(self, df_primary: pd.DataFrame, df_index: pd.DataFrame, 
                                  df_peers: List[pd.DataFrame]) -> pd.DataFrame:
        """Calculate sector correlation and relative strength features"""
        try:
            # Merge with index data
            merged = df_primary.merge(
                df_index[['timestamp', 'close']],
                on='timestamp',
                how='left',
                suffixes=('', '_index')
            )
            
            # Correlation with sector index (rolling 20-day)
            merged['correlation_nifty_bank'] = merged['returns_1d'].rolling(window=20).corr(
                merged['close_index'].pct_change()
            )
            
            # Relative strength vs sector
            merged['relative_strength_sector'] = merged['close'] / merged['close_index']
            
            # Average correlation with banking peers
            if df_peers:
                peer_returns = []
                for peer_df in df_peers:
                    peer_merged = merged.merge(
                        peer_df[['timestamp', 'close']],
                        on='timestamp',
                        how='left',
                        suffixes=('', '_peer')
                    )
                    peer_returns.append(peer_merged['close_peer'].pct_change())
                
                if peer_returns:
                    avg_peer_returns = pd.concat(peer_returns, axis=1).mean(axis=1)
                    merged['correlation_banking_peers'] = merged['returns_1d'].rolling(window=20).corr(
                        avg_peer_returns
                    )
            
            return merged
            
        except Exception as e:
            logger.error(f"Error calculating sector features: {str(e)}")
            return df_primary
    
    def classify_regime(self, df: pd.DataFrame) -> pd.DataFrame:
        """Classify market regime (trending up/down, ranging, volatile)"""
        try:
            # Trend classification based on moving averages
            df['trend_up'] = (df['sma_5'] > df['sma_20']) & (df['sma_20'] > df['sma_50'])
            df['trend_down'] = (df['sma_5'] < df['sma_20']) & (df['sma_20'] < df['sma_50'])
            
            # Trend strength (ADX-like measure)
            df['trend_strength'] = abs(df['sma_5'] - df['sma_50']) / df['sma_50']
            
            # Regime classification
            conditions = [
                df['trend_up'] & (df['trend_strength'] > 0.02),
                df['trend_down'] & (df['trend_strength'] > 0.02),
                df['volatility_20d'] > df['volatility_20d'].rolling(window=50).mean() * 1.5,
            ]
            choices = ['trending_up', 'trending_down', 'high_volatility']
            df['regime_classification'] = np.select(conditions, choices, default='ranging')
            
            return df
            
        except Exception as e:
            logger.error(f"Error classifying regime: {str(e)}")
            return df
    
    def prepare_features_for_storage(self, df: pd.DataFrame, symbol: str) -> List[Dict]:
        """Prepare features for database storage"""
        feature_columns = [
            'symbol', 'timestamp', 'feature_version',
            'sma_5', 'sma_20', 'sma_50', 'ema_12', 'ema_26',
            'rsi_14', 'macd', 'macd_signal', 'macd_histogram',
            'bollinger_upper', 'bollinger_middle', 'bollinger_lower',
            'atr_14', 'obv',
            'returns_1d', 'returns_5d', 'returns_20d', 'volatility_20d',
            'volume_sma_20', 'volume_ratio',
            'correlation_nifty_bank', 'correlation_banking_peers', 'relative_strength_sector',
            'regime_classification', 'trend_strength'
        ]
        
        # Add symbol and version
        df['symbol'] = symbol
        df['feature_version'] = self.FEATURE_VERSION
        
        # Select columns that exist
        available_columns = [col for col in feature_columns if col in df.columns]
        
        # Convert to records, dropping NaN values
        records = df[available_columns].replace({np.nan: None}).to_dict('records')
        
        return records
    
    def store_features(self, records: List[Dict], batch_size: int = 1000) -> bool:
        """Store features in database"""
        try:
            logger.info(f"Storing {len(records)} feature records")
            
            # Columns that are BIGINT in database schema
            bigint_columns = {'obv', 'volume_sma_20'}
            
            # Convert pandas Timestamps to strings for JSON serialization
            sanitized_records = []
            for record in records:
                sanitized = {}
                for key, value in record.items():
                    if pd.isna(value):
                        sanitized[key] = None
                    elif isinstance(value, pd.Timestamp):
                        sanitized[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                    elif key in bigint_columns:
                        # Convert to int for BIGINT columns
                        sanitized[key] = int(value) if not pd.isna(value) else None
                    elif isinstance(value, (np.integer, np.int64)):
                        sanitized[key] = int(value)
                    elif isinstance(value, (np.floating, np.float64)):
                        sanitized[key] = float(value)
                    else:
                        sanitized[key] = value
                sanitized_records.append(sanitized)
            
            # Insert in batches
            for i in range(0, len(sanitized_records), batch_size):
                batch = sanitized_records[i:i + batch_size]
                
                self.client.table('features_store').upsert(
                    batch,
                    on_conflict='symbol,timestamp,feature_version'
                ).execute()
                
                logger.debug(f"Stored batch {i // batch_size + 1}")
            
            logger.info("Features stored successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error storing features: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def engineer_features(self, symbol: str = 'HDFCBANK.NS', days_back: int = 365) -> bool:
        """
        Complete feature engineering pipeline
        
        Args:
            symbol: Primary symbol to engineer features for
            days_back: Days of historical data to process
        """
        try:
            logger.info(f"Engineering features for {symbol}")
            
            # Fetch primary symbol data
            df_primary = self.fetch_market_data(symbol, days_back)
            if df_primary.empty:
                logger.error(f"No data available for {symbol}")
                return False
            
            # Fetch sector index data
            df_index = self.fetch_market_data('^NSEBANK', days_back)
            
            # Fetch peer data
            peers = ['ICICIBANK.NS', 'KOTAKBANK.NS', 'AXISBANK.NS']
            df_peers = []
            for peer in peers:
                peer_df = self.fetch_market_data(peer, days_back)
                if not peer_df.empty:
                    df_peers.append(peer_df)
            
            # Calculate features
            logger.info("Calculating technical indicators...")
            df_primary = self.calculate_technical_indicators(df_primary)
            
            logger.info("Calculating price features...")
            df_primary = self.calculate_price_features(df_primary)
            
            logger.info("Calculating volume features...")
            df_primary = self.calculate_volume_features(df_primary)
            
            if not df_index.empty:
                logger.info("Calculating sector features...")
                df_primary = self.calculate_sector_features(df_primary, df_index, df_peers)
            
            logger.info("Classifying market regime...")
            df_primary = self.classify_regime(df_primary)
            
            # Prepare for storage
            records = self.prepare_features_for_storage(df_primary, symbol)
            
            # Store features
            success = self.store_features(records)
            
            return success
            
        except Exception as e:
            logger.error(f"Error in feature engineering pipeline: {str(e)}")
            return False


def run_feature_engineering():
    """Run feature engineering for HDFC Bank"""
    logger.info("="*60)
    logger.info("FEATURE ENGINEERING SERVICE")
    logger.info("="*60)
    
    engineer = FeatureEngineer()
    success = engineer.engineer_features('HDFCBANK.NS', days_back=730)  # 2 years
    
    if success:
        logger.info("Feature engineering completed successfully")
    else:
        logger.error("Feature engineering failed")
    
    return success


if __name__ == "__main__":
    logger.add(
        "logs/feature_engineering_{time}.log",
        rotation="100 MB",
        retention="30 days",
        level="INFO"
    )
    
    run_feature_engineering()
