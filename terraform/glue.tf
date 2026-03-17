##############################################################################
# Glue – ETL Job
##############################################################################

# ---------- Upload do script para o S3 ----------
resource "aws_s3_object" "glue_etl_script" {
  bucket = aws_s3_bucket.data_lake.id
  key    = "glue-scripts/etl_job.py"
  source = "${path.module}/glue/etl_job.py"
  etag   = filemd5("${path.module}/glue/etl_job.py")
}

# ---------- Glue Job ----------
resource "aws_glue_job" "etl" {
  name         = "${var.project_name}-${var.environment}-etl"
  description  = "ETL job que processa dados brutos da B3 (parquet), grava no layer refined e cataloga no Glue Catalog."
  role_arn     = aws_iam_role.glue_etl.arn
  glue_version = "4.0"
  max_retries  = 1
  timeout      = var.glue_job_timeout

  worker_type       = var.glue_worker_type
  number_of_workers = var.glue_number_of_workers

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.data_lake.id}/glue-scripts/etl_job.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--job-bookmark-option"              = "job-bookmark-enable"
    "--TempDir"                          = "s3://${aws_s3_bucket.data_lake.id}/glue-temp/"
    "--enable-metrics"                   = "true"
    "--enable-continuous-cloudwatch-log"  = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${aws_s3_bucket.data_lake.id}/glue-spark-logs/"

    # Argumentos default (serão sobrescritos pela Lambda em runtime)
    "--S3_INPUT_PATH" = "s3://${aws_s3_bucket.data_lake.id}/raw/"
    "--S3_BUCKET"     = aws_s3_bucket.data_lake.id
    "--S3_KEY"        = ""
    "--DATA_TYPE"     = "stocks"
    "--CATALOG_DB"    = aws_glue_catalog_database.b3_data.name
  }

  execution_property {
    max_concurrent_runs = 3
  }

  tags = {
    Name = "${var.project_name}-etl"
  }
}

# ---------- Glue Catalog Database ----------
resource "aws_glue_catalog_database" "b3_data" {
  name        = replace("${var.project_name}-${var.environment}", "-", "_")
  description = "Database do catálogo Glue para dados da B3. Tabelas criadas automaticamente pelo ETL job."
}
