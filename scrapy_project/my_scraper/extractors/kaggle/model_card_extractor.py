"""
Model card extraction functions
"""

import logging
import time
from typing import Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from lxml import html as lxml_html
from my_scraper.utils import is_xpath_selector
from my_scraper.extractors.selenium_utils import click_element
from my_scraper.extractors.retry_utils import retry_selenium_find, retry_xpath, retry_click, retry_operation
from my_scraper.extractors.html_utils import convert_html_to_markdown

logger = logging.getLogger(__name__)


def extract_model_card(driver: webdriver.Chrome, tree: lxml_html.HtmlElement,
                       selectors: Dict, name: str) -> str:
    """
    Extract the model card text with inline Markdown-formatted links

    Args:
        driver: Selenium driver instance
        tree: lxml tree object
        selectors: Selectors configuration dictionary
        name: Model name for logging

    Returns:
        Model card text with inline Markdown links (e.g., [text](url))
    """
    result = {'html': None, 'text': ''}

    # If no driver, can't extract model card (requires JavaScript rendering)
    if not driver:
        logger.debug(f"No driver provided, skipping model card extraction for {name}")
        return ""

    # Try to click action button if configured
    action_selectors = selectors.get('model_card_action')
    if action_selectors:
        # Handle both string and list of selectors
        if isinstance(action_selectors, str):
            action_selectors = [action_selectors]

        # Try each selector until one works
        for action_selector in action_selectors:
            try:
                # Detect if selector is XPath or CSS
                if is_xpath_selector(action_selector):
                    logger.debug(f"Trying action button XPath selector: {action_selector}")
                    by_type = By.XPATH
                else:
                    logger.debug(f"Trying action button CSS selector: {action_selector}")
                    by_type = By.CSS_SELECTOR

                if click_element(driver, action_selector, by=by_type):
                    logger.info(f"Clicked 'Read more' button using selector: {action_selector}")
                    time.sleep(1)
                    # Refresh tree after click (using driver's page source)
                    tree = lxml_html.fromstring(driver.page_source)
                    break  # Stop trying selectors once one works
            except Exception as e:
                logger.debug(f"Action button selector {action_selector} failed: {e}")
                pass

    # Try all selectors via Selenium (CSS or XPath)
    for sel in selectors.get('model_card_selectors', []):
        try:
            # Detect if selector is XPath or CSS
            if is_xpath_selector(sel):
                logger.debug(f"Trying model card XPath selector: {sel}")
                el = retry_selenium_find(driver, By.XPATH, sel)
            else:
                logger.debug(f"Trying model card CSS selector: {sel}")
                el = retry_selenium_find(driver, By.CSS_SELECTOR, sel)

            # Convert HTML content to text with inline Markdown links
            text_with_links = convert_html_to_markdown(el, driver)

            if text_with_links:
                result['text'] = text_with_links
                logger.info(f"Found model card using selector '{sel}'")

                # Count how many markdown links were created
                link_count = text_with_links.count('](')
                if link_count > 0:
                    logger.info(f"Converted {link_count} links to Markdown format")

                break
        except Exception as e:
            logger.debug(f"Model card selector {sel} failed: {e}")
            pass

    # Fallback to XPath using lxml (with Markdown link conversion)
    if not result['text']:
        fallback_xpaths = [
            '//div[contains(@class, "sc-lkCrJH")][1]',
            '//div[contains(@class, "sc-chzmIZ")]/div[1]'
        ]

        for xp in fallback_xpaths:
            try:
                elems = retry_xpath(tree, xp)
                if elems:
                    elem = elems[0]

                    # Use the reusable utility to convert lxml element to markdown
                    text = convert_html_to_markdown(elem)
                    if text:
                        result['text'] = text
                        logger.info(f"Found model card using fallback XPath: {xp}")
                        break
            except Exception as e:
                logger.debug(f"Fallback XPath {xp} failed: {e}")
                pass

    if not result['text']:
        logger.warning(f"Could not find model_card for {name}")

    return result['text']
