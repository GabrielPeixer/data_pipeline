"""
Glue ETL Job – Processa dados brutos (parquet) da B3.

Lê TODOS os parquets do layer raw/ para o data_type informado,
aplica as transformações obrigatórias e grava em processed/.

Transformações:
  A) Agrupamento numérico – soma de volume, média de preço, contagem.
  B) Renomeação de colunas – close → preco_fechamento, volume → volume_negociado.
  C) Cálculo com base na data – variação diária (%) e média móvel de 7 dias.
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# ---------- Argumentos ----------
args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "S3_INPUT_PATH",
        "S3_BUCKET",
        "S3_KEY",
        "DATA_TYPE",
    ],
)

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# ---------- Parâmetros ----------
bucket = args["S3_BUCKET"]
key = args["S3_KEY"]
data_type = args["DATA_TYPE"]  # stocks ou indices

# Lê TODOS os dados brutos do data_type (não apenas o arquivo recém-chegado)
input_base = f"s3://{bucket}/raw/{data_type}/"
detail_output = f"s3://{bucket}/processed/{data_type}/"
summary_output = f"s3://{bucket}/processed/summary/{data_type}/"

print(f"[ETL] Input base: {input_base}")
print(f"[ETL] Detail output: {detail_output}")
print(f"[ETL] Summary output: {summary_output}")
print(f"[ETL] Data type: {data_type}")
print(f"[ETL] Triggered by: s3://{bucket}/{key}")

# ================================================================
# LEITURA
# ================================================================
df = spark.read.parquet(input_base)

print(f"[ETL] Registros lidos: {df.count()}")
df.printSchema()

# Extrai o símbolo (nome do ativo) a partir do nome do arquivo parquet
# Ex: raw/stocks/year=2026/month=03/day=09/PETR4.parquet → PETR4
df = df.withColumn(
    "symbol",
    F.regexp_extract(F.input_file_name(), r"/([^/]+)\.parquet$", 1),
)

# Garante coluna date como tipo date
df = df.withColumn("date", F.to_date(F.col("date")))

# Remove duplicatas
df = df.dropDuplicates()

# Remove registros com volume zero (dados inválidos)
if "volume" in df.columns:
    df = df.filter(F.col("volume") > 0)

# Arredonda colunas numéricas
numeric_cols = ["open", "high", "low", "close", "adj_close"]
for col_name in numeric_cols:
    if col_name in df.columns:
        df = df.withColumn(col_name, F.round(F.col(col_name).cast("double"), 2))

# ================================================================
# TRANSFORMAÇÃO B – Renomear duas colunas existentes
# ================================================================
#   close  → preco_fechamento
#   volume → volume_negociado
df = df.withColumnRenamed("close", "preco_fechamento")
df = df.withColumnRenamed("volume", "volume_negociado")

print("[ETL] Colunas renomeadas: close → preco_fechamento, volume → volume_negociado")

# ================================================================
# TRANSFORMAÇÃO C – Cálculos com base na data
# ================================================================
# C1: Variação diária (%) = (fechamento - abertura) / abertura * 100
df = df.withColumn(
    "variacao_diaria_pct",
    F.round(
        (F.col("preco_fechamento") - F.col("open")) / F.col("open") * 100,
        2,
    ),
)

# C2: Média móvel de 7 dias do preço de fechamento (por símbolo)
window_7d = (
    Window.partitionBy("symbol")
    .orderBy("date")
    .rowsBetween(-6, 0)
)
df = df.withColumn(
    "media_movel_7d",
    F.round(F.avg("preco_fechamento").over(window_7d), 2),
)

print("[ETL] Cálculos de data aplicados: variacao_diaria_pct, media_movel_7d")

# Adiciona colunas de partição
df = (
    df.withColumn("year", F.year("date"))
    .withColumn("month", F.format_string("%02d", F.month("date")))
    .withColumn("day", F.format_string("%02d", F.dayofmonth("date")))
)

print(f"[ETL] Registros após transformações: {df.count()}")
df.printSchema()

# ================================================================
# ESCRITA – Layer de detalhe (particionado por data)
# ================================================================
(
    df.write.mode("overwrite")
    .partitionBy("year", "month", "day")
    .parquet(detail_output)
)
print("[ETL] Escrita do layer de detalhe concluída.")

# ================================================================
# TRANSFORMAÇÃO A – Agrupamento numérico / sumarização
# ================================================================
# Agrupa por símbolo e calcula métricas consolidadas
df_summary = df.groupBy("symbol").agg(
    F.sum("volume_negociado").alias("volume_total"),
    F.round(F.avg("preco_fechamento"), 2).alias("preco_medio_fechamento"),
    F.count("*").alias("total_registros"),
    F.min("preco_fechamento").alias("preco_minimo"),
    F.max("preco_fechamento").alias("preco_maximo"),
    F.round(F.avg("variacao_diaria_pct"), 2).alias("variacao_media_pct"),
)

print(f"[ETL] Registros no resumo: {df_summary.count()}")
df_summary.show(truncate=False)

# ================================================================
# ESCRITA – Layer de resumo (sumarizado)
# ================================================================
df_summary.write.mode("overwrite").parquet(summary_output)
print("[ETL] Escrita do layer de resumo concluída.")

job.commit()
print("[ETL] Job finalizado.")
