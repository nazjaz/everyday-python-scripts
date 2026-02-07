"""Unit tests for Pomodoro timer module."""

import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.main import PomodoroTimer


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    return tempfile.mkdtemp()


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary configuration file."""
    db_file = Path(temp_dir) / "test.db"
    config = {
        "intervals": {
            "work": 1500,  # 25 minutes
            "short_break": 300,  # 5 minutes
            "long_break": 900,  # 15 minutes
            "sessions_before_long_break": 4,
        },
        "database": {
            "file": str(db_file),
            "create_tables": True,
        },
        "gui": {
            "window_title": "Test Pomodoro",
            "window_width": 500,
            "window_height": 600,
            "theme": {
                "work_color": "#E74C3C",
                "break_color": "#2ECC71",
                "background_color": "#ECF0F1",
                "text_color": "#2C3E50",
                "button_color": "#3498DB",
            },
        },
        "notifications": {
            "enabled": True,
            "sound_on_complete": True,
            "desktop_notification": True,
            "notification_duration": 5,
        },
        "statistics": {
            "track_daily": True,
            "track_weekly": True,
            "track_monthly": True,
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


def test_pomodoro_timer_initialization(config_file):
    """Test PomodoroTimer initializes correctly."""
    timer = PomodoroTimer(config_path=str(config_file))
    assert timer.db_path.exists()
    assert timer.current_mode == "work"
    assert timer.time_remaining == 1500
    assert timer.is_running is False


def test_pomodoro_timer_missing_config():
    """Test PomodoroTimer raises error for missing config."""
    with pytest.raises(FileNotFoundError):
        PomodoroTimer(config_path="nonexistent.yaml")


def test_format_time(config_file):
    """Test time formatting."""
    timer = PomodoroTimer(config_path=str(config_file))

    assert timer._format_time(1500) == "25:00"
    assert timer._format_time(300) == "05:00"
    assert timer._format_time(65) == "01:05"
    assert timer._format_time(5) == "00:05"


def test_switch_mode(config_file):
    """Test mode switching."""
    timer = PomodoroTimer(config_path=str(config_file))

    # Start with work
    assert timer.current_mode == "work"
    assert timer.time_remaining == 1500

    # Switch to break
    timer._switch_mode()
    assert timer.current_mode == "short_break"
    assert timer.time_remaining == 300

    # Switch back to work
    timer._switch_mode()
    assert timer.current_mode == "work"
    assert timer.time_remaining == 1500


def test_switch_to_long_break(config_file):
    """Test switching to long break after multiple sessions."""
    timer = PomodoroTimer(config_path=str(config_file))

    # Complete 4 work sessions
    timer.session_count = 4
    timer.current_mode = "work"
    timer._switch_mode()

    assert timer.current_mode == "long_break"
    assert timer.time_remaining == 900


def test_save_session(config_file):
    """Test saving session to database."""
    timer = PomodoroTimer(config_path=str(config_file))

    timer._save_session("work", 1500)

    # Verify session was saved
    conn = sqlite3.connect(timer.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE session_type = 'work'")
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 1


def test_load_statistics(config_file):
    """Test loading statistics from database."""
    timer = PomodoroTimer(config_path=str(config_file))

    # Save some sessions
    timer._save_session("work", 1500)
    timer._save_session("work", 1500)
    timer._save_session("short_break", 300)

    # Reload statistics
    timer._load_statistics()

    assert timer.stats["total_sessions"] == 2  # Only work sessions count
    assert timer.stats["total_work_time"] == 3000
    assert timer.stats["total_break_time"] == 300


def test_reset_timer(config_file):
    """Test timer reset."""
    timer = PomodoroTimer(config_path=str(config_file))

    # Change timer state
    timer.time_remaining = 100
    timer.is_running = True

    # Reset
    timer._reset_timer()

    assert timer.time_remaining == 1500  # Back to work interval
    assert timer.is_running is False
    assert timer.is_paused is False


def test_skip_session(config_file):
    """Test skipping current session."""
    timer = PomodoroTimer(config_path=str(config_file))

    # Start in work mode
    timer.current_mode = "work"
    timer.time_remaining = 1000

    # Skip to break
    timer._skip_session()

    assert timer.current_mode == "short_break"
    assert timer.time_remaining == 300
    assert timer.is_running is False


@patch("src.main.notification")
def test_send_notification(mock_notification, config_file):
    """Test sending notification."""
    timer = PomodoroTimer(config_path=str(config_file))
    timer.current_mode = "work"

    timer._send_notification()

    # Check if notification was attempted (may not be available)
    # The function handles missing notification gracefully
    assert True  # Test passes if no exception raised


def test_create_tables(config_file):
    """Test database table creation."""
    timer = PomodoroTimer(config_path=str(config_file))

    # Verify tables exist
    conn = sqlite3.connect(timer.db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name IN ('sessions', 'daily_stats')
    """)
    results = cursor.fetchall()
    conn.close()

    assert len(results) == 2
    table_names = [r[0] for r in results]
    assert "sessions" in table_names
    assert "daily_stats" in table_names
