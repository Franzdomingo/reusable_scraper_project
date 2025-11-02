"""
Debug script to inspect version popup structure
"""

import sys
import os
import logging
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scrapy_project'))

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from my_scraper.selectors.site_selectors import get_selectors_for_site

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def debug_version_popup():
    """Debug the version popup to see what's in each item"""

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

        # Get selectors
        selectors = get_selectors_for_site('kaggle')

        # Find and click version button
        logger.info("Looking for versions button...")
        versions_button_selector = selectors.get('variation_versions_button')

        # Try each selector
        button = None
        for selector in versions_button_selector:
            try:
                if selector.startswith('//'):
                    button = driver.find_element(By.XPATH, selector)
                else:
                    button = driver.find_element(By.CSS_SELECTOR, selector)
                logger.info(f"Found button with selector: {selector}")
                logger.info(f"  Button text: '{button.text}'")
                break
            except:
                continue

        if not button:
            logger.error("Could not find versions button!")
            return

        # Click the button
        logger.info("\nClicking versions button...")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", button)
        time.sleep(2)

        # Find popup items
        popup_items_selector = selectors.get('variation_versions_popup_items')
        logger.info(f"\nLooking for popup items with selector: {popup_items_selector}")

        items = driver.find_elements(By.CSS_SELECTOR, popup_items_selector)
        logger.info(f"Found {len(items)} version items")

        # Inspect each item
        for idx, item in enumerate(items):
            logger.info(f"\n{'='*80}")
            logger.info(f"VERSION ITEM {idx + 1}")
            logger.info(f"{'='*80}")

            # Get full HTML
            html = item.get_attribute('outerHTML')
            logger.info(f"HTML: {html[:500]}...")

            # Try to find version number
            version_number_selectors = selectors.get('variation_version_number', [])
            logger.info(f"\nTrying {len(version_number_selectors)} version number selectors...")
            for v_idx, v_sel in enumerate(version_number_selectors):
                try:
                    elem = item.find_element(By.CSS_SELECTOR, v_sel)
                    logger.info(f"  ✓ Selector {v_idx + 1} FOUND: '{elem.text}'")
                except:
                    logger.info(f"  ✗ Selector {v_idx + 1} not found")

            # Try to find created_by
            created_by_selectors = selectors.get('variation_version_created_by', [])
            logger.info(f"\nTrying {len(created_by_selectors)} created_by selectors...")
            for c_idx, c_sel in enumerate(created_by_selectors):
                try:
                    elem = item.find_element(By.CSS_SELECTOR, c_sel)
                    logger.info(f"  ✓ Selector {c_idx + 1} FOUND: '{elem.text}'")
                except:
                    logger.info(f"  ✗ Selector {c_idx + 1} not found")

            # Try to find update_description
            update_desc_selectors = selectors.get('variation_version_update_desc', [])
            logger.info(f"\nTrying {len(update_desc_selectors)} update_desc selectors...")
            for u_idx, u_sel in enumerate(update_desc_selectors):
                try:
                    elem = item.find_element(By.CSS_SELECTOR, u_sel)
                    logger.info(f"  ✓ Selector {u_idx + 1} FOUND: '{elem.text}'")
                except:
                    logger.info(f"  ✗ Selector {u_idx + 1} not found")

            # List all spans in the item
            logger.info(f"\nAll <span> elements in this item:")
            spans = item.find_elements(By.TAG_NAME, 'span')
            for s_idx, span in enumerate(spans):
                logger.info(f"  Span {s_idx + 1}: '{span.text}' (class='{span.get_attribute('class')}')")

            # List all divs in the item
            logger.info(f"\nAll <div> elements in this item:")
            divs = item.find_elements(By.TAG_NAME, 'div')
            for d_idx, div in enumerate(divs[:5]):  # Only first 5
                logger.info(f"  Div {d_idx + 1}: '{div.text[:100]}' (class='{div.get_attribute('class')}')")

        logger.info("\n\nPress Enter to close...")
        input()

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            driver.quit()


if __name__ == '__main__':
    debug_version_popup()
