"""Transit Schedule Scraper - Scrape public transportation schedules.

This module provides functionality to scrape public transportation schedules
from transit websites and display next departure times for specified routes
and stops.
"""

import logging
import logging.handlers
import os
import re
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
import yaml
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class TransitScheduleScraper:
    """Scrapes transit schedules from websites and displays departure times."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize TransitScheduleScraper with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_database()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.config.get("scraping", {}).get(
                    "user_agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                )
            }
        )

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
        if os.getenv("REQUEST_TIMEOUT"):
            config["scraping"]["timeout"] = int(os.getenv("REQUEST_TIMEOUT"))

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/transit_scraper.log")

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

        # Routes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_id TEXT NOT NULL,
                route_name TEXT,
                transit_system TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(route_id, transit_system)
            )
        """)

        # Stops table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stop_id TEXT NOT NULL,
                stop_name TEXT,
                transit_system TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stop_id, transit_system)
            )
        """)

        # Departures table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS departures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_id TEXT NOT NULL,
                stop_id TEXT NOT NULL,
                departure_time TEXT NOT NULL,
                scheduled_time TEXT,
                delay_minutes INTEGER,
                transit_system TEXT,
                scraped_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(route_id) REFERENCES routes(route_id),
                FOREIGN KEY(stop_id) REFERENCES stops(stop_id)
            )
        """)

        conn.commit()
        conn.close()
        logger.debug("Database tables created/verified")

    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page.

        Args:
            url: URL to fetch.

        Returns:
            BeautifulSoup object or None if fetch failed.
        """
        timeout = self.config.get("scraping", {}).get("timeout", 30)
        delay = self.config.get("scraping", {}).get("delay", 1)

        try:
            time.sleep(delay)
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or "utf-8"

            soup = BeautifulSoup(response.text, "html.parser")
            logger.debug(f"Fetched page: {url}")
            return soup

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing page {url}: {e}")
            return None

    def _extract_departure_times(
        self, soup: BeautifulSoup, selectors: Dict[str, str]
    ) -> List[Dict[str, any]]:
        """Extract departure times from parsed HTML.

        Args:
            soup: BeautifulSoup object.
            selectors: Dictionary of CSS selectors for extracting data.

        Returns:
            List of departure dictionaries.
        """
        departures = []

        try:
            # Extract departure rows
            row_selector = selectors.get("departure_row", "tr.departure, .departure-row")
            rows = soup.select(row_selector)

            if not rows:
                # Try alternative selectors
                rows = soup.select("table tr, .schedule-item, .departure")

            for row in rows:
                departure = {}

                # Extract time
                time_selector = selectors.get("time", ".time, .departure-time, td.time")
                time_elem = row.select_one(time_selector)
                if time_elem:
                    departure["time"] = time_elem.get_text(strip=True)

                # Extract route
                route_selector = selectors.get("route", ".route, .route-name, td.route")
                route_elem = row.select_one(route_selector)
                if route_elem:
                    departure["route"] = route_elem.get_text(strip=True)

                # Extract destination
                dest_selector = selectors.get(
                    "destination", ".destination, .to, td.destination"
                )
                dest_elem = row.select_one(dest_selector)
                if dest_elem:
                    departure["destination"] = dest_elem.get_text(strip=True)

                # Extract delay/status
                delay_selector = selectors.get("delay", ".delay, .status, td.delay")
                delay_elem = row.select_one(delay_selector)
                if delay_elem:
                    departure["delay"] = delay_elem.get_text(strip=True)

                if departure.get("time"):
                    departures.append(departure)

        except Exception as e:
            logger.error(f"Error extracting departure times: {e}")

        return departures

    def _parse_time_string(self, time_str: str) -> Optional[datetime]:
        """Parse time string to datetime object.

        Args:
            time_str: Time string in various formats.

        Returns:
            Datetime object or None if parsing failed.
        """
        if not time_str:
            return None

        time_str = time_str.strip().upper()

        # Try parsing as "HH:MM" or "HH:MM AM/PM"
        time_patterns = [
            "%H:%M",
            "%I:%M %p",
            "%I:%M%p",
            "%H:%M:%S",
            "%I:%M:%S %p",
        ]

        for pattern in time_patterns:
            try:
                time_obj = datetime.strptime(time_str, pattern).time()
                now = datetime.now()
                departure = datetime.combine(now.date(), time_obj)

                # If time is in the past, assume it's tomorrow
                if departure < now:
                    departure += timedelta(days=1)

                return departure
            except ValueError:
                continue

        # Try parsing relative times like "5 min", "in 10 minutes"
        relative_match = re.search(r"(\d+)\s*(?:min|minute)", time_str, re.IGNORECASE)
        if relative_match:
            minutes = int(relative_match.group(1))
            return datetime.now() + timedelta(minutes=minutes)

        logger.warning(f"Could not parse time string: {time_str}")
        return None

    def scrape_departures(
        self, route_id: str, stop_id: str, transit_system: Optional[str] = None
    ) -> List[Dict[str, any]]:
        """Scrape departure times for a route and stop.

        Args:
            route_id: Route identifier.
            stop_id: Stop identifier.
            transit_system: Transit system name (uses default if not provided).

        Returns:
            List of departure dictionaries.
        """
        transit_system = transit_system or self.config.get("default_transit_system", "default")

        transit_config = self.config.get("transit_systems", {}).get(transit_system, {})
        if not transit_config:
            logger.error(f"Transit system not configured: {transit_system}")
            return []

        base_url = transit_config.get("base_url", "")
        url_template = transit_config.get("url_template", "")

        # Build URL
        url = url_template.format(route_id=route_id, stop_id=stop_id, base_url=base_url)
        if not urlparse(url).netloc:
            url = urljoin(base_url, url)

        logger.info(f"Scraping departures for route {route_id} at stop {stop_id} from {url}")

        soup = self._fetch_page(url)
        if not soup:
            return []

        selectors = transit_config.get("selectors", {})
        departures = self._extract_departure_times(soup, selectors)

        # Parse and store departures
        parsed_departures = []
        for dep in departures:
            parsed_time = self._parse_time_string(dep.get("time", ""))
            if parsed_time:
                parsed_dep = {
                    "route_id": route_id,
                    "stop_id": stop_id,
                    "departure_time": parsed_time.isoformat(),
                    "scheduled_time": dep.get("time", ""),
                    "route_name": dep.get("route", ""),
                    "destination": dep.get("destination", ""),
                    "delay": dep.get("delay", ""),
                    "transit_system": transit_system,
                }
                parsed_departures.append(parsed_dep)
                self._save_departure(parsed_dep)

        logger.info(f"Found {len(parsed_departures)} departures")
        return parsed_departures

    def _save_departure(self, departure: Dict[str, any]) -> bool:
        """Save departure to database.

        Args:
            departure: Departure dictionary.

        Returns:
            True if saved successfully, False otherwise.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Save route if not exists
            cursor.execute("""
                INSERT OR IGNORE INTO routes (route_id, route_name, transit_system)
                VALUES (?, ?, ?)
            """, (departure["route_id"], departure.get("route_name", ""), departure["transit_system"]))

            # Save stop if not exists
            cursor.execute("""
                INSERT OR IGNORE INTO stops (stop_id, stop_name, transit_system)
                VALUES (?, ?, ?)
            """, (departure["stop_id"], "", departure["transit_system"]))

            # Parse delay minutes
            delay_minutes = None
            delay_str = departure.get("delay", "")
            if delay_str:
                delay_match = re.search(r"(-?\d+)", delay_str)
                if delay_match:
                    delay_minutes = int(delay_match.group(1))

            # Save departure
            cursor.execute("""
                INSERT INTO departures 
                (route_id, stop_id, departure_time, scheduled_time, delay_minutes, transit_system)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                departure["route_id"],
                departure["stop_id"],
                departure["departure_time"],
                departure.get("scheduled_time", ""),
                delay_minutes,
                departure["transit_system"],
            ))

            conn.commit()
            return True

        except sqlite3.Error as e:
            logger.error(f"Database error saving departure: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_next_departures(
        self, route_id: str, stop_id: str, limit: int = 5
    ) -> List[Dict[str, any]]:
        """Get next departure times for a route and stop.

        Args:
            route_id: Route identifier.
            stop_id: Stop identifier.
            limit: Maximum number of departures to return.

        Returns:
            List of departure dictionaries sorted by time.
        """
        # First, try to scrape fresh data
        self.scrape_departures(route_id, stop_id)

        # Then get from database
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT d.*, r.route_name, s.stop_name
                FROM departures d
                LEFT JOIN routes r ON d.route_id = r.route_id AND d.transit_system = r.transit_system
                LEFT JOIN stops s ON d.stop_id = s.stop_id AND d.transit_system = s.transit_system
                WHERE d.route_id = ? AND d.stop_id = ?
                AND datetime(d.departure_time) >= datetime('now')
                ORDER BY d.departure_time ASC
                LIMIT ?
            """, (route_id, stop_id, limit))

            rows = cursor.fetchall()
            departures = []
            for row in rows:
                dep = dict(row)
                dep["departure_datetime"] = datetime.fromisoformat(dep["departure_time"])
                dep["time_until"] = self._format_time_until(dep["departure_datetime"])
                departures.append(dep)

            return departures

        except sqlite3.Error as e:
            logger.error(f"Database error getting departures: {e}")
            return []
        finally:
            conn.close()

    def _format_time_until(self, departure_time: datetime) -> str:
        """Format time until departure.

        Args:
            departure_time: Departure datetime.

        Returns:
            Formatted time string.
        """
        now = datetime.now()
        delta = departure_time - now

        if delta.total_seconds() < 0:
            return "Departed"

        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes} min"
        else:
            return "Now"

    def display_departures(
        self, route_id: str, stop_id: str, limit: int = 5
    ) -> None:
        """Display next departures for a route and stop.

        Args:
            route_id: Route identifier.
            stop_id: Stop identifier.
            limit: Maximum number of departures to display.
        """
        departures = self.get_next_departures(route_id, stop_id, limit)

        if not departures:
            print(f"\nNo upcoming departures found for route {route_id} at stop {stop_id}")
            return

        print(f"\n{'=' * 80}")
        print(f"Next Departures - Route: {route_id}, Stop: {stop_id}")
        print(f"{'=' * 80}")
        print(f"{'Time':<20} {'Route':<15} {'Destination':<25} {'Time Until':<15}")
        print("-" * 80)

        for dep in departures:
            dep_time = dep["departure_datetime"].strftime("%Y-%m-%d %H:%M")
            route_name = dep.get("route_name", route_id) or route_id
            destination = dep.get("destination", "")[:25]
            time_until = dep.get("time_until", "")

            delay_info = ""
            if dep.get("delay_minutes"):
                delay = dep["delay_minutes"]
                if delay > 0:
                    delay_info = f" (+{delay} min)"
                elif delay < 0:
                    delay_info = f" ({delay} min)"

            print(f"{dep_time:<20} {route_name:<15} {destination:<25} {time_until}{delay_info}")

        print("=" * 80)


def main() -> int:
    """Main entry point for transit schedule scraper."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape transit schedules and display next departure times"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-r",
        "--route",
        required=True,
        help="Route identifier",
    )
    parser.add_argument(
        "-s",
        "--stop",
        required=True,
        help="Stop identifier",
    )
    parser.add_argument(
        "-t",
        "--transit-system",
        help="Transit system name (uses default from config if not provided)",
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=5,
        help="Number of departures to display (default: 5)",
    )

    args = parser.parse_args()

    try:
        scraper = TransitScheduleScraper(config_path=args.config)
        scraper.display_departures(
            route_id=args.route,
            stop_id=args.stop,
            limit=args.limit,
        )
        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
