"""Unit tests for date range file finder."""

import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import (
    DateRangeFileFinder,
    load_config,
    parse_date,
)


class TestParseDate:
    """Test date parsing functionality."""

    def test_parse_date_with_time(self):
        """Test parsing date with time component."""
        result = parse_date("2024-01-15 14:30:00")
        assert result == datetime(2024, 1, 15, 14, 30, 0)

    def test_parse_date_without_time(self):
        """Test parsing date without time component."""
        result = parse_date("2024-01-15")
        assert result == datetime(2024, 1, 15, 0, 0, 0)

    def test_parse_date_invalid_format(self):
        """Test that invalid date format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date("15-01-2024")

    def test_parse_date_invalid_date(self):
        """Test that invalid date value raises ValueError."""
        with pytest.raises(ValueError):
            parse_date("2024-02-30")


class TestLoadConfig:
    """Test configuration file loading."""

    def test_load_config_valid_yaml(self):
        """Test loading valid YAML configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "search_path": "/test/path",
                "recursive": False,
                "file_pattern": "*.txt",
            }
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            result = load_config(config_path)
            assert result["search_path"] == "/test/path"
            assert result["recursive"] is False
            assert result["file_pattern"] == "*.txt"
        finally:
            config_path.unlink()

    def test_load_config_file_not_found(self):
        """Test that missing config file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config(Path("/nonexistent/config.yaml"))

    def test_load_config_invalid_yaml(self):
        """Test that invalid YAML raises YAMLError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = Path(f.name)

        try:
            with pytest.raises(yaml.YAMLError):
                load_config(config_path)
        finally:
            config_path.unlink()

    def test_load_config_empty_file(self):
        """Test loading empty config file returns empty dict."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            config_path = Path(f.name)

        try:
            result = load_config(config_path)
            assert result == {}
        finally:
            config_path.unlink()


class TestDateRangeFileFinder:
    """Test DateRangeFileFinder class."""

    def test_init_valid_parameters(self):
        """Test initialization with valid parameters."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        search_path = Path(tempfile.mkdtemp())

        finder = DateRangeFileFinder(
            start_date=start_date,
            end_date=end_date,
            search_path=search_path,
        )

        assert finder.start_date == start_date
        assert finder.end_date == end_date
        assert finder.search_path == search_path
        assert finder.recursive is True

    def test_init_start_date_after_end_date(self):
        """Test that start date after end date raises ValueError."""
        start_date = datetime(2024, 1, 31)
        end_date = datetime(2024, 1, 1)
        search_path = Path(tempfile.mkdtemp())

        with pytest.raises(ValueError, match="Start date must be before"):
            DateRangeFileFinder(
                start_date=start_date,
                end_date=end_date,
                search_path=search_path,
            )

    def test_init_nonexistent_path(self):
        """Test that nonexistent path raises FileNotFoundError."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        search_path = Path("/nonexistent/path")

        with pytest.raises(FileNotFoundError):
            DateRangeFileFinder(
                start_date=start_date,
                end_date=end_date,
                search_path=search_path,
            )

    def test_init_file_not_directory(self):
        """Test that file path raises NotADirectoryError."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            file_path = Path(f.name)

        try:
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 1, 31)

            with pytest.raises(NotADirectoryError):
                DateRangeFileFinder(
                    start_date=start_date,
                    end_date=end_date,
                    search_path=file_path,
                )
        finally:
            file_path.unlink()

    def test_find_files_in_range(self):
        """Test finding files within date range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            search_path = Path(tmpdir)
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 1, 31)

            test_file = search_path / "test.txt"
            test_file.write_text("test content")

            finder = DateRangeFileFinder(
                start_date=start_date,
                end_date=end_date,
                search_path=search_path,
            )

            files = finder.find_files()
            assert len(files) == 1
            assert test_file in files

    def test_find_files_outside_range(self):
        """Test that files outside date range are not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            search_path = Path(tmpdir)
            start_date = datetime(2024, 2, 1)
            end_date = datetime(2024, 2, 28)

            test_file = search_path / "test.txt"
            test_file.write_text("test content")

            finder = DateRangeFileFinder(
                start_date=start_date,
                end_date=end_date,
                search_path=search_path,
            )

            files = finder.find_files()
            assert len(files) == 0

    def test_find_files_recursive(self):
        """Test recursive file finding."""
        with tempfile.TemporaryDirectory() as tmpdir:
            search_path = Path(tmpdir)
            subdir = search_path / "subdir"
            subdir.mkdir()

            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 1, 31)

            test_file = subdir / "test.txt"
            test_file.write_text("test content")

            finder = DateRangeFileFinder(
                start_date=start_date,
                end_date=end_date,
                search_path=search_path,
                recursive=True,
            )

            files = finder.find_files()
            assert len(files) == 1
            assert test_file in files

    def test_find_files_non_recursive(self):
        """Test non-recursive file finding."""
        with tempfile.TemporaryDirectory() as tmpdir:
            search_path = Path(tmpdir)
            subdir = search_path / "subdir"
            subdir.mkdir()

            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 1, 31)

            root_file = search_path / "root.txt"
            root_file.write_text("test content")

            sub_file = subdir / "sub.txt"
            sub_file.write_text("test content")

            finder = DateRangeFileFinder(
                start_date=start_date,
                end_date=end_date,
                search_path=search_path,
                recursive=False,
            )

            files = finder.find_files()
            assert len(files) == 1
            assert root_file in files
            assert sub_file not in files

    def test_find_files_with_pattern(self):
        """Test file finding with pattern filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            search_path = Path(tmpdir)
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 1, 31)

            txt_file = search_path / "test.txt"
            txt_file.write_text("test content")

            py_file = search_path / "test.py"
            py_file.write_text("test content")

            finder = DateRangeFileFinder(
                start_date=start_date,
                end_date=end_date,
                search_path=search_path,
                file_pattern="*.txt",
            )

            files = finder.find_files()
            assert len(files) == 1
            assert txt_file in files
            assert py_file not in files

    def test_find_files_permission_error(self):
        """Test handling of permission errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            search_path = Path(tmpdir)
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 1, 31)

            finder = DateRangeFileFinder(
                start_date=start_date,
                end_date=end_date,
                search_path=search_path,
            )

            with patch("src.main.Path.glob") as mock_glob:
                mock_file = Mock()
                mock_file.is_file.return_value = True
                mock_file.stat.side_effect = PermissionError("Access denied")
                mock_glob.return_value = [mock_file]

                files = finder.find_files()
                assert len(files) == 0

    def test_format_results_with_files(self):
        """Test formatting results with files found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            search_path = Path(tmpdir)
            start_date = datetime(2024, 1, 15, 10, 0, 0)
            end_date = datetime(2024, 1, 15, 12, 0, 0)

            test_file = search_path / "test.txt"
            test_file.write_text("test content")

            finder = DateRangeFileFinder(
                start_date=start_date,
                end_date=end_date,
                search_path=search_path,
            )

            files = finder.find_files()
            result = finder.format_results(files)

            assert "Found 1 file(s)" in result
            assert "Start:" in result
            assert "End:" in result
            assert str(test_file) in result

    def test_format_results_no_files(self):
        """Test formatting results when no files found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            search_path = Path(tmpdir)
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 1, 31)

            finder = DateRangeFileFinder(
                start_date=start_date,
                end_date=end_date,
                search_path=search_path,
            )

            result = finder.format_results([])
            assert "No files found" in result
