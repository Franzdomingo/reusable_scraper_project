"""
Example usage field extraction for variations
"""

import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from my_scraper.extractors.retry_utils import retry_selenium_find, retry_xpath, retry_click, retry_operation
from my_scraper.extractors.html_utils import convert_html_to_markdown

logger = logging.getLogger(__name__)


def extract_example_usage(driver: webdriver.Chrome, example_usage_selector, variation_counter: int) -> str:
    """
    Extract example usage field using multiple selectors

    Args:
        driver: Selenium driver instance
        example_usage_selector: Single selector or list of selectors
        variation_counter: Current variation number for logging

    Returns:
        Example usage text or empty string if not found
    """
    example_usage_selectors = example_usage_selector if isinstance(example_usage_selector, list) else [example_usage_selector] if example_usage_selector else []

    for idx, eu_selector in enumerate(example_usage_selectors):
        try:
            example_usage_elem = retry_selenium_find(driver, By.CSS_SELECTOR, eu_selector)

            # Check if it contains the "no usage guide" message
            if 'This variation does not have a usage guide yet.' in example_usage_elem.text:
                logger.debug(f"Variation {variation_counter}: No usage guide available")
                return ''

            # Convert HTML to Markdown with inline links
            variation_example_usage = convert_html_to_markdown(example_usage_elem, driver)

            # Remove the "Example Use" header if present at the start
            if variation_example_usage.startswith('Example Use\n'):
                variation_example_usage = variation_example_usage[12:].strip()
            elif variation_example_usage.startswith('Example Use'):
                variation_example_usage = variation_example_usage[11:].strip()

            if variation_example_usage:
                logger.debug(f"Variation {variation_counter}: Extracted example usage ({len(variation_example_usage)} chars)")

                # Count and log markdown links
                link_count = variation_example_usage.count('](')
                if link_count > 0:
                    logger.debug(f"Variation {variation_counter}: Converted {link_count} links to Markdown format")

                return variation_example_usage
        except Exception as e:
            logger.debug(f"Variation {variation_counter}: Example usage selector {idx + 1}/{len(example_usage_selectors)} failed: {e}")
            continue

    if example_usage_selectors:
        logger.debug(f"Variation {variation_counter}: No example usage found")

    return ''
