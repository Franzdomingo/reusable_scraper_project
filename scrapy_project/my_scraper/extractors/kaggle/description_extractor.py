"""
Description extraction functions
"""

import logging
from typing import Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from lxml import html as lxml_html
from my_scraper.utils import html_to_text, is_css_selector, is_xpath_selector
from my_scraper.extractors.retry_utils import retry_selenium_find, retry_xpath

logger = logging.getLogger(__name__)


def extract_description(driver: webdriver.Chrome, tree: lxml_html.HtmlElement,
                       selectors: Dict, name: str) -> str:
    """
    Extract description using configured selectors

    Args:
        driver: Selenium driver instance
        tree: lxml tree object
        selectors: Selectors configuration dictionary
        name: Model name for logging

    Returns:
        Extracted description text or empty string
    """
    description = ""

    # First try CSS selectors (via Selenium) - these are more reliable for dynamic content
    for selector in selectors.get('description', []):
        if is_css_selector(selector):
            try:
                logger.debug(f"Trying description CSS selector via Selenium: {selector}")
                desc_element = retry_selenium_find(driver, By.CSS_SELECTOR, selector)
                if desc_element:
                    outer = desc_element.get_attribute('outerHTML')
                    if outer and outer.strip():
                        logger.debug(f"Extracted description using CSS selector")
                        return html_to_text(outer)
            except Exception as e:
                logger.debug(f"Description CSS selector {selector} not found: {e}")

    # Next try XPath selectors using lxml tree
    for selector in selectors.get('description', []):
        if is_css_selector(selector):
            continue
        try:
            logger.debug(f"Trying description XPath selector: {selector}")
            desc_elements = retry_xpath(tree, selector)
            if desc_elements and desc_elements[0].text_content().strip():
                logger.debug(f"Extracted description using XPath selector")
                return desc_elements[0].text_content().strip()
        except Exception as e:
            logger.debug(f"Description XPath selector {selector} failed: {e}")

    # Final fallback: use configured CSS fallback
    if 'description_css_fallback' in selectors:
        try:
            desc_element = retry_selenium_find(driver, By.CSS_SELECTOR, selectors['description_css_fallback'])
            if desc_element:
                outer = desc_element.get_attribute('outerHTML')
                if outer and outer.strip():
                    logger.debug(f"Extracted description using fallback CSS selector")
                    return html_to_text(outer)
        except Exception:
            logger.warning(f"No description found for {name}")

    return description
