"""
Usability extraction functions
"""

import logging
import time
from typing import Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lxml import html as lxml_html
from my_scraper.utils import is_css_selector, is_xpath_selector
from my_scraper.extractors.retry_utils import retry_selenium_find, retry_xpath, retry_click, retry_operation

logger = logging.getLogger(__name__)


def extract_usability(driver: webdriver.Chrome, tree: lxml_html.HtmlElement,
                      selectors: Dict, name: str) -> str:
    """
    Extract usability score using configured selectors

    Args:
        driver: Selenium driver instance (for dynamic content)
        tree: lxml tree object
        selectors: Selectors configuration dictionary
        name: Model name for logging

    Returns:
        Extracted usability score or empty string
    """
    usability = ""

    # If no driver, can't try Selenium extraction
    if not driver:
        logger.warning(f"No driver provided, skipping Selenium extraction for {name}")
        # Continue to fallback below
    else:
        # Wait a moment for dynamic content to load
        try:
            # Try to wait for the usability section to be present
            logger.debug(f"Waiting for usability section to load")
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Usability')]"))
            )
            time.sleep(0.5)  # Small additional wait for rendering
            logger.debug(f"Usability section loaded")
        except Exception as e:
            logger.debug(f"Timeout waiting for usability section: {e}")
            # Continue anyway and try the selectors

        # Try all selectors via Selenium for dynamic content
        for selector in selectors.get('usability', []):
            # Use smart selector detection
            if is_css_selector(selector):
                try:
                    logger.debug(f"Trying usability CSS selector: {selector}")
                    elements = retry_selenium_find(driver, By.CSS_SELECTOR, selector, find_multiple=True)
                    logger.debug(f"Found {len(elements) if elements else 0} elements with CSS selector")

                    if elements:
                        for i, elem in enumerate(elements):
                            try:
                                text = elem.text.strip()
                                logger.debug(f"Checking element {i+1} text: '{text}'")
                                if text:
                                    # Found a valid value - return it immediately
                                    logger.debug(f"Extracted usability using CSS selector: {text}")
                                    return text
                            except Exception as e:
                                logger.debug(f"Error getting text from element {i+1}: {e}")
                                continue
                except Exception as e:
                    logger.debug(f"Usability CSS selector {selector} failed: {e}")
            else:
                # XPath selector - use Selenium's XPath method for dynamic content
                try:
                    logger.debug(f"Trying usability XPath selector: {selector}")
                    elements = retry_selenium_find(driver, By.XPATH, selector, find_multiple=True)
                    logger.debug(f"Found {len(elements) if elements else 0} elements with XPath")

                    if elements:
                        for i, elem in enumerate(elements):
                            try:
                                text = elem.text.strip()
                                logger.debug(f"Checking element {i+1} text: '{text}'")
                                if text:
                                    # Found a valid value - return it immediately
                                    logger.debug(f"Extracted usability using XPath: {text}")
                                    return text
                            except Exception as e:
                                logger.debug(f"Error getting text from element {i+1}: {e}")
                                continue
                except Exception as e:
                    logger.debug(f"Usability XPath selector {selector} failed: {e}")

    # Fallback: Search for text near "Usability" heading
    if not usability:
        logger.debug(f"Trying fallback: searching for usability near 'Usability' heading")
        try:
            # Find the Usability heading and look for siblings/nearby elements
            usability_heading = retry_selenium_find(driver, By.XPATH, "//*[contains(text(), 'Usability')]", find_multiple=True)

            if usability_heading:
                logger.debug(f"Found {len(usability_heading)} 'Usability' headings")

                # Look for parent container and find the score within it
                for heading in usability_heading[:2]:
                    try:
                        # Try to find parent div/section
                        parent = retry_selenium_find(heading, By.XPATH, './ancestor::div[1]')
                        # Look for p elements in the parent's following siblings
                        following_p = retry_selenium_find(parent, By.XPATH, './following-sibling::*//p')
                        if following_p:
                            text = following_p.text.strip()
                            if text:
                                usability = text
                                logger.debug(f"Extracted usability using fallback: {usability}")
                                break
                    except Exception:
                        continue

        except Exception as e:
            logger.error(f"Fallback usability search failed: {e}")

    if not usability:
        logger.warning(f"No usability found for {name}")

    return usability
