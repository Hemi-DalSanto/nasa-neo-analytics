import logging
from src.extract import extract_neo_history
from src.load import load_to_database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def run_pipeline(days_back: int = 60):
    """
    Executa o pipeline completo:
    1. Extração da API da NASA (em lotes de 7 dias)
    2. Transformação e tratamento de tipos
    3. Carga no banco de dados relacional SQLite
    """
    logging.info("=== INICIANDO PIPELINE DE DADOS NEO NASA ===")
    
    # 1 e 2: Extrair e Transformar
    df_clean = extract_neo_history(days_back=days_back)
    
    # 3: Carregar
    if not df_clean.empty:
        load_to_database(df_clean, if_exists="replace")
        logging.info("=== PIPELINE EXECUTADO COM SUCESSO! ===")
    else:
        logging.error("Falha na execução: dados não foram carregados.")

if __name__ == "__main__":
    # Extrair os últimos 60 dias para termos uma massa de dados consistente
    run_pipeline(days_back=60)