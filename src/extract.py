import os
import requests
from dotenv import load_dotenv

#Carrega as variáveis do arquivo .env
load_dotenv()

API_KEY = os.getenv("NASA_API_KEY")
URL = "https://api.nasa.gov/neo/rest/v1/feed"

#Função para testar API 
def test_api_connection():
    if not API_KEY:
        print("ERRO: API não encontrada no arquivo .env")
        return
    
    params = {
        "start_date":"2026-08-01",
        "end_date":"2026-08-03",
        "api_key" : API_KEY      
        
    }
    
    try:
        response = requests.get(URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        total_objects = data.get("element_count", 0)
        print(f" Conexão estabelecida com sucesso! Objetos encontrados no período: {total_objects}")
    except requests.exceptions.RequestException as err:
        print(f"❌ Falha na requisição: {err}")
    
if __name__ == "__main__":
    test_api_connection()
       