#!/usr/bin/env python3
"""
Selectors Configuration
Contains all CSS/XPath selectors used for web scraping
Author: Franz Phillip G. Domingo
Date: 2025-10-08
"""

from typing import Dict, List


class KaggleSelectors:
    """Configuration class for Kaggle scraping selectors"""
    
    # Description selectors - ordered by priority (most specific first)
    # Updated 2025-10-23: Using stable selectors (meta tags, semantic HTML)
    DESCRIPTION_SELECTORS: List[str] = [
        # Most stable: meta description tag
        '//meta[@name="description"]/@content',
        # Semantic: Find description after "Language models" pattern
        '//p[contains(text(), "Language models") or contains(text(), "models pretrained")]',
        # Structure-based: Description appears after organization name
        '//h1[contains(@class, "sc-lgpSej")]/following-sibling::span//p[2]',
        # Fallback: Any paragraph with margin-top styling in main content
        '//div[@class="sc-guPfGz eukZsY"]//p[@style="margin-top: 40px;"]',
    ]
    
    # Download count selectors - ordered by priority
    # Updated 2025-10-23: Using absolute XPath selector
    # Target: span element containing download count at specific path
    DOWNLOAD_SELECTORS: List[str] = [
        '/html/body/div/div[1]/div[2]/div/div[2]/div/div[5]/div/div[1]/div[2]/div[1]/div[2]/div[1]/span',
    ]

    # Total views selectors - ordered by priority
    # Updated 2025-10-23: Using absolute XPath and CSS selectors for total views
    # Target: span element containing total views count
    TOTAL_VIEWS_SELECTORS: List[str] = [
        '/html/body/div/div[1]/div[2]/div/div[2]/div/div[5]/div/div[4]/div[2]/div[1]/div[2]/div[2]/span',
        '.sc-ffeAVz > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > span:nth-child(1)',
    ]

    # Total engagements selectors - ordered by priority
    # Updated 2025-10-23: Using absolute XPath and CSS selectors for total engagements
    # Target: span element containing total engagements count
    TOTAL_ENGAGEMENTS_SELECTORS: List[str] = [
        '/html/body/div/div[1]/div[2]/div/div[2]/div/div[5]/div/div[4]/div[2]/div[3]/div[2]/div[2]/span',
        'div.sc-fEaSUP:nth-child(3) > div:nth-child(2) > div:nth-child(2) > span:nth-child(1)',
    ]

    # Usability score selectors - ordered by priority
    # Updated 2025-10-23: Using absolute XPath selector
    # Target: p element containing usability score (numeric value)
    USABILITY_SELECTORS: List[str] = [
        # Absolute XPath selector
        '/html/body/div/div[1]/div[2]/div/div[2]/div/div[5]/div/div[1]/div[2]/p',
    ]
    
    # Tag selectors - ordered by priority
    # Updated 2025-10-23: Using stable selectors (heading anchors, semantic links)
    TAG_SELECTORS: List[str] = [
        # MOST STABLE: Find div containing h2 "Tags"
        '//div[.//h2[contains(text(), "Tags ")]]',
        '//h2[contains(text(), "Tags ")]/following-sibling::div[1]',
    ]

    # Individual tag link selector
    # Updated 2025-10-23: Using stable selectors (target attribute, href pattern)
    TAG_LINK_SELECTOR: str = 'a[target="_blank"][href*="/models?"]'

    # Tags "more" button selector (for expanding hidden tags)
    # Updated: prefer absolute XPath but keep original CSS class as a fallback
    # Stored as a list so callers can provide multiple selector types (XPath first, CSS fallback)
    TAG_MORE_BUTTON_TEXT_SPAN: List[str] = [
        '/html/body/div/div[1]/div[2]/div/div[2]/div/div[5]/div/div[2]/div[2]/div[2]/div[1]/div/button',  # XPath to the "more" button  # Fallback CSS selector (previous fragile class)
    ]
    TAG_MORE_POPUP_CONTAINER: str = '.eqXpEC'  # Popup container that appears when "more" is clicked
    TAG_POPUP_CHECKBOX_BUTTON: str = 'button[role="checkbox"]'  # Tag buttons within popup
    TAG_POPUP_TEXT_SPAN: str = 'span.bMbEZO'  # Span containing tag text within popup buttons

    # Collaborators action button (to expand/collapse the section if needed)
    # Updated 2025-10-22: New Kaggle redesign selectors
    COLLABORATORS_ACTION_BUTTON: str = 'button[aria-label="Expand Collaborators"]'

    # Collaborators selectors - ordered by priority
    # Target: p elements with margin-left style containing collaborator names
    # Updated 2025-10-22: Collaborators section is now collapsed by default
    COLLABORATORS_SELECTORS: List[str] = [
        # CSS selector - 2025-10-22 redesign
        # After clicking expand button, content appears in a div
        '//h3[text()="Collaborators"]/following::div//p',
        # Fallback - older selectors
        'p.sc-gGKoUb.bEqAGC',
        'p[style*="margin-left"]',
        '.sc-cFFDlC p',
        # XPath fallback
        '//div[contains(@class, "sc-cFFDlC")]//p[contains(@class, "sc-gGKoUb")]'
    ]

    # Authors action button (to expand the authors section)
    # Updated 2025-10-22: New Kaggle redesign selectors
    AUTHORS_ACTION_BUTTON: str = 'button[aria-label="Expand Authors"]'

    # Authors selectors - ordered by priority
    # Target: p element containing authors/contributors information
    # Updated 2025-10-22: Authors section is now collapsed by default
    AUTHORS_SELECTORS: List[str] = [
        # XPath selector - 2025-10-22 redesign
        # After clicking expand button, content appears in a div
        '//h3[text()="Authors"]/following::div//p',
        # Fallback - older selectors
        'div.sc-bBhMX:nth-child(2) > div:nth-child(2)',
        'div.sc-bBhMX:nth-child(2) p.sc-gGKoUb',
        '//div[contains(@class, "sc-bBhMX")][2]//p[contains(@class, "sc-gGKoUb")]'
    ]

    # Provenance action button (to expand the provenance section)
    # Updated 2025-10-22: New Kaggle redesign selectors
    PROVENANCE_ACTION_BUTTON: str = 'button[aria-label="Expand Provenance"]'

    # Provenance selectors - ordered by priority
    # Target: div containing provenance updates, sources, and citations
    # Updated 2025-10-22: Provenance section is now collapsed by default
    PROVENANCE_SELECTORS: List[str] = [
        # XPath selector - 2025-10-22 redesign
        # After clicking expand button, content appears in a div
        '//h3[text()="Provenance"]/following::div[1]',
        # Fallback - older selectors
        '.sc-fPzfn',
        'div.sc-cFFDlC.sc-fPzfn.esaBZM.hMDRMp',
        '//div[contains(@class, "sc-fPzfn")]'
    ]

    # Model card selectors - ordered by priority
    # Updated 2025-10-23: Using absolute XPath selector
    MODEL_CARD_SELECTORS: List[str] = [
        # Absolute XPath selector
        '/html/body/div/div[1]/div[2]/div/div[2]/div/div[5]/div/div[1]/div[1]/div[2]/div[1]',
    ]

    # Optional action button to reveal model card (click before scraping)
    # Using role and aria attributes for stability
    MODEL_CARD_ACTION_BUTTON: str = 'button[aria-label*="Read more"]'
    
    # All tab buttons (to extract all tabs for processing)
    # Target: All tab buttons with role="tab" containing tab names
    # Updated 2025-10-24: Made selector more specific to avoid matching popup tabs
    # Uses div[role="tablist"] to scope to framework tabs only, excluding version popup tabs
    VARIATION_TABS_ALL: str = 'div[role="tablist"] > button[role="tab"]'

    # Tab text selector (within each tab button)
    # Updated 2025-10-23: Using stable selectors (direct text extraction from button)
    # NOTE: Extract text directly from button[role="tab"] instead of relying on span classes
    VARIATION_TAB_TEXT: str = 'span'  # Generic span within tab button

    # Transformers variation dropdown action selector (click to open the list)
    # Target: The combobox button with aria-label="Select Variation"
    # Multiple selectors for fallback (ordered by specificity)
    TRANSFORMERS_VARIATION_ACTION: List[str] = [
        'div[role="combobox"][aria-label="Select Variation"]',  # Most specific
        'div[role="combobox"]',  # More generic - any combobox
        'div[aria-label="Select Variation"]',  # aria-label only
        'button[aria-label="Select Variation"]',  # Alternative - might be button instead of div
    ]

    # Transformers variation list container (the opened dropdown)
    # Target: ul element with role="listbox" that contains all variation options
    TRANSFORMERS_VARIATION_LIST_CONTAINER: str = 'ul[role="listbox"]'

    # Transformers variation list item selector (all list items in the dropdown)
    # Target: li elements with role="option" within the opened listbox
    TRANSFORMERS_VARIATION_LIST_ITEMS: str = 'li[role="option"]'

    # Transformers variation name selector (text within each list item in dropdown)
    # Target: div with class "sc-jaGrhB hYa-DAr" containing the variation name
    TRANSFORMERS_VARIATION_NAME: str = 'div.sc-jaGrhB.hYa-DAr'

    # Transformers variation details selectors (after clicking a variation)
    # These appear after selecting a variation from the dropdown

    # Selected variation name (appears in the selected state)
    TRANSFORMERS_VARIATION_SELECTED_NAME: str = 'div.sc-jaGrhB.hYa-DAr'

    # Version selector (appears after selecting a variation)
    # Updated 2025-10-23: Using absolute XPath selector
    # Target: a element containing version info at specific path
    TRANSFORMERS_VARIATION_VERSION: List[str] = [
        '/html/body/div/div[1]/div[2]/div/div[2]/div/div[5]/div/div[2]/div[2]/div[2]/div[1]/div[1]/div[2]/div[1]/p/a',
        'a.sc-cOpnSz',  # Fallback CSS selector
    ]

    # Version popup button selector (button to open versions list popup)
    # NOTE: This may be the same selector as TRANSFORMERS_VARIATION_VERSION
    # Updated 2025-10-23: Button that opens popup showing all available versions
    VARIATION_VERSIONS_BUTTON: List[str] = [
        '/html/body/div/div[1]/div[2]/div/div[2]/div/div[5]/div/div[2]/div[2]/div[2]/div[1]/div[1]/div[2]/div[1]/p/a',
        '.sc-cOpnSz',  # Fallback CSS selector
    ]

    # Version popup list items (all version items in the popup)
    # Target: All li elements with class MuiListItem-divider containing version data
    VARIATION_VERSIONS_POPUP_ITEMS: str = 'li.MuiListItem-divider'

    # Version popup - created by field (within each version item)
    # Target: span containing the creator/author name
    # XPath: /html/body/div[2]/div[3]/div/div/div[2]/div/ul/li[1]/div/a/div/div[2]/span[1]
    # CSS: li.MuiListItem-divider:nth-child(1) > div:nth-child(1) > a:nth-child(1) > div:nth-child(1) > div:nth-child(2) > span:nth-child(2)
    VARIATION_VERSION_CREATED_BY: List[str] = [
        'div > a > div > div:nth-child(2) > span:nth-child(2)',  # Relative to li.MuiListItem-divider
    ]

    # Version popup - update description field (within each version item)
    # Target: span containing the update/change description
    # XPath: /html/body/div[2]/div[3]/div/div/div[2]/div/ul/li[1]/div/a/div/div[2]/span[2]
    # CSS: li.MuiListItem-divider:nth-child(1) > div:nth-child(1) > a:nth-child(1) > div:nth-child(1) > div:nth-child(2) > span:nth-child(3)
    VARIATION_VERSION_UPDATE_DESC: List[str] = [
        'div > a > div > div:nth-child(2) > span:nth-child(3)',  # Relative to li.MuiListItem-divider
    ]

    # Version popup - version number field (within each version item)
    # Target: div containing version text like "Version 4"
    # XPath: /html/body/div[2]/div[3]/div/div/div[2]/div/ul/li[1]/div/a/div/div[2]/div
    # CSS: li.MuiListItem-divider:nth-child(1) > div:nth-child(1) > a:nth-child(1) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1)
    VARIATION_VERSION_NUMBER: List[str] = [
        'div > a > div > div:nth-child(2) > div:nth-child(1)',  # Relative to li.MuiListItem-divider
    ]

    # Downloads selector (appears after selecting a variation)
    # Target: span element with classes for download count
    # IMPORTANT: This must be the variation-specific downloads, NOT the main model downloads
    # Updated 2025-10-23: Using new XPath and CSS selectors
    # XPath: /html/body/div/div[1]/div[2]/div/div[2]/div/div[5]/div/div[2]/div[2]/div[2]/div[1]/div[1]/div[2]/div[2]/p/div/span
    # CSS: .sc-ftYudu > div:nth-child(2) > p:nth-child(2) > div:nth-child(1) > span:nth-child(1)
    TRANSFORMERS_VARIATION_DOWNLOADS_XPATH: str = '/html/body/div/div[1]/div[2]/div/div[2]/div/div[5]/div/div[2]/div[2]/div[2]/div[1]/div[1]/div[2]/div[2]/p/div/span'
    TRANSFORMERS_VARIATION_DOWNLOADS_CSS: str = '.sc-ftYudu > div:nth-child(2) > p:nth-child(2) > div:nth-child(1) > span:nth-child(1)'

    # Legacy selector for backward compatibility
    TRANSFORMERS_VARIATION_DOWNLOADS: str = TRANSFORMERS_VARIATION_DOWNLOADS_CSS

    # License selectors (appears after selecting a variation)
    # License can appear in different formats (link or plain text)
    TRANSFORMERS_VARIATION_LICENSE_SELECTORS: List[str] = [
        '/html/body/div/div[1]/div[2]/div/div[2]/div/div[5]/div/div[2]/div[2]/div[2]/div[3]/div[1]/div[2]/div[2]/p/a',
        'a.sc-kjwdDK',  # Fallback CSS selector
    ]

    # Model card selector for variation (appears after selecting a variation)
    # Target: div element containing the model card (Model Overview section)
    # This section contains an h2 with "Model Overview" text
    # Updated 2025-10-25: Prioritizing content-based XPath selector for stability
    # Structure: <div class="sc-iRTMaw buAyFc"><h2>Model Overview</h2>...</div>
    TRANSFORMERS_VARIATION_MODEL_CARD_SELECTORS: List[str] = [
        '//div[./h2[contains(text(), "Model Overview")]]',  # Primary: Stable content-based XPath - finds div containing h2 with "Model Overview"
        '/html/body/div/div[1]/div[2]/div/div[2]/div/div[5]/div/div[2]/div[2]/div[2]/div[3]/div[1]/div[3]',  # Fallback: Absolute XPath selector
    ]

    # Is Finetunable selector for variation (appears after selecting a variation)
    # Target: p element with "Yes" or "No" indicating if the model is finetunable
    # Updated 2025-10-25: Using content-based XPath selector (is_contain approach)
    # Finds the div containing "Fine-Tunable" span, then gets the p element with the Yes/No value
    # Structure: <div><span>Fine-Tunable</span><p style="margin-top: 8px;">Yes</p></div>
    TRANSFORMERS_IS_FINETUNABLE_SELECTORS: List[str] = [
        '//div[.//span[contains(text(), "Fine-Tunable")]]/p',  # Primary content-based XPath - stable
        '/html/body/div/div[1]/div[2]/div/div[2]/div/div[5]/div/div[2]/div[2]/div[2]/div[3]/div[1]/div[2]/div[1]/p',  # Fallback absolute XPath
        '.sc-huUlgU > div:nth-child(1) > p:nth-child(2)',  # Last resort CSS selector
    ]

    # Example Usage selector for variation (appears after selecting a variation)
    # Target: Parent container that holds both the header and content
    # The structure is: parent div contains:
    #   - div#example-use (header)
    #   - div.sc-lkCrJH.ghmUBs (actual content) OR p.sc-hwddKA.dIsQKt (no guide message)
    # If it contains "This variation does not have a usage guide yet.", the field should be empty
    TRANSFORMERS_EXAMPLE_USAGE_SELECTORS: List[str] = [
        'div:has(> div#example-use)',  # Parent div containing example-use
    ]
    
    # Fallback CSS selector for description (used with Selenium)
    DESCRIPTION_CSS_FALLBACK: str = '.sc-fhfEft > p:nth-child(2)'
    
    # Model links XPath
    MODEL_LINKS_XPATH: str = '//ul/li/div/a[contains(@href, "/models/")]'
    
    # Model name XPath (within link element)
    MODEL_NAME_XPATH: str = './/div/div[2]/div/text()'
    
    # Next button XPath
    NEXT_BUTTON_XPATH: str = '//button[.//svg[@data-testid="NavigateNextIcon"]]'
    
    # Alternative next button XPath
    NEXT_BUTTON_ALT_XPATH: str = '//nav//button[contains(@class, "MuiPaginationItem") and contains(@aria-label, "next")]'


