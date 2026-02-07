"""Unit tests for Crypto Price Tracker."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import CryptoPriceTracker


@pytest.fixture
def sample_config():
    """Create sample configuration dictionary."""
    return {
        "api": {
            "base_url": "https://api.coingecko.com/api/v3",
            "timeout": 10,
        },
        "app": {"title": "Crypto Price Tracker", "window_size": "800x600"},
        "update": {
            "interval_seconds": 60,
            "default_coins": ["bitcoin", "ethereum"],
        },
        "data": {"directory": "data"},
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
def temp_data_directory(tmp_path):
    """Create temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


class TestCryptoPriceTracker:
    """Test cases for CryptoPriceTracker class."""

    @patch("src.main.Tk")
    def test_init_loads_config(self, mock_tk, temp_config_file):
        """Test that initialization loads configuration file."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        app = CryptoPriceTracker(config_path=temp_config_file)
        assert app.config is not None
        assert "api" in app.config

    @patch("src.main.Tk")
    def test_init_uses_default_config(self, mock_tk):
        """Test that initialization uses default config if file not found."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        app = CryptoPriceTracker(config_path="nonexistent.yaml")
        assert app.config is not None
        assert "api" in app.config

    @patch("src.main.Tk")
    @patch("src.main.requests.get")
    def test_fetch_price(self, mock_get, mock_tk, temp_config_file):
        """Test fetching price from API."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        mock_response = Mock()
        mock_response.json.return_value = {"bitcoin": {"usd": 50000.0}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        app = CryptoPriceTracker(config_path=temp_config_file)
        price = app._fetch_price("bitcoin")

        assert price == 50000.0
        mock_get.assert_called_once()

    @patch("src.main.Tk")
    @patch("src.main.requests.get")
    def test_fetch_prices(self, mock_get, mock_tk, temp_config_file):
        """Test fetching prices for multiple coins."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        mock_response = Mock()
        mock_response.json.return_value = {
            "bitcoin": {"usd": 50000.0},
            "ethereum": {"usd": 3000.0},
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        app = CryptoPriceTracker(config_path=temp_config_file)
        prices = app._fetch_prices(["bitcoin", "ethereum"])

        assert "bitcoin" in prices
        assert "ethereum" in prices
        assert prices["bitcoin"] == 50000.0
        assert prices["ethereum"] == 3000.0

    @patch("src.main.Tk")
    def test_load_data(self, mock_tk, temp_config_file, tmp_path):
        """Test loading portfolio and alerts from files."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # Create data files
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        portfolio_file = data_dir / "portfolio.json"
        with open(portfolio_file, "w", encoding="utf-8") as f:
            json.dump({"bitcoin": {"amount": 0.5}}, f)

        alerts_file = data_dir / "alerts.json"
        with open(alerts_file, "w", encoding="utf-8") as f:
            json.dump([{"coin_id": "bitcoin", "target_price": 50000}], f)

        # Update config
        with open(temp_config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        config["data"]["directory"] = str(data_dir)
        with open(temp_config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        app = CryptoPriceTracker(config_path=temp_config_file)
        assert "bitcoin" in app.portfolio
        assert len(app.alerts) == 1

    @patch("src.main.Tk")
    def test_save_data(self, mock_tk, temp_config_file, tmp_path):
        """Test saving portfolio and alerts to files."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        data_dir = tmp_path / "data"
        data_dir.mkdir()

        # Update config
        with open(temp_config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        config["data"]["directory"] = str(data_dir)
        with open(temp_config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        app = CryptoPriceTracker(config_path=temp_config_file)
        app.portfolio = {"bitcoin": {"amount": 0.5}}
        app.alerts = [{"coin_id": "bitcoin", "target_price": 50000}]

        app._save_data()

        portfolio_file = data_dir / "portfolio.json"
        assert portfolio_file.exists()
        with open(portfolio_file, "r", encoding="utf-8") as f:
            portfolio = json.load(f)
        assert "bitcoin" in portfolio

        alerts_file = data_dir / "alerts.json"
        assert alerts_file.exists()
