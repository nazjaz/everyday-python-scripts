"""Unit tests for File Statistics Generator."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import FileStatisticsGenerator


@pytest.fixture
def sample_config():
    """Create sample configuration dictionary."""
    return {
        "scan": {
            "directory": ".",
            "recursive": True,
            "exclude": {
                "patterns": [],
                "directories": [],
                "extensions": [],
            },
        },
        "statistics": {
            "top_extensions": 10,
            "top_directories": 10,
            "size_ranges": [
                {"name": "Small", "max": 1024},
                {"name": "Large", "max": float("inf")},
            ],
            "trends": {
                "group_by": "month",
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

    # Create files with different sizes and extensions
    (test_dir / "file1.txt").write_text("small content")
    (test_dir / "file2.jpg").write_text("x" * 5000)  # Larger file
    (test_dir / "file3.pdf").write_text("x" * 2000)
    (test_dir / "file4.txt").write_text("another text file")

    return test_dir


class TestFileStatisticsGenerator:
    """Test cases for FileStatisticsGenerator class."""

    def test_init_loads_config(self, temp_config_file):
        """Test that initialization loads configuration file."""
        generator = FileStatisticsGenerator(config_path=temp_config_file)
        assert generator.config is not None
        assert "scan" in generator.config

    def test_init_raises_file_not_found(self):
        """Test that initialization raises error for missing config file."""
        with pytest.raises(FileNotFoundError):
            FileStatisticsGenerator(config_path="nonexistent.yaml")

    def test_scan_files(self, temp_config_file, temp_directory):
        """Test scanning files."""
        generator = FileStatisticsGenerator(config_path=temp_config_file)
        files = generator.scan_files(str(temp_directory))

        assert len(files) > 0
        assert all("path" in f for f in files)
        assert all("size" in f for f in files)
        assert all("extension" in f for f in files)

    def test_scan_files_nonexistent_directory(self, temp_config_file):
        """Test that nonexistent directory raises error."""
        generator = FileStatisticsGenerator(config_path=temp_config_file)
        with pytest.raises(FileNotFoundError):
            generator.scan_files("/nonexistent/path")

    def test_scan_files_non_recursive(self, temp_config_file, tmp_path):
        """Test non-recursive scanning."""
        generator = FileStatisticsGenerator(config_path=temp_config_file)
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        # Create file in root
        (test_dir / "file.txt").write_text("content")

        # Create subdirectory with file
        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "file.txt").write_text("content")

        files = generator.scan_files(str(test_dir), recursive=False)

        # Should find file in root but not in subdirectory
        assert len(files) >= 1

    def test_calculate_statistics(self, temp_config_file, temp_directory):
        """Test calculating statistics."""
        generator = FileStatisticsGenerator(config_path=temp_config_file)
        generator.scan_files(str(temp_directory))
        statistics = generator.calculate_statistics()

        assert "summary" in statistics
        assert "extensions" in statistics
        assert "size_distribution" in statistics
        assert statistics["summary"]["total_files"] > 0

    def test_calculate_statistics_raises_error_without_scan(self, temp_config_file):
        """Test that calculating statistics without scanning raises error."""
        generator = FileStatisticsGenerator(config_path=temp_config_file)
        with pytest.raises(ValueError, match="No file data"):
            generator.calculate_statistics()

    def test_calculate_statistics_summary(self, temp_config_file, temp_directory):
        """Test summary statistics calculation."""
        generator = FileStatisticsGenerator(config_path=temp_config_file)
        generator.scan_files(str(temp_directory))
        statistics = generator.calculate_statistics()

        summary = statistics["summary"]
        assert "total_files" in summary
        assert "total_size" in summary
        assert "average_size" in summary
        assert "median_size" in summary
        assert summary["total_files"] > 0
        assert summary["total_size"] > 0

    def test_calculate_statistics_extensions(self, temp_config_file, temp_directory):
        """Test extension statistics calculation."""
        generator = FileStatisticsGenerator(config_path=temp_config_file)
        generator.scan_files(str(temp_directory))
        statistics = generator.calculate_statistics()

        extensions = statistics["extensions"]
        assert "total_unique" in extensions
        assert "most_common" in extensions
        assert len(extensions["most_common"]) > 0

    def test_calculate_statistics_size_distribution(self, temp_config_file, temp_directory):
        """Test size distribution calculation."""
        generator = FileStatisticsGenerator(config_path=temp_config_file)
        generator.scan_files(str(temp_directory))
        statistics = generator.calculate_statistics()

        size_dist = statistics["size_distribution"]
        assert len(size_dist) > 0
        assert all("name" in r for r in size_dist)
        assert all("count" in r for r in size_dist)

    def test_calculate_statistics_date_trends(self, temp_config_file, temp_directory):
        """Test date trends calculation."""
        generator = FileStatisticsGenerator(config_path=temp_config_file)
        generator.scan_files(str(temp_directory))
        statistics = generator.calculate_statistics()

        trends = statistics["date_trends"]
        assert "group_by" in trends
        assert "periods" in trends

    def test_calculate_statistics_directory_stats(self, temp_config_file, temp_directory):
        """Test directory statistics calculation."""
        generator = FileStatisticsGenerator(config_path=temp_config_file)
        generator.scan_files(str(temp_directory))
        statistics = generator.calculate_statistics()

        dir_stats = statistics["directory_statistics"]
        assert "total_directories" in dir_stats
        assert "top_by_count" in dir_stats
        assert "top_by_size" in dir_stats

    def test_calculate_statistics_age_stats(self, temp_config_file, temp_directory):
        """Test age statistics calculation."""
        generator = FileStatisticsGenerator(config_path=temp_config_file)
        generator.scan_files(str(temp_directory))
        statistics = generator.calculate_statistics()

        age_stats = statistics["age_statistics"]
        assert "ranges" in age_stats
        assert len(age_stats["ranges"]) > 0

    def test_format_size(self, temp_config_file):
        """Test file size formatting."""
        generator = FileStatisticsGenerator(config_path=temp_config_file)

        assert "B" in generator._format_size(500)
        assert "KB" in generator._format_size(5000)
        assert "MB" in generator._format_size(5000000)
        assert "GB" in generator._format_size(5000000000)

    def test_is_excluded_by_directory(self, temp_config_file):
        """Test directory exclusion."""
        generator = FileStatisticsGenerator(config_path=temp_config_file)
        generator.config["scan"]["exclude"]["directories"] = [".git"]

        excluded_file = Path("/path/.git/config")
        assert generator._is_excluded(excluded_file) is True

        normal_file = Path("/path/file.txt")
        assert generator._is_excluded(normal_file) is False

    def test_generate_report_text(self, temp_config_file, temp_directory, tmp_path):
        """Test generating text report."""
        generator = FileStatisticsGenerator(config_path=temp_config_file)
        generator.scan_files(str(temp_directory))
        generator.calculate_statistics()

        report_file = tmp_path / "report.txt"
        report_content = generator.generate_report(str(report_file), format="text")

        assert len(report_content) > 0
        assert "File Statistics Report" in report_content
        assert report_file.exists()

    def test_generate_report_json(self, temp_config_file, temp_directory, tmp_path):
        """Test generating JSON report."""
        generator = FileStatisticsGenerator(config_path=temp_config_file)
        generator.scan_files(str(temp_directory))
        generator.calculate_statistics()

        report_file = tmp_path / "report.json"
        report_content = generator.generate_report(str(report_file), format="json")

        assert len(report_content) > 0
        import json

        data = json.loads(report_content)
        assert "summary" in data

    def test_generate_report_raises_error_without_stats(self, temp_config_file):
        """Test that generating report without statistics raises error."""
        generator = FileStatisticsGenerator(config_path=temp_config_file)
        with pytest.raises(ValueError, match="No statistics"):
            generator.generate_report()

    def test_get_statistics(self, temp_config_file, temp_directory):
        """Test getting statistics."""
        generator = FileStatisticsGenerator(config_path=temp_config_file)
        generator.scan_files(str(temp_directory))
        generator.calculate_statistics()

        stats = generator.get_statistics()
        assert "summary" in stats
        assert "extensions" in stats
