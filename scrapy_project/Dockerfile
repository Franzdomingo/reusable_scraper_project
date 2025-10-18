# Multi-stage Dockerfile for Scrapy web scraper
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for Chrome/Chromium and Scrapy
RUN apt-get update && apt-get install -y \
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
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Set up Chrome/Chromium environment
ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    DISPLAY=:99

# Create working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create output directory
RUN mkdir -p output

# Set permissions
RUN chmod +x run.py

# Default command: run all spiders
CMD ["python", "run.py"]
