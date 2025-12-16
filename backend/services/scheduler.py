"""
Scheduler Service
Manages periodic tasks for data ingestion, feature engineering, and predictions
"""
import schedule
import time
from datetime import datetime
from loguru import logger

from services.data_ingestion.realtime_ingestion import RealtimeDataIngestion
from services.feature_engineering.feature_engineer import FeatureEngineer
from services.prediction_service import PredictionService


class SchedulerService:
    """Manages all scheduled tasks"""
    
    def __init__(self):
        self.data_ingestion = RealtimeDataIngestion()
        self.feature_engineer = FeatureEngineer()
        self.prediction_service = PredictionService()
    
    def job_ingest_data(self):
        """Job: Ingest latest market data"""
        try:
            logger.info("Starting scheduled data ingestion...")
            self.data_ingestion.ingest_all_symbols()
            logger.info("Data ingestion completed")
        except Exception as e:
            logger.error(f"Error in data ingestion job: {str(e)}")
    
    def job_engineer_features(self):
        """Job: Engineer features"""
        try:
            logger.info("Starting scheduled feature engineering...")
            self.feature_engineer.engineer_features('HDFCBANK.NS', days_back=365)
            logger.info("Feature engineering completed")
        except Exception as e:
            logger.error(f"Error in feature engineering job: {str(e)}")
    
    def job_generate_predictions(self):
        """Job: Generate predictions"""
        try:
            logger.info("Starting scheduled prediction generation...")
            self.prediction_service.run()
            logger.info("Prediction generation completed")
        except Exception as e:
            logger.error(f"Error in prediction job: {str(e)}")
    
    def run(self):
        """Start scheduler"""
        logger.info("="*60)
        logger.info("SCHEDULER SERVICE STARTED")
        logger.info("="*60)
        
        # Schedule jobs
        
        # Daily at 4 PM IST (10:30 AM UTC) - After market close
        schedule.every().day.at("10:30").do(self.job_ingest_data)
        
        # Daily at 4:30 PM IST - After data ingestion
        schedule.every().day.at("11:00").do(self.job_engineer_features)
        
        # Daily at 5 PM IST - After feature engineering
        schedule.every().day.at("11:30").do(self.job_generate_predictions)
        
        # Also run every 6 hours as backup
        schedule.every(6).hours.do(self.job_ingest_data)
        schedule.every(6).hours.do(self.job_engineer_features)
        schedule.every(6).hours.do(self.job_generate_predictions)
        
        logger.info("Scheduled jobs:")
        logger.info("- Data ingestion: Daily at 4:00 PM IST + every 6 hours")
        logger.info("- Feature engineering: Daily at 4:30 PM IST + every 6 hours")
        logger.info("- Predictions: Daily at 5:00 PM IST + every 6 hours")
        
        # Run initial jobs
        logger.info("\nRunning initial jobs...")
        self.job_ingest_data()
        self.job_engineer_features()
        self.job_generate_predictions()
        
        # Start scheduler loop
        logger.info("\nScheduler running... (Ctrl+C to stop)")
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


if __name__ == "__main__":
    logger.add(
        "logs/scheduler_{time}.log",
        rotation="100 MB",
        retention="30 days",
        level="INFO"
    )
    
    scheduler = SchedulerService()
    scheduler.run()
