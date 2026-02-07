"""Unit tests for process monitor module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import yaml

from src.main import ProcessMonitor


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    return tempfile.mkdtemp()


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary configuration file."""
    config = {
        "monitoring": {
            "interval": 5,
            "enabled": True,
        },
        "cpu": {
            "enabled": True,
            "warning_threshold": 80.0,
            "kill_threshold": 95.0,
            "check_duration": 10,
        },
        "memory": {
            "enabled": True,
            "warning_threshold": 80.0,
            "kill_threshold": 90.0,
            "absolute_limit_mb": 0,
            "check_duration": 10,
        },
        "whitelist": {
            "enabled": True,
            "process_names": ["test_process"],
            "process_ids": [],
        },
        "actions": {
            "kill_on_cpu_exceed": True,
            "kill_on_memory_exceed": True,
            "send_warning_first": True,
            "warning_duration": 30,
        },
        "notifications": {
            "enabled": True,
            "notify_on_warning": True,
            "notify_on_kill": True,
            "notification_duration": 10,
        },
        "logging": {
            "level": "DEBUG",
            "file": f"{temp_dir}/test.log",
            "max_bytes": 1048576,
            "backup_count": 3,
        },
        "reporting": {
            "generate_reports": True,
            "report_interval": 3600,
            "report_file": f"{temp_dir}/report.txt",
        },
    }

    config_path = Path(temp_dir) / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config_path


def test_process_monitor_initialization(config_file):
    """Test ProcessMonitor initializes correctly."""
    monitor = ProcessMonitor(config_path=str(config_file))
    assert monitor.running is False
    assert monitor.stats["checks_performed"] == 0
    assert monitor.stats["processes_killed"] == 0


def test_process_monitor_missing_config():
    """Test ProcessMonitor raises error for missing config."""
    with pytest.raises(FileNotFoundError):
        ProcessMonitor(config_path="nonexistent.yaml")


@patch("src.main.psutil.Process")
def test_is_whitelisted(mock_process_class, config_file):
    """Test whitelist checking."""
    monitor = ProcessMonitor(config_path=str(config_file))

    # Mock whitelisted process
    mock_process = Mock()
    mock_process.name.return_value = "test_process"
    mock_process.pid = 1234

    result = monitor._is_whitelisted(mock_process)
    assert result is True


@patch("src.main.psutil.Process")
def test_is_not_whitelisted(mock_process_class, config_file):
    """Test non-whitelisted process."""
    monitor = ProcessMonitor(config_path=str(config_file))

    # Mock non-whitelisted process
    mock_process = Mock()
    mock_process.name.return_value = "other_process"
    mock_process.pid = 5678

    result = monitor._is_whitelisted(mock_process)
    assert result is False


@patch("src.main.psutil.Process")
@patch("src.main.psutil.virtual_memory")
def test_get_process_usage(mock_virtual_memory, mock_process_class, config_file):
    """Test getting process usage."""
    monitor = ProcessMonitor(config_path=str(config_file))

    # Mock process
    mock_process = Mock()
    mock_process.cpu_percent.return_value = 50.0
    mock_process.memory_info.return_value = Mock(rss=1024 * 1024 * 100)  # 100 MB

    # Mock system memory
    mock_virtual_memory.return_value = Mock(total=1024 * 1024 * 1024 * 4)  # 4 GB

    cpu, memory = monitor._get_process_usage(mock_process)

    assert cpu == 50.0
    assert memory > 0


@patch("src.main.psutil.Process")
def test_check_cpu_limit_under_threshold(mock_process_class, config_file):
    """Test CPU check when under threshold."""
    monitor = ProcessMonitor(config_path=str(config_file))

    mock_process = Mock()
    mock_process.pid = 1234
    mock_process.name.return_value = "test_process"
    mock_process.cmdline.return_value = ["test_process"]

    # Mock whitelist check to return False
    monitor._is_whitelisted = Mock(return_value=False)
    monitor._get_process_usage = Mock(return_value=(50.0, 30.0))  # Under threshold

    # Should not kill
    monitor._check_cpu_limit(mock_process, 50.0, 1234)

    assert 1234 not in monitor.process_tracking


@patch("src.main.psutil.Process")
def test_check_memory_limit_under_threshold(mock_process_class, config_file):
    """Test memory check when under threshold."""
    monitor = ProcessMonitor(config_path=str(config_file))

    mock_process = Mock()
    mock_process.pid = 1234
    mock_process.name.return_value = "test_process"

    # Mock whitelist check to return False
    monitor._is_whitelisted = Mock(return_value=False)

    # Should not kill
    monitor._check_memory_limit(mock_process, 50.0, 1234)

    assert 1234 not in monitor.process_tracking or monitor.process_tracking[1234].get("memory_exceed_start") is None


def test_start_stop_monitor(config_file):
    """Test starting and stopping monitor."""
    monitor = ProcessMonitor(config_path=str(config_file))

    monitor.start()
    assert monitor.running is True

    # Wait a bit
    import time
    time.sleep(0.1)

    monitor.stop()
    assert monitor.running is False


def test_generate_report(config_file):
    """Test report generation."""
    monitor = ProcessMonitor(config_path=str(config_file))
    monitor.stats["checks_performed"] = 10
    monitor.stats["processes_checked"] = 100
    monitor.stats["processes_killed"] = 2

    monitor._generate_report()

    # Check report file exists
    report_path = Path(monitor.config["reporting"]["report_file"])
    if not report_path.is_absolute():
        project_root = Path(__file__).parent.parent.parent
        report_path = project_root / report_path

    assert report_path.exists()

    # Check report content
    with open(report_path, "r") as f:
        content = f.read()
        assert "Process Monitor Report" in content
        assert "Checks Performed: 10" in content
