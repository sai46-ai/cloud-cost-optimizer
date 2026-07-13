<#
.SYNOPSIS
Deploys the Cloud Cost Optimizer to AWS using Terraform.

.DESCRIPTION
This script will check for the necessary tools (Terraform and AWS CLI), 
guide you through authentication, and execute the Terraform deployment.
#>

$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Cloud Cost Optimizer AWS Deployment     " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Check for AWS CLI
if (-not (Get-Command "aws" -ErrorAction SilentlyContinue)) {
    Write-Host "`n[ERROR] AWS CLI is not installed." -ForegroundColor Red
    Write-Host "Please download and install it from: https://aws.amazon.com/cli/"
    Write-Host "After installing, restart your terminal and run 'aws configure' before running this script again."
    exit 1
}

# 2. Check for Terraform
if (-not (Get-Command "terraform" -ErrorAction SilentlyContinue)) {
    Write-Host "`n[ERROR] Terraform is not installed." -ForegroundColor Red
    Write-Host "Please download and install it from: https://developer.hashicorp.com/terraform/downloads"
    Write-Host "Make sure it is added to your PATH, then restart your terminal."
    exit 1
}

# 3. Check AWS Authentication
Write-Host "`nChecking AWS credentials..." -ForegroundColor Yellow
try {
    aws sts get-caller-identity > $null
    Write-Host "Successfully authenticated with AWS." -ForegroundColor Green
} catch {
    Write-Host "`n[ERROR] Not authenticated with AWS." -ForegroundColor Red
    Write-Host "Please run 'aws configure' to set up your Access Key ID and Secret Access Key."
    exit 1
}

# 4. Deploy Infrastructure
Write-Host "`nInitializing Terraform..." -ForegroundColor Yellow
Set-Location -Path ".\infrastructure"
terraform init

Write-Host "`nPlanning Terraform deployment..." -ForegroundColor Yellow
terraform plan -out=tfplan

Write-Host "`nWould you like to apply this deployment? (y/N): " -ForegroundColor Cyan -NoNewline
$response = Read-Host
if ($response -eq 'y' -or $response -eq 'Y') {
    Write-Host "`nApplying Terraform deployment..." -ForegroundColor Yellow
    terraform apply tfplan
    Write-Host "`nDeployment completed successfully!" -ForegroundColor Green
    
    Write-Host "`nNext Steps:" -ForegroundColor Cyan
    Write-Host "1. Build your frontend (npm run build) and upload to the S3 bucket."
    Write-Host "2. Build your Docker images and push them to the ECR repositories."
    Write-Host "3. Set your VITE_GEMINI_API_KEY in AWS Secrets Manager."
} else {
    Write-Host "`nDeployment cancelled." -ForegroundColor Yellow
}
