"""Unit tests for File Size Analyzer."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import FileSizeAnalyzer


@pytest.fixture
def sample_config():
    """Create sample configuration dictionary."""
    return {
        "analysis": {
            "scan_directory": ".",
            "recursive": True,
            "exclude": {
                "patterns": [],
                "directories": [],
                "extensions": [],
            },
        },
        "cleanup": {
            "large_file_threshold_mb": 100,
            "old_file_threshold_days": 365,
            "duplicate_extension_threshold": 100,
            "extension_recommendations": {
                "log": {
                    "size_threshold_mb": 50,
                    "priority": "medium",
                    "reason": "Large log files",
                    "suggestion": "Archive log files",
                },
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

    # Create test files with different sizes
    (test_dir / "small.txt").write_text("small" * 10)
    (test_dir / "medium.txt").write_text("medium" * 1000)
    (test_dir / "large.txt").write_text("large" * 10000)

    # Create files with different extensions
    (test_dir / "file1.jpg").write_text("image" * 100)
    (test_dir / "file2.pdf").write_text("pdf" * 200)
    (test_dir / "file3.py").write_text("code" * 50)

    return test_dir


class TestFileSizeAnalyzer:
    """Test cases for FileSizeAnalyzer class."""

    def test_init_loads_config(self, temp_config_file):
        """Test that initialization loads configuration file."""
        analyzer = FileSizeAnalyzer(config_path=temp_config_file)
        assert analyzer.config is not None
        assert "analysis" in analyzer.config

    def test_init_raises_file_not_found(self):
        """Test that initialization raises error for missing config file."""
        with pytest.raises(FileNotFoundError):
            FileSizeAnalyzer(config_path="nonexistent.yaml")

    def test_format_size(self, temp_config_file):
        """Test file size formatting."""
        analyzer = FileSizeAnalyzer(config_path=temp_config_file)

        assert "B" in analyzer._format_size(500)
        assert "KB" in analyzer._format_size(5000)
        assert "MB" in analyzer._format_size(5000000)
        assert "GB" in analyzer._format_size(5000000000)

    def test_scan_directory(self, temp_config_file, temp_directory):
        """Test scanning directory."""
        analyzer = FileSizeAnalyzer(config_path=temp_config_file)
        files = analyzer.scan_directory(str(temp_directory), recursive=False)

        assert len(files) > 0
        assert analyzer.stats["total_files"] > 0
        assert analyzer.stats["total_size"] > 0

    def test_scan_directory_nonexistent(self, temp_config_file):
        """Test scanning nonexistent directory raises error."""
        analyzer = FileSizeAnalyzer(config_path=temp_config_file)
        with pytest.raises(FileNotFoundError):
            analyzer.scan_directory("/nonexistent/path")

    def test_get_largest_files(self, temp_config_file, temp_directory):
        """Test getting largest files."""
        analyzer = FileSizeAnalyzer(config_path=temp_config_file)
        analyzer.scan_directory(str(temp_directory))

        largest = analyzer.get_largest_files(5)
        assert len(largest) <= 5
        assert len(largest) > 0

        # Verify sorted by size (largest first)
        if len(largest) > 1:
            assert largest[0]["size"] >= largest[1]["size"]

    def test_get_size_distribution_by_type(self, temp_config_file, temp_directory):
        """Test getting size distribution by type."""
        analyzer = FileSizeAnalyzer(config_path=temp_config_file)
        analyzer.scan_directory(str(temp_directory))

        distribution = analyzer.get_size_distribution_by_type()

        assert isinstance(distribution, dict)
        assert len(distribution) > 0

        # Check structure
        for ext, data in distribution.items():
            assert "count" in data
            assert "total_size" in data
            assert "percentage_of_total_size" in data
            assert "percentage_of_total_files" in data
            assert "average_size" in data

    def test_generate_cleanup_recommendations(self, temp_config_file, temp_directory):
        """Test generating cleanup recommendations."""
        analyzer = FileSizeAnalyzer(config_path=temp_config_file)
        analyzer.scan_directory(str(temp_directory))

        recommendations = analyzer.generate_cleanup_recommendations()

        assert isinstance(recommendations, list)
        # Recommendations may be empty if thresholds not met

    def test_generate_report(self, temp_config_file, temp_directory, tmp_path):
        """Test generating report."""
        analyzer = FileSizeAnalyzer(config_path=temp_config_file)
        analyzer.scan_directory(str(temp_directory))

        report_file = tmp_path / "report.txt"
        report_content = analyzer.generate_report(str(report_file))

        assert len(report_content) > 0
        assert "File Size Analysis Report" in report_content
        assert report_file.exists()

    def test_is_excluded_by_directory(self, temp_config_file):
        """Test directory exclusion."""
        analyzer = FileSizeAnalyzer(config_path=temp_config_file)
        analyzer.config["analysis"]["exclude"]["directories"] = [".git"]

        excluded_file = Path("/path/.git/config")
        assert analyzer._is_excluded(excluded_file) is True

        normal_file = Path("/path/file.txt")
        assert analyzer._is_excluded(normal_file) is False

    def test_is_excluded_by_extension(self, temp_config_file):
        """Test extension exclusion."""
        analyzer = FileSizeAnalyzer(config_path=temp_config_file)
        analyzer.config["analysis"]["exclude"]["extensions"] = [".tmp"]

        excluded_file = Path("file.tmp")
        assert analyzer._is_excluded(excluded_file) is True

        normal_file = Path("file.txt")
        assert analyzer._is_excluded(normal_file) is False

    def test_get_statistics(self, temp_config_file):
        """Test getting statistics."""
        analyzer = FileSizeAnalyzer(config_path=temp_config_file)
        stats = analyzer.get_statistics()

        assert "total_files" in stats
        assert "total_size" in stats
        assert "directories_scanned" in stats
        assert "errors" in stats
