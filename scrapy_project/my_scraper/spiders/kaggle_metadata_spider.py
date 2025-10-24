"""
Kaggle Metadata Spider
Scrapes detailed metadata from Kaggle model pages
"""

import scrapy
import time
import csv
import os
from datetime import datetime
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lxml import html as lxml_html
from my_scraper.items import KaggleMetadataItem, TransformersVariationItem
from my_scraper.utils import html_to_text
from my_scraper.selectors.site_selectors import get_selectors_for_site
from my_scraper.extractors.selenium_utils import parse_tree_from_response, click_element
from my_scraper.extractors.kaggle.description_extractor import extract_description
from my_scraper.extractors.kaggle.downloads_extractor import extract_downloads
from my_scraper.extractors.kaggle.total_views_extractor import extract_total_views
from my_scraper.extractors.kaggle.total_engagements_extractor import extract_total_engagements
from my_scraper.extractors.kaggle.usability_extractor import extract_usability
from my_scraper.extractors.kaggle.tags_extractor import extract_tags
from my_scraper.extractors.kaggle.collaborators_extractor import extract_collaborators
from my_scraper.extractors.kaggle.authors_extractor import extract_authors
from my_scraper.extractors.kaggle.provenance_extractor import extract_provenance
from my_scraper.extractors.kaggle.variations_extractor import extract_variations
from my_scraper.extractors.kaggle.model_card_extractor import extract_model_card
from my_scraper.extractors.retry_utils import retry_selenium_find, retry_click, retry_operation


