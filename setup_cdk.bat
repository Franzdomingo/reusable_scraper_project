@echo off
REM CDK Setup Script for LLM Metadata Scraper (Windows)

echo ==========================================
echo CDK Setup for LLM Metadata Scraper
echo ==========================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    exit /b 1
)

REM Check if npm is installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo Error: npm is not installed. Please install Node.js first.
    exit /b 1
)

REM Install AWS CDK CLI globally
echo.
echo Installing AWS CDK CLI...
call npm install -g aws-cdk

REM Install Python CDK dependencies
echo.
echo Installing Python CDK dependencies...
pip install -r requirements-cdk.txt

REM Check if config files are updated
echo.
echo Checking configuration files...
findstr /C:"YOUR_AWS_ACCOUNT_ID" config\stg_config.json >nul
if %errorlevel% == 0 (
    echo.
    echo WARNING: Please update config files with your AWS account details:
    echo   - config\dev_config.json
    echo   - config\stg_config.json
    echo   - config\prod_config.json
    echo.
    echo Update the following values:
    echo   - account: YOUR_AWS_ACCOUNT_ID
    echo   - vpc_id: vpc-XXXXX
    echo   - private_subnet_ids: [subnet-XXXXX, subnet-YYYYY]
    echo   - ecs.cluster_name: your-ecs-cluster-name
    echo   - s3.bucket_name: your-output-bucket
)

REM Bootstrap CDK (optional)
echo.
set /p bootstrap="Do you want to bootstrap CDK now? (y/n): "
if /i "%bootstrap%"=="y" (
    set /p account_id="Enter AWS Account ID: "
    set /p region="Enter AWS Region (e.g., us-east-1): "
    echo Bootstrapping CDK...
    cdk bootstrap aws://%account_id%/%region%
)

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Update config files with your AWS resources
echo 2. Run: cdk synth -c env=stg
echo 3. Run: cdk deploy llm-stg-metadata-scraper -c env=stg
echo.
echo For GitHub Actions deployment:
echo 1. Add GitHub Secrets (AWS_ACCESS_KEY_STG, AWS_SECRET_KEY_STG, AWS_REGION_STG)
echo 2. Push to task/* branch to trigger staging deployment
echo.
echo See CDK_DEPLOYMENT.md for detailed instructions

pause
