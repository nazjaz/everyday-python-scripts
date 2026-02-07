"""Unit tests for Text Merger."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.main import TextMerger


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
        "output_file": str(temp_dir / "merged.txt"),
        "text_extensions": [".txt", ".md"],
        "sort_order": "alphabetical",
        "header_format": "=== {filename} ===",
        "separator": "\n---\n",
        "include_header": False,
        "exclusions": {"patterns": [], "extensions": []},
        "input_encoding": "utf-8",
        "output_encoding": "utf-8",
        "operations": {"recursive": False, "dry_run": False},
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
def test_files(temp_dir):
    """Create test text files."""
    source_dir = temp_dir / "source"
    source_dir.mkdir()

    (source_dir / "file1.txt").write_text("Content from file 1")
    (source_dir / "file2.txt").write_text("Content from file 2")
    (source_dir / "file3.txt").write_text("Content from file 3")

    return source_dir


def test_text_merger_initialization(config_file):
    """Test TextMerger initialization."""
    merger = TextMerger(config_path=config_file)
    assert merger.config is not None
    assert merger.source_dir.exists()


def test_load_config_file_not_found():
    """Test that FileNotFoundError is raised when config file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        TextMerger(config_path="nonexistent.yaml")


def test_is_text_file(config_file):
    """Test text file detection."""
    merger = TextMerger(config_path=config_file)

    assert merger._is_text_file(Path("test.txt")) is True
    assert merger._is_text_file(Path("test.md")) is True
    assert merger._is_text_file(Path("test.log")) is True
    assert merger._is_text_file(Path("test.doc")) is False


def test_should_include_file(config_file):
    """Test file inclusion filtering."""
    merger = TextMerger(config_path=config_file)

    normal_file = Path("test.txt")
    assert merger._should_include_file(normal_file) is True

    # Test exclusion by pattern
    merger.config["exclusions"]["patterns"] = [".tmp"]
    excluded_file = Path("test.tmp.txt")
    assert merger._should_include_file(excluded_file) is False

    # Test exclusion by extension
    merger.config["exclusions"]["extensions"] = [".bak"]
    excluded_ext = Path("test.bak")
    assert merger._should_include_file(excluded_ext) is False


def test_format_header(config_file):
    """Test header formatting."""
    merger = TextMerger(config_path=config_file)

    header = merger._format_header("test.txt")
    assert "test.txt" in header
    assert "===" in header


def test_format_separator(config_file):
    """Test separator formatting."""
    merger = TextMerger(config_path=config_file)

    separator = merger._format_separator()
    assert isinstance(separator, str)
    assert len(separator) > 0


def test_read_file_content(config_file, test_files):
    """Test reading file content."""
    merger = TextMerger(config_path=config_file)

    test_file = test_files / "file1.txt"
    content = merger._read_file_content(test_file)

    assert content is not None
    assert "Content from file 1" in content


def test_read_file_content_nonexistent(config_file):
    """Test reading non-existent file."""
    merger = TextMerger(config_path=config_file)

    nonexistent = Path("/nonexistent/file.txt")
    content = merger._read_file_content(nonexistent)

    assert content is None
    assert merger.stats["errors"] > 0


def test_get_file_list(config_file, test_files):
    """Test getting list of files to merge."""
    merger = TextMerger(config_path=config_file)

    file_list = merger._get_file_list()

    assert len(file_list) == 3
    assert all(f.name.startswith("file") for f in file_list)


def test_get_file_list_sorted(config_file, test_files):
    """Test file list sorting."""
    merger = TextMerger(config_path=config_file)
    merger.config["sort_order"] = "alphabetical"

    file_list = merger._get_file_list()

    # Should be sorted alphabetically
    names = [f.name for f in file_list]
    assert names == sorted(names)


def test_merge_files(config_file, test_files):
    """Test merging files."""
    merger = TextMerger(config_path=config_file)

    file_list = merger._get_file_list()
    merged_content = merger._merge_files(file_list)

    assert "file1.txt" in merged_content
    assert "file2.txt" in merged_content
    assert "file3.txt" in merged_content
    assert "Content from file 1" in merged_content
    assert "Content from file 2" in merged_content
    assert "Content from file 3" in merged_content


def test_merge_text_files_dry_run(config_file, test_files):
    """Test merging files in dry run mode."""
    merger = TextMerger(config_path=config_file)
    merger.config["operations"]["dry_run"] = True

    stats = merger.merge_text_files()

    assert stats["files_merged"] > 0
    assert not merger.output_path.exists()  # File should not be created


def test_merge_text_files_actual(config_file, test_files):
    """Test actual file merging."""
    merger = TextMerger(config_path=config_file)
    merger.config["operations"]["dry_run"] = False

    stats = merger.merge_text_files()

    assert stats["files_merged"] > 0
    assert merger.output_path.exists()

    # Check merged content
    content = merger.output_path.read_text()
    assert "file1.txt" in content
    assert "file2.txt" in content
    assert "file3.txt" in content


def test_environment_variable_overrides(temp_dir):
    """Test that environment variables override config."""
    source_dir = temp_dir / "source"
    source_dir.mkdir()

    config = {
        "source_directory": str(source_dir),
        "output_file": str(temp_dir / "merged.txt"),
        "text_extensions": [".txt"],
        "sort_order": "alphabetical",
        "header_format": "=== {filename} ===",
        "separator": "\n---\n",
        "include_header": False,
        "exclusions": {"patterns": [], "extensions": []},
        "input_encoding": "utf-8",
        "output_encoding": "utf-8",
        "operations": {"recursive": False, "dry_run": False},
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

    with patch.dict(os.environ, {"DRY_RUN": "true"}):
        merger = TextMerger(config_path=str(config_path))
        assert merger.config["operations"]["dry_run"] is True
