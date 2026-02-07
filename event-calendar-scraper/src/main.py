"""Event Calendar Scraper - Scrape public event listings and create calendar.

This module provides functionality to scrape public event listings from websites,
store them in a local database, and create a local event calendar with filtering
by date, location, or category.
"""

import logging
import logging.handlers
import os
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

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class EventCalendarScraper:
    """Scrapes events from websites and manages local event calendar."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize EventCalendarScraper with configuration.

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
            "events_scraped": 0,
            "events_saved": 0,
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
        log_file = log_config.get("file", "logs/event_scraper.log")

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

        # Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                start_date TEXT NOT NULL,
                end_date TEXT,
                location TEXT,
                category TEXT,
                source_url TEXT,
                source_name TEXT,
                event_url TEXT,
                price TEXT,
                scraped_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(title, start_date, location)
            )
        """)

        # Categories table for tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                event_count INTEGER DEFAULT 0
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

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to ISO format.

        Args:
            date_str: Date string in various formats.

        Returns:
            ISO format date string or None if parsing fails.
        """
        if not date_str:
            return None

        date_str = date_str.strip()

        # Try common date formats
        date_formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d %B %Y",
            "%d %b %Y",
        ]

        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.isoformat()
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    def _extract_events_from_page(
        self, soup: BeautifulSoup, source_config: Dict
    ) -> List[Dict]:
        """Extract events from parsed HTML page.

        Args:
            soup: BeautifulSoup object of the page.
            source_config: Configuration for the event source.

        Returns:
            List of event dictionaries.
        """
        events = []
        selectors = source_config.get("selectors", {})

        event_elements = soup.select(selectors.get("event", ""))
        if not event_elements:
            logger.warning(f"No events found with selector: {selectors.get('event')}")
            return events

        for element in event_elements:
            try:
                event = {}

                # Extract title
                title_selector = selectors.get("title", "")
                if title_selector:
                    title_elem = element.select_one(title_selector)
                    event["title"] = title_elem.get_text(strip=True) if title_elem else ""
                else:
                    event["title"] = element.get_text(strip=True)

                if not event["title"]:
                    continue

                # Extract description
                desc_selector = selectors.get("description", "")
                if desc_selector:
                    desc_elem = element.select_one(desc_selector)
                    event["description"] = desc_elem.get_text(strip=True) if desc_elem else ""
                else:
                    event["description"] = ""

                # Extract start date
                date_selector = selectors.get("date", "")
                if date_selector:
                    date_elem = element.select_one(date_selector)
                    date_str = date_elem.get_text(strip=True) if date_elem else ""
                    event["start_date"] = self._parse_date(date_str)
                else:
                    event["start_date"] = None

                if not event["start_date"]:
                    # Use current date as fallback
                    event["start_date"] = datetime.now().isoformat()

                # Extract end date
                end_date_selector = selectors.get("end_date", "")
                if end_date_selector:
                    end_date_elem = element.select_one(end_date_selector)
                    end_date_str = end_date_elem.get_text(strip=True) if end_date_elem else ""
                    event["end_date"] = self._parse_date(end_date_str)
                else:
                    event["end_date"] = None

                # Extract location
                location_selector = selectors.get("location", "")
                if location_selector:
                    location_elem = element.select_one(location_selector)
                    event["location"] = location_elem.get_text(strip=True) if location_elem else ""
                else:
                    event["location"] = ""

                # Extract category
                category_selector = selectors.get("category", "")
                if category_selector:
                    category_elem = element.select_one(category_selector)
                    event["category"] = category_elem.get_text(strip=True) if category_elem else ""
                else:
                    event["category"] = source_config.get("default_category", "general")

                # Extract event URL
                url_selector = selectors.get("url", "")
                if url_selector:
                    url_elem = element.select_one(url_selector)
                    if url_elem and url_elem.get("href"):
                        event_url = url_elem["href"]
                        if not event_url.startswith("http"):
                            event_url = urljoin(source_config.get("url", ""), event_url)
                        event["event_url"] = event_url
                    else:
                        event["event_url"] = ""
                else:
                    event["event_url"] = ""

                # Extract price
                price_selector = selectors.get("price", "")
                if price_selector:
                    price_elem = element.select_one(price_selector)
                    event["price"] = price_elem.get_text(strip=True) if price_elem else ""
                else:
                    event["price"] = ""

                # Add source information
                event["source_url"] = source_config.get("url", "")
                event["source_name"] = source_config.get("name", "Unknown")

                events.append(event)

            except Exception as e:
                logger.warning(f"Error extracting event from element: {e}")
                continue

        return events

    def _scrape_source(self, source_config: Dict) -> List[Dict]:
        """Scrape events from a single source.

        Args:
            source_config: Configuration for the event source.

        Returns:
            List of event dictionaries.
        """
        url = source_config.get("url", "")
        if not url:
            logger.warning(f"Source {source_config.get('name')} has no URL")
            return []

        logger.info(f"Scraping events from: {source_config.get('name')}")

        soup = self._fetch_page(url)
        if not soup:
            return []

        events = self._extract_events_from_page(soup, source_config)
        logger.info(f"Extracted {len(events)} events from {source_config.get('name')}")

        return events

    def _save_event(self, event: Dict) -> bool:
        """Save event to database.

        Args:
            event: Event dictionary.

        Returns:
            True if saved successfully, False otherwise.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR IGNORE INTO events 
                (title, description, start_date, end_date, location, category,
                 source_url, source_name, event_url, price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.get("title", ""),
                event.get("description", ""),
                event.get("start_date", ""),
                event.get("end_date"),
                event.get("location", ""),
                event.get("category", "general"),
                event.get("source_url", ""),
                event.get("source_name", ""),
                event.get("event_url", ""),
                event.get("price", ""),
            ))

            if cursor.rowcount > 0:
                # Update category count
                category = event.get("category", "general")
                cursor.execute("""
                    INSERT OR IGNORE INTO categories (name, event_count)
                    VALUES (?, 0)
                """, (category,))

                cursor.execute("""
                    UPDATE categories 
                    SET event_count = event_count + 1
                    WHERE name = ?
                """, (category,))

                conn.commit()
                return True
            else:
                return False

        except sqlite3.Error as e:
            logger.error(f"Database error saving event: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def scrape_events(self) -> Dict[str, int]:
        """Scrape events from all configured sources.

        Returns:
            Dictionary with scraping statistics.
        """
        logger.info("Starting event scraping")

        sources = self.config.get("sources", [])
        if not sources:
            logger.warning("No event sources configured")
            return self.stats

        for source_config in sources:
            events = self._scrape_source(source_config)
            self.stats["events_scraped"] += len(events)

            saved_count = 0
            for event in events:
                if self._save_event(event):
                    saved_count += 1

            self.stats["events_saved"] += saved_count
            self.stats["sources_processed"] += 1

            logger.info(
                f"Saved {saved_count}/{len(events)} events from "
                f"{source_config.get('name')}"
            )

            # Rate limiting between sources
            delay = self.config.get("scraping", {}).get("delay_between_sources", 2)
            if delay > 0:
                time.sleep(delay)

        logger.info("Event scraping completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats

    def filter_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        location: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Dict]:
        """Filter events by date, location, or category.

        Args:
            start_date: Filter events starting from this date (ISO format).
            end_date: Filter events ending before this date (ISO format).
            location: Filter events by location (partial match).
            category: Filter events by category.

        Returns:
            List of event dictionaries.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM events WHERE 1=1"
        params = []

        if start_date:
            query += " AND start_date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND (end_date IS NULL OR end_date <= ? OR start_date <= ?)"
            params.append(end_date)
            params.append(end_date)

        if location:
            query += " AND location LIKE ?"
            params.append(f"%{location}%")

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY start_date ASC"

        try:
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            events = []
            for row in rows:
                event = dict(zip(columns, row))
                events.append(event)

            return events

        except sqlite3.Error as e:
            logger.error(f"Database error filtering events: {e}")
            return []
        finally:
            conn.close()

    def get_categories(self) -> List[str]:
        """Get list of all event categories.

        Returns:
            List of category names.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT name FROM categories ORDER BY name")
            categories = [row[0] for row in cursor.fetchall()]
            return categories
        except sqlite3.Error as e:
            logger.error(f"Database error getting categories: {e}")
            return []
        finally:
            conn.close()

    def get_locations(self) -> List[str]:
        """Get list of all event locations.

        Returns:
            List of unique location names.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT DISTINCT location FROM events WHERE location != '' ORDER BY location")
            locations = [row[0] for row in cursor.fetchall()]
            return locations
        except sqlite3.Error as e:
            logger.error(f"Database error getting locations: {e}")
            return []
        finally:
            conn.close()

    def _cleanup_old_events(self) -> None:
        """Remove old events from database based on retention policy."""
        if not self.config.get("retention", {}).get("auto_cleanup", True):
            return

        days_to_keep = self.config.get("retention", {}).get("days_to_keep", 90)
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM events
                WHERE start_date < ?
            """, (cutoff_date.isoformat(),))

            deleted_count = cursor.rowcount
            conn.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old event(s)")

        except sqlite3.Error as e:
            logger.error(f"Error cleaning up old events: {e}")
            conn.rollback()
        finally:
            conn.close()


