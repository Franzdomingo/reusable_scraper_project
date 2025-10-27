"""
Base Model field extraction for variations
"""

import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from my_scraper.extractors.retry_utils import retry_selenium_find

logger = logging.getLogger(__name__)


def extract_base_model(driver: webdriver.Chrome, base_model_selector, variation_counter: int) -> str:
    """
    Extract base model URL from the variation details section

    Args:
        driver: Selenium driver instance
        base_model_selector: Single selector or list of selectors (can be XPath or CSS)
        variation_counter: Current variation number for logging

    Returns:
        Base model URL path (e.g., "/models/keras/gemma/keras/gemma_2b_en") or empty string if not found
    """
    base_model_selectors = base_model_selector if isinstance(base_model_selector, list) else [base_model_selector] if base_model_selector else []

    for idx, bm_selector in enumerate(base_model_selectors):
        try:
            # Determine selector type (XPath or CSS)
            if bm_selector.startswith('/') or bm_selector.startswith('('):
                # XPath selector
                base_model_elem = retry_selenium_find(driver, By.XPATH, bm_selector)
            else:
                # CSS selector
                base_model_elem = retry_selenium_find(driver, By.CSS_SELECTOR, bm_selector)

            # Get the href attribute to extract the URL path
            base_model_url = base_model_elem.get_attribute('href')

            if base_model_url:
                # Extract just the path from the URL (remove domain if present)
                if 'kaggle.com' in base_model_url:
                    # Extract path after kaggle.com
                    base_model_url = '/' + base_model_url.split('kaggle.com/')[-1]

                # Clean and normalize the URL
                base_model_url = base_model_url.strip()

                logger.info(f"Variation {variation_counter}: Found base model URL '{base_model_url}' using selector {idx + 1}/{len(base_model_selectors)}")
                return base_model_url
        except Exception as e:
            logger.debug(f"Variation {variation_counter}: Base model selector {idx + 1}/{len(base_model_selectors)} failed: {e}")
            continue

    if base_model_selectors:
        logger.debug(f"Variation {variation_counter}: Could not find base model with any selector")

    return ''
