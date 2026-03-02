##############################################################################
# Bootstrap – Bucket S3 para armazenar o Terraform State
#
# Execute ANTES da infra principal:
#   cd terraform/bootstrap
#   terraform init
#   terraform apply
#
# Depois volte para terraform/ e execute:
#   terraform init   (vai configurar o backend S3)
#   terraform apply
##############################################################################

terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "b3-data-pipeline"
      ManagedBy = "terraform"
      Purpose   = "tfstate-backend"
    }
  }
}

# ---------- Variáveis ----------
variable "aws_region" {
  description = "Região AWS"
  type        = string
  default     = "us-east-1"
}

variable "tfstate_bucket_name" {
  description = "Nome do bucket para o Terraform state"
  type        = string
  default     = "b3-data-pipeline-tfstate"
}

# ---------- Bucket S3 ----------
resource "aws_s3_bucket" "tfstate" {
  bucket = var.tfstate_bucket_name

  # Impede destruição acidental do state
  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name = var.tfstate_bucket_name
  }
}

# ---------- Versionamento (permite rollback do state) ----------
resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  versioning_configuration {
    status = "Enabled"
  }
}

# ---------- Criptografia server-side ----------
resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# ---------- Bloqueia acesso público ----------
resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ---------- Outputs ----------
output "tfstate_bucket_name" {
  description = "Nome do bucket de tfstate"
  value       = aws_s3_bucket.tfstate.id
}

output "tfstate_bucket_arn" {
  description = "ARN do bucket de tfstate"
  value       = aws_s3_bucket.tfstate.arn
}

output "next_steps" {
  description = "Próximos passos"
  value       = "Bucket criado. Agora execute: cd ../  &&  terraform init  &&  terraform plan"
}
