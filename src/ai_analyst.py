import google.generativeai as genai
import logging
import json
from config.settings import Settings

logger = logging.getLogger(__name__)

class AIAnalyst:
    def __init__(self):
        self.api_key = Settings.GEMINI_API_KEY
        self.models_to_try = ['gemini-2.5-pro', 'gemini-2.0-flash']
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
        else:
            logger.warning("GEMINI_API_KEY not set. AI Analysis will be skipped.")

    def _log_available_models(self):
        """Helper to log available models for debugging."""
        try:
            logger.info("Listing available Gemini models for this API key:")
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    logger.info(f" - {m.name}")
        except Exception as e:
            logger.warning(f"Could not list models: {e}")

    def generate_ai_analysis(self, portfolio_df, total_value, indicators):
        if not self.api_key:
            return "Análise de IA indisponível (Chave API não configurada)."

        # Prepare Data for AI
        portfolio_summary = portfolio_df.to_dict(orient='records')
        
        # Create a simplified summary to save tokens and focus attention
        summary_text = f"Valor Total: R$ {total_value:,.2f}\n"
        summary_text += f"Indicadores: Selic {indicators.get('selic_meta')}% | CDI {indicators.get('cdi')}% | PTAX {indicators.get('ptax_venda')}\n"
        summary_text += "Ativos:\n"
        for item in portfolio_summary:
            summary_text += f"- {item['ticker']} ({item['category']}): R$ {item['value_brl']:.2f} ({item['allocation']:.1f}%)\n"

        system_prompt = """
        Você é um analista financeiro extremamente rigoroso, crítico e orientado à verdade.
        Sua função é avaliar o desempenho da carteira do investidor diariamente.
        Você deve questionar suposições, apontar pontos cegos e destacar riscos.
        Fale de forma direta, madura e sem buscar agradar.
        Regras:
        1. Não use valores históricos manuais, analise o snapshot atual fornecido.
        2. Resumo Geral obrigatório: Valor total, peso por classe, ganhos/perdas.
        3. Aponte riscos: Exposição concentrada, sensibilidade ao ciclo econômico.
        4. Insights: "Oportunidades para estudar", "Alertas reais".
        5. Nunca elogie a carteira. Seja um analista crítico, não um torcedor.
        """

        full_prompt = f"{system_prompt}\n\nDados da Carteira:\n{summary_text}"

        for model_name in self.models_to_try:
            try:
                logger.info(f"Attempting AI analysis with model: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(full_prompt)
                return response.text
            except Exception as e:
                logger.error(f"Error generating analysis with {model_name}: {e}")
                
                # Log available models to help user debug 404s
                self._log_available_models()
                
                if model_name == self.models_to_try[-1]:
                    # If this was the last model, return a friendly error
                    logger.error("All AI models failed.")
                    return "Análise de IA temporariamente indisponível. Verifique os logs para detalhes dos modelos acessíveis."
                else:
                    logger.info("Switching to fallback model...")
                    continue
