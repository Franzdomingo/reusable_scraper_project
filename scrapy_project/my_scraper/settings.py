"""
Scrapy settings for my_scraper project

For simplicity, this file contains only settings considered important or
commonly used. You can find more settings consulting the documentation:

    https://docs.scrapy.org/en/latest/topics/settings.html
    https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
    https://docs.scrapy.org/en/latest/topics/spider-middleware.html
"""

import os
import multiprocessing

BOT_NAME = 'my_scraper'

# Retry settings
RETRY_MAX_ATTEMPTS = 2  # Only try twice
RETRY_DELAY = 1  # Wait less time between attempts

SPIDER_MODULES = ['my_scraper.spiders']
NEWSPIDER_MODULE = 'my_scraper.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# IMPORTANT: Must match SELENIUM_POOL_SIZE to prevent spider from closing prematurely
# When using Selenium, Scrapy should only schedule as many requests as there are drivers available
# Scroll down to the variable SELENIUM_POOL_SIZE to see the number of selenium drivers it should be there - Franz
CONCURRENT_REQUESTS_AND_SELENIUM_POOL_SIZE = 8
CONCURRENT_REQUESTS = CONCURRENT_REQUESTS_AND_SELENIUM_POOL_SIZE

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-dela# See also autothrottle settings and docs
# Reduced delay to allow concurrent Selenium requests (AutoThrottle will manage actual delays)
DOWNLOAD_DELAY = 0.1
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 8
CONCURRENT_REQUESTS_PER_IP = 8

# Disable cookies (enabled by default)
COOKIES_ENABLED = True

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'my_scraper.middlewares.MyScraperSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'my_scraper.middlewares.RandomUserAgentMiddleware': 400,
    'my_scraper.middlewares.ProxyRotationMiddleware': 750,  # Before Selenium
    'my_scraper.middlewares.SeleniumMiddleware': 800,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
EXTENSIONS = {
    'my_scraper.extensions.ColoredLoggingExtension': 0,  # Load first (priority 0)
}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'my_scraper.pipelines.DataCleaningPipeline': 100,
    'my_scraper.pipelines.JsonExportPipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay - reduced to allow faster concurrent Selenium requests
AUTOTHROTTLE_START_DELAY = 0.1
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 3.0
# The average number of requests Scrapy should be sending in parallel to
# each remote server (increased to allow more concurrent Selenium drivers to be used)
AUTOTHROTTLE_TARGET_CONCURRENCY = 8.0
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# Logging settings
LOG_LEVEL = 'INFO'
LOG_FORMAT = '[%(asctime)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%H:%M:%S'

# Custom settings
SELENIUM_DRIVER_NAME = 'chrome'
SELENIUM_DRIVER_EXECUTABLE_PATH = None  # Uses system chromedriver
SELENIUM_DRIVER_ARGUMENTS = [
    '--headless',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-blink-features=AutomationControlled',
    '--disable-gpu',
    '--disable-extensions',
]
#Number of concurrent Selenium drivers (should match AUTOTHROTTLE_TARGET_CONCURRENCY)
SELENIUM_POOL_SIZE = CONCURRENT_REQUESTS_AND_SELENIUM_POOL_SIZE
# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
FEED_EXPORT_ENCODING = 'utf-8'

# Increase connection pool size to match concurrency settings
# This prevents "Connection pool is full" warnings
CONCURRENT_REQUESTS_TO_REMOTE_SERVER = CONCURRENT_REQUESTS_AND_SELENIUM_POOL_SIZE * 2

# Proxy rotation settings (disabled by default)
# To enable proxy rotation:
# 1. Set ENABLE_PROXY_ROTATION = True
# 2. Add proxy URLs to ROTATING_PROXIES list
# 3. Proxy format: 'http://username:password@host:port' or 'http://host:port'
# I disabled proxy rotation by default try not to increase selenium pool size and scrapy concurrency too much as it may lead to enabling proxies unnecessarily. - Franz 
ENABLE_PROXY_ROTATION = False
ROTATING_PROXIES = [
    # Example proxies (uncomment and replace with your proxies):
    # 'http://proxy1.example.com:8080',
    # 'http://proxy2.example.com:8080',
    # 'http://username:password@proxy3.example.com:8080',
]

# Performance monitoring and system info
CPU_COUNT = multiprocessing.cpu_count()
SYSTEM_MEMORY_GB = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024.**3) if hasattr(os, 'sysconf') else 'N/A'

# Display configuration on startup
import logging
logger = logging.getLogger(__name__)

# Suppress urllib3 connection pool warnings
import warnings
from urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)
logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)
