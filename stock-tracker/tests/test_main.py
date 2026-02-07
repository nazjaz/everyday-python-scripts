"""Unit tests for Stock Tracker."""

import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.main import StockDataManager, StockPriceScraper


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def data_file(temp_dir):
    """Create a temporary data file."""
    return temp_dir / "test_stocks.json"


def test_stock_data_manager_initialization(data_file):
    """Test StockDataManager initialization."""
    manager = StockDataManager(data_file)
    assert manager.data_file == data_file
    assert isinstance(manager.stock_data, dict)


def test_update_stock_info_new_stock(data_file):
    """Test updating stock info for new stock."""
    manager = StockDataManager(data_file)

    manager.update_stock_info("AAPL", 150.50)

    assert "AAPL" in manager.stock_data
    assert manager.stock_data["AAPL"]["first_price"] == 150.50
    assert manager.stock_data["AAPL"]["last_price"] == 150.50


def test_update_stock_info_existing_stock(data_file):
    """Test updating stock info for existing stock."""
    manager = StockDataManager(data_file)
    manager.update_stock_info("AAPL", 150.50)
    manager.update_stock_info("AAPL", 155.75)

    assert manager.stock_data["AAPL"]["first_price"] == 150.50
    assert manager.stock_data["AAPL"]["last_price"] == 155.75


def test_get_stock_info(data_file):
    """Test getting stock info."""
    manager = StockDataManager(data_file)
    manager.update_stock_info("AAPL", 150.50)

    info = manager.get_stock_info("AAPL")
    assert info is not None
    assert info["first_price"] == 150.50
    assert info["last_price"] == 150.50


def test_get_stock_info_nonexistent(data_file):
    """Test getting stock info for non-existent stock."""
    manager = StockDataManager(data_file)

    info = manager.get_stock_info("NONEXISTENT")
    assert info is None


def test_save_and_load_data(data_file):
    """Test saving and loading data."""
    manager = StockDataManager(data_file)
    manager.update_stock_info("AAPL", 150.50)
    manager.update_stock_info("MSFT", 300.25)

    manager.save_data()

    manager2 = StockDataManager(data_file)

    assert "AAPL" in manager2.stock_data
    assert "MSFT" in manager2.stock_data
    assert manager2.stock_data["AAPL"]["first_price"] == 150.50
    assert manager2.stock_data["MSFT"]["first_price"] == 300.25


def test_load_nonexistent_data_file(temp_dir):
    """Test loading from non-existent file."""
    data_file = temp_dir / "nonexistent.json"

    manager = StockDataManager(data_file)
    assert isinstance(manager.stock_data, dict)
    assert len(manager.stock_data) == 0


@patch("src.main.yf.Ticker")
def test_get_stock_price_success(mock_ticker, temp_dir):
    """Test getting stock price successfully."""
    # Mock ticker info
    mock_info = {
        "currentPrice": 150.50,
        "previousClose": 148.25,
        "open": 149.00,
        "dayHigh": 151.00,
        "dayLow": 149.50,
    }
    mock_ticker_instance = Mock()
    mock_ticker_instance.info = mock_info
    mock_ticker.return_value = mock_ticker_instance

    scraper = StockPriceScraper()
    result = scraper.get_stock_price("AAPL")

    assert result is not None
    assert result["current_price"] == 150.50
    assert result["previous_close"] == 148.25
    assert result["open"] == 149.00
    assert result["high"] == 151.00
    assert result["low"] == 149.50


@patch("src.main.yf.Ticker")
def test_get_stock_price_fallback_to_history(mock_ticker, temp_dir):
    """Test getting stock price using history fallback."""
    try:
        import pandas as pd
        from datetime import datetime

        # Mock ticker with no currentPrice but with history
        mock_info = {}
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = mock_info

        # Mock history
        mock_history = pd.DataFrame({
            "Close": [150.50, 148.25]
        }, index=[datetime.now(), datetime.now()])
        mock_ticker_instance.history.return_value = mock_history

        mock_ticker.return_value = mock_ticker_instance

        scraper = StockPriceScraper()
        result = scraper.get_stock_price("AAPL")

        assert result is not None
        assert result["current_price"] == 150.50
    except ImportError:
        # Skip test if pandas not available (yfinance dependency)
        pytest.skip("pandas not available for testing")


@patch("src.main.yf.Ticker")
def test_get_stock_name_success(mock_ticker):
    """Test getting stock name successfully."""
    mock_info = {"longName": "Apple Inc."}
    mock_ticker_instance = Mock()
    mock_ticker_instance.info = mock_info
    mock_ticker.return_value = mock_ticker_instance

    scraper = StockPriceScraper()
    name = scraper.get_stock_name("AAPL")

    assert name == "Apple Inc."


@patch("src.main.yf.Ticker")
def test_get_stock_name_fallback(mock_ticker):
    """Test getting stock name with fallback to symbol."""
    mock_info = {}
    mock_ticker_instance = Mock()
    mock_ticker_instance.info = mock_info
    mock_ticker.return_value = mock_ticker_instance

    scraper = StockPriceScraper()
    name = scraper.get_stock_name("AAPL")

    assert name == "AAPL"


def test_stock_data_case_insensitive(data_file):
    """Test that stock symbols are stored in uppercase."""
    manager = StockDataManager(data_file)
    manager.update_stock_info("aapl", 150.50)

    assert "AAPL" in manager.stock_data
    assert "aapl" not in manager.stock_data

    info = manager.get_stock_info("aapl")
    assert info is not None
    assert info["first_price"] == 150.50
