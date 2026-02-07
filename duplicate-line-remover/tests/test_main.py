"""Unit tests for duplicate line remover module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.main import DuplicateLineRemover


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    return tempfile.mkdtemp()


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary configuration file."""
    config = {
        "processing": {
            "ignore_case": False,
            "ignore_whitespace": False,
            "preserve_empty_lines": True,
            "trim_lines": False,
            "normalize_whitespace": False,
        },
        "file_handling": {
            "input_encoding": "utf-8",
            "output_encoding": "utf-8",
            "backup_original": False,  # Disable backups for tests
            "overwrite_original": False,
        },
        "output": {
            "output_suffix": ".deduplicated",
            "create_output_file": True,
        },
        "logging": {
            "level": "DEBUG",
            "file": f"{temp_dir}/test.log",
            "max_bytes": 1048576,
            "backup_count": 3,
        },
        "reporting": {
            "generate_report": True,
            "report_file": f"{temp_dir}/report.txt",
            "include_statistics": True,
        },
    }

    config_path = Path(temp_dir) / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config_path


def test_duplicate_line_remover_initialization(config_file):
    """Test DuplicateLineRemover initializes correctly."""
    remover = DuplicateLineRemover(config_path=str(config_file))
    assert remover.stats["files_processed"] == 0
    assert remover.stats["duplicate_lines_removed"] == 0


def test_duplicate_line_remover_missing_config():
    """Test DuplicateLineRemover raises error for missing config."""
    with pytest.raises(FileNotFoundError):
        DuplicateLineRemover(config_path="nonexistent.yaml")


def test_normalize_line_basic(config_file):
    """Test basic line normalization."""
    remover = DuplicateLineRemover(config_path=str(config_file))

    assert remover._normalize_line("Hello World") == "Hello World"
    assert remover._normalize_line("  Hello  ") == "  Hello  "  # No trim by default


def test_normalize_line_ignore_case(config_file):
    """Test case-insensitive normalization."""
    remover = DuplicateLineRemover(config_path=str(config_file))
    remover.config["processing"]["ignore_case"] = True

    assert remover._normalize_line("Hello") == "hello"
    assert remover._normalize_line("HELLO") == "hello"
    assert remover._normalize_line("HeLLo") == "hello"


def test_normalize_line_ignore_whitespace(config_file):
    """Test whitespace-ignoring normalization."""
    remover = DuplicateLineRemover(config_path=str(config_file))
    remover.config["processing"]["ignore_whitespace"] = True

    assert remover._normalize_line("Hello World") == "HelloWorld"
    assert remover._normalize_line("Hello  World") == "HelloWorld"
    assert remover._normalize_line("  Hello World  ") == "HelloWorld"


def test_normalize_line_trim(config_file):
    """Test line trimming."""
    remover = DuplicateLineRemover(config_path=str(config_file))
    remover.config["processing"]["trim_lines"] = True

    assert remover._normalize_line("  Hello  ") == "Hello"
    assert remover._normalize_line("  Test  ") == "Test"


def test_remove_duplicates_basic(config_file, temp_dir):
    """Test basic duplicate removal."""
    remover = DuplicateLineRemover(config_path=str(config_file))

    # Create test file with duplicates
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("line1\nline2\nline1\nline3\nline2\n")

    lines, duplicates = remover._remove_duplicates(test_file)

    assert len(lines) == 3
    assert duplicates == 2
    assert "line1\n" in lines
    assert "line2\n" in lines
    assert "line3\n" in lines


def test_remove_duplicates_preserve_order(config_file, temp_dir):
    """Test that line order is preserved."""
    remover = DuplicateLineRemover(config_path=str(config_file))

    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("first\nsecond\nfirst\nthird\nsecond\n")

    lines, _ = remover._remove_duplicates(test_file)

    # Should preserve order: first, second, third
    assert lines[0] == "first\n"
    assert lines[1] == "second\n"
    assert lines[2] == "third\n"


def test_remove_duplicates_ignore_case(config_file, temp_dir):
    """Test duplicate removal with case-insensitive comparison."""
    remover = DuplicateLineRemover(config_path=str(config_file))
    remover.config["processing"]["ignore_case"] = True

    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello\nHELLO\nhello\nWorld\n")

    lines, duplicates = remover._remove_duplicates(test_file)

    assert len(lines) == 2  # Only "Hello" and "World" (case variants are duplicates)
    assert duplicates == 2


def test_remove_duplicates_ignore_whitespace(config_file, temp_dir):
    """Test duplicate removal with whitespace-ignoring comparison."""
    remover = DuplicateLineRemover(config_path=str(config_file))
    remover.config["processing"]["ignore_whitespace"] = True

    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello World\nHello  World\nHelloWorld\n")

    lines, duplicates = remover._remove_duplicates(test_file)

    assert len(lines) == 1  # All are considered duplicates
    assert duplicates == 2


def test_process_file(config_file, temp_dir):
    """Test processing a file."""
    remover = DuplicateLineRemover(config_path=str(config_file))

    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("line1\nline2\nline1\nline3\n")

    result = remover.process_file(test_file)

    assert result is True
    assert remover.stats["files_processed"] == 1
    assert remover.stats["duplicate_lines_removed"] == 1

    # Check output file exists
    output_file = test_file.with_suffix(test_file.suffix + ".deduplicated")
    assert output_file.exists()

    # Verify content
    content = output_file.read_text()
    assert "line1\n" in content
    assert "line2\n" in content
    assert "line3\n" in content
    assert content.count("line1\n") == 1  # Only one occurrence


def test_process_file_empty_lines(config_file, temp_dir):
    """Test handling of empty lines."""
    remover = DuplicateLineRemover(config_path=str(config_file))
    remover.config["processing"]["preserve_empty_lines"] = True

    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("line1\n\nline2\n\n")

    lines, duplicates = remover._remove_duplicates(test_file)

    # Should preserve first empty line
    assert len(lines) == 3  # line1, empty, line2
    assert duplicates == 1  # One duplicate empty line removed
