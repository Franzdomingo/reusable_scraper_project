"""
HTML to Markdown conversion utilities
Provides functions to convert HTML content to Markdown with inline links
"""

import logging
from typing import Union
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from lxml import html as lxml_html
from lxml.etree import _Element

logger = logging.getLogger(__name__)


def convert_html_to_markdown(element: Union[WebElement, _Element, str], driver: webdriver.Chrome = None) -> str:
    """
    Convert HTML element content to text with inline Markdown links

    Supports multiple input types:
    - Selenium WebElement: Extracts innerHTML and converts to Markdown
    - lxml Element: Converts lxml element tree to Markdown
    - str: Parses HTML string and converts to Markdown

    Args:
        element: The element to convert (WebElement, lxml Element, or HTML string)
        driver: Selenium driver instance (optional, only needed for WebElement type)

    Returns:
        Text with inline Markdown-formatted links [text](url)

    Examples:
        >>> # Selenium WebElement
        >>> markdown_text = convert_html_to_markdown(web_element, driver)

        >>> # lxml Element
        >>> markdown_text = convert_html_to_markdown(lxml_element)

        >>> # HTML string
        >>> markdown_text = convert_html_to_markdown('<p>Check our <a href="https://example.com">blog</a></p>')
    """
    try:
        # Handle different input types
        if isinstance(element, WebElement):
            # Selenium WebElement - extract innerHTML
            return _convert_webelement_to_markdown(element, driver)
        elif isinstance(element, _Element):
            # lxml Element - process directly
            return _convert_lxml_to_markdown(element)
        elif isinstance(element, str):
            # HTML string - parse and convert
            return _convert_html_string_to_markdown(element)
        else:
            logger.warning(f"Unsupported element type: {type(element)}")
            return str(element)

    except Exception as e:
        logger.debug(f"Failed to convert element to markdown: {e}")
        # Fallback to text extraction
        try:
            if isinstance(element, WebElement):
                return element.text
            elif isinstance(element, _Element):
                return element.text_content()
            elif isinstance(element, str):
                # Try to extract text from HTML string
                parsed = lxml_html.fragment_fromstring(element, create_parent='div')
                return parsed.text_content()
            else:
                return str(element)
        except:
            return str(element)


def _convert_webelement_to_markdown(element: WebElement, driver: webdriver.Chrome) -> str:
    """
    Convert Selenium WebElement to Markdown text

    Args:
        element: Selenium WebElement
        driver: Selenium driver instance

    Returns:
        Markdown-formatted text
    """
    # Get the innerHTML to preserve link structure
    inner_html = element.get_attribute('innerHTML')
    if not inner_html:
        return element.text or ""

    # Parse and convert
    return _convert_html_string_to_markdown(inner_html)


def _convert_html_string_to_markdown(html_string: str) -> str:
    """
    Convert HTML string to Markdown text

    Args:
        html_string: Raw HTML string

    Returns:
        Markdown-formatted text
    """
    # Parse the HTML string
    fragment = lxml_html.fragment_fromstring(html_string, create_parent='div')
    return _convert_lxml_to_markdown(fragment)


def _convert_lxml_to_markdown(elem: _Element) -> str:
    """
    Convert lxml element to Markdown text with inline links

    Recursively processes the element tree and converts:
    - <a> tags to [text](url) format
    - <br> tags to newlines
    - Preserves text content and structure

    Args:
        elem: lxml Element to convert

    Returns:
        Markdown-formatted text string
    """
    parts = []

    # Add text before first child
    if elem.text:
        parts.append(elem.text)

    # Process children recursively
    for child in elem:
        if child.tag == 'a':
            # Convert anchor to markdown link
            link_text = child.text_content().strip()
            href = child.get('href', '')

            if link_text and href:
                # Full markdown link format
                parts.append(f'[{link_text}]({href})')
            elif link_text:
                # Link text without href (shouldn't happen, but fallback)
                parts.append(link_text)
            elif href:
                # Href without text (use URL as text)
                parts.append(f'[{href}]({href})')

        elif child.tag in ['br']:
            # Handle line breaks
            parts.append('\n')

        else:
            # Recursively process other elements
            parts.append(_convert_lxml_to_markdown(child))

        # Add text after child (tail text)
        if child.tail:
            parts.append(child.tail)

    return ''.join(parts).strip()


def extract_links_from_element(element: Union[WebElement, _Element, str]) -> list:
    """
    Extract all href links from an HTML element

    Args:
        element: The element to extract links from (WebElement, lxml Element, or HTML string)

    Returns:
        List of href URLs found in the element

    Example:
        >>> links = extract_links_from_element(web_element)
        >>> # ['https://example.com/link1', 'https://example.com/link2']
    """
    links = []

    try:
        # Convert to lxml element if needed
        if isinstance(element, WebElement):
            inner_html = element.get_attribute('innerHTML')
            if not inner_html:
                return links
            elem = lxml_html.fragment_fromstring(inner_html, create_parent='div')
        elif isinstance(element, str):
            elem = lxml_html.fragment_fromstring(element, create_parent='div')
        elif isinstance(element, _Element):
            elem = element
        else:
            return links

        # Extract all anchor hrefs
        for anchor in elem.xpath('.//a[@href]'):
            href = anchor.get('href', '').strip()
            if href:
                links.append(href)

    except Exception as e:
        logger.debug(f"Failed to extract links from element: {e}")

    return links
