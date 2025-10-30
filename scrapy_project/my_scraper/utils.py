"""
Utility functions for web scraping
Contains text cleaning, HTML parsing, and common helper functions
"""

import re
import logging
from lxml import html
from typing import Optional, List
from my_scraper.selectors.site_selectors import GeneralSelectors


def html_to_text(html_snippet: str) -> str:
    """
    Convert an HTML snippet (outerHTML) into cleaned plain text.

    Uses lxml to parse and extract text_content(), then collapses whitespace.
    
    Args:
        html_snippet: HTML string to convert
        
    Returns:
        Cleaned plain text
    """
    if not html_snippet:
        return ''

    try:
        node = html.fromstring(html_snippet)
        text = node.text_content() or ''
    except Exception:
        # Fallback: remove tags with a simple regex
        text = re.sub(r'<[^>]+>', ' ', html_snippet)

    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def is_numeric_value(text: str) -> bool:
    """
    Check if text represents a numeric value (including K/M suffixes)

    Args:
        text: Text to check

    Returns:
        True if text appears to be a numeric value
    """
    # Reject strings that contain non-numeric words or special characters (except K/M/B, commas, periods)
    # This filters out text like "QWENLM · CREATED ON 2025.09.10"
    cleaned = text.replace(',', '').replace('.', '').upper()
    # Remove valid suffixes
    for suffix in ['K', 'M', 'B']:
        if cleaned.endswith(suffix):
            cleaned = cleaned[:-1]

    # After removing suffixes, periods, and commas, should only have digits
    # Allow single space for numbers like "1 234" but reject multiple words
    if not cleaned.replace(' ', '').isdigit():
        return False

    # If there are multiple spaces or other text patterns, reject
    if text.count(' ') > 2 or '·' in text or any(c.isalpha() for c in text.replace('K', '').replace('M', '').replace('B', '').replace('k', '').replace('m', '').replace('b', '')):
        return False

    # Simple digit check
    if text.isdigit():
        return True

    # Check against numeric patterns from config
    for pattern in GeneralSelectors.NUMERIC_PATTERNS:
        if re.match(pattern, text):
            return True

    # Fallback: check for common download indicators
    return bool(re.match(r'^\d+[KkMmBb]?$', text) or
               re.match(r'^\d+[\.,]\d+[KkMmBb]?$', text))


def clean_text(text: str) -> str:
    """
    Clean text by removing excessive whitespace while preserving newlines

    Args:
        text: Text to clean

    Returns:
        Cleaned text with preserved line breaks
    """
    if not text:
        return ''

    # Collapse multiple spaces and tabs (but preserve newlines)
    text = re.sub(r'[ \t]+', ' ', text)

    # Collapse excessive newlines (3+ consecutive newlines become 2)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def extract_model_name_from_url(url: str) -> str:
    """
    Extract a readable model name from a URL
    
    Args:
        url: Model URL
        
    Returns:
        Extracted model name
    """
    parts = url.strip('/').split('/')
    if len(parts) >= 2:
        return parts[-1].replace('-', ' ').title()
    return ''


def setup_logging(level: int = logging.INFO) -> None:
    """
    Setup logging configuration
    
    Args:
        level: Logging level (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )


def safe_extract(elements: List, index: int = 0, default: str = '') -> str:
    """
    Safely extract text from a list of elements
    
    Args:
        elements: List of elements
        index: Index to extract from (default: 0)
        default: Default value if extraction fails
        
    Returns:
        Extracted text or default value
    """
    try:
        if elements and len(elements) > index:
            return elements[index].strip() if hasattr(elements[index], 'strip') else str(elements[index])
    except Exception:
        pass
    return default


def build_full_url(base_url: str, href: str) -> str:
    """
    Build a full URL from a base URL and href

    Args:
        base_url: Base URL (e.g., 'https://www.kaggle.com')
        href: Relative or absolute URL

    Returns:
        Full URL
    """
    if href.startswith('http'):
        return href

    if href.startswith('/'):
        return f"{base_url.rstrip('/')}{href}"

    return f"{base_url.rstrip('/')}/{href.lstrip('/')}"


def is_xpath_selector(selector: str) -> bool:
    """
    Determine if a selector is XPath (as opposed to CSS)

    XPath selectors start with:
    - // (absolute path)
    - .// (relative path)
    - / (document root)

    CSS selectors start with:
    - . (class)
    - # (ID)
    - tag name
    - [ (attribute selector)

    Args:
        selector: The selector string to check

    Returns:
        True if selector is XPath, False if CSS
    """
    if not selector:
        return False

    # XPath always starts with // or / or .//
    # Also check for XPath-specific patterns
    return (selector.startswith('//') or
            selector.startswith('/') or
            selector.startswith('.//') or
            selector.startswith('(') or  # XPath expressions can start with parentheses
            '::' in selector or  # XPath axes like 'ancestor::div'
            '@' in selector[:20])  # XPath attributes like '//div[@class]'


def is_css_selector(selector: str) -> bool:
    """
    Determine if a selector is CSS (as opposed to XPath)

    This is the inverse of is_xpath_selector() for clarity

    Args:
        selector: The selector string to check

    Returns:
        True if selector is CSS, False if XPath
    """
    return not is_xpath_selector(selector)


def parse_formatted_number(value: str) -> int:
    """
    Parse a formatted number string into an integer.

    Handles formats like:
    - "755" -> 755
    - "50.3k" -> 50300
    - "1.2K" -> 1200
    - "2.5M" -> 2500000
    - "1.8B" -> 1800000000

    Args:
        value: Formatted number string

    Returns:
        Parsed integer value, or 0 if parsing fails
    """
    if not value:
        return 0

    # Remove whitespace and commas
    value = value.strip().replace(',', '')

    # Check for suffix multipliers
    multipliers = {
        'k': 1_000,
        'K': 1_000,
        'm': 1_000_000,
        'M': 1_000_000,
        'b': 1_000_000_000,
        'B': 1_000_000_000,
    }

    multiplier = 1

    # Check if the last character is a multiplier
    if value and value[-1] in multipliers:
        multiplier = multipliers[value[-1]]
        value = value[:-1]

    try:
        # Parse the numeric part (can be float like "50.3")
        numeric_value = float(value)
        # Multiply and convert to integer
        result = int(numeric_value * multiplier)
        return result
    except (ValueError, AttributeError):
        logging.warning(f"Failed to parse formatted number: {value}")
        return 0
