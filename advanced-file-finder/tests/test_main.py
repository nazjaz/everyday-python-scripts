"""Unit tests for Advanced File Finder application."""

import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.main import FileFinder, PatternMatcher, load_config


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


class TestPatternMatcher:
    """Test cases for PatternMatcher class."""

    @pytest.fixture
    def patterns(self):
        """Create test patterns."""
        return {
            "size": {},
            "date": {},
            "type": {},
            "filename": {},
            "content": {},
            "logic_operator": "AND",
        }

    @pytest.fixture
    def matcher(self, patterns):
        """Create a PatternMatcher instance."""
        return PatternMatcher(patterns)

    def test_init(self, patterns):
        """Test PatternMatcher initialization."""
        matcher = PatternMatcher(patterns)
        assert matcher.patterns == patterns
        assert matcher.logic_operator == "AND"

    def test_match_size(self, matcher, temp_dir):
        """Test size pattern matching."""
        # Test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        file_size = test_file.stat().st_size

        # No size pattern - should match
        assert matcher.match_size(test_file) is True

        # Min size pattern
        matcher.size_patterns = {"min_bytes": file_size - 1}
        assert matcher.match_size(test_file) is True

        matcher.size_patterns = {"min_bytes": file_size + 1}
        assert matcher.match_size(test_file) is False

        # Max size pattern
        matcher.size_patterns = {"max_bytes": file_size + 1}
        assert matcher.match_size(test_file) is True

        matcher.size_patterns = {"max_bytes": file_size - 1}
        assert matcher.match_size(test_file) is False

    def test_match_date(self, matcher, temp_dir):
        """Test date pattern matching."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        # No date pattern - should match
        assert matcher.match_date(test_file) is True

        # Days ago pattern
        matcher.date_patterns = {
            "modified": {"days_ago": 365}
        }
        # File is recent, so should match
        assert matcher.match_date(test_file) is True

    def test_parse_date_spec(self, matcher):
        """Test date specification parsing."""
        now = datetime.now()

        # ISO format
        date1 = matcher._parse_date_spec("2024-01-01", now)
        assert isinstance(date1, datetime)

        # Relative format
        date2 = matcher._parse_date_spec("30 days ago", now)
        assert isinstance(date2, datetime)
        assert date2 < now

    def test_match_type(self, matcher, temp_dir):
        """Test type pattern matching."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        # No type pattern - should match
        assert matcher.match_type(test_file) is True

        # Extension pattern
        matcher.type_patterns = {"extensions": [".txt"]}
        assert matcher.match_type(test_file) is True

        matcher.type_patterns = {"extensions": [".pdf"]}
        assert matcher.match_type(test_file) is False

        # Category pattern
        matcher.type_patterns = {"categories": ["document"]}
        assert matcher.match_type(test_file) is True

    def test_match_filename(self, matcher, temp_dir):
        """Test filename pattern matching."""
        test_file = temp_dir / "test_file.txt"
        test_file.write_text("test content")

        # No filename pattern - should match
        assert matcher.match_filename(test_file) is True

        # Glob pattern
        matcher.filename_patterns = {"glob": ["*.txt"]}
        assert matcher.match_filename(test_file) is True

        matcher.filename_patterns = {"glob": ["*.pdf"]}
        assert matcher.match_filename(test_file) is False

        # Contains pattern
        matcher.filename_patterns = {"contains": ["test"]}
        assert matcher.match_filename(test_file) is True

    def test_match_content(self, matcher, temp_dir):
        """Test content pattern matching."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("This is test content with TODO item")

        # No content pattern - should match
        assert matcher.match_content(test_file) is True

        # Text pattern
        matcher.content_patterns = {"text": ["TODO"]}
        assert matcher.match_content(test_file) is True

        matcher.content_patterns = {"text": ["NOTFOUND"]}
        assert matcher.match_content(test_file) is False

    def test_match_file(self, matcher, temp_dir):
        """Test complete file matching."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        # No patterns - should match
        assert matcher.match_file(test_file) is True

        # Size pattern
        matcher.size_patterns = {"min_bytes": 0}
        assert matcher.match_file(test_file) is True

        # Multiple patterns with AND
        matcher.size_patterns = {"min_bytes": 0}
        matcher.type_patterns = {"extensions": [".txt"]}
        matcher.logic_operator = "AND"
        assert matcher.match_file(test_file) is True

        # Multiple patterns with OR
        matcher.type_patterns = {"extensions": [".pdf"]}
        matcher.logic_operator = "OR"
        assert matcher.match_file(test_file) is True  # Size matches


