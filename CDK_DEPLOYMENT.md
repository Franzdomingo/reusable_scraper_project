# AWS CDK Deployment Guide

This guide explains how to deploy the LLM Metadata Scraper to AWS using CDK and GitHub Actions.

## Architecture Overview

The deployment creates:
- **ECS Task Definition**: Runs the Scrapy scraper in a Docker container
- **EventBridge Schedule**: Triggers the scraper on a cron schedule
- **IAM Roles**: Task role for S3 access, EventBridge role for ECS execution
- **S3 Bucket**: Stores scraped output data (configured separately)

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Existing ECS Cluster** on EC2 launch type
3. **VPC and Subnets** configured
4. **S3 Bucket** for output storage (optional)
5. **AWS CDK** installed: `npm install -g aws-cdk`
6. **Python 3.11+** installed

## Local Setup

### 1. Install CDK Dependencies

```bash
pip install -r requirements-cdk.txt
```

### 2. Configure Environment

Edit the configuration files in `config/` directory:
- `dev_config.json` - Development environment
- `stg_config.json` - Staging environment
- `prod_config.json` - Production environment

**Update these values:**
```json
{
  "stg": {
    "account": "YOUR_AWS_ACCOUNT_ID",      // Replace with your AWS account ID
    "region": "us-east-1",                  // Your AWS region
    "vpc_id": "vpc-XXXXX",                  // Your VPC ID
    "availability_zones": ["us-east-1a", "us-east-1b"],
    "private_subnet_ids": ["subnet-XXXXX", "subnet-YYYYY"],
    "ecs": {
      "cluster_name": "your-ecs-cluster-name"  // Your existing ECS cluster
    },
    "s3": {
      "bucket_name": "your-output-bucket"   // S3 bucket for outputs
    }
  }
}
```

### 3. Bootstrap CDK (First Time Only)

```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

### 4. Deploy Locally

**Deploy to staging:**
```bash
cdk synth -c env=stg
cdk deploy llm-stg-metadata-scraper -c env=stg
```

**Deploy to production:**
```bash
cdk synth -c env=prod
cdk deploy llm-prod-metadata-scraper -c env=prod
```

## GitHub Actions Deployment

### 1. Configure GitHub Secrets

Add these secrets to your GitHub repository (Settings > Secrets and variables > Actions):

**For Staging:**
- `AWS_ACCESS_KEY_STG` - AWS access key for staging
- `AWS_SECRET_KEY_STG` - AWS secret key for staging
- `AWS_REGION_STG` - AWS region for staging (e.g., `us-east-1`)

**For Production:**
- `AWS_ACCESS_KEY_PROD` - AWS access key for production
- `AWS_SECRET_KEY_PROD` - AWS secret key for production
- `AWS_REGION_PROD` - AWS region for production

### 2. Deployment Triggers

**Staging Deployment:**
- Triggers on push to `task/*` or `feature/*` branches
- Workflow: `.github/workflows/cdk-deploy-stg.yaml`

**Production Deployment:**
- Triggers when PR is merged to `main` branch
- Workflow: `.github/workflows/cdk-deploy-prod.yaml`

### 3. Deployment Process

1. **For Staging:**
   ```bash
   git checkout -b task/my-feature
   # Make changes
   git commit -m "Add new feature"
   git push origin task/my-feature
   # GitHub Actions automatically deploys to staging
   ```

2. **For Production:**
   ```bash
   # Create PR from task/* branch to main
   # After PR review and merge, GitHub Actions deploys to production
   ```

## EventBridge Schedules

The scraper runs on a cron schedule configured in the environment config files:

**Development:** Every 30 minutes
```json
"minute": "*/30",
"hour": "*"
```

**Staging/Production:** Daily at 2:00 AM UTC
```json
"minute": "0",
"hour": "2"
```

To modify the schedule, update the `eventbridge` section in the config files.

## Resource Naming Convention

All resources follow this pattern: `llm-{env}-{system_name}-{component}`

Examples:
- Task Definition: `llm-stg-metadata-scraper-task-role`
- EventBridge Role: `llm-stg-metadata-scraper-eventbridge-role`
- Stack Name: `llm-stg-metadata-scraper`

## Monitoring

**CloudWatch Logs:**
- Log Group: `/ecs/LLMScraperLogs`
- Check logs in AWS Console > CloudWatch > Log Groups

**ECS Tasks:**
- View running tasks in AWS Console > ECS > Clusters > {cluster-name}

**EventBridge:**
- View schedules in AWS Console > EventBridge > Rules

## Troubleshooting

### CDK Synth Fails
```bash
# Check if config file exists
ls config/stg_config.json

# Verify Python dependencies
pip install -r requirements-cdk.txt
```

### GitHub Actions Fails
1. Check GitHub Secrets are configured correctly
2. Verify AWS credentials have proper permissions
3. Check workflow logs in GitHub Actions tab

### ECS Task Fails to Start
1. Check CloudWatch logs for errors
2. Verify VPC/subnet configuration
3. Ensure ECS cluster has capacity
4. Check IAM role permissions

## Useful CDK Commands

```bash
# List all stacks
cdk ls

# Show CloudFormation template
cdk synth -c env=stg

# Compare deployed stack with current state
cdk diff llm-stg-metadata-scraper -c env=stg

# Destroy stack (be careful!)
cdk destroy llm-stg-metadata-scraper -c env=stg
```

## Cost Considerations

- **ECS Tasks**: Charged per CPU/memory and duration
- **EventBridge**: Minimal cost for rules
- **CloudWatch Logs**: Based on ingestion and storage
- **S3**: Based on storage and requests

Estimated cost for staging (running daily): ~$5-10/month

## Next Steps

1. Update config files with your AWS resources
2. Configure GitHub Secrets
3. Test deployment to staging
4. Monitor CloudWatch logs
5. Adjust memory/CPU limits based on performance
6. Configure S3 bucket lifecycle policies for output data
