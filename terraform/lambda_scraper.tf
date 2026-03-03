##############################################################################
# Lambda Scraper – Coleta dados B3 e grava Parquet no S3
# Deploy via Docker image (yfinance + pandas + pyarrow são pesados)
# Agendada via EventBridge para rodar diariamente
##############################################################################

# ---------- ECR Repository ----------
resource "aws_ecr_repository" "scraper" {
  name                 = "${var.project_name}-${var.environment}-scraper"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.project_name}-scraper"
  }
}

# ---------- ECR Lifecycle (mantém apenas as 5 últimas imagens) ----------
resource "aws_ecr_lifecycle_policy" "scraper" {
  repository = aws_ecr_repository.scraper.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Manter apenas 5 imagens"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ---------- Build e push da Docker image ----------
# Usa null_resource para build/push via Docker CLI
resource "null_resource" "scraper_docker_build" {
  triggers = {
    dockerfile_hash  = filemd5("${path.module}/lambda/Dockerfile.scraper")
    scraper_hash     = filemd5("${path.module}/lambda/scraper.py")
    requirements_hash = filemd5("${path.module}/lambda/requirements.txt")
  }

  provisioner "local-exec" {
    command = <<-EOT
      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.scraper.repository_url}
      docker build -t ${aws_ecr_repository.scraper.repository_url}:latest -f ${path.module}/lambda/Dockerfile.scraper ${path.module}/lambda/
      docker push ${aws_ecr_repository.scraper.repository_url}:latest
    EOT
  }

  depends_on = [aws_ecr_repository.scraper]
}

# ---------- CloudWatch Log Group ----------
resource "aws_cloudwatch_log_group" "lambda_scraper" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-scraper"
  retention_in_days = 30
}

# ---------- Lambda Function (Container Image) ----------
resource "aws_lambda_function" "scraper" {
  function_name = "${var.project_name}-${var.environment}-scraper"
  description   = "Coleta dados de ações e índices da B3, grava Parquet no S3 com partição diária."
  role          = aws_iam_role.lambda_scraper.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.scraper.repository_url}:latest"
  timeout       = var.scraper_lambda_timeout
  memory_size   = var.scraper_lambda_memory_size

  environment {
    variables = {
      S3_BUCKET      = aws_s3_bucket.data_lake.id
      S3_RAW_PREFIX  = trimsuffix(var.raw_data_prefix, "/")
    }
  }

  depends_on = [
    null_resource.scraper_docker_build,
    aws_cloudwatch_log_group.lambda_scraper,
    aws_iam_role_policy_attachment.scraper_basic_execution,
    aws_iam_role_policy_attachment.scraper_s3_access,
  ]

  tags = {
    Name = "${var.project_name}-scraper"
  }
}

# ---------- EventBridge – Agendamento diário ----------
resource "aws_scheduler_schedule" "scraper_daily" {
  name        = "${var.project_name}-${var.environment}-scraper-daily"
  description = "Executa o scraper B3 de segunda a sexta às 18:30 (horário de Brasília, após fechamento do mercado)"

  flexible_time_window {
    mode = "OFF"
  }

  # Segunda a sexta, 18:30 BRT (21:30 UTC)
  schedule_expression          = "cron(30 21 ? * MON-FRI *)"
  schedule_expression_timezone = "America/Sao_Paulo"

  target {
    arn      = aws_lambda_function.scraper.arn
    role_arn = aws_iam_role.eventbridge_scheduler.arn

    input = jsonencode({
      stocks  = var.scraper_stocks
      indices = var.scraper_indices
      period  = "1d"
    })

    retry_policy {
      maximum_retry_attempts       = 2
      maximum_event_age_in_seconds = 300
    }
  }
}

# ---------- IAM Role para EventBridge Scheduler ----------
resource "aws_iam_role" "eventbridge_scheduler" {
  name = "${var.project_name}-${var.environment}-eventbridge-scheduler"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "eventbridge_invoke_lambda" {
  name = "invoke-scraper-lambda"
  role = aws_iam_role.eventbridge_scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = aws_lambda_function.scraper.arn
      }
    ]
  })
}
