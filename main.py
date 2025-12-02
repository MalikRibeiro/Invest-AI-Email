import schedule
import time
import logging
import argparse
import sys
import os
from datetime import datetime
from config.settings import Settings
from src.data_collector import DataCollector
from src.portfolio import PortfolioManager
from src.report_generator import ReportGenerator
from src.notifier import Notifier
from src.ai_analyst import AIAnalyst
from src.news_collector import NewsCollector

# Configure Logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=getattr(logging, Settings.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

from src.sheets_manager import SheetsManager

def job():
    logger.info("Starting daily financial report job...")
    try:
        # 1. Load Portfolio from Sheets
        portfolio_data = SheetsManager.get_portfolio_from_sheets()
        if not portfolio_data:
            logger.error("Failed to load portfolio data. Aborting.")
            return

        # 2. Data Collection (Pass portfolio data)
        collector = DataCollector(portfolio_data)
        market_data = collector.get_market_data()
        indicators = collector.get_economic_indicators()
        
        # 2.1 News Collection
        news_collector = NewsCollector()
        news_summary = news_collector.get_top_news()
        
        # 3. Portfolio Logic (Pass portfolio data & market data)
        manager = PortfolioManager(portfolio_data, market_data, indicators)
        portfolio_df, total_value, daily_variation_pct = manager.calculate_portfolio()
        suggestions_df = manager.get_rebalancing_suggestions(portfolio_df, total_value)
        contribution_df = manager.suggest_contribution(250.00, suggestions_df)
        
        # 3. AI Analysis
        logger.info("Generating AI Analysis...")
        analyst = AIAnalyst()
        ai_analysis = analyst.generate_ai_analysis(portfolio_df, total_value, indicators, news_summary)
        
        # 4. Report Generation (Chart only)
        generator = ReportGenerator()
        chart_b64 = generator.generate_allocation_chart(portfolio_df)
        
        # 5. Notification
        notifier = Notifier()
        subject = f"Relatório Financeiro Diário - {datetime.now().strftime('%d/%m/%Y')}"
        
        # Prepare context for Email Template
        email_context = {
            'date': datetime.now().strftime('%d/%m/%Y'),
            'total_value': total_value,
            'daily_variation_pct': daily_variation_pct,
            'indicators': indicators,
            'ai_analysis': ai_analysis,
            'suggestions': suggestions_df,
            'contribution': contribution_df,
            'allocation_chart': chart_b64
        }
        
        # Send Email
        notifier.send_email(subject, email_context)
        
        
        logger.info("Job completed successfully.")
        
    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Financial Automation Bot")
    parser.add_argument("--test", action="store_true", help="Run the job immediately once and exit")
    args = parser.parse_args()
    
    if args.test:
        logger.info("Running in TEST mode.")
        job()
    else:
        logger.info("Scheduler started. Waiting for 19:00...")
        # Schedule for 19:00 weekdays
        schedule.every().monday.at("19:00").do(job)
        schedule.every().tuesday.at("19:00").do(job)
        schedule.every().wednesday.at("19:00").do(job)
        schedule.every().thursday.at("19:00").do(job)
        schedule.every().friday.at("19:00").do(job)
        
        while True:
            schedule.run_pending()
            time.sleep(60)

if __name__ == "__main__":
    main()
