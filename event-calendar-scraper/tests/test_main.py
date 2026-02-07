"""Unit tests for event calendar scraper."""

import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.main import EventCalendarScraper


@pytest.fixture
def temp_config_file():
    """Create temporary config file for testing."""
    config_content = """
sources:
  - name: "Test Source"
    url: "https://example.com/events"
    default_category: "test"
    selectors:
      event: ".event"
      title: ".title"
      date: ".date"
      location: ".location"
      category: ".category"

database:
  file: "test_events.db"
  create_tables: true

scraping:
  timeout: 30
  user_agent: "Test Agent"
  delay_between_sources: 0

retention:
  auto_cleanup: true
  days_to_keep: 90

logging:
  level: "DEBUG"
  file: "logs/test.log"
  max_bytes: 10485760
  backup_count: 5
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
    """Create EventCalendarScraper instance for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Update config to use temp directory
        import yaml

        with open(temp_config_file, "r") as f:
            config = yaml.safe_load(f)

        config["database"]["file"] = str(Path(temp_dir) / "test.db")
        config["logging"]["file"] = str(Path(temp_dir) / "test.log")

        with open(temp_config_file, "w") as f:
            yaml.dump(config, f)

        scraper = EventCalendarScraper(config_path=temp_config_file)
        yield scraper


