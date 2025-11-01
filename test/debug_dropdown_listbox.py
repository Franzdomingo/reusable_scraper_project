"""
Debug script to inspect what happens after clicking the dropdown
"""

import sys
import os
import logging
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scrapy_project'))

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def debug_dropdown():
    """Debug the dropdown and listbox"""

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

        # Find and click download button
        logger.info("Looking for download button...")
        button = driver.find_element(By.XPATH, '//button[.//span[contains(., "Download")]]')
        logger.info(f"Found button: '{button.text}'")

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", button)
        logger.info("Clicked download button")
        time.sleep(2)

        # Find the dropdown (combobox)
        logger.info("\nLooking for dropdown...")
        dropdown = driver.find_element(By.XPATH, '//div[@role="combobox"]')
        logger.info(f"Found dropdown")
        logger.info(f"  aria-expanded: {dropdown.get_attribute('aria-expanded')}")
        logger.info(f"  aria-controls: {dropdown.get_attribute('aria-controls')}")
        logger.info(f"  Text: '{dropdown.text}'")

        # Click the dropdown
        logger.info("\nClicking dropdown...")
        driver.execute_script("arguments[0].click();", dropdown)
        time.sleep(2)

        # Check aria-expanded after click
        logger.info(f"After click - aria-expanded: {dropdown.get_attribute('aria-expanded')}")

        # Look for listbox
        logger.info("\n\nSearching for listbox...")

        # Try all UL elements
        uls = driver.find_elements(By.TAG_NAME, 'ul')
        logger.info(f"Total <ul> elements: {len(uls)}")

        for idx, ul in enumerate(uls):
            if ul.is_displayed():
                role = ul.get_attribute('role')
                classes = ul.get_attribute('class')
                logger.info(f"\n  UL {idx} (visible):")
                logger.info(f"    role: '{role}'")
                logger.info(f"    class: '{classes}'")
                if role == 'listbox':
                    logger.info(f"    *** FOUND LISTBOX ***")
                    logger.info(f"    HTML: {ul.get_attribute('outerHTML')[:500]}")

                    # Count items
                    items = ul.find_elements(By.TAG_NAME, 'li')
                    logger.info(f"    Items in listbox: {len(items)}")
                    for item_idx, item in enumerate(items):
                        logger.info(f"      Item {item_idx}: '{item.text}' (role={item.get_attribute('role')})")

        # Also check for any new divs with MuiMenu or MuiPopover
        logger.info("\n\nSearching for MuiMenu elements...")
        menus = driver.find_elements(By.XPATH, '//*[contains(@class, "MuiMenu")]')
        logger.info(f"Found {len(menus)} MuiMenu elements")
        for idx, menu in enumerate(menus):
            if menu.is_displayed():
                logger.info(f"  Menu {idx}: {menu.get_attribute('class')}")

        logger.info("\n\nDumping page source...")
        with open('debug_dropdown_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info("Saved to debug_dropdown_source.html")

        logger.info("\nPress Enter to close...")
        input()

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            driver.quit()


if __name__ == '__main__':
    debug_dropdown()
