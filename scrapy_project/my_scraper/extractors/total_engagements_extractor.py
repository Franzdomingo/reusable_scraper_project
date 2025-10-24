"""
Total engagements extraction functions
"""

import logging
from typing import Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from lxml import html as lxml_html
from my_scraper.utils import is_numeric_value, is_css_selector, is_xpath_selector
from my_scraper.extractors.retry_utils import retry_selenium_find, retry_xpath, retry_click, retry_operation

logger = logging.getLogger(__name__)


def extract_total_engagements(driver: webdriver.Chrome, tree: lxml_html.HtmlElement,
                               selectors: Dict, name: str) -> str:
    """
    Extract total engagements count using configured selectors

    Args:
        driver: Selenium driver instance (for dynamic content)
        tree: lxml tree object
        selectors: Selectors configuration dictionary
        name: Model name for logging

    Returns:
        Extracted total engagements count or empty string
    """
    total_engagements = ""

    # If no driver, can't extract total engagements (requires JavaScript rendering)
    if not driver:
        logger.debug(f"No driver provided, skipping total engagements extraction for {name}")
        return total_engagements

    # Wait a moment for dynamic content to load
    import time
    time.sleep(1)

    # Try selectors via Selenium for dynamic content
    for selector in selectors.get('total_engagements', []):
        # Use smart selector detection
        if is_css_selector(selector):
            try:
                logger.debug(f"Trying total_engagements CSS selector via Selenium: {selector}")
                elements = retry_selenium_find(driver, By.CSS_SELECTOR, selector, max_retries=3, delay=0.5, find_multiple=True)
                logger.debug(f"Found {len(elements)} elements with CSS selector")

                for elem in elements:
                    try:
                        text = elem.text.strip()
                        logger.debug(f"Checking element text: '{text}'")
                        if text and is_numeric_value(text):
                            # Found a valid value - return it immediately
                            logger.info(f"Found total_engagements using selector '{selector}': {text}")
                            return text
                    except Exception as e:
                        logger.debug(f"Error getting text from element: {e}")
                        continue
            except Exception as e:
                logger.debug(f"Total engagements CSS selector {selector} failed: {e}")
        else:
            # XPath selector - use Selenium for dynamic content
            try:
                logger.debug(f"Trying total_engagements XPath selector via Selenium: {selector}")
                elements = retry_selenium_find(driver, By.XPATH, selector, max_retries=3, delay=0.5, find_multiple=True)
                logger.debug(f"Found {len(elements)} elements with XPath via Selenium")

                for elem in elements:
                    try:
                        text = elem.text.strip()
                        logger.debug(f"Checking element text: '{text}'")
                        if text and is_numeric_value(text):
                            # Found a valid value - return it immediately
                            logger.info(f"Found total_engagements using XPath via Selenium '{selector}': {text}")
                            return text
                    except Exception as e:
                        logger.debug(f"Error getting text from element: {e}")
                        continue
            except Exception as e:
                logger.debug(f"Total engagements XPath selector via Selenium {selector} failed: {e}")

    # Try XPath selectors using lxml tree as fallback
    for selector in selectors.get('total_engagements', []):
        # Use smart selector detection - skip CSS selectors (already tried above)
        if is_css_selector(selector):
            continue

        try:
            logger.debug(f"Trying total_engagements XPath selector: {selector}")
            engagement_elements = retry_xpath(tree, selector, max_retries=3, delay=0.5)
            logger.debug(f"Found {len(engagement_elements)} elements with XPath")

            if engagement_elements:
                for elem in engagement_elements:
                    text = elem.text_content().strip()
                    logger.debug(f"Checking element text: '{text}'")
                    if text and is_numeric_value(text):
                        # Found a valid value - return it immediately
                        logger.info(f"Found total_engagements using XPath '{selector}': {text}")
                        return text
        except Exception as e:
            logger.debug(f"Total engagements XPath selector {selector} failed: {e}")
            continue

    if not total_engagements:
        logger.warning(f"Could not find total engagements for {name}")

    return total_engagements
