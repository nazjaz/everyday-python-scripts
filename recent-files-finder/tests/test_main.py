"""Unit tests for Recent Files Finder."""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import RecentFilesFinder


@pytest.fixture
def sample_config():
    """Create sample configuration dictionary."""
    return {
        "search": {
            "directory": ".",
            "recursive": True,
            "patterns": [],
            "exclude": {
                "patterns": [],
                "directories": [],
                "extensions": [],
            },
        },
        "report": {
            "output_directory": "output",
            "output_file": "report.txt",
        },
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
def temp_directory(tmp_path):
    """Create temporary directory with test files."""
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()

    # Create recent file (just now)
    recent_file = test_dir / "recent.txt"
    recent_file.write_text("recent content")
    time.sleep(0.1)  # Ensure different timestamps

    # Create old file (by setting mtime)
    old_file = test_dir / "old.txt"
    old_file.write_text("old content")
    old_mtime = time.time() - (10 * 24 * 60 * 60)  # 10 days ago
    os.utime(old_file, (old_mtime, old_mtime))

    return test_dir


class TestRecentFilesFinder:
    """Test cases for RecentFilesFinder class."""

    def test_init_loads_config(self, temp_config_file):
        """Test that initialization loads configuration file."""
        finder = RecentFilesFinder(config_path=temp_config_file)
        assert finder.config is not None
        assert "search" in finder.config

    def test_init_raises_file_not_found(self):
        """Test that initialization raises error for missing config file."""
        with pytest.raises(FileNotFoundError):
            RecentFilesFinder(config_path="nonexistent.yaml")

    def test_find_recent_files_by_days(self, temp_config_file, temp_directory):
        """Test finding files modified within last N days."""
        finder = RecentFilesFinder(config_path=temp_config_file)
        files = finder.find_recent_files(
            time_value=1, time_unit="days", directory=str(temp_directory)
        )

        assert len(files) >= 1
        file_names = [f["name"] for f in files]
        assert "recent.txt" in file_names
        assert "old.txt" not in file_names

    def test_find_recent_files_by_hours(self, temp_config_file, temp_directory):
        """Test finding files modified within last N hours."""
        finder = RecentFilesFinder(config_path=temp_config_file)
        files = finder.find_recent_files(
            time_value=1, time_unit="hours", directory=str(temp_directory)
        )

        assert len(files) >= 1
        file_names = [f["name"] for f in files]
        assert "recent.txt" in file_names

    def test_find_recent_files_by_minutes(self, temp_config_file, temp_directory):
        """Test finding files modified within last N minutes."""
        finder = RecentFilesFinder(config_path=temp_config_file)
        files = finder.find_recent_files(
            time_value=60, time_unit="minutes", directory=str(temp_directory)
        )

        assert len(files) >= 1
        file_names = [f["name"] for f in files]
        assert "recent.txt" in file_names

    def test_find_recent_files_invalid_unit(self, temp_config_file, temp_directory):
        """Test that invalid time unit raises error."""
        finder = RecentFilesFinder(config_path=temp_config_file)
        with pytest.raises(ValueError):
            finder.find_recent_files(
                time_value=1, time_unit="invalid", directory=str(temp_directory)
            )

    def test_find_recent_files_negative_time(self, temp_config_file, temp_directory):
        """Test that negative time value raises error."""
        finder = RecentFilesFinder(config_path=temp_config_file)
        with pytest.raises(ValueError):
            finder.find_recent_files(
                time_value=-1, time_unit="days", directory=str(temp_directory)
            )

    def test_find_recent_files_nonexistent_directory(self, temp_config_file):
        """Test that nonexistent directory raises error."""
        finder = RecentFilesFinder(config_path=temp_config_file)
        with pytest.raises(FileNotFoundError):
            finder.find_recent_files(time_value=1, time_unit="days", directory="/nonexistent")

    def test_find_recent_files_with_pattern(self, temp_config_file, temp_directory):
        """Test finding files with pattern matching."""
        finder = RecentFilesFinder(config_path=temp_config_file)

        # Create a .log file
        log_file = temp_directory / "app.log"
        log_file.write_text("log content")

        files = finder.find_recent_files(
            time_value=1,
            time_unit="days",
            directory=str(temp_directory),
            patterns=["*.log"],
        )

        file_names = [f["name"] for f in files]
        assert "app.log" in file_names

    def test_find_recent_files_non_recursive(self, temp_config_file, tmp_path):
        """Test non-recursive search."""
        finder = RecentFilesFinder(config_path=temp_config_file)
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        # Create file in root
        (test_dir / "root.txt").write_text("root")

        # Create subdirectory with file
        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested")

        files = finder.find_recent_files(
            time_value=1, time_unit="days", directory=str(test_dir), recursive=False
        )

        file_names = [f["name"] for f in files]
        assert "root.txt" in file_names
        assert "nested.txt" not in file_names

    def test_is_excluded_by_directory(self, temp_config_file):
        """Test directory exclusion."""
        finder = RecentFilesFinder(config_path=temp_config_file)
        finder.config["search"]["exclude"]["directories"] = [".git"]

        excluded_file = Path("/path/.git/config")
        assert finder._is_excluded(excluded_file) is True

        normal_file = Path("/path/file.txt")
        assert finder._is_excluded(normal_file) is False

    def test_is_excluded_by_extension(self, temp_config_file):
        """Test extension exclusion."""
        finder = RecentFilesFinder(config_path=temp_config_file)
        finder.config["search"]["exclude"]["extensions"] = [".tmp"]

        excluded_file = Path("file.tmp")
        assert finder._is_excluded(excluded_file) is True

        normal_file = Path("file.txt")
        assert finder._is_excluded(normal_file) is False

    def test_matches_pattern(self, temp_config_file):
        """Test pattern matching."""
        finder = RecentFilesFinder(config_path=temp_config_file)

        test_file = Path("test.log")
        assert finder._matches_pattern(test_file, ["*.log"]) is True
        assert finder._matches_pattern(test_file, ["*.txt"]) is False
        assert finder._matches_pattern(test_file, None) is True

    def test_format_size(self, temp_config_file):
        """Test file size formatting."""
        finder = RecentFilesFinder(config_path=temp_config_file)

        assert "B" in finder._format_size(500)
        assert "KB" in finder._format_size(5000)
        assert "MB" in finder._format_size(5000000)

    def test_generate_report(self, temp_config_file, temp_directory, tmp_path):
        """Test generating report."""
        finder = RecentFilesFinder(config_path=temp_config_file)
        finder.find_recent_files(time_value=1, time_unit="days", directory=str(temp_directory))

        report_file = tmp_path / "report.txt"
        report_content = finder.generate_report(str(report_file))

        assert len(report_content) > 0
        assert "Recent Files Report" in report_content
        assert report_file.exists()

    def test_get_statistics(self, temp_config_file):
        """Test getting statistics."""
        finder = RecentFilesFinder(config_path=temp_config_file)
        stats = finder.get_statistics()

        assert "files_scanned" in stats
        assert "files_matched" in stats
        assert "directories_scanned" in stats
        assert "errors" in stats
