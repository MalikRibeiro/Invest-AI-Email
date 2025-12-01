# Invest-AI: Automação Financeira Diária

Este projeto automatiza a coleta de dados financeiros, cálculo de portfólio e envio de relatórios diários via E-mail e WhatsApp.

## Funcionalidades

- **Coleta de Dados**: Preços de Ações, FIIs, ETFs, REITs, Stocks e Cripto via Yahoo Finance.
- **Indicadores Econômicos**: Selic, CDI e PTAX via API do Banco Central.
- **Gestão de Portfólio**: Cálculo de valor total, alocação por categoria e sugestões de rebalanceamento.
- **Renda Fixa**: Atualização automática do valor do RDB Nubank (115% do CDI).
- **Relatórios**: Geração de relatório em Markdown e PDF.
- **Notificações**: Envio automático via E-mail (SMTP) e WhatsApp (Twilio).
- **Agendamento**: Execução automática todos os dias úteis às 19:00.

## Instalação

1.  **Clone o repositório** ou baixe os arquivos.
2.  **Instale as dependências**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure as variáveis de ambiente**:
    - Copie o arquivo `.env.example` para `.env`:
      ```bash
      cp .env.example .env
      ```
    - Edite o arquivo `.env` com suas credenciais de E-mail e Twilio (opcional).

## Configuração

- **Ativos e Quantidades**: Edite o arquivo `config/settings.py` para ajustar sua carteira (tickers e quantidades) e sua alocação ideal.
- **Renda Fixa**: O valor inicial do RDB é gerenciado em `data/portfolio_state.json`. O sistema cria este arquivo automaticamente na primeira execução com um valor padrão. Você pode editar este arquivo manualmente para ajustar o saldo inicial correto.

## Execução

### Teste Manual
Para rodar o robô imediatamente (teste):
```bash
python main.py --test
```

### Execução Automática (Agendada)
Para deixar o robô rodando e aguardando o horário (19:00):
```bash
python main.py
```

### Agendamento no Windows (Recomendado)
Em vez de deixar o terminal aberto, você pode usar o **Agendador de Tarefas do Windows**:
1.  Abra o Agendador de Tarefas.
2.  Crie uma nova tarefa básica.
3.  Defina o disparador para "Diariamente" às 19:00.
4.  Na ação, escolha "Iniciar um programa".
5.  Programa/Script: `python` (ou o caminho completo do seu python.exe).
6.  Argumentos: `main.py --test` (Use `--test` para que ele execute uma vez e feche, já que o agendador do Windows cuida do horário).
7.  Iniciar em: Caminho da pasta do projeto.

## Logs
Os logs de execução são salvos em `logs/app.log`.
