"""Unit tests for transit schedule scraper."""

import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.main import TransitScheduleScraper


class TestTransitScheduleScraper(unittest.TestCase):
    """Test cases for TransitScheduleScraper class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.yaml")
        self.db_path = os.path.join(self.temp_dir, "test_transit.db")

        # Create test config
        config_content = f"""
default_transit_system: "test_system"

transit_systems:
  test_system:
    base_url: "https://test-transit.com"
    url_template: "{{base_url}}/schedule?route={{route_id}}&stop={{stop_id}}"
    selectors:
      departure_row: "tr.departure"
      time: ".time"
      route: ".route"
      destination: ".destination"
      delay: ".delay"

scraping:
  timeout: 30
  delay: 1
  user_agent: "Test Agent"

database:
  file: "{self.db_path}"
  create_tables: true

logging:
  level: "DEBUG"
  file: "{os.path.join(self.temp_dir, 'test.log')}"
  max_bytes: 1048576
  backup_count: 3
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
"""
        with open(self.config_path, "w") as f:
            f.write(config_content)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_loads_config(self) -> None:
        """Test that initialization loads configuration correctly."""
        scraper = TransitScheduleScraper(config_path=self.config_path)
        self.assertEqual(scraper.config["default_transit_system"], "test_system")
        self.assertEqual(scraper.config["database"]["file"], self.db_path)

    def test_init_creates_database_tables(self) -> None:
        """Test that initialization creates database tables."""
        scraper = TransitScheduleScraper(config_path=self.config_path)
        self.assertTrue(os.path.exists(self.db_path))

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('routes', 'stops', 'departures')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        self.assertIn("routes", tables)
        self.assertIn("stops", tables)
        self.assertIn("departures", tables)

    def test_parse_time_string_24_hour(self) -> None:
        """Test parsing 24-hour time format."""
        scraper = TransitScheduleScraper(config_path=self.config_path)

        time_str = "14:30"
        result = scraper._parse_time_string(time_str)
        self.assertIsNotNone(result)
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 30)

    def test_parse_time_string_12_hour(self) -> None:
        """Test parsing 12-hour time format."""
        scraper = TransitScheduleScraper(config_path=self.config_path)

        time_str = "2:30 PM"
        result = scraper._parse_time_string(time_str)
        self.assertIsNotNone(result)
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 30)

    def test_parse_time_string_relative(self) -> None:
        """Test parsing relative time format."""
        scraper = TransitScheduleScraper(config_path=self.config_path)

        time_str = "5 min"
        result = scraper._parse_time_string(time_str)
        self.assertIsNotNone(result)

        # Should be approximately 5 minutes from now
        now = datetime.now()
        expected = now + timedelta(minutes=5)
        delta = abs((result - expected).total_seconds())
        self.assertLess(delta, 10)  # Within 10 seconds

    def test_parse_time_string_invalid(self) -> None:
        """Test parsing invalid time string."""
        scraper = TransitScheduleScraper(config_path=self.config_path)

        time_str = "invalid time"
        result = scraper._parse_time_string(time_str)
        self.assertIsNone(result)

    def test_format_time_until(self) -> None:
        """Test formatting time until departure."""
        scraper = TransitScheduleScraper(config_path=self.config_path)

        # Test future time
        future_time = datetime.now() + timedelta(minutes=15)
        result = scraper._format_time_until(future_time)
        self.assertIn("min", result)

        # Test past time
        past_time = datetime.now() - timedelta(minutes=5)
        result = scraper._format_time_until(past_time)
        self.assertEqual(result, "Departed")

    @patch("src.main.TransitScheduleScraper._fetch_page")
    def test_scrape_departures(self, mock_fetch) -> None:
        """Test scraping departures from HTML."""
        scraper = TransitScheduleScraper(config_path=self.config_path)

        # Mock HTML response
        from bs4 import BeautifulSoup

        html = """
        <html>
            <body>
                <tr class="departure">
                    <td class="time">14:30</td>
                    <td class="route">Route 1</td>
                    <td class="destination">Downtown</td>
                    <td class="delay">On time</td>
                </tr>
                <tr class="departure">
                    <td class="time">14:45</td>
                    <td class="route">Route 1</td>
                    <td class="destination">Downtown</td>
                    <td class="delay">+2 min</td>
                </tr>
            </body>
        </html>
        """
        mock_soup = BeautifulSoup(html, "html.parser")
        mock_fetch.return_value = mock_soup

        departures = scraper.scrape_departures("1", "12345")

        self.assertGreater(len(departures), 0)
        self.assertEqual(departures[0]["route_id"], "1")
        self.assertEqual(departures[0]["stop_id"], "12345")

    @patch("src.main.TransitScheduleScraper._fetch_page")
    def test_scrape_departures_no_data(self, mock_fetch) -> None:
        """Test scraping when no departures found."""
        scraper = TransitScheduleScraper(config_path=self.config_path)

        from bs4 import BeautifulSoup

        html = "<html><body><p>No departures</p></body></html>"
        mock_soup = BeautifulSoup(html, "html.parser")
        mock_fetch.return_value = mock_soup

        departures = scraper.scrape_departures("1", "12345")
        self.assertEqual(len(departures), 0)

    @patch("src.main.TransitScheduleScraper._fetch_page")
    def test_scrape_departures_fetch_fails(self, mock_fetch) -> None:
        """Test scraping when page fetch fails."""
        scraper = TransitScheduleScraper(config_path=self.config_path)

        mock_fetch.return_value = None

        departures = scraper.scrape_departures("1", "12345")
        self.assertEqual(len(departures), 0)

    def test_save_departure(self) -> None:
        """Test saving departure to database."""
        scraper = TransitScheduleScraper(config_path=self.config_path)

        departure = {
            "route_id": "1",
            "stop_id": "12345",
            "departure_time": datetime.now().isoformat(),
            "scheduled_time": "14:30",
            "route_name": "Route 1",
            "destination": "Downtown",
            "delay": "",
            "transit_system": "test_system",
        }

        result = scraper._save_departure(departure)
        self.assertTrue(result)

        # Verify in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM departures")
        count = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(count, 1)

    def test_get_next_departures(self) -> None:
        """Test getting next departures from database."""
        scraper = TransitScheduleScraper(config_path=self.config_path)

        # Add a future departure
        future_time = datetime.now() + timedelta(minutes=30)
        departure = {
            "route_id": "1",
            "stop_id": "12345",
            "departure_time": future_time.isoformat(),
            "scheduled_time": future_time.strftime("%H:%M"),
            "route_name": "Route 1",
            "destination": "Downtown",
            "delay": "",
            "transit_system": "test_system",
        }
        scraper._save_departure(departure)

        departures = scraper.get_next_departures("1", "12345", limit=5)
        self.assertGreater(len(departures), 0)
        self.assertIn("departure_datetime", departures[0])
        self.assertIn("time_until", departures[0])

    def test_config_file_not_found(self) -> None:
        """Test error handling for missing config file."""
        with self.assertRaises(FileNotFoundError):
            TransitScheduleScraper(config_path="nonexistent_config.yaml")

    @patch("src.main.requests.Session.get")
    def test_fetch_page_success(self, mock_get) -> None:
        """Test successful page fetch."""
        scraper = TransitScheduleScraper(config_path=self.config_path)

        mock_response = Mock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.encoding = "utf-8"
        mock_response.apparent_encoding = "utf-8"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        soup = scraper._fetch_page("https://test.com")
        self.assertIsNotNone(soup)

    @patch("src.main.requests.Session.get")
    def test_fetch_page_error(self, mock_get) -> None:
        """Test page fetch error handling."""
        scraper = TransitScheduleScraper(config_path=self.config_path)

        import requests

        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        soup = scraper._fetch_page("https://test.com")
        self.assertIsNone(soup)


if __name__ == "__main__":
    unittest.main()