class TestEventCalendarScraper:
    """Test cases for EventCalendarScraper class."""

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
            "SELECT name FROM sqlite_master WHERE type='table' AND name='events'"
        )
        assert cursor.fetchone() is not None

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='categories'"
        )
        assert cursor.fetchone() is not None

        conn.close()

    def test_parse_date_iso_format(self, scraper):
        """Test parsing ISO format date."""
        date_str = "2024-02-15"
        result = scraper._parse_date(date_str)
        assert result == "2024-02-15T00:00:00"

    def test_parse_date_slash_format(self, scraper):
        """Test parsing slash format date."""
        date_str = "02/15/2024"
        result = scraper._parse_date(date_str)
        assert result is not None

    def test_parse_date_invalid(self, scraper):
        """Test parsing invalid date format."""
        date_str = "invalid date"
        result = scraper._parse_date(date_str)
        assert result is None

    def test_save_event(self, scraper):
        """Test saving an event to database."""
        event = {
            "title": "Test Event",
            "description": "Test Description",
            "start_date": "2024-02-15T10:00:00",
            "end_date": None,
            "location": "Test Location",
            "category": "test",
            "source_url": "https://example.com",
            "source_name": "Test Source",
            "event_url": "https://example.com/event",
            "price": "Free",
        }

        result = scraper._save_event(event)
        assert result is True

        conn = sqlite3.connect(scraper.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM events WHERE title = ?", ("Test Event",))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "Test Event"
        conn.close()

    def test_save_duplicate_event(self, scraper):
        """Test that duplicate events are not saved."""
        event = {
            "title": "Duplicate Event",
            "description": "Test",
            "start_date": "2024-02-15T10:00:00",
            "end_date": None,
            "location": "Test Location",
            "category": "test",
            "source_url": "https://example.com",
            "source_name": "Test Source",
            "event_url": "",
            "price": "",
        }

        result1 = scraper._save_event(event)
        result2 = scraper._save_event(event)

        assert result1 is True
        assert result2 is False

        conn = sqlite3.connect(scraper.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events WHERE title = ?", ("Duplicate Event",))
        count = cursor.fetchone()[0]
        assert count == 1
        conn.close()

    def test_filter_events_by_date(self, scraper):
        """Test filtering events by date."""
        # Add test events
        event1 = {
            "title": "Event 1",
            "description": "",
            "start_date": "2024-02-15T10:00:00",
            "end_date": None,
            "location": "Location 1",
            "category": "test",
            "source_url": "https://example.com",
            "source_name": "Test Source",
            "event_url": "",
            "price": "",
        }
        event2 = {
            "title": "Event 2",
            "description": "",
            "start_date": "2024-03-15T10:00:00",
            "end_date": None,
            "location": "Location 2",
            "category": "test",
            "source_url": "https://example.com",
            "source_name": "Test Source",
            "event_url": "",
            "price": "",
        }

        scraper._save_event(event1)
        scraper._save_event(event2)

        # Filter by start date
        events = scraper.filter_events(start_date="2024-02-01")
        assert len(events) >= 2

        events = scraper.filter_events(start_date="2024-03-01")
        assert len(events) >= 1

    def test_filter_events_by_location(self, scraper):
        """Test filtering events by location."""
        event = {
            "title": "Location Event",
            "description": "",
            "start_date": "2024-02-15T10:00:00",
            "end_date": None,
            "location": "New York",
            "category": "test",
            "source_url": "https://example.com",
            "source_name": "Test Source",
            "event_url": "",
            "price": "",
        }

        scraper._save_event(event)

        events = scraper.filter_events(location="New York")
        assert len(events) >= 1
        assert events[0]["location"] == "New York"

        events = scraper.filter_events(location="Los Angeles")
        assert len(events) == 0

    def test_filter_events_by_category(self, scraper):
        """Test filtering events by category."""
        event = {
            "title": "Category Event",
            "description": "",
            "start_date": "2024-02-15T10:00:00",
            "end_date": None,
            "location": "Location",
            "category": "music",
            "source_url": "https://example.com",
            "source_name": "Test Source",
            "event_url": "",
            "price": "",
        }

        scraper._save_event(event)

        events = scraper.filter_events(category="music")
        assert len(events) >= 1
        assert events[0]["category"] == "music"

        events = scraper.filter_events(category="sports")
        assert len(events) == 0

    def test_get_categories(self, scraper):
        """Test getting list of categories."""
        event = {
            "title": "Test Event",
            "description": "",
            "start_date": "2024-02-15T10:00:00",
            "end_date": None,
            "location": "Location",
            "category": "music",
            "source_url": "https://example.com",
            "source_name": "Test Source",
            "event_url": "",
            "price": "",
        }

        scraper._save_event(event)

        categories = scraper.get_categories()
        assert "music" in categories

    def test_get_locations(self, scraper):
        """Test getting list of locations."""
        event = {
            "title": "Test Event",
            "description": "",
            "start_date": "2024-02-15T10:00:00",
            "end_date": None,
            "location": "San Francisco",
            "category": "test",
            "source_url": "https://example.com",
            "source_name": "Test Source",
            "event_url": "",
            "price": "",
        }

        scraper._save_event(event)

        locations = scraper.get_locations()
        assert "San Francisco" in locations

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


class TestMainFunction:
    """Test cases for main function."""

    @patch("src.main.EventCalendarScraper")
    def test_main_scrape_only(self, mock_scraper_class, temp_config_file):
        """Test main function with --scrape flag."""
        mock_scraper = MagicMock()
        mock_scraper.scrape_events.return_value = {
            "sources_processed": 1,
            "events_scraped": 5,
            "events_saved": 5,
            "errors": 0,
        }
        mock_scraper_class.return_value = mock_scraper

        from src.main import main
        import sys

        sys.argv = ["main.py", "--scrape", "-c", temp_config_file]
        result = main()

        assert result == 0
        mock_scraper.scrape_events.assert_called_once()

    @patch("src.main.EventCalendarScraper")
    def test_main_filter(self, mock_scraper_class, temp_config_file):
        """Test main function with --filter flag."""
        mock_scraper = MagicMock()
        mock_scraper.filter_events.return_value = [
            {
                "title": "Test Event",
                "start_date": "2024-02-15T10:00:00",
                "location": "Test Location",
            }
        ]
        mock_scraper_class.return_value = mock_scraper

        from src.main import main
        import sys

        sys.argv = ["main.py", "--filter", "-c", temp_config_file]
        result = main()

        assert result == 0
        mock_scraper.filter_events.assert_called_once()
