"""Unit tests for weather scraper module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import yaml

from src.main import WeatherScraper


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    return tempfile.mkdtemp()


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary configuration file."""
    config = {
        "location": {
            "default_city": "New York",
            "default_country": "US",
            "use_location_detection": False,
        },
        "weather_source": {
            "provider": "wttr",
            "base_url": "https://wttr.in",
            "format": "j1",
            "timeout": 10,
            "user_agent": "Weather-Scraper/1.0",
        },
        "updates": {
            "auto_refresh": False,
            "refresh_interval": 300,
            "refresh_on_start": False,
        },
        "display": {
            "show_current": True,
            "show_forecast": True,
            "forecast_days": 3,
            "temperature_unit": "C",
            "show_humidity": True,
            "show_wind": True,
            "show_pressure": True,
            "show_visibility": True,
        },
        "gui": {
            "window_title": "Test Weather",
            "window_width": 600,
            "window_height": 700,
            "theme": {
                "background_color": "#F0F0F0",
                "text_color": "#333333",
            },
        },
        "logging": {
            "level": "DEBUG",
            "file": f"{temp_dir}/test.log",
            "max_bytes": 1048576,
            "backup_count": 3,
        },
    }

    config_path = Path(temp_dir) / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config_path


def test_weather_scraper_initialization(config_file):
    """Test WeatherScraper initializes correctly."""
    scraper = WeatherScraper(config_path=str(config_file))
    assert scraper.current_city == "New York"
    assert scraper.current_weather is None
    assert len(scraper.forecast) == 0


def test_weather_scraper_missing_config():
    """Test WeatherScraper raises error for missing config."""
    with pytest.raises(FileNotFoundError):
        WeatherScraper(config_path="nonexistent.yaml")


@patch("src.main.requests.get")
def test_fetch_weather_data_success(mock_get, config_file):
    """Test successful weather data fetch."""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        "current_condition": [{"temp_C": "20", "weatherDesc": [{"value": "Sunny"}]}],
        "nearest_area": [{"areaName": [{"value": "New York"}]}],
        "weather": [],
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    scraper = WeatherScraper(config_path=str(config_file))
    data = scraper._fetch_weather_data("New York")

    assert data is not None
    assert "current_condition" in data
    mock_get.assert_called_once()


@patch("src.main.requests.get")
def test_fetch_weather_data_failure(mock_get, config_file):
    """Test weather data fetch failure."""
    mock_get.side_effect = Exception("Network error")

    scraper = WeatherScraper(config_path=str(config_file))
    data = scraper._fetch_weather_data("New York")

    assert data is None


def test_parse_weather_data(config_file):
    """Test parsing weather data."""
    scraper = WeatherScraper(config_path=str(config_file))

    test_data = {
        "current_condition": [
            {
                "temp_C": "20",
                "FeelsLikeC": "22",
                "weatherDesc": [{"value": "Sunny"}],
                "humidity": "65",
                "windspeedKmph": "15",
                "winddir16Point": "N",
                "pressure": "1013",
                "visibility": "10",
                "uvIndex": "5",
                "localObsDateTime": "2024-02-07 12:00",
            }
        ],
        "nearest_area": [
            {
                "areaName": [{"value": "New York"}],
                "country": [{"value": "United States"}],
            }
        ],
        "weather": [
            {
                "date": "2024-02-08",
                "avgtempC": "18",
                "maxtempC": "22",
                "mintempC": "15",
                "hourly": [{"weatherDesc": [{"value": "Cloudy"}]}],
            }
        ],
    }

    current, forecast = scraper._parse_weather_data(test_data)

    assert current is not None
    assert current["location"] == "New York"
    assert current["temperature"] == "20"
    assert len(forecast) == 1
    assert forecast[0]["date"] == "2024-02-08"


def test_parse_weather_data_empty(config_file):
    """Test parsing empty weather data."""
    scraper = WeatherScraper(config_path=str(config_file))

    current, forecast = scraper._parse_weather_data({})

    assert current is None
    assert len(forecast) == 0


@patch("src.main.WeatherScraper._fetch_weather_data")
@patch("src.main.WeatherScraper._parse_weather_data")
def test_fetch_weather_success(mock_parse, mock_fetch, config_file):
    """Test successful weather fetch."""
    mock_fetch.return_value = {"test": "data"}
    mock_parse.return_value = ({"location": "New York"}, [{"date": "2024-02-08"}])

    scraper = WeatherScraper(config_path=str(config_file))
    result = scraper.fetch_weather("New York")

    assert result is True
    assert scraper.current_weather is not None
    assert len(scraper.forecast) == 1


@patch("src.main.WeatherScraper._fetch_weather_data")
def test_fetch_weather_failure(mock_fetch, config_file):
    """Test weather fetch failure."""
    mock_fetch.return_value = None

    scraper = WeatherScraper(config_path=str(config_file))
    result = scraper.fetch_weather("New York")

    assert result is False
    assert scraper.current_weather is None
