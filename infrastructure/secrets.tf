# --- Secrets Manager ---

resource "aws_secretsmanager_secret" "gemini_api_key" {
  name        = "${var.project_name}/gemini-api-key"
  description = "Gemini API Key for Cloud Cost Optimizer"
}

# Note: The actual value should be set manually in the AWS Console or via the AWS CLI
# to avoid committing secrets to version control.

output "gemini_api_key_secret_arn" {
  value = aws_secretsmanager_secret.gemini_api_key.arn
}
