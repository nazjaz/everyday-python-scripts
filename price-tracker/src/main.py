"""Price Tracker - Scrape product prices and track price history.

This module provides functionality to scrape product prices from e-commerce
websites and save price history to a local database, tracking price changes
over time.
"""

import logging
import logging.handlers
import os
import re
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
import yaml
from bs4 import BeautifulSoup
from dotenv import load_dotenv

try:
    from plyer import notification
except ImportError:
    notification = None

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class PriceTracker:
    """Tracks product prices from e-commerce websites."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize PriceTracker with configuration.

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
            "products_checked": 0,
            "prices_updated": 0,
            "prices_failed": 0,
            "price_changes": 0,
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
        if os.getenv("NOTIFICATIONS_ENABLED"):
            config["notifications"]["enabled"] = (
                os.getenv("NOTIFICATIONS_ENABLED").lower() == "true"
            )

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/price_tracker.log")

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

        # Products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                website TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Price history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                price REAL NOT NULL,
                currency TEXT,
                title TEXT,
                checked_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # Price changes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                old_price REAL,
                new_price REAL NOT NULL,
                change_percent REAL,
                changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        conn.commit()
        conn.close()
        logger.debug("Database tables created/verified")

    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse webpage.

        Args:
            url: URL to fetch.

        Returns:
            BeautifulSoup object or None if fetch failed.
        """
        scraping_config = self.config.get("scraping", {})
        timeout = scraping_config.get("timeout", 30)
        user_agent = scraping_config.get("user_agent", "Price-Tracker/1.0")
        retry_attempts = scraping_config.get("retry_attempts", 3)
        retry_delay = scraping_config.get("retry_delay", 5)

        headers = {"User-Agent": user_agent}

        for attempt in range(retry_attempts):
            try:
                response = requests.get(url, headers=headers, timeout=timeout)
                response.raise_for_status()
                return BeautifulSoup(response.content, "html.parser")

            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1}/{retry_attempts} failed for {url}: {e}")
                if attempt < retry_attempts - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to fetch {url} after {retry_attempts} attempts")
                    return None

        return None

    def _extract_price(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[float]:
        """Extract price from HTML using CSS selectors.

        Args:
            soup: BeautifulSoup object.
            selectors: List of CSS selectors to try.

        Returns:
            Extracted price as float or None if not found.
        """
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    # Extract numeric value from text
                    price = self._parse_price(text)
                    if price:
                        return price
            except Exception as e:
                logger.debug(f"Error with selector '{selector}': {e}")
                continue

        return None

    def _parse_price(self, text: str) -> Optional[float]:
        """Parse price from text string.

        Args:
            text: Text containing price.

        Returns:
            Price as float or None if not found.
        """
        # Remove currency symbols and common characters
        text = re.sub(r"[^\d.,]", "", text)

        # Handle different decimal separators
        if "," in text and "." in text:
            # Assume comma is thousands separator
            text = text.replace(",", "")
        elif "," in text:
            # Could be decimal separator
            text = text.replace(",", ".")

        try:
            return float(text)
        except ValueError:
            return None

    def _extract_title(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Extract product title from HTML.

        Args:
            soup: BeautifulSoup object.
            selectors: List of CSS selectors to try.

        Returns:
            Product title or None if not found.
        """
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    return element.get_text(strip=True)
            except Exception:
                continue

        return None

    def _get_selectors(self, product: Dict) -> Tuple[List[str], List[str]]:
        """Get CSS selectors for price and title.

        Args:
            product: Product configuration dictionary.

        Returns:
            Tuple of (price_selectors, title_selectors).
        """
        website = product.get("website", "generic")
        website_selectors = self.config.get("website_selectors", {}).get(website, {})

        # Use product-specific selectors or fall back to website defaults
        price_selector = product.get("price_selector") or website_selectors.get("price_selector", ".price")
        title_selector = product.get("title_selector") or website_selectors.get("title_selector", "h1")

        # Split multiple selectors (comma-separated)
        price_selectors = [s.strip() for s in price_selector.split(",")]
        title_selectors = [s.strip() for s in title_selector.split(",")]

        return price_selectors, title_selectors

    def _get_product_id(self, url: str) -> Optional[int]:
        """Get product ID from database by URL.

        Args:
            url: Product URL.

        Returns:
            Product ID or None if not found.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM products WHERE url = ?", (url,))
        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def _add_product(self, name: str, url: str, website: str) -> int:
        """Add product to database.

        Args:
            name: Product name.
            url: Product URL.
            website: Website identifier.

        Returns:
            Product ID.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO products (name, url, website) VALUES (?, ?, ?)",
                (name, url, website),
            )
            product_id = cursor.lastrowid
            conn.commit()
            return product_id
        except sqlite3.IntegrityError:
            # Product already exists, get its ID
            cursor.execute("SELECT id FROM products WHERE url = ?", (url,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        finally:
            conn.close()

    def _save_price(self, product_id: int, price: float, currency: str, title: Optional[str]) -> bool:
        """Save price to database and check for changes.

        Args:
            product_id: Product ID.
            price: Current price.
            currency: Currency symbol.
            title: Product title.

        Returns:
            True if price was saved, False otherwise.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get last price
            cursor.execute(
                "SELECT price FROM price_history WHERE product_id = ? ORDER BY checked_at DESC LIMIT 1",
                (product_id,),
            )
            last_result = cursor.fetchone()
            last_price = last_result[0] if last_result else None

            # Save current price
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO price_history (product_id, price, currency, title, checked_at) VALUES (?, ?, ?, ?, ?)",
                (product_id, price, currency, title, now),
            )

            # Check for price change
            if last_price is not None and last_price != price:
                change_percent = ((price - last_price) / last_price) * 100
                cursor.execute(
                    "INSERT INTO price_changes (product_id, old_price, new_price, change_percent) VALUES (?, ?, ?, ?)",
                    (product_id, last_price, price, change_percent),
                )
                self.stats["price_changes"] += 1

                logger.info(
                    f"Price change detected: {last_price:.2f} -> {price:.2f} "
                    f"({change_percent:+.2f}%)"
                )

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error saving price: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def _cleanup_old_data(self) -> None:
        """Remove old price history based on retention policy."""
        if not self.config.get("retention", {}).get("auto_cleanup", True):
            return

        days_to_keep = self.config.get("retention", {}).get("days_to_keep", 365)
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "DELETE FROM price_history WHERE checked_at < ?",
                (cutoff_date.isoformat(),),
            )
            deleted_count = cursor.rowcount
            conn.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old price history entries")

        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            conn.rollback()
        finally:
            conn.close()

    def _check_product(self, product: Dict) -> bool:
        """Check price for a single product.

        Args:
            product: Product configuration dictionary.

        Returns:
            True if successful, False otherwise.
        """
        name = product.get("name", "Unknown")
        url = product.get("url", "")
        website = product.get("website", "generic")

        if not url:
            logger.warning(f"Product '{name}' has no URL, skipping")
            return False

        logger.info(f"Checking price for: {name} ({url})")

        # Fetch page
        soup = self._fetch_page(url)
        if not soup:
            self.stats["prices_failed"] += 1
            return False

        # Get selectors
        price_selectors, title_selectors = self._get_selectors(product)

        # Extract price
        price = self._extract_price(soup, price_selectors)
        if not price:
            logger.warning(f"Could not extract price for {name}")
            self.stats["prices_failed"] += 1
            return False

        # Extract title
        title = self._extract_title(soup, title_selectors) or name

        # Get currency
        website_selectors = self.config.get("website_selectors", {}).get(website, {})
        currency = website_selectors.get("currency_symbol", "$")

        # Get or create product in database
        product_id = self._get_product_id(url)
        if not product_id:
            product_id = self._add_product(name, url, website)

        # Save price
        if self._save_price(product_id, price, currency, title):
            self.stats["prices_updated"] += 1
            logger.info(f"Price updated for {name}: {currency}{price:.2f}")
            return True

        self.stats["prices_failed"] += 1
        return False

    def check_prices(self) -> dict:
        """Check prices for all configured products.

        Returns:
            Dictionary with checking statistics.
        """
        logger.info("Starting price check")

        products = self.config.get("products", [])
        if not products:
            logger.warning("No products configured")
            return self.stats

        for product in products:
            if not product.get("enabled", True):
                continue

            self.stats["products_checked"] += 1
            self._check_product(product)

        # Cleanup old data
        self._cleanup_old_data()

        # Generate report
        if self.config.get("reporting", {}).get("generate_reports", True):
            self._generate_report()

        logger.info("Price check completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats

    def _generate_report(self) -> None:
        """Generate price tracking report."""
        report_config = self.config.get("reporting", {})
        report_file = report_config.get("report_file", "logs/price_tracking_report.txt")

        report_path = Path(report_file)
        if not report_path.is_absolute():
            project_root = Path(__file__).parent.parent
            report_path = project_root / report_file

        report_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("Price Tracking Report\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")

            f.write("Statistics\n")
            f.write("-" * 60 + "\n")
            f.write(f"Products Checked: {self.stats['products_checked']}\n")
            f.write(f"Prices Updated: {self.stats['prices_updated']}\n")
            f.write(f"Prices Failed: {self.stats['prices_failed']}\n")
            f.write(f"Price Changes: {self.stats['price_changes']}\n")
            f.write("\n")

            # Recent price changes
            cursor.execute("""
                SELECT p.name, pc.old_price, pc.new_price, pc.change_percent, pc.changed_at
                FROM price_changes pc
                JOIN products p ON pc.product_id = p.id
                ORDER BY pc.changed_at DESC
                LIMIT 20
            """)
            changes = cursor.fetchall()

            if changes:
                f.write("Recent Price Changes\n")
                f.write("-" * 60 + "\n")
                for name, old_price, new_price, change_percent, changed_at in changes:
                    f.write(
                        f"{name}: ${old_price:.2f} -> ${new_price:.2f} "
                        f"({change_percent:+.2f}%) at {changed_at}\n"
                    )
                f.write("\n")

            # Current prices
            cursor.execute("""
                SELECT p.name, ph.price, ph.currency, ph.checked_at
                FROM products p
                JOIN (
                    SELECT product_id, price, currency, checked_at,
                           ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY checked_at DESC) as rn
                    FROM price_history
                ) ph ON p.id = ph.product_id
                WHERE ph.rn = 1
                ORDER BY p.name
            """)
            current_prices = cursor.fetchall()

            if current_prices:
                f.write("Current Prices\n")
                f.write("-" * 60 + "\n")
                for name, price, currency, checked_at in current_prices:
                    f.write(f"{name}: {currency}{price:.2f} (checked: {checked_at})\n")

        conn.close()
        logger.info(f"Report generated: {report_path}")


def main() -> int:
    """Main entry point for price tracker."""
    import argparse

    parser = argparse.ArgumentParser(description="Track product prices from e-commerce websites")
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-o",
        "--once",
        action="store_true",
        help="Run once and exit (don't loop)",
    )

    args = parser.parse_args()

    try:
        tracker = PriceTracker(config_path=args.config)
        tracker.check_prices()

        print("\n" + "=" * 50)
        print("Price Check Summary")
        print("=" * 50)
        print(f"Products Checked: {tracker.stats['products_checked']}")
        print(f"Prices Updated: {tracker.stats['prices_updated']}")
        print(f"Prices Failed: {tracker.stats['prices_failed']}")
        print(f"Price Changes: {tracker.stats['price_changes']}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
