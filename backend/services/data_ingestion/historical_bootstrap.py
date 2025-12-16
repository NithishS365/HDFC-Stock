"""
Historical Data Bootstrap Service
Ingests 5-10 years of historical data for HDFC Bank and related stocks
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from loguru import logger
import time
import random

from config.supabase_config import get_supabase_client


class HistoricalDataBootstrap:
    """Handles one-time historical data ingestion"""
    
    # Symbols to ingest
    SYMBOLS = {
        'primary': ['HDFCBANK.NS'],
        'banking_peers': ['ICICIBANK.NS', 'KOTAKBANK.NS', 'AXISBANK.NS', 'SBIN.NS'],
        'sector_indices': ['^NSEBANK', '^NSEI']
    }
    
    def __init__(self, years_back: int = 10):
        """
        Initialize bootstrap service
        
        Args:
            years_back: Number of years of historical data to fetch
        """
        self.client = get_supabase_client(service_role=True)
        self.years_back = years_back
        self.start_date = datetime.now() - timedelta(days=365 * years_back)
        self.end_date = datetime.now()
        
    def get_all_symbols(self) -> List[str]:
        """Get all symbols to ingest"""
        symbols = []
        for category, symbol_list in self.SYMBOLS.items():
            symbols.extend(symbol_list)
        return symbols
    
    def fetch_historical_data(self, symbol: str, max_retries: int = 3) -> Optional[pd.DataFrame]:
        """
        Fetch historical data for a symbol using yfinance with retry logic
        
        Args:
            symbol: Stock ticker symbol
            max_retries: Maximum number of retry attempts
            
        Returns:
            DataFrame with OHLCV data
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching historical data for {symbol} from {self.start_date.date()} to {self.end_date.date()} (attempt {attempt + 1}/{max_retries})")
                
                # Use download() method which is more reliable than Ticker().history()
                df = yf.download(
                    symbol,
                    start=self.start_date,
                    end=self.end_date,
                    interval='1d',
                    auto_adjust=False,
                    actions=False,  # Don't fetch dividends/splits
                    progress=False  # Disable progress bar
                )
                
                if df is None or df.empty:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 3 + random.uniform(0, 2)
                        logger.warning(f"No data retrieved for {symbol}, retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.warning(f"No data retrieved for {symbol} after {max_retries} attempts")
                        return None
                
                # Successfully got data
                logger.info(f"Successfully fetched {len(df)} records for {symbol}")
                break
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3 + random.uniform(0, 2)
                    logger.warning(f"Error fetching {symbol}: {str(e)}, retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Failed to fetch {symbol} after {max_retries} attempts: {str(e)}")
                    return None
        
        try:
            # Flatten multi-level columns if present (yf.download returns tuples)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Reset index to get timestamp as column
            df = df.reset_index()
            
            # Rename columns to match our schema
            df = df.rename(columns={
                'Date': 'timestamp',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume',
                'Adj Close': 'adjusted_close'
            })
            
            # Add symbol column
            df['symbol'] = symbol
            
            # Select only needed columns
            df = df[['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume', 'adjusted_close']]
            
            # Convert timestamp to ISO format string (remove timezone)
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Convert numeric columns to native Python float (not numpy)
            for col in ['open', 'high', 'low', 'close', 'volume', 'adjusted_close']:
                df[col] = df[col].astype(float)
            
            logger.info(f"Retrieved {len(df)} records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error processing data for {symbol}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def store_market_data(self, df: pd.DataFrame, batch_size: int = 1000) -> bool:
        """
        Store market data in Supabase
        
        Args:
            df: DataFrame with market data
            batch_size: Number of records per batch insert
            
        Returns:
            True if successful
        """
        try:
            symbol = df['symbol'].iloc[0]
            logger.info(f"Storing {len(df)} records for {symbol} in Supabase")
            
            # Convert DataFrame to list of dicts with proper type conversion
            records = []
            for _, row in df.iterrows():
                record = {
                    'symbol': str(row['symbol']),
                    'timestamp': str(row['timestamp']),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume']),  # bigint requires integer
                    'adjusted_close': float(row['adjusted_close'])
                }
                records.append(record)
            
            # Insert in batches to avoid payload size limits
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                # Upsert to handle duplicates
                response = self.client.table('market_data_raw').upsert(
                    batch,
                    on_conflict='symbol,timestamp'
                ).execute()
                
                logger.debug(f"Inserted batch {i // batch_size + 1} for {symbol}")
                time.sleep(0.1)  # Rate limiting
            
            logger.info(f"Successfully stored data for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing market data: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def log_job(self, job_type: str, status: str, message: str, details: Dict = None):
        """Log job execution to system_logs"""
        try:
            log_entry = {
                'job_type': job_type,
                'status': status,
                'message': message,
                'details': details or {}
            }
            self.client.table('system_logs').insert(log_entry).execute()
        except Exception as e:
            logger.error(f"Error logging to database: {str(e)}")
    
    def bootstrap_symbol(self, symbol: str) -> bool:
        """
        Bootstrap data for a single symbol
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            True if successful
        """
        self.log_job(
            'historical_bootstrap',
            'started',
            f'Starting historical data ingestion for {symbol}',
            {'symbol': symbol, 'years_back': self.years_back}
        )
        
        # Fetch data
        df = self.fetch_historical_data(symbol)
        if df is None or df.empty:
            self.log_job(
                'historical_bootstrap',
                'failed',
                f'No data retrieved for {symbol}',
                {'symbol': symbol}
            )
            return False
        
        # Store data
        success = self.store_market_data(df)
        
        if success:
            self.log_job(
                'historical_bootstrap',
                'completed',
                f'Successfully ingested {len(df)} records for {symbol}',
                {'symbol': symbol, 'records_count': len(df)}
            )
        else:
            self.log_job(
                'historical_bootstrap',
                'failed',
                f'Failed to store data for {symbol}',
                {'symbol': symbol}
            )
        
        return success
    
    def bootstrap_all(self) -> Dict[str, bool]:
        """
        Bootstrap historical data for all symbols
        
        Returns:
            Dictionary mapping symbol to success status
        """
        symbols = self.get_all_symbols()
        results = {}
        
        logger.info(f"Starting historical bootstrap for {len(symbols)} symbols")
        logger.info(f"Date range: {self.start_date.date()} to {self.end_date.date()}")
        
        for symbol in symbols:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing {symbol}")
            logger.info(f"{'='*60}")
            
            success = self.bootstrap_symbol(symbol)
            results[symbol] = success
            
            # Delay between symbols to respect rate limits
            time.sleep(1)
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info("BOOTSTRAP SUMMARY")
        logger.info(f"{'='*60}")
        
        successful = sum(1 for v in results.values() if v)
        failed = len(results) - successful
        
        logger.info(f"Total symbols: {len(results)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        
        for symbol, success in results.items():
            status = "✓" if success else "✗"
            logger.info(f"{status} {symbol}")
        
        return results
    
    def verify_data(self) -> Dict[str, int]:
        """
        Verify ingested data counts
        
        Returns:
            Dictionary mapping symbol to record count
        """
        symbols = self.get_all_symbols()
        counts = {}
        
        for symbol in symbols:
            try:
                response = self.client.table('market_data_raw') \
                    .select('id', count='exact') \
                    .eq('symbol', symbol) \
                    .execute()
                
                count = response.count if hasattr(response, 'count') else 0
                counts[symbol] = count
                logger.info(f"{symbol}: {count} records")
                
            except Exception as e:
                logger.error(f"Error verifying {symbol}: {str(e)}")
                counts[symbol] = -1
        
        return counts


def run_bootstrap(years_back: int = 10):
    """
    Run the historical data bootstrap
    
    Args:
        years_back: Number of years of historical data
    """
    logger.info("="*60)
    logger.info("HDFC STOCK PREDICTION - HISTORICAL DATA BOOTSTRAP")
    logger.info("="*60)
    
    bootstrap = HistoricalDataBootstrap(years_back=years_back)
    
    # Run bootstrap
    results = bootstrap.bootstrap_all()
    
    # Verify
    logger.info("\nVerifying ingested data...")
    counts = bootstrap.verify_data()
    
    logger.info("\nBootstrap complete!")
    return results, counts


if __name__ == "__main__":
    # Configure logging
    logger.add(
        "logs/bootstrap_{time}.log",
        rotation="500 MB",
        retention="30 days",
        level="INFO"
    )
    
    # Run bootstrap
    run_bootstrap(years_back=10)
