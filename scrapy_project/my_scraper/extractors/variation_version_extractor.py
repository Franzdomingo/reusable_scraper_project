"""
Version field extraction for variations
"""

import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from my_scraper.extractors.retry_utils import retry_selenium_find, retry_xpath, retry_click, retry_operation

logger = logging.getLogger(__name__)


def extract_version(driver: webdriver.Chrome, version_selector, variation_counter: int) -> str:
    """
    Extract version field using multiple selectors (CSS or XPath)

    Args:
        driver: Selenium driver instance
        version_selector: Single selector or list of selectors (can be CSS or XPath)
        variation_counter: Current variation number for logging

    Returns:
        Version string or empty string if not found
    """
    version_selectors = version_selector if isinstance(version_selector, list) else [version_selector] if version_selector else []

    for idx, ver_selector in enumerate(version_selectors):
        try:
            # Determine if this is an XPath or CSS selector
            if ver_selector.startswith('/') or ver_selector.startswith('('):
                # XPath selector
                version_elem = retry_selenium_find(driver, By.XPATH, ver_selector, max_retries=3, delay=0.5)
            else:
                # CSS selector
                version_elem = retry_selenium_find(driver, By.CSS_SELECTOR, ver_selector, max_retries=3, delay=0.5)

            variation_version = version_elem.text.strip()
            logger.info(f"Variation {variation_counter}: Found version '{variation_version}' using selector {idx + 1}/{len(version_selectors)}")
            return variation_version
        except Exception as e:
            logger.info(f"Variation {variation_counter}: Version selector {idx + 1}/{len(version_selectors)} failed: {e}")
            continue

    if version_selectors:
        logger.info(f"Variation {variation_counter}: Could not find version with any selector")

    return ''
