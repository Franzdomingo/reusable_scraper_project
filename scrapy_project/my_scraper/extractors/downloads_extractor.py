"""
Downloads extraction functions
"""

import logging
from typing import Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from lxml import html as lxml_html
from my_scraper.utils import is_numeric_value, is_css_selector, is_xpath_selector
from my_scraper.extractors.retry_utils import retry_selenium_find, retry_xpath

logger = logging.getLogger(__name__)


def extract_downloads(driver: webdriver.Chrome, tree: lxml_html.HtmlElement,
                     selectors: Dict, name: str) -> str:
    """
    Extract download count using configured selectors

    Args:
        driver: Selenium driver instance (for dynamic content)
        tree: lxml tree object
        selectors: Selectors configuration dictionary
        name: Model name for logging

    Returns:
        Extracted download count or empty string
    """
    downloads = ""

    # If no driver, can't extract downloads (requires JavaScript rendering)
    if not driver:
        logger.debug(f"No driver provided, skipping downloads extraction for {name}")
        return downloads

    # Wait a moment for dynamic content to load
    import time
    time.sleep(1)

    # Try selectors via Selenium for dynamic content
    # IMPORTANT: Use the FIRST valid match from prioritized selectors
    # Don't collect all candidates - trust the selector priority order
    for selector in selectors.get('downloads', []):
        # Use smart selector detection
        if is_css_selector(selector):
            try:
                logger.debug(f"Trying downloads CSS selector via Selenium: {selector}")
                elements = retry_selenium_find(driver, By.CSS_SELECTOR, selector, max_retries=3, delay=0.5, find_multiple=True)
                logger.debug(f"Found {len(elements)} elements with CSS selector")

                for elem in elements:
                    try:
                        text = elem.text.strip()
                        logger.debug(f"Checking element text: '{text}'")
                        if text and is_numeric_value(text):
                            # Filter out engagement values (small decimals < 1 without K/M/B suffix)
                            try:
                                # Check if it's a small decimal that looks like engagement ratio
                                if '.' in text and not any(x in text.upper() for x in ['K', 'M', 'B']):
                                    val = float(text.replace(',', ''))
                                    if val < 1:
                                        logger.debug(f"Skipping engagement-like value: {text}")
                                        continue
                            except (ValueError, TypeError):
                                pass  # If conversion fails, keep it as candidate

                            # Found a valid value - return it immediately
                            logger.info(f"Found downloads using selector '{selector}': {text}")
                            return text
                    except Exception as e:
                        logger.debug(f"Error getting text from element: {e}")
                        continue
            except Exception as e:
                logger.debug(f"Downloads CSS selector {selector} failed: {e}")
        else:
            # XPath selector - use Selenium for dynamic content
            try:
                logger.debug(f"Trying downloads XPath selector via Selenium: {selector}")
                elements = retry_selenium_find(driver, By.XPATH, selector, max_retries=3, delay=0.5, find_multiple=True)
                logger.debug(f"Found {len(elements)} elements with XPath via Selenium")

                for elem in elements:
                    try:
                        text = elem.text.strip()
                        logger.debug(f"Checking element text: '{text}'")
                        if text and is_numeric_value(text):
                            # Filter out engagement values (small decimals < 1 without K/M/B suffix)
                            try:
                                if '.' in text and not any(x in text.upper() for x in ['K', 'M', 'B']):
                                    val = float(text.replace(',', ''))
                                    if val < 1:
                                        logger.debug(f"Skipping engagement-like value: {text}")
                                        continue
                            except (ValueError, TypeError):
                                pass  # If conversion fails, keep it as candidate

                            # Found a valid value - return it immediately
                            logger.info(f"Found downloads using XPath via Selenium '{selector}': {text}")
                            return text
                    except Exception as e:
                        logger.debug(f"Error getting text from element: {e}")
                        continue
            except Exception as e:
                logger.debug(f"Downloads XPath selector via Selenium {selector} failed: {e}")

    # Try XPath selectors using lxml tree as fallback
    for selector in selectors.get('downloads', []):
        # Use smart selector detection - skip CSS selectors (already tried above)
        if is_css_selector(selector):
            continue

        try:
            logger.debug(f"Trying downloads XPath selector: {selector}")
            download_elements = retry_xpath(tree, selector, max_retries=3, delay=0.5)
            logger.debug(f"Found {len(download_elements)} elements with XPath")

            if download_elements:
                for elem in download_elements:
                    text = elem.text_content().strip()
                    logger.debug(f"Checking element text: '{text}'")
                    if text and is_numeric_value(text):
                        # Filter out engagement values (small decimals < 1 without K/M/B suffix)
                        try:
                            if '.' in text and not any(x in text.upper() for x in ['K', 'M', 'B']):
                                val = float(text.replace(',', ''))
                                if val < 1:
                                    logger.debug(f"Skipping engagement-like value: {text}")
                                    continue
                        except (ValueError, TypeError):
                            pass  # If conversion fails, keep it as candidate

                        # Found a valid value - return it immediately
                        logger.info(f"Found downloads using XPath '{selector}': {text}")
                        return text
        except Exception as e:
            logger.debug(f"Downloads XPath selector {selector} failed: {e}")
            continue

    # Fallback: Search for numeric values near "DOWNLOADS" heading
    if not downloads:
        logger.debug(f"Trying fallback: searching for downloads near 'DOWNLOADS' heading")
        all_candidates = []
        try:
            # Strategy 1: Find the DOWNLOADS heading and look for siblings/nearby elements
            downloads_heading = retry_selenium_find(driver, By.XPATH, "//*[contains(text(), 'DOWNLOADS') or contains(text(), 'Downloads')]", max_retries=3, delay=0.5, find_multiple=True)

            if downloads_heading:
                logger.debug(f"Found {len(downloads_heading)} 'DOWNLOADS' headings")

                # Look for parent container and find numeric value within it
                for heading in downloads_heading[:2]:
                    try:
                        # Try to find parent div/section
                        parent = heading.find_element(By.XPATH, './ancestor::div[1]')
                        # Look for all text in the parent
                        text = parent.text
                        # Extract numbers from the text
                        import re
                        numbers = re.findall(r'\d+(?:[,.]\d+)?[KMB]?', text)
                        for num in numbers:
                            if is_numeric_value(num):
                                all_candidates.append(num)
                                logger.debug(f"Found candidate near DOWNLOADS heading: {num}")
                    except Exception:
                        continue

            # Strategy 2: Look for all spans with numeric values
            if not all_candidates:
                all_spans = retry_selenium_find(driver, By.TAG_NAME, 'span', max_retries=3, delay=0.5, find_multiple=True)

                for span in all_spans:
                    try:
                        text = span.text.strip()
                        if text and is_numeric_value(text):
                            # Skip very small decimals (engagement ratios)
                            try:
                                if '.' in text and not any(x in text.upper() for x in ['K', 'M', 'B']):
                                    val = float(text.replace(',', ''))
                                    if val < 1:
                                        continue
                            except (ValueError, TypeError):
                                pass

                            all_candidates.append(text)
                    except:
                        continue

            if all_candidates:
                logger.info(f"Found {len(all_candidates)} download candidates: {all_candidates[:10]}")

                # Prefer values with K/M/B suffix, then largest plain number
                with_suffix = [c for c in all_candidates if any(x in c.upper() for x in ['K', 'M', 'B'])]
                if with_suffix:
                    downloads = with_suffix[0]
                    logger.info(f"Using first value with suffix: {downloads}")
                elif all_candidates:
                    # Find largest number (likely to be total downloads)
                    def to_int(val):
                        try:
                            digits = ''.join(c for c in val if c.isdigit())
                            return int(digits) if digits else 0
                        except:
                            return 0
                    downloads = max(all_candidates, key=to_int)
                    logger.info(f"Using largest number: {downloads}")

        except Exception as e:
            logger.error(f"Fallback download search failed: {e}")

    if not downloads:
        logger.warning(f"Could not find downloads for {name}")

    return downloads
