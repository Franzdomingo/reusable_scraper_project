# Testing Guide

## Prerequisites

- Docker and Docker Compose installed
- Or Python 3.11+ with Chrome/Chromium (for local testing)

## Testing Steps

### Option 1: Quick Docker Test (Recommended)

#### Step 1: Build the Docker Image

```bash
cd C:\Users\orste\Documents\reusable_scraper_project\reusable_scraper_project\scrapy_project

# Build the image
docker-compose build
```

Expected output:
- Should download Python base image
- Install system dependencies (Chromium, ChromeDriver)
- Install Python dependencies from requirements.txt
- Copy project files
- Complete without errors

#### Step 2: Test with a Single Spider (Quick Test)

Test with kaggle_links spider (limited pages):

```bash
docker-compose run scraper python run.py kaggle_links -a max_pages=2
```

Expected output:
```
============================================================
Running: scrapy crawl kaggle_links -a max_pages=2
============================================================
[scrapy.utils.log] INFO: Scrapy 2.11.x started
[scrapy.core.engine] INFO: Spider opened
... (scraping progress)
[scrapy.core.engine] INFO: Closing spider (finished)
```

Check the output:
```bash
ls output/
```

You should see a file like: `kaggle_links_YYYYMMDD_HHMMSS.json`

#### Step 3: Verify Output Data

```bash
# View the first few lines of the output
cat output/kaggle_links_*.json | head -20
```

Should show JSON data with model names and URLs.

### Option 2: Test All Scrapers in Sequence

Run all three scrapers (takes longer):

```bash
docker-compose up
```

Or:

```bash
docker-compose run scraper python run.py
```

Expected output:
```
============================================================
RUNNING ALL SPIDERS IN SEQUENCE
============================================================

============================================================
Running: scrapy crawl kaggle_links -a max_pages=100
============================================================
... (kaggle_links runs)

============================================================
Running: scrapy crawl kaggle_metadata
============================================================
... (kaggle_metadata runs)

============================================================
Running: scrapy crawl nvidia_models
============================================================
... (nvidia_models runs)

============================================================
EXECUTION SUMMARY
============================================================
kaggle_links         - SUCCESS
kaggle_metadata      - SUCCESS
nvidia_models        - SUCCESS
============================================================
```

Check outputs:
```bash
ls -lh output/
```

You should see:
- `kaggle_links_*.json`
- `kaggle_metadata_*.json`
- `nvidia_models_*.json`

### Option 3: Local Testing (Without Docker)

If you want to test locally without Docker:

#### Step 1: Install Dependencies

```bash
cd C:\Users\orste\Documents\reusable_scraper_project\reusable_scraper_project\scrapy_project

# Install Python dependencies
pip install -r requirements.txt

# Make sure Chrome/Chromium and ChromeDriver are installed
```

#### Step 2: Test run.py

```bash
# Test help/info
python run.py unknown_spider

# Test single spider with limited pages
python run.py kaggle_links -a max_pages=2

# Test all spiders
python run.py
```

## Verification Checklist

After running tests, verify:

- [ ] Docker image builds successfully
- [ ] No errors during spider execution
- [ ] Output files are created in `output/` directory
- [ ] JSON files contain valid data
- [ ] No "menu" or "interactive prompts" appear
- [ ] Scrapers run headless (no browser windows)

## Common Issues & Solutions

### Issue 1: "No module named 'scrapy'"
**Solution:** Dependencies not installed
```bash
docker-compose build
```

### Issue 2: "Chrome/ChromeDriver not found"
**Solution:** Docker image should include Chromium. Rebuild:
```bash
docker-compose build --no-cache
```

### Issue 3: Empty output files
**Solution:** Check logs for errors. May need to adjust selectors or wait times.

### Issue 4: Permission errors on output directory
**Solution:** Create output directory first:
```bash
mkdir -p output
chmod 777 output  # Linux/Mac
```

## Quick Validation Commands

Check if everything is working:

```bash
# 1. Build succeeds
docker-compose build

# 2. Container runs
docker-compose run scraper python --version

# 3. Scrapy is installed
docker-compose run scraper scrapy version

# 4. run.py is executable
docker-compose run scraper python run.py unknown_spider

# 5. Run a quick test
docker-compose run scraper python run.py kaggle_links -a max_pages=1
```

## Performance Testing

To test performance with different configurations:

```bash
# Small test (fast, ~1-2 minutes)
docker-compose run scraper python run.py kaggle_links -a max_pages=2

# Medium test (~5-10 minutes)
docker-compose run scraper python run.py kaggle_links -a max_pages=10

# Full test (longer, ~30+ minutes)
docker-compose up
```

## Success Criteria

✅ **Test Passed** if:
1. Docker image builds without errors
2. Scrapers run without crashes
3. Output files are generated
4. JSON data is valid and contains expected fields
5. No interactive prompts appear
6. Process exits with code 0

❌ **Test Failed** if:
1. Build errors occur
2. Scrapers crash with exceptions
3. No output files generated
4. Empty or invalid JSON
5. Interactive menus appear
6. Process hangs indefinitely