class TestFileFinder:
    """Test cases for FileFinder class."""

    @pytest.fixture
    def config(self, temp_dir):
        """Create a test configuration."""
        search_dir = temp_dir / "search"
        search_dir.mkdir()

        return {
            "search": {
                "directory": str(search_dir),
                "exclude_directories": [".git"],
            },
            "patterns": {
                "logic_operator": "AND",
                "size": {},
                "date": {},
                "type": {},
                "filename": {},
                "content": {},
            },
            "output": {"format": "text"},
            "logging": {"level": "INFO", "file": str(temp_dir / "test.log")},
        }

    @pytest.fixture
    def finder(self, config):
        """Create a FileFinder instance."""
        return FileFinder(config)

    def test_init(self, config):
        """Test FileFinder initialization."""
        finder = FileFinder(config)
        assert finder.config == config

    def test_should_exclude_directory(self, finder):
        """Test directory exclusion logic."""
        excluded = Path("/some/.git")
        assert finder.should_exclude_directory(excluded) is True

        included = Path("/some/normal_dir")
        assert finder.should_exclude_directory(included) is False

    def test_find_files(self, finder, temp_dir):
        """Test finding files."""
        search_dir = Path(finder.search_config["directory"])
        search_dir.mkdir(parents=True, exist_ok=True)

        # Create test files
        file1 = search_dir / "file1.txt"
        file1.write_text("content 1")
        file2 = search_dir / "file2.txt"
        file2.write_text("content 2")

        matches = finder.find_files(search_dir)
        assert len(matches) >= 2

    def test_find_files_with_patterns(self, finder, temp_dir):
        """Test finding files with patterns."""
        search_dir = Path(finder.search_config["directory"])
        search_dir.mkdir(parents=True, exist_ok=True)

        # Create test files
        file1 = search_dir / "test1.txt"
        file1.write_text("content")
        file2 = search_dir / "other.pdf"
        file2.write_text("content")

        # Set pattern to match only .txt files
        finder.matcher.type_patterns = {"extensions": [".txt"]}

        matches = finder.find_files(search_dir)
        assert len(matches) >= 1
        assert all(m["extension"] == ".txt" for m in matches)

    def test_format_output_text(self, finder):
        """Test text output formatting."""
        matches = [
            {
                "path": "/test/file.txt",
                "name": "file.txt",
                "size": 1024,
                "modified": "2024-01-01T00:00:00",
                "extension": ".txt",
            }
        ]

        output = finder.format_output(matches, format_type="text")
        assert "File Search Results" in output
        assert "file.txt" in output

    def test_format_output_json(self, finder):
        """Test JSON output formatting."""
        matches = [
            {
                "path": "/test/file.txt",
                "name": "file.txt",
                "size": 1024,
                "modified": "2024-01-01T00:00:00",
                "extension": ".txt",
            }
        ]

        output = finder.format_output(matches, format_type="json")
        assert "file.txt" in output
        # Should be valid JSON
        import json
        data = json.loads(output)
        assert len(data) == 1

    def test_format_output_csv(self, finder):
        """Test CSV output formatting."""
        matches = [
            {
                "path": "/test/file.txt",
                "name": "file.txt",
                "size": 1024,
                "modified": "2024-01-01T00:00:00",
                "extension": ".txt",
            }
        ]

        output = finder.format_output(matches, format_type="csv")
        assert "file.txt" in output
        assert "path" in output  # Header

    def test_format_size(self, finder):
        """Test size formatting."""
        assert "B" in finder._format_size(100)
        assert "KB" in finder._format_size(1024)
        assert "MB" in finder._format_size(1024 * 1024)


class TestLoadConfig:
    """Test cases for load_config function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    def test_load_config_valid(self, temp_dir):
        """Test loading a valid configuration file."""
        config_file = temp_dir / "config.yaml"
        config_file.write_text(
            "search:\n  directory: /test\npatterns:\n  logic_operator: AND\n"
        )

        config = load_config(config_file)
        assert config["search"]["directory"] == "/test"
        assert config["patterns"]["logic_operator"] == "AND"

    def test_load_config_nonexistent(self):
        """Test loading a nonexistent configuration file."""
        nonexistent = Path("/nonexistent/config.yaml")
        with pytest.raises(FileNotFoundError):
            load_config(nonexistent)

    def test_load_config_invalid_yaml(self, temp_dir):
        """Test loading an invalid YAML file."""
        config_file = temp_dir / "config.yaml"
        config_file.write_text("invalid: yaml: content: [unclosed")

        with pytest.raises(Exception):  # yaml.YAMLError
            load_config(config_file)
