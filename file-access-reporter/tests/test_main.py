"""Unit tests for file access reporter module."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.main import FileAccessReporter


class TestFileAccessReporter:
    """Test cases for FileAccessReporter class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def config_file(self, temp_dir):
        """Create temporary config file."""
        config = {
            "scan": {"skip_patterns": [".git", "__pycache__"]},
            "report": {
                "output_file": "report.txt",
                "json_output_file": "report.json",
                "time_bucket": "day",
            },
            "logging": {"level": "INFO", "file": "logs/app.log"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return str(config_path)

    @pytest.fixture
    def reporter(self, config_file):
        """Create FileAccessReporter instance."""
        return FileAccessReporter(config_path=config_file)

    def test_load_config_success(self, temp_dir):
        """Test successful configuration loading."""
        config = {
            "scan": {"skip_patterns": []},
            "report": {"output_file": "test.txt"},
            "logging": {"level": "INFO"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        reporter = FileAccessReporter(config_path=str(config_path))
        assert reporter.config["report"]["output_file"] == "test.txt"

    def test_load_config_file_not_found(self):
        """Test FileNotFoundError when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            FileAccessReporter(config_path="nonexistent.yaml")

    def test_load_config_invalid_yaml(self, temp_dir):
        """Test YAMLError when config file is invalid."""
        config_path = temp_dir / "invalid.yaml"
        with open(config_path, "w") as f:
            f.write("invalid: yaml: content: [unclosed")

        with pytest.raises(yaml.YAMLError):
            FileAccessReporter(config_path=str(config_path))

    def test_should_skip_path(self, reporter):
        """Test path skipping logic."""
        path = Path("/some/path/.git/config")
        assert reporter._should_skip_path(path) is True

        path = Path("/some/path/normal_file.txt")
        assert reporter._should_skip_path(path) is False

    def test_get_time_bucket_day(self, reporter):
        """Test time bucket calculation for day."""
        dt = datetime(2024, 2, 7, 12, 30, 0)
        bucket = reporter._get_time_bucket(dt, "day")
        assert bucket == "2024-02-07"

    def test_get_time_bucket_week(self, reporter):
        """Test time bucket calculation for week."""
        dt = datetime(2024, 2, 7, 12, 30, 0)
        bucket = reporter._get_time_bucket(dt, "week")
        assert "2024" in bucket and "W" in bucket

    def test_get_time_bucket_month(self, reporter):
        """Test time bucket calculation for month."""
        dt = datetime(2024, 2, 7, 12, 30, 0)
        bucket = reporter._get_time_bucket(dt, "month")
        assert bucket == "2024-02"

    def test_get_time_bucket_year(self, reporter):
        """Test time bucket calculation for year."""
        dt = datetime(2024, 2, 7, 12, 30, 0)
        bucket = reporter._get_time_bucket(dt, "year")
        assert bucket == "2024"

    def test_calculate_days_since(self, reporter):
        """Test days since calculation."""
        yesterday = datetime.now() - timedelta(days=1)
        days = reporter._calculate_days_since(yesterday)
        assert days == 1

    def test_calculate_days_since_today(self, reporter):
        """Test days since calculation for today."""
        today = datetime.now()
        days = reporter._calculate_days_since(today)
        assert days == 0

    def test_get_access_frequency_category_today(self, reporter):
        """Test access frequency category for today."""
        assert reporter._get_access_frequency_category(0) == "Today"

    def test_get_access_frequency_category_week(self, reporter):
        """Test access frequency category for this week."""
        assert reporter._get_access_frequency_category(3) == "This Week"
        assert reporter._get_access_frequency_category(7) == "This Week"

    def test_get_access_frequency_category_month(self, reporter):
        """Test access frequency category for this month."""
        assert reporter._get_access_frequency_category(15) == "This Month"
        assert reporter._get_access_frequency_category(30) == "This Month"

    def test_get_access_frequency_category_over_year(self, reporter):
        """Test access frequency category for over 1 year."""
        assert reporter._get_access_frequency_category(400) == "Over 1 Year"

    def test_collect_file_data_success(self, reporter, temp_dir):
        """Test successful file data collection."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        file_data = reporter._collect_file_data(test_file)

        assert file_data is not None
        assert file_data["path"] == str(test_file)
        assert file_data["name"] == "test.txt"
        assert "last_accessed" in file_data
        assert "last_modified" in file_data
        assert "days_since_access" in file_data

    def test_collect_file_data_permission_error(self, reporter):
        """Test file data collection with permission error."""
        mock_path = MagicMock()
        mock_path.stat.side_effect = PermissionError("Access denied")

        file_data = reporter._collect_file_data(mock_path)

        assert file_data is None
        assert reporter.stats["errors"] > 0

    def test_format_size_bytes(self, reporter):
        """Test size formatting for bytes."""
        assert reporter._format_size(512) == "512.00 B"

    def test_format_size_kilobytes(self, reporter):
        """Test size formatting for kilobytes."""
        assert reporter._format_size(2048) == "2.00 KB"

    def test_format_size_megabytes(self, reporter):
        """Test size formatting for megabytes."""
        size = 5 * 1024 * 1024
        assert reporter._format_size(size) == "5.00 MB"

    def test_scan_directory(self, reporter, temp_dir):
        """Test directory scanning."""
        # Create test files
        (temp_dir / "file1.txt").write_text("content 1")
        (temp_dir / "file2.txt").write_text("content 2")

        reporter.scan_directory(str(temp_dir))

        assert reporter.stats["files_scanned"] == 2
        assert len(reporter.file_data) == 2
        assert reporter.stats["directories_scanned"] >= 1

    def test_scan_directory_not_found(self, reporter):
        """Test FileNotFoundError when directory doesn't exist."""
        with pytest.raises(FileNotFoundError):
            reporter.scan_directory("/nonexistent/path")

    def test_scan_directory_not_a_directory(self, reporter, temp_dir):
        """Test ValueError when path is not a directory."""
        test_file = temp_dir / "file.txt"
        test_file.write_text("content")

        with pytest.raises(ValueError, match="not a directory"):
            reporter.scan_directory(str(test_file))

    def test_generate_report(self, reporter, temp_dir):
        """Test report generation."""
        # Create test files and scan
        (temp_dir / "file1.txt").write_text("content 1")
        (temp_dir / "file2.txt").write_text("content 2")

        reporter.scan_directory(str(temp_dir))

        report_path = temp_dir / "test_report.txt"
        reporter.generate_report(output_path=str(report_path))

        assert report_path.exists()
        content = report_path.read_text()
        assert "FILE ACCESS AND MODIFICATION REPORT" in content
        assert "SUMMARY" in content
        assert "ACCESS FREQUENCY DISTRIBUTION" in content

    def test_export_json(self, reporter, temp_dir):
        """Test JSON export."""
        # Create test files and scan
        (temp_dir / "file1.txt").write_text("content 1")

        reporter.scan_directory(str(temp_dir))

        json_path = temp_dir / "test_report.json"
        reporter.export_json(output_path=str(json_path))

        assert json_path.exists()
        with open(json_path) as f:
            data = json.load(f)
        assert "stats" in data
        assert "files" in data
        assert "access_patterns" in data
