# LLM Metadata Scraper - Architecture Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Selenium Integration](#selenium-integration)
6. [Extractor Architecture](#extractor-architecture)
7. [Concurrency Model](#concurrency-model)
8. [Configuration System](#configuration-system)
9. [Design Patterns](#design-patterns)
10. [Performance Optimization](#performance-optimization)

---

## Overview

The LLM Metadata Scraper is a Scrapy-based web scraper designed to extract metadata from AI model hosting platforms (Kaggle, NVIDIA). It combines Scrapy's asynchronous crawling framework with Selenium for JavaScript-heavy pages, using a modular extractor architecture for maintainable data extraction.

### Key Characteristics
- **Framework**: Scrapy 2.x with Selenium WebDriver integration
- **Browser**: Firefox (better anti-bot handling than Chrome)
- **Architecture**: Modular extractors with pure Selenium-based data extraction
- **Concurrency**: Thread-pool based Selenium driver pool with async request processing
- **Output**: JSON format with structured metadata

---

## System Architecture

### High-Level Architecture Flow

The system follows a linear data flow from user request to final output.

[See detailed step-by-step flow in Data Flow section below]

---

## Core Components

### 1. Spiders

Located in: `my_scraper/spiders/`

#### KaggleLinksSpider (`kaggle_links_spider.py`)
**Purpose**: Scrapes model URLs from Kaggle search pages

**Key Features**:
- Sequential pagination (1 concurrent request to avoid race conditions)
- Duplicate detection via `seen_urls` set
- Smart page change detection (monitors first model URL)
- Recursive parsing pattern (avoids creating new requests during pagination)

**Settings Override**:
```python
custom_settings = {
    'CONCURRENT_REQUESTS': 1,
    'SELENIUM_POOL_SIZE': 1,
    'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
}
```

**Output**: `kaggle_links_YYYYMMDD_HHMMSS.json`

#### KaggleMetadataSpider (`kaggle_metadata_spider.py`)
**Purpose**: Scrapes detailed metadata from Kaggle model pages

**Key Features**:
- Reads input from `kaggle_links` output (JSON) or CSV fallback
- Async/threaded extraction pattern for concurrent processing
- Extracts main metadata + nested variation items
- Uses `keep_driver=True` to retain driver for threaded extraction

**Data Extracted**:
- Model metadata (description, usability, tags, model card)
- Activity overview (downloads, views, engagements, timestamp)
- Model metadata (collaborators, authors, provenance)
- Variations (each with version-specific metadata)

**Concurrency Pattern**:
```python
# Spider sets keep_driver=True in request meta
meta={'keep_driver': True}

# Extraction runs in thread pool (allows concurrent processing)
async def parse(self, response):
    deferred = threads.deferToThread(
        self._extract_in_thread, response, driver, ...
    )
    item = await deferred_to_future(deferred)
```

**Output**: `kaggle_llm_model_metadata_YYYYMMDD_HHMMSS.json`

#### NvidiaModelsSpider (`nvidia_models_spider.py`)
**Purpose**: Scrapes NVIDIA model catalog

**Key Features**:
- Two-phase extraction: (1) main page data, (2) concurrent modelcard requests
- Infinite scroll handling with auto-scrolling
- Cookie popup dismissal
- Duplicate detection via URL and name tracking

**Concurrency Pattern**:
```python
# Phase 1: Extract all model data from main page
for idx in range(final_card_count):
    # Extract name, URL, tags, store in all_items[]

# Phase 2: Yield concurrent requests for model cards
for item in all_items:
    yield scrapy.Request(
        url=f"{model_url}/modelcard",
        callback=self.parse_modelcard,
        priority=1  # Higher priority for concurrent processing
    )
```

**Output**: `nvidia_llm_model_metadata_YYYYMMDD_HHMMSS.json`

### 2. Middleware

Located in: `my_scraper/middlewares.py`

#### SeleniumMiddleware
**Purpose**: Intercepts Scrapy requests and renders pages with Selenium

**Key Responsibilities**:
1. Manages thread-safe Selenium driver pool
2. Loads pages in separate threads (non-blocking)
3. Handles driver lifecycle (acquire → use → return)
4. Supports manual driver return for async spider operations

**Pool Initialization**:
```python
# Auto-calculated: 75% of CPU cores (min 2)
pool_size = max(2, int(CPU_COUNT * 0.75))
```

**Request Processing Flow**:
```python
def process_request(self, request, spider):
    if not request.meta.get('selenium'):
        return None  # Skip non-Selenium requests

    # Run in thread to avoid blocking reactor
    return threads.deferToThread(self._load_page_in_thread, request)

def _load_page_in_thread(self, request):
    driver = self.driver_pool.get(timeout=30)  # Blocks if pool empty
    self.active_drivers += 1
    driver.get(request.url)
    # ... wait for page load ...
    request.meta['driver'] = driver  # Pass to spider
    return HtmlResponse(...)
```

**Driver Return Patterns**:
1. **Automatic**: Middleware returns driver after `parse()` completes
2. **Manual**: Spider sets `keep_driver=True`, must call `middleware.return_driver_to_pool(driver)` later

#### RandomUserAgentMiddleware
**Purpose**: Rotates user agents to avoid detection

**Configuration**: Uses `GeneralSelectors.USER_AGENTS` list

### 3. Extractors

Located in: `my_scraper/extractors/`

**Core Principle**: All extractors use **pure Selenium** (NOT Scrapy selectors)

#### Extractor Structure

```python
def extract_field(driver: webdriver.Chrome, tree, selectors: Dict, name: str) -> str:
    """
    Extract a single field using multiple selector strategies

    Args:
        driver: Selenium WebDriver instance
        tree: lxml tree (for XPath queries)
        selectors: Selector configuration dict
        name: Model name (for logging)

    Returns:
        Extracted value or empty string on failure
    """
    for selector in selectors.get('field', []):
        try:
            element = retry_selenium_find(driver, By.CSS_SELECTOR, selector)
            return element.text.strip()
        except Exception as e:
            logger.debug(f"Selector {selector} failed: {e}")
    return ""
```

#### Site-Specific Extractors

**Kaggle Extractors** (`extractors/kaggle/`):
- `description_extractor.py` - Short description
- `downloads_extractor.py` - Download count
- `tags_extractor.py` - Tags (with "more" popup handling)
- `usability_extractor.py` - Usability score
- `collaborators_extractor.py` - Collaborator list (with expand button)
- `authors_extractor.py` - Author list (with expand button)
- `provenance_extractor.py` - Provenance info (with expand button)
- `model_card_extractor.py` - Model card markdown (with "Read more" button)
- `variations_extractor.py` - Orchestrates variation extraction
- `variation/` - Variation-specific extractors:
  - `version_popup_extractor.py` - Version list from popup
  - `variation_version_extractor.py` - Version number
  - `variation_downloads_extractor.py` - Variation downloads
  - `variation_license_extractor.py` - License info
  - `variation_base_model_extractor.py` - Base model reference
  - `variation_model_card_extractor.py` - Variation model card
  - `variation_is_finetunable_extractor.py` - Fine-tunable flag
  - `variation_example_usage_extractor.py` - Example usage code

**NVIDIA Extractors** (`extractors/nvidia/`):
- `nvidia_url_extractor.py` - Model name and URL
- `nvidia_tags_extractor.py` - Tags (with popover handling)
- `nvidia_modelcard_extractor.py` - Model card markdown

#### Utility Modules

**retry_utils.py**:
- `retry_operation()` - Generic retry wrapper
- `retry_selenium_find()` - Retry Selenium element finding
- `retry_xpath()` - Retry lxml XPath queries
- `retry_click()` - Retry element clicks with JS fallback

**Settings**:
```python
RETRY_MAX_ATTEMPTS = 2
RETRY_DELAY = 1  # seconds
```

**selenium_utils.py**:
- `parse_tree_from_response()` - Create lxml tree from response/driver
- `wait_for_element()` - Wait for element presence
- `click_element()` - Click with JS fallback
- `scroll_element_into_view()` - Scroll element into viewport
- `close_popup()` - Close popups by clicking body

**html_utils.py**:
- `convert_html_to_markdown()` - Convert HTML to Markdown with inline links
- `extract_links_from_element()` - Extract all hrefs from element

Supports multiple input types:
- Selenium WebElement
- lxml Element
- HTML string

### 4. Pipelines

Located in: `my_scraper/pipelines.py`

#### DataCleaningPipeline
**Purpose**: Clean and validate scraped data

**Operations**:
1. Clean text fields (remove excessive whitespace)
2. Convert usability to float
3. Clean nested metadata (collaborators, authors, provenance)
4. Parse formatted numbers in variations (e.g., "50.3k" → 50300)

#### JsonExportPipeline
**Purpose**: Export items to JSON file

**Features**:
- Creates `output/` directory if missing
- Generates timestamped filenames
- Custom filename mapping for known spiders
- Pretty-printed JSON (`indent=2`)

**Output Format**:
```json
[
  {
    "model_id": 1,
    "name": "gemma",
    "kaggle_url": "https://www.kaggle.com/models/...",
    "activity_overview": {
      "last_scraped": "2025-10-31T12:34:56",
      "total_downloads": 50300,
      "total_views": 123456,
      "total_engagements": 789.0
    },
    "variations": [
      {
        "variation": "transformers",
        "variation_name": "gemma_2b_en",
        "variation_downloads": 50300,
        ...
      }
    ]
  }
]
```

### 5. Configuration System

#### Selector Configuration (`selectors/site_selectors.py`)

**Architecture**:
- Site-specific selector classes (`KaggleSelectors`, `NvidiaSelectors`)
- Selectors organized by priority (most specific first)
- Supports both CSS and XPath selectors
- Fallback chains for resilience

**Example**:
```python
class KaggleSelectors:
    DESCRIPTION_SELECTORS: List[str] = [
        '/html/body/div/div[1]/div[2]/div/div[2]/div/div[2]/div[2]/div[1]/span/p[2]',  # Absolute XPath
        '.sc-ghOvAx > p:nth-child(2)',  # CSS selector
        '//div[@class="sc-guPfGz eukZsY"]//p[@style="margin-top: 40px;"]',  # Content-based XPath
    ]
```

**Selector Retrieval**:
```python
selectors = get_selectors_for_site('kaggle')
# Returns dict with all selectors for the site
```

#### Settings (`settings.py`)

**Concurrency Settings** (Auto-calculated):
```python
CPU_COUNT = multiprocessing.cpu_count()
CONCURRENT_REQUESTS_AND_SELENIUM_POOL_SIZE = max(2, int(CPU_COUNT * 0.75))

CONCURRENT_REQUESTS = CONCURRENT_REQUESTS_AND_SELENIUM_POOL_SIZE  # e.g., 6 on 8-core
SELENIUM_POOL_SIZE = CONCURRENT_REQUESTS_AND_SELENIUM_POOL_SIZE
AUTOTHROTTLE_TARGET_CONCURRENCY = float(CONCURRENT_REQUESTS_AND_SELENIUM_POOL_SIZE)
REACTOR_THREADPOOL_MAXSIZE = CONCURRENT_REQUESTS_AND_SELENIUM_POOL_SIZE * 2
```

**Selenium Settings**:
```python
SELENIUM_DRIVER_NAME = 'firefox'  # Better anti-bot handling
SELENIUM_DRIVER_ARGUMENTS = [
    '--headless',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-blink-features=AutomationControlled',
]
```

**AutoThrottle Settings**:
```python
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0  # Immediately utilize all drivers
AUTOTHROTTLE_MAX_DELAY = 3.0
```

---

## Data Flow

### Complete Request-to-Output Flow

The following describes the complete journey of a single scraping request from initiation to final output.

#### Step 1: User Initiates Scraping
```
User runs command:
$ python run.py kaggle_metadata
```

#### Step 2: Scrapy Engine Initialization
```
Scrapy Engine (Twisted Reactor) starts
  → Loads settings from settings.py
  → Calculates concurrency: POOL_SIZE = 75% of CPU cores (e.g., 6 on 8-core CPU)
  → Initializes middleware chain
  → Initializes pipelines
```

#### Step 3: Middleware Initialization
```
SeleniumMiddleware.spider_opened()
  → Creates driver pool (Queue)
  → Spawns N Firefox drivers (N = POOL_SIZE)
  → Firefox Driver 1 created ✓
  → Firefox Driver 2 created ✓
  → ...
  → Firefox Driver N created ✓
  → All drivers placed in thread-safe queue
  → Logs: "Driver Pool Ready: N/N drivers available"

RandomUserAgentMiddleware.from_crawler()
  → Loads user agent list from GeneralSelectors.USER_AGENTS
  → Ready to rotate user agents per request
```

#### Step 4: Spider Generates Requests
```
Spider.start_requests()
  → Reads input file (JSON/CSV for kaggle_metadata, or start_urls for others)
  → For each model URL:
      yield scrapy.Request(
        url="https://kaggle.com/models/...",
        callback=self.parse,
        meta={'selenium': True, 'selenium_wait': 3}
      )
  → Requests queued in Scrapy engine
```

#### Step 5: Request Processing (Middleware Chain)
```
For each request:

RandomUserAgentMiddleware.process_request()
  → Selects random user agent from list
  → Sets request.headers['User-Agent']
  → Passes request to next middleware

SeleniumMiddleware.process_request()
  → Checks if request.meta.get('selenium') == True
  → If True:
      → Offloads to thread pool: threads.deferToThread(_load_page_in_thread)
      → Returns Deferred (non-blocking)
  → If False:
      → Returns None (pass to standard Scrapy downloader)
```

#### Step 6: Page Loading (Threaded)
```
SeleniumMiddleware._load_page_in_thread() [runs in ThreadPoolExecutor]
  → Acquires driver from pool: driver = driver_pool.get(timeout=30)
      → If pool empty, blocks until driver available
  → Increments active_drivers counter (with thread lock)
  → Logs: "Acquired driver | Active: 2/6 | Available: 4"

  → Loads page: driver.get(request.url)
  → Waits for page load:
      → If selenium_wait_selector: WebDriverWait for specific element
      → Else: time.sleep(selenium_wait seconds)

  → Extracts page source: body = driver.page_source.encode('utf-8')
  → Stores driver in request metadata: request.meta['driver'] = driver
  → Creates HtmlResponse with page source
  → Logs: "Page loaded in X.XXs | Now parsing with spider..."
  → Returns HtmlResponse to Scrapy engine
```

#### Step 7: Spider Parsing
```
Spider.parse(response) [async method]
  → Retrieves driver: driver = response.meta.get('driver')
  → Retrieves model metadata: model_name, model_id

  → Option A: Direct Extraction (simple spiders)
      → Calls extractors directly
      → Creates item
      → yield item

  → Option B: Threaded Extraction (kaggle_metadata spider)
      → Offloads to thread pool:
          deferred = threads.deferToThread(
              self._extract_in_thread, response, driver, model_name, ...
          )
      → Awaits result: item = await deferred_to_future(deferred)
      → yield item
```

#### Step 8: Data Extraction (Extractor Layer)
```
Spider._extract_in_thread() or direct extractor calls [runs in thread if deferred]
  → Parses lxml tree: tree = parse_tree_from_response(response)

  → Calls site-specific extractors in sequence:
      1. extract_description(driver, tree, selectors, model_name)
         → Tries multiple selectors in priority order
         → Uses retry_selenium_find() for resilience
         → Returns: "Model for text generation"

      2. extract_downloads(driver, tree, selectors, model_name)
         → Returns: "50.3k"

      3. extract_tags(driver, tree, selectors, model_name)
         → Clicks "more" button if needed
         → Extracts visible tags + popup tags
         → Returns: ["nlp", "text-generation", "transformers"]

      4. extract_variations(driver, selectors, model_name, model_id, url)
         → Finds all variation tabs (Transformers, JAX, etc.)
         → For each tab:
             → Clicks tab
             → Opens variation dropdown
             → Extracts variation metadata (version, license, downloads, etc.)
             → Calls variation-specific extractors:
                 - variation_downloads_extractor.py
                 - variation_license_extractor.py
                 - variation_base_model_extractor.py
                 - variation_model_card_extractor.py
                 - variation_is_finetunable_extractor.py
                 - variation_example_usage_extractor.py
         → Returns: List[TransformersVariationItem]

  → Constructs item with all extracted data:
      item['name'] = model_name
      item['short_description'] = description
      item['tags'] = tags
      item['variations'] = variations
      item['activity_overview'] = {...}
      item['model_metadata'] = {...}

  → Returns item to spider
```

#### Step 9: Driver Return to Pool
```
If keep_driver=False (default):
  SeleniumMiddleware.process_response()
    → Retrieves driver: driver = request.meta['driver']
    → Decrements active_drivers counter (with thread lock)
    → Returns driver to pool: driver_pool.put(driver)
    → Logs: "← Returned driver to pool | Active: 1/6 | Available: 5"

If keep_driver=True (kaggle_metadata spider):
  Spider._extract_in_thread() finally block
    → Manually returns driver: middleware.return_driver_to_pool(driver)
    → Logs: "← Returned driver to pool (manual) | Active: 1/6 | Available: 5"
```

#### Step 10: Item Pipeline Processing
```
For each yielded item:

DataCleaningPipeline.process_item(item, spider)
  → Cleans text fields: clean_text(item['description'])
  → Converts numeric fields: float(item['usability'])
  → Parses formatted numbers in variations: "50.3k" → 50300
  → Returns cleaned item

JsonExportPipeline.process_item(item, spider)
  → Converts item to dict
  → Appends to in-memory buffer: self.items.append(dict(item))
  → Returns item
```

#### Step 11: Spider Completion
```
When all requests processed:

Spider finishes
  → No more pending requests
  → Scrapy signals spider_closed

SeleniumMiddleware.spider_closed(spider)
  → Logs shutdown statistics
  → Closes all drivers in pool:
      while not driver_pool.empty():
        driver = driver_pool.get_nowait()
        driver.quit()
  → Logs: "Driver Pool Shutdown Complete: N drivers closed"

JsonExportPipeline.close_spider(spider)
  → Writes buffered items to JSON file:
      filename = f"output/kaggle_llm_model_metadata_{timestamp}.json"
      json.dump(self.items, file, indent=2)
  → Logs: "Saved X items to output/..."
```

#### Step 12: Output Generated
```
Final output written to: output/kaggle_llm_model_metadata_YYYYMMDD_HHMMSS.json

Example structure:
[
  {
    "model_id": 1,
    "name": "gemma",
    "kaggle_url": "https://www.kaggle.com/models/...",
    "short_description": "...",
    "activity_overview": {
      "last_scraped": "2025-10-31T12:34:56",
      "total_downloads": 50300,
      "total_views": 123456,
      "total_engagements": 789.0
    },
    "variations": [
      {
        "variation": "transformers",
        "variation_name": "gemma_2b_en",
        "variation_version": "1",
        "variation_downloads": 50300,
        "variation_license": "gemma",
        ...
      }
    ]
  }
]
```



## Selenium Integration

### Driver Pool Architecture

**Purpose**: Enable concurrent Selenium operations without deadlocks

**Implementation**:
```python
class SeleniumMiddleware:
    def __init__(self, pool_size=8):
        self.driver_pool = Queue()  # Thread-safe FIFO queue
        self.lock = threading.Lock()
        self.active_drivers = 0

    def spider_opened(self, spider):
        # Initialize pool with N drivers
        for i in range(self.pool_size):
            driver = self._create_driver()
            self.driver_pool.put(driver)
```

**Pool Management**:
- **Acquisition**: `driver = self.driver_pool.get(timeout=30)` (blocks if empty)
- **Active Tracking**: Increment `active_drivers` with thread lock
- **Return**: `self.driver_pool.put(driver)` (manual or automatic)
- **Shutdown**: `driver.quit()` for all drivers in pool

**Pool Monitoring** (logged):
```
[SELENIUM POOL] Incoming request | URL: ... | Pool available: 5/6 | Active: 1
[SELENIUM POOL] Acquired driver | Active: 2/6 | Available: 4 | Total Processed: 15
[SELENIUM POOL] Page loaded in 2.34s | Now parsing with spider...
[SELENIUM POOL] ← Returned driver to pool | Active: 1/6 | Available: 5
```

### Thread Safety

**Critical Sections**:
```python
with self.lock:
    self.active_drivers += 1  # Atomic increment
    self.total_requests_processed += 1
```

**Queue Operations** (inherently thread-safe):
- `driver_pool.get()` - Blocks until driver available
- `driver_pool.put()` - Returns driver to pool

### Firefox vs Chrome

**Why Firefox?**:
- Better anti-bot detection handling for NVIDIA site
- No need for proxy rotation (Firefox + user agent sufficient)
- Disabled ChromeDriver verbose logging

**Configuration**:
```python
SELENIUM_DRIVER_NAME = 'firefox'
SELENIUM_DRIVER_ARGUMENTS = [
    '--headless',
    '--no-sandbox',
    '--disable-blink-features=AutomationControlled',  # Anti-detection
]
```

---

## Extractor Architecture

### Design Philosophy

1. **Pure Selenium**: Extractors use `driver.find_element()`, NOT `response.css()` or `response.xpath()`
2. **Fail-Safe**: Extractors return empty string/list on failure (never raise exceptions)
3. **Retry by Default**: Always use `retry_selenium_find()` instead of bare `find_element()`
4. **Selector Fallback**: Try multiple selectors in priority order
5. **Logging**: Log attempts at DEBUG, failures at WARNING, success at INFO

### Extractor Function Signature

```python
def extract_field(
    driver: webdriver.Chrome,
    tree,  # lxml tree (optional, for XPath queries)
    selectors: Dict,
    name: str  # Model name for logging context
) -> Union[str, List[str], int]:
    """
    Extract a field from the page

    Args:
        driver: Selenium WebDriver with page already loaded
        tree: lxml tree parsed from response
        selectors: Selector configuration dict from site_selectors.py
        name: Model name for contextual logging

    Returns:
        Extracted value or empty string/list on failure
    """
```

### Selector Strategy Pattern

**Multiple Selector Types**:
```python
selectors = [
    '/html/body/div[1]/...',  # Absolute XPath (fragile but precise)
    '.class-name > div',  # CSS selector
    '//div[contains(text(), "Label")]/following-sibling::p',  # Content-based XPath (stable)
]

for selector in selectors:
    try:
        if is_xpath_selector(selector):
            element = retry_selenium_find(driver, By.XPATH, selector)
        else:
            element = retry_selenium_find(driver, By.CSS_SELECTOR, selector)

        if element:
            return element.text.strip()
    except Exception as e:
        logger.debug(f"Selector failed: {selector} - {e}")
        continue

return ""  # All selectors failed
```

### Retry Mechanism

**retry_selenium_find()**:
```python
def retry_selenium_find(driver, by, selector, max_retries=2, delay=1, find_multiple=False):
    """
    Retry element finding with exponential backoff

    Handles transient failures:
    - StaleElementReferenceException
    - NoSuchElementException (temporary DOM state)
    - WebDriverException

    Returns:
        Element(s) or None/[] if all retries fail
    """
    for attempt in range(max_retries):
        try:
            if find_multiple:
                return driver.find_elements(by, selector)
            else:
                return driver.find_element(by, selector)
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    return [] if find_multiple else None
```

### Click Retry with JavaScript Fallback

```python
def retry_click(element, driver=None, max_retries=2, delay=1):
    """
    Retry clicking with JavaScript fallback on final attempt
    """
    for attempt in range(max_retries):
        try:
            element.click()
            return True
        except Exception as e:
            if driver and attempt == max_retries - 1:
                # Final attempt: JavaScript click
                driver.execute_script("arguments[0].click();", element)
                return True
            time.sleep(delay)
    return False
```

### HTML to Markdown Conversion

**Purpose**: Preserve links in extracted content (model cards, provenance, etc.)

**Usage**:
```python
from my_scraper.extractors.html_utils import convert_html_to_markdown

# Selenium WebElement
markdown = convert_html_to_markdown(web_element, driver)

# lxml Element
markdown = convert_html_to_markdown(lxml_element)

# HTML string
markdown = convert_html_to_markdown('<p>Check <a href="...">this link</a></p>')
# Output: "Check [this link](...)"
```

**Implementation**:
- Recursively processes element tree
- Converts `<a>` tags to `[text](url)` format
- Converts `<br>` to newlines
- Preserves text structure

---

## Concurrency Model

### Multi-Level Concurrency

The system uses 4 levels of concurrency working together:

#### Level 1: Scrapy Engine (Twisted Reactor)
```
Purpose: Async request scheduling
- Non-blocking I/O event loop
- Schedules multiple requests concurrently
- Setting: CONCURRENT_REQUESTS = 6 (75% of CPU cores)
- Handles: Request/response routing, middleware chain execution
```

#### Level 2: Selenium Driver Pool (Thread Queue)
```
Purpose: Manages reusable browser instances
- Pool size = 6 (matches CONCURRENT_REQUESTS)
- Thread-safe Queue for driver management
- Blocking queue.get() if pool empty (waits for available driver)
- Thread-safe acquire/return with lock protection
- Each driver is a persistent Firefox instance
```

#### Level 3: Twisted Thread Pool (for blocking operations)
```
Purpose: Prevents blocking the reactor with Selenium operations
- threads.deferToThread() wraps Selenium page loading
- Setting: REACTOR_THREADPOOL_MAXSIZE = 12 (2x pool size)
- Runs _load_page_in_thread() in separate threads
- Returns Deferred objects to maintain async flow
- Prevents reactor from freezing during driver.get()
```

#### Level 4: Spider Thread Pool (for heavy extraction)
```
Purpose: Allows blocking operations in data extraction
- KaggleMetadataSpider uses _extract_in_thread()
- Allows blocking operations: clicks, waits, navigation
- Multiple extractions run concurrently
- Each extraction can take several seconds without blocking others
- Used for: variation extraction, tab clicking, popup handling
```

**Concurrency Flow Example**:
```
1. Scrapy Engine schedules 6 requests concurrently (Level 1)
   ↓
2. Each request acquires a driver from pool (Level 2)
   ↓
3. Page load runs in Twisted thread pool (Level 3)
   └→ driver.get(url) - blocks this thread only
   ↓
4. Spider offloads extraction to thread pool (Level 4)
   └→ _extract_in_thread() - allows clicks, navigation
   ↓
5. Driver returned to pool (Level 2)
   ↓
6. Next request uses the same driver
```




### Concurrency Settings Calculation

**Auto-calculated based on CPU cores**:
```python
CPU_COUNT = multiprocessing.cpu_count()  # e.g., 8
POOL_SIZE = max(2, int(CPU_COUNT * 0.75))  # e.g., 6

# All settings synchronized
CONCURRENT_REQUESTS = POOL_SIZE  # 6
SELENIUM_POOL_SIZE = POOL_SIZE  # 6
AUTOTHROTTLE_TARGET_CONCURRENCY = float(POOL_SIZE)  # 6.0
REACTOR_THREADPOOL_MAXSIZE = POOL_SIZE * 2  # 12
```

**Why 75% of cores?**:
- Leaves headroom for OS and other processes
- Prevents resource exhaustion
- Balances throughput vs stability

### AutoThrottle Integration

**Purpose**: Dynamically adjust delays based on server response time

**Configuration**:
```python
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0  # Start fast (immediately use all drivers)
AUTOTHROTTLE_MAX_DELAY = 3.0  # Cap delay at 3 seconds
AUTOTHROTTLE_TARGET_CONCURRENCY = 6.0  # Target concurrent requests
```

**Behavior**:
- Monitors response latency
- Increases delay if server slows down
- Decreases delay when server responsive
- Prevents overwhelming target site

### Preventing Deadlocks

**Problem**: Spider closes prematurely if `CONCURRENT_REQUESTS` > `SELENIUM_POOL_SIZE`

**Solution**: Synchronize concurrency settings
```python
# IMPORTANT: Must match to prevent spider from closing prematurely
CONCURRENT_REQUESTS = SELENIUM_POOL_SIZE
```

**Why**: Scrapy closes spider when no more pending requests, but if requests are waiting for drivers, they're still "pending" from Scrapy's perspective.

---

## Design Patterns

### 1. Strategy Pattern (Selector Fallback)

**Intent**: Try multiple selector strategies in priority order

**Implementation**:
```python
selectors = [
    '//div[contains(text(), "Label")]/following-sibling::p',  # Stable content-based
    'div.specific-class > p',  # Class-based
    '/html/body/div[1]/div[2]/p',  # Absolute XPath
]

for selector in selectors:
    result = try_selector(selector)
    if result:
        return result
```

### 2. Object Pool Pattern (Driver Pool)

**Intent**: Reuse expensive Selenium driver instances

**Implementation**:
```python
class SeleniumMiddleware:
    def __init__(self, pool_size):
        self.pool = Queue()
        for _ in range(pool_size):
            self.pool.put(self._create_driver())

    def acquire(self):
        return self.pool.get()  # Blocks if empty

    def release(self, driver):
        self.pool.put(driver)
```

### 3. Deferred Execution Pattern (Async Spiders)

**Intent**: Offload blocking operations to thread pool

**Implementation**:
```python
async def parse(self, response):
    # Offload to thread
    deferred = threads.deferToThread(heavy_operation, response)

    # Await result
    result = await deferred_to_future(deferred)

    yield result
```

### 4. Extractor Pattern (Modular Data Extraction)

**Intent**: Separate extraction logic from spider orchestration

**Benefits**:
- Testable in isolation
- Reusable across spiders
- Easy to update selectors

**Structure**:
```
extractors/
├── kaggle/
│   ├── description_extractor.py
│   ├── downloads_extractor.py
│   ├── tags_extractor.py
│   ├── variations_extractor.py
│   ├── model_card_extractor.py
│   ├── variation/
│   │   ├── variation_downloads_extractor.py
│   │   ├── variation_license_extractor.py
│   │   └── ...
│   └── ...
├── nvidia/
│   ├── nvidia_tags_extractor.py
│   ├── nvidia_modelcard_extractor.py
│   └── ...
└── retry_utils.py, selenium_utils.py, html_utils.py
```

### 5. Pipeline Pattern (Data Processing)

**Intent**: Chain data transformations

**Implementation**:
```python
ITEM_PIPELINES = {
    'DataCleaningPipeline': 100,  # First
    'JsonExportPipeline': 300,    # Last
}

class DataCleaningPipeline:
    def process_item(self, item, spider):
        # Clean fields
        return item  # Pass to next pipeline
```

### 6. Factory Pattern (Settings Configuration)

**Intent**: Create site-specific configurations

**Implementation**:
```python
def get_selectors_for_site(site: str) -> Dict:
    selectors_map = {
        'kaggle': {...},
        'nvidia': {...},
    }
    return selectors_map.get(site, {})
```

---

## Performance Optimization

### 1. Driver Pool Sizing

**Formula**: `pool_size = max(2, int(CPU_COUNT * 0.75))`

**Rationale**:
- More drivers = higher throughput
- But: diminishing returns after 75% utilization
- Leaves headroom for OS processes

**Monitoring**:
```
[SELENIUM POOL] Incoming request | Pool available: 5/6 | Active: 1
```

### 2. AutoThrottle Configuration

**Start Delay = 0**: Immediately utilize all drivers
```python
AUTOTHROTTLE_START_DELAY = 0
```

**Max Delay = 3.0**: Cap delay to prevent over-throttling
```python
AUTOTHROTTLE_MAX_DELAY = 3.0
```

### 3. Concurrent Request Settings

**Synchronized Settings**:
```python
CONCURRENT_REQUESTS = POOL_SIZE
CONCURRENT_REQUESTS_PER_DOMAIN = POOL_SIZE
SELENIUM_POOL_SIZE = POOL_SIZE
AUTOTHROTTLE_TARGET_CONCURRENCY = float(POOL_SIZE)
```

**Why**: Ensures balanced request scheduling

### 4. Thread Pool Sizing

**Reactor Thread Pool**: `2x` driver pool size
```python
REACTOR_THREADPOOL_MAXSIZE = POOL_SIZE * 2  # 12 for 6 drivers
```

**Rationale**: Handles driver operations + other async tasks

### 5. Retry Configuration

**Max Retries = 2**: Balance speed vs resilience
```python
RETRY_MAX_ATTEMPTS = 2
```

**Delay = 1 second**: Allow DOM to stabilize
```python
RETRY_DELAY = 1
```

### 6. Page Load Optimization

**Selenium Wait Time**: 3 seconds (configurable per request)
```python
meta={
    'selenium': True,
    'selenium_wait': 3,
    'selenium_wait_selector': 'h2',  # Wait for specific element
}
```

**Smart Waiting**: Use `WebDriverWait` with expected conditions
```python
wait = WebDriverWait(driver, 10)
element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
```

### 7. Logging Optimization

**Suppress Verbose Logs**:
```python
# ChromeDriver logs to devnull
service = Service(log_path=os.devnull)

# Suppress urllib3 warnings
logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)
```

**Structured Logging**:
```
[SELENIUM POOL] [Thread: ThreadPoolExecutor-0_1] Acquired driver | Active: 2/6
[FAST PARSE] Extracting main page data for gemma
Variation 1: Found downloads '50.3k'
```

### 8. Memory Management

**Driver Cleanup**: Quit all drivers on spider close
```python
def spider_closed(self, spider):
    while not self.driver_pool.empty():
        driver = self.driver_pool.get_nowait()
        driver.quit()
```

**Item Buffering**: Pipelines buffer items in memory, write on close
```python
def open_spider(self, spider):
    self.items = []

def process_item(self, item, spider):
    self.items.append(dict(item))
    return item

def close_spider(self, spider):
    json.dump(self.items, self.file)
```

---

## Performance Metrics

### Typical Performance (8-core CPU)

**Driver Pool**:
- Pool size: 6 drivers (75% of 8 cores)
- Concurrent requests: 6
- Thread pool: 12 threads

**Throughput**:
- **Kaggle Links**: ~100 models/minute (sequential pagination)
- **Kaggle Metadata**: ~15-20 models/minute (with variations)
- **NVIDIA Models**: ~50-80 models/minute (with model cards)

**Resource Usage**:
- CPU: 60-80% average
- Memory: ~1.5-2 GB (6 Firefox instances)
- Network: Depends on page size, typically 5-10 Mbps

---

## Error Handling

### 1. Extractor Level

**Strategy**: Fail gracefully, return empty values
```python
def extract_field(driver, tree, selectors, name):
    try:
        for selector in selectors:
            try:
                element = retry_selenium_find(driver, By.CSS_SELECTOR, selector)
                if element:
                    return element.text.strip()
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
    except Exception as e:
        logger.error(f"Extractor failed for {name}: {e}")

    return ""  # Never raise
```

### 2. Spider Level

**Strategy**: Log errors, continue processing
```python
try:
    item = process_model(response)
    yield item
except Exception as e:
    logger.error(f"Error processing {model_name}: {e}")
    traceback.print_exc()
    # Continue to next model
```

### 3. Middleware Level

**Strategy**: Return driver to pool, return None
```python
try:
    driver.get(request.url)
    return HtmlResponse(...)
except Exception as e:
    logger.error(f"Error loading page: {e}")
    if driver:
        self.driver_pool.put(driver)  # Return to pool
    return None  # Scrapy will handle gracefully
```

### 4. Pipeline Level

**Strategy**: Skip invalid items
```python
def process_item(self, item, spider):
    try:
        # Clean item
        return item
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise DropItem(f"Invalid item: {e}")
```

---

## Testing Strategy

### Unit Testing

**Extractor Tests**:
```python
def test_extract_downloads():
    # Mock driver with test page
    driver = create_mock_driver(html='<span>50.3k</span>')

    downloads = extract_downloads(driver, tree, selectors, 'test_model')

    assert downloads == '50.3k'
```

### Integration Testing

**Spider Tests**:
```python
def test_kaggle_metadata_spider():
    # Use scrapy.contracts or manual testing
    spider = KaggleMetadataSpider(input_file='test_input.json')

    # Run spider
    results = list(spider.parse(response))

    assert len(results) > 0
    assert 'name' in results[0]
```

### Manual Testing

Manual testing is performed using ad-hoc scripts and local debugging helpers. These utility scripts are intended for local use and are not required for the core scraping pipeline.

---

## Future Enhancements

### 1. Distributed Crawling
- Use Scrapy-Redis for distributed queue
- Multiple machines sharing driver pool

### 2. Proxy Rotation
- Re-enable ProxyRotationMiddleware if needed
- Integrate with proxy services (ScraperAPI, BrightData)

### 3. Database Storage
- MongoDB pipeline for structured storage
- PostgreSQL for relational queries

### 4. Incremental Updates
- Track last scrape timestamp
- Only scrape changed models

### 5. API Integration
- Use Kaggle API for initial model discovery
- Selenium only for fields not in API

### 6. Monitoring & Alerting
- Prometheus metrics (requests/sec, errors, pool usage)
- Grafana dashboards
- Alert on failure rate > threshold

---

## Deployment

### Docker Deployment

**Dockerfile** (example):
```dockerfile
FROM python:3.11-slim

# Install Firefox and geckodriver
RUN apt-get update && apt-get install -y firefox-esr

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy project
COPY scrapy_project /app/scrapy_project
WORKDIR /app/scrapy_project

# Run spider
CMD ["python", "run.py", "kaggle_metadata"]
```

### Environment Variables

```bash
# Concurrency overrides
export CONCURRENT_REQUESTS=4
export SELENIUM_POOL_SIZE=4

# Selenium settings
export SELENIUM_DRIVER_NAME=firefox
export HEADLESS=true

# Output settings
export OUTPUT_DIR=/data/output
```

### Scheduling (cron)

```bash
# Daily scrape at 2 AM
0 2 * * * cd /app/scrapy_project && python run.py kaggle_metadata >> /var/log/scraper.log 2>&1
```

---

## Troubleshooting

### Common Issues

**1. Driver Pool Deadlock**
- **Symptom**: Spider hangs, no progress
- **Cause**: `CONCURRENT_REQUESTS > SELENIUM_POOL_SIZE`
- **Fix**: Ensure settings are synchronized

**2. StaleElementReferenceException**
- **Symptom**: Extractor fails intermittently
- **Cause**: DOM changed after element found
- **Fix**: Use retry_selenium_find() instead of bare find_element()

**3. Memory Leak**
- **Symptom**: Memory usage grows over time
- **Cause**: Drivers not properly closed
- **Fix**: Ensure spider_closed() is called, check driver.quit()

**4. Slow Scraping**
- **Symptom**: Lower throughput than expected
- **Cause**: Pool size too small, or AutoThrottle over-throttling
- **Fix**: Increase pool size, adjust AUTOTHROTTLE_MAX_DELAY

**5. Empty Results**
- **Symptom**: Extractors return empty strings
- **Cause**: Selectors outdated (site redesign)
- **Fix**: Update selectors in site_selectors.py

---

## References

### Documentation
- [Scrapy Documentation](https://docs.scrapy.org/)
- [Selenium WebDriver Docs](https://www.selenium.dev/documentation/)
- [Twisted Threads Documentation](https://docs.twisted.org/en/stable/core/howto/threading.html)

### Related Files
- `CLAUDE.md` - User instructions for AI assistant
- `README.md` - Project setup and usage
- `requirements.txt` - Python dependencies

### Code Locations
- **Spiders**: `my_scraper/spiders/`
- **Extractors**: `my_scraper/extractors/`
- **Middleware**: `my_scraper/middlewares.py`
- **Pipelines**: `my_scraper/pipelines.py`
- **Settings**: `my_scraper/settings.py`
- **Selectors**: `my_scraper/selectors/site_selectors.py`

---

**Last Updated**: 2025-11-03
**Architecture Version**: 1.0
**Maintainer**: Franz Pihllip G. Domingo
