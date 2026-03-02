##############################################################################
# Outputs
##############################################################################

output "s3_bucket_name" {
  description = "Nome do bucket S3 do data lake"
  value       = aws_s3_bucket.data_lake.id
}

output "s3_bucket_arn" {
  description = "ARN do bucket S3"
  value       = aws_s3_bucket.data_lake.arn
}

output "s3_raw_data_path" {
  description = "Path completo para ingestão de dados brutos"
  value       = "s3://${aws_s3_bucket.data_lake.id}/${var.raw_data_prefix}"
}

output "lambda_function_name" {
  description = "Nome da Lambda que aciona o Glue"
  value       = aws_lambda_function.trigger_glue.function_name
}

output "lambda_function_arn" {
  description = "ARN da Lambda trigger Glue"
  value       = aws_lambda_function.trigger_glue.arn
}

output "scraper_lambda_name" {
  description = "Nome da Lambda scraper (contém o código da app Python)"
  value       = aws_lambda_function.scraper.function_name
}

output "scraper_lambda_arn" {
  description = "ARN da Lambda scraper"
  value       = aws_lambda_function.scraper.arn
}

output "scraper_ecr_repository_url" {
  description = "URL do repositório ECR da imagem do scraper"
  value       = aws_ecr_repository.scraper.repository_url
}

output "scraper_schedule" {
  description = "Schedule do EventBridge para o scraper"
  value       = aws_scheduler_schedule.scraper_daily.schedule_expression
}

output "glue_job_name" {
  description = "Nome do Glue Job de ETL"
  value       = aws_glue_job.etl.name
}

output "glue_catalog_database" {
  description = "Nome do database no Glue Catalog"
  value       = aws_glue_catalog_database.b3_data.name
}

output "upload_example_stocks" {
  description = "Exemplo de upload de parquet para stocks com partição diária"
  value       = "aws s3 cp data.parquet s3://${aws_s3_bucket.data_lake.id}/raw/stocks/year=2026/month=03/day=02/data.parquet"
}

output "upload_example_indices" {
  description = "Exemplo de upload de parquet para indices com partição diária"
  value       = "aws s3 cp data.parquet s3://${aws_s3_bucket.data_lake.id}/raw/indices/year=2026/month=03/day=02/data.parquet"
}
