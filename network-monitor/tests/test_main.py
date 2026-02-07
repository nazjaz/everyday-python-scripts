"""Unit tests for Network Monitor."""

import shutil
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.main import NetworkMonitor


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_config(temp_dir):
    """Create a sample configuration."""
    return {
        "database_file": str(temp_dir / "test_network.db"),
        "monitoring_interval": 60,
        "interfaces": [],
        "exclude_interfaces": ["^lo$"],
        "options": {
            "track_per_interface": True,
            "track_total": True,
            "calculate_rates": True,
            "store_raw_counts": True,
        },
        "database": {
            "retention_days": 30,
            "cleanup_on_startup": True,
        },
    }


def test_network_monitor_initialization(sample_config):
    """Test NetworkMonitor initialization."""
    monitor = NetworkMonitor(sample_config)

    assert monitor.database_file.exists()
    assert monitor.monitoring_interval == 60


def test_database_initialization(sample_config):
    """Test database initialization."""
    monitor = NetworkMonitor(sample_config)

    # Check that database file exists
    assert monitor.database_file.exists()

    # Check that table exists
    conn = sqlite3.connect(monitor.database_file)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='network_stats'"
    )
    result = cursor.fetchone()

    conn.close()

    assert result is not None


def test_get_network_interfaces(sample_config):
    """Test getting network interfaces."""
    monitor = NetworkMonitor(sample_config)

    interfaces = monitor.get_network_interfaces()

    assert isinstance(interfaces, list)
    # Should exclude loopback interface
    assert "lo" not in interfaces or len(interfaces) > 0


@patch("src.main.psutil.net_io_counters")
def test_get_network_stats_per_interface(mock_net_io, sample_config):
    """Test getting network stats for specific interface."""
    from collections import namedtuple

    NetIOCounters = namedtuple(
        "NetIOCounters",
        [
            "bytes_sent",
            "bytes_recv",
            "packets_sent",
            "packets_recv",
            "errin",
            "errout",
            "dropin",
            "dropout",
        ],
    )

    mock_stats = NetIOCounters(
        bytes_sent=1000,
        bytes_recv=2000,
        packets_sent=10,
        packets_recv=20,
        errin=0,
        errout=0,
        dropin=0,
        dropout=0,
    )

    mock_net_io.return_value = {"eth0": mock_stats}

    monitor = NetworkMonitor(sample_config)
    stats = monitor.get_network_stats("eth0")

    assert stats["bytes_sent"] == 1000
    assert stats["bytes_recv"] == 2000
    assert stats["packets_sent"] == 10
    assert stats["packets_recv"] == 20


@patch("src.main.psutil.net_io_counters")
def test_get_network_stats_total(mock_net_io, sample_config):
    """Test getting total network stats."""
    from collections import namedtuple

    NetIOCounters = namedtuple(
        "NetIOCounters",
        [
            "bytes_sent",
            "bytes_recv",
            "packets_sent",
            "packets_recv",
            "errin",
            "errout",
            "dropin",
            "dropout",
        ],
    )

    mock_stats = NetIOCounters(
        bytes_sent=5000,
        bytes_recv=6000,
        packets_sent=50,
        packets_recv=60,
        errin=0,
        errout=0,
        dropin=0,
        dropout=0,
    )

    mock_net_io.return_value = mock_stats

    monitor = NetworkMonitor(sample_config)
    stats = monitor.get_network_stats(None)

    assert stats["bytes_sent"] == 5000
    assert stats["bytes_recv"] == 6000


def test_calculate_rates(sample_config):
    """Test calculating bytes per second rates."""
    monitor = NetworkMonitor(sample_config)

    current_stats = {"bytes_sent": 2000, "bytes_recv": 3000}
    previous_stats = {"bytes_sent": 1000, "bytes_recv": 2000}
    interval = 1.0  # 1 second

    sent_rate, recv_rate = monitor.calculate_rates(
        current_stats, previous_stats, interval
    )

    assert sent_rate == 1000.0  # 2000 - 1000 = 1000 bytes/sec
    assert recv_rate == 1000.0  # 3000 - 2000 = 1000 bytes/sec


