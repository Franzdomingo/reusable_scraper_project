# LLM Metadata Scraper - Docker Setup

This is a simplified, terminal-based scraper for collecting LLM model metadata from Kaggle and NVIDIA.

## Prerequisites

- Docker
- Docker Compose (optional, but recommended)

## Quick Start

### Option 1: Run All Scrapers (Recommended)

Run all scrapers in sequence (kaggle_links → kaggle_metadata → nvidia_models):

```bash
# Using docker-compose
docker-compose up

# Or using Docker directly
docker build -t llm-scraper .
docker run -v ./output:/app/output llm-scraper
```

### Option 2: Run Individual Spiders

#### Using Docker Compose

```bash
# Run kaggle_links spider
docker-compose run scraper python run.py kaggle_links -a max_pages=10

# Run kaggle_metadata spider
docker-compose run scraper python run.py kaggle_metadata

# Run nvidia_models spider
docker-compose run scraper python run.py nvidia_models
```

#### Using Docker Directly

```bash
# Build the image
docker build -t llm-scraper .

# Run individual spiders
docker run -v ./output:/app/output llm-scraper python run.py kaggle_links -a max_pages=10
docker run -v ./output:/app/output llm-scraper python run.py kaggle_metadata
docker run -v ./output:/app/output llm-scraper python run.py nvidia_models
```

## Available Spiders

1. **kaggle_links** - Scrapes model names and URLs from Kaggle
   - Arguments:
     - `max_pages`: Maximum pages to scrape (default: 100)
   - Example: `python run.py kaggle_links -a max_pages=10`

2. **kaggle_metadata** - Scrapes detailed metadata from Kaggle model pages
   - Automatically finds output from kaggle_links spider
   - Example: `python run.py kaggle_metadata`

3. **nvidia_models** - Scrapes model metadata from NVIDIA Build
   - Example: `python run.py nvidia_models`

## Output

All scraped data is saved to the `output/` directory:

```
output/
├── kaggle_links_YYYYMMDD_HHMMSS.json    # Kaggle model links
├── kaggle_metadata_YYYYMMDD_HHMMSS.json # Kaggle metadata
└── nvidia_models_YYYYMMDD_HHMMSS.json   # NVIDIA metadata
```

## Workflow

1. **First**: Run `kaggle_links` to get model URLs
2. **Second**: Run `kaggle_metadata` to get detailed metadata (uses output from step 1)
3. **Third**: Run `nvidia_models` to get NVIDIA model data

Or simply run without arguments to execute all three in sequence:
```bash
docker-compose up
```

## Advanced Usage

### Custom Arguments

```bash
# Limit Kaggle pages
docker-compose run scraper python run.py kaggle_links -a max_pages=5

# Use specific input file for metadata
docker-compose run scraper python run.py kaggle_metadata -a input_file=output/custom.json
```

### Debugging

To access the container for debugging:

```bash
docker-compose run scraper /bin/bash
```

### Rebuild After Changes

```bash
docker-compose build
# or
docker build -t llm-scraper .
```

## Notes

- The Docker image includes Chromium and ChromeDriver for Selenium automation
- Output files are persisted via volume mounts
- Scrapers run headless (no GUI)
- All terminal interactions have been removed
