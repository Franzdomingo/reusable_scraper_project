#!/usr/bin/env python3
"""
Simple entry point for running Scrapy spiders

Usage:
    python run.py [spider_name] [options]

    If no spider_name is provided, runs all spiders in sequence.

Examples:
    python run.py                                         # Run all spiders
    python run.py kaggle_links                            # Run single spider
    python run.py kaggle_links -a max_pages=10            # With arguments
    python run.py kaggle_metadata -a input_file=output/kaggle_output.csv
"""

import sys
import os
import subprocess
from pathlib import Path


def run_spider(spider_name, args=None):
    """
    Run a single spider

    Args:
        spider_name: Name of the spider to run
        args: List of additional arguments

    Returns:
        True if successful, False otherwise
    """
    if args is None:
        args = []

    # Build Scrapy command
    cmd = ['scrapy', 'crawl', spider_name] + args

    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print('='*60)

    # Execute Scrapy
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {spider_name}: {e}")
        return False


def run_all_spiders():
    """Run all spiders in sequence"""
    print("\n" + "="*60)
    print("RUNNING ALL SPIDERS IN SEQUENCE")
    print("="*60)

    # Define spider execution order
    spiders = [
        ('kaggle_links', ['-a', 'max_pages=100']),
        ('kaggle_metadata', []),
        ('nvidia_models', []),
    ]

    results = []

    for spider_name, default_args in spiders:
        success = run_spider(spider_name, default_args)
        results.append((spider_name, success))

    # Print summary
    print("\n" + "="*60)
    print("EXECUTION SUMMARY")
    print("="*60)
    for spider_name, success in results:
        status = "SUCCESS" if success else "FAILED"
        print(f"{spider_name:20} - {status}")
    print("="*60 + "\n")

    # Return overall success
    return all(success for _, success in results)


def main():
    """Main entry point for running spiders"""

    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    # Available spiders
    available_spiders = ['kaggle_links', 'kaggle_metadata', 'nvidia_models']

    # If no arguments or first arg is not a spider name, run all
    if len(sys.argv) < 2 or sys.argv[1] not in available_spiders:
        # Check if user provided arguments that don't match a spider
        if len(sys.argv) >= 2:
            print(f"Unknown spider: {sys.argv[1]}")
            print(f"\nAvailable spiders: {', '.join(available_spiders)}")
            print("\nTo run all spiders, use: python run.py")
            sys.exit(1)

        # Run all spiders
        success = run_all_spiders()
        sys.exit(0 if success else 1)
    else:
        # Run specific spider
        spider_name = sys.argv[1]
        args = sys.argv[2:] if len(sys.argv) > 2 else []

        success = run_spider(spider_name, args)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
