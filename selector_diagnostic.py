"""
Selector Diagnostic Tool
Tests current selectors against live Kaggle pages to identify what has changed
"""

import time
import sys
import io
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from lxml import html as lxml_html

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Import current selectors
sys.path.append('scrapy_project')
from my_scraper.selectors.site_selectors import get_selectors_for_site


def test_selectors_on_page(url: str):
    """Test all Kaggle selectors on a specific page"""

    print(f"\n{'='*80}")
    print(f"Testing selectors on: {url}")
    print(f"{'='*80}\n")

    # Setup headless Chrome
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    driver = webdriver.Chrome(options=options)

    try:
        # Load the page
        driver.get(url)
        time.sleep(3)  # Wait for page to load

        # Get selectors
        selectors = get_selectors_for_site('kaggle')

        # Parse the HTML
        tree = lxml_html.fromstring(driver.page_source)

        # Test variation tabs (most critical issue from logs)
        print("\n" + "="*80)
        print("TESTING VARIATION TABS (CRITICAL)")
        print("="*80)
        tabs_selector = selectors.get('variation_tabs_all')
        tab_text_selector = selectors.get('variation_tab_text')

        print(f"\nSelector: {tabs_selector}")
        try:
            tab_buttons = driver.find_elements(By.CSS_SELECTOR, tabs_selector)
            print(f"✓ Found {len(tab_buttons)} tab buttons")

            if len(tab_buttons) > 0:
                for idx, tab in enumerate(tab_buttons[:5]):  # Show first 5
                    try:
                        tab_text_elem = tab.find_element(By.CSS_SELECTOR, tab_text_selector)
                        print(f"  Tab {idx}: {tab_text_elem.text.strip()}")
                    except:
                        print(f"  Tab {idx}: (could not extract text with selector {tab_text_selector})")
                        # Try alternative: get text directly
                        print(f"  Tab {idx} direct text: {tab.text.strip()}")
            else:
                print("✗ NO TABS FOUND - SELECTOR MAY BE OUTDATED")

                # Try to find tabs with alternative selectors
                print("\nTrying alternative tab selectors:")
                alt_selectors = [
                    'button[role="tab"]',
                    'div[role="tab"]',
                    'button.MuiTab-root',
                    '[role="tab"]',
                ]
                for alt_sel in alt_selectors:
                    try:
                        alt_tabs = driver.find_elements(By.CSS_SELECTOR, alt_sel)
                        if len(alt_tabs) > 0:
                            print(f"  ✓ {alt_sel}: Found {len(alt_tabs)} tabs")
                            for idx, tab in enumerate(alt_tabs[:3]):
                                print(f"    Tab {idx}: {tab.text.strip()[:50]}")
                    except Exception as e:
                        print(f"  ✗ {alt_sel}: {e}")
        except Exception as e:
            print(f"✗ Error: {e}")

        # Test collaborators
        print("\n" + "="*80)
        print("TESTING COLLABORATORS")
        print("="*80)
        collab_selectors = selectors.get('collaborators', [])
        print(f"\nSelectors: {collab_selectors}")

        found_any = False
        for sel in collab_selectors:
            try:
                if sel.startswith('.') or sel.startswith('#') or sel.startswith('p') or sel.startswith('div'):
                    # CSS selector
                    elements = driver.find_elements(By.CSS_SELECTOR, sel)
                    if elements:
                        print(f"✓ CSS '{sel}': Found {len(elements)} elements")
                        for idx, elem in enumerate(elements[:3]):
                            print(f"  Element {idx}: {elem.text.strip()[:100]}")
                        found_any = True
                        break
                else:
                    # XPath selector
                    elements = tree.xpath(sel)
                    if elements:
                        print(f"✓ XPath '{sel}': Found {len(elements)} elements")
                        for idx, elem in enumerate(elements[:3]):
                            print(f"  Element {idx}: {elem.text_content().strip()[:100]}")
                        found_any = True
                        break
            except Exception as e:
                print(f"✗ '{sel}': {e}")

        if not found_any:
            print("\n✗ NO COLLABORATORS FOUND - SELECTORS MAY BE OUTDATED")

        # Test authors
        print("\n" + "="*80)
        print("TESTING AUTHORS")
        print("="*80)
        author_selectors = selectors.get('authors', [])
        print(f"\nSelectors: {author_selectors}")

        found_any = False
        for sel in author_selectors:
            try:
                if sel.startswith('.') or sel.startswith('#') or sel.startswith('p') or sel.startswith('div'):
                    # CSS selector
                    elements = driver.find_elements(By.CSS_SELECTOR, sel)
                    if elements:
                        print(f"✓ CSS '{sel}': Found {len(elements)} elements")
                        for idx, elem in enumerate(elements[:3]):
                            print(f"  Element {idx}: {elem.text.strip()[:100]}")
                        found_any = True
                        break
                else:
                    # XPath selector
                    elements = tree.xpath(sel)
                    if elements:
                        print(f"✓ XPath '{sel}': Found {len(elements)} elements")
                        for idx, elem in enumerate(elements[:3]):
                            print(f"  Element {idx}: {elem.text_content().strip()[:100]}")
                        found_any = True
                        break
            except Exception as e:
                print(f"✗ '{sel}': {e}")

        if not found_any:
            print("\n✗ NO AUTHORS FOUND - SELECTORS MAY BE OUTDATED")

        # Test provenance
        print("\n" + "="*80)
        print("TESTING PROVENANCE")
        print("="*80)
        prov_selectors = selectors.get('provenance', [])
        print(f"\nSelectors: {prov_selectors}")

        found_any = False
        for sel in prov_selectors:
            try:
                if sel.startswith('.') or sel.startswith('#') or sel.startswith('div'):
                    # CSS selector
                    elements = driver.find_elements(By.CSS_SELECTOR, sel)
                    if elements:
                        print(f"✓ CSS '{sel}': Found {len(elements)} elements")
                        for idx, elem in enumerate(elements[:3]):
                            print(f"  Element {idx}: {elem.text.strip()[:100]}")
                        found_any = True
                        break
                else:
                    # XPath selector
                    elements = tree.xpath(sel)
                    if elements:
                        print(f"✓ XPath '{sel}': Found {len(elements)} elements")
                        for idx, elem in enumerate(elements[:3]):
                            print(f"  Element {idx}: {elem.text_content().strip()[:100]}")
                        found_any = True
                        break
            except Exception as e:
                print(f"✗ '{sel}': {e}")

        if not found_any:
            print("\n✗ NO PROVENANCE FOUND - SELECTORS MAY BE OUTDATED")

        # Test downloads
        print("\n" + "="*80)
        print("TESTING DOWNLOADS")
        print("="*80)
        download_selectors = selectors.get('downloads', [])
        print(f"\nSelectors (first 5): {download_selectors[:5]}")

        found_any = False
        for sel in download_selectors:
            try:
                if sel.startswith('.') or sel.startswith('#') or sel.startswith('span') or sel.startswith('div'):
                    # CSS selector
                    elements = driver.find_elements(By.CSS_SELECTOR, sel)
                    if elements:
                        print(f"✓ CSS '{sel}': Found {len(elements)} elements")
                        for idx, elem in enumerate(elements[:5]):
                            print(f"  Element {idx}: {elem.text.strip()}")
                        found_any = True
                        break
                else:
                    # XPath selector
                    elements = tree.xpath(sel)
                    if elements:
                        print(f"✓ XPath '{sel}': Found {len(elements)} elements")
                        for idx, elem in enumerate(elements[:5]):
                            print(f"  Element {idx}: {elem.text_content().strip()}")
                        found_any = True
                        break
            except Exception as e:
                print(f"✗ '{sel}': {e}")

        if not found_any:
            print("\n✗ NO DOWNLOADS FOUND - SELECTORS MAY BE OUTDATED")

        # Save page source for manual inspection
        print("\n" + "="*80)
        print("SAVING PAGE SOURCE")
        print("="*80)
        with open('page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("✓ Saved to page_source.html for manual inspection")

    finally:
        driver.quit()

    print("\n" + "="*80)
    print("DIAGNOSTIC COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Test on a sample Kaggle model page
    # Using the model mentioned in the logs: "Qwen 3 VL"
    test_url = "https://www.kaggle.com/models/qwen-lm/qwen/transformers/qwen2.5-vl-7b-instruct"

    # Allow custom URL from command line
    if len(sys.argv) > 1:
        test_url = sys.argv[1]

    test_selectors_on_page(test_url)
