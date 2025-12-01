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

def job():
    logger.info("Starting daily financial report job...")
    try:
        # 1. Data Collection
        collector = DataCollector()
        market_data = collector.get_market_data()
        indicators = collector.get_economic_indicators()
        
        # 2. Portfolio Logic
        manager = PortfolioManager(market_data, indicators)
        portfolio_df, total_value = manager.calculate_portfolio()
        suggestions_df = manager.get_rebalancing_suggestions(portfolio_df, total_value)
        contribution_df = manager.suggest_contribution(250.00, suggestions_df)
        
        # 3. AI Analysis
        logger.info("Generating AI Analysis...")
        analyst = AIAnalyst()
        ai_analysis = analyst.generate_ai_analysis(portfolio_df, total_value, indicators)
        
        # 4. Report Generation
        generator = ReportGenerator()
        markdown_report = generator.generate_markdown_report(
            portfolio_df, total_value, suggestions_df, contribution_df, indicators, ai_analysis
        )
        
        os.makedirs("data", exist_ok=True)
        pdf_filename = f"data/report_{datetime.now().strftime('%Y%m%d')}.pdf"
        generator.generate_pdf_report(
            portfolio_df, total_value, suggestions_df, contribution_df, indicators, ai_analysis, filename=pdf_filename
        )
        
        # 5. Notification
        notifier = Notifier()
        subject = f"Relatório Financeiro Diário - {datetime.now().strftime('%d/%m/%Y')}"
        
        # Send Email
        notifier.send_email(subject, markdown_report, attachment_path=pdf_filename)
        
        # Send WhatsApp (Summary)
        whatsapp_msg = f"*Relatório Financeiro {datetime.now().strftime('%d/%m')}*\n\n"
        whatsapp_msg += f"💰 Valor Total: R$ {total_value:,.2f}\n"
        whatsapp_msg += f"📊 Selic: {indicators.get('selic_meta', 0)}% | CDI: {indicators.get('cdi', 0):.2f}%\n\n"
        whatsapp_msg += "Verifique seu e-mail para o relatório completo."
        notifier.send_whatsapp(whatsapp_msg)
        
        logger.info("Job completed successfully.")
        
    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)

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
