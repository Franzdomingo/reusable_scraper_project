"""
Example usage field extraction for variations
"""

import logging
from selenium import webdriver
from selenium.webdriver.common.by import By

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
            example_usage_elem = driver.find_element(By.CSS_SELECTOR, eu_selector)

            # First check if it contains the "no usage guide" message
            # Look for the specific paragraph element
            try:
                no_guide_elem = example_usage_elem.find_element(By.CSS_SELECTOR, 'p.sc-hwddKA.dIsQKt')
                if no_guide_elem and 'This variation does not have a usage guide yet.' in no_guide_elem.text:
                    logger.info(f"Variation {variation_counter}: No usage guide available")
                    return ''
            except:
                pass  # No "no guide" message found, continue with extraction

            # Try to find the content div (sibling to the header)
            try:
                content_elem = example_usage_elem.find_element(By.CSS_SELECTOR, 'div.sc-lkCrJH.ghmUBs')
                variation_example_usage = content_elem.text.strip()
            except:
                # Fallback: get all text from parent (includes header)
                variation_example_usage = example_usage_elem.text.strip()
                # Remove the "Example Use" header if present at the start
                if variation_example_usage.startswith('Example Use\n'):
                    variation_example_usage = variation_example_usage[12:].strip()
                elif variation_example_usage.startswith('Example Use'):
                    variation_example_usage = variation_example_usage[11:].strip()

            if variation_example_usage:
                # Log truncated version (first 100 chars) to avoid log spam
                preview = variation_example_usage[:100] + '...' if len(variation_example_usage) > 100 else variation_example_usage
                logger.info(f"Variation {variation_counter}: Found example usage using selector {idx + 1}/{len(example_usage_selectors)} - Preview: {preview}")
                return variation_example_usage
        except Exception as e:
            logger.info(f"Variation {variation_counter}: Example usage selector {idx + 1}/{len(example_usage_selectors)} failed: {e}")
            continue

    if example_usage_selectors:
        logger.info(f"Variation {variation_counter}: Could not find example usage with any selector")

    return ''
