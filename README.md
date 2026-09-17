# 🌠 NASA NEO Analytics

Pipeline de dados ponta a ponta que extrai informações de **asteroides próximos da Terra (Near Earth Objects)** direto da API pública da NASA, transforma e armazena os dados em um banco relacional, sincroniza automaticamente com o Google Sheets e alimenta um dashboard analítico no Looker Studio.

> Projeto pessoal desenvolvido para consolidar prática de ETL, engenharia de dados e visualização — do consumo de uma API real até a entrega de um dashboard de portfólio.

---

## 📊 Visão geral do pipeline

```
NASA NeoWs API  →  Extract (requests)  →  Transform (pandas)  →  Load
                                                                    │
                                        ┌───────────────────────────┴───────────────────────────┐
                                        ▼                                                        ▼
                              SQLite (data/processed)                                   Google Sheets (nuvem)
                                        │                                                        │
                                        ▼                                                        ▼
                                SQL Analytics (sql/)                                     Looker Studio Dashboard
```

1. **Extract** — consulta a [API NeoWs da NASA](https://api.nasa.gov/) em lotes de 7 dias (limite da própria API), com tratamento de falhas de rede e *rate limiting*.
2. **Transform** — normaliza o JSON aninhado da NASA em um DataFrame tabular, com tipagem correta (datas, floats, booleanos) e remoção de duplicatas.
3. **Load** — grava os dados em um banco **SQLite** local e sincroniza a mesma base automaticamente em uma planilha do **Google Sheets**, via API do Google.
4. **Analyze** — consultas SQL prontas (`sql/risk_analysis.sql`) para análise de risco, padrões temporais e ranking de aproximações críticas.
5. **Visualize** — a planilha do Google Sheets alimenta um dashboard no **Looker Studio**.

---

## 🛠️ Stack utilizada

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3 |
| Extração de dados | `requests` |
| Transformação | `pandas` |
| Banco de dados local | `SQLite` via `SQLAlchemy` |
| Sincronização em nuvem | `gspread` + `google-auth` (Google Sheets API) |
| Configuração de ambiente | `python-dotenv` |
| Análise | SQL (SQLite) |
| Visualização | Google Looker Studio |

---

## 📁 Estrutura do projeto

```
nasa-neo-analytics/
├── main.py                    # Orquestra o pipeline completo (extract → load)
├── src/
│   ├── extract.py             # Consome a API da NASA e trata/normaliza o JSON
│   ├── load.py                 # Grava no SQLite e sincroniza com Google Sheets
│   └── analyze.py              # Executa queries de análise direto no terminal
├── sql/
│   └── risk_analysis.sql       # Queries de análise de risco e padrões temporais
├── data/
│   ├── raw/                    # (reservado para dumps brutos, se necessário)
│   └── processed/
│       └── neo_database.db     # Banco SQLite gerado pelo pipeline
├── credentials.json             # Credenciais da conta de serviço do Google (não versionar)
├── .env                          # Variáveis de ambiente (não versionar)
├── .env.example                  # Modelo das variáveis de ambiente necessárias
└── requirements.txt              # Dependências do projeto
```

---

## 🚀 Como rodar o projeto

### 1. Clone o repositório e crie o ambiente virtual

```bash
git clone https://github.com/seu-usuario/nasa-neo-analytics.git
cd nasa-neo-analytics
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure sua chave da API da NASA

Crie uma chave gratuita em [api.nasa.gov](https://api.nasa.gov/) e copie o arquivo de exemplo:

```bash
cp .env.example .env
```

Edite o `.env` e preencha:

```
NASA_API_KEY=sua_chave_aqui
```

### 4. Configure a sincronização com o Google Sheets (opcional)

1. Crie um projeto no [Google Cloud Console](https://console.cloud.google.com/).
2. Ative a **Google Sheets API** e a **Google Drive API**.
3. Crie uma conta de serviço, gere uma chave em JSON e salve-a na raiz do projeto como `credentials.json`.
4. Compartilhe sua planilha do Google Sheets com o e-mail da conta de serviço (permissão de **Editor**).
5. Copie o ID da planilha (trecho da URL entre `/d/` e `/edit`) e configure em `src/load.py`, na variável `spreadsheet_id`.

> Se você pular esta etapa, o pipeline continua funcionando normalmente — os dados apenas não serão sincronizados com a nuvem, só ficam salvos localmente no SQLite.

### 5. Execute o pipeline

```bash
python main.py
```

Isso vai extrair os últimos 60 dias de dados, salvar em `data/processed/neo_database.db` e sincronizar com o Google Sheets (se configurado).

### 6. Rode as análises

```bash
python src/analyze.py
```

Ou explore livremente as queries em `sql/risk_analysis.sql` em qualquer cliente SQLite.

---

## 📈 Análises disponíveis

| Query | O que responde |
|---|---|
| **Resumo de risco** | Total de asteroides monitorados, quantos são potencialmente perigosos e o percentual de risco da base |
| **Padrão temporal** | Quantidade de asteroides únicos, velocidade média e menor distância de aproximação por mês |
| **Top alvos críticos** | Ranking dos 5 eventos com menor distância combinada a maior velocidade relativa |

---

## 🖥️ Dashboard

Os dados sincronizados no Google Sheets alimentam um dashboard no Looker Studio com:
- KPIs de resumo (total monitorado, % de risco, diâmetro e velocidade médios/máximos)
- Tendência de aproximações ao longo do tempo
- Gráfico de dispersão (diâmetro × velocidade, colorido por risco)
- Ranking das aproximações mais próximas
- Distribuição de tamanhos e padrão por dia da semana

🔗 *[Link do dashboard aqui]*

---

## 🗺️ Próximos passos

- [ ] Agendamento automático do pipeline (cron / Task Scheduler / GitHub Actions)
- [ ] Testes automatizados para as funções de extração e transformação
- [ ] Deploy do pipeline em nuvem (ex: Cloud Functions / AWS Lambda)
- [ ] Migração do SQLite para um banco na nuvem (ex: BigQuery) para consultas mais robustas

---

## 👩‍💻 Autora

**Hemilinei Talita Dal Santo**
Estudante de Ciência da Computação (UFU) | Analista de Inteligência de Dados/Tecnologia no Instituto Semear

