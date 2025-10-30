# Multi-stage Dockerfile for Scrapy web scraper
FROM python:3.11-slim

# Set environment variables
# Set DEBIAN_FRONTEND to noninteractive to avoid tzdata prompts during build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Manila

# Install system dependencies for Chrome/Chromium and Scrapy
RUN apt-get update && apt-get install -y --no-install-recommends \
    # timezone data so the container can be set to PH time
    tzdata \
    # Chrome dependencies
    wget \
    gnupg2 \
    ca-certificates \
    apt-transport-https \
    # Chromium and chromedriver
    chromium \
    chromium-driver \
    # Additional dependencies
    xvfb \
    && ln -snf /usr/share/zoneinfo/Asia/Manila /etc/localtime \
    && echo "Asia/Manila" > /etc/timezone \
    && dpkg-reconfigure -f noninteractive tzdata || true \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Set up Chrome/Chromium environment
ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    DISPLAY=:99

# Create working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY scrapy_project/requirements.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the scrapy_project application
COPY . .

# Copy the api module (project-level api directory must be in build context)
# When docker-compose build context is the repo root, the api folder is at ./api
COPY api /app/api

# Create output directories
RUN mkdir -p output api_output

# Set permissions for the project entrypoint inside scrapy_project
RUN chmod +x scrapy_project/run.py || true

# Default command: run all spiders (entrypoint is inside scrapy_project)
CMD ["python", "scrapy_project/run.py"]
