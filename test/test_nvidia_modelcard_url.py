"""
Test script to verify NVIDIA /modelcard URL pattern works correctly
This script tests the updated spider logic that uses direct /modelcard URLs
"""

import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_modelcard_url():
    """
    Test that navigating to /modelcard URL directly works
    """
    # Sample model URL - using Meta Llama3 8B as example
    base_url = "https://build.nvidia.com/meta/llama3-8b"
    modelcard_url = f"{base_url}/modelcard"

    print(f"Testing NVIDIA modelcard URL pattern...")
    print(f"Base URL: {base_url}")
    print(f"Modelcard URL: {modelcard_url}")
    print("-" * 80)

    # Setup Firefox driver
    options = FirefoxOptions()
    # options.add_argument('--headless')  # Comment out to see browser
    driver = webdriver.Firefox(options=options)

    try:
        # Navigate directly to modelcard URL
        print(f"\nNavigating to: {modelcard_url}")
        driver.get(modelcard_url)

        # Wait for page to load
        time.sleep(3)

        # Check if we're on the modelcard page
        current_url = driver.current_url
        print(f"Current URL after navigation: {current_url}")

        # Try to find the modelcard content
        selectors_to_try = [
            'div.prose.prose-markdown-compat',
            'div.prose.prose-markdown-compat.max-w-\\[85ch\\]',
            'div.prose',
            'div.prose-markdown-compat',
        ]

        found_content = False
        for selector in selectors_to_try:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                if element and element.text.strip():
                    print(f"\n[OK] Found modelcard content with selector: {selector}")
                    print(f"Content length: {len(element.text)} chars")
                    print(f"First 200 chars: {element.text[:200]}...")
                    found_content = True
                    break
            except Exception as e:
                print(f"[FAIL] Selector '{selector}' failed: {e}")

        if not found_content:
            print("\n[WARNING] No modelcard content found with any selector!")
            print("Page source (first 500 chars):")
            print(driver.page_source[:500])
        else:
            print("\n[SUCCESS] Modelcard content extracted successfully!")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        print("\nTest completed.")

if __name__ == '__main__':
    test_modelcard_url()
