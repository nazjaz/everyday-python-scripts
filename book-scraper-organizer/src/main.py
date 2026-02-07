"""Book Scraper and Organizer.

A Python script that scrapes public domain books from online libraries and
organizes them by author, genre, or publication date in a local database.
"""

import argparse
import logging
import re
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/scraper.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    BEAUTIFULSOUP_AVAILABLE = False
    BeautifulSoup = None
    logger.error("requests and beautifulsoup4 are required. Install with: pip install requests beautifulsoup4")


class BookDatabase:
    """Manages SQLite database for book metadata."""

    def __init__(self, db_path: Path) -> None:
        """Initialize the book database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT,
                genre TEXT,
                publication_date TEXT,
                isbn TEXT,
                language TEXT,
                file_path TEXT,
                file_url TEXT,
                download_date TEXT,
                file_size INTEGER,
                description TEXT,
                UNIQUE(title, author)
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_author ON books(author)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_genre ON books(genre)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_publication_date ON books(publication_date)
            """
        )

        conn.commit()
        conn.close()

        logger.info(f"Database initialized at {self.db_path}")

    def add_book(self, book_data: Dict[str, Any]) -> int:
        """Add a book to the database.

        Args:
            book_data: Dictionary containing book information

        Returns:
            Book ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO books
                (title, author, genre, publication_date, isbn, language,
                 file_path, file_url, download_date, file_size, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    book_data.get("title"),
                    book_data.get("author"),
                    book_data.get("genre"),
                    book_data.get("publication_date"),
                    book_data.get("isbn"),
                    book_data.get("language"),
                    book_data.get("file_path"),
                    book_data.get("file_url"),
                    book_data.get("download_date"),
                    book_data.get("file_size"),
                    book_data.get("description"),
                ),
            )

            book_id = cursor.lastrowid
            conn.commit()
            return book_id

        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_books(
        self,
        author: Optional[str] = None,
        genre: Optional[str] = None,
        publication_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query books from database.

        Args:
            author: Filter by author
            genre: Filter by genre
            publication_date: Filter by publication date

        Returns:
            List of book dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM books WHERE 1=1"
        params = []

        if author:
            query += " AND author LIKE ?"
            params.append(f"%{author}%")

        if genre:
            query += " AND genre LIKE ?"
            params.append(f"%{genre}%")

        if publication_date:
            query += " AND publication_date = ?"
            params.append(publication_date)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        books = [dict(row) for row in rows]
        conn.close()

        return books

    def book_exists(self, title: str, author: Optional[str] = None) -> bool:
        """Check if book already exists in database.

        Args:
            title: Book title
            author: Book author

        Returns:
            True if book exists, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if author:
            cursor.execute(
                "SELECT COUNT(*) FROM books WHERE title = ? AND author = ?",
                (title, author),
            )
        else:
            cursor.execute("SELECT COUNT(*) FROM books WHERE title = ?", (title,))

        count = cursor.fetchone()[0]
        conn.close()

        return count > 0


