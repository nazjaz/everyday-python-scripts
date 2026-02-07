"""Unit tests for temporary file cleaner module."""

import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.main import TemporaryFileCleaner


class TestTemporaryFileCleaner:
    """Test cases for TemporaryFileCleaner class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def config_file(self, temp_dir):
        """Create temporary config file."""
        config = {
            "cleanup": {
                "temp_extensions": [".tmp", ".download", ".part"],
                "temp_filename_patterns": [".tmp", "temp_"],
                "incomplete_min_age_days": 1,
                "incomplete_min_size_bytes": 1024,
            },
            "safety": {
                "min_age_days": 0,
                "max_size_bytes": None,
                "protected_patterns": ["important"],
                "protected_directories": [],
            },
            "scan": {"skip_patterns": [".git"]},
            "report": {"output_file": "report.txt"},
            "logging": {"level": "INFO", "file": "logs/app.log"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return str(config_path)

    @pytest.fixture
    def cleaner(self, config_file):
        """Create TemporaryFileCleaner instance."""
        return TemporaryFileCleaner(config_path=config_file)

    def test_load_config_success(self, temp_dir):
        """Test successful configuration loading."""
        config = {
            "cleanup": {"temp_extensions": [".tmp"]},
            "safety": {"min_age_days": 1},
            "logging": {"level": "INFO"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        cleaner = TemporaryFileCleaner(config_path=str(config_path))
        assert cleaner.config["cleanup"]["temp_extensions"] == [".tmp"]

    def test_load_config_file_not_found(self):
        """Test FileNotFoundError when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            TemporaryFileCleaner(config_path="nonexistent.yaml")

    def test_is_temporary_extension(self, cleaner, temp_dir):
        """Test temporary extension detection."""
        test_file = temp_dir / "file.tmp"
        assert cleaner._is_temporary_extension(test_file) is True

        test_file = temp_dir / "file.txt"
        assert cleaner._is_temporary_extension(test_file) is False

    def test_is_temporary_filename(self, cleaner, temp_dir):
        """Test temporary filename detection."""
        test_file = temp_dir / "temp_file.txt"
        assert cleaner._is_temporary_filename(test_file) is True

        test_file = temp_dir / "normal_file.txt"
        assert cleaner._is_temporary_filename(test_file) is False

    def test_is_incomplete_download(self, cleaner, temp_dir):
        """Test incomplete download detection."""
        # Create old temporary file
        test_file = temp_dir / "file.download"
        test_file.write_text("content")
        old_time = time.time() - (2 * 24 * 60 * 60)  # 2 days ago
        test_file.touch()
        os.utime(test_file, (old_time, old_time))

        assert cleaner._is_incomplete_download(test_file) is True

    def test_is_incomplete_download_recent(self, cleaner, temp_dir):
        """Test incomplete download detection for recent files."""
        # Create recent temporary file
        test_file = temp_dir / "file.download"
        test_file.write_text("content" * 1000)  # Large enough
        test_file.touch()

        # Recent file should not be considered incomplete
        assert cleaner._is_incomplete_download(test_file) is False

    def test_is_safe_to_delete_age_check(self, cleaner, temp_dir):
        """Test safety check for file age."""
        cleaner.config["safety"]["min_age_days"] = 2

        test_file = temp_dir / "file.tmp"
        test_file.write_text("content")
        file_info = {
            "age_days": 1,
            "size_bytes": 100,
        }

        assert cleaner._is_safe_to_delete(test_file, file_info) is False

    def test_is_safe_to_delete_size_check(self, cleaner, temp_dir):
        """Test safety check for file size."""
        cleaner.config["safety"]["max_size_bytes"] = 1000

        test_file = temp_dir / "file.tmp"
        test_file.write_text("content")
        file_info = {
            "age_days": 5,
            "size_bytes": 2000,
        }

        assert cleaner._is_safe_to_delete(test_file, file_info) is False

    def test_is_safe_to_delete_protected_pattern(self, cleaner, temp_dir):
        """Test safety check for protected patterns."""
        test_file = temp_dir / "important_file.tmp"
        test_file.write_text("content")
        file_info = {
            "age_days": 5,
            "size_bytes": 100,
        }

        assert cleaner._is_safe_to_delete(test_file, file_info) is False

    def test_should_skip_path(self, cleaner):
        """Test path skipping logic."""
        path = Path("/some/path/.git/config")
        assert cleaner._should_skip_path(path) is True

        path = Path("/some/path/normal_file.txt")
        assert cleaner._should_skip_path(path) is False

    def test_scan_directory(self, cleaner, temp_dir):
        """Test directory scanning."""
        # Create temporary files
        (temp_dir / "file1.tmp").write_text("content")
        (temp_dir / "file2.download").write_text("content")
        (temp_dir / "normal.txt").write_text("content")

        cleaner.scan_directory(str(temp_dir))

        assert cleaner.stats["files_scanned"] == 3
        assert cleaner.stats["temp_files_found"] >= 2

    def test_scan_directory_not_found(self, cleaner):
        """Test FileNotFoundError when directory doesn't exist."""
        with pytest.raises(FileNotFoundError):
            cleaner.scan_directory("/nonexistent/path")

    def test_cleanup_files_dry_run(self, cleaner, temp_dir):
        """Test file cleanup in dry-run mode."""
        # Create temporary file
        test_file = temp_dir / "file.tmp"
        test_file.write_text("content")

        cleaner.temp_files = [
            {
                "path": str(test_file),
                "size_bytes": 100,
                "age_days": 5,
            }
        ]

        cleaner.cleanup_files(dry_run=True)

        # File should still exist
        assert test_file.exists()
        assert cleaner.stats["files_deleted"] == 1

    def test_cleanup_files_actual(self, cleaner, temp_dir):
        """Test file cleanup in actual mode."""
        # Create temporary file
        test_file = temp_dir / "file.tmp"
        test_file.write_text("content")

        cleaner.temp_files = [
            {
                "path": str(test_file),
                "size_bytes": 100,
                "age_days": 5,
            }
        ]

        cleaner.cleanup_files(dry_run=False)

        # File should be deleted
        assert not test_file.exists()
        assert cleaner.stats["files_deleted"] == 1

    def test_generate_report(self, cleaner, temp_dir):
        """Test report generation."""
        # Create test data
        cleaner.temp_files = [
            {
                "path": str(temp_dir / "file.tmp"),
                "size_bytes": 100,
                "age_days": 5,
                "is_temp_extension": True,
                "is_temp_filename": False,
                "is_incomplete": False,
            }
        ]

        report_path = temp_dir / "test_report.txt"
        cleaner.generate_report(output_path=str(report_path))

        assert report_path.exists()
        content = report_path.read_text()
        assert "TEMPORARY FILE CLEANUP REPORT" in content
        assert "SUMMARY" in content

    def test_format_size(self, cleaner):
        """Test size formatting."""
        assert cleaner._format_size(512) == "512.00 B"
        assert cleaner._format_size(2048) == "2.00 KB"
        assert cleaner._format_size(1048576) == "1.00 MB"
