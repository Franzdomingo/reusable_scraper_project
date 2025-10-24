"""
Kaggle Links extraction functions
Extracts model links from Kaggle listing pages
"""

import logging
from typing import Dict, Set, Tuple, Optional
from lxml import html as lxml_html
from my_scraper.utils import extract_model_name_from_url, build_full_url
from my_scraper.extractors.retry_utils import retry_operation, retry_xpath

logger = logging.getLogger(__name__)


def extract_model_links(
    tree: lxml_html.HtmlElement,
    selectors: Dict,
    seen_urls: Set[str],
    page_num: int,
    base_url: str = 'https://www.kaggle.com'
) -> Tuple[list, int, Optional[str]]:
    """
    Extract model links from a Kaggle listing page

    Args:
        tree: lxml tree object
        selectors: Selectors configuration dictionary
        seen_urls: Set of already seen URLs to avoid duplicates
        page_num: Current page number for logging
        base_url: Base URL for building full URLs

    Returns:
        Tuple of (list of items, new_models_count, first_model_url)
        where items are dicts with 'name' and 'kaggle_url'
    """
    items = []
    new_models_count = 0
    first_model_url = None
    duplicate_count = 0

    # Extract model links using configured selector with retry
    model_links_xpath = selectors.get('model_links_xpath')
    list_items = retry_xpath(tree, model_links_xpath, max_retries=3, delay=0.5)

    if not list_items:
        logger.error(f'Page {page_num}: Failed to extract model links after retries')
        return items, new_models_count, first_model_url

    logger.info(f'Page {page_num}: Found {len(list_items)} model links')

    # Extract data from each link
    for link in list_items:
        # Extract href with retry
        href = retry_operation(link.get, 3, 0.5, 'link.get(href)', 'href', '')

        if not href or href == '/models':
            continue

        # Build full URL
        full_url = build_full_url(base_url, href)

        # Track first model URL on this page for content change detection
        if first_model_url is None:
            first_model_url = full_url

        # Skip if already seen
        if full_url in seen_urls:
            duplicate_count += 1
            logger.debug(f'Page {page_num}: Duplicate URL: {full_url}')
            continue

        seen_urls.add(full_url)
        new_models_count += 1

        # Extract model name with retry
        model_name_xpath = selectors.get('model_name_xpath')
        name_elements = retry_xpath(link, model_name_xpath, max_retries=3, delay=0.5)

        if name_elements:
            model_name = name_elements[0].strip()
        else:
            # Fallback: extract from link text or URL with retry
            model_name = retry_operation(link.text_content, 3, 0.5, 'link.text_content()')
            if model_name:
                model_name = model_name.strip()
            if not model_name:
                model_name = extract_model_name_from_url(href)

        if model_name:
            # Create item dict
            item = {
                'name': model_name,
                'kaggle_url': full_url
            }
            items.append(item)

    # Log results
    logger.info(f'Page {page_num}: Scraped {new_models_count} new models (total seen: {len(seen_urls)})')

    return items, new_models_count, first_model_url
