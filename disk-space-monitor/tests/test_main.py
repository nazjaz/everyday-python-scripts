"""Unit tests for Disk Space Monitor."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import DiskSpaceMonitor


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary config file."""
    config = {
        "thresholds": {"warning": 20.0, "critical": 10.0},
        "alert_cooldown_minutes": 60,
        "large_files": {"min_size_mb": 100, "max_results": 10},
        "logging": {
            "level": "INFO",
            "file": str(temp_dir / "test.log"),
            "max_bytes": 10485760,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }
    config_path = temp_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return str(config_path)


def test_disk_space_monitor_initialization(config_file):
    """Test DiskSpaceMonitor initialization."""
    monitor = DiskSpaceMonitor(config_path=config_file)
    assert monitor.config is not None
    assert monitor.alert_history == {}


def test_load_config_file_not_found():
    """Test that FileNotFoundError is raised when config file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        DiskSpaceMonitor(config_path="nonexistent.yaml")


def test_format_size():
    """Test size formatting."""
    monitor = DiskSpaceMonitor.__new__(DiskSpaceMonitor)
    monitor.config = {}

    assert "B" in monitor._format_size(500)
    assert "KB" in monitor._format_size(2048)
    assert "MB" in monitor._format_size(2 * 1024 * 1024)
    assert "GB" in monitor._format_size(2 * 1024 * 1024 * 1024)
    assert monitor._format_size(0) == "0 B"


def test_get_disk_usage(config_file, temp_dir):
    """Test getting disk usage."""
    monitor = DiskSpaceMonitor(config_path=config_file)

    usage = monitor._get_disk_usage(str(temp_dir))
    assert usage is not None
    assert len(usage) == 3
    assert all(isinstance(x, int) for x in usage)


def test_calculate_percentage_free(config_file):
    """Test percentage calculation."""
    monitor = DiskSpaceMonitor(config_path=config_file)

    assert monitor._calculate_percentage_free(100, 50) == 50.0
    assert monitor._calculate_percentage_free(100, 20) == 20.0
    assert monitor._calculate_percentage_free(100, 5) == 5.0
    assert monitor._calculate_percentage_free(0, 0) == 0.0


def test_get_alert_level(config_file):
    """Test alert level determination."""
    monitor = DiskSpaceMonitor(config_path=config_file)

    assert monitor._get_alert_level(5.0) == "critical"
    assert monitor._get_alert_level(15.0) == "warning"
    assert monitor._get_alert_level(25.0) is None


def test_should_send_alert(config_file):
    """Test alert cooldown mechanism."""
    monitor = DiskSpaceMonitor(config_path=config_file)

    # First alert should be sent
    assert monitor._should_send_alert("/test", "warning") is True

    # Second alert immediately should not be sent (cooldown)
    assert monitor._should_send_alert("/test", "warning") is False

    # Different drive should be allowed
    assert monitor._should_send_alert("/test2", "warning") is True


@patch("src.main.subprocess.run")
def test_send_desktop_notification_windows(mock_subprocess, config_file):
    """Test sending notification on Windows."""
    monitor = DiskSpaceMonitor(config_path=config_file)

    with patch("platform.system", return_value="Windows"):
        with patch("src.main.ToastNotifier", side_effect=ImportError):
            result = monitor._send_desktop_notification(
                "Test", "Message", "warning"
            )
            assert result is True


@patch("src.main.subprocess.run")
def test_send_desktop_notification_macos(mock_subprocess, config_file):
    """Test sending notification on macOS."""
    monitor = DiskSpaceMonitor(config_path=config_file)

    with patch("platform.system", return_value="Darwin"):
        result = monitor._send_desktop_notification("Test", "Message", "warning")
        assert result is True
        mock_subprocess.assert_called()


@patch("src.main.subprocess.run")
def test_send_desktop_notification_linux(mock_subprocess, config_file):
    """Test sending notification on Linux."""
    monitor = DiskSpaceMonitor(config_path=config_file)

    with patch("platform.system", return_value="Linux"):
        result = monitor._send_desktop_notification("Test", "Message", "warning")
        assert result is True
        mock_subprocess.assert_called()


def test_get_cleanup_suggestions(config_file, temp_dir):
    """Test cleanup suggestion generation."""
    monitor = DiskSpaceMonitor(config_path=config_file)

    suggestions = monitor._get_cleanup_suggestions(str(temp_dir), 15.0)

    assert isinstance(suggestions, list)
    # Should have some suggestions for low disk space
    assert len(suggestions) > 0


def test_check_drive(config_file, temp_dir):
    """Test checking a single drive."""
    monitor = DiskSpaceMonitor(config_path=config_file)

    info = monitor._check_drive(str(temp_dir))

    assert info is not None
    assert "drive" in info
    assert "total" in info
    assert "used" in info
    assert "free" in info
    assert "free_percentage" in info


def test_monitor_disks(config_file):
    """Test monitoring all disks."""
    monitor = DiskSpaceMonitor(config_path=config_file)

    with patch.object(monitor, "_get_all_drives", return_value=["/test"]):
        with patch.object(monitor, "_check_drive", return_value={"drive": "/test"}):
            result = monitor.monitor_disks()

            assert "drives" in result
            assert "stats" in result
            assert result["stats"]["drives_checked"] > 0


def test_environment_variable_overrides(temp_dir):
    """Test that environment variables override config."""
    config = {
        "thresholds": {"warning": 20.0, "critical": 10.0},
        "alert_cooldown_minutes": 60,
        "large_files": {"min_size_mb": 100, "max_results": 10},
        "logging": {
            "level": "INFO",
            "file": str(temp_dir / "test.log"),
            "max_bytes": 10485760,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }
    config_path = temp_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    with patch.dict(os.environ, {"WARNING_THRESHOLD": "25.0"}):
        monitor = DiskSpaceMonitor(config_path=str(config_path))
        assert monitor.config["thresholds"]["warning"] == 25.0
