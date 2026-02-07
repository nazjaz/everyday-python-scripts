"""Unit tests for file size finder."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.main import FileSizeFinder


@pytest.fixture
def temp_config_file():
    """Create temporary config file for testing."""
    config_content = """
search:
  directory: "."

size:
  min_bytes: 0
  max_bytes: null

skip:
  patterns: []
  directories: []
  excluded_paths: []

include:
  extensions: []
  include_no_extension: true

report:
  auto_save: false
  output_file: "logs/test_report.txt"
  sort_by_size: true

logging:
  level: "DEBUG"
  file: "logs/test.log"
  max_bytes: 10485760
  backup_count: 5
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        f.write(config_content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def temp_directory():
    """Create temporary directory with test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files with different sizes
        (temp_path / "small.txt").write_text("small")
        (temp_path / "medium.txt").write_text("x" * 1000)
        (temp_path / "large.txt").write_text("x" * 10000)

        # Create subdirectory
        subdir = temp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("x" * 5000)

        yield temp_path


@pytest.fixture
def finder(temp_config_file):
    """Create FileSizeFinder instance for testing."""
    finder = FileSizeFinder(config_path=temp_config_file)
    yield finder


class TestFileSizeFinder:
    """Test cases for FileSizeFinder class."""

    def test_init_loads_config(self, finder):
        """Test that finder loads configuration correctly."""
        assert finder.config is not None
        assert "search" in finder.config
        assert "size" in finder.config

    def test_parse_size_bytes(self, finder):
        """Test parsing size in bytes."""
        assert finder._parse_size("1024") == 1024
        assert finder._parse_size("1024B") == 1024

    def test_parse_size_kb(self, finder):
        """Test parsing size in kilobytes."""
        assert finder._parse_size("1KB") == 1024
        assert finder._parse_size("2KB") == 2048
        assert finder._parse_size("1.5KB") == 1536

    def test_parse_size_mb(self, finder):
        """Test parsing size in megabytes."""
        assert finder._parse_size("1MB") == 1024 ** 2
        assert finder._parse_size("10MB") == 10 * 1024 ** 2

    def test_parse_size_gb(self, finder):
        """Test parsing size in gigabytes."""
        assert finder._parse_size("1GB") == 1024 ** 3

    def test_parse_size_invalid(self, finder):
        """Test parsing invalid size format."""
        with pytest.raises(ValueError):
            finder._parse_size("invalid")

        with pytest.raises(ValueError):
            finder._parse_size("10XX")

    def test_format_size(self, finder):
        """Test formatting size to human-readable string."""
        assert finder._format_size(1024) == "1.00 KB"
        assert finder._format_size(1024 ** 2) == "1.00 MB"
        assert finder._format_size(1024 ** 3) == "1.00 GB"

    def test_matches_size_criteria_min_only(self, finder):
        """Test size matching with minimum only."""
        finder.config["size"]["min_bytes"] = 1000
        finder.config["size"]["max_bytes"] = None

        assert finder._matches_size_criteria(1500) is True
        assert finder._matches_size_criteria(500) is False

    def test_matches_size_criteria_max_only(self, finder):
        """Test size matching with maximum only."""
        finder.config["size"]["min_bytes"] = 0
        finder.config["size"]["max_bytes"] = 1000

        assert finder._matches_size_criteria(500) is True
        assert finder._matches_size_criteria(1500) is False

    def test_matches_size_criteria_range(self, finder):
        """Test size matching with both min and max."""
        finder.config["size"]["min_bytes"] = 1000
        finder.config["size"]["max_bytes"] = 5000

        assert finder._matches_size_criteria(2500) is True
        assert finder._matches_size_criteria(500) is False
        assert finder._matches_size_criteria(6000) is False

    def test_should_skip_path_pattern(self, finder):
        """Test skip pattern matching."""
        finder.config["skip"]["patterns"] = [".git", "node_modules"]

        assert finder._should_skip_path(Path("/path/to/.git/config")) is True
        assert finder._should_skip_path(Path("/path/to/node_modules/package")) is True
        assert finder._should_skip_path(Path("/path/to/normal/file.txt")) is False

    def test_should_skip_path_directory(self, finder):
        """Test skip directory matching."""
        finder.config["skip"]["directories"] = [".git"]

        assert finder._should_skip_path(Path("/path/.git/file")) is True
        assert finder._should_skip_path(Path("/path/normal/file.txt")) is False

    def test_should_include_extension_all(self, finder):
        """Test extension filtering with all extensions."""
        finder.config["include"]["extensions"] = []

        assert finder._should_include_extension(Path("file.txt")) is True
        assert finder._should_include_extension(Path("file.pdf")) is True

    def test_should_include_extension_filtered(self, finder):
        """Test extension filtering with specific extensions."""
        finder.config["include"]["extensions"] = [".txt", ".pdf"]

        assert finder._should_include_extension(Path("file.txt")) is True
        assert finder._should_include_extension(Path("file.pdf")) is True
        assert finder._should_include_extension(Path("file.jpg")) is False

    def test_should_include_extension_no_extension(self, finder):
        """Test extension filtering for files without extensions."""
        finder.config["include"]["extensions"] = [".txt"]
        finder.config["include"]["include_no_extension"] = True

        assert finder._should_include_extension(Path("file")) is True

        finder.config["include"]["include_no_extension"] = False
        assert finder._should_include_extension(Path("file")) is False

    def test_find_files(self, finder, temp_directory):
        """Test finding files in directory."""
        finder.config["size"]["min_bytes"] = 0
        finder.config["size"]["max_bytes"] = None

        files = finder.find_files(directory=str(temp_directory))

        assert len(files) >= 4
        assert finder.results["files_found"] >= 4
        assert finder.results["directories_scanned"] >= 1

    def test_find_files_with_min_size(self, finder, temp_directory):
        """Test finding files with minimum size filter."""
        finder.config["size"]["min_bytes"] = 5000
        finder.config["size"]["max_bytes"] = None

        files = finder.find_files(directory=str(temp_directory))

        # Should find large.txt and nested.txt
        file_names = [f["name"] for f in files]
        assert "large.txt" in file_names or "nested.txt" in file_names

    def test_find_files_with_max_size(self, finder, temp_directory):
        """Test finding files with maximum size filter."""
        finder.config["size"]["min_bytes"] = 0
        finder.config["size"]["max_bytes"] = 100

        files = finder.find_files(directory=str(temp_directory))

        # Should find small.txt
        file_names = [f["name"] for f in files]
        assert "small.txt" in file_names

    def test_find_files_nonexistent_directory(self, finder):
        """Test finding files in nonexistent directory."""
        with pytest.raises(FileNotFoundError):
            finder.find_files(directory="/nonexistent/path")

    def test_generate_report(self, finder, temp_directory):
        """Test report generation."""
        finder.config["size"]["min_bytes"] = 0
        files = finder.find_files(directory=str(temp_directory))

        report = finder.generate_report(files)

        assert "FILE SIZE FINDER REPORT" in report
        assert "STATISTICS" in report
        assert "FILES FOUND" in report

    def test_generate_report_save_file(self, finder, temp_directory):
        """Test saving report to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = str(Path(temp_dir) / "test_report.txt")
            finder.config["size"]["min_bytes"] = 0
            files = finder.find_files(directory=str(temp_directory))

            report = finder.generate_report(files, output_file=report_file)

            assert Path(report_file).exists()
            assert report is not None

    def test_print_summary(self, finder, temp_directory, capsys):
        """Test printing summary to console."""
        finder.config["size"]["min_bytes"] = 0
        files = finder.find_files(directory=str(temp_directory))

        finder.print_summary(files)
        captured = capsys.readouterr()

        assert "FILE SIZE FINDER SUMMARY" in captured.out
        assert "Files found" in captured.out


class TestMainFunction:
    """Test cases for main function."""

    @patch("src.main.FileSizeFinder")
    def test_main_basic(self, mock_finder_class, temp_config_file):
        """Test main function with basic arguments."""
        mock_finder = MagicMock()
        mock_finder.find_files.return_value = []
        mock_finder.config = {"report": {"auto_save": False}}
        mock_finder_class.return_value = mock_finder

        from src.main import main
        import sys

        sys.argv = ["main.py", "-c", temp_config_file]
        result = main()

        assert result == 0
        mock_finder.find_files.assert_called_once()

    @patch("src.main.FileSizeFinder")
    def test_main_with_directory(self, mock_finder_class, temp_config_file):
        """Test main function with directory argument."""
        mock_finder = MagicMock()
        mock_finder.find_files.return_value = []
        mock_finder.config = {"report": {"auto_save": False}}
        mock_finder_class.return_value = mock_finder

        from src.main import main
        import sys

        sys.argv = ["main.py", "-c", temp_config_file, "-d", "/test/dir"]
        result = main()

        assert result == 0
        mock_finder.find_files.assert_called_with(directory="/test/dir")
