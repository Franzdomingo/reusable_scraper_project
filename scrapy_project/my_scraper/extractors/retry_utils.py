"""
Retry utilities for robust selector and field extraction operations
Provides retry mechanisms with configurable max attempts and delays
"""

import logging
import time
import re
from typing import Callable, Any

logger = logging.getLogger(__name__)

# ANSI color codes for terminal output
class Colors:
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'


def _clean_exception_message(exception: Exception) -> str:
    """
    Clean exception message by removing verbose Chrome stack traces

    Args:
        exception: Exception object

    Returns:
        Cleaned exception message without stack traces
    """
    message = str(exception)

    # Remove Stacktrace section and everything after it
    if 'Stacktrace:' in message:
        message = message.split('Stacktrace:')[0].strip()

    # Remove any remaining Chrome internal stack traces
    message = re.sub(r'\n\s*GetHandleVerifier.*', '', message)
    message = re.sub(r'\n\s*\(No symbol\).*', '', message)
    message = re.sub(r'\n\s*BaseThreadInitThunk.*', '', message)
    message = re.sub(r'\n\s*RtlUserThreadStart.*', '', message)

    return message.strip()

# Import settings for default retry configuration
try:
    from my_scraper.settings import RETRY_MAX_ATTEMPTS, RETRY_DELAY
    DEFAULT_MAX_RETRIES = RETRY_MAX_ATTEMPTS
    DEFAULT_DELAY = RETRY_DELAY
except ImportError:
    try:
        # Try relative import for when module is loaded from within extractors
        from ..settings import RETRY_MAX_ATTEMPTS, RETRY_DELAY
        DEFAULT_MAX_RETRIES = RETRY_MAX_ATTEMPTS
        DEFAULT_DELAY = RETRY_DELAY
    except ImportError:
        # Fallback if settings not available
        DEFAULT_MAX_RETRIES = 3
        DEFAULT_DELAY = 0.5


def retry_operation(func: Callable, max_retries: int = None, delay: float = None, operation_name: str = None, *args, **kwargs) -> Any:
    """
    Retry an operation up to max_retries times on failure

    Args:
        func: Function to execute
        max_retries: Maximum number of retry attempts (default: from settings.RETRY_MAX_ATTEMPTS)
        delay: Delay in seconds between retries (default: from settings.RETRY_DELAY)
        operation_name: Optional name for logging purposes
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func

    Returns:
        Result of the function call, or None if all retries fail
    """
    # Use settings defaults if not specified
    if max_retries is None:
        max_retries = DEFAULT_MAX_RETRIES
    if delay is None:
        delay = DEFAULT_DELAY

    last_error = None
    op_name = operation_name or getattr(func, '__name__', str(func))

    for attempt in range(max_retries):
        try:
            result = func(*args, **kwargs)
            if result is not None or attempt == 0:  # Accept result on first try even if None
                if attempt > 0:
                    logger.info(f'{op_name}: Retry succeeded on attempt {attempt + 1}')
                return result
        except Exception as e:
            last_error = e
            clean_message = _clean_exception_message(e)
            logger.warning(f'{Colors.RED}{op_name}: Attempt {attempt + 1}/{max_retries} failed: {clean_message}{Colors.RESET}')

        if attempt < max_retries - 1:
            time.sleep(delay)

    clean_message = _clean_exception_message(last_error)
    logger.error(f'{Colors.RED}{op_name}: All {max_retries} attempts failed. Last error: {clean_message}{Colors.RESET}')
    return None


