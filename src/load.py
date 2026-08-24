import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

DB_DIR = "data/processed"
DB_PATH = os.path.join(DB_DIR, "neo_database.db")
DB_URL = f"sqlite:///{DB_PATH}"


def get_db_engine():
    """Cria e retorna a engine do SQLAlchemy para o SQLite local."""
    os.makedirs(DB_DIR, exist_ok=True)
    return create_engine(DB_URL, echo=False)


def create_indexes(engine):
    """Cria índices para otimizar consultas analíticas frequentes com tratamento de segurança."""
    queries = [
        "CREATE INDEX IF NOT EXISTS idx_approach_date ON near_earth_objects (close_approach_date);",
        "CREATE INDEX IF NOT EXISTS idx_miss_distance ON near_earth_objects (miss_distance_km);"
    ]
    with engine.connect() as conn:
        for query in queries:
            conn.execute(text(query))
        
        # Validação dinâmica para o campo booleano de perigo
        result = conn.execute(text("PRAGMA table_info(near_earth_objects);"))
        columns = [row[1] for row in result.fetchall()]
        
        hazard_col = next((col for col in columns if "hazard" in col.lower()), None)
        if hazard_col:
            idx_query = f"CREATE INDEX IF NOT EXISTS idx_hazard ON near_earth_objects ({hazard_col});"
            conn.execute(text(idx_query))
            logging.info(f"Índice criado com sucesso para a coluna de risco: {hazard_col}")
        else:
            logging.warning("Coluna de perigo não encontrada para indexação automática.")
            
        conn.commit()
    logging.info("Verificação de índices concluída.")

def load_to_database(df: pd.DataFrame, if_exists: str = "replace") -> None:
    """
    Grava o DataFrame tratado na tabela 'near_earth_objects' e aplica índices.
    """
    if df.empty:
        logging.warning("DataFrame vazio. Nenhuma carga executada.")
        return

    engine = get_db_engine()
    
    # Gravando no SQLite
    logging.info(f"Salvando {len(df)} registros na tabela 'near_earth_objects'...")
    df.to_sql("near_earth_objects", con=engine, if_exists=if_exists, index=False)
    
    # Criando índices analíticos
    create_indexes(engine)
    logging.info("Carga no banco de dados concluída com sucesso!")


if __name__ == "__main__":
    # Teste rápido de leitura do banco
    engine = get_db_engine()
    if os.path.exists(DB_PATH):
        sample_df = pd.read_sql("SELECT COUNT(*) as total_records FROM near_earth_objects", con=engine)
        print("Total de registros no banco:", sample_df.iloc[0]["total_records"])
    else:
        print("Banco de dados ainda não foi criado.")