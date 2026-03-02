"""
Glue ETL Job – Processa dados brutos (parquet) da B3.

Lê o parquet do path raw/, aplica transformações e escreve
no path processed/ com partição por data_type / year / month / day.
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F

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
input_path = args["S3_INPUT_PATH"]
bucket = args["S3_BUCKET"]
key = args["S3_KEY"]
data_type = args["DATA_TYPE"]  # stocks ou indices

output_base = f"s3://{bucket}/processed/{data_type}/"

print(f"[ETL] Input: {input_path}")
print(f"[ETL] Output base: {output_base}")
print(f"[ETL] Data type: {data_type}")

# ---------- Leitura ----------
df = spark.read.parquet(input_path)

print(f"[ETL] Registros lidos: {df.count()}")
df.printSchema()

# ---------- Transformações ----------

# Garante coluna date como tipo date
if "date" in df.columns:
    df = df.withColumn("date", F.to_date(F.col("date"), "yyyy-MM-dd"))

# Adiciona colunas de partição baseadas na coluna date
if "date" in df.columns:
    df = (
        df.withColumn("year", F.year(F.col("date")))
        .withColumn("month", F.format_string("%02d", F.month(F.col("date"))))
        .withColumn("day", F.format_string("%02d", F.dayofmonth(F.col("date"))))
    )

# Remove duplicatas
df = df.dropDuplicates()

# Remove registros com volume zero (dados inválidos)
if "volume" in df.columns:
    df = df.filter(F.col("volume") > 0)

# Converte valores para precisão adequada
numeric_cols = ["open", "high", "low", "close", "adj_close"]
for col_name in numeric_cols:
    if col_name in df.columns:
        df = df.withColumn(col_name, F.round(F.col(col_name).cast("double"), 2))

print(f"[ETL] Registros após transformações: {df.count()}")

# ---------- Escrita particionada ----------
(
    df.write.mode("append")
    .partitionBy("year", "month", "day")
    .parquet(output_base)
)

print("[ETL] Escrita concluída com sucesso.")

job.commit()
print("[ETL] Job finalizado.")
