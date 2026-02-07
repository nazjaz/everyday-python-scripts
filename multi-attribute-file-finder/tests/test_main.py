"""Unit tests for Multi-Attribute File Finder application."""

import os
import shutil
import stat
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.main import AttributeMatcher, MultiAttributeFileFinder, load_config


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


class TestAttributeMatcher:
    """Test cases for AttributeMatcher class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return {
            "attributes": {},
            "combinations": [
                {
                    "name": "test_combination",
                    "size": {"min_bytes": 1024},
                    "age": {"modified": {"days_ago_max": 30}},
                }
            ],
        }

    @pytest.fixture
    def matcher(self, config):
        """Create an AttributeMatcher instance."""
        return AttributeMatcher(config)

    def test_init(self, config):
        """Test AttributeMatcher initialization."""
        matcher = AttributeMatcher(config)
        assert matcher.config == config

    def test_check_size(self, matcher, temp_dir):
        """Test size checking."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("x" * 2048)  # 2 KB file

        # Test min_bytes
        size_criteria = {"min_bytes": 1024}
        assert matcher.check_size(test_file, size_criteria) is True

        size_criteria = {"min_bytes": 5000}
        assert matcher.check_size(test_file, size_criteria) is False

        # Test categories
        size_criteria = {"categories": ["small"]}
        assert matcher.check_size(test_file, size_criteria) is True

    def test_check_age(self, matcher, temp_dir):
        """Test age checking."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        # Set old modification time
        old_time = (datetime.now() - timedelta(days=100)).timestamp()
        os.utime(test_file, (old_time, old_time))

        age_criteria = {"modified": {"days_ago_min": 90}}
        assert matcher.check_age(test_file, age_criteria) is True

        age_criteria = {"modified": {"days_ago_max": 30}}
        assert matcher.check_age(test_file, age_criteria) is False

    def test_check_type(self, matcher, temp_dir):
        """Test type checking."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        # Test extension
        type_criteria = {"extensions": [".txt"]}
        assert matcher.check_type(test_file, type_criteria) is True

        type_criteria = {"extensions": [".pdf"]}
        assert matcher.check_type(test_file, type_criteria) is False

        # Test categories
        type_criteria = {"categories": ["document"]}
        assert matcher.check_type(test_file, type_criteria) is True

    def test_check_type_executable(self, matcher, temp_dir):
        """Test executable type checking."""
        test_file = temp_dir / "test.sh"
        test_file.write_text("#!/bin/bash\necho test")

        # Make executable
        test_file.chmod(test_file.stat().st_mode | stat.S_IXUSR)

        type_criteria = {"executable": True}
        assert matcher.check_type(test_file, type_criteria) is True

        # Make non-executable
        test_file.chmod(test_file.stat().st_mode & ~stat.S_IXUSR)
        assert matcher.check_type(test_file, type_criteria) is False

    def test_check_filename(self, matcher, temp_dir):
        """Test filename checking."""
        test_file = temp_dir / "test_file.txt"
        test_file.write_text("content")

        # Test glob
        filename_criteria = {"glob": ["*.txt"]}
        assert matcher.check_filename(test_file, filename_criteria) is True

        # Test contains
        filename_criteria = {"contains": ["test"]}
        assert matcher.check_filename(test_file, filename_criteria) is True

    def test_match_combination(self, matcher, temp_dir):
        """Test matching a combination."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("x" * 2048)  # 2 KB file

        combination = {
            "size": {"min_bytes": 1024},
            "type": {"extensions": [".txt"]},
        }

        assert matcher.match_combination(test_file, combination) is True

        # Should fail if doesn't match all criteria
        combination = {
            "size": {"min_bytes": 10000},  # Too large
            "type": {"extensions": [".txt"]},
        }
        assert matcher.match_combination(test_file, combination) is False

    def test_match_file(self, matcher, temp_dir):
        """Test matching file against all combinations."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("x" * 2048)

        matching = matcher.match_file(test_file)
        assert isinstance(matching, list)


class TestMultiAttributeFileFinder:
    """Test cases for MultiAttributeFileFinder class."""

    @pytest.fixture
    def config(self, temp_dir):
        """Create a test configuration."""
        return {
            "search": {
                "directory": str(temp_dir),
                "exclude_directories": [".git"],
            },
            "combinations": [
                {
                    "name": "small_files",
                    "size": {"max_bytes": 1048576},
                }
            ],
            "output": {"format": "text"},
            "logging": {"level": "INFO", "file": str(temp_dir / "test.log")},
        }

    @pytest.fixture
    def finder(self, config):
        """Create a MultiAttributeFileFinder instance."""
        return MultiAttributeFileFinder(config)

    def test_init(self, config):
        """Test MultiAttributeFileFinder initialization."""
        finder = MultiAttributeFileFinder(config)
        assert finder.config == config

    def test_should_exclude_directory(self, finder):
        """Test directory exclusion logic."""
        excluded = Path("/some/.git")
        assert finder.should_exclude_directory(excluded) is True

        included = Path("/some/normal_dir")
        assert finder.should_exclude_directory(included) is False

    def test_find_files(self, finder, temp_dir):
        """Test finding files."""
        # Create test files
        file1 = temp_dir / "small.txt"
        file1.write_text("content")  # Small file

        file2 = temp_dir / "large.txt"
        file2.write_text("x" * 2000000)  # Large file

        results = finder.find_files(temp_dir)
        assert isinstance(results, dict)
        assert "small_files" in results or len(results) > 0

    def test_format_output_text(self, finder):
        """Test text output formatting."""
        results = {
            "test_combination": [
                {
                    "path": "/test/file.txt",
                    "name": "file.txt",
                    "size": 1024,
                    "modified": "2024-01-01T00:00:00",
                    "extension": ".txt",
                }
            ]
        }

        output = finder.format_output(results, format_type="text")
        assert "Multi-Attribute File Search Results" in output
        assert "file.txt" in output

    def test_format_output_json(self, finder):
        """Test JSON output formatting."""
        results = {
            "test_combination": [
                {
                    "path": "/test/file.txt",
                    "name": "file.txt",
                    "size": 1024,
                    "modified": "2024-01-01T00:00:00",
                    "extension": ".txt",
                }
            ]
        }

        output = finder.format_output(results, format_type="json")
        assert "file.txt" in output
        # Should be valid JSON
        import json
        data = json.loads(output)
        assert "test_combination" in data

    def test_format_output_csv(self, finder):
        """Test CSV output formatting."""
        results = {
            "test_combination": [
                {
                    "path": "/test/file.txt",
                    "name": "file.txt",
                    "size": 1024,
                    "modified": "2024-01-01T00:00:00",
                    "extension": ".txt",
                }
            ]
        }

        output = finder.format_output(results, format_type="csv")
        assert "file.txt" in output
        assert "Combination" in output  # Header


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
            "search:\n  directory: /test\ncombinations:\n  - name: test\n"
        )

        config = load_config(config_file)
        assert config["search"]["directory"] == "/test"

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
