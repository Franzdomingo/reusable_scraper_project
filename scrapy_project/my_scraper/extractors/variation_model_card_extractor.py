"""
Model card field extraction for variations
"""

import logging
from selenium import webdriver
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)


def extract_model_card(driver: webdriver.Chrome, model_card_selector, variation_counter: int) -> str:
    """
    Extract model card field using multiple selectors

    Args:
        driver: Selenium driver instance
        model_card_selector: Single selector or list of selectors (CSS or XPath)
        variation_counter: Current variation number for logging

    Returns:
        Model card text or empty string if not found
    """
    model_card_selectors = model_card_selector if isinstance(model_card_selector, list) else [model_card_selector] if model_card_selector else []

    for idx, mc_selector in enumerate(model_card_selectors):
        try:
            # Determine if selector is XPath or CSS
            # XPath selectors start with / or //
            if mc_selector.startswith('/'):
                by_type = By.XPATH
                selector_type = "XPath"
            else:
                by_type = By.CSS_SELECTOR
                selector_type = "CSS"

            # Try to find all matching elements (there might be multiple)
            model_card_elems = driver.find_elements(by_type, mc_selector)

            # If selector doesn't exist (0 elements found), skip and leave field empty
            if len(model_card_elems) == 0:
                logger.info(f"Variation {variation_counter}: {selector_type} selector '{mc_selector}' found 0 elements - skipping")
                continue

            logger.info(f"Variation {variation_counter}: Found {len(model_card_elems)} elements matching {selector_type} model card selector: '{mc_selector}'")

            # Try each element until we find one with content
            for elem_idx, model_card_elem in enumerate(model_card_elems):
                try:
                    # Get text content
                    text_content = model_card_elem.text.strip()

                    # Only accept if it has meaningful content (> 5 chars)
                    if text_content and len(text_content) > 5:
                        # Log truncated version (first 100 chars) to avoid log spam
                        preview = text_content[:100] + '...' if len(text_content) > 100 else text_content
                        logger.info(f"Variation {variation_counter}: Found model card - Preview: {preview}")
                        return text_content
                    else:
                        logger.info(f"Variation {variation_counter}: Element {elem_idx + 1} has content too short ({len(text_content)} chars)")
                except Exception as elem_error:
                    logger.info(f"Variation {variation_counter}: Error extracting text from element {elem_idx + 1}: {elem_error}")
                    continue
        except Exception as e:
            logger.info(f"Variation {variation_counter}: Model card selector failed: {e}")
            continue

    # Log if field remains empty (this is expected and OK if selector doesn't exist)
    logger.info(f"Variation {variation_counter}: Model card field will be empty (selector not found or no content)")
    return ''
