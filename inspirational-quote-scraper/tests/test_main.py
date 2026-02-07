"""Unit tests for inspirational quote scraper."""

import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.main import QuoteScraper


@pytest.fixture
def temp_config_file():
    """Create temporary config file for testing."""
    config_content = """
sources:
  - name: "Test Source"
    url: "https://example.com/quotes"
    category: "inspirational"
    selectors:
      quote: ".quote"
      text: ".quote-text"
      author: ".author"

database:
  file: "test_quotes.db"
  create_tables: true

scraping:
  timeout: 30
  user_agent: "Test Agent"
  delay_between_sources: 0
  min_quote_length: 10
  max_quote_length: 500

display:
  recent_days_avoid: 30

notifications:
  enabled: false
  title: "Test Quote"
  timeout: 5
  max_length: 200

logging:
  level: "DEBUG"
  file: "logs/test.log"
  max_bytes: 10485760
  backup_count: 5

retention:
  auto_cleanup: true
  days_to_keep: 90
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        f.write(config_content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def scraper(temp_config_file):
    """Create QuoteScraper instance for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Update config to use temp directory
        import yaml

        with open(temp_config_file, "r") as f:
            config = yaml.safe_load(f)

        config["database"]["file"] = str(Path(temp_dir) / "test.db")
        config["logging"]["file"] = str(Path(temp_dir) / "test.log")

        with open(temp_config_file, "w") as f:
            yaml.dump(config, f)

        scraper = QuoteScraper(config_path=temp_config_file)
        yield scraper


