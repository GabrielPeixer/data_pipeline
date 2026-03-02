"""
Lambda Scraper – Coleta dados da B3 e grava no S3 em Parquet.
Agendada via EventBridge para rodar diariamente.

Contém o código do scraper (app/) embutido diretamente na Lambda.
"""

import io
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3
import pandas as pd
import yfinance as yf

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ──────────────────────────────────────────────
# Configuração
# ──────────────────────────────────────────────
S3_BUCKET = os.environ["S3_BUCKET"]
S3_RAW_PREFIX = os.environ.get("S3_RAW_PREFIX", "raw")

s3_client = boto3.client("s3")

B3_INDICES = {
    "IBOVESPA": "^BVSP",
    "IBRX100": "^IBX100",
    "IBRX50": "^IBX50",
    "IDIV": "IDIV11.SA",
    "SMALL": "SMAL11.SA",
}

POPULAR_STOCKS = [
    "PETR4", "VALE3", "ITUB4", "BBDC4", "ABEV3",
    "B3SA3", "WEGE3", "RENT3", "SUZB3", "GGBR4",
]

SA_SUFFIX = ".SA"


# ──────────────────────────────────────────────
# Scraper (lógica extraída de app/services/scraper.py)
# ──────────────────────────────────────────────
def _format_symbol(symbol: str) -> str:
    symbol = symbol.upper().strip()
    if not symbol.endswith(SA_SUFFIX) and not symbol.startswith("^"):
        return f"{symbol}{SA_SUFFIX}"
    return symbol


def _parse_dataframe(df: pd.DataFrame) -> List[Dict[str, Any]]:
    if df.empty:
        return []
    df = df.reset_index()
    records = []
    for _, row in df.iterrows():
        records.append({
            "date": row["Date"].strftime("%Y-%m-%d"),
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "adj_close": round(float(row.get("Adj Close", row["Close"])), 2),
            "volume": int(row["Volume"]),
        })
    return records


def scrape_stock(symbol: str, period: str = "1d") -> Dict[str, Any]:
    formatted = _format_symbol(symbol)
    ticker = yf.Ticker(formatted)
    df = ticker.history(period=period, interval="1d")
    if df.empty:
        raise ValueError(f"Nenhum dado para {symbol}")
    info = ticker.info
    return {
        "symbol": symbol.upper(),
        "company_name": info.get("longName") or info.get("shortName"),
        "currency": "BRL",
        "data": _parse_dataframe(df),
        "total_records": len(df),
    }


def scrape_index(index_name: str, period: str = "1d") -> Dict[str, Any]:
    index_name = index_name.upper()
    if index_name not in B3_INDICES:
        raise ValueError(f"Índice não encontrado: {index_name}")
    symbol = B3_INDICES[index_name]
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval="1d")
    if df.empty:
        raise ValueError(f"Nenhum dado para {index_name}")
    records = _parse_dataframe(df)
    for r in records:
        r.pop("adj_close", None)
    return {
        "index_name": index_name,
        "symbol": symbol,
        "data": records,
        "total_records": len(df),
    }


# ──────────────────────────────────────────────
# Upload S3 em Parquet com partição diária
# ──────────────────────────────────────────────
def _to_parquet_bytes(records: List[Dict[str, Any]]) -> bytes:
    df = pd.DataFrame(records)
    buf = io.BytesIO()
    df.to_parquet(buf, engine="pyarrow", index=False)
    return buf.getvalue()


def _upload_parquet(data_type: str, name: str, records: List[Dict[str, Any]]) -> str:
    now = datetime.now(timezone.utc)
    key = (
        f"{S3_RAW_PREFIX}/{data_type}/"
        f"year={now.year}/"
        f"month={now.month:02d}/"
        f"day={now.day:02d}/"
        f"{name}.parquet"
    )
    body = _to_parquet_bytes(records)
    s3_client.put_object(Bucket=S3_BUCKET, Key=key, Body=body)
    path = f"s3://{S3_BUCKET}/{key}"
    logger.info("[S3] %s  (%d bytes, %d registros)", path, len(body), len(records))
    return path


# ──────────────────────────────────────────────
# Handler
# ──────────────────────────────────────────────
def handler(event, context):
    """
    Entrada da Lambda. Aceita:
      - Invocação agendada (EventBridge) → coleta todos stocks + índices
      - Invocação manual com payload:
          { "stocks": ["PETR4"], "indices": ["IBOVESPA"], "period": "5d" }
    """
    logger.info("Evento: %s", json.dumps(event, default=str))

    # Determina o que coletar
    stocks = event.get("stocks", POPULAR_STOCKS)
    indices = event.get("indices", list(B3_INDICES.keys()))
    period = event.get("period", "1d")

    results = {"stocks": [], "indices": [], "errors": []}

    # ── Stocks ──
    for symbol in stocks:
        try:
            data = scrape_stock(symbol, period=period)
            path = _upload_parquet("stocks", symbol.upper(), data["data"])
            results["stocks"].append({"symbol": symbol, "path": path, "records": data["total_records"]})
        except Exception as e:
            logger.error("Erro stock %s: %s", symbol, e)
            results["errors"].append({"type": "stock", "symbol": symbol, "error": str(e)})

    # ── Índices ──
    for idx_name in indices:
        try:
            data = scrape_index(idx_name, period=period)
            path = _upload_parquet("indices", idx_name.upper(), data["data"])
            results["indices"].append({"index": idx_name, "path": path, "records": data["total_records"]})
        except Exception as e:
            logger.error("Erro index %s: %s", idx_name, e)
            results["errors"].append({"type": "index", "index": idx_name, "error": str(e)})

    logger.info(
        "Resumo: %d stocks OK, %d indices OK, %d erros",
        len(results["stocks"]),
        len(results["indices"]),
        len(results["errors"]),
    )

    return {
        "statusCode": 200,
        "body": results,
    }