class KaggleMetadataSpider(scrapy.Spider):
    """
    Spider to scrape Kaggle model metadata
    
    Reads model URLs from a CSV file and extracts:
    - Short description
    - Download count
    - Tags
    - Model card
    - Transformers variations
    """
    
    name = 'kaggle_metadata'
    allowed_domains = ['kaggle.com']

    def __init__(self, input_file=None, *args, **kwargs):
        """
        Initialize spider

        Args:
            input_file: Path to JSON or CSV file with model URLs (default: looks for recent kaggle_links output)
        """
        super().__init__(*args, **kwargs)
        self.selectors = get_selectors_for_site('kaggle')

        # Determine input file path
        if input_file:
            self.input_file = input_file
        else:
            # Look for input file in common locations
            # Prioritize JSON files from kaggle_links spider
            import glob

            self.input_file = None

            # First look for recent JSON files from kaggle_links
            json_patterns = [
                'output/kaggle_links_*.json',
                '../output/kaggle_links_*.json',
            ]

            for pattern in json_patterns:
                matching_files = glob.glob(pattern)
                if matching_files:
                    # Filter out empty files (files with size 0 or just whitespace)
                    non_empty_files = [
                        f for f in matching_files
                        if os.path.getsize(f) > 2  # More than just "[]" or "{}"
                    ]

                    if non_empty_files:
                        # Get the most recent non-empty file
                        self.input_file = max(non_empty_files, key=os.path.getctime)
                        self.logger.info(f'Found recent kaggle_links JSON output: {self.input_file}')
                        break
                    else:
                        self.logger.warning(f'Found {len(matching_files)} files matching {pattern}, but all are empty')

            # Fallback to CSV files if no JSON found
            if not self.input_file:
                csv_paths = [
                    'output/kaggle_output.csv',
                    '../output/kaggle_output.csv',
                    '../../output/kaggle_output.csv',
                ]

                for path in csv_paths:
                    if os.path.exists(path):
                        self.input_file = path
                        self.logger.info(f'Found CSV file: {self.input_file}')
                        break

        if not self.input_file:
            raise ValueError(
                'Input file not found. Please:\n'
                '1. First run: python run.py kaggle_links -a max_pages=10\n'
                '2. Then run: python run.py kaggle_metadata\n'
                'Or provide input_file parameter: -a input_file=path/to/file.json'
            )

        self.logger.info(f'Using input file: {self.input_file}')
        self.model_counter = 0
    
    def start_requests(self):
        """Generate requests from input JSON or CSV file"""
        import json

        # Determine file type by extension
        is_json = self.input_file.endswith('.json')

        if is_json:
            # Read JSON file
            with open(self.input_file, 'r', encoding='utf-8') as jsonfile:
                data = json.load(jsonfile)

                # Handle both list and dict formats
                if isinstance(data, list):
                    items = data
                else:
                    items = [data]

                for item in items:
                    self.model_counter += 1

                    name = item.get('name', '')
                    url = item.get('kaggle_url', '')

                    if not url:
                        self.logger.warning(f'No URL for model: {name}')
                        continue

                    yield scrapy.Request(
                        url=url,
                        callback=self.parse,
                        meta={
                            'selenium': True,
                            'selenium_wait': 3,
                            'selenium_wait_selector': 'h2',
                            'model_name': name,
                            'model_id': self.model_counter
                        }
                    )
        else:
            # Read CSV file
            with open(self.input_file, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    self.model_counter += 1

                    name = row.get('name', '')
                    url = row.get('kaggle_url', '')

                    if not url:
                        self.logger.warning(f'No URL for model: {name}')
                        continue

                    yield scrapy.Request(
                        url=url,
                        callback=self.parse,
                        meta={
                            'selenium': True,
                            'selenium_wait': 3,
                            'selenium_wait_selector': 'h2',
                            'model_name': name,
                            'model_id': self.model_counter
                        }
                    )
    
    def parse(self, response):
        """
        Parse Kaggle model page for metadata

        Args:
            response: Scrapy response object

        Yields:
            KaggleMetadataItem with extracted metadata
        """
        model_name = response.meta.get('model_name', '')
        model_id = response.meta.get('model_id', 0)

        self.logger.info(f'Processing {model_id}: {model_name}')

        # Use the driver from the middleware (already loaded with the page)
        driver = response.meta.get('driver')

        if not driver:
            self.logger.error(f'No driver available for {model_name}')
            return

        try:
            # Parse tree from the response
            tree = parse_tree_from_response(response)

            # Create item
            item = KaggleMetadataItem()
            item['model_id'] = model_id
            item['name'] = model_name
            item['kaggle_url'] = response.url

            # Extract using driver from middleware pool
            item['short_description'] = extract_description(driver, tree, self.selectors, model_name)
            item['downloads'] = extract_downloads(driver, tree, self.selectors, model_name)
            item['usability'] = extract_usability(driver, tree, self.selectors, model_name)
            item['model_card'] = extract_model_card(driver, tree, self.selectors, model_name)
            item['tags'] = extract_tags(driver, tree, self.selectors, model_name)

            # Extract activity overview data
            total_downloads = extract_downloads(driver, tree, self.selectors, model_name)
            total_views = extract_total_views(driver, tree, self.selectors, model_name)
            total_engagements = extract_total_engagements(driver, tree, self.selectors, model_name)

            # Convert string values to integers/floats for activity_overview
            def parse_numeric_int(value_str):
                """Parse numeric string to integer (handles K, M, B suffixes)"""
                if not value_str:
                    return 0
                try:
                    value_str = value_str.strip().upper()
                    multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
                    for suffix, multiplier in multipliers.items():
                        if suffix in value_str:
                            return int(float(value_str.replace(suffix, '').replace(',', '')) * multiplier)
                    return int(value_str.replace(',', ''))
                except (ValueError, AttributeError):
                    return 0

            def parse_numeric_float(value_str):
                """Parse numeric string to float (handles K, M, B suffixes)"""
                if not value_str:
                    return 0.0
                try:
                    value_str = value_str.strip().upper()
                    multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
                    for suffix, multiplier in multipliers.items():
                        if suffix in value_str:
                            return float(value_str.replace(suffix, '').replace(',', '')) * multiplier
                    return float(value_str.replace(',', ''))
                except (ValueError, AttributeError):
                    return 0.0

            # Build activity_overview structure
            current_time = datetime.now().isoformat()
            item['activity_overview'] = {
                'last_scraped': current_time,
                'total_downloads': parse_numeric_int(total_downloads),
                'total_views': parse_numeric_int(total_views),
                'total_engagements': parse_numeric_float(total_engagements)
            }

            # IMPORTANT: Extract model_metadata BEFORE variations
            # Collaborators, authors, and provenance exist on the main model page
            # If we extract variations first, we'll navigate away from the main page
            collaborators = extract_collaborators(driver, tree, self.selectors, model_name)
            authors = extract_authors(driver, tree, self.selectors, model_name)
            provenance = extract_provenance(driver, tree, self.selectors, model_name)
            item['model_metadata'] = {
                'collaborators': collaborators,
                'authors': authors,
                'provenance': provenance
            }

            # Extract variations
            # NOTE: Variations extraction now handles all versions within each variation
            # No need to queue separate URLs - all versions are scraped in-place
            # This must come AFTER model_metadata extraction since it navigates to variation pages
            item['variations'] = extract_variations(
                driver, self.selectors, model_name, model_id, response.url
            )

            # Log concise summary
            self.logger.info(f"✓ {model_name} - Downloads: {item['downloads']}, Views: {total_views}, Engagements: {total_engagements}, Variations: {len(item.get('variations', []))}")

            yield item

        except Exception as e:
            self.logger.error(f'Error processing {model_name}: {e}')
            import traceback
            traceback.print_exc()