class NvidiaSelectors:
    """Configuration class for Nvidia scraping selectors"""

    # Model card selectors on the main page
    # Target: All model cards on the page
    MODEL_CARDS: str = 'a[data-linkbox-overlay="true"]'

    # Model name selector within each card
    # Target: The title attribute containing the model name
    MODEL_NAME_ATTRIBUTE: str = 'title'

    # Model URL selector (href attribute)
    # Target: The href attribute containing the relative URL
    MODEL_URL_ATTRIBUTE: str = 'href'

    # Initial visible tags container
    # Target: div containing the first set of visible tag buttons
    # Example: <div class="flex items-center gap-2 overflow-hidden">
    VISIBLE_TAGS_CONTAINER: str = 'div.flex.items-center.gap-2.overflow-hidden'

    # Individual visible tag buttons/links
    # Target: button elements containing tag links
    # Example: <button class="inline-flex min-w-fit..."><a href="/search?q=tool+calling">tool calling</a></button>
    VISIBLE_TAG_BUTTONS: str = 'button.inline-flex.min-w-fit'

    # Tag link within button (to get tag text)
    TAG_LINK: str = 'a'

    # "More tags" button selector (e.g., "+3" button)
    # Target: button that opens popover with additional tags
    # Example: <button data-testid="nv-popover-trigger" type="button"...>+3</button>
    MORE_TAGS_BUTTON: str = 'button[data-testid="nv-popover-trigger"]'

    # Popover container (appears after clicking more tags button)
    # Target: div containing the additional tags in the popover
    # Example: <div class="flex w-fit max-w-[calc(...)] flex-wrap items-center gap-2...">
    POPOVER_TAGS_CONTAINER: str = 'div.flex.w-fit.max-w-\\[calc\\(var\\(--radix-popover-content-available-width\\)_-_32px\\)\\]'

    # Alternative simpler popover selector
    POPOVER_TAGS_CONTAINER_ALT: str = 'div[class*="flex"][class*="w-fit"][class*="flex-wrap"]'

    # Tag buttons within popover
    # Same structure as visible tags
    POPOVER_TAG_BUTTONS: str = 'button.inline-flex.min-w-fit'

    # Model card content selector (from /modelcard page)
    # Target: div containing the full model card markdown content
    # Example: <div class="prose prose-markdown-compat max-w-[85ch]">...</div>
    MODEL_CARD_CONTENT: str = 'div.prose.prose-markdown-compat'