class BookScraper:
    """Scrapes public domain books from online libraries."""

    def __init__(
        self,
        database: BookDatabase,
        output_directory: Path,
        rate_limit: float = 1.0,
        user_agent: Optional[str] = None,
    ) -> None:
        """Initialize the book scraper.

        Args:
            database: BookDatabase instance
            output_directory: Directory to save downloaded books
            rate_limit: Delay between requests in seconds
            user_agent: Custom user agent string
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests and beautifulsoup4 are required")

        self.database = database
        self.output_directory = Path(output_directory).expanduser().resolve()
        self.output_directory.mkdir(parents=True, exist_ok=True)
        self.rate_limit = rate_limit

        self.user_agent = (
            user_agent
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

        self.stats = {
            "books_scraped": 0,
            "books_downloaded": 0,
            "books_skipped": 0,
            "errors": 0,
        }

    def _extract_book_metadata(self, url: str, soup: Any) -> Dict[str, Any]:
        """Extract book metadata from webpage.

        Args:
            url: Book page URL
            soup: BeautifulSoup object of the page

        Returns:
            Dictionary with book metadata
        """
        metadata: Dict[str, any] = {
            "title": None,
            "author": None,
            "genre": None,
            "publication_date": None,
            "isbn": None,
            "language": "English",
            "description": None,
            "file_url": None,
        }

        title_tag = soup.find("h1") or soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.get_text().strip()

        author_patterns = [
            r"Author[:\s]+([^\n<]+)",
            r"By\s+([^\n<]+)",
            r"Written by\s+([^\n<]+)",
        ]

        for pattern in author_patterns:
            match = re.search(pattern, soup.get_text(), re.IGNORECASE)
            if match:
                metadata["author"] = match.group(1).strip()
                break

        date_patterns = [
            r"Published[:\s]+(\d{4})",
            r"Publication[:\s]+(\d{4})",
            r"(\d{4})\s+publication",
        ]

        for pattern in date_patterns:
            match = re.search(pattern, soup.get_text(), re.IGNORECASE)
            if match:
                metadata["publication_date"] = match.group(1)
                break

        download_links = soup.find_all("a", href=True)
        for link in download_links:
            href = link.get("href", "")
            text = link.get_text().lower()

            if any(
                ext in href.lower() or ext in text
                for ext in [".txt", ".pdf", ".epub", ".html"]
            ):
                metadata["file_url"] = urljoin(url, href)
                break

        return metadata

    def _download_book(self, url: str, file_path: Path) -> bool:
        """Download book file from URL.

        Args:
            url: Book file URL
            file_path: Destination file path

        Returns:
            True if download successful, False otherwise
        """
        try:
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()

            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = file_path.stat().st_size
            if file_size == 0:
                file_path.unlink()
                return False

            logger.info(f"Downloaded: {url} -> {file_path} ({file_size:,} bytes)")
            return True

        except requests.RequestException as e:
            logger.warning(f"Error downloading {url}: {e}")
            return False
        except (IOError, OSError) as e:
            logger.error(f"Error saving file {file_path}: {e}")
            return False

    def _get_organized_path(
        self, book_data: Dict[str, any], organize_by: str
    ) -> Path:
        """Get organized file path based on organization method.

        Args:
            book_data: Book metadata dictionary
            organize_by: Organization method - "author", "genre", or "date"

        Returns:
            Organized file path
        """
        title = book_data.get("title", "unknown")
        safe_title = re.sub(r"[^\w\s-]", "", title)[:100]

        if organize_by == "author":
            author = book_data.get("author", "Unknown")
            safe_author = re.sub(r"[^\w\s-]", "", author)[:50]
            org_path = self.output_directory / safe_author / f"{safe_title}.txt"
        elif organize_by == "genre":
            genre = book_data.get("genre", "Unknown")
            safe_genre = re.sub(r"[^\w\s-]", "", genre)[:50]
            org_path = self.output_directory / safe_genre / f"{safe_title}.txt"
        elif organize_by == "date":
            pub_date = book_data.get("publication_date", "Unknown")
            org_path = self.output_directory / pub_date / f"{safe_title}.txt"
        else:
            org_path = self.output_directory / f"{safe_title}.txt"

        return org_path

    def scrape_book(self, url: str, organize_by: str = "author") -> bool:
        """Scrape a single book from URL.

        Args:
            url: Book page URL
            organize_by: Organization method

        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            book_data = self._extract_book_metadata(url, soup)

            if not book_data.get("title"):
                logger.warning(f"Could not extract title from {url}")
                self.stats["errors"] += 1
                return False

            if self.database.book_exists(
                book_data["title"], book_data.get("author")
            ):
                logger.info(f"Book already exists: {book_data['title']}")
                self.stats["books_skipped"] += 1
                return False

            if not book_data.get("file_url"):
                logger.warning(f"No download link found for {url}")
                self.stats["errors"] += 1
                return False

            file_path = self._get_organized_path(book_data, organize_by)

            if self._download_book(book_data["file_url"], file_path):
                book_data["file_path"] = str(file_path)
                book_data["file_size"] = file_path.stat().st_size
                book_data["download_date"] = datetime.now().isoformat()

                self.database.add_book(book_data)

                self.stats["books_scraped"] += 1
                self.stats["books_downloaded"] += 1

                time.sleep(self.rate_limit)
                return True

            self.stats["errors"] += 1
            return False

        except requests.RequestException as e:
            logger.warning(f"Error scraping {url}: {e}")
            self.stats["errors"] += 1
            return False
        except Exception as e:
            logger.exception(f"Unexpected error scraping {url}: {e}")
            self.stats["errors"] += 1
            return False

    def scrape_books(
        self, urls: List[str], organize_by: str = "author"
    ) -> Dict[str, int]:
        """Scrape multiple books.

        Args:
            urls: List of book page URLs
            organize_by: Organization method

        Returns:
            Dictionary with statistics
        """
        logger.info(f"Starting scrape of {len(urls)} book(s)")

        for url in urls:
            self.scrape_book(url, organize_by=organize_by)

        logger.info("Scraping complete")
        logger.info(
            f"Statistics: {self.stats['books_downloaded']} downloaded, "
            f"{self.stats['books_skipped']} skipped, {self.stats['errors']} errors"
        )

        return self.stats.copy()


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Dictionary containing configuration values

    Raises:
        FileNotFoundError: If config file does not exist
        yaml.YAMLError: If config file is invalid YAML
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config if config else {}
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in config file: {e}")
        raise


