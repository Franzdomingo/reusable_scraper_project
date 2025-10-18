"""
NVIDIA Models Spider
Scrapes model metadata from NVIDIA Build (https://build.nvidia.com/models)
"""

import scrapy
import time
import random
from datetime import datetime
from typing import Dict, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from lxml import html as lxml_html

from my_scraper.items import NvidiaModelItem
from my_scraper.selectors.site_selectors import get_selectors_for_site
from my_scraper.extractors.selenium_utils import parse_tree_from_response
from my_scraper.extractors.nvidia_tags_extractor import extract_nvidia_tags
from my_scraper.extractors.nvidia_modelcard_extractor import extract_modelcard
from my_scraper.extractors.nvidia_url_extractor import (
    extract_model_name_from_card,
    extract_model_url_from_card,
    extract_parent_container,
)


class NvidiaModelsSpider(scrapy.Spider):
    """
    Spider to scrape NVIDIA model metadata from build.nvidia.com

    Extracts:
    - Model name
    - NVIDIA URL (relative path)
    - Tags (both visible and from "+N" popover)
    """

    name = 'nvidia_models'
    allowed_domains = ['build.nvidia.com']
    start_urls = ['https://build.nvidia.com/models']

    def __init__(self, *args, skip_modelcard=False, **kwargs):
        """
        Initialize spider

        Args:
            skip_modelcard: If True, skip model card extraction for faster scraping
        """
        super().__init__(*args, **kwargs)
        self.selectors = get_selectors_for_site('nvidia')
        self.model_counter = 0
        self.processed_urls = set()  # Track processed URLs to avoid duplicates
        self.processed_names = set()  # Track processed names to avoid duplicates
        self.skip_modelcard = skip_modelcard

        if self.skip_modelcard:
            self.logger.info('Model card extraction is DISABLED - will scrape faster')

    def start_requests(self):
        """Generate initial request to NVIDIA models page"""
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    'selenium': True,
                    'selenium_wait': 5,  # Wait for dynamic content to load
                    'selenium_wait_selector': 'a[data-linkbox-overlay="true"]',
                }
            )

    def parse(self, response):
        """
        Parse NVIDIA models page and extract model information

        Args:
            response: Scrapy response object

        Yields:
            NvidiaModelItem with extracted metadata
        """
        # Use the driver from the middleware (already loaded with the page)
        driver = response.meta.get('driver')

        if not driver:
            self.logger.error('No driver available for NVIDIA models page')
            return

        try:
            # Parse tree from the response
            tree = parse_tree_from_response(response)

            # Get model cards selector
            model_cards_selector = self.selectors.get('model_cards')

            if not model_cards_selector:
                self.logger.error('No model cards selector configured')
                return

            # Find all model cards on the page
            model_cards = driver.find_elements(By.CSS_SELECTOR, model_cards_selector)

            if not model_cards:
                self.logger.warning('No model cards found on page')
                return

            total_cards = len(model_cards)
            self.logger.info(f'Found {total_cards} model cards on page')

            # Process each model card
            processed_in_iteration = 0

            # Scroll to bottom to ensure all lazy-loaded cards are visible
            self.logger.info('Scrolling page to load all model cards...')
            last_height = driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scroll_attempts = 10

            while scroll_attempts < max_scroll_attempts:
                # Scroll down to bottom
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)  # Wait for page to load

                # Calculate new scroll height and compare with last scroll height
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    # No more content loaded, break
                    break

                last_height = new_height
                scroll_attempts += 1

                # Re-count cards after scrolling
                current_cards = driver.find_elements(By.CSS_SELECTOR, model_cards_selector)
                self.logger.info(f'Scroll attempt {scroll_attempts}: Found {len(current_cards)} cards')

            # Get final card count after scrolling
            model_cards = driver.find_elements(By.CSS_SELECTOR, model_cards_selector)
            final_card_count = len(model_cards)
            self.logger.info(f'After scrolling: Found {final_card_count} model cards (initially found {total_cards})')

            # STEP 1: Extract ALL model data from the main page FIRST
            # This prevents the driver from navigating away while we're still processing
            all_items = []

            self.logger.info('STEP 1: Extracting all model data from main page...')
            for idx in range(final_card_count):
                try:
                    # Re-find all cards in each iteration to avoid stale references
                    model_cards = driver.find_elements(By.CSS_SELECTOR, model_cards_selector)

                    # Check if current card index is still valid
                    if idx >= len(model_cards):
                        self.logger.warning(f'Card at index {idx} no longer available (have {len(model_cards)} cards)')
                        continue

                    card = model_cards[idx]

                    # Extract model name using extractor
                    model_name = extract_model_name_from_card(
                        card, driver, self.selectors, model_cards_selector, idx
                    )

                    if not model_name:
                        continue

                    # Extract model URL using extractor
                    model_url = extract_model_url_from_card(
                        card, driver, self.selectors, model_cards_selector, idx, model_name
                    )

                    if not model_url:
                        continue

                    # Check for duplicates - skip if already processed
                    if model_url in self.processed_urls:
                        self.logger.debug(f'Skipping duplicate URL: {model_url} ({model_name})')
                        continue

                    if model_name in self.processed_names:
                        self.logger.debug(f'Skipping duplicate name: {model_name}')
                        continue

                    # Mark as processed
                    self.processed_urls.add(model_url)
                    self.processed_names.add(model_name)
                    self.model_counter += 1
                    processed_in_iteration += 1

                    self.logger.info(f'Extracting {self.model_counter}/{final_card_count}: {model_name}')

                    # Create item
                    item = NvidiaModelItem()
                    item['name'] = model_name
                    item['nvidia_url'] = model_url

                    # Add timestamp
                    item['scraped_on'] = datetime.now().isoformat()

                    # Extract tags for this model
                    # Note: We need to find the parent container of the card to locate tags
                    try:
                        # Extract parent container using extractor
                        parent_container = extract_parent_container(
                            card, driver, idx, model_name, model_cards_selector
                        )

                        if parent_container:
                            # Scroll the container into view to ensure tags are visible
                            driver.execute_script("arguments[0].scrollIntoView(true);", parent_container)
                            time.sleep(random.uniform(0.2, 0.4))  # Reduced delay for faster extraction

                            # Extract tags for this specific model, passing the scoped container
                            item['tags'] = extract_nvidia_tags(parent_container, driver, self.selectors, model_name)
                        else:
                            self.logger.warning(f'Could not find parent container for {model_name}')
                            item['tags'] = []

                    except Exception as e:
                        self.logger.warning(f'Error extracting tags for {model_name}: {e}')
                        item['tags'] = []

                    # Store item for later processing
                    all_items.append(item)

                except Exception as e:
                    self.logger.error(f'Error processing model card {idx + 1}: {e}')
                    import traceback
                    traceback.print_exc()
                    continue

            self.logger.info(f'STEP 1 COMPLETE: Extracted {len(all_items)} models from main page')

            # STEP 2: Now yield all items (with or without modelcard requests)
            self.logger.info('STEP 2: Yielding items and requesting modelcards...')
            for item in all_items:
                model_name = item.get('name')
                model_url = item.get('nvidia_url')
                tags_count = len(item.get('tags', [])) if item.get('tags') else 0

                # Check if we should fetch model card
                if self.skip_modelcard:
                    # Yield item immediately without model card
                    item['model_card'] = ''
                    self.logger.info(f"DONE {model_name} - URL: {model_url} - Tags: {tags_count} - ModelCard: Skipped")
                    yield item
                else:
                    # Make request to modelcard page to extract model card content
                    modelcard_url = f"{model_url}/modelcard"
                    self.logger.debug(f"Requesting modelcard: {modelcard_url}")

                    yield scrapy.Request(
                        url=modelcard_url,
                        callback=self.parse_modelcard,
                        errback=self.handle_modelcard_error,
                        meta={
                            'selenium': True,
                            'selenium_wait': 5,
                            'selenium_wait_selector': 'div.prose',
                            'item': item,  # Pass the fully filled item (except model_card)
                        },
                        dont_filter=True
                    )

            self.logger.info(f'Successfully extracted and queued {len(all_items)} models for processing')

        except Exception as e:
            self.logger.error(f'Error parsing NVIDIA models page: {e}')
            import traceback
            traceback.print_exc()

    def handle_modelcard_error(self, failure):
        """
        Handle errors when requesting model card page

        Args:
            failure: Twisted Failure object

        Yields:
            NvidiaModelItem with empty model_card field
        """
        # Get the item from the request meta
        item = failure.request.meta.get('item')

        if item:
            model_name = item.get('name', 'Unknown')
            model_url = item.get('nvidia_url', 'Unknown')

            # Log the error but continue with the item
            self.logger.warning(f'Failed to fetch modelcard for {model_name}: {failure.value}')

            # Set model card to empty string
            item['model_card'] = ''

            # Log final summary
            tags_count = len(item.get('tags', [])) if item.get('tags') else 0
            self.logger.info(f"DONE {model_name} - URL: {model_url} - Tags: {tags_count} - ModelCard: Error/Not Found")

            # Yield the item anyway so it's not lost
            yield item
        else:
            self.logger.error(f'No item found in failed request: {failure.request.url}')

    def parse_modelcard(self, response):
        """
        Parse NVIDIA model card page and extract model card content

        Args:
            response: Scrapy response object from /modelcard page

        Yields:
            Complete NvidiaModelItem with model card content
        """
        # Get the partially filled item from meta
        item = response.meta.get('item')

        if not item:
            self.logger.error('No item found in meta for modelcard page')
            return

        model_name = item.get('name', 'Unknown')
        model_url = item.get('nvidia_url', 'Unknown')

        # Use the driver from the middleware
        driver = response.meta.get('driver')

        if not driver:
            self.logger.warning(f'No driver available for modelcard page: {model_name}')
            # Yield item without model card if driver unavailable
            item['model_card'] = ''
            yield item
            return

        try:
            # Extract model card using extractor
            item['model_card'] = extract_modelcard(driver, self.selectors, model_name)

            # Log final summary
            tags_count = len(item.get('tags', [])) if item.get('tags') else 0
            has_model_card = 'Yes' if item.get('model_card') else 'No'
            self.logger.info(f"DONE {model_name} - URL: {model_url} - Tags: {tags_count} - ModelCard: {has_model_card}")

            yield item

        except Exception as e:
            self.logger.error(f'Error parsing modelcard for {model_name}: {e}')
            import traceback
            traceback.print_exc()
            # Yield item without model card in case of error
            item['model_card'] = ''
            yield item
