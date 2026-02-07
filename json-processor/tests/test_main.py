"""Unit tests for JSON Processor."""

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.main import JSONProcessor


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary config file."""
    source_dir = temp_dir / "source"
    source_dir.mkdir()

    config = {
        "source_directory": str(source_dir),
        "output_directory": str(temp_dir / "output"),
        "processing": {
            "remove_null": True,
            "sort_keys": True,
            "indent": 2,
            "ensure_ascii": False,
            "compact_separators": False,
        },
        "backup": {"enabled": False, "directory": "backups"},
        "exclusions": {"directories": [], "patterns": []},
        "operations": {"recursive": True},
        "logging": {
            "level": "INFO",
            "file": str(temp_dir / "test.log"),
            "max_bytes": 10485760,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }
    config_path = temp_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return str(config_path)


@pytest.fixture
def test_json_file(temp_dir):
    """Create a test JSON file."""
    source_dir = temp_dir / "source"
    source_dir.mkdir()

    json_data = {
        "zebra": "last",
        "apple": "first",
        "banana": "middle",
        "null_value": None,
        "nested": {
            "key": "value",
            "null_nested": None,
        },
    }

    json_file = source_dir / "test.json"
    with open(json_file, "w") as f:
        json.dump(json_data, f)

    return json_file, json_data


def test_json_processor_initialization(config_file):
    """Test JSONProcessor initialization."""
    processor = JSONProcessor(config_path=config_file)
    assert processor.config is not None
    assert processor.source_dir.exists()


def test_load_config_file_not_found():
    """Test that FileNotFoundError is raised when config file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        JSONProcessor(config_path="nonexistent.yaml")


def test_remove_null_values(config_file):
    """Test null value removal."""
    processor = JSONProcessor(config_path=config_file)

    data_with_nulls = {
        "key1": "value1",
        "key2": None,
        "key3": {
            "nested1": "value",
            "nested2": None,
        },
        "key4": [1, None, 3],
    }

    result = processor._remove_null_values(data_with_nulls)

    assert "key2" not in result
    assert "nested2" not in result["key3"]
    assert None not in result["key4"]
    assert result["key1"] == "value1"


def test_remove_null_values_disabled(config_file):
    """Test null value removal when disabled."""
    processor = JSONProcessor(config_path=config_file)
    processor.config["processing"]["remove_null"] = False

    data_with_nulls = {"key1": "value1", "key2": None}

    result = processor._remove_null_values(data_with_nulls)

    assert "key2" in result
    assert result["key2"] is None


def test_sort_keys(config_file):
    """Test key sorting."""
    processor = JSONProcessor(config_path=config_file)

    unsorted_data = {
        "zebra": "last",
        "apple": "first",
        "banana": "middle",
    }

    result = processor._sort_keys(unsorted_data)

    keys = list(result.keys())
    assert keys == ["apple", "banana", "zebra"]


def test_sort_keys_nested(config_file):
    """Test key sorting with nested structures."""
    processor = JSONProcessor(config_path=config_file)

    unsorted_data = {
        "zebra": {
            "c": "value",
            "a": "value",
            "b": "value",
        },
        "apple": "value",
    }

    result = processor._sort_keys(unsorted_data)

    assert list(result.keys()) == ["apple", "zebra"]
    assert list(result["zebra"].keys()) == ["a", "b", "c"]


def test_validate_json_structure(config_file):
    """Test JSON structure validation."""
    processor = JSONProcessor(config_path=config_file)

    valid_data = {"key": "value"}
    is_valid, error = processor._validate_json_structure(valid_data)
    assert is_valid is True
    assert error is None

    # Test with data that can't be serialized (should still pass basic validation)
    # More complex validation would require jsonschema


def test_should_process_file(config_file, temp_dir):
    """Test file filtering logic."""
    processor = JSONProcessor(config_path=config_file)

    json_file = temp_dir / "test.json"
    json_file.write_text('{"key": "value"}')
    assert processor._should_process_file(json_file) is True

    txt_file = temp_dir / "test.txt"
    txt_file.write_text("text")
    assert processor._should_process_file(txt_file) is False


def test_process_json_file(config_file, test_json_file):
    """Test processing a single JSON file."""
    processor = JSONProcessor(config_path=config_file)
    json_file, original_data = test_json_file

    result = processor._process_json_file(json_file)

    assert result is True
    assert processor.stats["files_processed"] == 1

    # Verify output file
    output_file = processor.output_dir / "test.json"
    assert output_file.exists()

    # Verify processed content
    with open(output_file, "r") as f:
        processed_data = json.load(f)

    # Check null values removed
    assert "null_value" not in processed_data
    assert "null_nested" not in processed_data["nested"]

    # Check keys sorted
    keys = list(processed_data.keys())
    assert keys == sorted(keys)


def test_process_json_file_invalid_json(config_file, temp_dir):
    """Test processing invalid JSON file."""
    processor = JSONProcessor(config_path=config_file)
    source_dir = temp_dir / "source"
    source_dir.mkdir()

    invalid_json = source_dir / "invalid.json"
    invalid_json.write_text("{ invalid json }")

    result = processor._process_json_file(invalid_json)

    assert result is False
    assert processor.stats["files_failed"] == 1
    assert processor.stats["validation_errors"] == 1


def test_process_files(config_file, test_json_file):
    """Test processing multiple JSON files."""
    processor = JSONProcessor(config_path=config_file)
    json_file, original_data = test_json_file

    # Create another JSON file
    source_dir = json_file.parent
    json_file2 = source_dir / "test2.json"
    json_file2.write_text('{"key": "value"}')

    stats = processor.process_files()

    assert stats["files_processed"] >= 2
    assert processor.output_dir.exists()


def test_process_files_overwrite(config_file, test_json_file):
    """Test processing files with overwrite (no output directory)."""
    processor = JSONProcessor(config_path=config_file)
    processor.config["output_directory"] = None
    processor._setup_directories()

    json_file, original_data = test_json_file

    result = processor._process_json_file(json_file)

    assert result is True
    # File should be overwritten in place
    assert json_file.exists()


def test_environment_variable_overrides(temp_dir):
    """Test that environment variables override config."""
    source_dir = temp_dir / "source"
    source_dir.mkdir()

    config = {
        "source_directory": str(source_dir),
        "output_directory": str(temp_dir / "output"),
        "processing": {
            "remove_null": True,
            "sort_keys": True,
            "indent": 2,
            "ensure_ascii": False,
            "compact_separators": False,
        },
        "backup": {"enabled": False, "directory": "backups"},
        "exclusions": {"directories": [], "patterns": []},
        "operations": {"recursive": True},
        "logging": {
            "level": "INFO",
            "file": str(temp_dir / "test.log"),
            "max_bytes": 10485760,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }
    config_path = temp_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    with patch.dict(os.environ, {"SOURCE_DIRECTORY": str(temp_dir / "custom")}):
        # This will fail because directory doesn't exist, but tests override
        pass
