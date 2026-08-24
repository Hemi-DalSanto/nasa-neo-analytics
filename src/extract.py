import os
import time
import logging
from datetime import datetime, timedelta
import requests
import pandas as pd
from dotenv import load_dotenv

#Configuração do logging para exibir mensagens de log no console
logging.basicConfig(
    level=logging.INFO,
    format="|%(asctime)s [%(levelname)s] %(message)s",
    handlers= [logging.StreamHandler()]
    
)


#Carrega as variáveis do arquivo .env
load_dotenv()

API_KEY = os.getenv("NASA_API_KEY")
BASE_URL = "https://api.nasa.gov/neo/rest/v1/feed"

#INGESTÃO ISOLADA E PROTEGIDA CONTRA FALHAS DE REDE
#Esta função recebe duas datas, consulta a API da NASA de forma segura e devolver o dado bruto exatamente como ele veio do servidor, tratando qualquer instabilidade da rede sem quebrar o programa.

def fetch_neo_chunk(start_date: str, end_date: str)-> dict:
    #Validação: Se a chave não existir na memória, encerra a execução antes de abrir a conexão web
    if not API_KEY:
        raise ValueError("NASA_API_KEY não configurada no arquivo .env")
    
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "api_key": API_KEY
    }
    try:
        #Dispara a requisição HTTP do tipo GET para a API da NASA, com timeout de 15 segundos
        response= requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status()  # Levanta um erro para erros HTTP
        return response.json() #Converte o corpo da resposta em JSON e retorna como dicionário
    
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"Erro HTTP para o intervalo {start_date} a {end_date}: {http_err}")
    
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Erro de conexão: {req_err}")
    
    return {} # Retorna um dicionário vazio em caso de erro

    #FUNÇÃO QUE TRANSFORMA O JSON HIERÁRQUICO DA NASA EM UM DATAFRAME TABULAR NORMALIZADO
def parse_neo_payload(raw_data:dict)-> pd.DataFrame:
    
    records=[]
    
    #Extrai o nó central de asteroides de forma segura(.get evita KeyError)
    near_earth_objects = raw_data.get("near_earth_objects", {})
    
    #Laço 1: Percorre cada data presente no retorno
    for date_str, neo_list in near_earth_objects.items():
        #Laço 2: Percorre cada asteroide da lista de asteroides para aquela data
        for neo in neo_list:
            close_approaches = neo.get("close_approach_data", [])
            #Pega a aproximação registrada para o evento
            approach = close_approaches[0] if close_approaches else {}
            
            record = {
                "neo_reference_id": str(neo.get("id")),
                "name": neo.get("name"),
                "absolute_magnitude_h": neo.get("absolute_magnitude_h"),
                "estimated_diameter_min_km": neo.get("estimated_diameter", {}).get("kilometers", {}).get("estimated_diameter_min"),
                "estimated_diameter_max_km": neo.get("estimated_diameter", {}).get("kilometers", {}).get("estimated_diameter_max"),
                "is_potentially_hazardous_asteroid": neo.get("is_potentially_hazardous_asteroid"),
                "close_approach_date": approach.get("close_approach_date"),
                "relative_velocity_kmh": approach.get("relative_velocity", {}).get("kilometers_per_hour"),
                "miss_distance_km": approach.get("miss_distance", {}).get("kilometers"),
                "orbiting_body": approach.get("orbiting_body")
            }
            records.append(record)
    
    df = pd.DataFrame(records)
    
    if not df.empty:
        #Conversão e coerção de tipos de dados para garantir consistência
        # pd.to_numeric converte texto para float/int; errors="coerce" transforma valores corrompidos em NaN
        df["absolute_magnitude_h"] = pd.to_numeric(df["absolute_magnitude_h"], errors='coerce')
        df["estimated_diameter_min_km"] = pd.to_numeric(df["estimated_diameter_min_km"], errors='coerce')
        df["estimated_diameter_max_km"] = pd.to_numeric(df["estimated_diameter_max_km"], errors='coerce')
        df["relative_velocity_kmh"] = pd.to_numeric(df["relative_velocity_kmh"], errors='coerce')
        df["miss_distance_km"] = pd.to_numeric(df["miss_distance_km"], errors='coerce')
        # Converte a string de data para o formato datetime nativo do Pandas (Timestamp)
        df["close_approach_date"] = pd.to_datetime(df["close_approach_date"], errors='coerce')
        # Garante que a coluna de risco seja explicitamente booleana (True ou False)
        df["is_potentially_hazardous_asteroid"] = df["is_potentially_hazardous_asteroid"].astype(bool)
    # Retorna o DataFrame devidamente tipado e limpo
    return df

