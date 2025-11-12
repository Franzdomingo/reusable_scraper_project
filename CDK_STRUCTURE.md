# CDK Project Structure

This document shows the complete CDK infrastructure structure for the LLM Metadata Scraper.

```
reusable_scraper_project/
│
├── app.py                          # CDK app entry point
├── cdk.json                        # CDK configuration
├── requirements-cdk.txt            # CDK Python dependencies
├── CDK_DEPLOYMENT.md              # Deployment guide
│
├── config/                         # Environment configurations
│   ├── dev_config.json            # Development environment
│   ├── stg_config.json            # Staging environment
│   └── prod_config.json           # Production environment
│
├── cdk_resources/                  # CDK constructs
│   ├── __init__.py
│   ├── utils.py                   # Utility functions (tagging)
│   ├── llm_metadata_scraper.py    # Main stack definition
│   │
│   ├── ecs/                       # ECS constructs
│   │   ├── __init__.py
│   │   └── ecs_cluster.py         # ECS cluster, task definition, container
│   │
│   ├── events/                    # EventBridge constructs
│   │   ├── __init__.py
│   │   └── eventbridge_schedule.py # Cron schedule for scraper
│   │
│   └── iam/                       # IAM role constructs
│       ├── __init__.py
│       ├── ecs_role.py            # ECS task role (S3 permissions)
│       └── eventbridge_role.py    # EventBridge execution role
│
├── .github/                        # GitHub Actions
│   ├── workflows/
│   │   ├── cdk-deploy-stg.yaml    # Staging deployment workflow
│   │   └── cdk-deploy-prod.yaml   # Production deployment workflow
│   │
│   └── actions/
│       └── cdk-deploy/
│           └── action.yaml        # Reusable CDK deploy action
│
└── scrapy_project/                # Scrapy application (containerized)
    ├── Dockerfile                 # Docker image for ECS
    ├── docker-compose.yml         # Local development
    └── ... (scrapy code)
```

## Resource Flow

```
EventBridge Schedule (Cron)
    ↓
EventBridge Role (IAM)
    ↓
ECS Task Definition
    ↓
Container (Docker from scrapy_project/)
    ↓
ECS Task Role (IAM) → S3 Bucket (outputs)
```

## Configuration Files

### app.py
- Reads environment config from `config/{env}_config.json`
- Creates CDK stack: `llm-{env}-metadata-scraper`
- Passes config to stack constructs

### Stack (llm_metadata_scraper.py)
Orchestrates three main constructs:
1. **ECSClusterConstruct** - Creates task definition with container
2. **EventBridgeRoleConstruct** - IAM role for EventBridge
3. **EventBridgeScheduleConstruct** - Cron schedule to trigger tasks

### ECS Cluster Construct
- Imports existing VPC and ECS cluster
- Creates task definition with Docker container
- Configures container resources (CPU, memory)
- Sets environment variables for Selenium

### EventBridge Schedule Construct
- Creates EventBridge rule with cron expression
- Targets ECS task with specified launch type (EC2)
- Uses EventBridge role for execution

### IAM Role Constructs
- **ECS Task Role**: S3 permissions for output storage
- **EventBridge Role**: ECS execution permissions (RunTask, StopTask)

## GitHub Actions Workflows

### Staging Deployment
- **Trigger**: Push to `task/*` or `feature/*` branches
- **Action**: Deploy to staging environment
- **Secrets**: `AWS_ACCESS_KEY_STG`, `AWS_SECRET_KEY_STG`, `AWS_REGION_STG`

### Production Deployment
- **Trigger**: PR merged to `main`
- **Action**: Deploy to production environment
- **Secrets**: `AWS_ACCESS_KEY_PROD`, `AWS_SECRET_KEY_PROD`, `AWS_REGION_PROD`

### Reusable Action (cdk-deploy)
Steps:
1. Install Python dependencies
2. Install AWS CDK CLI
3. Configure AWS credentials
4. Run `cdk synth`
5. Run `cdk deploy`

## Environment Variables

Configured in `config/{env}_config.json` and passed to ECS container:

```json
"environment_var": {
  "DISPLAY": ":99",
  "CHROME_BIN": "/usr/bin/chromium",
  "CHROMEDRIVER_PATH": "/usr/bin/chromedriver"
}
```

## Resource Naming Convention

Pattern: `llm-{env}-{system_name}-{component}`

Examples:
- Stack: `llm-stg-metadata-scraper`
- Task Role: `llm-stg-metadata-scraper-task-role`
- EventBridge Role: `llm-stg-metadata-scraper-eventbridge-role`
- Container: `llm-stg-metadata-scraper-app-container`

## Tags

All resources are tagged using `apply_tags()` utility:

```json
"tags": {
  "owner": "llm-team",
  "env": "stg",
  "sys": "metadata-scraper"
}
```

## Deployment Commands

```bash
# Synth CloudFormation template
cdk synth -c env=stg

# Deploy to staging
cdk deploy llm-stg-metadata-scraper -c env=stg

# Deploy to production
cdk deploy llm-prod-metadata-scraper -c env=prod

# List all stacks
cdk ls

# Compare deployed vs current state
cdk diff llm-stg-metadata-scraper -c env=stg

# Destroy stack
cdk destroy llm-stg-metadata-scraper -c env=stg
```

## Next Steps

1. Update `config/{env}_config.json` with your AWS resources
2. Configure GitHub Secrets for deployment
3. Test local deployment with `cdk deploy`
4. Push to `task/*` branch to trigger staging deployment
5. Monitor CloudWatch logs for scraper execution
