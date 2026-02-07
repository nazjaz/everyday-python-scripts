"""Unit tests for Historical Events Database application."""

import os
import shutil
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.main import (
    HistoricalDatabase,
    HistoricalDataScraper,
    HistoricalEventsManager,
    load_config,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


class TestHistoricalDatabase:
    """Test cases for HistoricalDatabase class."""

    @pytest.fixture
    def db_path(self, temp_dir):
        """Create a temporary database path."""
        return temp_dir / "test.db"

    @pytest.fixture
    def database(self, db_path):
        """Create a HistoricalDatabase instance."""
        return HistoricalDatabase(db_path)

    def test_init(self, db_path):
        """Test HistoricalDatabase initialization."""
        database = HistoricalDatabase(db_path)
        assert database.db_path == db_path
        assert db_path.exists()

    def test_insert_event(self, database):
        """Test inserting an event."""
        event = {
            "date": "1776-07-04",
            "year": 1776,
            "month": 7,
            "day": 4,
            "description": "Test event",
            "location": "USA",
            "topic": "independence",
            "source": "test",
            "url": "https://example.com",
        }

        result = database.insert_event(event)
        assert result is True

    def test_search_by_date_year(self, database):
        """Test searching by year."""
        # Insert test event
        event = {
            "date": "1776-07-04",
            "year": 1776,
            "month": 7,
            "day": 4,
            "description": "Test event",
            "location": "USA",
            "topic": "independence",
            "source": "test",
            "url": "https://example.com",
        }
        database.insert_event(event)

        results = database.search_by_date(year=1776)
        assert len(results) >= 1
        assert results[0]["year"] == 1776

    def test_search_by_date_full(self, database):
        """Test searching by full date."""
        event = {
            "date": "1776-07-04",
            "year": 1776,
            "month": 7,
            "day": 4,
            "description": "Test event",
            "location": "USA",
            "topic": "independence",
            "source": "test",
            "url": "https://example.com",
        }
        database.insert_event(event)

        results = database.search_by_date(year=1776, month=7, day=4)
        assert len(results) >= 1

    def test_search_by_location(self, database):
        """Test searching by location."""
        event = {
            "date": "1776-07-04",
            "year": 1776,
            "month": 7,
            "day": 4,
            "description": "Test event in USA",
            "location": "USA",
            "topic": "independence",
            "source": "test",
            "url": "https://example.com",
        }
        database.insert_event(event)

        results = database.search_by_location("USA")
        assert len(results) >= 1

    def test_search_by_topic(self, database):
        """Test searching by topic."""
        event = {
            "date": "1776-07-04",
            "year": 1776,
            "month": 7,
            "day": 4,
            "description": "Declaration of independence",
            "location": "USA",
            "topic": "independence",
            "source": "test",
            "url": "https://example.com",
        }
        database.insert_event(event)

        results = database.search_by_topic("independence")
        assert len(results) >= 1

    def test_get_statistics(self, database):
        """Test getting database statistics."""
        # Insert test event
        event = {
            "date": "1776-07-04",
            "year": 1776,
            "month": 7,
            "day": 4,
            "description": "Test event",
            "location": "USA",
            "topic": "independence",
            "source": "test",
            "url": "https://example.com",
        }
        database.insert_event(event)

        stats = database.get_statistics()
        assert "total_events" in stats
        assert stats["total_events"] >= 1


class TestHistoricalDataScraper:
    """Test cases for HistoricalDataScraper class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return {
            "sources": {"wikipedia": {"enabled": False}},
            "scraping": {"request_delay_seconds": 0.1, "max_retries": 2},
        }

    @pytest.fixture
    def scraper(self, config):
        """Create a HistoricalDataScraper instance."""
        return HistoricalDataScraper(config)

    def test_init(self, config):
        """Test HistoricalDataScraper initialization."""
        scraper = HistoricalDataScraper(config)
        assert scraper.config == config

    def test_parse_date(self, scraper):
        """Test date parsing."""
        # Test various date formats
        assert scraper._parse_date("1776-07-04") == (1776, 7, 4)
        assert scraper._parse_date("1776") == (1776, 1, 1)
        assert scraper._parse_date("July 4, 1776") is not None
        assert scraper._parse_date("invalid") is None

    def test_extract_location(self, scraper):
        """Test location extraction."""
        text = "Battle happened in France during the war"
        location = scraper._extract_location(text)
        assert "France" in location or location != ""

    def test_extract_topic(self, scraper):
        """Test topic extraction."""
        text = "A major battle occurred during the war"
        topic = scraper._extract_topic(text)
        assert topic in ["war", "battle", "general"]

    @patch("src.main.HistoricalDataScraper._make_request")
    def test_scrape_wikipedia_events(self, mock_request, scraper):
        """Test Wikipedia scraping with mocked request."""
        # Mock response
        mock_response = Mock()
        mock_response.content = b'<html><body><h2>1776</h2><p>Event description</p></body></html>'
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        events = scraper.scrape_wikipedia_events(limit=1)
        assert isinstance(events, list)


class TestHistoricalEventsManager:
    """Test cases for HistoricalEventsManager class."""

    @pytest.fixture
    def config(self, temp_dir):
        """Create a test configuration."""
        return {
            "database": {"path": str(temp_dir / "test.db")},
            "sources": {"wikipedia": {"enabled": False}},
            "scraping": {"request_delay_seconds": 0.1},
            "logging": {"level": "INFO", "file": str(temp_dir / "test.log")},
        }

    @pytest.fixture
    def manager(self, config):
        """Create a HistoricalEventsManager instance."""
        return HistoricalEventsManager(config)

    def test_init(self, config):
        """Test HistoricalEventsManager initialization."""
        manager = HistoricalEventsManager(config)
        assert manager.config == config

    def test_search_events(self, manager):
        """Test searching events."""
        # Insert test event
        event = {
            "date": "1776-07-04",
            "year": 1776,
            "month": 7,
            "day": 4,
            "description": "Test event",
            "location": "USA",
            "topic": "independence",
            "source": "test",
            "url": "https://example.com",
        }
        manager.database.insert_event(event)

        # Search by year
        results = manager.search_events(year=1776)
        assert isinstance(results, list)

        # Search by location
        results = manager.search_events(location="USA")
        assert isinstance(results, list)

        # Search by topic
        results = manager.search_events(topic="independence")
        assert isinstance(results, list)


class TestLoadConfig:
    """Test cases for load_config function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    def test_load_config_valid(self, temp_dir):
        """Test loading a valid configuration file."""
        config_file = temp_dir / "config.yaml"
        config_file.write_text(
            "database:\n  path: /test.db\nsources:\n  wikipedia:\n    enabled: true\n"
        )

        config = load_config(config_file)
        assert config["database"]["path"] == "/test.db"
        assert config["sources"]["wikipedia"]["enabled"] is True

    def test_load_config_nonexistent(self):
        """Test loading a nonexistent configuration file."""
        nonexistent = Path("/nonexistent/config.yaml")
        with pytest.raises(FileNotFoundError):
            load_config(nonexistent)

    def test_load_config_invalid_yaml(self, temp_dir):
        """Test loading an invalid YAML file."""
        config_file = temp_dir / "config.yaml"
        config_file.write_text("invalid: yaml: content: [unclosed")

        with pytest.raises(Exception):  # yaml.YAMLError
            load_config(config_file)
