"""
Quick test script to debug NVIDIA modelcard extraction
"""

import logging
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sys
import os

# Add scrapy_project to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scrapy_project'))

from my_scraper.selectors.site_selectors import get_selectors_for_site
from my_scraper.extractors.nvidia.nvidia_modelcard_extractor import extract_modelcard

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Test URL - new format as specified by user
TEST_URL = "https://build.nvidia.com/nvidia/nemotron-parse/modelcard"

def main():
    logger.info(f"Testing NVIDIA modelcard extraction on: {TEST_URL}")

    # Create Firefox driver since it works in your Firefox browser
    options = Options()
    # options.add_argument('--headless')  # Disabled for debugging

    driver = None
    try:
        driver = webdriver.Firefox(options=options)
        logger.info("Firefox driver created successfully")

        # First visit the main models page to handle popup
        logger.info("First visiting main models page to handle popup...")
        driver.get("https://build.nvidia.com/models")
        time.sleep(5)  # Let page fully load

        # Try to dismiss cookie/popup on main page
        logger.info("Looking for cookie/popup dismiss buttons on main page...")

        # List of cookie consent button selectors to try
        cookie_selectors = [
            '//*[@id="onetrust-reject-all-handler"]',  # Reject all cookies (preferred)
            '//*[@id="nv-done-btn-handler"]',          # Your originally specified button
            '#onetrust-accept-btn-handler',            # OneTrust accept button (fallback)
        ]

        for selector in cookie_selectors:
            try:
                # Try XPath first if it starts with /
                if selector.startswith('/'):
                    button = driver.find_element(By.XPATH, selector)
                else:
                    button = driver.find_element(By.CSS_SELECTOR, selector)

                if button and button.is_displayed():
                    logger.info(f"Found cookie button with selector: {selector}")
                    button.click()
                    time.sleep(2)  # Wait for popup to close
                    logger.info("Cookie popup dismissed on main page")
                    break
            except Exception:
                continue
        else:
            logger.info("No cookie popup found on main page")

        # Now navigate to the model page first (without /modelcard)
        model_page_url = TEST_URL.replace('/modelcard', '')
        logger.info(f"First loading model page: {model_page_url}")
        driver.get(model_page_url)
        logger.info("Waiting 5 seconds for page to fully load...")
        time.sleep(5)  # Let page fully load and JS initialize

        # Try to find and click the modelcard tab/link
        logger.info("Looking for modelcard tab to click...")
        modelcard_tab_selectors = [
            '//a[contains(@href, "/modelcard")]',
            '//button[contains(text(), "Model Card")]',
            '//a[contains(text(), "Model Card")]',
            '//div[contains(text(), "Model Card")]//ancestor::button',
            '//div[contains(text(), "Model Card")]//ancestor::a',
        ]

        modelcard_clicked = False
        for selector in modelcard_tab_selectors:
            try:
                tab = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                logger.info(f"Found modelcard tab with selector: {selector}")
                tab.click()
                logger.info("Waiting 5 seconds for modelcard content to load...")
                time.sleep(5)  # Wait for content to load after clicking
                modelcard_clicked = True
                logger.info("Clicked on modelcard tab")
                break
            except Exception as e:
                logger.debug(f"Tab selector {selector} failed: {e}")
                continue

        if not modelcard_clicked:
            logger.warning("Could not find modelcard tab, trying direct URL anyway...")
            driver.get(TEST_URL)

        # Wait for content
        logger.info("Waiting 5 seconds for final content load...")
        time.sleep(5)  # Let page fully load

        logger.info(f"Current URL: {driver.current_url}")
        logger.info(f"Page title: {driver.title}")

        # Try to dismiss popup first
        logger.info("Looking for popup dismiss button...")
        try:
            # Wait for the popup button to appear
            popup_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="nv-done-btn-handler"]'))
            )
            logger.info("Found popup dismiss button, clicking it...")
            popup_button.click()
            time.sleep(2)  # Wait for popup to close and content to load
            logger.info("Popup dismissed successfully")
        except Exception as e:
            logger.warning(f"No popup found or couldn't dismiss: {e}")

        # Check if we got a 404
        if "404" in driver.page_source and "Not Found" in driver.page_source:
            logger.error("Page returned 404 - Not Found")
        else:
            logger.info("Page loaded successfully (no 404 detected)")

        # Try to find prose elements
        prose_elements = driver.find_elements(By.CSS_SELECTOR, 'div.prose')
        logger.info(f"Found {len(prose_elements)} div.prose elements")

        # Save screenshot and HTML for debugging
        driver.save_screenshot("nvidia_debug.png")
        logger.info("Saved screenshot to nvidia_debug.png")

        # Get selectors
        selectors = get_selectors_for_site('nvidia')
        logger.info(f"Selectors loaded: {selectors.keys()}")

        # Extract modelcard
        logger.info("Extracting modelcard...")
        modelcard = extract_modelcard(driver, selectors, "test-model")

        if modelcard:
            logger.info(f"SUCCESS! Extracted {len(modelcard)} characters")
            logger.info(f"First 200 chars: {modelcard[:200]}")
        else:
            logger.error("FAILED! No modelcard content extracted")

            # Debug: try to find elements manually
            logger.info("Debugging - checking page structure...")
            logger.info(f"Page title: {driver.title}")
            logger.info(f"Current URL: {driver.current_url}")

            # Try to find prose elements
            prose_elements = driver.find_elements(By.CSS_SELECTOR, 'div.prose')
            logger.info(f"Found {len(prose_elements)} div.prose elements")

            if prose_elements:
                logger.info(f"First prose element text (first 200 chars): {prose_elements[0].text[:200]}")

            # Save page source for inspection
            with open('nvidia_page_source.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info("Saved page source to nvidia_page_source.html")

            # Try alternative selectors
            logger.info("Trying alternative selectors...")
            for selector in ['article', 'main', 'div[role="main"]', 'div.container', 'div.content']:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                logger.info(f"  {selector}: found {len(elements)} elements")

    except Exception as e:
        logger.error(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
            logger.info("Driver closed")

if __name__ == "__main__":
    main()
