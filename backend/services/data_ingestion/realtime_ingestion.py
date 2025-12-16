"""
Real-time Data Ingestion Service
Continuously fetches latest market data and updates the database
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from loguru import logger
import time
import schedule

from config.supabase_config import get_supabase_client


class RealtimeDataIngestion:
    """Handles real-time/incremental data ingestion"""
    
    SYMBOLS = ['HDFCBANK.NS', 'ICICIBANK.NS', 'KOTAKBANK.NS', 'AXISBANK.NS', 
               'SBIN.NS', '^NSEBANK', '^NSEI']
    
    def __init__(self):
        self.client = get_supabase_client(service_role=True)
    
    def get_latest_timestamp(self, symbol: str) -> Optional[datetime]:
        """Get the latest timestamp for a symbol in the database"""
        try:
            response = self.client.table('market_data_raw') \
                .select('timestamp') \
                .eq('symbol', symbol) \
                .order('timestamp', desc=True) \
                .limit(1) \
                .execute()
            
            if response.data and len(response.data) > 0:
                timestamp_str = response.data[0]['timestamp']
                return pd.to_datetime(timestamp_str)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest timestamp for {symbol}: {str(e)}")
            return None
    
    def fetch_incremental_data(self, symbol: str, since: Optional[datetime] = None) -> Optional[pd.DataFrame]:
        """
        Fetch incremental data since last update
        
        Args:
            symbol: Stock ticker symbol
            since: Fetch data since this timestamp (if None, fetches last 7 days)
        """
        try:
            if since is None:
                since = datetime.now() - timedelta(days=7)
            
            # Add 1 day to since to avoid duplicates
            start_date = since + timedelta(days=1)
            end_date = datetime.now()
            
            logger.info(f"Fetching incremental data for {symbol} from {start_date.date()}")
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval='1d',
                auto_adjust=False
            )
            
            if df.empty:
                logger.debug(f"No new data for {symbol}")
                return None
            
            # Process DataFrame
            df = df.reset_index()
            df = df.rename(columns={
                'Date': 'timestamp',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume',
                'Adj Close': 'adjusted_close'
            })
            
            df['symbol'] = symbol
            df = df[['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume', 'adjusted_close']]
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S%z')
            
            logger.info(f"Retrieved {len(df)} new records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching incremental data for {symbol}: {str(e)}")
            return None
    
    def store_market_data(self, df: pd.DataFrame) -> bool:
        """Store market data in Supabase"""
        try:
            symbol = df['symbol'].iloc[0]
            records = df.to_dict('records')
            
            response = self.client.table('market_data_raw').upsert(
                records,
                on_conflict='symbol,timestamp'
            ).execute()
            
            logger.info(f"Stored {len(records)} records for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing market data: {str(e)}")
            return False
    
    def ingest_symbol(self, symbol: str) -> bool:
        """Ingest latest data for a symbol"""
        try:
            # Get latest timestamp
            latest_ts = self.get_latest_timestamp(symbol)
            
            if latest_ts:
                logger.info(f"Latest data for {symbol}: {latest_ts.date()}")
            else:
                logger.info(f"No existing data for {symbol}, fetching initial batch")
            
            # Fetch incremental data
            df = self.fetch_incremental_data(symbol, latest_ts)
            
            if df is None or df.empty:
                logger.debug(f"No new data to ingest for {symbol}")
                return True
            
            # Store data
            success = self.store_market_data(df)
            return success
            
        except Exception as e:
            logger.error(f"Error ingesting {symbol}: {str(e)}")
            return False
    
    def ingest_all_symbols(self):
        """Ingest latest data for all symbols"""
        logger.info("Starting real-time data ingestion")
        
        for symbol in self.SYMBOLS:
            try:
                self.ingest_symbol(symbol)
                time.sleep(1)  # Rate limiting
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
        
        logger.info("Real-time ingestion complete")
    
    def schedule_ingestion(self):
        """Schedule periodic ingestion"""
        # Run every day at market close (3:30 PM IST / 10:00 AM UTC)
        schedule.every().day.at("10:00").do(self.ingest_all_symbols)
        
        # Also run every hour during market hours as backup
        schedule.every().hour.do(self.ingest_all_symbols)
        
        logger.info("Scheduled real-time ingestion jobs")
        logger.info("- Daily at 10:00 UTC (3:30 PM IST)")
        logger.info("- Hourly backup")
        
        while True:
            schedule.run_pending()
            time.sleep(60)


def run_realtime_ingestion():
    """Run real-time data ingestion service"""
    logger.info("="*60)
    logger.info("REAL-TIME DATA INGESTION SERVICE")
    logger.info("="*60)
    
    ingestion = RealtimeDataIngestion()
    
    # Run once immediately
    logger.info("Running initial ingestion...")
    ingestion.ingest_all_symbols()
    
    # Then schedule periodic runs
    logger.info("\nStarting scheduled ingestion...")
    ingestion.schedule_ingestion()


if __name__ == "__main__":
    logger.add(
        "logs/realtime_ingestion_{time}.log",
        rotation="100 MB",
        retention="30 days",
        level="INFO"
    )
    
    run_realtime_ingestion()
