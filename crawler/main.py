#!/usr/bin/env python3
"""
Bookstore Finder Crawler
Main entry point for crawling bookstore websites to find product pages
and extract location information.
"""

import argparse
import csv
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict

from config import (
    BOOK_CONFIG,
    CRAWLER_CONFIG,
    OUTPUT_CONFIG,
    LOGGING_CONFIG
)
from database import BookstoreDatabase
from google_search import ProductPageFinder
from extractor import LocationExtractor
from utils import RateLimiter, RobotsChecker, make_request

# Configure logging
logging.basicConfig(
    level=LOGGING_CONFIG["level"],
    format=LOGGING_CONFIG["format"],
    datefmt=LOGGING_CONFIG["date_format"],
    handlers=[
        logging.FileHandler(OUTPUT_CONFIG["log_file"]),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class BookstoreCrawler:
    """
    Main crawler class that orchestrates the crawling process.
    """

    def __init__(
        self,
        db_path: str,
        respect_robots: bool = True,
        verbose: bool = False
    ):
        """
        Initialize the crawler.

        Args:
            db_path: Path to SQLite database
            respect_robots: Whether to respect robots.txt
            verbose: Enable verbose logging
        """
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        self.db = BookstoreDatabase(db_path)
        self.user_agent = CRAWLER_CONFIG["user_agent"]
        self.timeout = CRAWLER_CONFIG["request_timeout"]

        # Initialize components
        self.rate_limiter = RateLimiter(CRAWLER_CONFIG["delay_between_requests"])
        self.robots_checker = RobotsChecker(self.user_agent) if respect_robots else None
        self.product_finder = ProductPageFinder(self.user_agent, self.timeout)
        self.location_extractor = LocationExtractor(self.user_agent, self.timeout)

        logger.info("Crawler initialized")
        logger.info(f"Book: {BOOK_CONFIG['title']} by {BOOK_CONFIG['author']}")

    def crawl_bookstore(self, name: str, url: str, prefilled_postal_code: str = None, prefilled_city: str = None) -> Dict:
        """
        Crawl a single bookstore.

        Args:
            name: Bookstore name
            url: Bookstore homepage URL
            prefilled_postal_code: Pre-filled postal code from CSV (optional)
            prefilled_city: Pre-filled city from CSV (optional)

        Returns:
            Dictionary with crawl results
        """
        logger.info(f"{'='*60}")
        logger.info(f"Processing: {name}")
        logger.info(f"URL: {url}")
        if prefilled_postal_code:
            logger.info(f"Pre-filled location: {prefilled_postal_code}, {prefilled_city}")

        result = {
            "name": name,
            "homepage_url": url,
            "product_url": None,
            "postal_code": prefilled_postal_code,
            "city": prefilled_city,
            "success": False,
            "error_message": None
        }

        try:
            # Check robots.txt
            if self.robots_checker and not self.robots_checker.can_fetch(url):
                logger.warning(f"Robots.txt disallows crawling: {url}")
                result["error_message"] = "Disallowed by robots.txt"
                return result

            # Rate limiting
            self.rate_limiter.wait_if_needed(url)

            # Step 1: Find product page
            logger.info("Step 1: Searching for product page...")
            product_url = self.product_finder.find_product_page(name, url)

            if not product_url:
                logger.warning(f"Product page not found for {name}")
                result["error_message"] = "Product page not found"
                return result

            result["product_url"] = product_url
            logger.info(f"✓ Found product page: {product_url}")

            # Step 2: Extract location (postal code + city)
            # Skip if we already have pre-filled data
            if prefilled_postal_code and prefilled_city:
                logger.info(f"✓ Using pre-filled location: {prefilled_postal_code}, {prefilled_city}")
                result["success"] = True
            else:
                logger.info("Step 2: Extracting location information...")

                # Fetch homepage for location extraction
                self.rate_limiter.wait_if_needed(url)
                response = make_request(url, self.user_agent, self.timeout)

                if response:
                    postal_code, city = self.location_extractor.extract_location(
                        url,
                        response.text
                    )

                    if postal_code:
                        result["postal_code"] = postal_code
                        result["city"] = city or "Unknown"
                        result["success"] = True
                        logger.info(f"✓ Found location: {postal_code}, {city}")
                    else:
                        logger.warning(f"Could not extract postal code for {name}")
                        result["error_message"] = "Postal code not found"
                else:
                    logger.warning(f"Could not fetch homepage for location extraction")
                    result["error_message"] = "Could not fetch homepage"

        except Exception as e:
            logger.error(f"Error crawling {name}: {e}", exc_info=True)
            result["error_message"] = str(e)

        return result

    def crawl_from_csv(self, csv_path: str, limit: Optional[int] = None) -> Dict:
        """
        Crawl bookstores from a CSV file.

        Args:
            csv_path: Path to CSV file with bookstore data
            limit: Optional limit on number of bookstores to process

        Returns:
            Dictionary with crawl statistics
        """
        logger.info(f"Reading bookstores from: {csv_path}")

        # Read CSV
        bookstores = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    bookstore = {
                        "name": row["name"].strip(),
                        "url": row["url"].strip(),
                        "postal_code": row.get("postal_code", "").strip() if row.get("postal_code") else None,
                        "city": row.get("city", "").strip() if row.get("city") else None
                    }
                    bookstores.append(bookstore)
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            return {"error": str(e)}

        logger.info(f"Found {len(bookstores)} bookstores in CSV")

        # Apply limit if specified
        if limit:
            bookstores = bookstores[:limit]
            logger.info(f"Limiting to {limit} bookstores")

        # Start crawl run
        run_id = self.db.start_crawl_run()

        # Crawl each bookstore
        total = len(bookstores)
        successful = 0
        failed = 0

        for i, bookstore in enumerate(bookstores, 1):
            logger.info(f"\n[{i}/{total}] Processing bookstore...")

            result = self.crawl_bookstore(
                bookstore["name"],
                bookstore["url"],
                prefilled_postal_code=bookstore.get("postal_code"),
                prefilled_city=bookstore.get("city")
            )

            # Save to database
            self.db.upsert_bookstore(
                name=result["name"],
                homepage_url=result["homepage_url"],
                product_url=result["product_url"],
                postal_code=result["postal_code"],
                city=result["city"],
                success=result["success"],
                error_message=result["error_message"]
            )

            if result["success"]:
                successful += 1
                logger.info(f"✓ Success ({successful}/{total})")
            else:
                failed += 1
                logger.warning(f"✗ Failed ({failed}/{total}): {result['error_message']}")

            # Add delay between bookstores (Google search rate limiting)
            if i < total and CRAWLER_CONFIG["use_google_search"]:
                delay = CRAWLER_CONFIG["google_delay"]
                logger.debug(f"Waiting {delay}s before next bookstore...")
                time.sleep(delay)

        # Complete crawl run
        self.db.complete_crawl_run(run_id, total, successful, failed)

        # Statistics
        stats = {
            "total": total,
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful/total*100):.1f}%" if total > 0 else "0%"
        }

        logger.info(f"\n{'='*60}")
        logger.info("CRAWL COMPLETED")
        logger.info(f"{'='*60}")
        logger.info(f"Total bookstores: {stats['total']}")
        logger.info(f"Successful: {stats['successful']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"Success rate: {stats['success_rate']}")
        logger.info(f"{'='*60}\n")

        return stats

    def export_json(self, output_path: str, manual_entries_path: str = None) -> int:
        """
        Export results to JSON.

        Args:
            output_path: Path to output JSON file
            manual_entries_path: Optional path to CSV with manual entries

        Returns:
            Number of bookstores exported
        """
        logger.info(f"Exporting to JSON: {output_path}")
        if manual_entries_path:
            logger.info(f"Including manual entries from: {manual_entries_path}")
        count = self.db.export_to_json(output_path, manual_entries_path)
        logger.info(f"Exported {count} bookstores")
        return count

    def show_statistics(self):
        """
        Display database statistics.
        """
        stats = self.db.get_statistics()

        logger.info(f"\n{'='*60}")
        logger.info("DATABASE STATISTICS")
        logger.info(f"{'='*60}")
        logger.info(f"Total bookstores in database: {stats['total_bookstores']}")
        logger.info(f"Successful crawls: {stats['successful_crawls']}")
        logger.info(f"With product URL: {stats['with_product_url']}")
        logger.info(f"With postal code: {stats['with_postal_code']}")
        logger.info(f"Complete records: {stats['complete_records']}")
        if stats['last_crawl']:
            logger.info(f"Last crawl: {stats['last_crawl']}")
        logger.info(f"{'='*60}\n")


def main():
    """
    Main entry point.
    """
    parser = argparse.ArgumentParser(
        description="Crawl bookstore websites to find book product pages and locations."
    )

    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to CSV file with bookstore data (name,url)"
    )

    parser.add_argument(
        "--output",
        "-o",
        default=OUTPUT_CONFIG["json_output_path"],
        help="Path to output JSON file (default: %(default)s)"
    )

    parser.add_argument(
        "--db",
        default=OUTPUT_CONFIG["database_path"],
        help="Path to SQLite database (default: %(default)s)"
    )

    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        help="Limit number of bookstores to process (for testing)"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--no-robots",
        action="store_true",
        help="Disable robots.txt checking (not recommended)"
    )

    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only show statistics, don't crawl"
    )

    parser.add_argument(
        "--manual",
        "-m",
        default="../data/manual_entries.csv",
        help="Path to CSV with manual entries (default: %(default)s)"
    )

    args = parser.parse_args()

    # Initialize crawler
    crawler = BookstoreCrawler(
        db_path=args.db,
        respect_robots=not args.no_robots,
        verbose=args.verbose
    )

    # Show statistics only
    if args.stats_only:
        crawler.show_statistics()
        return

    # Run crawl
    logger.info("Starting Bookstore Finder Crawler")
    logger.info(f"Input CSV: {args.input}")
    logger.info(f"Output JSON: {args.output}")
    logger.info(f"Database: {args.db}")

    stats = crawler.crawl_from_csv(args.input, limit=args.limit)

    # Export to JSON (always export, even with 0 crawled - manual entries may exist)
    crawler.export_json(args.output, manual_entries_path=args.manual)

    # Show final statistics
    crawler.show_statistics()

    logger.info("Done!")


if __name__ == "__main__":
    main()
