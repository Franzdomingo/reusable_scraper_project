"""
Test script for download method extractor
Tests extraction of download methods from Kaggle model pages
"""

import sys
import os
import logging

# Add the scrapy_project directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scrapy_project'))

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from my_scraper.extractors.kaggle.variation.variation_download_method_extractor import extract_download_methods

# Set up logging
logging.basicConfig(level=logging.DEBUG)  # Changed to DEBUG for more details
logger = logging.getLogger(__name__)


def test_download_method_extraction():
    """Test download method extraction on a real Kaggle model page"""

    # Test URL - using ai21labs model that has download button
    test_url = "https://www.kaggle.com/models/ai21labs/ai21-jamba-reasoning-3b"

    # Set up Firefox driver
    firefox_options = FirefoxOptions()
    # firefox_options.add_argument('--headless')  # Comment out to see browser
    firefox_options.set_preference('general.useragent.override',
                                   'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    driver = None
    try:
        logger.info(f"Initializing Firefox driver...")
        driver = webdriver.Firefox(options=firefox_options)

        logger.info(f"Navigating to: {test_url}")
        driver.get(test_url)

        # Wait for page to load
        import time
        time.sleep(3)

        logger.info("Extracting download methods...")
        download_methods = extract_download_methods(driver, variation_counter=1)

        logger.info(f"\nExtracted {len(download_methods)} download methods:")
        logger.info("="*80)

        for idx, method in enumerate(download_methods):
            logger.info(f"\nMethod {idx + 1}:")
            logger.info(f"  Name: {method.get('download_method_name', '')}")
            command = method.get('download_method_command', '')
            if command:
                logger.info(f"  Command ({len(command)} chars): {command[:200]}..." if len(command) > 200 else f"  Command: {command}")
            else:
                logger.info(f"  Command: [EMPTY]")
            logger.info("-"*80)

        # Verify we got some results
        if len(download_methods) > 0:
            logger.info("\n✓ Test PASSED - Successfully extracted download methods")
            return True
        else:
            logger.warning("\n✗ Test FAILED - No download methods extracted")
            return False

    except Exception as e:
        logger.error(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if driver:
            logger.info("Closing driver...")
            driver.quit()


if __name__ == '__main__':
    logger.info("Starting download method extractor test...")
    success = test_download_method_extraction()
    sys.exit(0 if success else 1)
