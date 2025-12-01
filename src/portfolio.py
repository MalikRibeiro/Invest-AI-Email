import pandas as pd
import json
import os
from datetime import datetime
from config.settings import Settings
import logging

logger = logging.getLogger(__name__)

class PortfolioManager:
    def __init__(self, market_data, indicators):
        self.market_data = market_data
        self.indicators = indicators
        self.quantities = Settings.PORTFOLIO_QTY
        self.target_alloc = Settings.TARGET_ALLOCATION
        self.assets_map = Settings.ASSETS
        self.state_file = "data/portfolio_state.json"
        
        # Ensure data dir exists
        os.makedirs("data", exist_ok=True)

    def _get_rdb_value(self):
        """Calculates updated RDB value based on CDI."""
        # Default initial value if not exists (User should update this in json)
        default_state = {
            "rdb_value": 1000.00, # Placeholder
            "last_update": datetime.now().strftime("%Y-%m-%d")
        }
        
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                state = json.load(f)
        else:
            state = default_state
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        
        last_date = datetime.strptime(state["last_update"], "%Y-%m-%d")
        today = datetime.now()
        
        # Calculate days passed (business days would be better, but using calendar days for simplicity or need a calendar lib)
        # For CDI, it's usually business days (252/year).
        # Simple approximation: Daily rate applied for business days difference.
        # I'll just apply the daily factor for now if the date changed.
        
        if today.date() > last_date.date():
            # Get CDI daily rate (approx from Selic Meta)
            selic_meta = self.indicators.get('selic_meta', 11.75) # Fallback
            cdi_yearly = selic_meta - 0.10
            # Daily factor (1 + CDI)^(1/252) - 1
            # RDB is 115% of CDI
            daily_cdi = (1 + cdi_yearly/100)**(1/252) - 1
            daily_rdb = daily_cdi * 1.15
            
            days_diff = (today - last_date).days # This is calendar days. 
            # Ideally we check business days. For MVP, assuming every weekday run.
            # If run daily, days_diff is 1.
            
            # Update value
            new_value = state["rdb_value"] * ((1 + daily_rdb) ** days_diff) # Rough approx for weekends
            
            state["rdb_value"] = new_value
            state["last_update"] = today.strftime("%Y-%m-%d")
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
                
            return new_value
        else:
            return state["rdb_value"]

    def calculate_portfolio(self):
        portfolio = []
        total_value = 0
        
        # 1. Process Tickers
        for ticker, qty in self.quantities.items():
            if ticker == "USDT-BRL": 
                # Special handling for USDT if needed, but it's in market_data
                pass
                
            data = self.market_data.get(ticker, {})
            price = data.get('price', 0)
            
            # Determine Category
            category = "OUTROS"
            for cat, tickers in self.assets_map.items():
                if ticker in tickers:
                    category = cat
                    break
            if ticker == "USDT-BRL" or ticker == "USDT-USD": category = "CRYPTO"
            
            # Currency Conversion
            # If category is Crypto or ticker ends with -USD, convert to BRL
            if category in ["US_REITS", "US_STOCKS", "CRYPTO"] or ticker.endswith("-USD"):
                usd_rate = self.market_data.get('BRL=X', {}).get('price', 5.0)
                if usd_rate == 0: usd_rate = 5.0 # Fallback
                
                # If it's already in BRL (like USDT-BRL), don't multiply
                if ticker.endswith("-BRL"):
                    value_brl = price * qty
                else:
                    value_brl = price * qty * usd_rate
            else:
                value_brl = price * qty
                
            if price == 0:
                logger.warning(f"Price for {ticker} is 0. Check data source.")

            total_value += value_brl
            
            portfolio.append({
                "ticker": ticker,
                "qty": qty,
                "price": price,
                "value_brl": value_brl,
                "category": category,
                "name": data.get('name', ticker),
                "dy_12m": data.get('dy_12m', 0),
                "p_vp": data.get('p_vp', 0),
                "change_1d": data.get('change_1d', 0),
                "change_12m": data.get('change_12m', 0)
            })
            
        # 2. Process RDB (Fixed Income)
        rdb_val = self._get_rdb_value()
        portfolio.append({
            "ticker": "RDB Nubank",
            "qty": 1,
            "price": rdb_val,
            "value_brl": rdb_val,
            "category": "RENDA_FIXA", # Internal name
            "name": "RDB Nubank 115% CDI",
            "dy_12m": 0,
            "p_vp": 0,
            "change_1d": 0,
            "change_12m": 0
        })
        total_value += rdb_val
        
        df = pd.DataFrame(portfolio)
        df['allocation'] = (df['value_brl'] / total_value) * 100
        
        return df, total_value

    def get_rebalancing_suggestions(self, df, total_value):
        # Map internal categories to Target Allocation keys
        cat_map = {
            "BR_STOCKS": "Ações BR",
            "FIIS": "FIIs",
            "ETFS": "ETFs",
            "US_REITS": "REITs",
            "US_STOCKS": "Ações EUA",
            "CRYPTO": "Cripto",
            "RENDA_FIXA": "Renda Fixa"
        }
        
        # Group by category
        df['target_cat'] = df['category'].map(cat_map)
        current_alloc = df.groupby('target_cat')['value_brl'].sum() / total_value
        
        suggestions = []
        
        for cat, target_pct in self.target_alloc.items():
            current_pct = current_alloc.get(cat, 0.0)
            diff = (current_pct * 100) - (target_pct * 100)
            
            status = "OK"
            if diff > 5:
                status = "VENDER"
            elif diff < -5:
                status = "COMPRAR"
                
            suggestions.append({
                "category": cat,
                "current_pct": current_pct * 100,
                "target_pct": target_pct * 100,
                "diff": diff,
                "status": status
            })
            
        return pd.DataFrame(suggestions)

    def suggest_contribution(self, amount, df_suggestions):
        # Simple logic: Distribute amount to categories with biggest negative deviation (COMPRAR)
        # Prioritize Variable Income if RF > 40% (User rule: "priorizar variável enquanto RF >40%")
        
        # Check RF allocation
        rf_row = df_suggestions[df_suggestions['category'] == "Renda Fixa"]
        rf_pct = rf_row['current_pct'].values[0] if not rf_row.empty else 0
        
        # Filter candidates
        candidates = df_suggestions[df_suggestions['diff'] < 0].copy()
        
        if rf_pct > 40:
            # Exclude RF from contributions
            candidates = candidates[candidates['category'] != "Renda Fixa"]
            
        if candidates.empty:
            return "Nenhuma sugestão específica (alocação equilibrada)."
            
        # Distribute proportionally to the "gap"
        total_gap = candidates['diff'].abs().sum()
        candidates['contribution'] = (candidates['diff'].abs() / total_gap) * amount
        
        return candidates[['category', 'contribution']]