class TestQuoteScraper:
    """Test cases for QuoteScraper class."""

    def test_init_loads_config(self, scraper):
        """Test that scraper loads configuration correctly."""
        assert scraper.config is not None
        assert "sources" in scraper.config
        assert "database" in scraper.config

    def test_database_creation(self, scraper):
        """Test that database tables are created."""
        conn = sqlite3.connect(scraper.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='quotes'"
        )
        assert cursor.fetchone() is not None

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='daily_quotes'"
        )
        assert cursor.fetchone() is not None

        conn.close()

    def test_save_quote(self, scraper):
        """Test saving a quote to database."""
        quote = {
            "text": "Test quote text",
            "author": "Test Author",
            "source_url": "https://example.com",
            "source_name": "Test Source",
            "category": "inspirational",
        }

        result = scraper._save_quote(quote)
        assert result is True

        conn = sqlite3.connect(scraper.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT text, author FROM quotes WHERE text = ?", (quote["text"],))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == quote["text"]
        assert row[1] == quote["author"]
        conn.close()

    def test_save_duplicate_quote(self, scraper):
        """Test that duplicate quotes are not saved."""
        quote = {
            "text": "Duplicate test quote",
            "author": "Test Author",
            "source_url": "https://example.com",
            "source_name": "Test Source",
            "category": "inspirational",
        }

        result1 = scraper._save_quote(quote)
        result2 = scraper._save_quote(quote)

        assert result1 is True
        assert result2 is False

        conn = sqlite3.connect(scraper.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM quotes WHERE text = ?", (quote["text"],))
        count = cursor.fetchone()[0]
        assert count == 1
        conn.close()

    def test_extract_text_with_selector(self, scraper):
        """Test text extraction with CSS selector."""
        from bs4 import BeautifulSoup

        html = '<div class="quote"><span class="text">Test quote</span></div>'
        soup = BeautifulSoup(html, "html.parser")
        element = soup.select_one(".quote")

        text = scraper._extract_text(element, ".text")
        assert text == "Test quote"

    def test_extract_text_without_selector(self, scraper):
        """Test text extraction without CSS selector."""
        from bs4 import BeautifulSoup

        html = '<div class="quote">Direct text</div>'
        soup = BeautifulSoup(html, "html.parser")
        element = soup.select_one(".quote")

        text = scraper._extract_text(element, "")
        assert text == "Direct text"

    @patch("src.main.requests.get")
    def test_fetch_page_success(self, mock_get, scraper):
        """Test successful page fetch."""
        mock_response = Mock()
        mock_response.content = b"<html><body>Test</body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        soup = scraper._fetch_page("https://example.com")
        assert soup is not None
        mock_get.assert_called_once()

    @patch("src.main.requests.get")
    def test_fetch_page_failure(self, mock_get, scraper):
        """Test page fetch failure handling."""
        mock_get.side_effect = Exception("Connection error")

        soup = scraper._fetch_page("https://example.com")
        assert soup is None
        assert scraper.stats["errors"] > 0

    def test_get_daily_quote_no_quotes(self, scraper):
        """Test getting daily quote when no quotes exist."""
        quote = scraper.get_daily_quote()
        assert quote is None

    def test_get_daily_quote_with_quotes(self, scraper):
        """Test getting daily quote when quotes exist."""
        # Add a quote to database
        quote = {
            "text": "Test daily quote",
            "author": "Test Author",
            "source_url": "https://example.com",
            "source_name": "Test Source",
            "category": "inspirational",
        }
        scraper._save_quote(quote)

        daily_quote = scraper.get_daily_quote()
        assert daily_quote is not None
        assert daily_quote["text"] == quote["text"]
        assert daily_quote["author"] == quote["author"]

    def test_get_daily_quote_same_date(self, scraper):
        """Test that same quote is returned for same date."""
        quote = {
            "text": "Test daily quote",
            "author": "Test Author",
            "source_url": "https://example.com",
            "source_name": "Test Source",
            "category": "inspirational",
        }
        scraper._save_quote(quote)

        quote1 = scraper.get_daily_quote()
        quote2 = scraper.get_daily_quote()

        assert quote1 is not None
        assert quote2 is not None
        assert quote1["id"] == quote2["id"]

    @patch("src.main.notification.notify")
    def test_send_notification(self, mock_notify, scraper):
        """Test sending desktop notification."""
        quote = {
            "text": "Test notification quote",
            "author": "Test Author",
            "category": "inspirational",
        }

        scraper._send_notification(quote)
        mock_notify.assert_called_once()

    def test_display_quote(self, scraper, capsys):
        """Test displaying quote in console."""
        quote = {
            "text": "Test display quote",
            "author": "Test Author",
            "category": "inspirational",
            "source_name": "Test Source",
        }

        scraper.display_quote(quote)
        captured = capsys.readouterr()
        assert "Test display quote" in captured.out
        assert "Test Author" in captured.out

    def test_cleanup_old_entries(self, scraper):
        """Test cleanup of old daily quote entries."""
        # Add a quote
        quote = {
            "text": "Old quote",
            "author": "Test Author",
            "source_url": "https://example.com",
            "source_name": "Test Source",
            "category": "inspirational",
        }
        scraper._save_quote(quote)

        # Add old daily quote entry
        conn = sqlite3.connect(scraper.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM quotes LIMIT 1")
        quote_id = cursor.fetchone()[0]

        old_date = (datetime.now() - scraper.config["retention"]["days_to_keep"] - timedelta(days=1)).strftime("%Y-%m-%d")
        cursor.execute(
            "INSERT INTO daily_quotes (quote_id, display_date) VALUES (?, ?)",
            (quote_id, old_date),
        )
        conn.commit()
        conn.close()

        # Run cleanup
        scraper._cleanup_old_entries()

        # Verify old entry is removed
        conn = sqlite3.connect(scraper.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM daily_quotes WHERE display_date = ?", (old_date,))
        count = cursor.fetchone()[0]
        assert count == 0
        conn.close()


class TestMainFunction:
    """Test cases for main function."""

    @patch("src.main.QuoteScraper")
    def test_main_scrape_only(self, mock_scraper_class, temp_config_file):
        """Test main function with --scrape flag."""
        mock_scraper = MagicMock()
        mock_scraper.scrape_quotes.return_value = {
            "sources_processed": 1,
            "quotes_scraped": 5,
            "quotes_saved": 5,
            "errors": 0,
        }
        mock_scraper_class.return_value = mock_scraper

        from src.main import main
        import sys

        sys.argv = ["main.py", "--scrape", "-c", temp_config_file]
        result = main()

        assert result == 0
        mock_scraper.scrape_quotes.assert_called_once()

    @patch("src.main.QuoteScraper")
    def test_main_display_only(self, mock_scraper_class, temp_config_file):
        """Test main function with --display flag."""
        mock_scraper = MagicMock()
        mock_scraper.get_daily_quote.return_value = {
            "text": "Test quote",
            "author": "Test Author",
        }
        mock_scraper_class.return_value = mock_scraper

        from src.main import main
        import sys

        sys.argv = ["main.py", "--display", "-c", temp_config_file]
        result = main()

        assert result == 0
        mock_scraper.get_daily_quote.assert_called_once()
        mock_scraper.display_quote.assert_called_once()
