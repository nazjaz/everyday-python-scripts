"""Unit tests for Time Tracker application."""

import json
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import TimeTrackerApp


@pytest.fixture
def sample_config():
    """Create sample configuration dictionary."""
    return {
        "app": {"title": "Time Tracker", "window_size": "700x600"},
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


class TestTimeTrackerApp:
    """Test cases for TimeTrackerApp class."""

    @patch("src.main.Tk")
    def test_init_loads_config(self, mock_tk, temp_config_file):
        """Test that initialization loads configuration file."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        app = TimeTrackerApp(config_path=temp_config_file)
        assert app.config is not None
        assert "app" in app.config

    @patch("src.main.Tk")
    def test_init_uses_default_config(self, mock_tk):
        """Test that initialization uses default config if file not found."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        app = TimeTrackerApp(config_path="nonexistent.yaml")
        assert app.config is not None
        assert "app" in app.config

    @patch("src.main.Tk")
    def test_format_time(self, mock_tk, temp_config_file):
        """Test time formatting."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        app = TimeTrackerApp(config_path=temp_config_file)

        assert app._format_time(0) == "00:00:00"
        assert app._format_time(3661) == "01:01:01"  # 1 hour, 1 minute, 1 second
        assert app._format_time(125) == "00:02:05"  # 2 minutes, 5 seconds

    @patch("src.main.Tk")
    def test_load_data(self, mock_tk, temp_config_file, tmp_path):
        """Test loading time entries from file."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # Create data file
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        entries_file = data_dir / "time_entries.json"
        test_entries = [
            {
                "task": "Test Task",
                "duration_seconds": 3600,
                "date": "2024-01-01",
                "time": "10:00:00",
                "timestamp": "2024-01-01T10:00:00",
            }
        ]
        with open(entries_file, "w", encoding="utf-8") as f:
            json.dump(test_entries, f)

        # Update config
        with open(temp_config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        config["data"]["directory"] = str(data_dir)
        with open(temp_config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        app = TimeTrackerApp(config_path=temp_config_file)
        assert len(app.time_entries) == 1
        assert app.time_entries[0]["task"] == "Test Task"

    @patch("src.main.Tk")
    def test_save_data(self, mock_tk, temp_config_file, tmp_path):
        """Test saving time entries to file."""
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

        app = TimeTrackerApp(config_path=temp_config_file)
        app.time_entries = [
            {
                "task": "Test",
                "duration_seconds": 1800,
                "date": "2024-01-01",
                "time": "10:00:00",
                "timestamp": "2024-01-01T10:00:00",
            }
        ]

        app._save_data()

        entries_file = data_dir / "time_entries.json"
        assert entries_file.exists()
        with open(entries_file, "r", encoding="utf-8") as f:
            entries = json.load(f)
        assert len(entries) == 1

    @patch("src.main.Tk")
    def test_start_timer(self, mock_tk, temp_config_file):
        """Test starting timer."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        app = TimeTrackerApp(config_path=temp_config_file)
        app.task_entry = Mock()
        app.task_entry.get.return_value = "Test Task"

        app._start_timer()

        assert app.timer_running is True
        assert app.current_task == "Test Task"
        assert app.start_time is not None

    @patch("src.main.Tk")
    def test_stop_timer(self, mock_tk, temp_config_file):
        """Test stopping timer."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        app = TimeTrackerApp(config_path=temp_config_file)
        app.timer_running = True
        app.start_time = time.time() - 10  # 10 seconds ago

        app._stop_timer()

        assert app.timer_running is False
        assert app.current_task is None

    @patch("src.main.Tk")
    def test_log_entry(self, mock_tk, temp_config_file):
        """Test logging time entry."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        app = TimeTrackerApp(config_path=temp_config_file)
        app.timer_running = True
        app.current_task = "Test Task"
        app.start_time = time.time() - 5  # 5 seconds ago

        app._log_entry()

        assert len(app.time_entries) == 1
        assert app.time_entries[0]["task"] == "Test Task"
        assert app.time_entries[0]["duration_seconds"] >= 5

    @patch("src.main.Tk")
    def test_create_daily_report(self, mock_tk, temp_config_file):
        """Test creating daily report."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        app = TimeTrackerApp(config_path=temp_config_file)
        app.time_entries = [
            {
                "task": "Task 1",
                "duration_seconds": 3600,
                "date": "2024-02-07",
                "time": "10:00:00",
                "timestamp": "2024-02-07T10:00:00",
            }
        ]

        report = app._create_daily_report("2024-02-07")
        assert "Daily Time Report" in report
        assert "Task 1" in report

    @patch("src.main.Tk")
    def test_create_weekly_report(self, mock_tk, temp_config_file):
        """Test creating weekly report."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        app = TimeTrackerApp(config_path=temp_config_file)
        today = datetime.now()
        date_str = today.strftime("%Y-%m-%d")
        app.time_entries = [
            {
                "task": "Task 1",
                "duration_seconds": 3600,
                "date": date_str,
                "time": "10:00:00",
                "timestamp": f"{date_str}T10:00:00",
            }
        ]

        report = app._create_weekly_report()
        assert "Weekly Time Report" in report
