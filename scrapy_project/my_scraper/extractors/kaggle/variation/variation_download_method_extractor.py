"""
Download method extraction for variations
Extracts download method names and commands from the download popup
"""

import logging
import time
from typing import Dict, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from my_scraper.extractors.retry_utils import retry_selenium_find, retry_click, retry_operation, check_and_handle_redirect
from my_scraper.selectors.site_selectors import KaggleSelectors
from my_scraper.extractors.kaggle.dropdown_handler import click_dropdown_to_open

logger = logging.getLogger(__name__)


def extract_download_methods(driver: webdriver.Chrome, variation_counter: int, selectors: Dict = None, expected_url: str = None) -> List[Dict[str, str]]:
    """
    Extract download methods by clicking the download button and iterating through method options

    This function:
    1. Clicks the download button to open the download popup
    2. Finds all download method options in the dropdown
    3. For each method, clicks it and extracts the command
    4. Returns a list of {download_method_name, download_method_command} dictionaries

    Args:
        driver: Selenium driver instance
        variation_counter: Current variation number for logging
        selectors: Optional selectors dictionary (will use defaults if not provided)
        expected_url: Expected URL to check for redirects (e.g., to /license/consent)

    Returns:
        List of dictionaries containing download_method_name and download_method_command
        Returns empty list if extraction fails
    """
    download_methods = []

    # Get selectors from config or use defaults
    if selectors is None:
        selectors = {}

    button_selectors_config = selectors.get('download_method_button', KaggleSelectors.DOWNLOAD_METHOD_BUTTON)
    popup_selectors_config = selectors.get('download_popup', KaggleSelectors.DOWNLOAD_POPUP)
    dropdown_selectors_config = selectors.get('download_via_dropdown', KaggleSelectors.DOWNLOAD_VIA_DROPDOWN)
    list_items_selectors_config = selectors.get('download_method_list_items', KaggleSelectors.DOWNLOAD_METHOD_LIST_ITEMS)
    method_name_selectors_config = selectors.get('download_method_name', KaggleSelectors.DOWNLOAD_METHOD_NAME)
    command_selectors_config = selectors.get('download_command', KaggleSelectors.DOWNLOAD_COMMAND)

    try:
        # Step 1: Click the download button to open popup
        logger.debug(f"Variation {variation_counter}: Attempting to click download button")

        # Wait a bit for the page to stabilize
        time.sleep(0.5)

        # Try to find and click the download button using multiple strategies
        button_clicked = False

        # Convert config selectors to (By, selector) tuples
        button_selectors = []
        for selector in button_selectors_config:
            if selector.startswith('//') or selector.startswith('('):
                button_selectors.append((By.XPATH, selector))
            else:
                button_selectors.append((By.CSS_SELECTOR, selector))

        for by_type, selector in button_selectors:
            try:
                logger.debug(f"Variation {variation_counter}: Trying to find button with {by_type}: {selector}")
                button = retry_selenium_find(driver, by_type, selector)

                if not button:
                    logger.debug(f"Variation {variation_counter}: Button not found with {by_type}: {selector}")
                    continue

                # Scroll into view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(0.3)

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
                        logger.debug(f"Variation {variation_counter}: Trying {method_name}")
                        click_func()
                        time.sleep(0.8)  # Wait for popup to appear

                        # Check if popup appeared (try multiple selectors for popup)
                        popup_found = False
                        popup_selectors = [
                            (By.XPATH, '/html/body/div[2]/div[3]/div/div[1]/div/div'),
                            (By.CSS_SELECTOR, 'div[role="dialog"]'),
                            (By.XPATH, '//div[contains(@class, "MuiDialog")]//div[contains(@class, "MuiDialogContent")]'),
                        ]

                        for popup_by, popup_selector in popup_selectors:
                            try:
                                retry_selenium_find(driver, popup_by, popup_selector)
                                popup_found = True
                                break
                            except:
                                continue

                        if popup_found:
                            logger.debug(f"Variation {variation_counter}: Clicked download button using {method_name}")
                            button_clicked = True
                            break
                        else:
                            logger.debug(f"Variation {variation_counter}: Popup didn't appear after {method_name}, trying next method")
                            continue

                    except (ElementClickInterceptedException, Exception) as e:
                        logger.debug(f"Variation {variation_counter}: {method_name} failed: {e}")
                        continue

                if button_clicked:
                    break

            except (NoSuchElementException, Exception) as e:
                logger.debug(f"Variation {variation_counter}: Could not find/click button with {by_type}: {selector} - {e}")
                continue

        if not button_clicked:
            logger.warning(f"Variation {variation_counter}: Could not click download button - all methods failed")
            return download_methods

        # Check if we were redirected to license/consent page
        if expected_url:
            if not check_and_handle_redirect(driver, expected_url, f"Variation {variation_counter} - Download methods"):
                logger.warning(f"Variation {variation_counter}: Redirected to license/consent page, cannot extract download methods")
                return download_methods

        # Step 2: Wait for popup to appear
        popup_appeared = False

        try:
            wait = WebDriverWait(driver, 5)

            for selector in popup_selectors_config:
                try:
                    logger.debug(f"Variation {variation_counter}: Checking for popup with selector: {selector}")
                    wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                    popup_appeared = True
                    logger.debug(f"Variation {variation_counter}: Download popup appeared")
                    break
                except TimeoutException:
                    continue

            if not popup_appeared:
                logger.warning(f"Variation {variation_counter}: Timeout waiting for download popup to appear")
                return download_methods

            time.sleep(1.5)  # Wait longer for popup content to fully render (increased from 0.8)
        except Exception as e:
            logger.warning(f"Variation {variation_counter}: Error waiting for popup: {e}")
            return download_methods

        # Step 3: Click the "Download via" dropdown to open the methods list
        logger.debug(f"Variation {variation_counter}: Looking for 'Download via' dropdown")

        # First, wait specifically for the combobox to be present and get it
        dropdown = None
        try:
            wait = WebDriverWait(driver, 5)
            dropdown = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="combobox" and contains(@aria-label, "Download via")]')))
            logger.debug(f"Variation {variation_counter}: Found 'Download via' combobox")
            time.sleep(0.3)
        except TimeoutException:
            logger.warning(f"Variation {variation_counter}: Timeout waiting for 'Download via' combobox")
            return download_methods

        # Now use the robust click_dropdown_to_open function
        selector = '//div[@role="combobox" and contains(@aria-label, "Download via")]'
        logger.debug(f"Variation {variation_counter}: Attempting to open 'Download via' dropdown")
        dropdown_clicked = click_dropdown_to_open(driver, selector, timeout=5)

        if not dropdown_clicked:
            logger.warning(f"Variation {variation_counter}: Could not click Download via dropdown")
            return download_methods

        # Step 4: Wait for listbox with download method options to appear
        logger.debug(f"Variation {variation_counter}: Waiting for download methods listbox to appear")

        try:
            # Get the aria-controls attribute to find the controlled listbox ID
            aria_controls = None
            for selector in dropdown_selectors_config:
                try:
                    dropdown_elem = retry_selenium_find(driver, By.XPATH, selector)
                    if dropdown_elem:
                        aria_controls = dropdown_elem.get_attribute('aria-controls')
                        if aria_controls:
                            logger.debug(f"Variation {variation_counter}: Found aria-controls='{aria_controls}'")
                            break
                except:
                    continue

            # Wait for the listbox to appear after clicking dropdown
            wait = WebDriverWait(driver, 5)
            listbox_appeared = False

            # Try to find the listbox with the download methods
            listbox_selectors = []

            # If we found aria-controls, add it as first priority
            if aria_controls:
                listbox_selectors.append(f'//ul[@id="{aria_controls}"]')

            # Add generic selectors
            listbox_selectors.extend([
                '//ul[@role="listbox" and contains(@class, "MuiMenu-list")]',
                '//ul[@role="listbox"]',
                '//div[@role="presentation"]//ul[@role="listbox"]',
            ])

            for listbox_sel in listbox_selectors:
                try:
                    wait.until(EC.presence_of_element_located((By.XPATH, listbox_sel)))
                    logger.debug(f"Variation {variation_counter}: Listbox appeared")
                    listbox_appeared = True
                    break
                except TimeoutException:
                    continue

            if not listbox_appeared:
                logger.warning(f"Variation {variation_counter}: Listbox did not appear after clicking dropdown")
                # Log what we can see for debugging
                try:
                    all_uls = driver.find_elements(By.TAG_NAME, 'ul')
                    visible_uls = [ul for ul in all_uls if ul.is_displayed()]
                    logger.debug(f"Variation {variation_counter}: Found {len(visible_uls)} visible <ul> elements")
                except:
                    pass
                return download_methods

            time.sleep(0.5)  # Additional wait for items to render

        except Exception as e:
            logger.warning(f"Variation {variation_counter}: Error waiting for listbox: {e}")
            return download_methods

        # Step 5: Find all menu items (download method options) in the opened listbox
        menu_items = []
        try:
            for items_selector in list_items_selectors_config:
                try:
                    menu_items = retry_selenium_find(driver, By.XPATH, items_selector, find_multiple=True)
                    if len(menu_items) > 0:
                        logger.debug(f"Variation {variation_counter}: Found {len(menu_items)} menu items")
                        break
                except:
                    continue

            if len(menu_items) == 0:
                logger.warning(f"Variation {variation_counter}: No download method options found")
                return download_methods

        except Exception as e:
            logger.warning(f"Variation {variation_counter}: Error finding download method options: {e}")
            return download_methods

        # Step 6: Click each method and extract its command
        # Store the working selector for re-finding items
        working_items_selector = None
        for selector in list_items_selectors_config:
            try:
                test_items = retry_selenium_find(driver, By.XPATH, selector, find_multiple=True)
                if len(test_items) > 0:
                    working_items_selector = selector
                    break
            except:
                continue

        for idx in range(len(menu_items)):
            try:
                logger.debug(f"Variation {variation_counter}: Processing download method {idx + 1}/{len(menu_items)}")

                # Re-find menu items (they may be stale)
                if working_items_selector:
                    menu_items = retry_selenium_find(driver, By.XPATH, working_items_selector, find_multiple=True)

                if idx >= len(menu_items):
                    logger.warning(f"Variation {variation_counter}: Menu item {idx + 1} no longer available")
                    break

                item = menu_items[idx]

                # Extract the method name from the list item
                method_name = ""
                try:
                    # Try to find the name within the item using config selectors
                    for name_sel in method_name_selectors_config:
                        try:
                            name_elem = retry_selenium_find(item, By.CSS_SELECTOR, name_sel)
                            if name_elem:
                                method_name = name_elem.text.strip()
                                if method_name:
                                    break
                        except:
                            continue

                    # Fallback to item text if no specific element found
                    if not method_name:
                        method_name = item.text.strip()

                except Exception as e:
                    # Final fallback to item text
                    method_name = item.text.strip()

                logger.debug(f"Variation {variation_counter}: Found download method '{method_name}'")

                # Click the method option to display its command
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
                    time.sleep(0.2)
                    driver.execute_script("arguments[0].click();", item)
                    logger.debug(f"Variation {variation_counter}: Clicked download method '{method_name}'")

                    # Wait longer for the command area to update with the new command
                    # The UI needs time to fetch and display the specific command for this method
                    time.sleep(1.2)  # Increased from 0.5s to ensure command updates
                except Exception as e:
                    logger.warning(f"Variation {variation_counter}: Could not click method '{method_name}': {e}")
                    continue

                # Extract the command from the code block
                # Try to find the command in the popup (more specific context)
                command = ""

                # First, try to find the command within the download popup context
                # to avoid getting commands from other parts of the page
                popup_command_selectors = [
                    '//div[@role="presentation"]//div[contains(@class, "MuiPaper-root")]//pre/code',
                    '//div[contains(@class, "MuiPopover-root")]//pre/code',
                ]

                # Try popup-specific selectors first
                for cmd_selector in popup_command_selectors:
                    try:
                        logger.debug(f"Variation {variation_counter}: Trying popup command selector: {cmd_selector}")
                        command_elem = retry_selenium_find(driver, By.XPATH, cmd_selector)
                        if command_elem:
                            # Try multiple methods to get text
                            command = command_elem.text.strip()
                            if not command:
                                command = command_elem.get_attribute('innerText')
                                if command:
                                    command = command.strip()
                            if not command:
                                command = command_elem.get_attribute('textContent')
                                if command:
                                    command = command.strip()

                            # Verify this looks like a download command (not example usage)
                            # Download commands typically contain specific patterns
                            if command and any(pattern in command.lower() for pattern in ['kagglehub.model_download', 'kaggle models', 'curl', 'wget']):
                                logger.debug(f"Variation {variation_counter}: Extracted command for '{method_name}'")
                                break
                            else:
                                logger.debug(f"Variation {variation_counter}: Found text but doesn't look like download command: {command[:100]}...")
                                command = ""  # Reset if it's not a download command
                    except Exception as e:
                        logger.debug(f"Variation {variation_counter}: Could not extract command with {cmd_selector}: {e}")
                        continue

                # If popup-specific selectors didn't work, try the general ones
                if not command:
                    for cmd_selector in command_selectors_config:
                        try:
                            logger.debug(f"Variation {variation_counter}: Trying command selector: {cmd_selector}")
                            command_elem = retry_selenium_find(driver, By.XPATH, cmd_selector)
                            if command_elem:
                                # Try multiple methods to get text
                                command = command_elem.text.strip()
                                if not command:
                                    command = command_elem.get_attribute('innerText')
                                    if command:
                                        command = command.strip()
                                if not command:
                                    command = command_elem.get_attribute('textContent')
                                    if command:
                                        command = command.strip()

                                if command:
                                    logger.debug(f"Variation {variation_counter}: Extracted command for '{method_name}'")
                                    break
                                else:
                                    logger.debug(f"Variation {variation_counter}: Found element but text is empty with {cmd_selector}")
                        except Exception as e:
                            logger.debug(f"Variation {variation_counter}: Could not extract command with {cmd_selector}: {e}")
                            continue

                if not command:
                    logger.warning(f"Variation {variation_counter}: Could not extract command for '{method_name}' with any selector")

                # Add to results
                if method_name or command:
                    download_methods.append({
                        'download_method_name': method_name,
                        'download_method_command': command
                    })

                # Re-open dropdown for next method (if not last)
                if idx < len(menu_items) - 1:
                    logger.debug(f"Variation {variation_counter}: Re-opening dropdown for next method")

                    # Wait a bit for previous command to be displayed
                    time.sleep(0.3)

                    # Re-find and click the dropdown (element may be stale after clicking option)
                    # Use the robust click_dropdown_to_open function with the original selector
                    dropdown_reopened = click_dropdown_to_open(driver, '//div[@role="combobox" and contains(@aria-label, "Download via")]', timeout=5)

                    if not dropdown_reopened:
                        logger.warning(f"Variation {variation_counter}: Could not re-open dropdown")
                        break

                    # Wait for listbox to appear again and items to load
                    time.sleep(0.8)

            except Exception as e:
                logger.warning(f"Variation {variation_counter}: Error processing download method {idx + 1}: {e}")
                continue

        if download_methods:
            logger.info(f"Variation {variation_counter}: Extracted {len(download_methods)} download methods")
        else:
            logger.warning(f"Variation {variation_counter}: No download methods extracted")

        # Close popup if still open
        try:
            from selenium.webdriver.common.keys import Keys
            retry_selenium_find(driver, By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(0.2)
        except:
            pass

    except Exception as e:
        logger.error(f"Variation {variation_counter}: Error extracting download methods: {e}")

    return download_methods
