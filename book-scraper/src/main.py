"""Book Scraper - Scrape book information and manage reading list.

This module provides functionality to scrape book information from library
websites, maintain a personal reading list with progress tracking, and store
notes for each book.
"""

import json
import logging
import logging.handlers
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
import yaml
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class BookScraper:
    """Scrapes book information from library websites."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize BookScraper with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.reading_list_path = self._get_data_file_path("reading_list.json")
        self.reading_list: Dict[str, Dict[str, Any]] = {}
        self.session = requests.Session()
        self._setup_session()

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
        if os.getenv("DATA_DIRECTORY"):
            config["data"]["directory"] = os.getenv("DATA_DIRECTORY")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/book_scraper.log")

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

    def _setup_session(self) -> None:
        """Configure HTTP session with headers and timeout."""
        headers = self.config.get("scraping", {}).get("headers", {})
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        }
        default_headers.update(headers)
        self.session.headers.update(default_headers)

        timeout = self.config.get("scraping", {}).get("timeout", 30)
        self.session.timeout = timeout

    def _get_data_file_path(self, filename: str) -> Path:
        """Get absolute path to data file.

        Args:
            filename: Name of data file.

        Returns:
            Absolute path to data file.
        """
        data_dir = self.config.get("data", {}).get("directory", "data")
        data_path = Path(data_dir)

        if not data_path.is_absolute():
            project_root = Path(__file__).parent.parent
            data_path = project_root / data_dir

        data_path.mkdir(parents=True, exist_ok=True)
        return data_path / filename

    def _load_reading_list(self) -> None:
        """Load reading list from JSON file."""
        if self.reading_list_path.exists():
            try:
                with open(self.reading_list_path, "r", encoding="utf-8") as f:
                    self.reading_list = json.load(f)
                logger.info(f"Loaded {len(self.reading_list)} book(s) from reading list")
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing reading list JSON: {e}")
                self.reading_list = {}
            except Exception as e:
                logger.error(f"Error loading reading list: {e}")
                self.reading_list = {}
        else:
            self.reading_list = {}
            logger.info("Reading list file not found, starting with empty list")

    def _save_reading_list(self) -> None:
        """Save reading list to JSON file."""
        try:
            with open(self.reading_list_path, "w", encoding="utf-8") as f:
                json.dump(self.reading_list, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.reading_list)} book(s) to reading list")
        except Exception as e:
            logger.error(f"Error saving reading list: {e}")
            raise

    def _get_book_id(self, title: str, author: str) -> str:
        """Generate unique book ID from title and author.

        Args:
            title: Book title.
            author: Book author.

        Returns:
            Unique book identifier.
        """
        # Create ID from normalized title and author
        normalized_title = re.sub(r"[^a-zA-Z0-9]", "", title.lower())
        normalized_author = re.sub(r"[^a-zA-Z0-9]", "", author.lower())
        book_id = f"{normalized_title}_{normalized_author}"
        return book_id[:100]  # Limit length

    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse webpage.

        Args:
            url: URL to fetch.

        Returns:
            BeautifulSoup object or None if fetch fails.
        """
        try:
            delay = self.config.get("scraping", {}).get("delay", 1)
            time.sleep(delay)

            response = self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            logger.debug(f"Successfully fetched: {url}")
            return soup

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None

    def _extract_book_info(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract book information from parsed HTML.

        Args:
            soup: BeautifulSoup object of the book page.
            url: URL of the book page.

        Returns:
            Dictionary with book information.
        """
        book_info = {
            "title": "",
            "author": "",
            "isbn": "",
            "publication_date": "",
            "publisher": "",
            "description": "",
            "pages": 0,
            "genres": [],
            "url": url,
            "scraped_at": datetime.now().isoformat(),
        }

        scraping_config = self.config.get("scraping", {})
        selectors = scraping_config.get("selectors", {})

        # Extract title
        title_selector = selectors.get("title", "h1, .title, [class*='title']")
        title_elem = soup.select_one(title_selector)
        if title_elem:
            book_info["title"] = title_elem.get_text(strip=True)

        # Extract author
        author_selector = selectors.get("author", "[class*='author'], .author")
        author_elem = soup.select_one(author_selector)
        if author_elem:
            book_info["author"] = author_elem.get_text(strip=True)

        # Extract ISBN
        isbn_selector = selectors.get("isbn", "[class*='isbn'], .isbn")
        isbn_elem = soup.select_one(isbn_selector)
        if isbn_elem:
            isbn_text = isbn_elem.get_text(strip=True)
            # Extract ISBN-13 or ISBN-10 pattern
            isbn_match = re.search(r"\b\d{13}|\b\d{10}\b", isbn_text)
            if isbn_match:
                book_info["isbn"] = isbn_match.group()

        # Extract publication date
        date_selector = selectors.get("publication_date", "[class*='date'], .date")
        date_elem = soup.select_one(date_selector)
        if date_elem:
            book_info["publication_date"] = date_elem.get_text(strip=True)

        # Extract publisher
        publisher_selector = selectors.get("publisher", "[class*='publisher'], .publisher")
        publisher_elem = soup.select_one(publisher_selector)
        if publisher_elem:
            book_info["publisher"] = publisher_elem.get_text(strip=True)

        # Extract description
        desc_selector = selectors.get("description", "[class*='description'], .description")
        desc_elem = soup.select_one(desc_selector)
        if desc_elem:
            book_info["description"] = desc_elem.get_text(strip=True)

        # Extract pages
        pages_selector = selectors.get("pages", "[class*='pages'], .pages")
        pages_elem = soup.select_one(pages_selector)
        if pages_elem:
            pages_text = pages_elem.get_text(strip=True)
            pages_match = re.search(r"\d+", pages_text)
            if pages_match:
                book_info["pages"] = int(pages_match.group())

        # Extract genres
        genres_selector = selectors.get("genres", "[class*='genre'], .genre")
        genre_elems = soup.select(genres_selector)
        book_info["genres"] = [elem.get_text(strip=True) for elem in genre_elems]

        # Fallback: try to extract from meta tags
        if not book_info["title"]:
            meta_title = soup.find("meta", property="og:title")
            if meta_title:
                book_info["title"] = meta_title.get("content", "")

        if not book_info["description"]:
            meta_desc = soup.find("meta", property="og:description")
            if meta_desc:
                book_info["description"] = meta_desc.get("content", "")

        return book_info

    def scrape_book(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape book information from URL.

        Args:
            url: URL of the book page.

        Returns:
            Dictionary with book information or None if scraping fails.
        """
        logger.info(f"Scraping book from: {url}")

        soup = self._fetch_page(url)
        if not soup:
            return None

        book_info = self._extract_book_info(soup, url)

        if not book_info["title"]:
            logger.warning(f"Could not extract title from: {url}")
            return None

        logger.info(f"Successfully scraped: {book_info['title']} by {book_info['author']}")
        return book_info

    def add_book(
        self,
        book_info: Dict[str, Any],
        status: str = "to_read",
        notes: str = "",
    ) -> str:
        """Add book to reading list.

        Args:
            book_info: Dictionary with book information.
            status: Reading status (to_read, reading, completed, abandoned).
            notes: Initial notes for the book.

        Returns:
            Book ID.
        """
        if not book_info.get("title") or not book_info.get("author"):
            raise ValueError("Book must have title and author")

        book_id = self._get_book_id(book_info["title"], book_info["author"])

        # Check if book already exists
        if book_id in self.reading_list:
            logger.warning(f"Book already exists: {book_info['title']}")
            return book_id

        self.reading_list[book_id] = {
            **book_info,
            "status": status,
            "notes": notes,
            "progress": {
                "pages_read": 0,
                "percentage": 0.0,
                "started_date": None,
                "completed_date": None,
            },
            "added_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        self._save_reading_list()
        logger.info(f"Added book to reading list: {book_info['title']}")

        return book_id

    def update_progress(
        self, book_id: str, pages_read: Optional[int] = None, percentage: Optional[float] = None
    ) -> None:
        """Update reading progress for a book.

        Args:
            book_id: Book identifier.
            pages_read: Number of pages read.
            percentage: Percentage of book read (0-100).

        Raises:
            KeyError: If book_id not found.
            ValueError: If pages_read or percentage is invalid.
        """
        if book_id not in self.reading_list:
            raise KeyError(f"Book not found: {book_id}")

        book = self.reading_list[book_id]
        progress = book["progress"]

        if pages_read is not None:
            total_pages = book.get("pages", 0)
            if total_pages > 0:
                if pages_read < 0 or pages_read > total_pages:
                    raise ValueError(f"Pages read must be between 0 and {total_pages}")
                progress["pages_read"] = pages_read
                progress["percentage"] = (pages_read / total_pages) * 100
            else:
                progress["pages_read"] = pages_read
                logger.warning("Total pages unknown, cannot calculate percentage")

        if percentage is not None:
            if percentage < 0 or percentage > 100:
                raise ValueError("Percentage must be between 0 and 100")
            progress["percentage"] = percentage
            total_pages = book.get("pages", 0)
            if total_pages > 0:
                progress["pages_read"] = int((percentage / 100) * total_pages)

        # Update status based on progress
        if progress["percentage"] == 0:
            book["status"] = "to_read"
        elif progress["percentage"] == 100:
            book["status"] = "completed"
            progress["completed_date"] = datetime.now().isoformat()
        elif progress["percentage"] > 0:
            if book["status"] == "to_read":
                book["status"] = "reading"
                progress["started_date"] = datetime.now().isoformat()

        book["updated_at"] = datetime.now().isoformat()
        self._save_reading_list()

        logger.info(
            f"Updated progress for {book['title']}: "
            f"{progress['pages_read']} pages, {progress['percentage']:.1f}%"
        )

    def update_status(self, book_id: str, status: str) -> None:
        """Update reading status for a book.

        Args:
            book_id: Book identifier.
            status: New status (to_read, reading, completed, abandoned).

        Raises:
            KeyError: If book_id not found.
            ValueError: If status is invalid.
        """
        valid_statuses = ["to_read", "reading", "completed", "abandoned"]
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")

        if book_id not in self.reading_list:
            raise KeyError(f"Book not found: {book_id}")

        book = self.reading_list[book_id]
        book["status"] = status
        book["updated_at"] = datetime.now().isoformat()

        progress = book["progress"]
        if status == "completed" and not progress["completed_date"]:
            progress["completed_date"] = datetime.now().isoformat()
            if book.get("pages", 0) > 0:
                progress["pages_read"] = book["pages"]
                progress["percentage"] = 100.0
        elif status == "reading" and not progress["started_date"]:
            progress["started_date"] = datetime.now().isoformat()

        self._save_reading_list()
        logger.info(f"Updated status for {book['title']}: {status}")

    def add_note(self, book_id: str, note: str) -> None:
        """Add note to a book.

        Args:
            book_id: Book identifier.
            note: Note text to add.

        Raises:
            KeyError: If book_id not found.
        """
        if book_id not in self.reading_list:
            raise KeyError(f"Book not found: {book_id}")

        book = self.reading_list[book_id]
        existing_notes = book.get("notes", "")
        if existing_notes:
            book["notes"] = f"{existing_notes}\n\n{datetime.now().strftime('%Y-%m-%d %H:%M')}: {note}"
        else:
            book["notes"] = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}: {note}"

        book["updated_at"] = datetime.now().isoformat()
        self._save_reading_list()

        logger.info(f"Added note to {book['title']}")

    def get_reading_list(
        self, status: Optional[str] = None, sort_by: str = "added_at"
    ) -> List[Dict[str, Any]]:
        """Get reading list with optional filtering and sorting.

        Args:
            status: Filter by status (to_read, reading, completed, abandoned).
            sort_by: Field to sort by (added_at, updated_at, title, author).

        Returns:
            List of book dictionaries.
        """
        books = list(self.reading_list.values())

        if status:
            books = [book for book in books if book.get("status") == status]

        # Sort books
        reverse = sort_by in ["added_at", "updated_at"]
        try:
            books.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)
        except (KeyError, TypeError):
            logger.warning(f"Could not sort by {sort_by}, using default")
            books.sort(key=lambda x: x.get("added_at", ""), reverse=True)

        return books

    def get_book(self, book_id: str) -> Optional[Dict[str, Any]]:
        """Get book information by ID.

        Args:
            book_id: Book identifier.

        Returns:
            Book dictionary or None if not found.
        """
        return self.reading_list.get(book_id)

    def delete_book(self, book_id: str) -> None:
        """Delete book from reading list.

        Args:
            book_id: Book identifier.

        Raises:
            KeyError: If book_id not found.
        """
        if book_id not in self.reading_list:
            raise KeyError(f"Book not found: {book_id}")

        book_title = self.reading_list[book_id]["title"]
        del self.reading_list[book_id]
        self._save_reading_list()

        logger.info(f"Deleted book from reading list: {book_title}")


