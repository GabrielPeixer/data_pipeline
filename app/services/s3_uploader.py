"""
Utilitário para upload de dados do scraper para o S3 em formato Parquet
com partição diária: raw/{data_type}/year=YYYY/month=MM/day=DD/

Uso:
    from app.services.s3_uploader import S3ParquetUploader
    uploader = S3ParquetUploader(bucket_name="b3-data-pipeline-dev-data-lake")
    uploader.upload_stock_data("PETR4", data_dict)
    uploader.upload_index_data("IBOVESPA", data_dict)
"""

import io
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

import boto3
import pandas as pd


class S3ParquetUploader:
    """Faz upload de dados da B3 para o S3 em formato Parquet com partição diária."""

    def __init__(self, bucket_name: str | None = None, region: str = "us-east-1"):
        self.bucket_name = bucket_name or os.environ.get("S3_BUCKET_NAME", "")
        self.s3_client = boto3.client("s3", region_name=region)

    def _build_s3_key(self, data_type: str, symbol: str, date: datetime | None = None) -> str:
        """
        Monta o path S3 com partição diária.
        Ex: raw/stocks/year=2026/month=03/day=02/PETR4.parquet
        """
        dt = date or datetime.now(timezone.utc)
        return (
            f"raw/{data_type}/"
            f"year={dt.year}/"
            f"month={dt.month:02d}/"
            f"day={dt.day:02d}/"
            f"{symbol}.parquet"
        )

    def _records_to_parquet_bytes(self, records: List[Dict[str, Any]]) -> bytes:
        """Converte lista de dicts para bytes Parquet."""
        df = pd.DataFrame(records)
        buffer = io.BytesIO()
        df.to_parquet(buffer, engine="pyarrow", index=False)
        return buffer.getvalue()

    def upload_stock_data(self, symbol: str, data: Dict[str, Any]) -> str:
        """
        Faz upload dos dados de uma ação para o S3.
        Espera o formato retornado por B3Scraper.get_stock_data().
        """
        records = data.get("data", [])
        if not records:
            raise ValueError(f"Sem registros para {symbol}")

        parquet_bytes = self._records_to_parquet_bytes(records)
        s3_key = self._build_s3_key("stocks", symbol.upper())

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=parquet_bytes,
            ContentType="application/octet-stream",
        )

        path = f"s3://{self.bucket_name}/{s3_key}"
        print(f"[S3] Upload OK: {path} ({len(parquet_bytes)} bytes)")
        return path

    def upload_index_data(self, index_name: str, data: Dict[str, Any]) -> str:
        """
        Faz upload dos dados de um índice para o S3.
        Espera o formato retornado por B3Scraper.get_index_data().
        """
        records = data.get("data", [])
        if not records:
            raise ValueError(f"Sem registros para {index_name}")

        parquet_bytes = self._records_to_parquet_bytes(records)
        s3_key = self._build_s3_key("indices", index_name.upper())

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=parquet_bytes,
            ContentType="application/octet-stream",
        )

        path = f"s3://{self.bucket_name}/{s3_key}"
        print(f"[S3] Upload OK: {path} ({len(parquet_bytes)} bytes)")
        return path
