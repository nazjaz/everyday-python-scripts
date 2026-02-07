"""Unit tests for calendar manager module."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import yaml

from src.main import CalendarManager


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    return tempfile.mkdtemp()


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary configuration file."""
    calendar_file = Path(temp_dir) / "test_calendar.ics"
    config = {
        "calendar": {
            "file": str(calendar_file),
            "create_if_missing": True,
            "backup_enabled": False,
        },
        "reminders": {
            "enabled": True,
            "check_interval": 60,
            "default_reminder_minutes": 15,
        },
        "notifications": {
            "enabled": True,
            "notification_duration": 10,
        },
        "display": {
            "default_view": "week",
            "start_of_week": "monday",
            "time_format": "24h",
        },
        "event_defaults": {
            "duration_minutes": 60,
            "reminder_minutes": 15,
        },
        "gui": {
            "window_title": "Test Calendar",
            "window_width": 900,
            "window_height": 700,
            "theme": {
                "background_color": "#FFFFFF",
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


def test_calendar_manager_initialization(config_file):
    """Test CalendarManager initializes correctly."""
    manager = CalendarManager(config_path=str(config_file))
    assert manager.calendar_path.exists()
    assert len(manager.events) == 0


def test_calendar_manager_missing_config():
    """Test CalendarManager raises error for missing config."""
    with pytest.raises(FileNotFoundError):
        CalendarManager(config_path="nonexistent.yaml")


def test_load_calendar_new_file(config_file):
    """Test loading new calendar file."""
    manager = CalendarManager(config_path=str(config_file))
    result = manager.load_calendar()

    assert result is True
    assert manager.calendar is not None
    assert len(manager.events) == 0


def test_add_event(config_file):
    """Test adding event to calendar."""
    manager = CalendarManager(config_path=str(config_file))
    manager.load_calendar()

    dtstart = datetime.now()
    result = manager.add_event(
        "Test Event",
        dtstart,
        description="Test description",
        location="Test location",
        reminder_minutes=15,
    )

    assert result is True
    assert len(manager.events) == 1
    assert manager.events[0]["summary"] == "Test Event"


def test_add_event_with_default_duration(config_file):
    """Test adding event with default duration."""
    manager = CalendarManager(config_path=str(config_file))
    manager.load_calendar()

    dtstart = datetime.now()
    result = manager.add_event("Test Event", dtstart)

    assert result is True
    assert len(manager.events) == 1
    event = manager.events[0]
    assert event["dtend"] == dtstart + timedelta(minutes=60)


def test_delete_event(config_file):
    """Test deleting event from calendar."""
    manager = CalendarManager(config_path=str(config_file))
    manager.load_calendar()

    # Add event
    dtstart = datetime.now()
    manager.add_event("Test Event", dtstart)
    uid = manager.events[0]["uid"]

    # Delete event
    result = manager.delete_event(uid)

    assert result is True
    assert len(manager.events) == 0


def test_get_events_for_date(config_file):
    """Test getting events for specific date."""
    manager = CalendarManager(config_path=str(config_file))
    manager.load_calendar()

    # Add events for today and tomorrow
    today = datetime.now()
    tomorrow = today + timedelta(days=1)

    manager.add_event("Today Event", today)
    manager.add_event("Tomorrow Event", tomorrow)

    # Get today's events
    today_events = manager.get_events_for_date(today)

    assert len(today_events) == 1
    assert today_events[0]["summary"] == "Today Event"


def test_save_calendar(config_file):
    """Test saving calendar to file."""
    manager = CalendarManager(config_path=str(config_file))
    manager.load_calendar()

    # Add event
    dtstart = datetime.now()
    manager.add_event("Test Event", dtstart)

    # Save
    result = manager.save_calendar()

    assert result is True
    assert manager.calendar_path.exists()

    # Reload and verify
    manager2 = CalendarManager(config_path=str(config_file))
    manager2.load_calendar()

    assert len(manager2.events) == 1
    assert manager2.events[0]["summary"] == "Test Event"


@patch("src.main.notification")
def test_send_reminder(mock_notification, config_file):
    """Test sending reminder notification."""
    manager = CalendarManager(config_path=str(config_file))

    event = {
        "summary": "Test Event",
        "dtstart": datetime.now() + timedelta(minutes=10),
        "location": "Test Location",
    }

    manager._send_reminder(event)

    if notification:
        mock_notification.notify.assert_called_once()
