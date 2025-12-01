import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class Settings:
    # E-mail (Credenciais carregadas do .env)
    EMAIL_SENDER = os.getenv("EMAIL_SENDER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

    # WhatsApp (Credenciais carregadas do .env)
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
    WHATSAPP_TO_NUMBER = os.getenv("WHATSAPP_TO_NUMBER")

    # IA (Gemini)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # App
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Ativos (Mapeamento para Yahoo Finance)
    ASSETS = {
        "BR_STOCKS": ["BBAS3.SA", "SAPR3.SA", "SAPR4.SA", "LWSA3.SA"],
        "FIIS": ["XPML11.SA", "KFOF11.SA", "RBRR11.SA", "HCTR11.SA", "IRDM11.SA", "VINO11.SA"],
        "ETFS": ["B5P211.SA", "PACB11.SA", "FIXA11.SA", "GOLD11.SA", "XINA11.SA"],
        "US_REITS": ["O"],
        "US_STOCKS": ["HPQ"],
        "CRYPTO": ["USDT-USD"]
    }

    # Quantidades (Sua Carteira Atual)
    PORTFOLIO_QTY = {
        # Ações BR
        "BBAS3.SA": 37, 
        "SAPR3.SA": 5, 
        "SAPR4.SA": 2, 
        "LWSA3.SA": 1,
        # FIIs
        "XPML11.SA": 3,
        "KFOF11.SA": 3,
        "RBRR11.SA": 2,
        "HCTR11.SA": 7,
        "IRDM11.SA": 2, 
        "VINO11.SA": 2,
        # ETFs
        "B5P211.SA": 2, 
        "PACB11.SA": 12, 
        "FIXA11.SA": 5, 
        "GOLD11.SA": 3, 
        "XINA11.SA": 1,
        # Exterior
        "O": 0.93, 
        "HPQ": 1.82931885,
        # Cripto
        "USDT-USD": 37.94885362
    }
    
    # Alocação Ideal Atualizada
    TARGET_ALLOCATION = {
        "Renda Fixa": 0.35,  # 35%
        "Ações BR": 0.20,    # 20%
        "ETFs": 0.15,        # 15%
        "FIIs": 0.10,        # 10%
        "REITs": 0.07,       # 7%
        "Ações EUA": 0.07,   # 7%
        "Cripto": 0.06       # 6%
    }