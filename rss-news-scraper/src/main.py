"""RSS News Scraper - Scrape news headlines from RSS feeds.

This module provides functionality to scrape news headlines from RSS feeds,
save them to a local database, categorize by topic, and generate daily summaries.
"""

import logging
import logging.handlers
import os
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import feedparser
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class RSSNewsScraper:
    """Scrapes news from RSS feeds and stores in database."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize RSSNewsScraper with configuration.

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
            "feeds_processed": 0,
            "headlines_scraped": 0,
            "headlines_saved": 0,
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
        if os.getenv("SCRAPING_INTERVAL"):
            config["scraping"]["interval"] = int(os.getenv("SCRAPING_INTERVAL"))

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/rss_scraper.log")

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

        # Headlines table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS headlines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                link TEXT NOT NULL UNIQUE,
                description TEXT,
                published_date TEXT,
                feed_name TEXT,
                feed_url TEXT,
                category TEXT,
                scraped_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Categories table for tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                headline_count INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()
        logger.debug("Database tables created/verified")

    def _categorize_headline(self, title: str, description: str = "") -> str:
        """Categorize headline based on keywords.

        Args:
            title: Headline title.
            description: Headline description (optional).

        Returns:
            Category name.
        """
        if not self.config.get("categorization", {}).get("enabled", True):
            return self.config.get("categorization", {}).get("default_category", "general")

        text = f"{title} {description}".lower()
        categories = self.config.get("categorization", {}).get("categories", {})

        # Check each category's keywords
        for category_name, category_config in categories.items():
            keywords = category_config.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in text:
                    return category_name

        return self.config.get("categorization", {}).get("default_category", "general")

    def _parse_feed(self, feed_url: str, feed_name: str) -> List[Dict]:
        """Parse RSS feed and extract headlines.

        Args:
            feed_url: URL of RSS feed.
            feed_name: Name of the feed source.

        Returns:
            List of headline dictionaries.
        """
        headlines = []
        scraping_config = self.config.get("scraping", {})
        max_items = scraping_config.get("max_items_per_feed", 50)
        timeout = scraping_config.get("timeout", 30)
        user_agent = scraping_config.get("user_agent", "RSS-News-Scraper/1.0")

        try:
            # Parse feed with custom user agent
            feed = feedparser.parse(
                feed_url,
                agent=user_agent,
            )

            if feed.bozo and feed.bozo_exception:
                logger.warning(
                    f"Feed parsing warning for {feed_name}: {feed.bozo_exception}"
                )

            items = feed.entries[:max_items]

            for item in items:
                headline = {
                    "title": getattr(item, "title", "").strip(),
                    "link": getattr(item, "link", "").strip(),
                    "description": getattr(item, "description", "").strip()
                    if hasattr(item, "description")
                    else "",
                    "published_date": self._parse_published_date(item),
                    "feed_name": feed_name,
                    "feed_url": feed_url,
                }

                # Categorize headline
                headline["category"] = self._categorize_headline(
                    headline["title"], headline["description"]
                )

                headlines.append(headline)

            logger.info(
                f"Parsed {len(headlines)} headlines from {feed_name}"
            )

        except Exception as e:
            logger.error(f"Error parsing feed {feed_name} ({feed_url}): {e}")
            self.stats["errors"] += 1

        return headlines

    def _parse_published_date(self, item) -> Optional[str]:
        """Parse published date from feed item.

        Args:
            item: Feed item object.

        Returns:
            ISO format date string or None.
        """
        if hasattr(item, "published_parsed") and item.published_parsed:
            try:
                dt = datetime(*item.published_parsed[:6])
                return dt.isoformat()
            except Exception:
                pass

        if hasattr(item, "published"):
            try:
                # Try to parse common date formats
                date_str = item.published
                # feedparser usually handles this, but fallback if needed
                return date_str
            except Exception:
                pass

        return None

    def _save_headline(self, headline: Dict) -> bool:
        """Save headline to database.

        Args:
            headline: Headline dictionary.

        Returns:
            True if saved successfully, False otherwise.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR IGNORE INTO headlines 
                (title, link, description, published_date, feed_name, feed_url, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                headline["title"],
                headline["link"],
                headline["description"],
                headline["published_date"],
                headline["feed_name"],
                headline["feed_url"],
                headline["category"],
            ))

            if cursor.rowcount > 0:
                # Update category count
                cursor.execute("""
                    INSERT OR IGNORE INTO categories (name, headline_count)
                    VALUES (?, 0)
                """, (headline["category"],))

                cursor.execute("""
                    UPDATE categories 
                    SET headline_count = headline_count + 1
                    WHERE name = ?
                """, (headline["category"],))

                conn.commit()
                return True
            else:
                # Duplicate entry (link already exists)
                return False

        except sqlite3.Error as e:
            logger.error(f"Database error saving headline: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def _cleanup_old_entries(self) -> None:
        """Remove old entries from database based on retention policy."""
        if not self.config.get("retention", {}).get("auto_cleanup", True):
            return

        days_to_keep = self.config.get("retention", {}).get("days_to_keep", 30)
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM headlines
                WHERE scraped_at < ?
            """, (cutoff_date.isoformat(),))

            deleted_count = cursor.rowcount
            conn.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old headline(s)")

        except sqlite3.Error as e:
            logger.error(f"Error cleaning up old entries: {e}")
            conn.rollback()
        finally:
            conn.close()

    def scrape_feeds(self) -> Dict[str, int]:
        """Scrape all configured RSS feeds.

        Returns:
            Dictionary with scraping statistics.
        """
        logger.info("Starting RSS feed scraping")

        feeds = self.config.get("rss_feeds", [])
        if not feeds:
            logger.warning("No RSS feeds configured")
            return self.stats

        for feed_config in feeds:
            feed_name = feed_config.get("name", "Unknown")
            feed_url = feed_config.get("url", "")

            if not feed_url:
                logger.warning(f"Feed {feed_name} has no URL, skipping")
                continue

            logger.info(f"Scraping feed: {feed_name}")

            # Parse feed
            headlines = self._parse_feed(feed_url, feed_name)
            self.stats["headlines_scraped"] += len(headlines)

            # Save headlines
            saved_count = 0
            for headline in headlines:
                if self._save_headline(headline):
                    saved_count += 1

            self.stats["headlines_saved"] += saved_count
            self.stats["feeds_processed"] += 1

            logger.info(
                f"Saved {saved_count}/{len(headlines)} headlines from {feed_name}"
            )

        # Cleanup old entries
        self._cleanup_old_entries()

        logger.info("RSS feed scraping completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats

    def generate_daily_summary(self, date: Optional[datetime] = None) -> str:
        """Generate daily summary of headlines.

        Args:
            date: Date to generate summary for (default: today).

        Returns:
            Summary text.
        """
        if not self.config.get("daily_summary", {}).get("enabled", True):
            return ""

        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        summary_lines = []

        # Get headline count by category
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM headlines
            WHERE scraped_at >= ? AND scraped_at < ?
            GROUP BY category
            ORDER BY count DESC
        """, (start_date.isoformat(), end_date.isoformat()))

        category_counts = cursor.fetchall()

        # Summary header
        summary_lines.append("=" * 60)
        summary_lines.append(f"Daily News Summary - {date_str}")
        summary_lines.append("=" * 60)
        summary_lines.append("")

        # Category breakdown
        if self.config.get("daily_summary", {}).get("include_categories", True):
            summary_lines.append("Category Breakdown:")
            summary_lines.append("-" * 60)
            total_headlines = 0
            for category, count in category_counts:
                summary_lines.append(f"  {category.capitalize()}: {count}")
                total_headlines += count
            summary_lines.append(f"\nTotal Headlines: {total_headlines}")
            summary_lines.append("")

        # Top headlines by category
        if self.config.get("daily_summary", {}).get("include_top_headlines", True):
            top_count = self.config.get("daily_summary", {}).get("top_headlines_count", 5)

            for category, _ in category_counts:
                cursor.execute("""
                    SELECT title, link, feed_name
                    FROM headlines
                    WHERE category = ? 
                    AND scraped_at >= ? AND scraped_at < ?
                    ORDER BY scraped_at DESC
                    LIMIT ?
                """, (category, start_date.isoformat(), end_date.isoformat(), top_count))

                headlines = cursor.fetchall()

                if headlines:
                    summary_lines.append(f"\n{category.capitalize()} - Top Headlines:")
                    summary_lines.append("-" * 60)
                    for i, (title, link, feed_name) in enumerate(headlines, 1):
                        summary_lines.append(f"{i}. {title}")
                        summary_lines.append(f"   Source: {feed_name}")
                        summary_lines.append(f"   Link: {link}")
                        summary_lines.append("")

        conn.close()

        summary_text = "\n".join(summary_lines)

        # Save summary to file
        summary_config = self.config.get("daily_summary", {})
        output_file = summary_config.get("output_file", f"logs/daily_summary_{date_str}.txt")
        output_file = output_file.replace("{date}", date_str)

        output_path = Path(output_file)
        if not output_path.is_absolute():
            project_root = Path(__file__).parent.parent
            output_path = project_root / output_file

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(summary_text)

        logger.info(f"Daily summary saved to: {output_path}")

        return summary_text


