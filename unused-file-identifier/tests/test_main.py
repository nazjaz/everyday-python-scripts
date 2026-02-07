"""Unit tests for unused file identifier module."""

import json
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

from src.main import UnusedFileIdentifier


class TestUnusedFileIdentifier:
    """Test cases for UnusedFileIdentifier class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def config_file(self, temp_dir):
        """Create temporary config file."""
        config = {
            "scan": {
                "unused_threshold": "30d",
                "skip_patterns": [".git", "__pycache__"],
            },
            "report": {
                "output_file": "cleanup_report.txt",
                "json_output_file": "cleanup_report.json",
            },
            "logging": {
                "level": "INFO",
                "file": "logs/app.log",
            },
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return str(config_path)

    @pytest.fixture
    def identifier(self, config_file):
        """Create UnusedFileIdentifier instance."""
        return UnusedFileIdentifier(config_path=config_file)

    def test_load_config_success(self, temp_dir):
        """Test successful configuration loading."""
        config = {
            "scan": {"unused_threshold": "90d"},
            "report": {"output_file": "report.txt"},
            "logging": {"level": "INFO"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        identifier = UnusedFileIdentifier(config_path=str(config_path))
        assert identifier.config["scan"]["unused_threshold"] == "90d"

    def test_load_config_file_not_found(self):
        """Test FileNotFoundError when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            UnusedFileIdentifier(config_path="nonexistent.yaml")

    def test_load_config_invalid_yaml(self, temp_dir):
        """Test YAMLError when config file is invalid."""
        config_path = temp_dir / "invalid.yaml"
        with open(config_path, "w") as f:
            f.write("invalid: yaml: content: [unclosed")

        with pytest.raises(yaml.YAMLError):
            UnusedFileIdentifier(config_path=str(config_path))

    def test_parse_time_period_days(self, identifier):
        """Test parsing time period in days."""
        result = identifier._parse_time_period("30d")
        assert result == timedelta(days=30)

    def test_parse_time_period_weeks(self, identifier):
        """Test parsing time period in weeks."""
        result = identifier._parse_time_period("2w")
        assert result == timedelta(days=14)

    def test_parse_time_period_months(self, identifier):
        """Test parsing time period in months."""
        result = identifier._parse_time_period("6m")
        assert result == timedelta(days=180)

    def test_parse_time_period_years(self, identifier):
        """Test parsing time period in years."""
        result = identifier._parse_time_period("1y")
        assert result == timedelta(days=365)

    def test_parse_time_period_invalid_unit(self, identifier):
        """Test ValueError for invalid time unit."""
        with pytest.raises(ValueError, match="Invalid time unit"):
            identifier._parse_time_period("30x")

    def test_parse_time_period_invalid_format(self, identifier):
        """Test ValueError for invalid format."""
        with pytest.raises(ValueError):
            identifier._parse_time_period("30")

    def test_is_file_unused_recent_file(self, identifier, temp_dir):
        """Test that recent files are not marked as unused."""
        test_file = temp_dir / "recent.txt"
        test_file.write_text("test content")
        # Touch file to make it recent
        os.utime(test_file, (time.time(), time.time()))

        result = identifier._is_file_unused(
            test_file, timedelta(days=30)
        )
        assert result is None

    def test_is_file_unused_old_file(self, identifier, temp_dir):
        """Test that old files are marked as unused."""
        test_file = temp_dir / "old.txt"
        test_file.write_text("test content")
        # Set modification and access time to 60 days ago
        old_time = time.time() - (60 * 24 * 60 * 60)
        os.utime(test_file, (old_time, old_time))

        result = identifier._is_file_unused(
            test_file, timedelta(days=30)
        )
        assert result is not None
        assert result["path"] == str(test_file)
        assert "size_bytes" in result
        assert "last_modified" in result
        assert "last_accessed" in result

    def test_is_file_unused_permission_error(self, identifier):
        """Test handling of permission errors."""
        # Create a mock path that raises PermissionError
        mock_path = MagicMock()
        mock_path.stat.side_effect = PermissionError("Access denied")

        result = identifier._is_file_unused(
            mock_path, timedelta(days=30)
        )
        assert result is None
        assert identifier.stats["errors"] > 0

    def test_should_skip_path_matches_pattern(self, identifier):
        """Test that paths matching skip patterns are skipped."""
        identifier.config["scan"]["skip_patterns"] = [".git", "test"]
        path = Path("/some/path/.git/config")
        assert identifier._should_skip_path(path) is True

    def test_should_skip_path_no_match(self, identifier):
        """Test that paths not matching patterns are not skipped."""
        identifier.config["scan"]["skip_patterns"] = [".git"]
        path = Path("/some/path/normal_file.txt")
        assert identifier._should_skip_path(path) is False

    def test_scan_directory_finds_unused_files(self, identifier, temp_dir):
        """Test scanning directory finds unused files."""
        # Create old file
        old_file = temp_dir / "old_file.txt"
        old_file.write_text("old content")
        old_time = time.time() - (60 * 24 * 60 * 60)
        os.utime(old_file, (old_time, old_time))

        # Create recent file
        recent_file = temp_dir / "recent_file.txt"
        recent_file.write_text("recent content")
        os.utime(recent_file, (time.time(), time.time()))

        identifier.scan_directory(str(temp_dir))

        assert identifier.stats["files_scanned"] == 2
        assert identifier.stats["unused_files_found"] == 1
        assert len(identifier.unused_files) == 1
        assert identifier.unused_files[0]["path"] == str(old_file)

    def test_scan_directory_not_found(self, identifier):
        """Test FileNotFoundError when directory doesn't exist."""
        with pytest.raises(FileNotFoundError):
            identifier.scan_directory("/nonexistent/path")

    def test_scan_directory_not_a_directory(self, identifier, temp_dir):
        """Test ValueError when path is not a directory."""
        test_file = temp_dir / "file.txt"
        test_file.write_text("content")

        with pytest.raises(ValueError, match="not a directory"):
            identifier.scan_directory(str(test_file))

    def test_generate_report_creates_file(self, identifier, temp_dir):
        """Test that report generation creates output file."""
        # Create some unused files
        old_file = temp_dir / "old.txt"
        old_file.write_text("content")
        old_time = time.time() - (60 * 24 * 60 * 60)
        os.utime(old_file, (old_time, old_time))

        identifier.scan_directory(str(temp_dir))
        report_path = temp_dir / "test_report.txt"
        identifier.generate_report(output_path=str(report_path))

        assert report_path.exists()
        content = report_path.read_text()
        assert "UNUSED FILES CLEANUP REPORT" in content
        assert "SUMMARY" in content
        assert str(old_file) in content

    def test_export_json_creates_file(self, identifier, temp_dir):
        """Test that JSON export creates output file."""
        # Create some unused files
        old_file = temp_dir / "old.txt"
        old_file.write_text("content")
        old_time = time.time() - (60 * 24 * 60 * 60)
        os.utime(old_file, (old_time, old_time))

        identifier.scan_directory(str(temp_dir))
        json_path = temp_dir / "test_report.json"
        identifier.export_json(output_path=str(json_path))

        assert json_path.exists()
        with open(json_path) as f:
            data = json.load(f)
        assert "stats" in data
        assert "unused_files" in data
        assert len(data["unused_files"]) == 1

    def test_format_size_bytes(self, identifier):
        """Test size formatting for bytes."""
        assert identifier._format_size(512) == "512.00 B"

    def test_format_size_kilobytes(self, identifier):
        """Test size formatting for kilobytes."""
        assert identifier._format_size(2048) == "2.00 KB"

    def test_format_size_megabytes(self, identifier):
        """Test size formatting for megabytes."""
        size = 5 * 1024 * 1024
        assert identifier._format_size(size) == "5.00 MB"

    def test_format_size_gigabytes(self, identifier):
        """Test size formatting for gigabytes."""
        size = 2 * 1024 * 1024 * 1024
        assert identifier._format_size(size) == "2.00 GB"
