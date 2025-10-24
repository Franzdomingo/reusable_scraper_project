"""
Version popup extraction functions
Extracts version data from the versions popup list
"""

import logging
import time
import re
from typing import Dict, List, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from my_scraper.extractors.retry_utils import retry_selenium_find, retry_xpath, retry_click, retry_operation

logger = logging.getLogger(__name__)


def extract_version_number_from_text(version_text: str) -> str:
    """
    Extract numeric version from text like "Version 4"

    Args:
        version_text: Text containing version number (e.g., "Version 4")

    Returns:
        Numeric version string (e.g., "4")
    """
    # Extract number from text like "Version 4"
    match = re.search(r'Version\s+(\d+)', version_text, re.IGNORECASE)
    if match:
        return match.group(1)

    # If no match, try to extract any number
    match = re.search(r'(\d+)', version_text)
    if match:
        return match.group(1)

    return ""


def construct_version_url(base_url: str, version_number: str) -> str:
    """
    Construct version URL from base URL and version number

    Args:
        base_url: Base model URL (e.g., https://www.kaggle.com/models/google/gemma/keras)
        version_number: Version number (e.g., "4")

    Returns:
        Version URL (e.g., https://www.kaggle.com/models/google/gemma/keras/4)
    """
    # Remove trailing slash if present
    base_url = base_url.rstrip('/')

    # Add version number
    return f"{base_url}/{version_number}"


