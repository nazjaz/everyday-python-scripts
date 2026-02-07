"""Inspirational Quote Scraper - Scrape and display daily inspirational quotes.

This module provides functionality to scrape public domain quotes from websites,
store them in a local database, display daily inspirational quotes, and send
desktop notifications.
"""

import logging
import logging.handlers
import os
import random
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
import yaml
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from plyer import notification

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class QuoteScraper:
    """Scrapes quotes from websites and stores them in database."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize QuoteScraper with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_database()
        self.stats = {
            "sources_processed": 0,
            "quotes_scraped": 0,
            "quotes_saved": 0,
            "errors": 0,
        }

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Configuration dictionary.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid.
        """
        config_file = Path(config_path)

        if not config_file.is_absolute():
            if not config_file.exists():
                parent_config = Path(__file__).parent.parent / config_path
                if parent_config.exists():
                    config_file = parent_config
                else:
                    cwd_config = Path.cwd() / config_path
                    if cwd_config.exists():
                        config_file = cwd_config

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Override with environment variables if present
        if os.getenv("DATABASE_FILE"):
            config["database"]["file"] = os.getenv("DATABASE_FILE")
        if os.getenv("SCRAPING_TIMEOUT"):
            config["scraping"]["timeout"] = int(os.getenv("SCRAPING_TIMEOUT"))

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/quote_scraper.log")

        log_path = Path(log_file)
        if not log_path.is_absolute():
            project_root = Path(__file__).parent.parent
            log_path = project_root / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.handlers.clear()

        file_handler = logging.handlers.RotatingFileHandler(
            str(log_path),
            maxBytes=log_config.get("max_bytes", 10485760),
            backupCount=log_config.get("backup_count", 5),
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            log_config.get(
                "format",
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter("%(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        logger.info("Logging configured successfully")

    def _setup_database(self) -> None:
        """Set up SQLite database and create tables if needed."""
        db_file = self.config["database"]["file"]
        db_path = Path(db_file)
        if not db_path.is_absolute():
            project_root = Path(__file__).parent.parent
            db_path = project_root / db_file

        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path

        if self.config["database"].get("create_tables", True):
            self._create_tables()

        logger.info(f"Database initialized: {db_path}")

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Quotes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                author TEXT,
                source_url TEXT,
                source_name TEXT,
                category TEXT,
                scraped_at TEXT DEFAULT CURRENT_TIMESTAMP,
                displayed_at TEXT,
                display_count INTEGER DEFAULT 0
            )
        """)

        # Daily quotes tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_id INTEGER NOT NULL,
                display_date TEXT NOT NULL UNIQUE,
                FOREIGN KEY (quote_id) REFERENCES quotes(id)
            )
        """)

        conn.commit()
        conn.close()
        logger.debug("Database tables created/verified")

    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse HTML page.

        Args:
            url: URL to fetch.

        Returns:
            BeautifulSoup object or None if fetch fails.
        """
        scraping_config = self.config.get("scraping", {})
        timeout = scraping_config.get("timeout", 30)
        user_agent = scraping_config.get(
            "user_agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )

        headers = {"User-Agent": user_agent}

        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, "html.parser")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            self.stats["errors"] += 1
            return None

    def _extract_quotes_from_page(
        self, soup: BeautifulSoup, source_config: Dict
    ) -> List[Dict]:
        """Extract quotes from parsed HTML page.

        Args:
            soup: BeautifulSoup object of the page.
            source_config: Configuration for the quote source.

        Returns:
            List of quote dictionaries.
        """
        quotes = []
        selectors = source_config.get("selectors", {})

        quote_elements = soup.select(selectors.get("quote", ""))
        if not quote_elements:
            logger.warning(f"No quotes found with selector: {selectors.get('quote')}")
            return quotes

        for element in quote_elements:
            try:
                quote_text = self._extract_text(element, selectors.get("text", ""))
                if not quote_text:
                    continue

                author = self._extract_text(element, selectors.get("author", ""))
                category = source_config.get("category", "general")

                quote = {
                    "text": quote_text.strip(),
                    "author": author.strip() if author else None,
                    "source_url": source_config.get("url", ""),
                    "source_name": source_config.get("name", "Unknown"),
                    "category": category,
                }

                # Validate quote text length
                min_length = self.config.get("scraping", {}).get("min_quote_length", 10)
                max_length = self.config.get("scraping", {}).get("max_quote_length", 500)
                if min_length <= len(quote["text"]) <= max_length:
                    quotes.append(quote)
                else:
                    logger.debug(
                        f"Quote length {len(quote['text'])} outside range, skipping"
                    )

            except Exception as e:
                logger.warning(f"Error extracting quote from element: {e}")
                continue

        return quotes

    def _extract_text(self, element, selector: str) -> str:
        """Extract text from element using selector.

        Args:
            element: BeautifulSoup element.
            selector: CSS selector string.

        Returns:
            Extracted text or empty string.
        """
        if not selector:
            return element.get_text(strip=True)

        sub_element = element.select_one(selector)
        if sub_element:
            return sub_element.get_text(strip=True)

        return ""

    def _scrape_source(self, source_config: Dict) -> List[Dict]:
        """Scrape quotes from a single source.

        Args:
            source_config: Configuration for the quote source.

        Returns:
            List of quote dictionaries.
        """
        url = source_config.get("url", "")
        if not url:
            logger.warning(f"Source {source_config.get('name')} has no URL")
            return []

        logger.info(f"Scraping quotes from: {source_config.get('name')}")

        soup = self._fetch_page(url)
        if not soup:
            return []

        quotes = self._extract_quotes_from_page(soup, source_config)
        logger.info(f"Extracted {len(quotes)} quotes from {source_config.get('name')}")

        return quotes

    def _save_quote(self, quote: Dict) -> bool:
        """Save quote to database.

        Args:
            quote: Quote dictionary.

        Returns:
            True if saved successfully, False otherwise.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Check if quote already exists (by text and author)
            cursor.execute("""
                SELECT id FROM quotes
                WHERE text = ? AND (author = ? OR (author IS NULL AND ? IS NULL))
            """, (quote["text"], quote["author"], quote["author"]))

            existing = cursor.fetchone()

            if existing:
                return False

            cursor.execute("""
                INSERT INTO quotes (text, author, source_url, source_name, category)
                VALUES (?, ?, ?, ?, ?)
            """, (
                quote["text"],
                quote["author"],
                quote["source_url"],
                quote["source_name"],
                quote["category"],
            ))

            conn.commit()
            return True

        except sqlite3.Error as e:
            logger.error(f"Database error saving quote: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def scrape_quotes(self) -> Dict[str, int]:
        """Scrape quotes from all configured sources.

        Returns:
            Dictionary with scraping statistics.
        """
        logger.info("Starting quote scraping")

        sources = self.config.get("sources", [])
        if not sources:
            logger.warning("No quote sources configured")
            return self.stats

        for source_config in sources:
            quotes = self._scrape_source(source_config)
            self.stats["quotes_scraped"] += len(quotes)

            saved_count = 0
            for quote in quotes:
                if self._save_quote(quote):
                    saved_count += 1

            self.stats["quotes_saved"] += saved_count
            self.stats["sources_processed"] += 1

            logger.info(
                f"Saved {saved_count}/{len(quotes)} quotes from "
                f"{source_config.get('name')}"
            )

            # Rate limiting between sources
            delay = self.config.get("scraping", {}).get("delay_between_sources", 2)
            if delay > 0:
                time.sleep(delay)

        logger.info("Quote scraping completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats

    def get_daily_quote(self, date: Optional[datetime] = None) -> Optional[Dict]:
        """Get or assign daily quote for a specific date.

        Args:
            date: Date to get quote for (default: today).

        Returns:
            Quote dictionary or None if no quotes available.
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Check if quote already assigned for this date
            cursor.execute("""
                SELECT q.id, q.text, q.author, q.category, q.source_name
                FROM quotes q
                JOIN daily_quotes dq ON q.id = dq.quote_id
                WHERE dq.display_date = ?
            """, (date_str,))

            existing = cursor.fetchone()

            if existing:
                quote_id, text, author, category, source_name = existing
                # Update display count
                cursor.execute("""
                    UPDATE quotes
                    SET display_count = display_count + 1,
                        displayed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (quote_id,))
                conn.commit()

                return {
                    "id": quote_id,
                    "text": text,
                    "author": author,
                    "category": category,
                    "source_name": source_name,
                }

            # Assign new quote for this date
            # Get quotes that haven't been displayed recently
            days_to_avoid = self.config.get("display", {}).get("recent_days_avoid", 30)
            cutoff_date = (date - timedelta(days=days_to_avoid)).strftime("%Y-%m-%d")

            cursor.execute("""
                SELECT q.id, q.text, q.author, q.category, q.source_name
                FROM quotes q
                LEFT JOIN daily_quotes dq ON q.id = dq.quote_id
                WHERE dq.display_date IS NULL OR dq.display_date < ?
                ORDER BY RANDOM()
                LIMIT 1
            """, (cutoff_date,))

            quote_data = cursor.fetchone()

            if not quote_data:
                # Fallback: get any random quote
                cursor.execute("""
                    SELECT id, text, author, category, source_name
                    FROM quotes
                    ORDER BY RANDOM()
                    LIMIT 1
                """)
                quote_data = cursor.fetchone()

            if quote_data:
                quote_id, text, author, category, source_name = quote_data

                # Save daily quote assignment
                cursor.execute("""
                    INSERT OR REPLACE INTO daily_quotes (quote_id, display_date)
                    VALUES (?, ?)
                """, (quote_id, date_str))

                # Update quote display stats
                cursor.execute("""
                    UPDATE quotes
                    SET display_count = display_count + 1,
                        displayed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (quote_id,))

                conn.commit()

                return {
                    "id": quote_id,
                    "text": text,
                    "author": author,
                    "category": category,
                    "source_name": source_name,
                }

            return None

        except sqlite3.Error as e:
            logger.error(f"Database error getting daily quote: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def display_quote(self, quote: Dict) -> None:
        """Display quote in console and send desktop notification.

        Args:
            quote: Quote dictionary.
        """
        print("\n" + "=" * 70)
        print("DAILY INSPIRATIONAL QUOTE")
        print("=" * 70)
        print(f"\n{quote['text']}\n")
        if quote.get("author"):
            print(f"  - {quote['author']}")
        if quote.get("category"):
            print(f"  Category: {quote['category']}")
        if quote.get("source_name"):
            print(f"  Source: {quote['source_name']}")
        print("=" * 70 + "\n")

        # Send desktop notification
        if self.config.get("notifications", {}).get("enabled", True):
            self._send_notification(quote)

    def _send_notification(self, quote: Dict) -> None:
        """Send desktop notification with quote.

        Args:
            quote: Quote dictionary.
        """
        notification_config = self.config.get("notifications", {})
        title = notification_config.get("title", "Daily Inspirational Quote")

        # Truncate quote text for notification
        max_length = notification_config.get("max_length", 200)
        message = quote["text"]
        if len(message) > max_length:
            message = message[:max_length - 3] + "..."

        if quote.get("author"):
            message += f"\n\n- {quote['author']}"

        try:
            notification.notify(
                title=title,
                message=message,
                timeout=notification_config.get("timeout", 10),
                app_name=notification_config.get("app_name", "Quote Scraper"),
            )
            logger.info("Desktop notification sent successfully")
        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    def _cleanup_old_entries(self) -> None:
        """Remove old daily quote entries based on retention policy."""
        if not self.config.get("retention", {}).get("auto_cleanup", True):
            return

        days_to_keep = self.config.get("retention", {}).get("days_to_keep", 90)
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM daily_quotes
                WHERE display_date < ?
            """, (cutoff_date.strftime("%Y-%m-%d"),))

            deleted_count = cursor.rowcount
            conn.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old daily quote entry(ies)")

        except sqlite3.Error as e:
            logger.error(f"Error cleaning up old entries: {e}")
            conn.rollback()
        finally:
            conn.close()


def main() -> int:
    """Main entry point for inspirational quote scraper."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape and display daily inspirational quotes"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-s",
        "--scrape",
        action="store_true",
        help="Scrape quotes from configured sources",
    )
    parser.add_argument(
        "-d",
        "--display",
        action="store_true",
        help="Display daily inspirational quote",
    )
    parser.add_argument(
        "--date",
        help="Date for quote display (YYYY-MM-DD), defaults to today",
    )

    args = parser.parse_args()

    try:
        scraper = QuoteScraper(config_path=args.config)

        if args.scrape:
            stats = scraper.scrape_quotes()
            print("\n" + "=" * 50)
            print("Scraping Summary")
            print("=" * 50)
            print(f"Sources processed: {stats['sources_processed']}")
            print(f"Quotes scraped: {stats['quotes_scraped']}")
            print(f"Quotes saved: {stats['quotes_saved']}")
            print(f"Errors: {stats['errors']}")

        if args.display:
            quote_date = None
            if args.date:
                try:
                    quote_date = datetime.strptime(args.date, "%Y-%m-%d")
                except ValueError:
                    logger.error(f"Invalid date format: {args.date}")
                    return 1

            quote = scraper.get_daily_quote(quote_date)
            if quote:
                scraper.display_quote(quote)
            else:
                logger.warning("No quotes available. Run with --scrape first.")
                print("No quotes available. Please scrape quotes first using --scrape")
                return 1

        # If no action specified, do both
        if not args.scrape and not args.display:
            stats = scraper.scrape_quotes()
            quote = scraper.get_daily_quote()
            if quote:
                scraper.display_quote(quote)
            else:
                logger.warning("No quotes available after scraping")
                print("No quotes were scraped. Check your configuration.")

        # Cleanup old entries
        scraper._cleanup_old_entries()

        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
