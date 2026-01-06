import google.generativeai as genai
import logging
import json
from config.settings import Settings

logger = logging.getLogger(__name__)

class AIAnalyst:
    def __init__(self):
        self.api_key = Settings.GEMINI_API_KEY
        # Atualizado com os modelos confirmados no seu log de jan/2026
        self.models_to_try = [
            'gemini-2.0-flash', 
            'gemini-2.5-flash', 
            'gemini-2.0-flash-lite',
            'gemini-3-flash-preview'
        ]
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
        else:
            logger.warning("GEMINI_API_KEY não configurada. A análise de IA será pulada.")

    def _log_available_models(self):
        """Auxiliar para listar modelos disponíveis no log em caso de erro."""
        try:
            logger.info("Listando modelos Gemini disponíveis para esta chave API:")
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    logger.info(f" - {m.name}")
        except Exception as e:
            logger.warning(f"Não foi possível listar os modelos: {e}")

    def generate_ai_analysis(self, portfolio_df, total_value, indicators, news_summary):
        if not self.api_key:
            return "Análise de IA indisponível (Chave API não configurada)."

        # Formatação dos dados da carteira para o prompt
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
            
            summary_text += (f"- {item['ticker']} ({item['category']}): R$ {item['value_brl']:.2f} "
                            f"({item['allocation']:.1f}%) | L/P: {pl_pct:.2f}% (R$ {pl_val:.2f}) | "
                            f"P/L: {pe:.1f} | ROE: {roe:.1f}% | DY: {dy:.1f}% | Setor: {sector} | Rec: {rec}\n")

        system_prompt = f"""
        Você é um **Gestor de Portfólio Sênior (CFA)** e Arquiteto de Investimentos. 
        Sua missão é analisar a carteira do cliente com profundidade, usando dados fundamentalistas e o contexto de mercado atual.

        **CONTEXTO DE MERCADO (NOTÍCIAS DE HOJE):**
        {news_summary}

        **DIRETRIZES DE ANÁLISE:**
        1.  **Contexto Macro:** Explique como as notícias impactam a carteira (ex: juros vs FIIs).
        2.  **Análise Fundamentalista:** Avalie se quedas de preço são oportunidades (baseado em P/L e ROE).
        3.  **REGRA DE OURO (RENDA FIXA):** Se a categoria 'RENDA_FIXA' estiver acima da meta, NÃO sugira vender. Interprete como 'Reserva de Oportunidade'.
        4.  **Tom de Voz:** Executivo, sofisticado e direto.

        **DADOS DA CARTEIRA:**
        {summary_text}
        """

        # Tentativa iterativa com os modelos da lista
        for model_name in self.models_to_try:
            try:
                logger.info(f"Tentando análise com o modelo: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(system_prompt)
                
                if response and response.text:
                    return response.text
                
            except Exception as e:
                logger.error(f"Erro ao gerar análise com o modelo {model_name}: {e}")
                
                # Se for o último modelo da lista e falhar, retorna erro amigável
                if model_name == self.models_to_try[-1]:
                    self._log_available_models()
                    logger.error("Todos os modelos de IA falharam.")
                    return "Análise de IA temporariamente indisponível. Verifique a cota ou os modelos acessíveis."
                
                logger.info("Alternando para o próximo modelo de reserva...")
                continue