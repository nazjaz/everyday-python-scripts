"""Historical Events Database - CLI tool for scraping and searching historical data.

This module provides a command-line tool for scraping public domain historical
data and creating a local searchable database of historical events searchable
by date, location, or topic.
"""

import argparse
import logging
import logging.handlers
import re
import sqlite3
import sys
import time
from datetime import datetime
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


class HistoricalDataScraper:
    """Scrapes historical data from public domain sources."""

    def __init__(self, config: Dict) -> None:
        """Initialize HistoricalDataScraper.

        Args:
            config: Configuration dictionary containing scraping settings.
        """
        self.config = config
        self.sources_config = config.get("sources", {})
        self.scraping_config = config.get("scraping", {})

        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (compatible; HistoricalDataScraper/1.0)"
            }
        )

        # Rate limiting
        self.request_delay = self.scraping_config.get("request_delay_seconds", 2)

    def _make_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Make HTTP request with retry logic and rate limiting.

        Args:
            url: URL to request.
            max_retries: Maximum number of retry attempts.

        Returns:
            Response object if successful, None otherwise.
        """
        time.sleep(self.request_delay)

        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{max_retries}): {url} - {e}",
                    extra={"url": url, "attempt": attempt + 1, "error": str(e)},
                )
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(
                        f"Failed to fetch {url} after {max_retries} attempts",
                        extra={"url": url, "error": str(e)},
                    )
        return None

    def _parse_date(self, date_text: str) -> Optional[Tuple[int, int, int]]:
        """Parse date from text.

        Args:
            date_text: Text containing date information.

        Returns:
            Tuple of (year, month, day) or None if cannot parse.
        """
        # Try various date formats
        date_patterns = [
            r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})",  # YYYY-MM-DD or YYYY/MM/DD
            r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})",  # MM-DD-YYYY or MM/DD/YYYY
            r"(\d{4})\s+(\w+)\s+(\d{1,2})",  # YYYY Month DD
            r"(\d{4})",  # Just year
        ]

        for pattern in date_patterns:
            match = re.search(pattern, date_text)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    try:
                        year = int(groups[0])
                        month = int(groups[1])
                        day = int(groups[2])
                        # Handle year in different positions
                        if year < 100:  # Likely day or month
                            if len(groups[0]) == 4:  # Last group is year
                                year = int(groups[2])
                                month = int(groups[0])
                                day = int(groups[1])
                        return (year, month, day)
                    except (ValueError, IndexError):
                        continue
                elif len(groups) == 1:
                    try:
                        year = int(groups[0])
                        return (year, 1, 1)  # Default to January 1
                    except ValueError:
                        continue

        return None

    def scrape_wikipedia_events(self, limit: int = 50) -> List[Dict]:
        """Scrape historical events from Wikipedia.

        Args:
            limit: Maximum number of events to scrape.

        Returns:
            List of event dictionaries.
        """
        events = []
        base_url = "https://en.wikipedia.org"

        try:
            # Wikipedia "On this day" or historical events pages
            events_url = f"{base_url}/wiki/Portal:Current_events"
            response = self._make_request(events_url)

            if not response:
                # Try alternative: List of years
                events_url = f"{base_url}/wiki/List_of_years"
                response = self._make_request(events_url)

            if not response:
                return events

            soup = BeautifulSoup(response.content, "html.parser")

            # Look for date-based event listings
            # This is a simplified parser - Wikipedia structure varies
            date_sections = soup.find_all(["h2", "h3"], string=re.compile(r"\d{4}"))

            for section in date_sections[:limit]:
                try:
                    # Extract date from section heading
                    date_text = section.get_text()
                    parsed_date = self._parse_date(date_text)

                    if not parsed_date:
                        continue

                    year, month, day = parsed_date

                    # Find event descriptions in following content
                    content = section.find_next_sibling()
                    if content:
                        event_text = content.get_text()[:500]  # Limit length

                        # Extract location if mentioned
                        location = self._extract_location(event_text)

                        # Extract topic/keywords
                        topic = self._extract_topic(event_text)

                        events.append(
                            {
                                "date": f"{year:04d}-{month:02d}-{day:02d}",
                                "year": year,
                                "month": month,
                                "day": day,
                                "description": event_text.strip(),
                                "location": location,
                                "topic": topic,
                                "source": "wikipedia",
                                "url": urljoin(base_url, section.find("a")["href"])
                                if section.find("a")
                                else events_url,
                            }
                        )

                        logger.info(
                            f"Scraped event: {date_text}",
                            extra={"date": f"{year}-{month}-{day}"},
                        )

                except Exception as e:
                    logger.warning(
                        f"Error parsing Wikipedia section: {e}",
                        extra={"error": str(e)},
                    )
                    continue

        except Exception as e:
            logger.error(
                f"Error accessing Wikipedia: {e}",
                extra={"error": str(e)},
            )

        return events

    def scrape_custom_source(self, source_config: Dict) -> List[Dict]:
        """Scrape historical events from a custom source.

        Args:
            source_config: Source configuration dictionary.

        Returns:
            List of event dictionaries.
        """
        events = []
        base_url = source_config.get("base_url", "")
        list_url = source_config.get("list_url", "")

        if not base_url or not list_url:
            return events

        try:
            response = self._make_request(list_url)
            if not response:
                return events

            soup = BeautifulSoup(response.content, "html.parser")

            # Generic parsing - would need customization per source
            event_elements = soup.find_all(
                source_config.get("event_selector", "div"), class_=re.compile("event")
            )

            limit = source_config.get("limit", 50)
            for element in event_elements[:limit]:
                try:
                    # Extract date
                    date_elem = element.find(source_config.get("date_selector", "span"))
                    date_text = date_elem.get_text() if date_elem else ""
                    parsed_date = self._parse_date(date_text)

                    if not parsed_date:
                        continue

                    year, month, day = parsed_date

                    # Extract description
                    desc_elem = element.find(
                        source_config.get("description_selector", "p")
                    )
                    description = desc_elem.get_text() if desc_elem else ""

                    location = self._extract_location(description)
                    topic = self._extract_topic(description)

                    events.append(
                        {
                            "date": f"{year:04d}-{month:02d}-{day:02d}",
                            "year": year,
                            "month": month,
                            "day": day,
                            "description": description.strip(),
                            "location": location,
                            "topic": topic,
                            "source": source_config.get("name", "custom"),
                            "url": list_url,
                        }
                    )

                except Exception as e:
                    logger.warning(
                        f"Error parsing custom source event: {e}",
                        extra={"error": str(e)},
                    )
                    continue

        except Exception as e:
            logger.error(
                f"Error accessing custom source: {e}",
                extra={"error": str(e)},
            )

        return events

    def _extract_location(self, text: str) -> str:
        """Extract location from text.

        Args:
            text: Text to analyze.

        Returns:
            Location string or empty string.
        """
        # Common location patterns
        location_patterns = [
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:City|State|Country|Kingdom|Empire|Republic)\b",
            r"\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b",
            r"\bat\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b",
        ]

        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return ""

    def _extract_topic(self, text: str) -> str:
        """Extract topic/keywords from text.

        Args:
            text: Text to analyze.

        Returns:
            Topic string or empty string.
        """
        # Common historical topics
        topics = [
            "war",
            "battle",
            "treaty",
            "independence",
            "revolution",
            "discovery",
            "invention",
            "election",
            "coronation",
            "death",
            "birth",
        ]

        text_lower = text.lower()
        for topic in topics:
            if topic in text_lower:
                return topic

        return "general"


class HistoricalDatabase:
    """Manages the historical events database."""

    def __init__(self, db_path: Path) -> None:
        """Initialize HistoricalDatabase.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                day INTEGER NOT NULL,
                description TEXT NOT NULL,
                location TEXT,
                topic TEXT,
                source TEXT,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Create indexes for faster searching
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_date ON events(date)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_year ON events(year)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_location ON events(location)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_topic ON events(topic)"
        )

        conn.commit()
        conn.close()

    def insert_event(self, event: Dict) -> bool:
        """Insert an event into the database.

        Args:
            event: Event dictionary.

        Returns:
            True if inserted successfully, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO events 
                (date, year, month, day, description, location, topic, source, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.get("date"),
                    event.get("year"),
                    event.get("month"),
                    event.get("day"),
                    event.get("description"),
                    event.get("location"),
                    event.get("topic"),
                    event.get("source"),
                    event.get("url"),
                ),
            )

            conn.commit()
            conn.close()
            return True

        except sqlite3.Error as e:
            logger.error(
                f"Error inserting event: {e}",
                extra={"event": event, "error": str(e)},
            )
            return False

    def search_by_date(
        self, year: Optional[int] = None, month: Optional[int] = None,
        day: Optional[int] = None, date_range: Optional[Tuple[str, str]] = None
    ) -> List[Dict]:
        """Search events by date.

        Args:
            year: Year to search for.
            month: Month to search for.
            day: Day to search for.
            date_range: Tuple of (start_date, end_date) in YYYY-MM-DD format.

        Returns:
            List of matching event dictionaries.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if date_range:
                start_date, end_date = date_range
                cursor.execute(
                    "SELECT * FROM events WHERE date BETWEEN ? AND ? ORDER BY date",
                    (start_date, end_date),
                )
            elif year and month and day:
                cursor.execute(
                    "SELECT * FROM events WHERE year = ? AND month = ? AND day = ? ORDER BY date",
                    (year, month, day),
                )
            elif year and month:
                cursor.execute(
                    "SELECT * FROM events WHERE year = ? AND month = ? ORDER BY date",
                    (year, month),
                )
            elif year:
                cursor.execute(
                    "SELECT * FROM events WHERE year = ? ORDER BY date",
                    (year,),
                )
            else:
                cursor.execute("SELECT * FROM events ORDER BY date")

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Error searching by date: {e}", extra={"error": str(e)})
            return []

    def search_by_location(self, location: str) -> List[Dict]:
        """Search events by location.

        Args:
            location: Location to search for.

        Returns:
            List of matching event dictionaries.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM events WHERE location LIKE ? ORDER BY date",
                (f"%{location}%",),
            )

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(
                f"Error searching by location: {e}",
                extra={"location": location, "error": str(e)},
            )
            return []

    def search_by_topic(self, topic: str) -> List[Dict]:
        """Search events by topic.

        Args:
            topic: Topic to search for.

        Returns:
            List of matching event dictionaries.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM events WHERE topic LIKE ? OR description LIKE ? ORDER BY date",
                (f"%{topic}%", f"%{topic}%"),
            )

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(
                f"Error searching by topic: {e}",
                extra={"topic": topic, "error": str(e)},
            )
            return []

    def get_statistics(self) -> Dict:
        """Get database statistics.

        Returns:
            Dictionary with statistics.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM events")
            total_events = cursor.fetchone()[0]

            cursor.execute("SELECT MIN(year), MAX(year) FROM events")
            min_max = cursor.fetchone()
            min_year = min_max[0] if min_max[0] else 0
            max_year = min_max[1] if min_max[1] else 0

            cursor.execute(
                "SELECT COUNT(DISTINCT location) FROM events WHERE location != ''"
            )
            unique_locations = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(DISTINCT topic) FROM events WHERE topic != ''"
            )
            unique_topics = cursor.fetchone()[0]

            conn.close()

            return {
                "total_events": total_events,
                "year_range": (min_year, max_year),
                "unique_locations": unique_locations,
                "unique_topics": unique_topics,
            }

        except sqlite3.Error as e:
            logger.error(f"Error getting statistics: {e}", extra={"error": str(e)})
            return {}


class HistoricalEventsManager:
    """Main class for managing historical events database."""

    def __init__(self, config: Dict) -> None:
        """Initialize HistoricalEventsManager.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.database_config = config.get("database", {})

        # Setup logging
        self._setup_logging()

        # Initialize database
        db_path = Path(self.database_config.get("path", "./historical_events.db"))
        self.database = HistoricalDatabase(db_path)

        # Initialize scraper
        self.scraper = HistoricalDataScraper(config)

    def _setup_logging(self) -> None:
        """Configure logging for the application."""
        log_level = self.config.get("logging", {}).get("level", "INFO")
        log_file = self.config.get("logging", {}).get("file", "logs/historical.log")

        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.handlers.RotatingFileHandler(
                    log_file, maxBytes=10485760, backupCount=5
                ),
                logging.StreamHandler(sys.stdout),
            ],
        )

    def scrape_and_store(self, dry_run: bool = False) -> Dict[str, int]:
        """Scrape historical data and store in database.

        Args:
            dry_run: If True, only report what would be scraped.

        Returns:
            Dictionary with scraping statistics.
        """
        results = {"scraped": 0, "stored": 0, "failed": 0}

        # Scrape from Wikipedia if enabled
        if self.config.get("sources", {}).get("wikipedia", {}).get("enabled", False):
            limit = self.config.get("sources", {}).get("wikipedia", {}).get("limit", 50)
            logger.info(f"Scraping from Wikipedia (limit: {limit})")
            events = self.scraper.scrape_wikipedia_events(limit=limit)
            results["scraped"] += len(events)

            if not dry_run:
                for event in events:
                    if self.database.insert_event(event):
                        results["stored"] += 1
                    else:
                        results["failed"] += 1

        # Scrape from custom sources
        custom_sources = self.config.get("sources", {}).get("custom_sources", [])
        for source_config in custom_sources:
            if source_config.get("enabled", False):
                logger.info(f"Scraping from custom source: {source_config.get('name')}")
                events = self.scraper.scrape_custom_source(source_config)
                results["scraped"] += len(events)

                if not dry_run:
                    for event in events:
                        if self.database.insert_event(event):
                            results["stored"] += 1
                        else:
                            results["failed"] += 1

        return results

    def search_events(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None,
        location: Optional[str] = None,
        topic: Optional[str] = None,
        date_range: Optional[Tuple[str, str]] = None,
    ) -> List[Dict]:
        """Search events in the database.

        Args:
            year: Year to search for.
            month: Month to search for.
            day: Day to search for.
            location: Location to search for.
            topic: Topic to search for.
            date_range: Tuple of (start_date, end_date).

        Returns:
            List of matching event dictionaries.
        """
        if location:
            return self.database.search_by_location(location)
        elif topic:
            return self.database.search_by_topic(topic)
        else:
            return self.database.search_by_date(
                year=year, month=month, day=day, date_range=date_range
            )


