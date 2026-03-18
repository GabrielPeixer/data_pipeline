# Data Pipeline – Dados da B3

Pipeline de dados serverless na AWS para coleta, ingestão e transformação de ações e índices da Bolsa de Valores do Brasil (B3).

## Arquitetura

```
EventBridge (diário) → Lambda Scraper → S3 raw/ (Parquet)
                                            │
                                    S3 Event Notification
                                            │
                                     Lambda trigger_glue
                                            │
                                       Glue ETL Job
                                            │
                              ┌─────────────┴─────────────┐
                         S3 refined/              Glue Data Catalog
                    (Parquet particionado)    (tabelas refined_* e summary_*)
```

## Componentes

| Componente | Descrição |
|------------|-----------|
| **Lambda Scraper** | Coleta dados diários da B3 via `yfinance` e grava Parquet no S3 |
| **Lambda trigger_glue** | Acionada pelo S3 ao receber novo Parquet; inicia o Glue Job |
| **Glue ETL Job** | Aplica transformações e grava dados refinados catalogando no Glue Catalog |
| **S3 Data Lake** | Bucket com camadas `raw/` e `refined/`, versionamento e criptografia AES-256 |
| **Glue Data Catalog** | Tabelas criadas automaticamente pelo job, consultáveis via Athena |
| **EventBridge Scheduler** | Executa o scraper de segunda a sexta às 18:30 BRT (após fechamento) |
| **API local (FastAPI)** | Interface HTTP opcional para consulta local dos dados |

## Estrutura do Projeto

```
.
├── app/                        # API local FastAPI (uso opcional)
│   ├── main.py
│   ├── routers/
│   │   ├── stocks.py
│   │   └── indices.py
│   ├── services/
│   │   ├── scraper.py          # Scraper B3 (yfinance)
│   │   └── s3_uploader.py      # Upload Parquet para S3
│   └── models/schemas.py
├── terraform/
│   ├── main.tf                 # Provider e backend
│   ├── variables.tf
│   ├── s3.tf                   # Bucket, notificação S3 → Lambda
│   ├── lambda.tf               # Lambda trigger_glue
│   ├── lambda_scraper.tf       # Lambda scraper (Docker/ECR) + EventBridge
│   ├── glue.tf                 # Glue Job + Catalog Database
│   ├── iam.tf                  # Roles e policies
│   ├── outputs.tf
│   ├── lambda/
│   │   ├── scraper.py          # Código da Lambda scraper
│   │   ├── trigger_glue.py     # Código da Lambda trigger
│   │   ├── Dockerfile.scraper
│   │   └── requirements.txt
│   └── glue/
│       └── etl_job.py          # Script do Glue ETL Job
└── requirements.txt
```

## Particionamento dos Dados

**Layer raw** (dados brutos):
```
s3://<bucket>/raw/{stocks|indices}/year=YYYY/month=MM/day=DD/<SYMBOL>.parquet
```

**Layer refined** (dados transformados):
```
s3://<bucket>/refined/{stocks|indices}/symbol=<SYMBOL>/year=YYYY/month=MM/day=DD/
```

**Layer summary** (dados agregados por símbolo):
```
s3://<bucket>/refined/summary/{stocks|indices}/symbol=<SYMBOL>/
```

## Transformações do Glue ETL Job

| # | Transformação | Detalhe |
|---|---------------|---------|
| A | Agrupamento / sumarização | `groupBy(symbol)` com `sum`, `avg`, `count`, `min`, `max` |
| B | Renomear colunas | `close → preco_fechamento`, `volume → volume_negociado` |
| C | Cálculo com base na data | `variacao_diaria_pct` e `media_movel_7d` (média móvel 7 dias) |

## Tabelas no Glue Catalog

Criadas/atualizadas automaticamente pelo job a cada execução:

| Tabela | Conteúdo |
|--------|----------|
| `refined_stocks` | Dados refinados de ações particionados por símbolo e data |
| `refined_indices` | Dados refinados de índices particionados por símbolo e data |
| `summary_stocks` | Métricas agregadas por ação |
| `summary_indices` | Métricas agregadas por índice |

Consulta via Athena:
```sql
SELECT * FROM "refined_stocks" WHERE symbol = 'PETR4' AND year = '2026';
```

## Ativos Monitorados

**Ações:** PETR4, VALE3, ITUB4, BBDC4, ABEV3, B3SA3, WEGE3, RENT3, SUZB3, GGBR4

**Índices:** IBOVESPA, IBRX100, IBRX50, IDIV, SMALL

## Deploy (Infraestrutura)

```bash
cd terraform

# Primeira vez – cria o backend S3/DynamoDB
cd bootstrap && terraform init && terraform apply && cd ..

# Deploy principal
cp terraform.tfvars.example terraform.tfvars  # preencha as variáveis
terraform init
terraform plan
terraform apply
```

## API Local (Opcional)

Para consulta local sem AWS:

```bash
pip install -r requirements.txt
python run.py
# API disponível em http://localhost:8000
```

**Endpoints disponíveis:**

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/stocks/{symbol}` | Dados históricos de uma ação |
| GET | `/stocks/{symbol}/info` | Informações da empresa |
| POST | `/stocks/batch` | Dados de várias ações |
| GET | `/stocks/popular` | Lista ações populares |
| GET | `/indices/{index_name}` | Dados de um índice |
| GET | `/indices/` | Lista índices disponíveis |
