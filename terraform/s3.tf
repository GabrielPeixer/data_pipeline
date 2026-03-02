##############################################################################
# S3 – Bucket para dados brutos (raw) e processados
# Partição diária: raw/{stocks|indices}/year=YYYY/month=MM/day=DD/*.parquet
##############################################################################

resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project_name}-${var.environment}-data-lake"

  # Protege contra destruição acidental
  force_destroy = false

  tags = {
    Name = "${var.project_name}-data-lake"
  }
}

# ---------- Versionamento ----------
resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

# ---------- Criptografia ----------
resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# ---------- Bloqueia acesso público ----------
resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ---------- Lifecycle – move dados antigos para IA ----------
resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "raw-data-lifecycle"
    status = "Enabled"

    filter {
      prefix = var.raw_data_prefix
    }

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 365
      storage_class = "GLACIER"
    }
  }

  rule {
    id     = "processed-data-lifecycle"
    status = "Enabled"

    filter {
      prefix = var.processed_data_prefix
    }

    transition {
      days          = 180
      storage_class = "STANDARD_IA"
    }
  }
}

# ---------- Notificação S3 → Lambda ----------
resource "aws_s3_bucket_notification" "trigger_lambda" {
  bucket = aws_s3_bucket.data_lake.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.trigger_glue.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = var.raw_data_prefix
    filter_suffix       = ".parquet"
  }

  depends_on = [aws_lambda_permission.allow_s3_invoke]
}
