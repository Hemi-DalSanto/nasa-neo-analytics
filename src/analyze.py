import sqlite3
import pandas as pd

DB_PATH = "data/processed/neo_database.db"

def run_queries():
    conn = sqlite3.connect(DB_PATH)
    
    queries = {
        "1. Resumo de Risco": """
            SELECT 
                COUNT(*) AS total_asteroids,
                SUM(CASE WHEN is_potentially_hazardous_asteroid = 1 THEN 1 ELSE 0 END) AS hazardous_count,
                ROUND((SUM(CASE WHEN is_potentially_hazardous_asteroid = 1 THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 2) AS hazardous_percentage
            FROM near_earth_objects;
        """,
        "2. Top 3 Aproximações Mais Próximas": """
            SELECT name, close_approach_date, ROUND(miss_distance_km, 2) as miss_distance_km, is_potentially_hazardous_asteroid
            FROM near_earth_objects
            ORDER BY miss_distance_km ASC
            LIMIT 3;
        """
    }
    
    for title, query in queries.items():
        print(f"\n--- {title} ---")
        df = pd.read_sql(query, conn)
        print(df.to_string(index=False))
        
    conn.close()

if __name__ == "__main__":
    run_queries()