def main() -> int:
    """Main entry point for book scraper."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape book information and manage reading list"
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
        help="URL of book page to scrape",
    )
    parser.add_argument(
        "-a",
        "--add",
        help="Add scraped book to reading list (use with --scrape)",
        action="store_true",
    )
    parser.add_argument(
        "-l",
        "--list",
        help="List books in reading list",
        action="store_true",
    )
    parser.add_argument(
        "--status",
        help="Filter reading list by status",
        choices=["to_read", "reading", "completed", "abandoned"],
    )
    parser.add_argument(
        "-u",
        "--update-progress",
        nargs=2,
        metavar=("BOOK_ID", "PAGES"),
        help="Update reading progress (book_id pages_read)",
    )
    parser.add_argument(
        "-n",
        "--note",
        nargs=2,
        metavar=("BOOK_ID", "NOTE"),
        help="Add note to book",
    )
    parser.add_argument(
        "-d",
        "--delete",
        help="Delete book from reading list (book_id)",
    )

    args = parser.parse_args()

    try:
        scraper = BookScraper(config_path=args.config)
        scraper._load_reading_list()

        if args.scrape:
            book_info = scraper.scrape_book(args.scrape)
            if book_info:
                print("\nScraped Book Information:")
                print("=" * 50)
                print(f"Title: {book_info.get('title', 'N/A')}")
                print(f"Author: {book_info.get('author', 'N/A')}")
                print(f"ISBN: {book_info.get('isbn', 'N/A')}")
                print(f"Pages: {book_info.get('pages', 'N/A')}")
                print(f"Publisher: {book_info.get('publisher', 'N/A')}")

                if args.add:
                    book_id = scraper.add_book(book_info)
                    print(f"\nBook added to reading list (ID: {book_id})")

        if args.list:
            books = scraper.get_reading_list(status=args.status)
            print(f"\nReading List ({len(books)} book(s)):")
            print("=" * 50)
            for book in books:
                progress = book.get("progress", {})
                print(f"\n{book.get('title', 'N/A')} by {book.get('author', 'N/A')}")
                print(f"  Status: {book.get('status', 'N/A')}")
                print(
                    f"  Progress: {progress.get('pages_read', 0)} pages, "
                    f"{progress.get('percentage', 0):.1f}%"
                )

        if args.update_progress:
            book_id, pages = args.update_progress
            scraper.update_progress(book_id, pages_read=int(pages))
            print(f"Progress updated for book {book_id}")

        if args.note:
            book_id, note = args.note
            scraper.add_note(book_id, note)
            print(f"Note added to book {book_id}")

        if args.delete:
            scraper.delete_book(args.delete)
            print(f"Book {args.delete} deleted from reading list")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except KeyError as e:
        logger.error(f"Key error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
