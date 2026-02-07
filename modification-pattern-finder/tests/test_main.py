"""Unit tests for modification pattern finder."""

import os
import tempfile
from datetime import datetime, time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import (
    ModificationPatternFinder,
    load_config,
    parse_days_of_week,
    parse_time,
)


class TestLoadConfig:
    """Test configuration file loading."""

    def test_load_config_valid_yaml(self):
        """Test loading valid YAML configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "time_start": "09:00",
                "time_end": "17:00",
                "days_of_week": ["monday", "friday"],
                "file_patterns": [".py", ".txt"],
                "recursive": True,
            }
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            result = load_config(config_path)
            assert result["time_start"] == "09:00"
            assert result["time_end"] == "17:00"
            assert result["days_of_week"] == ["monday", "friday"]
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


class TestParseTime:
    """Test time parsing."""

    def test_parse_time_hh_mm(self):
        """Test parsing time in HH:MM format."""
        result = parse_time("09:30")
        assert result == time(9, 30)

    def test_parse_time_hh_mm_ss(self):
        """Test parsing time in HH:MM:SS format."""
        result = parse_time("09:30:45")
        assert result == time(9, 30, 45)

    def test_parse_time_invalid_format(self):
        """Test that invalid time format raises ValueError."""
        with pytest.raises(ValueError):
            parse_time("invalid")

    def test_parse_time_invalid_values(self):
        """Test that invalid time values raise ValueError."""
        with pytest.raises(ValueError):
            parse_time("25:00")


class TestParseDaysOfWeek:
    """Test day of week parsing."""

    def test_parse_days_full_names(self):
        """Test parsing full day names."""
        result = parse_days_of_week(["monday", "friday"])
        assert 0 in result
        assert 4 in result

    def test_parse_days_abbreviations(self):
        """Test parsing day abbreviations."""
        result = parse_days_of_week(["mon", "fri"])
        assert 0 in result
        assert 4 in result

    def test_parse_days_case_insensitive(self):
        """Test that day parsing is case insensitive."""
        result1 = parse_days_of_week(["MONDAY"])
        result2 = parse_days_of_week(["monday"])
        assert result1 == result2

    def test_parse_days_invalid(self):
        """Test that invalid day name raises ValueError."""
        with pytest.raises(ValueError):
            parse_days_of_week(["invalidday"])


class TestModificationPatternFinder:
    """Test ModificationPatternFinder class."""

    def test_init(self):
        """Test initialization."""
        finder = ModificationPatternFinder()
        assert finder.time_start is None
        assert finder.time_end is None
        assert finder.days_of_week is None

    def test_init_with_time(self):
        """Test initialization with time filters."""
        time_start = time(9, 0)
        time_end = time(17, 0)
        finder = ModificationPatternFinder(time_start=time_start, time_end=time_end)

        assert finder.time_start == time_start
        assert finder.time_end == time_end

    def test_init_time_start_after_end(self):
        """Test that time_start after time_end raises ValueError."""
        with pytest.raises(ValueError, match="time_start must be before"):
            ModificationPatternFinder(
                time_start=time(17, 0), time_end=time(9, 0)
            )

    def test_matches_time_pattern_no_filter(self):
        """Test time pattern matching with no filter."""
        finder = ModificationPatternFinder()
        assert finder._matches_time_pattern(time(12, 0)) is True

    def test_matches_time_pattern_with_range(self):
        """Test time pattern matching with time range."""
        finder = ModificationPatternFinder(
            time_start=time(9, 0), time_end=time(17, 0)
        )

        assert finder._matches_time_pattern(time(12, 0)) is True
        assert finder._matches_time_pattern(time(8, 0)) is False
        assert finder._matches_time_pattern(time(18, 0)) is False

    def test_matches_time_pattern_overnight(self):
        """Test time pattern matching with overnight range."""
        finder = ModificationPatternFinder(
            time_start=time(22, 0), time_end=time(6, 0)
        )

        assert finder._matches_time_pattern(time(23, 0)) is True
        assert finder._matches_time_pattern(time(2, 0)) is True
        assert finder._matches_time_pattern(time(12, 0)) is False

    def test_matches_day_pattern_no_filter(self):
        """Test day pattern matching with no filter."""
        finder = ModificationPatternFinder()
        test_datetime = datetime(2024, 1, 15, 12, 0)

        assert finder._matches_day_pattern(test_datetime) is True

    def test_matches_day_pattern_with_filter(self):
        """Test day pattern matching with day filter."""
        finder = ModificationPatternFinder(days_of_week={0, 4})
        monday = datetime(2024, 1, 15, 12, 0)
        tuesday = datetime(2024, 1, 16, 12, 0)

        assert finder._matches_day_pattern(monday) is True
        assert finder._matches_day_pattern(tuesday) is False

    def test_matches_file_pattern_no_filter(self):
        """Test file pattern matching with no filter."""
        finder = ModificationPatternFinder()
        file_path = Path("test.txt")

        assert finder._matches_file_pattern(file_path) is True

    def test_matches_file_pattern_with_extension(self):
        """Test file pattern matching with extension filter."""
        finder = ModificationPatternFinder(file_patterns=[".py", ".txt"])
        py_file = Path("test.py")
        txt_file = Path("test.txt")
        js_file = Path("test.js")

        assert finder._matches_file_pattern(py_file) is True
        assert finder._matches_file_pattern(txt_file) is True
        assert finder._matches_file_pattern(js_file) is False

    def test_find_files(self):
        """Test finding files matching patterns."""
        finder = ModificationPatternFinder()

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            file1 = dir_path / "file1.txt"
            file1.write_text("content")

            matching_files = finder.find_files([dir_path])

            assert isinstance(matching_files, list)
            assert len(matching_files) >= 1

    def test_find_files_with_time_filter(self):
        """Test finding files with time filter."""
        current_time = datetime.now().time()
        time_start = time(current_time.hour - 1, current_time.minute)
        time_end = time(current_time.hour + 1, current_time.minute)

        finder = ModificationPatternFinder(time_start=time_start, time_end=time_end)

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            file1 = dir_path / "file1.txt"
            file1.write_text("content")

            matching_files = finder.find_files([dir_path])

            assert isinstance(matching_files, list)

    def test_find_files_recursive(self):
        """Test recursive file finding."""
        finder = ModificationPatternFinder()

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            subdir = dir_path / "subdir"
            subdir.mkdir()
            file1 = dir_path / "file1.txt"
            file1.write_text("content")
            file2 = subdir / "file2.txt"
            file2.write_text("content")

            matching_files = finder.find_files([dir_path], recursive=True)

            assert len(matching_files) >= 2

    def test_format_report(self):
        """Test report formatting."""
        finder = ModificationPatternFinder()

        matching_files = [
            {
                "path": "/path/to/file1.txt",
                "name": "file1.txt",
                "size": 1000,
                "modified_datetime": "2024-01-15T12:00:00",
                "modified_date": "2024-01-15",
                "modified_time": "12:00:00",
                "day_of_week": "Monday",
                "day_of_week_number": 0,
            }
        ]

        report = finder.format_report(matching_files)

        assert "Modification Pattern Analysis Report" in report
        assert "/path/to/file1.txt" in report
        assert "file1.txt" in report

    def test_format_report_empty(self):
        """Test report formatting with no matches."""
        finder = ModificationPatternFinder()
        report = finder.format_report([])

        assert "No files found" in report