def main() -> int:
    """Main entry point for event calendar scraper."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape public event listings and create local calendar"
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
        help="Scrape events from configured sources",
    )
    parser.add_argument(
        "-f",
        "--filter",
        action="store_true",
        help="Filter and display events",
    )
    parser.add_argument(
        "--start-date",
        help="Filter events starting from this date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        help="Filter events ending before this date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--location",
        help="Filter events by location",
    )
    parser.add_argument(
        "--category",
        help="Filter events by category",
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List all available categories",
    )
    parser.add_argument(
        "--list-locations",
        action="store_true",
        help="List all available locations",
    )

    args = parser.parse_args()

    try:
        scraper = EventCalendarScraper(config_path=args.config)

        if args.scrape:
            stats = scraper.scrape_events()
            print("\n" + "=" * 50)
            print("Scraping Summary")
            print("=" * 50)
            print(f"Sources processed: {stats['sources_processed']}")
            print(f"Events scraped: {stats['events_scraped']}")
            print(f"Events saved: {stats['events_saved']}")
            print(f"Errors: {stats['errors']}")

        if args.list_categories:
            categories = scraper.get_categories()
            print("\nAvailable Categories:")
            for category in categories:
                print(f"  - {category}")

        if args.list_locations:
            locations = scraper.get_locations()
            print("\nAvailable Locations:")
            for location in locations:
                print(f"  - {location}")

        if args.filter:
            events = scraper.filter_events(
                start_date=args.start_date,
                end_date=args.end_date,
                location=args.location,
                category=args.category,
            )

            print("\n" + "=" * 80)
            print("FILTERED EVENTS")
            print("=" * 80)
            print(f"Found {len(events)} event(s)\n")

            for event in events:
                print(f"Title: {event.get('title', 'N/A')}")
                print(f"Date: {event.get('start_date', 'N/A')}")
                if event.get("end_date"):
                    print(f"End Date: {event.get('end_date')}")
                if event.get("location"):
                    print(f"Location: {event.get('location')}")
                if event.get("category"):
                    print(f"Category: {event.get('category')}")
                if event.get("description"):
                    print(f"Description: {event.get('description')[:100]}...")
                if event.get("event_url"):
                    print(f"URL: {event.get('event_url')}")
                print("-" * 80)

        # If no action specified, do both
        if not args.scrape and not args.filter and not args.list_categories and not args.list_locations:
            stats = scraper.scrape_events()
            events = scraper.filter_events()
            print(f"\nTotal events in calendar: {len(events)}")

        # Cleanup old events
        scraper._cleanup_old_events()

        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
