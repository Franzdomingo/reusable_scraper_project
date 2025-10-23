"""
Variation version metadata extraction (created_by and update_description)
"""

import logging
import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

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

    for idx, selector in enumerate(created_by_selectors):
        try:
            elem = item.find_element(By.CSS_SELECTOR, selector)
            created_by = elem.text.strip()

            if created_by:

                logger.debug(f"Found created_by '{created_by}' using selector {idx + 1}/{len(created_by_selectors)}")
                return created_by
        except NoSuchElementException:
            logger.debug(f"Created by selector {idx + 1}/{len(created_by_selectors)} not found")
            continue
        except Exception as e:
            logger.debug(f"Created by selector {idx + 1}/{len(created_by_selectors)} failed: {e}")
            continue

    if created_by_selectors:
        logger.debug(f"Could not find created_by with any selector")

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

    for idx, selector in enumerate(update_desc_selectors):
        try:
            elem = item.find_element(By.CSS_SELECTOR, selector)
            update_desc = elem.text.strip()

            if update_desc:
                logger.debug(f"Found update_description '{update_desc}' using selector {idx + 1}/{len(update_desc_selectors)}")
                return update_desc
        except NoSuchElementException:
            logger.debug(f"Update description selector {idx + 1}/{len(update_desc_selectors)} not found")
            continue
        except Exception as e:
            logger.debug(f"Update description selector {idx + 1}/{len(update_desc_selectors)} failed: {e}")
            continue

    if update_desc_selectors:
        logger.debug(f"Could not find update_description with any selector")

    return ""