def main() -> int:
    """Main entry point for the script.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        description="Scrape public domain books and organize in database"
    )
    parser.add_argument(
        "urls",
        type=str,
        nargs="+",
        help="URLs of book pages to scrape",
    )
    parser.add_argument(
        "--database",
        type=str,
        default="books.db",
        help="Path to SQLite database file (default: books.db)",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output directory for downloaded books",
    )
    parser.add_argument(
        "--organize-by",
        type=str,
        choices=["author", "genre", "date"],
        default="author",
        help="Organization method (default: author)",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Query books from database (author, genre, or date)",
    )
    parser.add_argument(
        "--query-type",
        type=str,
        choices=["author", "genre", "date"],
        default=None,
        help="Type of query filter",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file (YAML)",
    )

    args = parser.parse_args()

    try:
        if not REQUESTS_AVAILABLE:
            logger.error("Required libraries not available. Install with: pip install requests beautifulsoup4")
            return 1

        database_path = Path(args.database)
        output_dir = Path(args.output)
        organize_by = args.organize_by
        rate_limit = args.rate_limit

        if args.config:
            config = load_config(Path(args.config))
            if "database" in config:
                database_path = Path(config["database"])
            if "output_directory" in config:
                output_dir = Path(config["output_directory"])
            if "organize_by" in config:
                organize_by = config["organize_by"]
            if "rate_limit" in config:
                rate_limit = config["rate_limit"]
            if "urls" in config:
                args.urls = config["urls"]

        database = BookDatabase(database_path)

        if args.query and args.query_type:
            books = database.get_books(**{args.query_type: args.query})
            print(f"\nFound {len(books)} book(s):")
            for book in books:
                print(f"  - {book['title']} by {book.get('author', 'Unknown')}")
            return 0

        scraper = BookScraper(
            database=database,
            output_directory=output_dir,
            rate_limit=rate_limit,
        )

        stats = scraper.scrape_books(args.urls, organize_by=organize_by)

        print("\nScraping Statistics:")
        print(f"  Books scraped: {stats['books_scraped']}")
        print(f"  Books downloaded: {stats['books_downloaded']}")
        print(f"  Books skipped: {stats['books_skipped']}")
        print(f"  Errors: {stats['errors']}")

        return 0

    except (ValueError, FileNotFoundError, ImportError) as e:
        logger.error(f"Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
