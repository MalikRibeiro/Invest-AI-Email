import yfinance as yf
import pandas as pd
import requests
from datetime import datetime
import logging
from config.settings import Settings

logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self):
        self.tickers = []
        for category, items in Settings.ASSETS.items():
            self.tickers.extend(items)
        # Add USD/BRL explicitly if not in list
        if "BRL=X" not in self.tickers:
            self.tickers.append("BRL=X")

    def get_market_data(self):
        """Fetches prices, variations, and fundamentals for all assets."""
        logger.info("Fetching market data for tickers: %s", self.tickers)
        results = {}
        
        # Fetch data one by one to ensure we get 'info' for fundamentals
        # Bulk download is faster for prices but doesn't give 'info'
        
        for ticker in self.tickers:
            try:
                logger.info(f"Processing {ticker}...")
                stock = yf.Ticker(ticker)
                
                # Get history for price and variation
                hist = stock.history(period="1y")
                
                if hist.empty:
                    logger.warning(f"No history found for {ticker}")
                    results[ticker] = {
                        "price": 0.0,
                        "change_1d": 0.0,
                        "change_12m": 0.0,
                        "dy_12m": 0.0,
                        "p_vp": 0.0
                    }
                    continue

                current_price = hist['Close'].iloc[-1]
                
                # 1D Variation
                if len(hist) >= 2:
                    prev_close = hist['Close'].iloc[-2]
                    change_1d = ((current_price - prev_close) / prev_close) * 100
                else:
                    change_1d = 0.0
                    
                # 12M Variation
                if len(hist) > 0:
                    price_12m_ago = hist['Close'].iloc[0]
                    change_12m = ((current_price - price_12m_ago) / price_12m_ago) * 100
                else:
                    change_12m = 0.0

                # Fundamentals
                # Note: yfinance info is sometimes slow or incomplete
                try:
                    info = stock.info
                    dy = info.get('dividendYield', 0)
                    if dy is None: dy = 0
                    dy = dy * 100 # Convert to percentage
                    
                    p_vp = info.get('priceToBook', 0)
                    if p_vp is None: p_vp = 0
                except Exception as e:
                    logger.warning(f"Could not fetch info for {ticker}: {e}")
                    dy = 0
                    p_vp = 0

                results[ticker] = {
                    "price": current_price,
                    "change_1d": change_1d,
                    "change_12m": change_12m,
                    "dy_12m": dy,
                    "p_vp": p_vp,
                    "name": info.get('shortName', ticker)
                }
                
            except Exception as e:
                logger.error(f"Error fetching data for {ticker}: {e}")
                results[ticker] = {
                    "price": 0.0, "change_1d": 0.0, "change_12m": 0.0, "dy_12m": 0.0, "p_vp": 0.0
                }

        return results

    def get_economic_indicators(self):
        """Fetches Selic, CDI, and PTAX from BCB API."""
        indicators = {}
        today = datetime.now().strftime("%d/%m/%Y")
        
        # BCB API Endpoints
        # Selic Meta (432)
        try:
            url_selic = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
            r_selic = requests.get(url_selic, timeout=10)
            if r_selic.status_code == 200:
                indicators['selic_meta'] = float(r_selic.json()[0]['valor'])
            else:
                indicators['selic_meta'] = 0.0
        except Exception as e:
            logger.error(f"Error fetching Selic: {e}")
            indicators['selic_meta'] = 0.0

        # CDI (12) - Daily rate, usually very small. 
        # For "CDI do dia", users usually mean the annualized rate or the daily factor.
        # Let's fetch the accumulated CDI (4389) or just use Selic as proxy if needed.
        # Actually, let's fetch the daily rate (12) and annualized it roughly or just show it.
        # Better: Fetch CDI Annualized (Accumulated in month/year is harder).
        # Let's stick to Selic Meta as the main benchmark.
        # Or try to get CDI from another source if needed.
        # For now, I'll use Selic Meta as the main "CDI" proxy if CDI API fails or is confusing.
        indicators['cdi'] = indicators['selic_meta'] - 0.10 # Approximation

        # PTAX (USD)
        # https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarDia(dataCotacao=@dataCotacao)?@dataCotacao='MM-DD-YYYY'
        # This API requires exact date and valid business day. It's flaky for "today" if run before closing.
        # I will use yfinance 'BRL=X' as the primary source for USD price in the market data section.
        # But for "PTAX Oficial", I'll try the API.
        try:
            # Try to get PTAX from the last available day
            url_ptax = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)?@dataInicial='{}'&@dataFinalCotacao='{}'&$top=1&$orderby=dataHoraCotacao%20desc&$format=json".format(
                (datetime.now() - pd.Timedelta(days=5)).strftime('%m-%d-%Y'),
                datetime.now().strftime('%m-%d-%Y')
            )
            r_ptax = requests.get(url_ptax, timeout=10)
            if r_ptax.status_code == 200:
                data = r_ptax.json()
                if 'value' in data and len(data['value']) > 0:
                    indicators['ptax_venda'] = data['value'][0]['cotacaoVenda']
                else:
                    indicators['ptax_venda'] = 0.0
            else:
                indicators['ptax_venda'] = 0.0
        except Exception as e:
            logger.error(f"Error fetching PTAX: {e}")
            indicators['ptax_venda'] = 0.0

        return indicators
