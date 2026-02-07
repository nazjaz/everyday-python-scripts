"""Unit tests for Regex File Finder."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import RegexFileFinder


@pytest.fixture
def sample_config():
    """Create sample configuration dictionary."""
    return {
        "search": {
            "directory": ".",
            "case_sensitive": False,
            "match_full_path": False,
            "recursive": True,
            "max_file_size": 10485760,
            "encoding": "utf-8",
            "exclude": {
                "patterns": [],
                "directories": [],
                "extensions": [],
            },
        },
        "operations": {
            "output_directory": "output",
            "overwrite_existing": False,
            "preserve_structure": False,
        },
        "logging": {
            "level": "INFO",
            "file": "logs/test.log",
            "max_bytes": 10485760,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }


@pytest.fixture
def temp_config_file(sample_config, tmp_path):
    """Create temporary configuration file."""
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(sample_config, f)
    return str(config_path)


@pytest.fixture
def temp_directory(tmp_path):
    """Create temporary directory with test files."""
    test_dir = tmp_path / "test_search"
    test_dir.mkdir()

    # Create test files
    (test_dir / "file1.txt").write_text("This is a test file")
    (test_dir / "file2.log").write_text("Log entry here")
    (test_dir / "file3.py").write_text("import os\n# TODO: fix this")
    (test_dir / "test_file.txt").write_text("Another test file")
    (test_dir / "data.json").write_text('{"key": "value"}')

    # Create subdirectory
    subdir = test_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested.txt").write_text("Nested file")

    return test_dir


class TestRegexFileFinder:
    """Test cases for RegexFileFinder class."""

    def test_init_loads_config(self, temp_config_file):
        """Test that initialization loads configuration file."""
        finder = RegexFileFinder(config_path=temp_config_file)
        assert finder.config is not None
        assert "search" in finder.config

    def test_init_raises_file_not_found(self):
        """Test that initialization raises error for missing config file."""
        with pytest.raises(FileNotFoundError):
            RegexFileFinder(config_path="nonexistent.yaml")

    def test_matches_name_pattern(self, temp_config_file):
        """Test filename pattern matching."""
        finder = RegexFileFinder(config_path=temp_config_file)
        test_file = Path("test_file.txt")

        assert finder._matches_name_pattern(test_file, r"\.txt$") is True
        assert finder._matches_name_pattern(test_file, r"\.log$") is False
        assert finder._matches_name_pattern(test_file, r"test") is True

    def test_matches_name_pattern_case_insensitive(self, temp_config_file):
        """Test case-insensitive filename matching."""
        finder = RegexFileFinder(config_path=temp_config_file)
        finder.config["search"]["case_sensitive"] = False
        test_file = Path("TestFile.txt")

        assert finder._matches_name_pattern(test_file, r"test") is True
        assert finder._matches_name_pattern(test_file, r"TEST") is True

    def test_matches_content_pattern(self, temp_config_file, tmp_path):
        """Test content pattern matching."""
        finder = RegexFileFinder(config_path=temp_config_file)
        test_file = tmp_path / "test.txt"
        test_file.write_text("This file contains TODO comment")

        assert finder._matches_content_pattern(test_file, r"TODO") is True
        assert finder._matches_content_pattern(test_file, r"FIXME") is False

    def test_is_excluded_by_directory(self, temp_config_file):
        """Test directory exclusion."""
        finder = RegexFileFinder(config_path=temp_config_file)
        finder.config["search"]["exclude"]["directories"] = [".git"]

        excluded_file = Path("/path/.git/config")
        assert finder._is_excluded(excluded_file) is True

        normal_file = Path("/path/file.txt")
        assert finder._is_excluded(normal_file) is False

    def test_is_excluded_by_extension(self, temp_config_file):
        """Test extension exclusion."""
        finder = RegexFileFinder(config_path=temp_config_file)
        finder.config["search"]["exclude"]["extensions"] = [".exe", ".dll"]

        excluded_file = Path("program.exe")
        assert finder._is_excluded(excluded_file) is True

        normal_file = Path("file.txt")
        assert finder._is_excluded(normal_file) is False

    def test_find_files_by_name(self, temp_config_file, temp_directory):
        """Test finding files by name pattern."""
        finder = RegexFileFinder(config_path=temp_config_file)
        files = finder.find_files(
            r"\.txt$", search_directory=str(temp_directory), search_in="name"
        )

        assert len(files) >= 2
        file_names = [f["name"] for f in files]
        assert "file1.txt" in file_names or any("txt" in name for name in file_names)

    def test_find_files_by_content(self, temp_config_file, temp_directory):
        """Test finding files by content pattern."""
        finder = RegexFileFinder(config_path=temp_config_file)
        files = finder.find_files(
            r"TODO", search_directory=str(temp_directory), search_in="content"
        )

        assert len(files) >= 1
        file_names = [f["name"] for f in files]
        assert "file3.py" in file_names

    def test_find_files_both(self, temp_config_file, temp_directory):
        """Test finding files by both name and content."""
        finder = RegexFileFinder(config_path=temp_config_file)
        files = finder.find_files(
            r"test", search_directory=str(temp_directory), search_in="both"
        )

        assert len(files) >= 1

    def test_find_files_empty_pattern(self, temp_config_file, temp_directory):
        """Test that empty pattern raises error."""
        finder = RegexFileFinder(config_path=temp_config_file)
        with pytest.raises(ValueError):
            finder.find_files("", search_directory=str(temp_directory))

    def test_find_files_invalid_search_in(self, temp_config_file, temp_directory):
        """Test that invalid search_in raises error."""
        finder = RegexFileFinder(config_path=temp_config_file)
        with pytest.raises(ValueError):
            finder.find_files(
                r"test", search_directory=str(temp_directory), search_in="invalid"
            )

    def test_find_files_nonexistent_directory(self, temp_config_file):
        """Test that nonexistent directory raises error."""
        finder = RegexFileFinder(config_path=temp_config_file)
        with pytest.raises(FileNotFoundError):
            finder.find_files(r"test", search_directory="/nonexistent/path")

    def test_find_files_non_recursive(self, temp_config_file, temp_directory):
        """Test non-recursive search."""
        finder = RegexFileFinder(config_path=temp_config_file)
        files = finder.find_files(
            r"\.txt$",
            search_directory=str(temp_directory),
            search_in="name",
            recursive=False,
        )

        # Should not find nested.txt in subdirectory
        file_paths = [f["path"] for f in files]
        assert not any("nested.txt" in path for path in file_paths)

    def test_list_files(self, temp_config_file, temp_directory):
        """Test list_files method."""
        finder = RegexFileFinder(config_path=temp_config_file)
        files = finder.list_files(
            r"\.txt$", search_directory=str(temp_directory), search_in="name"
        )

        assert isinstance(files, list)
        assert len(files) >= 1

    def test_copy_files(self, temp_config_file, temp_directory, tmp_path):
        """Test copying files."""
        finder = RegexFileFinder(config_path=temp_config_file)
        dest_dir = tmp_path / "output"
        dest_dir.mkdir()

        count = finder.copy_files(
            r"\.txt$",
            destination=str(dest_dir),
            search_directory=str(temp_directory),
            search_in="name",
        )

        assert count > 0
        copied_files = list(dest_dir.glob("*.txt"))
        assert len(copied_files) > 0

    def test_copy_files_preserve_structure(
        self, temp_config_file, temp_directory, tmp_path
    ):
        """Test copying files with structure preservation."""
        finder = RegexFileFinder(config_path=temp_config_file)
        dest_dir = tmp_path / "output"
        dest_dir.mkdir()

        count = finder.copy_files(
            r"\.txt$",
            destination=str(dest_dir),
            preserve_structure=True,
            search_directory=str(temp_directory),
            search_in="name",
        )

        assert count > 0
        # Check if subdirectory structure is preserved
        subdir_files = list((dest_dir / "subdir").glob("*.txt"))
        assert len(subdir_files) > 0

    def test_move_files(self, temp_config_file, temp_directory, tmp_path):
        """Test moving files."""
        finder = RegexFileFinder(config_path=temp_config_file)
        dest_dir = tmp_path / "output"
        dest_dir.mkdir()

        # Count files before move
        txt_files_before = list(temp_directory.rglob("*.txt"))

        count = finder.move_files(
            r"\.txt$",
            destination=str(dest_dir),
            search_directory=str(temp_directory),
            search_in="name",
        )

        assert count > 0
        # Verify files moved
        txt_files_after = list(temp_directory.rglob("*.txt"))
        assert len(txt_files_after) < len(txt_files_before)

    def test_get_stats(self, temp_config_file):
        """Test getting statistics."""
        finder = RegexFileFinder(config_path=temp_config_file)
        stats = finder.get_stats()

        assert "files_scanned" in stats
        assert "files_matched" in stats
        assert "files_moved" in stats
        assert "files_copied" in stats
        assert "errors" in stats

    def test_matches_content_pattern_binary_file(
        self, temp_config_file, tmp_path
    ):
        """Test that binary files are skipped in content search."""
        finder = RegexFileFinder(config_path=temp_config_file)
        # Create a file with null bytes (binary)
        binary_file = tmp_path / "binary.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03")

        result = finder._matches_content_pattern(binary_file, r"test")
        assert result is False

    def test_matches_content_pattern_large_file(
        self, temp_config_file, tmp_path
    ):
        """Test that files exceeding size limit are skipped."""
        finder = RegexFileFinder(config_path=temp_config_file)
        finder.config["search"]["max_file_size"] = 100  # Very small limit

        large_file = tmp_path / "large.txt"
        large_file.write_text("x" * 200)  # Larger than limit

        result = finder._matches_content_pattern(large_file, r"x")
        assert result is False
