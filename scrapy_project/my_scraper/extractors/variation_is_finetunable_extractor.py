"""
Is finetunable field extraction for variations
"""

import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from my_scraper.extractors.retry_utils import retry_selenium_find, retry_xpath, retry_click, retry_operation

logger = logging.getLogger(__name__)


def extract_is_finetunable(driver: webdriver.Chrome, is_finetunable_selector, variation_counter: int) -> str:
    """
    Extract is_finetunable field using multiple selectors (XPath and CSS)

    Args:
        driver: Selenium driver instance
        is_finetunable_selector: Single selector or list of selectors (can be XPath or CSS)
        variation_counter: Current variation number for logging

    Returns:
        'Yes' or 'No' or empty string if not found
    """
    is_finetunable_selectors = is_finetunable_selector if isinstance(is_finetunable_selector, list) else [is_finetunable_selector] if is_finetunable_selector else []

    for idx, ft_selector in enumerate(is_finetunable_selectors):
        try:
            # Determine if selector is XPath (starts with /) or CSS
            if ft_selector.startswith('/'):
                # Use XPath
                finetunable_elems = retry_selenium_find(driver, By.XPATH, ft_selector, max_retries=3, delay=0.5, find_multiple=True)
                selector_type = "XPath"
            else:
                # Use CSS
                finetunable_elems = retry_selenium_find(driver, By.CSS_SELECTOR, ft_selector, max_retries=3, delay=0.5, find_multiple=True)
                selector_type = "CSS"

            logger.info(f"Variation {variation_counter}: Found {len(finetunable_elems)} elements matching is_finetunable {selector_type} selector {idx + 1}")

            # Look for element with "Yes" or "No" text
            for elem in finetunable_elems:
                text = elem.text.strip()
                # Check if it's a Yes/No value (case-insensitive)
                if text.lower() in ['yes', 'no']:
                    logger.info(f"Variation {variation_counter}: Found is_finetunable '{text}' using {selector_type} selector {idx + 1}/{len(is_finetunable_selectors)}")
                    return text
        except Exception as e:
            logger.info(f"Variation {variation_counter}: Is_finetunable selector {idx + 1}/{len(is_finetunable_selectors)} failed: {e}")
            continue

    if is_finetunable_selectors:
        logger.info(f"Variation {variation_counter}: Could not find is_finetunable with any selector")

    return ''
