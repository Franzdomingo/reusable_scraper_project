#!/usr/bin/env python3
"""
Simple entry point for running Scrapy spiders and Kaggle API commands

Usage:
    python run.py [spider_name|api_command] [options]

    If no spider_name is provided, runs all spiders in sequence.

Examples:
    # Scrapy spiders
    python run.py                                         # Run all spiders
    python run.py kaggle_links                            # Run single spider
    python run.py kaggle_links -a max_pages=10            # With arguments
    python run.py kaggle_metadata -a input_file=output/kaggle_output.csv

    # Kaggle API commands
    python run.py kaggle_api_list --page-size=20 --max-pages=5 --output=models.json
    python run.py kaggle_api_csv --input-csv=input.csv --output=models.json
"""

import sys
import os
import subprocess
from pathlib import Path

# Add parent directory to path to import api module
sys.path.insert(0, str(Path(__file__).parent.parent))


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


def run_kaggle_api_command(command, args=None):
    """
    Run a Kaggle API command

    Args:
        command: 'list' or 'csv'
        args: List of command line arguments

    Returns:
        True if successful, False otherwise
    """
    if args is None:
        args = []

    from api.kaggle_api import list_models_and_save, fetch_models_from_csv
    import argparse

    print(f"\n{'='*60}")
    print(f"Running Kaggle API command: {command}")
    print('='*60)

    try:
        if command == 'list':
            # Parse arguments for list command
            parser = argparse.ArgumentParser(description='List Kaggle models')
            parser.add_argument('--page-size', type=int, default=20)
            parser.add_argument('--max-pages', type=int, default=5)
            parser.add_argument('--output', type=str, default='kaggle_models.json')
            parser.add_argument('--filter', type=str, nargs='*')
            parser.add_argument('--output-dir', type=str, default='api_output')

            parsed_args = parser.parse_args(args)
            list_models_and_save(
                page_size=parsed_args.page_size,
                max_pages=parsed_args.max_pages,
                output_file=parsed_args.output,
                filter_keywords=parsed_args.filter,
                output_dir=parsed_args.output_dir
            )
            return True

        elif command == 'csv':
            # Parse arguments for CSV command
            parser = argparse.ArgumentParser(description='Fetch Kaggle models from CSV')
            parser.add_argument('--input-csv', type=str, required=True)
            parser.add_argument('--output', type=str, default='models.json')
            parser.add_argument('--output-dir', type=str, default='api_output')

            parsed_args = parser.parse_args(args)
            fetch_models_from_csv(
                input_csv=parsed_args.input_csv,
                output_file=parsed_args.output,
                output_dir=parsed_args.output_dir
            )
            return True

        else:
            print(f"Unknown API command: {command}")
            return False

    except Exception as e:
        print(f"Error running Kaggle API command: {e}")
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
    """Main entry point for running spiders and API commands"""

    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    # Available spiders and API commands
    available_spiders = ['kaggle_links', 'kaggle_metadata', 'nvidia_models']
    available_api_commands = ['kaggle_api_list', 'kaggle_api_csv']

    # If no arguments, run all spiders
    if len(sys.argv) < 2:
        success = run_all_spiders()
        sys.exit(0 if success else 1)

    command_or_spider = sys.argv[1]

    # Check if it's an API command
    if command_or_spider in available_api_commands:
        api_command = command_or_spider.replace('kaggle_api_', '')
        args = sys.argv[2:] if len(sys.argv) > 2 else []
        success = run_kaggle_api_command(api_command, args)
        sys.exit(0 if success else 1)

    # Check if it's a spider
    elif command_or_spider in available_spiders:
        args = sys.argv[2:] if len(sys.argv) > 2 else []
        success = run_spider(command_or_spider, args)
        sys.exit(0 if success else 1)

    # Unknown command
    else:
        print(f"Unknown command: {command_or_spider}")
        print(f"\nAvailable spiders: {', '.join(available_spiders)}")
        print(f"Available API commands: {', '.join(available_api_commands)}")
        print("\nTo run all spiders, use: python run.py")
        sys.exit(1)


if __name__ == '__main__':
    main()
