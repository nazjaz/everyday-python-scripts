"""Unit tests for Temp Cleaner."""

import os
import shutil
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import TempCleaner


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
        "min_age_days": 1,
        "temp_directories": [str(temp_dir)],
        "exclusions": {
            "directories": [],
            "patterns": [],
            "extensions": [],
            "processes": [],
        },
        "operations": {"dry_run": False},
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


@pytest.fixture
def old_file(temp_dir):
    """Create an old file for testing."""
    old_file_path = temp_dir / "old_file.txt"
    old_file_path.write_text("test content")
    # Set modification time to 2 days ago
    two_days_ago = time.time() - (2 * 24 * 60 * 60)
    os.utime(old_file_path, (two_days_ago, two_days_ago))
    return old_file_path


@pytest.fixture
def new_file(temp_dir):
    """Create a new file for testing."""
    new_file_path = temp_dir / "new_file.txt"
    new_file_path.write_text("test content")
    return new_file_path


def test_temp_cleaner_initialization(config_file):
    """Test TempCleaner initialization."""
    cleaner = TempCleaner(config_path=config_file)
    assert cleaner.config is not None
    assert len(cleaner.temp_directories) > 0


def test_load_config_file_not_found():
    """Test that FileNotFoundError is raised when config file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        TempCleaner(config_path="nonexistent.yaml")


def test_is_file_old_enough(config_file, old_file, new_file):
    """Test file age checking."""
    cleaner = TempCleaner(config_path=config_file)
    cleaner.config["min_age_days"] = 1

    assert cleaner._is_file_old_enough(old_file) is True
    assert cleaner._is_file_old_enough(new_file) is False


def test_should_exclude_file_by_directory(config_file, temp_dir):
    """Test exclusion by directory."""
    cleaner = TempCleaner(config_path=config_file)
    excluded_dir = temp_dir / "excluded"
    excluded_dir.mkdir()
    excluded_file = excluded_dir / "file.txt"
    excluded_file.write_text("test")

    cleaner.config["exclusions"]["directories"] = [str(excluded_dir)]

    assert cleaner._should_exclude_file(excluded_file) is True

    normal_file = temp_dir / "normal.txt"
    normal_file.write_text("test")
    assert cleaner._should_exclude_file(normal_file) is False


def test_should_exclude_file_by_pattern(config_file, temp_dir):
    """Test exclusion by pattern."""
    cleaner = TempCleaner(config_path=config_file)
    cleaner.config["exclusions"]["patterns"] = [".lock"]

    lock_file = temp_dir / "file.lock"
    lock_file.write_text("test")
    assert cleaner._should_exclude_file(lock_file) is True

    normal_file = temp_dir / "file.txt"
    normal_file.write_text("test")
    assert cleaner._should_exclude_file(normal_file) is False


def test_should_exclude_file_by_extension(config_file, temp_dir):
    """Test exclusion by extension."""
    cleaner = TempCleaner(config_path=config_file)
    cleaner.config["exclusions"]["extensions"] = [".pid"]

    pid_file = temp_dir / "process.pid"
    pid_file.write_text("12345")
    assert cleaner._should_exclude_file(pid_file) is True

    normal_file = temp_dir / "file.txt"
    normal_file.write_text("test")
    assert cleaner._should_exclude_file(normal_file) is False


def test_is_file_in_use(config_file, temp_dir):
    """Test file in use detection."""
    cleaner = TempCleaner(config_path=config_file)
    test_file = temp_dir / "test.txt"
    test_file.write_text("test")

    # File should not be in use (we just created it)
    assert cleaner._is_file_in_use(test_file) is False


def test_format_size():
    """Test file size formatting."""
    cleaner = TempCleaner.__new__(TempCleaner)
    cleaner.config = {}

    assert "B" in cleaner._format_size(500)
    assert "KB" in cleaner._format_size(2048)
    assert "MB" in cleaner._format_size(2 * 1024 * 1024)
    assert cleaner._format_size(0) == "0 B"


def test_delete_file_dry_run(config_file, old_file):
    """Test file deletion in dry run mode."""
    cleaner = TempCleaner(config_path=config_file)
    cleaner.config["operations"]["dry_run"] = True

    assert old_file.exists()
    result = cleaner._delete_file(old_file)
    assert result is True
    assert old_file.exists()  # File should still exist in dry run


def test_delete_file_actual(config_file, old_file):
    """Test actual file deletion."""
    cleaner = TempCleaner(config_path=config_file)
    cleaner.config["operations"]["dry_run"] = False

    assert old_file.exists()
    result = cleaner._delete_file(old_file)
    assert result is True
    assert not old_file.exists()  # File should be deleted


def test_clean_directory(config_file, temp_dir, old_file, new_file):
    """Test cleaning a directory."""
    cleaner = TempCleaner(config_path=config_file)
    cleaner.config["min_age_days"] = 1
    cleaner.config["operations"]["dry_run"] = False

    # Create excluded file
    excluded_file = temp_dir / "excluded.lock"
    excluded_file.write_text("test")
    two_days_ago = time.time() - (2 * 24 * 60 * 60)
    os.utime(excluded_file, (two_days_ago, two_days_ago))
    cleaner.config["exclusions"]["patterns"] = [".lock"]

    cleaner._clean_directory(temp_dir)

    # Old file should be deleted
    assert not old_file.exists()
    # New file should remain
    assert new_file.exists()
    # Excluded file should remain
    assert excluded_file.exists()


def test_clean_temp_files(config_file, temp_dir, old_file):
    """Test main cleanup function."""
    cleaner = TempCleaner(config_path=config_file)
    cleaner.config["min_age_days"] = 1
    cleaner.config["operations"]["dry_run"] = False

    stats = cleaner.clean_temp_files()

    assert stats["files_scanned"] > 0
    assert stats["files_deleted"] > 0
    assert not old_file.exists()


def test_environment_variable_overrides(temp_dir):
    """Test that environment variables override config."""
    config = {
        "min_age_days": 7,
        "temp_directories": [str(temp_dir)],
        "exclusions": {
            "directories": [],
            "patterns": [],
            "extensions": [],
            "processes": [],
        },
        "operations": {"dry_run": False},
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

    with patch.dict(os.environ, {"MIN_AGE_DAYS": "14"}):
        cleaner = TempCleaner(config_path=str(config_path))
        assert cleaner.config["min_age_days"] == 14
