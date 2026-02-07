"""Unit tests for file usage analytics module."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.main import FileUsageAnalytics


class TestFileUsageAnalytics:
    """Test cases for FileUsageAnalytics class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def config_file(self, temp_dir):
        """Create temporary config file."""
        config = {
            "scan": {"skip_patterns": [".git"]},
            "visualizations": {"output_dir": "charts"},
            "report": {"output_file": "report.txt"},
            "logging": {"level": "INFO", "file": "logs/app.log"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return str(config_path)

    @pytest.fixture
    def analytics(self, config_file):
        """Create FileUsageAnalytics instance."""
        return FileUsageAnalytics(config_path=config_file)

    def test_load_config_success(self, temp_dir):
        """Test successful configuration loading."""
        config = {
            "scan": {"skip_patterns": []},
            "logging": {"level": "INFO"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        analytics = FileUsageAnalytics(config_path=str(config_path))
        assert analytics.config["scan"]["skip_patterns"] == []

    def test_load_config_file_not_found(self):
        """Test FileNotFoundError when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            FileUsageAnalytics(config_path="nonexistent.yaml")

    def test_load_config_invalid_yaml(self, temp_dir):
        """Test YAMLError when config file is invalid."""
        config_path = temp_dir / "invalid.yaml"
        with open(config_path, "w") as f:
            f.write("invalid: yaml: content: [unclosed")

        import yaml

        with pytest.raises(yaml.YAMLError):
            FileUsageAnalytics(config_path=str(config_path))

    def test_should_skip_path(self, analytics):
        """Test path skipping logic."""
        path = Path("/some/path/.git/config")
        assert analytics._should_skip_path(path) is True

        path = Path("/some/path/normal_file.txt")
        assert analytics._should_skip_path(path) is False

    def test_collect_file_metadata(self, analytics, temp_dir):
        """Test file metadata collection."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        metadata = analytics._collect_file_metadata(test_file)

        assert metadata is not None
        assert metadata["path"] == str(test_file)
        assert metadata["size"] > 0
        assert "modified" in metadata
        assert "accessed" in metadata
        assert "extension" in metadata

    def test_collect_file_metadata_nonexistent(self, analytics):
        """Test metadata collection for nonexistent file."""
        nonexistent = Path("/nonexistent/file.txt")
        metadata = analytics._collect_file_metadata(nonexistent)
        assert metadata is None

    def test_analyze_directory(self, analytics, temp_dir):
        """Test directory analysis."""
        # Create test files
        (temp_dir / "file1.txt").write_text("content 1")
        (temp_dir / "file2.pdf").write_text("content 2")
        (temp_dir / "subdir").mkdir()
        (temp_dir / "subdir" / "file3.doc").write_text("content 3")

        analytics.analyze_directory(str(temp_dir))

        assert analytics.stats["files_analyzed"] == 3
        assert analytics.stats["directories_scanned"] > 0
        assert len(analytics.analytics_data["files"]) == 3

    def test_analyze_directory_not_found(self, analytics):
        """Test FileNotFoundError when directory doesn't exist."""
        with pytest.raises(FileNotFoundError):
            analytics.analyze_directory("/nonexistent/path")

    def test_analyze_directory_not_a_directory(self, analytics, temp_dir):
        """Test ValueError when path is not a directory."""
        test_file = temp_dir / "file.txt"
        test_file.write_text("content")

        with pytest.raises(ValueError, match="not a directory"):
            analytics.analyze_directory(str(test_file))

    def test_generate_visualizations_no_data(self, analytics):
        """Test ValueError when no analytics data available."""
        with pytest.raises(ValueError, match="No analytics data available"):
            analytics.generate_visualizations()

    def test_generate_visualizations(self, analytics, temp_dir):
        """Test visualization generation."""
        # Create test files
        (temp_dir / "file1.txt").write_text("content 1")
        (temp_dir / "file2.pdf").write_text("content 2")

        analytics.analyze_directory(str(temp_dir))

        output_dir = temp_dir / "charts"
        charts = analytics.generate_visualizations(output_dir=str(output_dir))

        assert len(charts) == 5
        assert "access_patterns" in charts
        assert "modification_trends" in charts
        assert "storage_growth" in charts
        assert "extension_distribution" in charts
        assert "size_distribution" in charts

        # Verify files were created
        for chart_path in charts.values():
            assert chart_path.exists()

    def test_generate_report_no_data(self, analytics):
        """Test ValueError when no analytics data available."""
        with pytest.raises(ValueError, match="No analytics data available"):
            analytics.generate_report()

    def test_generate_report(self, analytics, temp_dir):
        """Test report generation."""
        # Create test files
        (temp_dir / "file1.txt").write_text("content 1")
        (temp_dir / "file2.pdf").write_text("content 2")

        analytics.analyze_directory(str(temp_dir))

        report_path = temp_dir / "report.txt"
        report_content = analytics.generate_report(output_path=str(report_path))

        assert report_path.exists()
        assert "FILE USAGE ANALYTICS REPORT" in report_content
        assert "Files analyzed" in report_content

    def test_analytics_data_structure(self, analytics, temp_dir):
        """Test that analytics data has correct structure."""
        (temp_dir / "test.txt").write_text("test content")

        analytics.analyze_directory(str(temp_dir))

        assert "files" in analytics.analytics_data
        assert "access_patterns" in analytics.analytics_data
        assert "modification_trends" in analytics.analytics_data
        assert "storage_growth" in analytics.analytics_data
        assert "extension_distribution" in analytics.analytics_data
        assert "size_distribution" in analytics.analytics_data
