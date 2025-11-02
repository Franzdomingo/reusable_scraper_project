"""
Variation version metadata extraction (created_by and update_description)
"""

import logging
import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from my_scraper.extractors.retry_utils import retry_selenium_find, retry_xpath, retry_click, retry_operation

logger = logging.getLogger(__name__)


def extract_created_by(item, created_by_selector) -> str:
    """
    Extract created_by field using multiple selectors

    Args:
        item: Selenium WebElement (version item from popup)
        created_by_selector: Single selector or list of selectors (CSS)

    Returns:
        Created by string or empty string if not found
    """
    created_by_selectors = created_by_selector if isinstance(created_by_selector, list) else [created_by_selector] if created_by_selector else []

    logger.debug(f"extract_created_by: Have {len(created_by_selectors)} selectors to try")

    for idx, selector in enumerate(created_by_selectors):
        try:
            logger.debug(f"extract_created_by: Trying selector {idx + 1}: {selector}")
            elem = retry_selenium_find(item, By.CSS_SELECTOR, selector)
            if elem:
                created_by = elem.text.strip()
                logger.debug(f"extract_created_by: Element found, text='{created_by}'")

                if created_by:
                    logger.debug(f"extract_created_by: Extracted '{created_by}'")
                    return created_by
                else:
                    logger.debug(f"extract_created_by: Element text is empty")
            else:
                logger.debug(f"extract_created_by: retry_selenium_find returned None")
        except NoSuchElementException:
            logger.debug(f"extract_created_by: Selector {idx + 1}/{len(created_by_selectors)} not found (NoSuchElementException)")
            continue
        except Exception as e:
            logger.debug(f"extract_created_by: Selector {idx + 1}/{len(created_by_selectors)} failed: {e}")
            continue

    if created_by_selectors:
        logger.debug(f"extract_created_by: No created_by found")
    else:
        logger.debug(f"extract_created_by: No selectors provided")

    return ""


def extract_update_description(item, update_desc_selector) -> str:
    """
    Extract update_description field using multiple selectors

    Args:
        item: Selenium WebElement (version item from popup)
        update_desc_selector: Single selector or list of selectors (CSS)

    Returns:
        Update description string or empty string if not found
    """
    update_desc_selectors = update_desc_selector if isinstance(update_desc_selector, list) else [update_desc_selector] if update_desc_selector else []

    logger.debug(f"extract_update_description: Have {len(update_desc_selectors)} selectors to try")

    for idx, selector in enumerate(update_desc_selectors):
        try:
            logger.debug(f"extract_update_description: Trying selector {idx + 1}: {selector}")
            elem = retry_selenium_find(item, By.CSS_SELECTOR, selector)
            if elem:
                update_desc = elem.text.strip()
                logger.debug(f"extract_update_description: Element found, text='{update_desc}'")

                if update_desc:
                    logger.debug(f"extract_update_description: Extracted '{update_desc}'")
                    return update_desc
                else:
                    logger.debug(f"extract_update_description: Element text is empty")
            else:
                logger.debug(f"extract_update_description: retry_selenium_find returned None")
        except NoSuchElementException:
            logger.debug(f"extract_update_description: Selector {idx + 1}/{len(update_desc_selectors)} not found (NoSuchElementException)")
            continue
        except Exception as e:
            logger.debug(f"extract_update_description: Selector {idx + 1}/{len(update_desc_selectors)} failed: {e}")
            continue

    if update_desc_selectors:
        logger.debug(f"extract_update_description: No update_description found")
    else:
        logger.debug(f"extract_update_description: No selectors provided")

    return ""
