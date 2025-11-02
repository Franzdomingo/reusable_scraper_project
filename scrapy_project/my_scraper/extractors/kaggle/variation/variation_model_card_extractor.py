"""
Model card field extraction for variations
"""

import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from my_scraper.extractors.retry_utils import retry_selenium_find, retry_xpath, retry_click, retry_operation
from my_scraper.extractors.html_utils import convert_html_to_markdown

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
                logger.debug(f"Variation {variation_counter}: {selector_type} selector found 0 elements")
                continue

            logger.debug(f"Variation {variation_counter}: Found {len(model_card_elems)} elements matching selector")

            # Try each element until we find one with content
            for elem_idx, model_card_elem in enumerate(model_card_elems):
                try:
                    # Convert HTML to Markdown with inline links
                    text_content = convert_html_to_markdown(model_card_elem, driver)

                    # Only accept if it has meaningful content (> 5 chars)
                    if text_content and len(text_content) > 5:
                        logger.debug(f"Variation {variation_counter}: Extracted model card ({len(text_content)} chars)")

                        # Count and log markdown links
                        link_count = text_content.count('](')
                        if link_count > 0:
                            logger.debug(f"Variation {variation_counter}: Converted {link_count} links to Markdown format")

                        return text_content
                    else:
                        logger.debug(f"Variation {variation_counter}: Element {elem_idx + 1} has content too short ({len(text_content)} chars)")
                except Exception as elem_error:
                    logger.debug(f"Variation {variation_counter}: Error extracting text from element {elem_idx + 1}: {elem_error}")
                    continue
        except Exception as e:
            logger.debug(f"Variation {variation_counter}: Model card selector failed: {e}")
            continue

    # Log if field remains empty (this is expected and OK if selector doesn't exist)
    logger.debug(f"Variation {variation_counter}: No model card found")
    return ''
