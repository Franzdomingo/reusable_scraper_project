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

logger = logging.getLogger(__name__)


def extract_model_card(driver: webdriver.Chrome, tree: lxml_html.HtmlElement,
                       selectors: Dict, name: str) -> str:
    """
    Extract the model card text and links

    Args:
        driver: Selenium driver instance
        tree: lxml tree object
        selectors: Selectors configuration dictionary
        name: Model name for logging

    Returns:
        Model card text with links
    """
    result = {'text': '', 'links': []}

    # If no driver, can't extract model card (requires JavaScript rendering)
    if not driver:
        logger.debug(f"No driver provided, skipping model card extraction for {name}")
        return ""

    # Try to click action button if configured
    action_selector = selectors.get('model_card_action')
    if action_selector:
        try:
            if click_element(driver, action_selector):
                time.sleep(1)
                # Refresh tree after click (using driver's page source)
                tree = lxml_html.fromstring(driver.page_source)
        except Exception:
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

            text = el.text.strip()
            if text:
                result['text'] = text
                logger.info(f"Found model card using selector '{sel}'")

                # Extract anchor hrefs
                try:
                    anchors = retry_selenium_find(el, By.TAG_NAME, 'a', find_multiple=True)
                    for a in anchors:
                        href = a.get_attribute('href')
                        if href:
                            result['links'].append(href)
                except Exception:
                    pass

                break
        except Exception as e:
            logger.debug(f"Model card selector {sel} failed: {e}")
            pass

    # Fallback to XPath using lxml
    if not result['text']:
        fallback_xpaths = [
            '//div[contains(@class, "sc-lkCrJH")][1]',
            '//div[contains(@class, "sc-chzmIZ")]/div[1]'
        ]

        for xp in fallback_xpaths:
            try:
                elems = retry_xpath(tree, xp)
                if elems:
                    text = elems[0].text_content().strip()
                    if text:
                        result['text'] = text

                        # Extract links
                        try:
                            anchor_nodes = elems[0].xpath('.//a')
                            for node in anchor_nodes:
                                href = node.get('href')
                                if href:
                                    result['links'].append(href)
                        except Exception:
                            pass

                        break
            except Exception:
                pass

    if not result['text']:
        logger.warning(f"Could not find model_card for {name}")

    # Combine text and links
    model_card_text = result['text']
    if result['links']:
        model_card_text += '\n\nLinks:\n' + '\n'.join([f"- {l}" for l in result['links']])

    return model_card_text
