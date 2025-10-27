# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LLM Metadata Scraper - A Scrapy-based web scraper that extracts metadata from AI model hosting platforms (Kaggle, NVIDIA). Uses Selenium for JavaScript rendering and a modular extractor architecture for data extraction.

## Common Commands

### Setup & Environment
Windows PowerShell:
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r scrapy_project\requirements.txt
```

macOS/Linux:
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r scrapy_project/requirements.txt
```

### Running Spiders

Windows:
```powershell
# Interactive menu
python scrapy_project\main.py

# List all spiders
python scrapy_project\main.py --list

# Run specific spider
python scrapy_project\run.py kaggle_metadata

# Run with arguments
python scrapy_project\run.py kaggle_links -a max_pages=10
```

macOS/Linux:
```bash
# Interactive menu
python scrapy_project/main.py

# List all spiders
python scrapy_project/main.py --list

# Run specific spider
python scrapy_project/run.py kaggle_metadata

# Run with arguments
python scrapy_project/run.py kaggle_links -a max_pages=10
```

Available spiders:
- `kaggle_links` - Scrapes model URLs from Kaggle search pages
- `kaggle_metadata` - Scrapes detailed metadata from Kaggle model pages
- `nvidia_models` - Scrapes NVIDIA model catalog

## Architecture

### Data Flow
1. **Spider** (`my_scraper/spiders/*.py`) - Generates Scrapy requests, orchestrates extraction
2. **Selenium Middleware** (`middlewares.py:SeleniumMiddleware`) - Intercepts requests, renders pages with Selenium driver pool
3. **Extractors** (`my_scraper/extractors/`) - Pure data extraction functions using Selenium WebDriver
4. **Pipelines** (`pipelines.py`) - Data cleaning and export (JSON/CSV)

### Selenium Integration
- **Driver Pool**: Thread-safe pool of Selenium drivers (default: 8 concurrent drivers)
- **Middleware Pattern**: SeleniumMiddleware intercepts Scrapy requests and renders pages
- **Async Processing**: Uses Twisted threads to prevent blocking the reactor
- **Key setting**: `SELENIUM_POOL_SIZE` in `settings.py` (should match `AUTOTHROTTLE_TARGET_CONCURRENCY`)

### Extractor Architecture
**Critical**: All extractors use **pure Selenium** for data extraction (NOT Scrapy selectors)

- Extractors are functions that accept `driver: webdriver.Chrome` and return extracted data
- Located in `my_scraper/extractors/{site}/` (e.g., `kaggle/`, `nvidia/`)
- **Always use retry utilities** from `retry_utils.py`:
  - `retry_selenium_find()` instead of `driver.find_element()`
  - `retry_click()` for clicking elements
  - `retry_xpath()` for lxml tree queries
- Retry settings: `RETRY_MAX_ATTEMPTS=2`, `RETRY_DELAY=0.5` in `settings.py`

Example extractor pattern:
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from my_scraper.extractors.retry_utils import retry_selenium_find

def extract_field(driver: webdriver.Chrome, selectors: Dict, name: str) -> str:
    for selector in selectors.get('field', []):
        try:
            element = retry_selenium_find(driver, By.CSS_SELECTOR, selector)
            return element.text.strip()
        except Exception as e:
            logger.debug(f"Selector {selector} failed: {e}")
    return ""
```

### Selector Configuration
- Selectors defined in `my_scraper/selectors/site_selectors.py`
- Classes: `KaggleSelectors`, `NvidiaSelectors`, `GeneralSelectors`
- Organized by priority (most specific first)
- Supports both CSS and XPath selectors

### Concurrency Settings
Performance tuned for concurrent Selenium operations:
- `CONCURRENT_REQUESTS = 32`
- `SELENIUM_POOL_SIZE = 8`
- `AUTOTHROTTLE_TARGET_CONCURRENCY = 8.0`
- `DOWNLOAD_DELAY = 0.1` (AutoThrottle manages actual delays)

### Spider-Specific Details

**kaggle_metadata spider**:
- Reads input from `kaggle_links` spider output (JSON) or CSV fallback
- Uses threaded async pattern for page loading and variation extraction
- Extracts main metadata + transformers variations (nested items)
- Outputs to `output/kaggle_metadata_{timestamp}.json`

**Variation extraction pattern**:
- Clicks version popups to load variation data
- Concurrent thread-based extraction for multiple variations per model
- Each variation has its own set of extractors in `extractors/kaggle/variation/`

## Code Style & Patterns

### Logging
- Use variation counters in logs for tracking: `logger.info(f"Variation {variation_counter}: Found downloads '{value}'")`
- Log selector attempts and failures at DEBUG level
- Log successful extractions at INFO level

### Error Handling
- Extractors return empty string/list on failure (never raise exceptions to spider)
- Use try-except blocks in extractors with specific logging
- Retry utilities handle transient Selenium failures

### File Organization
```
my_scraper/
├── spiders/              # Spider definitions
├── extractors/           # Data extraction logic
│   ├── kaggle/          # Kaggle-specific extractors
│   │   └── variation/   # Variation-specific extractors
│   ├── nvidia/          # NVIDIA-specific extractors
│   └── retry_utils.py   # Retry utilities (ALWAYS USE THESE)
├── selectors/           # CSS/XPath selector definitions
├── middlewares.py       # Selenium middleware
├── pipelines.py         # Data cleaning & export
└── settings.py          # Scrapy configuration
```

## Important Notes

- **No Scrapy selectors**: Codebase uses `driver.find_element()` directly, not `response.css()` or `response.xpath()`
- **Proxy rotation**: Disabled by default (`ENABLE_PROXY_ROTATION = False`), enable only if necessary
- **ChromeDriver required**: Ensure ChromeDriver is installed and on PATH for Selenium
- **Output location**: Spiders output to `output/` directory by default
- **Input chaining**: `kaggle_metadata` reads from `kaggle_links` output automatically
