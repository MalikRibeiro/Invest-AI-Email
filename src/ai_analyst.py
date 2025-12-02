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

    def generate_ai_analysis(self, portfolio_df, total_value, indicators, news_summary):
        if not self.api_key:
            return "Análise de IA indisponível (Chave API não configurada)."
        portfolio_summary = portfolio_df.to_dict(orient='records')

        summary_text = f"Valor Total: R$ {total_value:,.2f}\n"
        summary_text += f"Indicadores: Selic {indicators.get('selic_meta')}% | CDI {indicators.get('cdi')}% | PTAX {indicators.get('ptax_venda')}\n"
        summary_text += "Ativos:\n"
        for item in portfolio_summary:
            pl_pct = item.get('profit_loss_pct', 0.0)
            pl_val = item.get('profit_loss_val', 0.0)
            pe = item.get('pe', 0)
            roe = item.get('roe', 0)
            dy = item.get('dy_12m', 0)
            sector = item.get('sector', 'N/A')
            rec = item.get('recommendation', 'N/A')
            
            summary_text += f"- {item['ticker']} ({item['category']}): R$ {item['value_brl']:.2f} ({item['allocation']:.1f}%) | L/P: {pl_pct:.2f}% (R$ {pl_val:.2f}) | P/L: {pe:.1f} | ROE: {roe:.1f}% | DY: {dy:.1f}% | Setor: {sector} | Rec: {rec}\n"

        system_prompt = """
        Você é um **Gestor de Portfólio Sênior (CFA)** e Arquiteto de Investimentos. 
        Sua missão é analisar a carteira do cliente com profundidade, usando dados fundamentalistas e o contexto de mercado atual.

        **CONTEXTO DE MERCADO (NOTÍCIAS DE HOJE):**
        {news_summary}

        **DIRETRIZES DE ANÁLISE:**
        1.  **Contexto Macro:** Comece explicando brevemente como as notícias de hoje (acima) impactam a carteira (ex: alta de juros impactando FIIs/Varejo).
        2.  **Análise Fundamentalista:** Não olhe apenas preço. Se um ativo caiu, verifique seus fundamentos (P/L, ROE). 
            - Exemplo: "A queda de X% em BBAS3 parece injustificada dado seu P/L de Y e ROE de Z%, sugerindo oportunidade."
            - Exemplo: "A queda em HCTR11 preocupa devido à perda de fundamentos..."
        3.  **REGRA DE OURO PARA ALOCAÇÃO (RENDA FIXA):**
            - Se a categoria 'RENDA_FIXA' estiver acima da meta (ex: 40% vs 35%), **NÃO SUGIRA VENDER**. 
            - Interprete esse excesso como **'Reserva de Oportunidade' (Dry Powder)** para aproveitar quedas na bolsa.
            - Apenas sugira venda de Renda Fixa se o usuário precisar de liquidez imediata, caso contrário, mantenha.
            - Sugira venda apenas de ativos de risco (Ações/FIIs) se perderem fundamento ou subiram demais injustificadamente.
        4.  **Tom de Voz:** Executivo, direto, sofisticado, mas claro. Evite clichês genéricos.

        **DADOS DA CARTEIRA:**
        {summary_text}
        """

        full_prompt = system_prompt.format(news_summary=news_summary, summary_text=summary_text)

        for model_name in self.models_to_try:
            try:
                logger.info(f"Attempting AI analysis with model: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(full_prompt)
                return response.text
            except Exception as e:
                logger.error(f"Error generating analysis with {model_name}: {e}")
                self._log_available_models()
                
                if model_name == self.models_to_try[-1]:
                    logger.error("All AI models failed.")
                    return "Análise de IA temporariamente indisponível. Verifique os logs para detalhes dos modelos acessíveis."
                else:
                    logger.info("Switching to fallback model...")
                    continue
