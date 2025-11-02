"""
License field extraction for variations
"""

import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from my_scraper.extractors.retry_utils import retry_selenium_find, retry_xpath, retry_click, retry_operation

logger = logging.getLogger(__name__)


def extract_license(driver: webdriver.Chrome, license_selector, variation_counter: int) -> str:
    """
    Extract license field using multiple selectors

    Args:
        driver: Selenium driver instance
        license_selector: Single selector or list of selectors (can be XPath or CSS)
        variation_counter: Current variation number for logging

    Returns:
        License string or empty string if not found
    """
    license_selectors = license_selector if isinstance(license_selector, list) else [license_selector] if license_selector else []

    for idx, lic_selector in enumerate(license_selectors):
        try:
            # Determine selector type (XPath or CSS)
            if lic_selector.startswith('/') or lic_selector.startswith('('):
                # XPath selector
                license_elem = retry_selenium_find(driver, By.XPATH, lic_selector)
            else:
                # CSS selector
                license_elem = retry_selenium_find(driver, By.CSS_SELECTOR, lic_selector)

            variation_license = license_elem.text.strip()

            # Clean license text - remove icon text and extra whitespace
            if variation_license:
                # Remove common icon texts
                variation_license = variation_license.replace('open_in_new', '').strip()
                # Remove multiple spaces
                variation_license = ' '.join(variation_license.split())

                logger.debug(f"Variation {variation_counter}: Extracted license: {variation_license}")
                return variation_license
        except Exception as e:
            logger.debug(f"Variation {variation_counter}: License selector {idx + 1}/{len(license_selectors)} failed: {e}")
            continue

    if license_selectors:
        logger.debug(f"Variation {variation_counter}: No license found")

    return ''