def extract_versions_from_popup(
    driver: webdriver.Chrome,
    selectors: Dict,
    base_url: str,
    variation_counter: int
) -> List[Dict]:
    """
    Extract version data from the versions popup and scrape each version

    This function:
    1. Clicks the versions button to open the popup
    2. Extracts all version items from the popup
    3. For each version, clicks it and navigates to that version
    4. Extracts full data for that version (downloads, license, model_card, etc.)
    5. Returns to popup and continues to next version

    Args:
        driver: Selenium driver instance
        selectors: Selectors configuration dictionary
        base_url: Base model URL from response
        variation_counter: Variation counter for logging

    Returns:
        List of version dictionaries, each containing:
        - created_by: Creator/author
        - update_description: Update description
        - version_number: Version text (e.g., "Version 4")
        - downloads: Downloads count for this version
        - license: License for this version
        - model_card: Model card for this version
        - is_finetunable: Whether finetunable
        - example_usage: Usage example
    """
    versions_data = []

    try:
        # Get selectors
        versions_button_selector = selectors.get('variation_versions_button')
        popup_items_selector = selectors.get('variation_versions_popup_items')
        created_by_selector = selectors.get('variation_version_created_by')
        update_desc_selector = selectors.get('variation_version_update_desc')
        version_number_selector = selectors.get('variation_version_number')

        if not all([versions_button_selector, popup_items_selector]):
            logger.warning(f"Version popup selectors not configured")
            return created_by, update_description, version_urls

        # Step 1: Click the versions button to open popup
        logger.info(f"Attempting to click versions button for variation {variation_counter}")

        # Wait a bit for the page to stabilize after variation selection
        time.sleep(1.0)

        # First, let's try to find all possible versions button candidates
        button_clicked = False
        button_candidates = []

        # Strategy 1: Try configured selectors
        for selector in (versions_button_selector if isinstance(versions_button_selector, list) else [versions_button_selector]):
            try:
                # Determine selector type (XPath or CSS)
                if selector.startswith('/') or selector.startswith('('):
                    by_type = By.XPATH
                else:
                    by_type = By.CSS_SELECTOR

                # Find all matching elements
                elements = retry_selenium_find(driver, by_type, selector, find_multiple=True)
                for elem in elements:
                    button_candidates.append(('configured_selector', selector, elem))
                    logger.debug(f"Found button candidate with selector '{selector}': text='{elem.text[:50]}'")

            except (NoSuchElementException, Exception) as e:
                logger.debug(f"Could not find versions button with selector '{selector}': {e}")
                continue

        # Strategy 2: Look for elements containing "Version" text (more resilient)
        if not button_candidates:
            logger.info(f"Configured selectors didn't find button, trying text-based search")
            try:
                # Look for <a> tags containing "Version" text
                version_links = retry_selenium_find(driver, By.XPATH, "//a[contains(text(), 'Version')]", find_multiple=True)
                for elem in version_links:
                    button_candidates.append(('text_search', 'xpath://a[contains(text(), "Version")]', elem))
                    logger.debug(f"Found button candidate by text search: text='{elem.text[:50]}'")

                # Also try looking for elements with "version" in aria-label
                aria_elements = retry_selenium_find(driver, By.XPATH, "//*[contains(@aria-label, 'version') or contains(@aria-label, 'Version')]", find_multiple=True)
                for elem in aria_elements:
                    button_candidates.append(('aria_label', f'xpath://*[@aria-label contains version]', elem))
                    logger.debug(f"Found button candidate by aria-label: aria-label='{elem.get_attribute('aria-label')}'")

            except Exception as e:
                logger.debug(f"Text-based search failed: {e}")

        # Strategy 3: If still no candidates, log detailed debug info
        if not button_candidates:
            logger.warning(f"No versions button candidates found for variation {variation_counter}")
            logger.warning(f"Dumping debug info:")
            try:
                # Find all links on the page
                all_links = retry_selenium_find(driver, By.TAG_NAME, 'a', find_multiple=True)
                logger.warning(f"Total <a> tags on page: {len(all_links)}")

                # Look for any links with "version" text
                for link in all_links[:20]:  # First 20 links
                    if 'version' in link.text.lower():
                        logger.warning(f"  Link with 'version' text: '{link.text[:100]}', classes='{link.get_attribute('class')}'")
            except:
                pass

            return versions_data

        logger.info(f"Found {len(button_candidates)} versions button candidate(s)")

        # Try to click each candidate
        for strategy, selector_desc, button in button_candidates:
            try:
                # Check if element is visible and enabled
                if not button.is_displayed():
                    logger.debug(f"Button candidate not visible, skipping: {selector_desc}")
                    continue

                # Scroll element into view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(0.3)

                # Hide any overlays that might intercept clicks
                driver.execute_script("""
                    // Remove or hide common overlay elements
                    document.querySelectorAll('[class*="overlay"], [class*="modal"], [class*="popup"]').forEach(el => {
                        if (el.style.zIndex > 100) el.style.display = 'none';
                    });
                """)

                # Try multiple click methods
                click_methods = [
                    ('JavaScript click', lambda: driver.execute_script("arguments[0].click();", button)),
                    ('JavaScript MouseEvent', lambda: driver.execute_script("""
                        var evt = new MouseEvent('click', {
                            bubbles: true,
                            cancelable: true,
                            view: window
                        });
                        arguments[0].dispatchEvent(evt);
                    """, button)),
                    ('Regular click', lambda: button.click()),
                ]

                for method_name, click_func in click_methods:
                    try:
                        logger.debug(f"Trying {method_name} for button found via {strategy}")
                        click_func()
                        time.sleep(0.8)  # Increased wait time for popup to appear

                        # Check if popup appeared (look for popup items)
                        try:
                            popup_elements = retry_selenium_find(driver, By.CSS_SELECTOR, popup_items_selector, find_multiple=True)
                            if len(popup_elements) > 0:
                                logger.info(f"✓ Successfully clicked versions button using {method_name} via {strategy}")
                                logger.info(f"  Selector: {selector_desc}")
                                logger.info(f"  Button text: '{button.text[:100]}'")
                                button_clicked = True
                                break
                            else:
                                logger.debug(f"Popup items not found after click, trying next method")
                                continue
                        except NoSuchElementException:
                            # Popup didn't appear, try next method
                            logger.debug(f"Popup didn't appear after {method_name}, trying next method")
                            continue

                    except (ElementClickInterceptedException, Exception) as e:
                        logger.debug(f"{method_name} failed: {e}")
                        continue

                if button_clicked:
                    break

            except (NoSuchElementException, Exception) as e:
                logger.debug(f"Could not click button candidate: {e}")
                continue

        if not button_clicked:
            logger.warning(f"Could not click versions button for variation {variation_counter} - tried all {len(button_candidates)} candidates and all click methods")
            # Log current page URL for debugging
            logger.warning(f"Current URL: {driver.current_url}")
            return versions_data

        # Step 2: Wait for popup to appear and find all version items
        try:
            wait = WebDriverWait(driver, 3)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, popup_items_selector)))
            logger.info(f"Version popup appeared")
            time.sleep(0.3)  # Additional wait for items to render
        except TimeoutException:
            logger.warning(f"Timeout waiting for version popup to appear")
            return versions_data

        # Find all version items
        version_items = retry_selenium_find(driver, By.CSS_SELECTOR, popup_items_selector, find_multiple=True)
        logger.info(f"Found {len(version_items)} version items in popup")

        if len(version_items) == 0:
            logger.warning(f"No version items found in popup")
            return versions_data

        # Step 3: Click each version item and extract data
        # Import extractors we need
        from .variation_downloads_extractor import extract_downloads
        from .variation_license_extractor import extract_license
        from .variation_model_card_extractor import extract_model_card
        from .variation_is_finetunable_extractor import extract_is_finetunable
        from .variation_example_usage_extractor import extract_example_usage
        from .variation_version_metadata_extractor import extract_created_by, extract_update_description

        for idx in range(len(version_items)):
            try:
                logger.info(f"Processing version item {idx + 1}/{len(version_items)}")

                # Re-open popup if needed (it may have closed)
                if idx > 0:
                    # Click version button again to open popup
                    logger.debug(f"Re-opening version popup for item {idx + 1}")
                    # Use same clicking logic as before
                    button_found = False
                    for selector in (versions_button_selector if isinstance(versions_button_selector, list) else [versions_button_selector]):
                        try:
                            if selector.startswith('/') or selector.startswith('('):
                                button = retry_selenium_find(driver, By.XPATH, selector)
                            else:
                                button = retry_selenium_find(driver, By.CSS_SELECTOR, selector)

                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                            time.sleep(0.1)
                            driver.execute_script("arguments[0].click();", button)
                            time.sleep(0.5)
                            button_found = True
                            break
                        except:
                            continue

                    if not button_found:
                        logger.warning(f"Could not re-open popup for version {idx + 1}")
                        break

                    # Wait for popup
                    time.sleep(0.3)

                # Re-find version items (they may be stale)
                version_items = retry_selenium_find(driver, By.CSS_SELECTOR, popup_items_selector, find_multiple=True)
                if idx >= len(version_items):
                    logger.warning(f"Version item {idx + 1} no longer available")
                    break

                item = version_items[idx]

                # Extract metadata from popup item
                item_created_by = extract_created_by(item, created_by_selector)
                item_update_desc = extract_update_description(item, update_desc_selector)
                item_version_text = ""

                # Extract version number
                if version_number_selector:
                    for selector in (version_number_selector if isinstance(version_number_selector, list) else [version_number_selector]):
                        try:
                            elem = retry_selenium_find(item, By.CSS_SELECTOR, selector)
                            item_version_text = elem.text.strip()
                            if item_version_text:
                                break
                        except NoSuchElementException:
                            continue

                logger.info(f"Version {idx + 1}: {item_version_text} (Created by: {item_created_by})")

                # Click the version item to navigate to that version
                try:
                    # Find the clickable link within the item
                    link = retry_selenium_find(item, By.CSS_SELECTOR, 'a')
                    driver.execute_script("arguments[0].click();", link)
                    logger.info(f"Clicked version {idx + 1}: {item_version_text}")
                    time.sleep(1.0)  # Wait for page to load/update

                    # Log current URL after version switch
                    current_url = driver.current_url
                    logger.info(f"Currently on URL: {current_url}")
                except Exception as e:
                    logger.warning(f"Could not click version {idx + 1}: {e}")
                    continue

                # Extract data for this version
                version_downloads = extract_downloads(driver, selectors, variation_counter)
                version_license = extract_license(driver, selectors.get('variation_license'), variation_counter)
                version_model_card = extract_model_card(driver, selectors.get('variation_model_card'), variation_counter)
                version_is_finetunable = extract_is_finetunable(driver, selectors.get('is_finetunable'), variation_counter)
                version_example_usage = extract_example_usage(driver, selectors.get('example_usage'), variation_counter)

                # Create version data dictionary
                version_data = {
                    'created_by': item_created_by,
                    'update_description': item_update_desc,
                    'version_number': item_version_text,
                    'downloads': version_downloads,
                    'license': version_license,
                    'model_card': version_model_card,
                    'is_finetunable': version_is_finetunable,
                    'example_usage': version_example_usage
                }

                versions_data.append(version_data)
                logger.info(f"Extracted version {idx + 1}: {item_version_text} - Downloads: {version_downloads}, License: {version_license}")

            except Exception as e:
                logger.warning(f"Error processing version item {idx + 1}: {e}")
                continue

        logger.info(f"Extracted data for {len(versions_data)} versions from popup")

        # Close popup if still open
        try:
            from selenium.webdriver.common.keys import Keys
            retry_selenium_find(driver, By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(0.2)
        except:
            pass

    except Exception as e:
        logger.error(f"Error extracting versions from popup: {e}")

    return versions_data
