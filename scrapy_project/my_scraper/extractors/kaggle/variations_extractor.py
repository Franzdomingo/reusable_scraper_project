"""
Transformers variations extraction functions
"""

import logging
import re
import time
from typing import Dict, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

from .dropdown_handler import click_dropdown_to_open
from .variation.variation_version_extractor import extract_version
from .variation.variation_downloads_extractor import extract_downloads
from .variation.variation_license_extractor import extract_license
from .variation.variation_base_model_extractor import extract_base_model
from .variation.variation_model_card_extractor import extract_model_card
from .variation.variation_is_finetunable_extractor import extract_is_finetunable
from .variation.variation_example_usage_extractor import extract_example_usage
from .variation.variation_download_method_extractor import extract_download_methods
from .tab_handler import build_tab_queue, click_tab
from .variation.version_popup_extractor import extract_versions_from_popup
from my_scraper.extractors.retry_utils import retry_selenium_find, retry_xpath, retry_click, retry_operation

logger = logging.getLogger(__name__)


def clean_variation_name(raw_name: str) -> str:
    """
    Clean variation name by removing unwanted elements like icons and extra text

    Args:
        raw_name: Raw variation name text from DOM

    Returns:
        Cleaned variation name
    """
    if not raw_name:
        return ''

    # Remove "push_pin" icon text
    cleaned = raw_name.replace('push_pin', '')

    # Remove "(managed by Keras)" or similar text
    cleaned = re.sub(r'\s*\(managed by[^)]*\)', '', cleaned, flags=re.IGNORECASE)

    # Replace newlines with spaces and clean up multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)

    # Strip leading/trailing whitespace
    cleaned = cleaned.strip()

    return cleaned


