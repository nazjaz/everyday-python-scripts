"""Unit tests for Habit Tracker."""

import json
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import HabitDataManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def data_file(temp_dir):
    """Create a temporary data file."""
    return temp_dir / "test_habits.json"


def test_habit_data_manager_initialization(data_file):
    """Test HabitDataManager initialization."""
    manager = HabitDataManager(data_file)
    assert manager.data_file == data_file
    assert isinstance(manager.habits, dict)


def test_add_habit(data_file):
    """Test adding a habit."""
    manager = HabitDataManager(data_file)

    result = manager.add_habit("Exercise", "Daily workout")
    assert result is True
    assert "Exercise" in manager.habits
    assert manager.habits["Exercise"]["description"] == "Daily workout"


def test_add_duplicate_habit(data_file):
    """Test adding duplicate habit."""
    manager = HabitDataManager(data_file)
    manager.add_habit("Exercise")

    result = manager.add_habit("Exercise")
    assert result is False


def test_remove_habit(data_file):
    """Test removing a habit."""
    manager = HabitDataManager(data_file)
    manager.add_habit("Exercise")

    result = manager.remove_habit("Exercise")
    assert result is True
    assert "Exercise" not in manager.habits


def test_remove_nonexistent_habit(data_file):
    """Test removing non-existent habit."""
    manager = HabitDataManager(data_file)

    result = manager.remove_habit("Nonexistent")
    assert result is False


def test_log_habit(data_file):
    """Test logging a habit."""
    manager = HabitDataManager(data_file)
    manager.add_habit("Exercise")

    result = manager.log_habit("Exercise", "2024-01-15")
    assert result is True
    assert "2024-01-15" in manager.habits["Exercise"]["entries"]


def test_log_habit_today(data_file):
    """Test logging habit for today."""
    manager = HabitDataManager(data_file)
    manager.add_habit("Exercise")

    result = manager.log_habit("Exercise")
    assert result is True

    today = datetime.now().strftime("%Y-%m-%d")
    assert today in manager.habits["Exercise"]["entries"]


def test_unlog_habit(data_file):
    """Test unlogging a habit."""
    manager = HabitDataManager(data_file)
    manager.add_habit("Exercise")
    manager.log_habit("Exercise", "2024-01-15")

    result = manager.unlog_habit("Exercise", "2024-01-15")
    assert result is True
    assert "2024-01-15" not in manager.habits["Exercise"]["entries"]


def test_is_logged(data_file):
    """Test checking if habit is logged."""
    manager = HabitDataManager(data_file)
    manager.add_habit("Exercise")
    manager.log_habit("Exercise", "2024-01-15")

    assert manager.is_logged("Exercise", "2024-01-15") is True
    assert manager.is_logged("Exercise", "2024-01-16") is False


def test_get_streak_no_entries(data_file):
    """Test streak calculation with no entries."""
    manager = HabitDataManager(data_file)
    manager.add_habit("Exercise")

    streak = manager.get_streak("Exercise")
    assert streak == 0


def test_get_streak_consecutive(data_file):
    """Test streak calculation with consecutive days."""
    manager = HabitDataManager(data_file)
    manager.add_habit("Exercise")

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    day_before = today - timedelta(days=2)

    manager.log_habit("Exercise", today.strftime("%Y-%m-%d"))
    manager.log_habit("Exercise", yesterday.strftime("%Y-%m-%d"))
    manager.log_habit("Exercise", day_before.strftime("%Y-%m-%d"))

    streak = manager.get_streak("Exercise")
    assert streak == 3


def test_get_streak_with_gap(data_file):
    """Test streak calculation with a gap."""
    manager = HabitDataManager(data_file)
    manager.add_habit("Exercise")

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    three_days_ago = today - timedelta(days=3)

    manager.log_habit("Exercise", today.strftime("%Y-%m-%d"))
    manager.log_habit("Exercise", yesterday.strftime("%Y-%m-%d"))
    manager.log_habit("Exercise", three_days_ago.strftime("%Y-%m-%d"))

    streak = manager.get_streak("Exercise")
    assert streak == 2  # Only today and yesterday


def test_get_weekly_stats(data_file):
    """Test weekly statistics calculation."""
    manager = HabitDataManager(data_file)
    manager.add_habit("Exercise")

    # Get current week start (Monday)
    today = datetime.now().date()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)

    # Log some days in current week
    manager.log_habit("Exercise", week_start.strftime("%Y-%m-%d"))
    manager.log_habit("Exercise", (week_start + timedelta(days=1)).strftime("%Y-%m-%d"))
    manager.log_habit("Exercise", (week_start + timedelta(days=2)).strftime("%Y-%m-%d"))

    stats = manager.get_weekly_stats("Exercise")

    assert stats["completed"] == 3
    assert stats["total"] == 7
    assert stats["percentage"] > 0


def test_get_weekly_stats_nonexistent_habit(data_file):
    """Test weekly stats for non-existent habit."""
    manager = HabitDataManager(data_file)

    stats = manager.get_weekly_stats("Nonexistent")
    assert stats["completed"] == 0
    assert stats["total"] == 7
    assert stats["percentage"] == 0.0


def test_save_and_load_data(data_file):
    """Test saving and loading data."""
    manager = HabitDataManager(data_file)
    manager.add_habit("Exercise", "Daily workout")
    manager.log_habit("Exercise", "2024-01-15")

    # Save data
    manager.save_data()

    # Create new manager and load data
    manager2 = HabitDataManager(data_file)

    assert "Exercise" in manager2.habits
    assert manager2.habits["Exercise"]["description"] == "Daily workout"
    assert "2024-01-15" in manager2.habits["Exercise"]["entries"]


def test_load_nonexistent_data_file(temp_dir):
    """Test loading from non-existent file."""
    data_file = temp_dir / "nonexistent.json"

    manager = HabitDataManager(data_file)
    assert isinstance(manager.habits, dict)
    assert len(manager.habits) == 0
