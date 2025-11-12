#!/bin/bash
# CDK Setup Script for LLM Metadata Scraper

set -e

echo "=========================================="
echo "CDK Setup for LLM Metadata Scraper"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed. Please install Node.js first."
    exit 1
fi

# Install AWS CDK CLI globally
echo ""
echo "Installing AWS CDK CLI..."
npm install -g aws-cdk

# Install Python CDK dependencies
echo ""
echo "Installing Python CDK dependencies..."
pip install -r requirements-cdk.txt

# Check if config files are updated
echo ""
echo "Checking configuration files..."
if grep -q "YOUR_AWS_ACCOUNT_ID" config/stg_config.json; then
    echo ""
    echo "WARNING: Please update config files with your AWS account details:"
    echo "  - config/dev_config.json"
    echo "  - config/stg_config.json"
    echo "  - config/prod_config.json"
    echo ""
    echo "Update the following values:"
    echo "  - account: YOUR_AWS_ACCOUNT_ID"
    echo "  - vpc_id: vpc-XXXXX"
    echo "  - private_subnet_ids: [subnet-XXXXX, subnet-YYYYY]"
    echo "  - ecs.cluster_name: your-ecs-cluster-name"
    echo "  - s3.bucket_name: your-output-bucket"
fi

# Bootstrap CDK (optional)
echo ""
read -p "Do you want to bootstrap CDK now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter AWS Account ID: " account_id
    read -p "Enter AWS Region (e.g., us-east-1): " region
    echo "Bootstrapping CDK..."
    cdk bootstrap aws://$account_id/$region
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Update config files with your AWS resources"
echo "2. Run: cdk synth -c env=stg"
echo "3. Run: cdk deploy llm-stg-metadata-scraper -c env=stg"
echo ""
echo "For GitHub Actions deployment:"
echo "1. Add GitHub Secrets (AWS_ACCESS_KEY_STG, AWS_SECRET_KEY_STG, AWS_REGION_STG)"
echo "2. Push to task/* branch to trigger staging deployment"
echo ""
echo "See CDK_DEPLOYMENT.md for detailed instructions"