def extract_variations_for_tab(
    driver: webdriver.Chrome,
    selectors: Dict,
    name: str,
    tab_prefix: str,
    base_url: str,
    variation_counter_start: int = 1
) -> List[Dict]:
    """
    Extract variations for a single tab

    For each base variation, this will create multiple variation entries
    if there are multiple versions available.

    Args:
        driver: Selenium driver instance
        selectors: Selectors configuration dictionary
        name: Model name for logging
        tab_prefix: Tab name to use as prefix (e.g., "Transformers", "GGUF")
        base_url: Base model URL for constructing version URLs
        variation_counter_start: Starting number for variation counter

    Returns:
        List of variation dictionaries with detailed information
        Multiple entries may be created for the same variation_name if multiple versions exist
    """
    variations = []

    try:
        logger.debug(f"Extracting variations for tab '{tab_prefix}' - {name}")

        # Get selectors from configuration
        action_selector = selectors.get('variation_action')
        list_items_selector = selectors.get('variation_list_items')
        # name_selector removed - variation names extracted directly from item.text
        version_selector = selectors.get('variation_version')
        downloads_selector = selectors.get('variation_downloads')
        license_selector = selectors.get('variation_license')
        base_model_selector = selectors.get('variation_base_model')
        model_card_selector = selectors.get('variation_model_card')
        is_finetunable_selector = selectors.get('is_finetunable')
        example_usage_selector = selectors.get('example_usage')

        # Step 1: Click the dropdown button to open the variation list
        if not action_selector:
            logger.warning(f"No action_selector configured for variations")
            return variations

        try:
            # Support both single selector string and list of selectors
            action_selectors = action_selector if isinstance(action_selector, list) else [action_selector]

            # Try each selector in order until one works
            dropdown_found = False
            working_selector = None

            for selector in action_selectors:
                dropdown_buttons = retry_selenium_find(driver, By.CSS_SELECTOR, selector, find_multiple=True)
                logger.debug(f"Trying selector '{selector}': found {len(dropdown_buttons)} dropdown buttons")

                if len(dropdown_buttons) > 0:
                    dropdown_found = True
                    working_selector = selector
                    logger.debug(f"Using selector '{selector}' for dropdown")
                    break

            if not dropdown_found:
                logger.warning(f"No variation dropdown found for {name} with any selector - this model may not have variations")
                return variations

            # Update action_selector to the working one for use in the rest of the function
            action_selector = working_selector

            # Click the first dropdown button to open the variation list
            logger.debug(f"Attempting to click dropdown button for {name}")
            if not click_dropdown_to_open(driver, action_selector):
                logger.warning(f"Could not open variation dropdown for {name} - all click methods failed")
                return variations

            logger.debug(f"Successfully opened variation dropdown for {name}")
            time.sleep(0.5)  # Additional wait for list to render

        except Exception as e:
            logger.error(f"Error finding/clicking variation dropdown for {name}: {e}")
            return variations

        # Step 2: Build a queue of variation buttons to click
        variation_queue = []

        if not list_items_selector:
            logger.warning(f"No list_items_selector configured for variations")
            return variations

        try:
            # Wait for the list container to appear first
            list_container_selector = selectors.get('variation_list_container', 'ul[role="listbox"]')

            logger.debug(f"Waiting for list container with selector '{list_container_selector}'")

            # Try multiple selectors with fallback
            list_container_found = False
            container_selectors = [
                list_container_selector,  # ul[role="listbox"]
                'ul.MuiMenu-list[role="listbox"]',  # More specific MUI selector
                'ul.MuiList-root[role="listbox"]',  # Alternative MUI selector
                'ul[role="listbox"][aria-labelledby]',  # With aria-labelledby attribute
            ]

            for selector in container_selectors:
                try:
                    logger.debug(f"Trying container selector: {selector}")
                    # Use shorter timeout for each attempt (2 seconds)
                    wait = WebDriverWait(driver, 2)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    logger.debug(f"List container appeared with selector: {selector}")
                    list_container_selector = selector  # Update to working selector
                    list_container_found = True
                    break
                except TimeoutException:
                    logger.debug(f"Selector '{selector}' timed out, trying next...")
                    continue

            if not list_container_found:
                logger.warning(f"Could not find list container with any selector")
                return variations

            # Add small delay for list items to render
            time.sleep(0.5)

            # Find all variation list items within the list container
            # Use a more specific selector that targets items within the listbox
            specific_selector = f'{list_container_selector} {list_items_selector}'
            logger.debug(f"Finding list items with selector '{specific_selector}'")

            list_items = retry_selenium_find(driver, By.CSS_SELECTOR, specific_selector, find_multiple=True)
            logger.debug(f"Found {len(list_items)} variation list items")

            if len(list_items) == 0:
                logger.warning(f"Dropdown opened but no variation list items found for {name}")
                return variations

            # Build queue: store variation names and their indices
            for idx, item in enumerate(list_items):
                try:
                    # Extract variation name directly from the list item text
                    # The li[role="option"] element contains the variation name as text
                    raw_name = item.text.strip()

                    # Clean the variation name (remove push_pin, managed by text, etc.)
                    variation_name = clean_variation_name(raw_name)

                    if variation_name:
                        variation_queue.append({
                            'index': idx,
                            'name': variation_name
                        })
                        logger.debug(f"Added to queue - Index {idx}: {variation_name}")

                except Exception as e:
                    logger.warning(f"Error extracting name from list item {idx}: {e}")
                    continue

            logger.debug(f"Built variation queue with {len(variation_queue)} items for {name}")

        except TimeoutException:
            logger.warning(f"Timeout waiting for variation list items to appear for {name}")
            return variations
        except Exception as e:
            logger.error(f"Error building variation queue for {name}: {e}")
            return variations

        # Step 3: Process each variation in the queue
        variation_counter = variation_counter_start

        for queue_item in variation_queue:
            idx = queue_item['index']
            queued_name = queue_item['name']

            try:
                logger.debug(f"Processing variation {variation_counter}/{len(variation_queue)}: {queued_name}")

                # Re-open the dropdown (it may have closed after previous selection)
                if variation_counter > 1:  # Don't re-open on first iteration
                    try:
                        # Add explicit wait for dropdown element to be available
                        logger.debug(f"Waiting for dropdown element to be available for variation {variation_counter}")
                        dropdown_available = False
                        working_selector = None

                        # Support both single selector and list of selectors
                        action_selectors = action_selector if isinstance(action_selector, list) else [action_selector]

                        # Try to find the dropdown element with retries (up to 5 attempts)
                        for attempt in range(5):
                            # Try each selector in order
                            for selector in action_selectors:
                                try:
                                    # Wait for element to be present
                                    wait = WebDriverWait(driver, 1)  # Shorter timeout per selector
                                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                                    dropdown_available = True
                                    working_selector = selector
                                    logger.debug(f"Dropdown element found with selector '{selector}' on attempt {attempt + 1}")
                                    break
                                except TimeoutException:
                                    logger.debug(f"Selector '{selector}' not found on attempt {attempt + 1}")
                                    continue

                            if dropdown_available:
                                break

                            logger.warning(f"No dropdown selector worked on attempt {attempt + 1}, retrying...")
                            time.sleep(0.5)

                        if not dropdown_available:
                            logger.warning(f"Dropdown element not available with any selector after 5 attempts for variation {variation_counter}")
                            continue

                        # Now try to open the dropdown with the working selector
                        if not click_dropdown_to_open(driver, working_selector):
                            logger.warning(f"Could not re-open dropdown for variation {variation_counter}")
                            continue
                        logger.debug(f"Re-opened dropdown for variation {variation_counter}")
                        time.sleep(0.5)  # Increased wait for dropdown to fully open
                    except Exception as e:
                        logger.error(f"Error re-opening dropdown for variation {variation_counter}: {e}")
                        continue

                # Re-find the list items (they may be stale after re-opening dropdown)
                try:
                    # Wait for list container to appear again
                    list_container_selector = selectors.get('variation_list_container', 'ul[role="listbox"]')
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, list_container_selector)))
                    time.sleep(0.3)  # Small delay for items to render

                    # Find items within the list container
                    specific_selector = f'{list_container_selector} {list_items_selector}'
                    list_items = retry_selenium_find(driver, By.CSS_SELECTOR, specific_selector, find_multiple=True)

                    if idx >= len(list_items):
                        logger.warning(f"Index {idx} out of range, only {len(list_items)} items found")
                        continue

                    # Click the variation button at the specified index
                    variation_button = list_items[idx]

                    # Scroll into view before clicking (prevents "element not interactable" errors)
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", variation_button)
                    time.sleep(0.3)  # Wait for scroll to complete

                    # Try JavaScript click (more reliable for dropdown items)
                    driver.execute_script("arguments[0].click();", variation_button)
                    logger.debug(f"Clicked variation button at index {idx}: {queued_name}")
                    time.sleep(0.8)  # Wait for variation details to load

                except (TimeoutException, StaleElementReferenceException) as e:
                    logger.warning(f"Could not find/click variation button at index {idx}: {e}")
                    continue

                # Step 4: Extract variation details after clicking
                variation_name = queued_name  # Use the name from queue

                # Extract version popup data - this returns a LIST of version data
                versions_data = []
                try:
                    versions_data = extract_versions_from_popup(
                        driver, selectors, base_url, variation_counter
                    )
                    logger.debug(f"Found {len(versions_data)} versions for variation {variation_counter}")
                except Exception as e:
                    logger.warning(f"Error extracting version popup data for variation {variation_counter}: {e}")

                # If we found versions, create one variation entry for each version
                if versions_data:
                    for version_data in versions_data:
                        # Create variation dictionary with prefix
                        # Format: "Transformers/variation_01" using tab_prefix
                        variation_id = f'{tab_prefix}/variation_{variation_counter:02d}'

                        variation = {
                            'variation': variation_id,
                            'variation_name': variation_name,
                            'variation_version': version_data.get('version_number', ''),
                            'variation_created_by': version_data.get('created_by', ''),
                            'variation_update_description': version_data.get('update_description', ''),
                            'variation_license': version_data.get('license', ''),
                            'variation_base_model': version_data.get('base_model', ''),
                            'variation_downloads': version_data.get('downloads', ''),
                            'variations_model_card': version_data.get('model_card', ''),
                            'variations_is_finetunable': version_data.get('is_finetunable', ''),
                            'variations_example_usage': version_data.get('example_usage', ''),
                            'download_methods': version_data.get('download_methods', [])
                        }
                        variations.append(variation)
                        logger.info(f"Extracted {variation_id}: {variation_name} (Version: {version_data.get('version_number')}, Created by: {version_data.get('created_by')}, Downloads: {version_data.get('downloads')}, License: {version_data.get('license')})")
                        variation_counter += 1
                else:
                    # No versions found, extract data from current page as single variation
                    logger.debug(f"No versions found in popup, extracting current page data")

                    variation_version = extract_version(driver, version_selector, variation_counter)
                    variation_downloads = extract_downloads(driver, selectors, variation_counter)
                    variation_license = extract_license(driver, license_selector, variation_counter)
                    variation_base_model = extract_base_model(driver, base_model_selector, variation_counter)
                    variation_model_card = extract_model_card(driver, model_card_selector, variation_counter)
                    variation_is_finetunable = extract_is_finetunable(driver, is_finetunable_selector, variation_counter)
                    variation_example_usage = extract_example_usage(driver, example_usage_selector, variation_counter)
                    variation_download_methods = extract_download_methods(driver, variation_counter, selectors, expected_url=base_url)

                    variation_id = f'{tab_prefix}/variation_{variation_counter:02d}'

                    variation = {
                        'variation': variation_id,
                        'variation_name': variation_name,
                        'variation_version': variation_version,
                        'variation_created_by': '',
                        'variation_update_description': '',
                        'variation_license': variation_license,
                        'variation_base_model': variation_base_model,
                        'variation_downloads': variation_downloads,
                        'variations_model_card': variation_model_card,
                        'variations_is_finetunable': variation_is_finetunable,
                        'variations_example_usage': variation_example_usage,
                        'download_methods': variation_download_methods
                    }
                    variations.append(variation)
                    logger.info(f"Extracted {variation_id}: {variation_name} (Version: {variation_version}, Downloads: {variation_downloads}, License: {variation_license})")
                    variation_counter += 1

            except Exception as e:
                logger.warning(f"Error processing variation {variation_counter} ({queued_name}): {e}")
                continue

        if variations:
            logger.info(f"Successfully extracted {len(variations)} variations for tab '{tab_prefix}' - {name}")
        else:
            logger.warning(f"No variations extracted for tab '{tab_prefix}' - {name}")

    except Exception as e:
        logger.error(f"Error extracting variations for tab '{tab_prefix}' - {name}: {e}")

    return variations


