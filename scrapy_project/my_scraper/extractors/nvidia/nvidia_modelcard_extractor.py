"""
NVIDIA model card extraction functions
"""

import logging
import time
import random
import re
from typing import Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def clean_model_card_html(html_content: str) -> str:
    """
    Convert model card HTML to clean plain text

    Args:
        html_content: Raw HTML string from model card page

    Returns:
        Clean plain text string without HTML tags
    """
    if not html_content:
        return ''

    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove unwanted elements that don't contribute to content
        # 1. Remove all SVG elements (icons, graphics)
        for svg in soup.find_all('svg'):
            svg.decompose()

        # 2. Remove all button elements
        for button in soup.find_all('button'):
            button.decompose()

        # 3. Remove script and style tags
        for script in soup.find_all(['script', 'style']):
            script.decompose()

        # Get text content with some structure preservation
        text_lines = []

        # Process each element to preserve some structure
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'a', 'strong', 'em']):
            text = element.get_text(strip=True)
            if not text:
                continue

            # Add formatting for headings
            if element.name in ['h1', 'h2']:
                text_lines.append('\n' + text + '\n' + '=' * len(text))
            elif element.name in ['h3', 'h4']:
                text_lines.append('\n' + text + '\n' + '-' * len(text))
            elif element.name == 'li':
                text_lines.append('• ' + text)
            elif element.name == 'a' and element.get('href'):
                # Include link URL in parentheses
                href = element.get('href')
                if href and href != text:
                    text_lines.append(f'{text} ({href})')
                else:
                    text_lines.append(text)
            else:
                text_lines.append(text)

        # Join lines and clean up
        cleaned_text = '\n'.join(text_lines)

        # Remove excessive whitespace
        cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
        cleaned_text = re.sub(r'  +', ' ', cleaned_text)

        # Remove duplicate lines that may have been created
        lines = cleaned_text.split('\n')
        unique_lines = []
        prev_line = None
        for line in lines:
            if line != prev_line or line.strip() in ['', '=' * len(line.strip()), '-' * len(line.strip())]:
                unique_lines.append(line)
                prev_line = line

        cleaned_text = '\n'.join(unique_lines).strip()

        return cleaned_text

    except Exception as e:
        logger.warning(f'Error cleaning HTML: {e}')
        # Fallback: just get text without formatting
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text(separator='\n', strip=True)
        except:
            return html_content


def extract_modelcard(driver: webdriver.Chrome, selectors: Dict, model_name: str) -> str:
    """
    Extract NVIDIA model card content from the current page

    Args:
        driver: Selenium driver instance (should already be on the modelcard page)
        selectors: Selectors configuration dictionary
        model_name: Model name for logging

    Returns:
        Extracted and cleaned model card text, or empty string if not found
    """
    if not driver:
        logger.warning(f'No driver provided for {model_name}, cannot extract model card')
        return ''

    try:
        # Add extra wait time for content to fully load with randomization
        # Reduced wait time for better throughput
        wait_time = random.uniform(1.0, 1.5)
        logger.debug(f"Waiting {wait_time:.2f}s for model card to load")
        time.sleep(wait_time)  # Give more time for heavy content to load

        # Get model card content selector
        model_card_selector = selectors.get('model_card_content', 'div.prose.prose-markdown-compat')

        # Alternative selectors to try
        alternative_selectors = [
            'div.prose.prose-markdown-compat.max-w-[85ch]',  # Full prose format
            'div.prose',  # Generic prose
            'div.prose-markdown-compat',  # Just markdown-compat
        ]

        model_card_element = None
        used_selector = None

        # Try to find the model card content div with multiple selectors
        try:
            # First try the primary selector (reduced timeout from 10 to 5)
            try:
                model_card_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, model_card_selector))
                )
                used_selector = model_card_selector
                logger.debug(f"Found model card with primary selector for {model_name}")
            except:
                # Try alternative selectors
                for alt_selector in alternative_selectors:
                    try:
                        model_card_element = driver.find_element(By.CSS_SELECTOR, alt_selector)
                        used_selector = alt_selector
                        logger.debug(f"Found model card with alternative selector '{alt_selector}' for {model_name}")
                        break
                    except:
                        continue

            if model_card_element:
                # Add a small delay to ensure content is fully rendered (reduced from 0.5)
                time.sleep(0.2)

                # Extract the HTML content or text content
                # Using outerHTML to preserve the full structure including div
                model_card_html = None

                for attempt in range(3):
                    try:
                        model_card_html = model_card_element.get_attribute('outerHTML')
                        break
                    except StaleElementReferenceException:
                        logger.debug(f'Stale element getting model card HTML, retrying (attempt {attempt + 1})')
                        time.sleep(0.5)
                        # Re-find the element
                        try:
                            if used_selector:
                                model_card_element = driver.find_element(By.CSS_SELECTOR, used_selector)
                        except:
                            break

                if model_card_html and model_card_html.strip():
                    # Clean the HTML to remove UI elements
                    cleaned_html = clean_model_card_html(model_card_html)
                    logger.info(f"✓ Extracted model card for {model_name} ({len(model_card_html)} chars -> {len(cleaned_html)} chars after cleaning)")
                    return cleaned_html
                else:
                    # Fallback to text content if outerHTML is empty
                    model_card_text = None
                    for attempt in range(3):
                        try:
                            model_card_text = model_card_element.text.strip()
                            break
                        except StaleElementReferenceException:
                            logger.debug(f'Stale element getting model card text, retrying (attempt {attempt + 1})')
                            time.sleep(0.5)
                            try:
                                if used_selector:
                                    model_card_element = driver.find_element(By.CSS_SELECTOR, used_selector)
                            except:
                                break

                    if model_card_text:
                        logger.info(f"✓ Extracted model card text for {model_name} ({len(model_card_text)} chars)")
                        return model_card_text
                    else:
                        logger.warning(f"Model card element found but empty for {model_name}")
                        return ''
            else:
                logger.warning(f'Could not find model card element with any selector for {model_name}')
                return ''

        except Exception as e:
            logger.warning(f'Could not find model card element for {model_name}: {e}')
            return ''

    except Exception as e:
        logger.error(f'Error extracting model card for {model_name}: {e}')
        import traceback
        traceback.print_exc()
        return ''
