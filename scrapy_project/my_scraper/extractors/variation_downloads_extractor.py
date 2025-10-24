"""
Downloads field extraction for variations
"""

import logging
from typing import Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from my_scraper.extractors.retry_utils import retry_selenium_find, retry_xpath, retry_click, retry_operation

logger = logging.getLogger(__name__)


def extract_downloads(driver: webdriver.Chrome, selectors: Dict, variation_counter: int) -> str:
    """
    Extract downloads field using XPath first, then CSS selector as fallback

    Args:
        driver: Selenium driver instance
        selectors: Selectors configuration dictionary
        variation_counter: Current variation number for logging

    Returns:
        Downloads string or empty string if not found
    """
    variation_downloads = ''
    downloads_xpath_selector = selectors.get('variation_downloads_xpath')
    downloads_css_selector = selectors.get('variation_downloads')

    # Try XPath selector first
    if downloads_xpath_selector:
        try:
            downloads_elem = retry_selenium_find(driver, By.XPATH, downloads_xpath_selector, max_retries=3, delay=0.5)
            text = downloads_elem.text.strip()
            if text:
                variation_downloads = text
                logger.info(f"Variation {variation_counter}: Found downloads '{variation_downloads}' using XPath selector")
                return variation_downloads
        except Exception as e:
            logger.info(f"Variation {variation_counter}: XPath downloads selector failed: {e}")

    # Try CSS selector as fallback
    if downloads_css_selector:
        try:
            # Find all matching elements to ensure we get the right one
            downloads_elems = retry_selenium_find(driver, By.CSS_SELECTOR, downloads_css_selector, max_retries=3, delay=0.5, find_multiple=True)
            logger.info(f"Variation {variation_counter}: Found {len(downloads_elems)} elements matching CSS downloads selector")

            # Look for the element with numeric content only (no text)
            for idx, elem in enumerate(downloads_elems):
                text = elem.text.strip()
                # Check if text is numeric (digits only, possibly with K/M suffix)
                if text and (text.isdigit() or (text[:-1].isdigit() and text[-1] in ['K', 'M', 'k', 'm'])):
                    variation_downloads = text
                    logger.info(f"Variation {variation_counter}: Found downloads '{variation_downloads}' from CSS element {idx + 1}/{len(downloads_elems)}")
                    return variation_downloads

            # If no numeric-only element found, use the first one as fallback
            if len(downloads_elems) > 0:
                variation_downloads = downloads_elems[0].text.strip()
                logger.info(f"Variation {variation_counter}: Using first CSS element for downloads: '{variation_downloads}'")
                return variation_downloads
        except Exception as e:
            logger.info(f"Variation {variation_counter}: Could not find downloads with CSS: {e}")

    if not variation_downloads:
        logger.info(f"Variation {variation_counter}: Could not find downloads with any selector")

    return variation_downloads
