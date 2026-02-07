"""Unit tests for price tracker module."""

import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import PriceTracker


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    return tempfile.mkdtemp()


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary configuration file."""
    db_file = Path(temp_dir) / "test.db"
    config = {
        "database": {
            "file": str(db_file),
            "create_tables": True,
        },
        "products": [
            {
                "name": "Test Product",
                "url": "https://example.com/product",
                "website": "example",
                "enabled": True,
                "price_selector": ".price",
                "title_selector": "h1",
            }
        ],
        "website_selectors": {
            "example": {
                "price_selector": ".price",
                "title_selector": "h1",
                "currency_symbol": "$",
            }
        },
        "scraping": {
            "interval": 3600,
            "timeout": 30,
            "user_agent": "Price-Tracker/1.0",
            "retry_attempts": 3,
            "retry_delay": 5,
        },
        "price_tracking": {
            "track_all_changes": True,
            "min_change_percent": 0,
        },
        "retention": {
            "days_to_keep": 365,
            "auto_cleanup": True,
        },
        "logging": {
            "level": "DEBUG",
            "file": f"{temp_dir}/test.log",
            "max_bytes": 1048576,
            "backup_count": 3,
        },
        "reporting": {
            "generate_reports": True,
            "report_file": f"{temp_dir}/report.txt",
        },
    }

    config_path = Path(temp_dir) / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config_path


def test_price_tracker_initialization(config_file):
    """Test PriceTracker initializes correctly."""
    tracker = PriceTracker(config_path=str(config_file))
    assert tracker.db_path.exists()
    assert tracker.stats["products_checked"] == 0


def test_price_tracker_missing_config():
    """Test PriceTracker raises error for missing config."""
    with pytest.raises(FileNotFoundError):
        PriceTracker(config_path="nonexistent.yaml")


def test_parse_price():
    """Test price parsing from text."""
    from src.main import PriceTracker

    tracker = PriceTracker.__new__(PriceTracker)

    assert tracker._parse_price("$19.99") == 19.99
    assert tracker._parse_price("19.99") == 19.99
    assert tracker._parse_price("1,234.56") == 1234.56
    assert tracker._parse_price("€25,50") == 25.50
    assert tracker._parse_price("invalid") is None


def test_get_product_id(config_file):
    """Test getting product ID from database."""
    tracker = PriceTracker(config_path=str(config_file))

    # Add product
    product_id = tracker._add_product("Test Product", "https://example.com/test", "example")

    # Get product ID
    retrieved_id = tracker._get_product_id("https://example.com/test")

    assert retrieved_id == product_id


def test_save_price(config_file):
    """Test saving price to database."""
    tracker = PriceTracker(config_path=str(config_file))

    # Add product
    product_id = tracker._add_product("Test Product", "https://example.com/test", "example")

    # Save price
    result = tracker._save_price(product_id, 19.99, "$", "Test Product")

    assert result is True

    # Verify price was saved
    conn = sqlite3.connect(tracker.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT price FROM price_history WHERE product_id = ?", (product_id,))
    result = cursor.fetchone()
    conn.close()

    assert result is not None
    assert result[0] == 19.99


def test_save_price_change(config_file):
    """Test detecting price changes."""
    tracker = PriceTracker(config_path=str(config_file))

    # Add product
    product_id = tracker._add_product("Test Product", "https://example.com/test", "example")

    # Save first price
    tracker._save_price(product_id, 19.99, "$", "Test Product")

    # Save different price
    tracker._save_price(product_id, 24.99, "$", "Test Product")

    # Verify price change was recorded
    conn = sqlite3.connect(tracker.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM price_changes WHERE product_id = ?", (product_id,))
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 1
    assert tracker.stats["price_changes"] == 1


@patch("src.main.requests.get")
def test_fetch_page_success(mock_get, config_file):
    """Test successful page fetch."""
    mock_response = Mock()
    mock_response.content = b"<html><body><div class='price'>$19.99</div></body></html>"
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    tracker = PriceTracker(config_path=str(config_file))
    soup = tracker._fetch_page("https://example.com/product")

    assert soup is not None
    assert soup.find("div", class_="price") is not None


@patch("src.main.requests.get")
def test_extract_price(mock_get, config_file):
    """Test price extraction from HTML."""
    mock_response = Mock()
    mock_response.content = b"<html><body><div class='price'>$19.99</div></body></html>"
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    tracker = PriceTracker(config_path=str(config_file))
    soup = tracker._fetch_page("https://example.com/product")

    price = tracker._extract_price(soup, [".price"])

    assert price == 19.99


def test_get_selectors(config_file):
    """Test getting CSS selectors for product."""
    tracker = PriceTracker(config_path=str(config_file))

    product = {
        "name": "Test",
        "url": "https://example.com",
        "website": "example",
        "price_selector": ".custom-price",
    }

    price_selectors, title_selectors = tracker._get_selectors(product)

    assert ".custom-price" in price_selectors
    assert len(title_selectors) > 0
