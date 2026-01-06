from google import genai
import logging
import json
from config.settings import Settings

logger = logging.getLogger(__name__)

class AIAnalyst:
    def __init__(self):
        self.api_key = Settings.GEMINI_API_KEY
        self.models_to_try = [
            'gemini-2.0-flash', 
            'gemini-2.5-flash', 
            'gemini-2.0-flash-lite'
        ]
        
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("GEMINI_API_KEY não configurada. A análise de IA será pulada.")

    def generate_ai_analysis(self, portfolio_df, total_value, indicators, news_summary):
        if not self.client:
            return "Análise de IA indisponível (Chave API não configurada)."

        portfolio_summary = portfolio_df.to_dict(orient='records')
        summary_text = f"Valor Total: R$ {total_value:,.2f}\n"
        summary_text += f"Indicadores: Selic {indicators.get('selic_meta')}% | CDI {indicators.get('cdi')}% | PTAX {indicators.get('ptax_venda')}\n"
        summary_text += "Ativos:\n"
        
        for item in portfolio_summary:
            summary_text += (f"- {item['ticker']} ({item['category']}): R$ {item['value_brl']:.2f} "
                            f"({item['allocation']:.1f}%) | L/P: {item.get('profit_loss_pct', 0):.2f}% | "
                            f"P/L: {item.get('pe', 0):.1f} | ROE: {item.get('roe', 0):.1f}% | Rec: {item.get('recommendation', 'N/A')}\n")

        full_prompt = f"""
        Você é um Gestor de Portfólio Sênior. Analise a carteira com base no contexto:
        
        NOTÍCIAS DO DIA:
        {news_summary}

        DADOS DA CARTEIRA:
        {summary_text}
        
        Gere uma análise direta e executiva sobre o que fazer hoje.
        """

        for model_id in self.models_to_try:
            try:
                logger.info(f"Tentando análise com o modelo: {model_id}")
                response = self.client.models.generate_content(
                    model=model_id,
                    contents=full_prompt
                )
                
                if response and response.text:
                    return response.text
                
            except Exception as e:
                logger.error(f"Erro com o modelo {model_id}: {e}")
                if model_id == self.models_to_try[-1]:
                    return "Análise de IA temporariamente indisponível (Erro de conexão/cota)."
                continue