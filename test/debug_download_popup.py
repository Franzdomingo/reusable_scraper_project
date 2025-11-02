"""
Debug script to inspect the download popup structure
"""

import sys
import os
import logging
import time

# Add the scrapy_project directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scrapy_project'))

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def debug_popup():
    """Debug the download popup structure"""

    test_url = "https://www.kaggle.com/models/ai21labs/ai21-jamba-reasoning-3b"

    firefox_options = FirefoxOptions()
    firefox_options.set_preference('general.useragent.override',
                                   'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    driver = None
    try:
        logger.info("Initializing Firefox driver...")
        driver = webdriver.Firefox(options=firefox_options)

        logger.info(f"Navigating to: {test_url}")
        driver.get(test_url)
        time.sleep(3)

        # Try to find the download button
        logger.info("Looking for download button...")

        button_selectors = [
            (By.XPATH, '//button[.//span[contains(., "Download")]]'),
            (By.XPATH, '//button[contains(., "download")]'),
            (By.CSS_SELECTOR, 'button[data-testid*="download"]'),
        ]

        button = None
        for by_type, selector in button_selectors:
            try:
                button = driver.find_element(by_type, selector)
                logger.info(f"✓ Found button with {by_type}: {selector}")
                logger.info(f"  Button text: '{button.text}'")
                logger.info(f"  Button HTML: {button.get_attribute('outerHTML')[:200]}")
                break
            except:
                logger.debug(f"  Not found: {by_type}: {selector}")
                continue

        if not button:
            logger.error("Could not find download button!")
            return

        # Click the button
        logger.info("\nClicking download button...")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", button)

        logger.info("Waiting for popup to appear...")
        time.sleep(2)

        # Try to find the popup
        logger.info("\nLooking for popup elements...")

        # Get all visible divs
        all_divs = driver.find_elements(By.TAG_NAME, 'div')
        logger.info(f"Total divs on page: {len(all_divs)}")

        # Look for dialogs
        dialogs = driver.find_elements(By.XPATH, '//div[@role="dialog"]')
        logger.info(f"Dialogs found: {len(dialogs)}")
        for idx, dialog in enumerate(dialogs):
            logger.info(f"  Dialog {idx}: {dialog.get_attribute('class')}")
            logger.info(f"    HTML: {dialog.get_attribute('outerHTML')[:300]}")

        # Look for any ul elements
        uls = driver.find_elements(By.TAG_NAME, 'ul')
        logger.info(f"\nAll <ul> elements: {len(uls)}")
        for idx, ul in enumerate(uls):
            if ul.is_displayed():
                logger.info(f"  UL {idx} (visible): role='{ul.get_attribute('role')}', class='{ul.get_attribute('class')}'")
                logger.info(f"    HTML: {ul.get_attribute('outerHTML')[:200]}")

        # Look for menu-like elements
        menus = driver.find_elements(By.XPATH, '//*[@role="menu" or @role="listbox"]')
        logger.info(f"\nMenu/Listbox elements: {len(menus)}")
        for idx, menu in enumerate(menus):
            logger.info(f"  Menu {idx}: {menu.tag_name}, role='{menu.get_attribute('role')}'")
            logger.info(f"    HTML: {menu.get_attribute('outerHTML')[:300]}")

        # Look for list items
        lis = driver.find_elements(By.XPATH, '//li[@role="option"]')
        logger.info(f"\nList items with role='option': {len(lis)}")
        for idx, li in enumerate(lis):
            if li.is_displayed():
                logger.info(f"  LI {idx}: '{li.text}'")

        logger.info("\n\nDumping page source to file for inspection...")
        with open('debug_popup_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info("✓ Saved to debug_popup_source.html")

        logger.info("\nPress Enter to close browser...")
        input()

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            driver.quit()


if __name__ == '__main__':
    debug_popup()