def load_config(config_path: Path) -> Dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to configuration file.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        yaml.YAMLError: If config file is invalid YAML.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config or {}
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in config file: {e}") from e


def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Scrape public domain historical data and create searchable database"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--scrape",
        action="store_true",
        help="Scrape historical data and populate database",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without storing data",
    )
    parser.add_argument(
        "--search-date",
        type=str,
        help="Search by date (YYYY-MM-DD or YYYY or YYYY-MM)",
    )
    parser.add_argument(
        "--search-location",
        type=str,
        help="Search by location",
    )
    parser.add_argument(
        "--search-topic",
        type=str,
        help="Search by topic",
    )
    parser.add_argument(
        "--date-range",
        nargs=2,
        metavar=("START", "END"),
        help="Search by date range (YYYY-MM-DD YYYY-MM-DD)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show database statistics",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(str(e))
        sys.exit(1)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    manager = HistoricalEventsManager(config)

    # Scrape if requested
    if args.scrape:
        if args.dry_run:
            logger.info("Running in dry-run mode - no data will be stored")

        results = manager.scrape_and_store(dry_run=args.dry_run)

        print("\n" + "=" * 60)
        print("Scraping Summary")
        print("=" * 60)
        print(f"Events scraped: {results['scraped']}")
        print(f"Events stored: {results['stored']}")
        print(f"Events failed: {results['failed']}")
        print("=" * 60)

    # Show statistics
    if args.stats:
        stats = manager.database.get_statistics()
        print("\n" + "=" * 60)
        print("Database Statistics")
        print("=" * 60)
        print(f"Total Events: {stats.get('total_events', 0):,}")
        if stats.get("year_range"):
            min_year, max_year = stats["year_range"]
            print(f"Year Range: {min_year} - {max_year}")
        print(f"Unique Locations: {stats.get('unique_locations', 0):,}")
        print(f"Unique Topics: {stats.get('unique_topics', 0):,}")
        print("=" * 60)

    # Search if requested
    if args.search_date or args.search_location or args.search_topic or args.date_range:
        year = None
        month = None
        day = None

        if args.search_date:
            parts = args.search_date.split("-")
            year = int(parts[0]) if parts[0] else None
            month = int(parts[1]) if len(parts) > 1 and parts[1] else None
            day = int(parts[2]) if len(parts) > 2 and parts[2] else None

        date_range = None
        if args.date_range:
            date_range = tuple(args.date_range)

        events = manager.search_events(
            year=year,
            month=month,
            day=day,
            location=args.search_location,
            topic=args.search_topic,
            date_range=date_range,
        )

        print("\n" + "=" * 60)
        print(f"Search Results: {len(events)} events found")
        print("=" * 60)

        for event in events[:20]:  # Limit to 20 results
            print(f"\nDate: {event.get('date')}")
            print(f"Location: {event.get('location', 'N/A')}")
            print(f"Topic: {event.get('topic', 'N/A')}")
            print(f"Description: {event.get('description', '')[:200]}...")
            print(f"Source: {event.get('source', 'N/A')}")
            print("-" * 60)

        if len(events) > 20:
            print(f"\n... and {len(events) - 20} more events")

    # If no action specified, show help
    if not any([args.scrape, args.stats, args.search_date, args.search_location,
                args.search_topic, args.date_range]):
        parser.print_help()


if __name__ == "__main__":
    main()