def retry_selenium_find(driver, by, selector, max_retries: int = None, delay: float = None, find_multiple: bool = False) -> Any:
    """
    Retry a Selenium find_element(s) operation

    Args:
        driver: Selenium WebDriver instance
        by: Selenium By locator strategy
        selector: Selector string
        max_retries: Maximum number of retry attempts (default: from settings.RETRY_MAX_ATTEMPTS)
        delay: Delay in seconds between retries (default: from settings.RETRY_DELAY)
        find_multiple: If True, use find_elements instead of find_element

    Returns:
        Element(s) found, or None/empty list if all retries fail
    """
    # Use settings defaults if not specified
    if max_retries is None:
        max_retries = DEFAULT_MAX_RETRIES
    if delay is None:
        delay = DEFAULT_DELAY

    func = driver.find_elements if find_multiple else driver.find_element
    operation_name = f'find_elements({by}, {selector})' if find_multiple else f'find_element({by}, {selector})'

    last_error = None

    for attempt in range(max_retries):
        try:
            result = func(by, selector)
            if result or attempt == 0:  # Accept result on first try even if empty
                if attempt > 0:
                    logger.info(f'{operation_name}: Retry succeeded on attempt {attempt + 1}')
                return result
        except Exception as e:
            last_error = e
            clean_message = _clean_exception_message(e)
            logger.warning(f'{Colors.RED}{operation_name}: Attempt {attempt + 1}/{max_retries} failed: {clean_message}{Colors.RESET}')

        if attempt < max_retries - 1:
            time.sleep(delay)

    clean_message = _clean_exception_message(last_error)
    logger.error(f'{Colors.RED}{operation_name}: All {max_retries} attempts failed. Last error: {clean_message}{Colors.RESET}')
    return [] if find_multiple else None


def retry_xpath(tree, xpath: str, max_retries: int = None, delay: float = None) -> list:
    """
    Retry an XPath query operation

    Args:
        tree: lxml tree object
        xpath: XPath selector string
        max_retries: Maximum number of retry attempts (default: from settings.RETRY_MAX_ATTEMPTS)
        delay: Delay in seconds between retries (default: from settings.RETRY_DELAY)

    Returns:
        List of elements found, or empty list if all retries fail
    """
    # Use settings defaults if not specified
    if max_retries is None:
        max_retries = DEFAULT_MAX_RETRIES
    if delay is None:
        delay = DEFAULT_DELAY

    return retry_operation(tree.xpath, max_retries, delay, f'xpath({xpath})', xpath) or []


def retry_click(element, driver=None, max_retries: int = None, delay: float = None) -> bool:
    """
    Retry clicking an element, with JavaScript fallback

    Args:
        element: Selenium WebElement to click
        driver: Optional WebDriver instance for JavaScript fallback
        max_retries: Maximum number of retry attempts (default: from settings.RETRY_MAX_ATTEMPTS)
        delay: Delay in seconds between retries (default: from settings.RETRY_DELAY)

    Returns:
        True if click succeeded, False otherwise
    """
    # Use settings defaults if not specified
    if max_retries is None:
        max_retries = DEFAULT_MAX_RETRIES
    if delay is None:
        delay = DEFAULT_DELAY

    last_error = None

    for attempt in range(max_retries):
        try:
            element.click()
            if attempt > 0:
                logger.info(f'Click retry succeeded on attempt {attempt + 1}')
            return True
        except Exception as e:
            last_error = e
            clean_message = _clean_exception_message(e)
            logger.warning(f'{Colors.RED}Click attempt {attempt + 1}/{max_retries} failed: {clean_message}{Colors.RESET}')

            # Try JavaScript click as fallback if driver is provided
            if driver and attempt == max_retries - 1:
                try:
                    logger.info('Attempting JavaScript click as final fallback')
                    driver.execute_script("arguments[0].click();", element)
                    logger.info('JavaScript click succeeded')
                    return True
                except Exception as js_error:
                    clean_js_message = _clean_exception_message(js_error)
                    logger.error(f'{Colors.RED}JavaScript click also failed: {clean_js_message}{Colors.RESET}')

        if attempt < max_retries - 1:
            time.sleep(delay)

    clean_message = _clean_exception_message(last_error)
    logger.error(f'{Colors.RED}Click: All {max_retries} attempts failed. Last error: {clean_message}{Colors.RESET}')
    return False
