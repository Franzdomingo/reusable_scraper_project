"""
Dropdown interaction utilities for variations extraction
"""

import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from my_scraper.extractors.retry_utils import retry_selenium_find, retry_xpath, retry_click, retry_operation

logger = logging.getLogger(__name__)


def click_dropdown_to_open(driver: webdriver.Chrome, selector: str, timeout: int = 3) -> bool:
    """
    Aggressively try to open a dropdown by clicking it multiple ways

    Args:
        driver: Selenium driver instance
        selector: CSS selector or XPath for dropdown element (XPath should start with /)
        timeout: Max seconds to wait for aria-expanded=true

    Returns:
        True if dropdown opened (aria-expanded=true), False otherwise
    """
    try:
        # Determine if selector is XPath or CSS
        # Updated 2025-10-25: Support both XPath and CSS selectors
        if selector.startswith('/'):
            by_type = By.XPATH
            selector_type = "XPath"
        else:
            by_type = By.CSS_SELECTOR
            selector_type = "CSS"

        logger.info(f"Using {selector_type} selector: {selector}")
        element = retry_selenium_find(driver, by_type, selector)

        # First, scroll the element into view
        logger.info("Scrolling dropdown element into view")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
        time.sleep(0.5)

        # Try to hide any overlaying elements (common issue)
        try:
            logger.info("Attempting to hide overlay elements")
            # Hide overlays using stable selectors (role="presentation" is semantic)
            # Updated 2025-10-25: Removed fragile CSS classes, using ARIA roles instead
            driver.execute_script("""
                // Hide elements with role="presentation" (common overlay pattern)
                let overlays = document.querySelectorAll('[role="presentation"]');
                overlays.forEach(el => el.style.display = 'none');

                // Also hide elements with common z-index patterns that might block clicks
                let highZIndexElements = Array.from(document.querySelectorAll('*')).filter(el => {
                    let zIndex = window.getComputedStyle(el).zIndex;
                    return zIndex !== 'auto' && parseInt(zIndex) > 1000;
                });
                highZIndexElements.forEach(el => {
                    if (el.contains(arguments[0]) === false) {
                        el.style.display = 'none';
                    }
                });
            """, element)
            time.sleep(0.3)
        except Exception as e:
            logger.info(f"Could not hide overlays: {e}")

        # Method 1: JavaScript click with force
        try:
            logger.info("Method 1: Trying JavaScript click")
            driver.execute_script("arguments[0].click();", element)
            time.sleep(0.5)
            if element.get_attribute('aria-expanded') == 'true':
                logger.info("Method 1 succeeded - dropdown opened")
                return True
        except Exception as e:
            logger.info(f"Method 1 failed: {e}")

        # Method 2: JavaScript MouseEvent dispatch (most powerful)
        try:
            logger.info("Method 2: Trying JavaScript MouseEvent dispatch")
            driver.execute_script("""
                var element = arguments[0];
                var event = new MouseEvent('mousedown', {
                    view: window,
                    bubbles: true,
                    cancelable: true
                });
                element.dispatchEvent(event);

                var clickEvent = new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true
                });
                element.dispatchEvent(clickEvent);
            """, element)
            time.sleep(0.5)
            if element.get_attribute('aria-expanded') == 'true':
                logger.info("Method 2 succeeded - dropdown opened")
                return True
        except Exception as e:
            logger.info(f"Method 2 failed: {e}")

        # Method 3: Focus and press SPACE key (accessibility method)
        try:
            logger.info("Method 3: Trying focus via JavaScript and SPACE key")
            driver.execute_script("arguments[0].focus();", element)
            time.sleep(0.2)
            element.send_keys(Keys.SPACE)
            time.sleep(0.5)
            if element.get_attribute('aria-expanded') == 'true':
                logger.info("Method 3 succeeded - dropdown opened")
                return True
        except Exception as e:
            logger.info(f"Method 3 failed: {e}")

        # Method 4: Focus and press ENTER key
        try:
            logger.info("Method 4: Trying focus via JavaScript and ENTER key")
            driver.execute_script("arguments[0].focus();", element)
            time.sleep(0.2)
            element.send_keys(Keys.ENTER)
            time.sleep(0.5)
            if element.get_attribute('aria-expanded') == 'true':
                logger.info("Method 4 succeeded - dropdown opened")
                return True
        except Exception as e:
            logger.info(f"Method 4 failed: {e}")

        # Method 5: Regular Selenium click (after overlay removal)
        try:
            logger.info("Method 5: Trying regular Selenium click after overlay removal")
            element.click()
            time.sleep(0.5)
            if element.get_attribute('aria-expanded') == 'true':
                logger.info("Method 5 succeeded - dropdown opened")
                return True
        except Exception as e:
            logger.info(f"Method 5 failed: {e}")

        # Method 6: ActionChains with offset
        try:
            logger.info("Method 6: Trying ActionChains with offset")
            actions = ActionChains(driver)
            actions.move_to_element(element).move_by_offset(0, 0).click().perform()
            time.sleep(0.5)
            if element.get_attribute('aria-expanded') == 'true':
                logger.info("Method 6 succeeded - dropdown opened")
                return True
        except Exception as e:
            logger.info(f"Method 6 failed: {e}")

        logger.warning("All click methods failed - dropdown did not open")
        return False

    except Exception as e:
        logger.error(f"Error in click_dropdown_to_open: {e}")
        return False
