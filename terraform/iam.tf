##############################################################################
# IAM – Roles e Policies para Lambda e Glue
##############################################################################

# ========================== LAMBDA ==========================

# ---------- Role ----------
resource "aws_iam_role" "lambda_trigger_glue" {
  name = "${var.project_name}-${var.environment}-lambda-trigger-glue"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-lambda-role"
  }
}

# ---------- Policy: CloudWatch Logs ----------
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_trigger_glue.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ---------- Policy: Permissão para iniciar Glue Job ----------
resource "aws_iam_policy" "lambda_glue_access" {
  name        = "${var.project_name}-${var.environment}-lambda-glue-access"
  description = "Permite que a Lambda inicie jobs do Glue"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowStartGlueJob"
        Effect = "Allow"
        Action = [
          "glue:StartJobRun",
          "glue:GetJobRun",
          "glue:GetJobRuns",
          "glue:BatchStopJobRun"
        ]
        Resource = [
          aws_glue_job.etl.arn,
          "${aws_glue_job.etl.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_glue_access" {
  role       = aws_iam_role.lambda_trigger_glue.name
  policy_arn = aws_iam_policy.lambda_glue_access.arn
}

# ========================== GLUE ==========================

# ---------- Role ----------
resource "aws_iam_role" "glue_etl" {
  name = "${var.project_name}-${var.environment}-glue-etl"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-glue-role"
  }
}

# ---------- Policy: Glue Service Role ----------
resource "aws_iam_role_policy_attachment" "glue_service_role" {
  role       = aws_iam_role.glue_etl.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# ---------- Policy: Acesso ao S3 do Data Lake ----------
resource "aws_iam_policy" "glue_s3_access" {
  name        = "${var.project_name}-${var.environment}-glue-s3-access"
  description = "Permite que o Glue leia/escreva no bucket do data lake"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowS3ReadWrite"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "glue_s3_access" {
  role       = aws_iam_role.glue_etl.name
  policy_arn = aws_iam_policy.glue_s3_access.arn
}

# ---------- Policy: Glue Catalog ----------
resource "aws_iam_policy" "glue_catalog_access" {
  name        = "${var.project_name}-${var.environment}-glue-catalog-access"
  description = "Permite que o Glue acesse o Data Catalog"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowGlueCatalog"
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetTable",
          "glue:GetTables",
          "glue:CreateTable",
          "glue:UpdateTable",
          "glue:GetPartition",
          "glue:GetPartitions",
          "glue:CreatePartition",
          "glue:BatchCreatePartition"
        ]
        Resource = [
          "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:catalog",
          "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:database/${aws_glue_catalog_database.b3_data.name}",
          "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/${aws_glue_catalog_database.b3_data.name}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "glue_catalog_access" {
  role       = aws_iam_role.glue_etl.name
  policy_arn = aws_iam_policy.glue_catalog_access.arn
}

# ---------- Policy: CloudWatch Logs para Glue ----------
resource "aws_iam_policy" "glue_cloudwatch" {
  name        = "${var.project_name}-${var.environment}-glue-cloudwatch"
  description = "Permite que o Glue escreva logs no CloudWatch"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws-glue/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "glue_cloudwatch" {
  role       = aws_iam_role.glue_etl.name
  policy_arn = aws_iam_policy.glue_cloudwatch.arn
}

# ========================== LAMBDA SCRAPER ==========================

# ---------- Role ----------
resource "aws_iam_role" "lambda_scraper" {
  name = "${var.project_name}-${var.environment}-lambda-scraper"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-lambda-scraper-role"
  }
}

# ---------- Policy: CloudWatch Logs ----------
resource "aws_iam_role_policy_attachment" "scraper_basic_execution" {
  role       = aws_iam_role.lambda_scraper.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ---------- Policy: S3 PutObject (grava parquet no bucket) ----------
resource "aws_iam_policy" "scraper_s3_access" {
  name        = "${var.project_name}-${var.environment}-scraper-s3-access"
  description = "Permite que a Lambda scraper grave parquet no S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowS3Put"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.data_lake.arn}/${var.raw_data_prefix}*"
      },
      {
        Sid      = "AllowS3ListBucket"
        Effect   = "Allow"
        Action   = "s3:ListBucket"
        Resource = aws_s3_bucket.data_lake.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "scraper_s3_access" {
  role       = aws_iam_role.lambda_scraper.name
  policy_arn = aws_iam_policy.scraper_s3_access.arn
}
