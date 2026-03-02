##############################################################################
# Variables
##############################################################################

variable "aws_region" {
  description = "Região AWS"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nome do projeto (usado como prefixo nos recursos)"
  type        = string
  default     = "b3-data-pipeline"
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "glue_job_timeout" {
  description = "Timeout do job Glue em minutos"
  type        = number
  default     = 60
}

variable "glue_number_of_workers" {
  description = "Número de workers do Glue"
  type        = number
  default     = 2
}

variable "glue_worker_type" {
  description = "Tipo de worker do Glue (Standard, G.1X, G.2X)"
  type        = string
  default     = "G.1X"
}

variable "lambda_timeout" {
  description = "Timeout da Lambda em segundos"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Memória da Lambda em MB"
  type        = number
  default     = 128
}

variable "raw_data_prefix" {
  description = "Prefixo dos dados brutos no S3"
  type        = string
  default     = "raw/"
}

variable "processed_data_prefix" {
  description = "Prefixo dos dados processados no S3"
  type        = string
  default     = "processed/"
}

# ──────────────── Lambda Scraper ────────────────

variable "scraper_lambda_timeout" {
  description = "Timeout da Lambda scraper em segundos (precisa de tempo para chamar yfinance)"
  type        = number
  default     = 300
}

variable "scraper_lambda_memory_size" {
  description = "Memória da Lambda scraper em MB (pandas + pyarrow precisam de mais memória)"
  type        = number
  default     = 512
}

variable "scraper_stocks" {
  description = "Lista de ações para o scraper coletar diariamente"
  type        = list(string)
  default = [
    "PETR4", "VALE3", "ITUB4", "BBDC4", "ABEV3",
    "B3SA3", "WEGE3", "RENT3", "SUZB3", "GGBR4"
  ]
}

variable "scraper_indices" {
  description = "Lista de índices para o scraper coletar diariamente"
  type        = list(string)
  default     = ["IBOVESPA", "IBRX100", "IBRX50", "IDIV", "SMALL"]
}
