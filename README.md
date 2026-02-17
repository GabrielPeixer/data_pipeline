# API de Dados da B3

API simples para extrair dados de ações e índices da Bolsa de Valores do Brasil (B3).

## O que faz

- Pega dados históricos diários de ações da B3
- Pega dados de índices como IBOVESPA
- Mostra informações básicas das empresas
- Permite pegar dados de várias ações de uma vez

## Como usar

### Instalar

1. Instale Python 3.9+
2. Baixe as dependências:
```bash
pip install -r requirements.txt
```

### Rodar

```bash
python run.py
```

A API fica em http://localhost:8000

## Endpoints

### Ações

- `GET /stocks/{symbol}` - Dados históricos de uma ação
- `GET /stocks/{symbol}/info` - Info da empresa
- `POST /stocks/batch` - Dados de várias ações
- `GET /stocks/popular` - Lista ações populares

### Índices

- `GET /indices/{index_name}` - Dados de um índice
- `GET /indices/` - Lista índices disponíveis

## Exemplos

Pegar dados da PETR4:
```bash
curl http://localhost:8000/stocks/PETR4
```

Pegar dados do IBOVESPA:
```bash
curl http://localhost:8000/indices/IBOVESPA
```

Pegar várias ações:
```bash
curl -X POST http://localhost:8000/stocks/batch \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["PETR4", "VALE3"]}'
```

## Índices disponíveis

- IBOVESPA
- IBRX100
- IBRX50
- IDIV
- SMALL

## Ações populares

PETR4, VALE3, ITUB4, BBDC4, ABEV3, etc.

## Dados retornados

Para cada dia:
- Preço de abertura
- Preço máximo
- Preço mínimo
- Preço de fechamento
- Volume negociado
