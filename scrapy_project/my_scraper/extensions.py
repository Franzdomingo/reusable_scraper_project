"""
Custom Scrapy extensions

This module contains custom extensions for enhancing Scrapy functionality.

"""

import logging
from scrapy import signals
from colorama import Fore, Style, init as colorama_init


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output based on log level"""

    COLORS = {
        'ERROR': Fore.RED,
        'WARNING': Fore.YELLOW,
        'INFO': Fore.WHITE,
        'DEBUG': Fore.CYAN,
        'CRITICAL': Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        """Format the log record with appropriate color"""
        # Make a copy of the record to avoid modifying the original
        record = logging.makeLogRecord(record.__dict__)

        # Get the color for this log level
        log_color = self.COLORS.get(record.levelname, Fore.WHITE)

        # Color the levelname
        record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"

        return super().format(record)


class ColoredLoggingExtension:
    """
    Scrapy extension to enable colored logging output

    This extension configures all logging handlers to use colored output
    where ERROR logs appear in red and WARNING logs appear in yellow.
    """

    def __init__(self):
        """Initialize colorama for cross-platform colored terminal output"""
        colorama_init(autoreset=True)

    @classmethod
    def from_crawler(cls, crawler):
        """
        Create extension instance from crawler

        This is called by Scrapy to instantiate the extension.
        """
        ext = cls()

        # Connect to spider_opened signal to configure logging when spider starts
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)

        return ext

    def spider_opened(self, spider):
        """
        Configure colored logging when spider opens

        Args:
            spider: The spider instance that was opened
        """
        # Get the log format from settings, or use default
        log_format = spider.settings.get('LOG_FORMAT', '[%(asctime)s] %(levelname)s: %(message)s')
        log_dateformat = spider.settings.get('LOG_DATEFORMAT', '%H:%M:%S')

        # Create colored formatter
        formatter = ColoredFormatter(log_format, datefmt=log_dateformat)

        # Get the root logger
        root_logger = logging.getLogger()

        # Apply colored formatter to all existing handlers
        for handler in root_logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler):
                handler.setFormatter(formatter)

        # Also configure scrapy's logger specifically
        scrapy_logger = logging.getLogger('scrapy')
        for handler in scrapy_logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler):
                handler.setFormatter(formatter)

        spider.logger.info('Colored logging extension initialized')
