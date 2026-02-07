"""Unit tests for Book Scraper."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import BookScraper


@pytest.fixture
def sample_config():
    """Create sample configuration dictionary."""
    return {
        "data": {"directory": "data"},
        "scraping": {
            "timeout": 30,
            "delay": 1,
            "headers": {},
            "selectors": {
                "title": "h1",
                "author": ".author",
                "isbn": ".isbn",
                "publication_date": ".date",
                "publisher": ".publisher",
                "description": ".description",
                "pages": ".pages",
                "genres": ".genre",
            },
        },
        "reading_list": {
            "auto_save": True,
            "backup_enabled": True,
            "backup_count": 5,
        },
        "progress": {"auto_update_status": True},
        "logging": {
            "level": "INFO",
            "file": "logs/test.log",
            "max_bytes": 10485760,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }


@pytest.fixture
def temp_config_file(sample_config, tmp_path):
    """Create temporary configuration file."""
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(sample_config, f)
    return str(config_path)


@pytest.fixture
def sample_html():
    """Create sample HTML for book page."""
    return """
    <html>
        <head>
            <meta property="og:title" content="Test Book Title">
            <meta property="og:description" content="Test book description">
        </head>
        <body>
            <h1>Test Book Title</h1>
            <div class="author">Test Author</div>
            <div class="isbn">ISBN: 1234567890123</div>
            <div class="pages">300 pages</div>
            <div class="publisher">Test Publisher</div>
            <div class="description">This is a test book description.</div>
            <div class="date">2024-01-01</div>
            <div class="genre">Fiction</div>
            <div class="genre">Science Fiction</div>
        </body>
    </html>
    """


class TestBookScraper:
    """Test cases for BookScraper class."""

    def test_init_loads_config(self, temp_config_file):
        """Test that initialization loads configuration file."""
        scraper = BookScraper(config_path=temp_config_file)
        assert scraper.config is not None
        assert "data" in scraper.config

    def test_init_raises_file_not_found(self):
        """Test that initialization raises error for missing config file."""
        with pytest.raises(FileNotFoundError):
            BookScraper(config_path="nonexistent.yaml")

    def test_get_book_id(self, temp_config_file):
        """Test book ID generation."""
        scraper = BookScraper(config_path=temp_config_file)
        book_id = scraper._get_book_id("Test Book", "Test Author")
        assert isinstance(book_id, str)
        assert len(book_id) > 0

    def test_get_book_id_same_input_same_output(self, temp_config_file):
        """Test that same input produces same ID."""
        scraper = BookScraper(config_path=temp_config_file)
        id1 = scraper._get_book_id("Test Book", "Test Author")
        id2 = scraper._get_book_id("Test Book", "Test Author")
        assert id1 == id2

    @patch("src.main.BookScraper._fetch_page")
    def test_extract_book_info(self, mock_fetch, temp_config_file, sample_html):
        """Test book information extraction from HTML."""
        from bs4 import BeautifulSoup

        scraper = BookScraper(config_path=temp_config_file)
        soup = BeautifulSoup(sample_html, "html.parser")

        book_info = scraper._extract_book_info(soup, "http://example.com/book")

        assert book_info["title"] == "Test Book Title"
        assert book_info["author"] == "Test Author"
        assert "1234567890123" in book_info["isbn"]
        assert book_info["pages"] == 300
        assert "Fiction" in book_info["genres"]

    @patch("src.main.BookScraper._fetch_page")
    def test_scrape_book_success(self, mock_fetch, temp_config_file, sample_html):
        """Test successful book scraping."""
        from bs4 import BeautifulSoup

        scraper = BookScraper(config_path=temp_config_file)
        soup = BeautifulSoup(sample_html, "html.parser")
        mock_fetch.return_value = soup

        book_info = scraper.scrape_book("http://example.com/book")

        assert book_info is not None
        assert book_info["title"] == "Test Book Title"
        assert book_info["author"] == "Test Author"

    @patch("src.main.BookScraper._fetch_page")
    def test_scrape_book_failure(self, mock_fetch, temp_config_file):
        """Test book scraping when fetch fails."""
        scraper = BookScraper(config_path=temp_config_file)
        mock_fetch.return_value = None

        book_info = scraper.scrape_book("http://example.com/book")

        assert book_info is None

    def test_add_book(self, temp_config_file, tmp_path):
        """Test adding book to reading list."""
        scraper = BookScraper(config_path=temp_config_file)
        scraper.reading_list_path = tmp_path / "reading_list.json"
        scraper._load_reading_list()

        book_info = {
            "title": "Test Book",
            "author": "Test Author",
            "pages": 300,
        }

        book_id = scraper.add_book(book_info)

        assert book_id in scraper.reading_list
        assert scraper.reading_list[book_id]["title"] == "Test Book"
        assert scraper.reading_list[book_id]["status"] == "to_read"

    def test_add_book_missing_title(self, temp_config_file):
        """Test adding book without title raises error."""
        scraper = BookScraper(config_path=temp_config_file)
        scraper._load_reading_list()

        book_info = {"author": "Test Author"}

        with pytest.raises(ValueError):
            scraper.add_book(book_info)

    def test_update_progress_by_pages(self, temp_config_file, tmp_path):
        """Test updating progress by pages read."""
        scraper = BookScraper(config_path=temp_config_file)
        scraper.reading_list_path = tmp_path / "reading_list.json"
        scraper._load_reading_list()

        book_info = {
            "title": "Test Book",
            "author": "Test Author",
            "pages": 300,
        }
        book_id = scraper.add_book(book_info)

        scraper.update_progress(book_id, pages_read=150)

        progress = scraper.reading_list[book_id]["progress"]
        assert progress["pages_read"] == 150
        assert progress["percentage"] == 50.0
        assert scraper.reading_list[book_id]["status"] == "reading"

    def test_update_progress_by_percentage(self, temp_config_file, tmp_path):
        """Test updating progress by percentage."""
        scraper = BookScraper(config_path=temp_config_file)
        scraper.reading_list_path = tmp_path / "reading_list.json"
        scraper._load_reading_list()

        book_info = {
            "title": "Test Book",
            "author": "Test Author",
            "pages": 300,
        }
        book_id = scraper.add_book(book_info)

        scraper.update_progress(book_id, percentage=75.0)

        progress = scraper.reading_list[book_id]["progress"]
        assert progress["percentage"] == 75.0
        assert progress["pages_read"] == 225

    def test_update_progress_completes_book(self, temp_config_file, tmp_path):
        """Test that updating progress to 100% completes book."""
        scraper = BookScraper(config_path=temp_config_file)
        scraper.reading_list_path = tmp_path / "reading_list.json"
        scraper._load_reading_list()

        book_info = {
            "title": "Test Book",
            "author": "Test Author",
            "pages": 300,
        }
        book_id = scraper.add_book(book_info)

        scraper.update_progress(book_id, pages_read=300)

        assert scraper.reading_list[book_id]["status"] == "completed"
        progress = scraper.reading_list[book_id]["progress"]
        assert progress["completed_date"] is not None

    def test_update_progress_invalid_pages(self, temp_config_file, tmp_path):
        """Test updating progress with invalid pages raises error."""
        scraper = BookScraper(config_path=temp_config_file)
        scraper.reading_list_path = tmp_path / "reading_list.json"
        scraper._load_reading_list()

        book_info = {
            "title": "Test Book",
            "author": "Test Author",
            "pages": 300,
        }
        book_id = scraper.add_book(book_info)

        with pytest.raises(ValueError):
            scraper.update_progress(book_id, pages_read=500)

    def test_update_status(self, temp_config_file, tmp_path):
        """Test updating book status."""
        scraper = BookScraper(config_path=temp_config_file)
        scraper.reading_list_path = tmp_path / "reading_list.json"
        scraper._load_reading_list()

        book_info = {
            "title": "Test Book",
            "author": "Test Author",
        }
        book_id = scraper.add_book(book_info)

        scraper.update_status(book_id, "reading")

        assert scraper.reading_list[book_id]["status"] == "reading"

    def test_update_status_invalid(self, temp_config_file, tmp_path):
        """Test updating status with invalid value raises error."""
        scraper = BookScraper(config_path=temp_config_file)
        scraper.reading_list_path = tmp_path / "reading_list.json"
        scraper._load_reading_list()

        book_info = {
            "title": "Test Book",
            "author": "Test Author",
        }
        book_id = scraper.add_book(book_info)

        with pytest.raises(ValueError):
            scraper.update_status(book_id, "invalid_status")

    def test_add_note(self, temp_config_file, tmp_path):
        """Test adding note to book."""
        scraper = BookScraper(config_path=temp_config_file)
        scraper.reading_list_path = tmp_path / "reading_list.json"
        scraper._load_reading_list()

        book_info = {
            "title": "Test Book",
            "author": "Test Author",
        }
        book_id = scraper.add_book(book_info)

        scraper.add_note(book_id, "Test note")

        assert "Test note" in scraper.reading_list[book_id]["notes"]

    def test_get_reading_list(self, temp_config_file, tmp_path):
        """Test getting reading list."""
        scraper = BookScraper(config_path=temp_config_file)
        scraper.reading_list_path = tmp_path / "reading_list.json"
        scraper._load_reading_list()

        book_info1 = {"title": "Book 1", "author": "Author 1"}
        book_info2 = {"title": "Book 2", "author": "Author 2"}

        scraper.add_book(book_info1, status="to_read")
        scraper.add_book(book_info2, status="reading")

        books = scraper.get_reading_list()
        assert len(books) == 2

        reading_books = scraper.get_reading_list(status="reading")
        assert len(reading_books) == 1
        assert reading_books[0]["title"] == "Book 2"

    def test_get_book(self, temp_config_file, tmp_path):
        """Test getting book by ID."""
        scraper = BookScraper(config_path=temp_config_file)
        scraper.reading_list_path = tmp_path / "reading_list.json"
        scraper._load_reading_list()

        book_info = {
            "title": "Test Book",
            "author": "Test Author",
        }
        book_id = scraper.add_book(book_info)

        book = scraper.get_book(book_id)
        assert book is not None
        assert book["title"] == "Test Book"

        nonexistent = scraper.get_book("nonexistent_id")
        assert nonexistent is None

    def test_delete_book(self, temp_config_file, tmp_path):
        """Test deleting book from reading list."""
        scraper = BookScraper(config_path=temp_config_file)
        scraper.reading_list_path = tmp_path / "reading_list.json"
        scraper._load_reading_list()

        book_info = {
            "title": "Test Book",
            "author": "Test Author",
        }
        book_id = scraper.add_book(book_info)

        assert book_id in scraper.reading_list

        scraper.delete_book(book_id)

        assert book_id not in scraper.reading_list

    def test_delete_book_not_found(self, temp_config_file):
        """Test deleting non-existent book raises error."""
        scraper = BookScraper(config_path=temp_config_file)
        scraper._load_reading_list()

        with pytest.raises(KeyError):
            scraper.delete_book("nonexistent_id")