def extract_variations(driver: webdriver.Chrome, selectors: Dict, name: str, model_id: int, base_url: str) -> List[Dict]:
    """
    Extract ALL variations across ALL tabs by detecting and clicking each tab

    For each base variation, if multiple versions exist, this will create
    multiple variation entries within the variations array.

    Args:
        driver: Selenium driver instance
        selectors: Selectors configuration dictionary
        name: Model name for logging
        model_id: Model ID
        base_url: Base model URL for constructing version URLs

    Returns:
        List of variation dictionaries with detailed information from all tabs
        Multiple entries may be created for the same variation_name if multiple versions exist
    """
    all_variations = []

    if not driver:
        logger.info(f"No driver provided, skipping variations extraction for {name}")
        return all_variations

    try:
        logger.info(f"Starting multi-tab variations extraction for {name}")

        # Get tab selectors from configuration
        tabs_all_selector = selectors.get('variation_tabs_all')
        tab_text_selector = selectors.get('variation_tab_text')

        if not tabs_all_selector or not tab_text_selector:
            logger.warning(f"Tab selectors not configured, falling back to single-tab extraction")
            # Fallback: extract without tab information
            return extract_variations_for_tab(driver, selectors, name, "variation", base_url, 1)

        # Step 1: Build a tab queue
        tab_queue = build_tab_queue(driver, tabs_all_selector, tab_text_selector, name)

        if len(tab_queue) == 0:
            logger.warning(f"No tabs found for {name}, skipping variations")
            return all_variations

        # Step 2: Process each tab
        variation_counter = 1  # Global counter across all tabs

        for tab_item in tab_queue:
            tab_idx = tab_item['index']
            tab_text = tab_item['text']

            try:
                # Navigate back to base URL before clicking next tab
                # This ensures tabs are available (version URLs may not have tabs)
                logger.info(f"Navigating back to base URL before processing tab: {base_url}")
                driver.get(base_url)
                time.sleep(1.5)  # Wait for page to load
                logger.info(f"Successfully navigated to base URL")

                logger.info(f"Processing tab {tab_idx + 1}/{len(tab_queue)}: {tab_text}")

                # Click the tab button
                if not click_tab(driver, tabs_all_selector, tab_idx, tab_text, expected_url=base_url):
                    continue

                # Extract variations for this tab
                tab_variations = extract_variations_for_tab(
                    driver, selectors, name, tab_text, base_url, variation_counter
                )

                # Add to all_variations and update counter
                all_variations.extend(tab_variations)
                variation_counter += len(tab_variations)

                logger.info(f"Extracted {len(tab_variations)} variations from tab '{tab_text}'")

            except Exception as e:
                logger.warning(f"Error processing tab '{tab_text}': {e}")
                continue

        logger.info(f"Completed multi-tab extraction: {len(all_variations)} total variations from {len(tab_queue)} tabs for {name}")

    except Exception as e:
        logger.error(f"Error in multi-tab extract_variations for {name}: {e}")

    return all_variations
1