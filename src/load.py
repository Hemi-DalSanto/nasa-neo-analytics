import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
import gspread
from google.oauth2.service_account import Credentials

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

DB_DIR = "data/processed"
DB_PATH = os.path.join(DB_DIR, "neo_database.db")
DB_URL = f"sqlite:///{DB_PATH}"

def get_db_engine():
    os.makedirs(DB_DIR, exist_ok=True)
    return create_engine(DB_URL, echo=False)

def create_indexes(engine):
    queries = [
        "CREATE INDEX IF NOT EXISTS idx_approach_date ON near_earth_objects (close_approach_date);",
        "CREATE INDEX IF NOT EXISTS idx_miss_distance ON near_earth_objects (miss_distance_km);"
    ]
    with engine.connect() as conn:
        for query in queries:
            conn.execute(text(query))
        
        result = conn.execute(text("PRAGMA table_info(near_earth_objects);"))
        columns = [row[1] for row in result.fetchall()]
        hazard_col = next((col for col in columns if "hazard" in col.lower()), None)
        if hazard_col:
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_hazard ON near_earth_objects ({hazard_col});"))
        conn.commit()

from pathlib import Path

def sync_to_google_sheets(df: pd.DataFrame) -> None:
    # Usa Pathlib para encontrar o credentials.json na raiz do projeto com segurança no Windows
    base_dir = Path(__file__).resolve().parent.parent
    creds_file = base_dir / "credentials.json"
    
    if not creds_file.exists():
        logging.warning(f"Arquivo 'credentials.json' não encontrado em: {creds_file}")
        return
        
    spreadsheet_id = "1ehMUVxJItVXiAxDWAlUDsK5LpBc_iemmTMTA16raAEw"

    # COLE AQUI O ID DA SUA PLANILHA DO GOOGLE SHEETS (o trecho entre /d/ e /edit da URL)
    spreadsheet_id = "1ehMUVxJItVXiAxDWAlUDsK5LpBc_iemmTMTA16raAEw"
    
    if spreadsheet_id == "":
        logging.warning("ID da planilha do Google Sheets não configurado em src/load.py.")
        return

    try:
        logging.info("Autenticando na API do Google Sheets...")
        creds = Credentials.from_service_account_file(str(creds_file), scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        gc = gspread.authorize(creds)

        logging.info("Abrindo a planilha na nuvem...")
        sheet = gc.open_by_key(spreadsheet_id).sheet1

        # Converte datas para string para evitar erros de serialização do JSON
        df_to_upload = df.copy()
        if "close_approach_date" in df_to_upload.columns:
            df_to_upload["close_approach_date"] = df_to_upload["close_approach_date"].astype(str)

        logging.info("Limpando e atualizando dados na planilha...")
        sheet.clear()
        
        data_to_write = [df_to_upload.columns.tolist()] + df_to_upload.fillna("").values.tolist()
        sheet.update(data_to_write)
        
        logging.info("Planilha do Google Sheets atualizada com sucesso via pipeline!")
    except Exception as e:
        logging.error(f"Erro ao sincronizar com o Google Sheets: {e!r}", exc_info=True)

def load_to_database(df: pd.DataFrame, if_exists: str = "replace") -> None:
    if df.empty:
        logging.warning("DataFrame vazio. Nenhuma carga executada.")
        return

    engine = get_db_engine()
    
    # 1. Salva no banco SQLite local
    logging.info(f"Salvando {len(df)} registros na tabela local 'near_earth_objects'...")
    df.to_sql("near_earth_objects", con=engine, if_exists=if_exists, index=False)
    create_indexes(engine)
    
    # 2. Sincroniza automaticamente com o Google Sheets na nuvem
    sync_to_google_sheets(df)
    
    logging.info("Processo de carga local e em nuvem concluído!")