"""
Test script for version popup extraction
Tests the two-phase extraction approach for version metadata
"""

import sys
import os
import logging
import time

# Add the scrapy_project directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scrapy_project'))

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from my_scraper.extractors.kaggle.variation.version_popup_extractor import extract_versions_from_popup
from my_scraper.selectors.site_selectors import get_selectors_for_site

# Set up logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)


def test_version_popup_extraction():
    """Test version popup extraction on a real Kaggle model page"""

    # Test URL - using ai21labs model that has multiple versions
    test_url = "https://www.kaggle.com/models/ai21labs/ai21-jamba-reasoning-3b"

    # Set up Firefox driver
    firefox_options = FirefoxOptions()
    firefox_options.set_preference('general.useragent.override',
                                   'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    driver = None
    try:
        logger.info("Initializing Firefox driver...")
        driver = webdriver.Firefox(options=firefox_options)

        logger.info(f"Navigating to: {test_url}")
        driver.get(test_url)

        # Wait for page to load
        time.sleep(3)

        # Get selectors
        selectors = get_selectors_for_site('kaggle')
        base_url = test_url

        logger.info("Extracting versions from popup...")
        versions_data = extract_versions_from_popup(driver, selectors, base_url, variation_counter=1)

        logger.info(f"\n{'='*80}")
        logger.info(f"Extracted {len(versions_data)} versions:")
        logger.info(f"{'='*80}\n")

        for idx, version in enumerate(versions_data):
            logger.info(f"Version {idx + 1}:")
            logger.info(f"  Version Number: '{version.get('version_number', '')}'")
            logger.info(f"  Created By: '{version.get('created_by', '')}'")
            logger.info(f"  Update Description: '{version.get('update_description', '')}'")
            logger.info(f"  Downloads: '{version.get('downloads', '')}'")
            logger.info(f"  License: '{version.get('license', '')}'")
            logger.info(f"  Base Model: '{version.get('base_model', '')}'")
            logger.info(f"  Is Finetunable: '{version.get('is_finetunable', '')}'")
            logger.info(f"  Download Methods: {len(version.get('download_methods', []))} methods")
            logger.info(f"-"*80)

        # Verify we got some results
        if len(versions_data) > 0:
            # Check if Version 1 (usually the second in list) has metadata
            has_metadata_issue = False
            for idx, version in enumerate(versions_data):
                version_num = version.get('version_number', '')
                created_by = version.get('created_by', '')
                update_desc = version.get('update_description', '')

                if not created_by and not update_desc:
                    logger.warning(f"\n⚠ Version '{version_num}' is missing metadata (created_by and update_description are empty)")
                    has_metadata_issue = True

            if has_metadata_issue:
                logger.warning("\n✗ Test FAILED - Some versions are missing metadata")
                return False
            else:
                logger.info("\n✓ Test PASSED - All versions have metadata")
                return True
        else:
            logger.warning("\n✗ Test FAILED - No versions extracted")
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
    logger.info("Starting version popup extraction test...")
    success = test_version_popup_extraction()
    sys.exit(0 if success else 1)
