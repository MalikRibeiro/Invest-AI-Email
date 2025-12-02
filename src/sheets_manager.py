import pandas as pd
import logging
from config.settings import Settings

logger = logging.getLogger(__name__)

class SheetsManager:
    @staticmethod
    def get_portfolio_from_sheets():
        """Reads portfolio data from Google Sheets CSV."""
        url = Settings.SHEET_CSV_URL
        if not url:
            logger.error("SHEET_CSV_URL not found in settings.")
            return []
            
        try:
            logger.info("Baixando carteira do Google Sheets...")
            df = pd.read_csv(url)
            
            # Expected columns: Ticker, Quantidade, Categoria, Meta
            required_cols = ['Ticker', 'Quantidade', 'Categoria', 'Meta']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"Missing columns in Sheet. Expected: {required_cols}")
                return []
                
            portfolio = []
            for _, row in df.iterrows():
                ticker = str(row['Ticker']).strip().upper()
                
                # Clean Quantity (remove R$, dots, replace comma with dot)
                qty_str = str(row['Quantidade'])
                qty_str = qty_str.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
                try:
                    qty = float(qty_str)
                except ValueError:
                    logger.warning(f"Invalid quantity for {ticker}: {row['Quantidade']}")
                    qty = 0.0

                # Clean Meta (Target Allocation)
                meta_str = str(row['Meta'])
                meta_str = meta_str.replace('%', '').replace(' ', '').replace(',', '.')
                try:
                    meta = float(meta_str)
                except ValueError:
                    meta = 0.0
                    
                category = str(row['Categoria']).strip().upper()
                
                if qty > 0:
                    portfolio.append({
                        "ticker": ticker,
                        "quantity": qty,
                        "category": category,
                        "target_pct": meta
                    })
            
            logger.info(f"Carteira carregada com sucesso: {len(portfolio)} ativos.")
            return portfolio
            
        except Exception as e:
            logger.error(f"Error reading Google Sheet: {e}")
            return []