def main() -> int:
    """Main entry point for RSS news scraper."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape news headlines from RSS feeds"
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
        help="Scrape RSS feeds",
    )
    parser.add_argument(
        "-g",
        "--generate-summary",
        action="store_true",
        help="Generate daily summary",
    )
    parser.add_argument(
        "-d",
        "--date",
        help="Date for summary (YYYY-MM-DD), defaults to today",
    )

    args = parser.parse_args()

    try:
        scraper = RSSNewsScraper(config_path=args.config)

        if args.scrape:
            stats = scraper.scrape_feeds()
            print("\n" + "=" * 50)
            print("Scraping Summary")
            print("=" * 50)
            print(f"Feeds processed: {stats['feeds_processed']}")
            print(f"Headlines scraped: {stats['headlines_scraped']}")
            print(f"Headlines saved: {stats['headlines_saved']}")
            print(f"Errors: {stats['errors']}")

        if args.generate_summary:
            summary_date = None
            if args.date:
                try:
                    summary_date = datetime.strptime(args.date, "%Y-%m-%d")
                except ValueError:
                    logger.error(f"Invalid date format: {args.date}")
                    return 1

            summary = scraper.generate_daily_summary(summary_date)
            print("\n" + summary)

        # If no action specified, do both
        if not args.scrape and not args.generate_summary:
            stats = scraper.scrape_feeds()
            summary = scraper.generate_daily_summary()
            print("\n" + "=" * 50)
            print("Scraping Summary")
            print("=" * 50)
            print(f"Feeds processed: {stats['feeds_processed']}")
            print(f"Headlines scraped: {stats['headlines_scraped']}")
            print(f"Headlines saved: {stats['headlines_saved']}")
            print(f"\n{summary}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
