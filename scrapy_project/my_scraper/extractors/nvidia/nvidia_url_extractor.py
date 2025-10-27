"""
NVIDIA model URL and name extraction functions
"""

import logging
import time
from typing import Dict, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException

logger = logging.getLogger(__name__)


def safe_get_element_attribute(element, driver: webdriver.Chrome, card_selector: str,
                               attribute: str, max_retries: int = 3) -> Optional[str]:
    """
    Safely get attribute from a potentially stale element with retry logic

    Args:
        element: WebElement that might be stale
        driver: Selenium WebDriver instance
        card_selector: CSS selector to re-find the element
        attribute: Attribute name to extract
        max_retries: Maximum number of retries

    Returns:
        Attribute value or None if not found
    """
    for attempt in range(max_retries):
        try:
            return element.get_attribute(attribute)
        except StaleElementReferenceException:
            if attempt < max_retries - 1:
                logger.debug(f'Stale element on attempt {attempt + 1}, re-finding element...')
                time.sleep(0.2)  # Brief pause before retry
                try:
                    # Re-find the element using the selector
                    element = driver.find_element(By.CSS_SELECTOR, card_selector)
                except Exception as e:
                    logger.warning(f'Could not re-find element: {e}')
                    return None
            else:
                logger.warning(f'Element remained stale after {max_retries} attempts')
                raise
        except Exception as e:
            logger.debug(f'Error getting attribute: {e}')
            return None
    return None


def extract_model_name_from_card(card, driver: webdriver.Chrome, selectors: Dict,
                                card_selector: str, idx: int) -> Optional[str]:
    """
    Extract model name from a model card element with retry logic

    Args:
        card: WebElement representing the model card
        driver: Selenium driver instance
        selectors: Selectors configuration dictionary
        card_selector: CSS selector for the card (used for re-finding)
        idx: Index of the card (for re-finding after stale reference)

    Returns:
        Model name string or None if not found
    """
    model_name_attr = selectors.get('model_name_attr', 'title')
    model_name = None

    for attempt in range(3):
        try:
            model_name = card.get_attribute(model_name_attr)
            break
        except StaleElementReferenceException:
            logger.debug(f'Stale element for card {idx + 1}, re-finding (attempt {attempt + 1})')
            time.sleep(0.3)
            try:
                model_cards = driver.find_elements(By.CSS_SELECTOR, card_selector)
                if idx < len(model_cards):
                    card = model_cards[idx]
                else:
                    logger.warning(f'Card index {idx} out of range after re-finding')
                    break
            except Exception as e:
                logger.warning(f'Error re-finding card: {e}')
                break

    if not model_name:
        logger.warning(f'Model card {idx + 1} has no name attribute')

    return model_name


def extract_model_url_from_card(card, driver: webdriver.Chrome, selectors: Dict,
                               card_selector: str, idx: int, model_name: str) -> Optional[str]:
    """
    Extract model URL from a model card element with retry logic

    Args:
        card: WebElement representing the model card
        driver: Selenium driver instance
        selectors: Selectors configuration dictionary
        card_selector: CSS selector for the card (used for re-finding)
        idx: Index of the card (for re-finding after stale reference)
        model_name: Model name for logging

    Returns:
        Full model URL string or None if not found
    """
    model_url_attr = selectors.get('model_url_attr', 'href')
    model_url = None

    for attempt in range(3):
        try:
            model_url = card.get_attribute(model_url_attr)
            break
        except StaleElementReferenceException:
            logger.debug(f'Stale element getting URL for {model_name}, re-finding (attempt {attempt + 1})')
            time.sleep(0.3)
            try:
                model_cards = driver.find_elements(By.CSS_SELECTOR, card_selector)
                if idx < len(model_cards):
                    card = model_cards[idx]
                else:
                    logger.warning(f'Card index {idx} out of range after re-finding')
                    break
            except Exception as e:
                logger.warning(f'Error re-finding card: {e}')
                break

    if not model_url:
        logger.warning(f'Model {model_name} has no URL attribute')
        return None

    # Ensure we have the full URL
    if not model_url.startswith('http'):
        # If it's just a path, prepend the base URL
        model_url = f'https://build.nvidia.com{model_url}'

    return model_url


def extract_parent_container(card, driver: webdriver.Chrome, idx: int,
                            model_name: str, card_selector: str):
    """
    Extract the parent container element for a model card (used for tags extraction)

    Args:
        card: WebElement representing the model card
        driver: Selenium driver instance
        idx: Index of the card (for re-finding after stale reference)
        model_name: Model name for logging
        card_selector: CSS selector for the card (used for re-finding)

    Returns:
        Parent container WebElement or None if not found
    """
    parent_container = None

    # Navigate to parent container that includes both the link and tags
    # The structure is typically: a[data-linkbox-overlay] is nested within several divs
    # that also contain the tags. We need to find the right ancestor.
    for attempt in range(3):
        try:
            parent_container = card.find_element(By.XPATH, './ancestor::div[3]')
            break
        except StaleElementReferenceException:
            logger.debug(f'Stale element finding parent for {model_name}, re-finding (attempt {attempt + 1})')
            time.sleep(0.3)
            try:
                model_cards = driver.find_elements(By.CSS_SELECTOR, card_selector)
                if idx < len(model_cards):
                    card = model_cards[idx]
                else:
                    logger.warning(f'Card index {idx} out of range after re-finding')
                    break
            except Exception as e:
                logger.warning(f'Error re-finding card: {e}')
                break

    if not parent_container:
        logger.warning(f'Could not find parent container for {model_name}')

    return parent_container
