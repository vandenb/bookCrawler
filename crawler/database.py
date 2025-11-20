"""
SQLite database operations for storing and exporting bookstore data.
"""

import sqlite3
import json
import logging
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path

from config import BOOK_CONFIG

logger = logging.getLogger(__name__)


class BookstoreDatabase:
    """
    Handles SQLite database operations for bookstore data.
    """

    def __init__(self, db_path: str):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Create tables if they don't exist
        self._init_database()

    def _init_database(self):
        """
        Create database tables if they don't exist.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Bookstores table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookstores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    homepage_url TEXT NOT NULL UNIQUE,
                    product_url TEXT,
                    postal_code TEXT,
                    city TEXT,
                    crawled_at TIMESTAMP,
                    success BOOLEAN,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Metadata table (for tracking crawl runs)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crawl_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_title TEXT NOT NULL,
                    book_author TEXT NOT NULL,
                    book_isbn TEXT,
                    crawl_started_at TIMESTAMP,
                    crawl_completed_at TIMESTAMP,
                    total_bookstores INTEGER,
                    successful_crawls INTEGER,
                    failed_crawls INTEGER
                )
            """)

            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    def start_crawl_run(self) -> int:
        """
        Record the start of a new crawl run.

        Returns:
            ID of the crawl run
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO crawl_metadata
                (book_title, book_author, book_isbn, crawl_started_at)
                VALUES (?, ?, ?, ?)
            """, (
                BOOK_CONFIG["title"],
                BOOK_CONFIG["author"],
                BOOK_CONFIG["isbn"],
                datetime.now()
            ))

            conn.commit()
            return cursor.lastrowid

    def complete_crawl_run(
        self,
        run_id: int,
        total_bookstores: int,
        successful_crawls: int,
        failed_crawls: int
    ):
        """
        Mark a crawl run as completed.

        Args:
            run_id: ID of the crawl run
            total_bookstores: Total number of bookstores processed
            successful_crawls: Number of successful crawls
            failed_crawls: Number of failed crawls
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE crawl_metadata
                SET crawl_completed_at = ?,
                    total_bookstores = ?,
                    successful_crawls = ?,
                    failed_crawls = ?
                WHERE id = ?
            """, (
                datetime.now(),
                total_bookstores,
                successful_crawls,
                failed_crawls,
                run_id
            ))

            conn.commit()

    def upsert_bookstore(
        self,
        name: str,
        homepage_url: str,
        product_url: Optional[str] = None,
        postal_code: Optional[str] = None,
        city: Optional[str] = None,
        success: bool = False,
        error_message: Optional[str] = None
    ) -> int:
        """
        Insert or update a bookstore record.

        Args:
            name: Bookstore name
            homepage_url: Homepage URL
            product_url: Product page URL (if found)
            postal_code: Postal code (if found)
            city: City name (if found)
            success: Whether the crawl was successful
            error_message: Error message (if failed)

        Returns:
            ID of the inserted/updated record
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check if bookstore exists
            cursor.execute("""
                SELECT id FROM bookstores WHERE homepage_url = ?
            """, (homepage_url,))

            existing = cursor.fetchone()

            now = datetime.now()

            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE bookstores
                    SET name = ?,
                        product_url = ?,
                        postal_code = ?,
                        city = ?,
                        crawled_at = ?,
                        success = ?,
                        error_message = ?,
                        updated_at = ?
                    WHERE homepage_url = ?
                """, (
                    name,
                    product_url,
                    postal_code,
                    city,
                    now,
                    success,
                    error_message,
                    now,
                    homepage_url
                ))

                bookstore_id = existing[0]
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO bookstores
                    (name, homepage_url, product_url, postal_code, city,
                     crawled_at, success, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    name,
                    homepage_url,
                    product_url,
                    postal_code,
                    city,
                    now,
                    success,
                    error_message
                ))

                bookstore_id = cursor.lastrowid

            conn.commit()
            return bookstore_id

    def get_successful_bookstores(self) -> List[Dict]:
        """
        Get all bookstores with successful crawls (have product URL and postal code).

        Returns:
            List of bookstore dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    name,
                    homepage_url,
                    product_url,
                    postal_code,
                    city,
                    crawled_at
                FROM bookstores
                WHERE success = 1
                  AND product_url IS NOT NULL
                  AND postal_code IS NOT NULL
                ORDER BY city, name
            """)

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_all_bookstores(self) -> List[Dict]:
        """
        Get all bookstores, including failed ones.

        Returns:
            List of bookstore dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    name,
                    homepage_url,
                    product_url,
                    postal_code,
                    city,
                    success,
                    error_message,
                    crawled_at
                FROM bookstores
                ORDER BY success DESC, city, name
            """)

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def export_to_json(self, output_path: str, manual_entries_path: str = None) -> int:
        """
        Export successful bookstores to JSON file, including manual entries.

        Args:
            output_path: Path to output JSON file
            manual_entries_path: Optional path to CSV with manual entries

        Returns:
            Number of bookstores exported
        """
        import csv

        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        bookstores = self.get_successful_bookstores()

        # Load manual entries if provided
        manual_entries = []
        if manual_entries_path and Path(manual_entries_path).exists():
            try:
                with open(manual_entries_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Skip comment lines (name starts with #)
                        if row.get("name", "").strip().startswith("#"):
                            continue
                        if row.get("name") and row.get("product_url"):
                            manual_entries.append({
                                "name": row["name"].strip(),
                                "product_url": row["product_url"].strip(),
                                "postal_code": row.get("postal_code", "").strip(),
                                "city": row.get("city", "").strip(),
                                "crawled_at": "manual"
                            })
                logger.info(f"Loaded {len(manual_entries)} manual entries from {manual_entries_path}")
            except Exception as e:
                logger.warning(f"Could not load manual entries: {e}")

        # Combine crawled and manual entries
        all_bookstores = bookstores + manual_entries

        # Remove duplicates (prefer manual entries over crawled)
        seen_names = set()
        unique_bookstores = []

        # First add manual entries (they take precedence)
        for b in manual_entries:
            if b["name"] not in seen_names:
                seen_names.add(b["name"])
                unique_bookstores.append(b)

        # Then add crawled entries (skip if already in manual)
        for b in bookstores:
            if b["name"] not in seen_names:
                seen_names.add(b["name"])
                unique_bookstores.append(b)

        # Sort by city, then name
        unique_bookstores.sort(key=lambda x: (x.get("city", ""), x.get("name", "")))

        # Build JSON structure
        data = {
            "metadata": {
                "book_title": BOOK_CONFIG["title"],
                "book_author": BOOK_CONFIG["author"],
                "book_isbn": BOOK_CONFIG["isbn"],
                "last_updated": datetime.now().isoformat(),
                "total_bookstores": len(unique_bookstores),
                "crawled_count": len(bookstores),
                "manual_count": len(manual_entries)
            },
            "bookstores": [
                {
                    "name": b["name"],
                    "product_url": b["product_url"],
                    "postal_code": b["postal_code"],
                    "city": b["city"],
                    "source": "manual" if b.get("crawled_at") == "manual" else "crawled"
                }
                for b in unique_bookstores
            ]
        }

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Exported {len(unique_bookstores)} bookstores to {output_path} ({len(bookstores)} crawled, {len(manual_entries)} manual)")
        return len(unique_bookstores)

    def get_statistics(self) -> Dict:
        """
        Get statistics about the database.

        Returns:
            Dictionary with statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            stats = {}

            # Total bookstores
            cursor.execute("SELECT COUNT(*) FROM bookstores")
            stats["total_bookstores"] = cursor.fetchone()[0]

            # Successful crawls
            cursor.execute("SELECT COUNT(*) FROM bookstores WHERE success = 1")
            stats["successful_crawls"] = cursor.fetchone()[0]

            # With product URL
            cursor.execute("SELECT COUNT(*) FROM bookstores WHERE product_url IS NOT NULL")
            stats["with_product_url"] = cursor.fetchone()[0]

            # With postal code
            cursor.execute("SELECT COUNT(*) FROM bookstores WHERE postal_code IS NOT NULL")
            stats["with_postal_code"] = cursor.fetchone()[0]

            # Complete records (product URL + postal code)
            cursor.execute("""
                SELECT COUNT(*) FROM bookstores
                WHERE product_url IS NOT NULL AND postal_code IS NOT NULL
            """)
            stats["complete_records"] = cursor.fetchone()[0]

            # Last crawl
            cursor.execute("""
                SELECT MAX(crawl_started_at) FROM crawl_metadata
            """)
            last_crawl = cursor.fetchone()[0]
            stats["last_crawl"] = last_crawl

            return stats

    def close(self):
        """
        Close database connection (not needed with context manager, but here for completeness).
        """
        pass
