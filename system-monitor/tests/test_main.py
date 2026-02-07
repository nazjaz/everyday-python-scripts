"""Unit tests for system monitor module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.main import SystemMonitor


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    return tempfile.mkdtemp()


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary configuration file."""
    config = {
        "monitoring": {
            "interval": 1,
            "csv_log_interval": 2,
        },
        "csv_logging": {
            "enabled": True,
            "file": f"{temp_dir}/test_metrics.csv",
            "include_timestamp": True,
            "include_cpu": True,
            "include_memory": True,
            "include_disk": True,
            "include_network": False,
        },
        "cpu": {
            "enabled": True,
            "warning_threshold": 70.0,
            "critical_threshold": 90.0,
            "notify_on_warning": True,
            "notify_on_critical": True,
        },
        "memory": {
            "enabled": True,
            "warning_threshold": 75.0,
            "critical_threshold": 90.0,
            "notify_on_warning": True,
            "notify_on_critical": True,
        },
        "disk": {
            "enabled": True,
            "warning_threshold": 80.0,
            "critical_threshold": 95.0,
            "notify_on_warning": True,
            "notify_on_critical": True,
            "monitor_paths": ["/"],
        },
        "notifications": {
            "enabled": True,
            "warning_duration": 5,
            "critical_duration": 10,
            "cooldown_period": 60,
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


def test_system_monitor_initialization(config_file):
    """Test SystemMonitor initializes correctly."""
    monitor = SystemMonitor(config_path=str(config_file))
    assert monitor.running is False
    assert monitor.stats["checks_performed"] == 0


def test_system_monitor_missing_config():
    """Test SystemMonitor raises error for missing config."""
    with pytest.raises(FileNotFoundError):
        SystemMonitor(config_path="nonexistent.yaml")


@patch("src.main.psutil.cpu_percent")
def test_get_cpu_usage(mock_cpu, config_file):
    """Test CPU usage retrieval."""
    mock_cpu.return_value = 45.5
    monitor = SystemMonitor(config_path=str(config_file))
    cpu_usage = monitor._get_cpu_usage()
    assert cpu_usage == 45.5


@patch("src.main.psutil.virtual_memory")
def test_get_memory_usage(mock_memory, config_file):
    """Test memory usage retrieval."""
    mock_mem = MagicMock()
    mock_mem.percent = 65.0
    mock_mem.used = 8 * (1024 ** 3)  # 8 GB
    mock_mem.total = 16 * (1024 ** 3)  # 16 GB
    mock_memory.return_value = mock_mem

    monitor = SystemMonitor(config_path=str(config_file))
    percent, used_gb, total_gb = monitor._get_memory_usage()

    assert percent == 65.0
    assert abs(used_gb - 8.0) < 0.1
    assert abs(total_gb - 16.0) < 0.1


@patch("src.main.psutil.disk_usage")
def test_get_disk_usage(mock_disk, config_file):
    """Test disk usage retrieval."""
    mock_disk_obj = MagicMock()
    mock_disk_obj.percent = 55.0
    mock_disk_obj.used = 100 * (1024 ** 3)  # 100 GB
    mock_disk_obj.total = 500 * (1024 ** 3)  # 500 GB
    mock_disk.return_value = mock_disk_obj

    monitor = SystemMonitor(config_path=str(config_file))
    percent, used_gb, total_gb = monitor._get_disk_usage()

    assert percent == 55.0
    assert abs(used_gb - 100.0) < 0.1
    assert abs(total_gb - 500.0) < 0.1


def test_check_thresholds(config_file):
    """Test threshold checking logic."""
    monitor = SystemMonitor(config_path=str(config_file))

    # Below warning threshold
    assert monitor._check_thresholds(50.0, 70.0, 90.0) is None

    # At warning threshold
    assert monitor._check_thresholds(75.0, 70.0, 90.0) == "warning"

    # At critical threshold
    assert monitor._check_thresholds(95.0, 70.0, 90.0) == "critical"


@patch("src.main.notification.notify")
def test_send_notification(mock_notify, config_file):
    """Test notification sending."""
    monitor = SystemMonitor(config_path=str(config_file))
    monitor._send_notification("Test Title", "Test Message", "warning")

    mock_notify.assert_called_once()
    call_args = mock_notify.call_args
    assert call_args[1]["title"] == "Test Title"
    assert call_args[1]["message"] == "Test Message"


@patch("src.main.psutil.cpu_percent")
@patch("src.main.SystemMonitor._should_send_notification")
@patch("src.main.SystemMonitor._send_notification")
def test_check_cpu_warning(
    mock_send, mock_should_send, mock_cpu, config_file
):
    """Test CPU warning notification."""
    mock_cpu.return_value = 75.0
    mock_should_send.return_value = True

    monitor = SystemMonitor(config_path=str(config_file))
    monitor._check_cpu()

    mock_send.assert_called_once()
    call_args = mock_send.call_args
    assert "CPU Warning" in call_args[0][0]


@patch("src.main.psutil.cpu_percent")
@patch("src.main.SystemMonitor._should_send_notification")
@patch("src.main.SystemMonitor._send_notification")
def test_check_cpu_critical(
    mock_send, mock_should_send, mock_cpu, config_file
):
    """Test CPU critical notification."""
    mock_cpu.return_value = 95.0
    mock_should_send.return_value = True

    monitor = SystemMonitor(config_path=str(config_file))
    monitor._check_cpu()

    mock_send.assert_called_once()
    call_args = mock_send.call_args
    assert "CPU Critical Alert" in call_args[0][0]


def test_should_send_notification_cooldown(config_file):
    """Test notification cooldown mechanism."""
    import time

    monitor = SystemMonitor(config_path=str(config_file))
    monitor.config["notifications"]["cooldown_period"] = 60

    # First notification should be sent
    assert monitor._should_send_notification("cpu", "warning") is True

    # Second notification within cooldown should be blocked
    assert monitor._should_send_notification("cpu", "warning") is False

    # Different alert type should be allowed
    assert monitor._should_send_notification("memory", "warning") is True


@patch("src.main.psutil.cpu_percent")
@patch("src.main.psutil.virtual_memory")
@patch("src.main.psutil.disk_usage")
def test_log_to_csv(mock_disk, mock_memory, mock_cpu, config_file, temp_dir):
    """Test CSV logging functionality."""
    mock_cpu.return_value = 50.0

    mock_mem = MagicMock()
    mock_mem.percent = 60.0
    mock_mem.used = 8 * (1024 ** 3)
    mock_mem.total = 16 * (1024 ** 3)
    mock_memory.return_value = mock_mem

    mock_disk_obj = MagicMock()
    mock_disk_obj.percent = 70.0
    mock_disk_obj.used = 100 * (1024 ** 3)
    mock_disk_obj.total = 500 * (1024 ** 3)
    mock_disk.return_value = mock_disk_obj

    monitor = SystemMonitor(config_path=str(config_file))
    monitor._log_to_csv()

    # Verify CSV file was created and contains data
    csv_path = Path(temp_dir) / "test_metrics.csv"
    assert csv_path.exists()

    with open(csv_path, "r") as f:
        lines = f.readlines()
        assert len(lines) >= 2  # Header + at least one data row
