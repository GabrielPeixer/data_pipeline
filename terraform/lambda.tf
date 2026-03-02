##############################################################################
# Lambda – Trigger Glue (acionada pelo S3)
##############################################################################

# ---------- Empacota o código Python ----------
data "archive_file" "lambda_trigger_glue" {
  type        = "zip"
  source_file = "${path.module}/lambda/trigger_glue.py"
  output_path = "${path.module}/.build/trigger_glue.zip"
}

# ---------- CloudWatch Log Group ----------
resource "aws_cloudwatch_log_group" "lambda_trigger_glue" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-trigger-glue"
  retention_in_days = 30
}

# ---------- Lambda Function ----------
resource "aws_lambda_function" "trigger_glue" {
  function_name    = "${var.project_name}-${var.environment}-trigger-glue"
  description      = "Acionada pelo S3 ao receber parquet. Inicia o Glue Job de ETL."
  role             = aws_iam_role.lambda_trigger_glue.arn
  handler          = "trigger_glue.handler"
  runtime          = "python3.12"
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory_size
  filename         = data.archive_file.lambda_trigger_glue.output_path
  source_code_hash = data.archive_file.lambda_trigger_glue.output_base64sha256

  environment {
    variables = {
      GLUE_JOB_NAME = aws_glue_job.etl.name
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_trigger_glue,
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy_attachment.lambda_glue_access,
  ]

  tags = {
    Name = "${var.project_name}-trigger-glue"
  }
}

# ---------- Permissão para o S3 invocar a Lambda ----------
resource "aws_lambda_permission" "allow_s3_invoke" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.trigger_glue.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.data_lake.arn
  source_account = data.aws_caller_identity.current.account_id
}

# ---------- Data source para Account ID ----------
data "aws_caller_identity" "current" {}
