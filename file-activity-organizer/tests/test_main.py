"""Unit tests for File Activity Organizer application."""

import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.main import FileActivityTracker, load_config


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


class TestFileActivityTracker:
    """Test cases for FileActivityTracker class."""

    @pytest.fixture
    def config(self, temp_dir):
        """Create a test configuration."""
        source_dir = temp_dir / "source"
        active_dir = temp_dir / "active"
        archived_dir = temp_dir / "archived"
        dormant_dir = temp_dir / "dormant"
        source_dir.mkdir()
        active_dir.mkdir()
        archived_dir.mkdir()
        dormant_dir.mkdir()

        return {
            "source_directory": str(source_dir),
            "organization": {
                "active_directory": str(active_dir),
                "archived_directory": str(archived_dir),
                "dormant_directory": str(dormant_dir),
                "preserve_structure": False,
                "skip_duplicates": True,
            },
            "activity_thresholds": {
                "active_days": 30,
                "archived_days": 90,
                "dormant_days": 365,
            },
            "filtering": {
                "exclude_directories": [".git"],
                "exclude_files": [".DS_Store"],
                "exclude_extensions": [".tmp"],
            },
            "logging": {"level": "INFO", "file": str(temp_dir / "test.log")},
        }

    @pytest.fixture
    def tracker(self, config):
        """Create a FileActivityTracker instance."""
        return FileActivityTracker(config)

    def test_init(self, config):
        """Test FileActivityTracker initialization."""
        tracker = FileActivityTracker(config)
        assert tracker.config == config
        assert tracker.source_dir == Path(config["source_directory"])
        assert tracker.active_dir == Path(config["organization"]["active_directory"])

    def test_get_file_statistics(self, tracker, temp_dir):
        """Test getting file statistics."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        stats = tracker.get_file_statistics(test_file)
        assert stats is not None
        assert "modification_time" in stats
        assert "access_time" in stats
        assert "size" in stats
        assert isinstance(stats["modification_time"], datetime)
        assert isinstance(stats["access_time"], datetime)

    def test_get_file_statistics_nonexistent(self, tracker):
        """Test getting statistics for nonexistent file."""
        nonexistent = Path("/nonexistent/file.txt")
        result = tracker.get_file_statistics(nonexistent)
        assert result is None

    def test_calculate_file_hash(self, tracker, temp_dir):
        """Test calculating file hash."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        file_hash = tracker.calculate_file_hash(test_file)
        assert file_hash is not None
        assert len(file_hash) == 32  # MD5 hash length

    def test_calculate_file_hash_nonexistent(self, tracker):
        """Test calculating hash for nonexistent file."""
        nonexistent = Path("/nonexistent/file.txt")
        result = tracker.calculate_file_hash(nonexistent)
        assert result is None

    def test_should_exclude_file(self, tracker):
        """Test file exclusion logic."""
        excluded = Path("/some/file.DS_Store")
        assert tracker.should_exclude_file(excluded) is True

        excluded = Path("/some/file.tmp")
        assert tracker.should_exclude_file(excluded) is True

        excluded = Path("/some/.hidden")
        assert tracker.should_exclude_file(excluded) is True

        included = Path("/some/file.txt")
        assert tracker.should_exclude_file(included) is False

    def test_should_exclude_directory(self, tracker):
        """Test directory exclusion logic."""
        excluded = Path("/some/.git")
        assert tracker.should_exclude_directory(excluded) is True

        included = Path("/some/normal_dir")
        assert tracker.should_exclude_directory(included) is False

    def test_categorize_file_activity_active(self, tracker):
        """Test categorizing active files."""
        now = datetime.now()
        file_stats = {
            "modification_time": now - timedelta(days=10),
            "access_time": now - timedelta(days=5),
        }

        category = tracker.categorize_file_activity(file_stats, now)
        assert category == "active"

    def test_categorize_file_activity_archived(self, tracker):
        """Test categorizing archived files."""
        now = datetime.now()
        file_stats = {
            "modification_time": now - timedelta(days=60),
            "access_time": now - timedelta(days=50),
        }

        category = tracker.categorize_file_activity(file_stats, now)
        assert category == "archived"

    def test_categorize_file_activity_dormant(self, tracker):
        """Test categorizing dormant files."""
        now = datetime.now()
        file_stats = {
            "modification_time": now - timedelta(days=200),
            "access_time": now - timedelta(days=180),
        }

        category = tracker.categorize_file_activity(file_stats, now)
        assert category == "dormant"

    def test_scan_files(self, tracker, temp_dir):
        """Test scanning files."""
        source_dir = Path(tracker.source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)

        # Create test files
        file1 = source_dir / "file1.txt"
        file1.write_text("content 1")
        file2 = source_dir / "file2.txt"
        file2.write_text("content 2")

        files = tracker.scan_files()
        assert len(files) >= 2

    def test_scan_files_excludes(self, tracker, temp_dir):
        """Test that scanning excludes specified files."""
        source_dir = Path(tracker.source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)

        # Create files that should be excluded
        excluded1 = source_dir / ".DS_Store"
        excluded1.write_text("system file")
        excluded2 = source_dir / "file.tmp"
        excluded2.write_text("temp file")

        # Create a file that should be included
        included = source_dir / "file.txt"
        included.write_text("normal file")

        files = tracker.scan_files()
        file_names = [f["path"].name for f in files]
        assert ".DS_Store" not in file_names
        assert "file.tmp" not in file_names
        assert "file.txt" in file_names

    def test_detect_duplicates(self, tracker, temp_dir):
        """Test duplicate detection."""
        source_dir = Path(tracker.source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)

        # Create duplicate files
        file1 = source_dir / "file1.txt"
        file1.write_text("same content")
        file2 = source_dir / "file2.txt"
        file2.write_text("same content")

        # Create unique file
        file3 = source_dir / "file3.txt"
        file3.write_text("different content")

        files = [
            tracker.get_file_statistics(file1),
            tracker.get_file_statistics(file2),
            tracker.get_file_statistics(file3),
        ]
        files = [f for f in files if f is not None]

        duplicates = tracker.detect_duplicates(files)
        assert len(duplicates) >= 1

    def test_get_destination_path(self, tracker, temp_dir):
        """Test getting destination path."""
        source_file = temp_dir / "test.txt"
        dest_path = tracker.get_destination_path(source_file, "active")
        assert dest_path.parent == tracker.active_dir
        assert dest_path.name == "test.txt"

    def test_organize_file_dry_run(self, tracker, temp_dir):
        """Test organizing file in dry-run mode."""
        source_dir = Path(tracker.source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)

        test_file = source_dir / "test.txt"
        test_file.write_text("content")

        file_stats = tracker.get_file_statistics(test_file)
        result = tracker.organize_file(file_stats, "active", dry_run=True)
        assert result is True
        assert test_file.exists()  # Should still exist in dry-run

    def test_organize_file(self, tracker, temp_dir):
        """Test organizing file."""
        source_dir = Path(tracker.source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)

        test_file = source_dir / "test.txt"
        test_file.write_text("content")

        file_stats = tracker.get_file_statistics(test_file)
        result = tracker.organize_file(file_stats, "active", dry_run=False)
        assert result is True
        assert not test_file.exists()  # Should be moved

        # Check destination
        dest_file = tracker.active_dir / "test.txt"
        assert dest_file.exists()

    def test_process_files_dry_run(self, tracker, temp_dir):
        """Test processing files in dry-run mode."""
        source_dir = Path(tracker.source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)

        # Create files with different ages
        recent_file = source_dir / "recent.txt"
        recent_file.write_text("recent")
        os.utime(recent_file, (
            (datetime.now() - timedelta(days=10)).timestamp(),
            (datetime.now() - timedelta(days=10)).timestamp(),
        ))

        old_file = source_dir / "old.txt"
        old_file.write_text("old")
        os.utime(old_file, (
            (datetime.now() - timedelta(days=200)).timestamp(),
            (datetime.now() - timedelta(days=200)).timestamp(),
        ))

        results = tracker.process_files(dry_run=True, detect_dups=False)
        assert results["scanned"] >= 2
        assert recent_file.exists()  # Should still exist in dry-run
        assert old_file.exists()  # Should still exist in dry-run


class TestLoadConfig:
    """Test cases for load_config function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    def test_load_config_valid(self, temp_dir):
        """Test loading a valid configuration file."""
        config_file = temp_dir / "config.yaml"
        config_file.write_text(
            "source_directory: /test\norganization:\n  active_directory: /active\n"
        )

        config = load_config(config_file)
        assert config["source_directory"] == "/test"
        assert config["organization"]["active_directory"] == "/active"

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
