"""
Lambda – Trigger Glue Job
Acionada por eventos S3 (upload de parquet no prefix raw/).
Extrai metadados do path S3 e inicia o Glue Job passando os argumentos.
"""

import json
import os
import logging
import urllib.parse

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

glue_client = boto3.client("glue")

GLUE_JOB_NAME = os.environ["GLUE_JOB_NAME"]


def handler(event, context):
    """
    Recebe evento S3, extrai bucket/key e inicia o job Glue.
    """
    logger.info("Evento recebido: %s", json.dumps(event, default=str))

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        size = record["s3"]["object"].get("size", 0)

        logger.info("Arquivo: s3://%s/%s (%d bytes)", bucket, key, size)

        # Ignora arquivos vazios ou _SUCCESS markers
        if size == 0 or key.endswith("_SUCCESS"):
            logger.info("Ignorando arquivo vazio ou marker: %s", key)
            continue

        # Extrai partição do path (ex: raw/stocks/year=2026/month=03/day=02/data.parquet)
        parts = key.split("/")
        data_type = parts[1] if len(parts) > 1 else "unknown"  # stocks ou indices

        try:
            response = glue_client.start_job_run(
                JobName=GLUE_JOB_NAME,
                Arguments={
                    "--S3_INPUT_PATH": f"s3://{bucket}/{key}",
                    "--S3_BUCKET": bucket,
                    "--S3_KEY": key,
                    "--DATA_TYPE": data_type,
                },
            )

            job_run_id = response["JobRunId"]
            logger.info(
                "Glue job '%s' iniciado. RunId: %s | Arquivo: %s",
                GLUE_JOB_NAME,
                job_run_id,
                key,
            )

        except glue_client.exceptions.ConcurrentRunsExceededException:
            logger.warning(
                "Job '%s' já em execução. Arquivo %s será processado depois.",
                GLUE_JOB_NAME,
                key,
            )
        except Exception:
            logger.exception("Erro ao iniciar Glue job para %s", key)
            raise

    return {"statusCode": 200, "body": "OK"}
