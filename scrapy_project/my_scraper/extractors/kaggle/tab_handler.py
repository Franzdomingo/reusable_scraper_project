"""
Tab navigation and processing utilities for variations extraction
"""

import logging
import time
from typing import Dict, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from my_scraper.extractors.retry_utils import retry_selenium_find, retry_xpath, retry_click, retry_operation
from my_scraper.selectors.site_selectors import KaggleSelectors

logger = logging.getLogger(__name__)


def build_tab_queue(driver: webdriver.Chrome, tabs_all_selector: str, tab_text_selector: str, name: str) -> List[Dict]:
    """
    Build a queue of tabs to process

    Args:
        driver: Selenium driver instance
        tabs_all_selector: CSS selector for all tab buttons
        tab_text_selector: CSS selector for tab text within tab button
        name: Model name for logging

    Returns:
        List of dictionaries containing tab index and text
    """
    tab_queue = []

    try:
        tab_buttons = retry_selenium_find(driver, By.CSS_SELECTOR, tabs_all_selector, find_multiple=True)
        logger.debug(f"Found {len(tab_buttons)} tab buttons")

        if len(tab_buttons) == 0:
            logger.warning(f"No tabs found for {name}")
            return tab_queue

        # Build queue: store tab text and indices
        for idx, tab_button in enumerate(tab_buttons):
            try:
                # Extract tab text
                tab_text_elem = retry_selenium_find(tab_button, By.CSS_SELECTOR, tab_text_selector)
                tab_text = tab_text_elem.text.strip()

                if tab_text:
                    tab_queue.append({
                        'index': idx,
                        'text': tab_text,
                        'button': tab_button
                    })
                    logger.debug(f"Added tab to queue - Index {idx}: {tab_text}")

            except Exception as e:
                logger.warning(f"Error extracting text from tab button {idx}: {e}")
                continue

        logger.debug(f"Built tab queue with {len(tab_queue)} tabs for {name}")

    except Exception as e:
        logger.error(f"Error building tab queue for {name}: {e}")

    return tab_queue


def click_tab(driver: webdriver.Chrome, tabs_all_selector: str, tab_idx: int, tab_text: str) -> bool:
    """
    Click a tab button by re-finding it to avoid stale element references
    Uses multiple click methods to handle overlaying elements

    Args:
        driver: Selenium driver instance
        tabs_all_selector: CSS selector for all tab buttons
        tab_idx: Index of the tab to click
        tab_text: Text of the tab for logging

    Returns:
        True if tab was successfully clicked, False otherwise
    """
    try:
        # Re-find the tab button (it may be stale)
        tab_buttons = retry_selenium_find(driver, By.CSS_SELECTOR, tabs_all_selector, find_multiple=True)
        if tab_idx >= len(tab_buttons):
            logger.warning(f"Tab index {tab_idx} out of range")
            return False

        tab_button = tab_buttons[tab_idx]

        # Scroll into view first
        logger.debug(f"Scrolling tab '{tab_text}' into view")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", tab_button)
        time.sleep(0.5)

        # Try to hide overlaying elements that might intercept the click
        try:
            logger.debug(f"Attempting to hide overlaying elements for tab '{tab_text}'")
            # Get selectors from KaggleSelectors
            overlay_button_class = KaggleSelectors.OVERLAY_BUTTON_CLASS
            overlay_button_xpath = KaggleSelectors.OVERLAY_BUTTON_XPATH
            overlay_element_selectors = ', '.join(KaggleSelectors.OVERLAY_ELEMENTS_CLASSES)

            # Hide the specific overlaying button mentioned in the error
            driver.execute_script(f"""
                // Hide the specific overlaying button by class
                let overlayButtons = document.querySelectorAll('{overlay_button_class}');
                overlayButtons.forEach(btn => {{
                    btn.style.display = 'none';
                    btn.style.visibility = 'hidden';
                }});

                // Also try the XPath-based selector
                let xpathButton = document.evaluate(
                    '{overlay_button_xpath}',
                    document,
                    null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE,
                    null
                ).singleNodeValue;
                if (xpathButton) {{
                    xpathButton.style.display = 'none';
                    xpathButton.style.visibility = 'hidden';
                }}

                // Hide other common overlay elements
                let overlays = document.querySelectorAll('{overlay_element_selectors}');
                overlays.forEach(el => {{
                    if (el.style.zIndex > 1000) {{
                        el.style.display = 'none';
                    }}
                }});
            """)
            time.sleep(0.3)
            logger.debug(f"Successfully hid overlaying elements for tab '{tab_text}'")
        except Exception as e:
            logger.debug(f"Could not hide overlays for tab '{tab_text}': {e}")

        # Method 1: JavaScript click (most reliable for intercepted elements)
        try:
            logger.debug(f"Method 1: Trying JavaScript click for tab '{tab_text}'")
            driver.execute_script("arguments[0].click();", tab_button)
            time.sleep(1)  # Wait for tab content to load
            logger.debug(f"Method 1 succeeded - clicked tab: {tab_text}")
            return True
        except Exception as e:
            logger.debug(f"Method 1 failed for tab '{tab_text}': {e}")

        # Method 2: JavaScript MouseEvent dispatch
        try:
            logger.debug(f"Method 2: Trying JavaScript MouseEvent dispatch for tab '{tab_text}'")
            driver.execute_script("""
                var element = arguments[0];
                var event = new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true
                });
                element.dispatchEvent(event);
            """, tab_button)
            time.sleep(1)
            logger.debug(f"Method 2 succeeded - clicked tab: {tab_text}")
            return True
        except Exception as e:
            logger.debug(f"Method 2 failed for tab '{tab_text}': {e}")

        # Method 3: Regular Selenium click (after hiding overlays)
        try:
            logger.debug(f"Method 3: Trying regular Selenium click for tab '{tab_text}'")
            tab_button.click()
            time.sleep(1)
            logger.debug(f"Method 3 succeeded - clicked tab: {tab_text}")
            return True
        except Exception as e:
            logger.debug(f"Method 3 failed for tab '{tab_text}': {e}")

        logger.error(f"All click methods failed for tab '{tab_text}'")
        return False

    except Exception as e:
        logger.error(f"Error clicking tab '{tab_text}': {e}")
        return False