#FUNÇÃO Itera em janelas de 7 dias para extrair o histórico completo respeitando os limites da API.
def extract_neo_history(days_back: int=30) -> pd.DataFrame:
    #Calcula a data final como o dia de ontem (não inclui o dia atual)
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=days_back)
    
    #Ponteiro móvel que marcará o início de cada lote de 7 dias dentro do laço
    current_start = start_date
    #Lista acumuladora onde cada item será um DataFrame processado de um lote de 7 dias
    all_chunks = []
    
    logging.info(f"Iniciando extração de dados de {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
    
    #Enquanto o ponteiro de início não alcançar o final do período total
    while current_start < end_date:
        # A janela vai do current_start até 6 dias à frente (totalizando 7 dias) ou até a data limite final
        current_end = min(current_start + timedelta(days=6), end_date)
        
        # Converte os objetos de data para strings no formato exigido pela NASA ("AAAA-MM-DD")
        s_str = current_start.strftime("%Y-%m-%d")
        e_str = current_end.strftime("%Y-%m-%d")

        logging.info(f"Extraindo lote: {s_str} a {e_str}")
        
        # 1. Ingestão Bruta: busca o JSON de até 7 dias
        payload = fetch_neo_chunk(s_str, e_str)

        # 2. Transformação e Tipagem: se houver retorno válido, transforma o JSON em DataFrame
        if payload:
            df_chunk = parse_neo_payload(payload)
            # Se o DataFrame contiver dados, adiciona à lista acumuladora
            if not df_chunk.empty:
                all_chunks.append(df_chunk)

        # Avança o ponteiro de início para o dia seguinte ao término do lote atual
        current_start = current_end + timedelta(days=1)
        
        # Pausa de 500ms (Rate Limiting) para evitar bloqueio por excesso de requisições por segundo
        time.sleep(0.5)

    # Caso nenhum registro tenha sido retornado em nenhum dos lotes
    if not all_chunks:
        logging.warning("Nenhum registro retornado.")
        return pd.DataFrame()
    
    # pd.concat une verticalmente a lista de DataFrames menores em uma única tabela contínua
    # ignore_index=True renumera o índice de 0 até N de forma sequencial
    full_df = pd.concat(all_chunks, ignore_index=True)

    # Regra de integridade: remove registros com o mesmo ID de asteroide e mesma data de aproximação
    full_df = full_df.drop_duplicates(subset=["neo_reference_id", "close_approach_date"])
    
    # Registra o sucesso da extração exibindo a volumetria total de registros únicos
    logging.info(f"Extração finalizada com sucesso! Total de asteroides processados: {len(full_df)}")
    return full_df


# Ponto de entrada padrão do Python (Entrypoint)
if __name__ == "__main__":
    # Dispara a extração completa para o histórico dos últimos 30 dias
    df_result = extract_neo_history(days_back=30)
    
    # Exibe no terminal o diagnóstico estrutural do DataFrame (colunas, tipos e valores nulos)
    print("\n--- Amostra dos Dados Extraídos ---")
    print(df_result.info())
    
    # Imprime as 5 primeiras linhas da tabela limpa para inspeção visual rápida
    print(df_result.head())
        
    