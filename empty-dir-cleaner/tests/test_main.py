"""Unit tests for empty directory cleaner module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.main import EmptyDirectoryCleaner


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    return tempfile.mkdtemp()


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary configuration file."""
    config = {
        "targets": [
            {"path": temp_dir, "enabled": True},
        ],
        "preserve_patterns": {
            "enabled": True,
            "patterns": [".git", "__pycache__", "node_modules"],
            "match_type": "name",
        },
        "safety": {
            "dry_run": True,  # Use dry run for tests
            "confirm_before_delete": False,
            "max_depth": None,
            "follow_symlinks": False,
        },
        "deletion": {
            "recursive": True,
            "remove_parent_if_empty": True,
            "batch_size": 100,
        },
        "logging": {
            "level": "DEBUG",
            "file": f"{temp_dir}/test.log",
            "max_bytes": 1048576,
            "backup_count": 3,
            "log_deletions": True,
            "log_preserved": False,
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


def test_empty_directory_cleaner_initialization(config_file):
    """Test EmptyDirectoryCleaner initializes correctly."""
    cleaner = EmptyDirectoryCleaner(config_path=str(config_file))
    assert cleaner.stats["directories_scanned"] == 0
    assert cleaner.stats["directories_deleted"] == 0


def test_empty_directory_cleaner_missing_config():
    """Test EmptyDirectoryCleaner raises error for missing config."""
    with pytest.raises(FileNotFoundError):
        EmptyDirectoryCleaner(config_path="nonexistent.yaml")


def test_is_directory_empty(config_file, temp_dir):
    """Test checking if directory is empty."""
    cleaner = EmptyDirectoryCleaner(config_path=str(config_file))

    # Create empty directory
    empty_dir = Path(temp_dir) / "empty_dir"
    empty_dir.mkdir()

    assert cleaner._is_directory_empty(empty_dir) is True

    # Create non-empty directory
    non_empty_dir = Path(temp_dir) / "non_empty_dir"
    non_empty_dir.mkdir()
    (non_empty_dir / "file.txt").touch()

    assert cleaner._is_directory_empty(non_empty_dir) is False


def test_should_preserve(config_file):
    """Test pattern preservation checking."""
    cleaner = EmptyDirectoryCleaner(config_path=str(config_file))

    # Should preserve .git
    git_dir = Path("/test/.git")
    assert cleaner._should_preserve(git_dir) is True

    # Should preserve __pycache__
    cache_dir = Path("/test/__pycache__")
    assert cleaner._should_preserve(cache_dir) is True

    # Should not preserve other directories
    other_dir = Path("/test/other_dir")
    assert cleaner._should_preserve(other_dir) is False


def test_find_empty_directories(config_file, temp_dir):
    """Test finding empty directories."""
    cleaner = EmptyDirectoryCleaner(config_path=str(config_file))

    # Create directory structure with empty dirs
    test_root = Path(temp_dir) / "test_root"
    test_root.mkdir()

    empty1 = test_root / "empty1"
    empty1.mkdir()

    empty2 = test_root / "empty2"
    empty2.mkdir()

    non_empty = test_root / "non_empty"
    non_empty.mkdir()
    (non_empty / "file.txt").touch()

    # Nested empty directory
    nested = test_root / "nested"
    nested.mkdir()
    nested_empty = nested / "nested_empty"
    nested_empty.mkdir()

    empty_dirs = cleaner._find_empty_directories(test_root)

    # Should find empty directories (deepest first)
    empty_paths = {str(d) for d in empty_dirs}
    assert str(empty1) in empty_paths
    assert str(empty2) in empty_paths
    assert str(nested_empty) in empty_paths
    assert str(non_empty) not in empty_paths


def test_delete_directory_dry_run(config_file, temp_dir):
    """Test deleting directory in dry run mode."""
    cleaner = EmptyDirectoryCleaner(config_path=str(config_file))
    cleaner.config["safety"]["dry_run"] = True

    # Create empty directory
    empty_dir = Path(temp_dir) / "to_delete"
    empty_dir.mkdir()

    result = cleaner._delete_directory(empty_dir)

    assert result is True
    # Directory should still exist in dry run
    assert empty_dir.exists()


def test_clean_directories(config_file, temp_dir):
    """Test cleaning directories."""
    cleaner = EmptyDirectoryCleaner(config_path=str(config_file))

    # Create test structure
    test_root = Path(temp_dir) / "clean_test"
    test_root.mkdir()

    empty1 = test_root / "empty1"
    empty1.mkdir()

    empty2 = test_root / "empty2"
    empty2.mkdir()

    # Update config to use test directory
    cleaner.config["targets"] = [{"path": str(test_root), "enabled": True}]

    stats = cleaner.clean_directories()

    assert stats["empty_directories_found"] >= 2
    assert stats["directories_deleted"] >= 2  # In dry run, still counts as deleted


def test_preserve_patterns(config_file, temp_dir):
    """Test that preserved patterns are not deleted."""
    cleaner = EmptyDirectoryCleaner(config_path=str(config_file))

    # Create test structure with preserved directory
    test_root = Path(temp_dir) / "preserve_test"
    test_root.mkdir()

    git_dir = test_root / ".git"
    git_dir.mkdir()

    empty_dir = test_root / "empty_dir"
    empty_dir.mkdir()

    cleaner.config["targets"] = [{"path": str(test_root), "enabled": True}]

    stats = cleaner.clean_directories()

    # .git should be preserved
    assert stats["directories_preserved"] >= 1
    # empty_dir should be deleted (not preserved)
    assert stats["directories_deleted"] >= 1
