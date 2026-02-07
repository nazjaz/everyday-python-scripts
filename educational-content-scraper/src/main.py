"""Educational Content Scraper - CLI tool for scraping public domain content.

This module provides a command-line tool for scraping public domain educational
content from various sources, organizing it by subject and difficulty level,
and creating a local learning resource library.
"""

import argparse
import hashlib
import logging
import logging.handlers
import os
import re
import sys
import time
from collections import defaultdict
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


class ContentScraper:
    """Scrapes educational content from public domain sources."""

    def __init__(self, config: Dict) -> None:
        """Initialize ContentScraper.

        Args:
            config: Configuration dictionary containing scraping settings.
        """
        self.config = config
        self.sources_config = config.get("sources", {})
        self.organization_config = config.get("organization", {})
        self.scraping_config = config.get("scraping", {})

        self.library_dir = Path(
            self.organization_config.get("library_directory", "./library")
        )
        self.library_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self._setup_logging()

        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (compatible; EducationalContentScraper/1.0)"
            }
        )

        # Rate limiting
        self.request_delay = self.scraping_config.get("request_delay_seconds", 1)

    def _setup_logging(self) -> None:
        """Configure logging for the application."""
        log_level = self.config.get("logging", {}).get("level", "INFO")
        log_file = self.config.get("logging", {}).get("file", "logs/scraper.log")

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

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility.

        Args:
            filename: Original filename.

        Returns:
            Sanitized filename.
        """
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        filename = filename.strip(". ")
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        return filename

    def _categorize_subject(self, title: str, content: str = "") -> str:
        """Categorize content by subject based on title and content.

        Args:
            title: Content title.
            content: Content text (optional).

        Returns:
            Subject category.
        """
        text = (title + " " + content).lower()

        subject_keywords = self.organization_config.get("subject_keywords", {})
        for subject, keywords in subject_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return subject

        return "general"

    def _determine_difficulty(self, title: str, content: str = "") -> str:
        """Determine difficulty level based on title and content.

        Args:
            title: Content title.
            content: Content text (optional).

        Returns:
            Difficulty level: beginner, intermediate, or advanced.
        """
        text = (title + " " + content).lower()

        # Check for difficulty indicators
        beginner_keywords = [
            "introduction",
            "beginner",
            "basics",
            "getting started",
            "101",
            "elementary",
        ]
        advanced_keywords = [
            "advanced",
            "expert",
            "master",
            "graduate",
            "research",
            "thesis",
        ]

        for keyword in advanced_keywords:
            if keyword in text:
                return "advanced"

        for keyword in beginner_keywords:
            if keyword in text:
                return "beginner"

        return "intermediate"

    def _calculate_content_hash(self, content: str) -> str:
        """Calculate hash of content for duplicate detection.

        Args:
            content: Content text.

        Returns:
            MD5 hash string.
        """
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def scrape_project_gutenberg(self, limit: int = 10) -> List[Dict]:
        """Scrape content from Project Gutenberg.

        Args:
            limit: Maximum number of items to scrape.

        Returns:
            List of content dictionaries.
        """
        contents = []
        base_url = "https://www.gutenberg.org"

        try:
            # Get list of recent books
            catalog_url = f"{base_url}/browse/scores/top"
            response = self._make_request(catalog_url)

            if not response:
                return contents

            soup = BeautifulSoup(response.content, "html.parser")
            book_links = soup.find_all("a", href=re.compile(r"/ebooks/\d+"))

            for i, link in enumerate(book_links[:limit]):
                try:
                    book_url = urljoin(base_url, link["href"])
                    book_response = self._make_request(book_url)

                    if not book_response:
                        continue

                    book_soup = BeautifulSoup(book_response.content, "html.parser")
                    title_elem = book_soup.find("h1") or book_soup.find("title")
                    title = title_elem.get_text().strip() if title_elem else "Untitled"

                    # Try to get plain text version
                    text_link = book_soup.find("a", href=re.compile(r"\.txt"))
                    if text_link:
                        text_url = urljoin(book_url, text_link["href"])
                        text_response = self._make_request(text_url)

                        if text_response:
                            content = text_response.text[:50000]  # Limit content size
                            subject = self._categorize_subject(title, content[:1000])
                            difficulty = self._determine_difficulty(title, content[:1000])

                            contents.append(
                                {
                                    "title": title,
                                    "content": content,
                                    "subject": subject,
                                    "difficulty": difficulty,
                                    "source": "project_gutenberg",
                                    "url": book_url,
                                }
                            )

                            logger.info(
                                f"Scraped from Project Gutenberg: {title}",
                                extra={"title": title, "subject": subject},
                            )

                except Exception as e:
                    logger.warning(
                        f"Error scraping Project Gutenberg item: {e}",
                        extra={"error": str(e)},
                    )
                    continue

        except Exception as e:
            logger.error(
                f"Error accessing Project Gutenberg: {e}",
                extra={"error": str(e)},
            )

        return contents

    def scrape_openstax(self, limit: int = 10) -> List[Dict]:
        """Scrape content from OpenStax (example implementation).

        Args:
            limit: Maximum number of items to scrape.

        Returns:
            List of content dictionaries.
        """
        contents = []
        base_url = "https://openstax.org"

        try:
            # OpenStax books listing
            books_url = f"{base_url}/subjects"
            response = self._make_request(books_url)

            if not response:
                return contents

            soup = BeautifulSoup(response.content, "html.parser")
            book_links = soup.find_all("a", href=re.compile(r"/books/"))

            for i, link in enumerate(book_links[:limit]):
                try:
                    book_url = urljoin(base_url, link["href"])
                    book_response = self._make_request(book_url)

                    if not book_response:
                        continue

                    book_soup = BeautifulSoup(book_response.content, "html.parser")
                    title_elem = book_soup.find("h1") or book_soup.find("title")
                    title = title_elem.get_text().strip() if title_elem else "Untitled"

                    # Extract main content
                    content_elem = book_soup.find("main") or book_soup.find("article")
                    if content_elem:
                        content = content_elem.get_text()[:50000]
                        subject = self._categorize_subject(title, content[:1000])
                        difficulty = self._determine_difficulty(title, content[:1000])

                        contents.append(
                            {
                                "title": title,
                                "content": content,
                                "subject": subject,
                                "difficulty": difficulty,
                                "source": "openstax",
                                "url": book_url,
                            }
                        )

                        logger.info(
                            f"Scraped from OpenStax: {title}",
                            extra={"title": title, "subject": subject},
                        )

                except Exception as e:
                    logger.warning(
                        f"Error scraping OpenStax item: {e}",
                        extra={"error": str(e)},
                    )
                    continue

        except Exception as e:
            logger.error(
                f"Error accessing OpenStax: {e}",
                extra={"error": str(e)},
            )

        return contents

    def scrape_custom_source(self, source_config: Dict) -> List[Dict]:
        """Scrape content from a custom source.

        Args:
            source_config: Source configuration dictionary.

        Returns:
            List of content dictionaries.
        """
        contents = []
        base_url = source_config.get("base_url", "")
        list_url = source_config.get("list_url", "")
        content_selector = source_config.get("content_selector", "body")
        title_selector = source_config.get("title_selector", "h1")

        if not base_url or not list_url:
            return contents

        try:
            response = self._make_request(list_url)
            if not response:
                return contents

            soup = BeautifulSoup(response.content, "html.parser")
            links = soup.find_all("a", href=True)

            limit = source_config.get("limit", 10)
            for link in links[:limit]:
                try:
                    content_url = urljoin(base_url, link["href"])
                    content_response = self._make_request(content_url)

                    if not content_response:
                        continue

                    content_soup = BeautifulSoup(content_response.content, "html.parser")
                    title_elem = content_soup.select_one(title_selector)
                    title = title_elem.get_text().strip() if title_elem else "Untitled"

                    content_elem = content_soup.select_one(content_selector)
                    if content_elem:
                        content = content_elem.get_text()[:50000]
                        subject = self._categorize_subject(title, content[:1000])
                        difficulty = self._determine_difficulty(title, content[:1000])

                        contents.append(
                            {
                                "title": title,
                                "content": content,
                                "subject": subject,
                                "difficulty": difficulty,
                                "source": source_config.get("name", "custom"),
                                "url": content_url,
                            }
                        )

                except Exception as e:
                    logger.warning(
                        f"Error scraping custom source item: {e}",
                        extra={"error": str(e)},
                    )
                    continue

        except Exception as e:
            logger.error(
                f"Error accessing custom source: {e}",
                extra={"error": str(e)},
            )

        return contents

    def save_content(self, content: Dict) -> bool:
        """Save content to library with proper organization.

        Args:
            content: Content dictionary.

        Returns:
            True if saved successfully, False otherwise.
        """
        try:
            # Create directory structure: library/subject/difficulty/
            subject_dir = self.library_dir / content["subject"]
            difficulty_dir = subject_dir / content["difficulty"]
            difficulty_dir.mkdir(parents=True, exist_ok=True)

            # Sanitize filename
            filename = self._sanitize_filename(content["title"])
            file_path = difficulty_dir / f"{filename}.txt"

            # Check for duplicates
            content_hash = self._calculate_content_hash(content["content"])
            hash_file = difficulty_dir / ".hashes.txt"

            # Read existing hashes
            existing_hashes = set()
            if hash_file.exists():
                try:
                    with open(hash_file, "r") as f:
                        existing_hashes = set(line.strip() for line in f)
                except (OSError, IOError):
                    pass

            # Skip if duplicate
            if content_hash in existing_hashes:
                logger.info(
                    f"Skipping duplicate content: {content['title']}",
                    extra={"title": content["title"]},
                )
                return False

            # Save content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"Title: {content['title']}\n")
                f.write(f"Source: {content['source']}\n")
                f.write(f"URL: {content.get('url', 'N/A')}\n")
                f.write(f"Subject: {content['subject']}\n")
                f.write(f"Difficulty: {content['difficulty']}\n")
                f.write(f"Scraped: {datetime.now().isoformat()}\n")
                f.write("-" * 80 + "\n\n")
                f.write(content["content"])

            # Save hash
            with open(hash_file, "a") as f:
                f.write(f"{content_hash}\n")

            logger.info(
                f"Saved content: {content['title']} -> "
                f"{content['subject']}/{content['difficulty']}/",
                extra={
                    "title": content["title"],
                    "subject": content["subject"],
                    "difficulty": content["difficulty"],
                },
            )
            return True

        except (OSError, IOError, PermissionError) as e:
            logger.error(
                f"Failed to save content {content['title']}: {e}",
                extra={"title": content["title"], "error": str(e)},
            )
            return False

    def scrape_all_sources(self, dry_run: bool = False) -> Dict[str, int]:
        """Scrape content from all configured sources.

        Args:
            dry_run: If True, only report what would be scraped.

        Returns:
            Dictionary with scraping statistics.
        """
        results = {
            "scraped": 0,
            "saved": 0,
            "duplicates": 0,
            "failed": 0,
        }

        # Scrape from Project Gutenberg if enabled
        if self.sources_config.get("project_gutenberg", {}).get("enabled", False):
            limit = self.sources_config.get("project_gutenberg", {}).get("limit", 10)
            logger.info(f"Scraping from Project Gutenberg (limit: {limit})")
            contents = self.scrape_project_gutenberg(limit=limit)
            results["scraped"] += len(contents)

            if not dry_run:
                for content in contents:
                    if self.save_content(content):
                        results["saved"] += 1
                    else:
                        results["duplicates"] += 1

        # Scrape from OpenStax if enabled
        if self.sources_config.get("openstax", {}).get("enabled", False):
            limit = self.sources_config.get("openstax", {}).get("limit", 10)
            logger.info(f"Scraping from OpenStax (limit: {limit})")
            contents = self.scrape_openstax(limit=limit)
            results["scraped"] += len(contents)

            if not dry_run:
                for content in contents:
                    if self.save_content(content):
                        results["saved"] += 1
                    else:
                        results["duplicates"] += 1

        # Scrape from custom sources
        custom_sources = self.sources_config.get("custom_sources", [])
        for source_config in custom_sources:
            if source_config.get("enabled", False):
                logger.info(f"Scraping from custom source: {source_config.get('name')}")
                contents = self.scrape_custom_source(source_config)
                results["scraped"] += len(contents)

                if not dry_run:
                    for content in contents:
                        if self.save_content(content):
                            results["saved"] += 1
                        else:
                            results["duplicates"] += 1

        return results


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
        description="Scrape public domain educational content and create "
        "local learning resource library"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Perform a dry run without saving content",
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

    scraper = ContentScraper(config)

    if args.dry_run:
        logger.info("Running in dry-run mode - no content will be saved")

    results = scraper.scrape_all_sources(dry_run=args.dry_run)

    # Print summary
    print("\n" + "=" * 60)
    print("Scraping Summary")
    print("=" * 60)
    print(f"Content scraped: {results['scraped']}")
    print(f"Content saved: {results['saved']}")
    print(f"Duplicates skipped: {results['duplicates']}")
    print(f"Failed: {results['failed']}")
    print("=" * 60)

    if results["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
