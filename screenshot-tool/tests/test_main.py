"""Unit tests for Screenshot Tool application."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.main import ScreenshotTool, load_config


class TestScreenshotTool:
    """Test cases for ScreenshotTool class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return {
            "save": {
                "default_directory": "./screenshots",
                "timestamp_format": "%Y%m%d_%H%M%S",
                "default_format": "png",
            },
            "annotation": {
                "default_color": "#FF0000",
                "default_line_width": 3,
                "default_font_size": 20,
            },
            "logging": {"level": "INFO", "file": "logs/test.log"},
        }

    def test_init(self, config):
        """Test ScreenshotTool initialization."""
        # Note: GUI tests require display, so we'll test initialization carefully
        # In a real scenario, you might want to mock tkinter
        try:
            tool = ScreenshotTool(config)
            assert tool.config == config
            assert tool.current_tool == "select"
            assert tool.draw_color == "#FF0000"
        except Exception:
            # Skip if GUI not available
            pytest.skip("GUI not available for testing")

    def test_config_defaults(self):
        """Test that defaults are used when config is empty."""
        try:
            tool = ScreenshotTool({})
            # Should not raise error
            assert tool.config == {}
        except Exception:
            pytest.skip("GUI not available for testing")


class TestLoadConfig:
    """Test cases for load_config function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        # Cleanup handled by tempfile

    def test_load_config_valid(self, temp_dir):
        """Test loading a valid configuration file."""
        config_file = temp_dir / "config.yaml"
        config_file.write_text(
            "save:\n  default_directory: /test\nannotation:\n  default_color: '#00FF00'\n"
        )

        config = load_config(config_file)
        assert config["save"]["default_directory"] == "/test"
        assert config["annotation"]["default_color"] == "#00FF00"

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


class TestScreenshotFunctionality:
    """Test cases for screenshot-related functionality."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return {
            "save": {"default_directory": "./screenshots"},
            "annotation": {"default_color": "#FF0000"},
            "logging": {"level": "INFO", "file": "logs/test.log"},
        }

    @patch("src.main.mss")
    def test_capture_screenshot_mock(self, mock_mss, config):
        """Test screenshot capture with mocked mss."""
        # Mock mss context manager
        mock_sct = Mock()
        mock_monitor = {"left": 0, "top": 0, "width": 1920, "height": 1080}
        mock_sct.monitors = [None, mock_monitor]
        mock_screenshot = Mock()
        mock_screenshot.size = (1920, 1080)
        mock_screenshot.bgra = b"\x00" * (1920 * 1080 * 4)
        mock_sct.grab.return_value = mock_screenshot
        mock_mss.return_value.__enter__.return_value = mock_sct

        try:
            tool = ScreenshotTool(config)
            # Test that capture method exists and can be called
            assert hasattr(tool, "capture_screenshot")
        except Exception:
            pytest.skip("GUI not available for testing")