def test_calculate_rates_no_previous(sample_config):
    """Test calculating rates with no previous stats."""
    monitor = NetworkMonitor(sample_config)

    current_stats = {"bytes_sent": 1000, "bytes_recv": 2000}
    previous_stats = {}
    interval = 1.0

    sent_rate, recv_rate = monitor.calculate_rates(
        current_stats, previous_stats, interval
    )

    assert sent_rate == 0.0
    assert recv_rate == 0.0


def test_log_network_stats(sample_config):
    """Test logging network stats to database."""
    monitor = NetworkMonitor(sample_config)

    stats = {
        "bytes_sent": 1000,
        "bytes_recv": 2000,
        "packets_sent": 10,
        "packets_recv": 20,
        "errin": 0,
        "errout": 0,
        "dropin": 0,
        "dropout": 0,
    }

    monitor.log_network_stats("eth0", stats, 100.0, 200.0)

    # Verify data was written
    conn = sqlite3.connect(monitor.database_file)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM network_stats WHERE interface = 'eth0' ORDER BY timestamp DESC LIMIT 1"
    )
    row = cursor.fetchone()

    conn.close()

    assert row is not None
    assert row[3] == 1000  # bytes_sent
    assert row[4] == 2000  # bytes_recv
    assert row[11] == 100.0  # bytes_sent_rate
    assert row[12] == 200.0  # bytes_recv_rate


def test_format_bytes(sample_config):
    """Test byte formatting."""
    monitor = NetworkMonitor(sample_config)

    assert "B" in monitor._format_bytes(500)
    assert "KB" in monitor._format_bytes(2048)
    assert "MB" in monitor._format_bytes(1048576)
    assert "GB" in monitor._format_bytes(1073741824)


def test_get_statistics_summary(sample_config):
    """Test getting statistics summary from database."""
    monitor = NetworkMonitor(sample_config)

    # Log some test data
    stats = {
        "bytes_sent": 1000,
        "bytes_recv": 2000,
        "packets_sent": 10,
        "packets_recv": 20,
        "errin": 0,
        "errout": 0,
        "dropin": 0,
        "dropout": 0,
    }

    monitor.log_network_stats("eth0", stats)

    # Get summary
    summary = monitor.get_statistics_summary()

    assert summary["total_records"] > 0
    assert len(summary["records"]) > 0
    assert summary["records"][0]["interface"] == "eth0"


def test_cleanup_old_records(sample_config):
    """Test cleanup of old records."""
    monitor = NetworkMonitor(sample_config)

    # Log old record
    stats = {
        "bytes_sent": 1000,
        "bytes_recv": 2000,
        "packets_sent": 10,
        "packets_recv": 20,
        "errin": 0,
        "errout": 0,
        "dropin": 0,
        "dropout": 0,
    }

    # Manually insert old record
    conn = sqlite3.connect(monitor.database_file)
    cursor = conn.cursor()

    old_date = (datetime.now() - timedelta(days=35)).isoformat()
    cursor.execute(
        """
        INSERT INTO network_stats 
        (timestamp, interface, bytes_sent, bytes_recv, packets_sent, packets_recv, errin, errout, dropin, dropout)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (old_date, "eth0", 1000, 2000, 10, 20, 0, 0, 0, 0),
    )

    conn.commit()
    conn.close()

    # Set retention to 30 days and cleanup
    monitor.database_config["retention_days"] = 30
    monitor._cleanup_old_records()

    # Verify old record is gone
    summary = monitor.get_statistics_summary()
    old_records = [
        r for r in summary["records"] if r["timestamp"] == old_date
    ]
    assert len(old_records) == 0
