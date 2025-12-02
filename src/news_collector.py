from GoogleNews import GoogleNews
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NewsCollector:
    def __init__(self):
        self.googlenews = GoogleNews(lang='pt', region='BR')
        
    def get_top_news(self):
        """
        Busca as top 5 notícias sobre 'Mercado Financeiro' e 'Ibovespa'.
        Retorna uma string formatada com as manchetes.
        """
        try:
            logger.info("Buscando notícias do mercado financeiro...")
            self.googlenews.clear()
            
            # Busca combinada para ter um contexto geral
            self.googlenews.search('Mercado Financeiro Ibovespa')
            results = self.googlenews.result()
            
            # Filtra e formata
            top_news = []
            seen_titles = set()
            
            for news in results:
                title = news.get('title')
                date = news.get('date')
                link = news.get('link')
                
                # Evita duplicatas e notícias muito antigas (embora a busca seja recente)
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    top_news.append(f"- {title} ({date})")
                
                if len(top_news) >= 5:
                    break
            
            if not top_news:
                return "Nenhuma notícia relevante encontrada hoje."
                
            return "\n".join(top_news)

        except Exception as e:
            logger.error(f"Erro ao buscar notícias: {e}")
            return "Erro ao buscar notícias."