class GeneralSelectors:
    """Configuration class for general scraping selectors"""
    
    # Common patterns for numeric values that might represent downloads
    NUMERIC_PATTERNS: List[str] = [
        r'\d+[KkMm]?',  # Numbers with optional K/M suffix
        r'\d+[\.\,]\d+[KkMm]?',  # Decimal numbers with K/M suffix
    ]
    
    # Common user-agent strings
    USER_AGENTS: List[str] = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
    ]


def get_selectors_for_site(site: str) -> Dict:
    """
    Get selectors configuration for a specific site
    
    Args:
        site: The site name ('kaggle', 'nvidia', etc.)
        
    Returns:
        Dictionary containing selectors for the specified site
    """
    selectors_map = {
        'kaggle': {
            'description': KaggleSelectors.DESCRIPTION_SELECTORS,
            'downloads': KaggleSelectors.DOWNLOAD_SELECTORS,
            'total_views': KaggleSelectors.TOTAL_VIEWS_SELECTORS,
            'total_engagements': KaggleSelectors.TOTAL_ENGAGEMENTS_SELECTORS,
            'usability': KaggleSelectors.USABILITY_SELECTORS,
            'description_css_fallback': KaggleSelectors.DESCRIPTION_CSS_FALLBACK,
            'model_card_selectors': KaggleSelectors.MODEL_CARD_SELECTORS,
            'model_card_action': KaggleSelectors.MODEL_CARD_ACTION_BUTTON,
            'variation_tabs_all': KaggleSelectors.VARIATION_TABS_ALL,
            'variation_tab_text': KaggleSelectors.VARIATION_TAB_TEXT,
            'variation_action': KaggleSelectors.TRANSFORMERS_VARIATION_ACTION,
            'variation_list_container': KaggleSelectors.TRANSFORMERS_VARIATION_LIST_CONTAINER,
            'variation_list_items': KaggleSelectors.TRANSFORMERS_VARIATION_LIST_ITEMS,
            'variation_name': KaggleSelectors.TRANSFORMERS_VARIATION_NAME,
            'variation_selected_name': KaggleSelectors.TRANSFORMERS_VARIATION_SELECTED_NAME,
            'variation_version': KaggleSelectors.TRANSFORMERS_VARIATION_VERSION,
            'variation_versions_button': KaggleSelectors.VARIATION_VERSIONS_BUTTON,
            'variation_versions_popup_items': KaggleSelectors.VARIATION_VERSIONS_POPUP_ITEMS,
            'variation_version_created_by': KaggleSelectors.VARIATION_VERSION_CREATED_BY,
            'variation_version_update_desc': KaggleSelectors.VARIATION_VERSION_UPDATE_DESC,
            'variation_version_number': KaggleSelectors.VARIATION_VERSION_NUMBER,
            'variation_downloads': KaggleSelectors.TRANSFORMERS_VARIATION_DOWNLOADS_CSS,
            'variation_downloads_xpath': KaggleSelectors.TRANSFORMERS_VARIATION_DOWNLOADS_XPATH,
            'variation_license': KaggleSelectors.TRANSFORMERS_VARIATION_LICENSE_SELECTORS,
            'variation_model_card': KaggleSelectors.TRANSFORMERS_VARIATION_MODEL_CARD_SELECTORS,
            'is_finetunable': KaggleSelectors.TRANSFORMERS_IS_FINETUNABLE_SELECTORS,
            'example_usage': KaggleSelectors.TRANSFORMERS_EXAMPLE_USAGE_SELECTORS,
            'tags': KaggleSelectors.TAG_SELECTORS,
            'tag_links': KaggleSelectors.TAG_LINK_SELECTOR,
            'tag_more_button_span': KaggleSelectors.TAG_MORE_BUTTON_TEXT_SPAN,
            'tag_more_popup': KaggleSelectors.TAG_MORE_POPUP_CONTAINER,
            'tag_popup_checkbox': KaggleSelectors.TAG_POPUP_CHECKBOX_BUTTON,
            'tag_popup_text_span': KaggleSelectors.TAG_POPUP_TEXT_SPAN,
            'collaborators': KaggleSelectors.COLLABORATORS_SELECTORS,
            'collaborators_action': KaggleSelectors.COLLABORATORS_ACTION_BUTTON,
            'authors': KaggleSelectors.AUTHORS_SELECTORS,
            'authors_action': KaggleSelectors.AUTHORS_ACTION_BUTTON,
            'provenance': KaggleSelectors.PROVENANCE_SELECTORS,
            'provenance_action': KaggleSelectors.PROVENANCE_ACTION_BUTTON,
            'model_links_xpath': KaggleSelectors.MODEL_LINKS_XPATH,
            'model_name_xpath': KaggleSelectors.MODEL_NAME_XPATH,
            'next_button_xpath': KaggleSelectors.NEXT_BUTTON_XPATH,
            'next_button_alt_xpath': KaggleSelectors.NEXT_BUTTON_ALT_XPATH,
        },
        'nvidia': {
            'model_cards': NvidiaSelectors.MODEL_CARDS,
            'model_name_attr': NvidiaSelectors.MODEL_NAME_ATTRIBUTE,
            'model_url_attr': NvidiaSelectors.MODEL_URL_ATTRIBUTE,
            'visible_tags_container': NvidiaSelectors.VISIBLE_TAGS_CONTAINER,
            'visible_tag_buttons': NvidiaSelectors.VISIBLE_TAG_BUTTONS,
            'tag_link': NvidiaSelectors.TAG_LINK,
            'more_tags_button': NvidiaSelectors.MORE_TAGS_BUTTON,
            'popover_tags_container': NvidiaSelectors.POPOVER_TAGS_CONTAINER,
            'popover_tags_container_alt': NvidiaSelectors.POPOVER_TAGS_CONTAINER_ALT,
            'popover_tag_buttons': NvidiaSelectors.POPOVER_TAG_BUTTONS,
            'model_card_content': NvidiaSelectors.MODEL_CARD_CONTENT,
        }
    }
    
    return selectors_map.get(site, {})
