"""Unit tests for Duplicate Name Finder."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import DuplicateNameFinder


@pytest.fixture
def sample_config():
    """Create sample configuration dictionary."""
    return {
        "search": {
            "directory": ".",
            "recursive": True,
            "exclude": {
                "patterns": [],
                "directories": [],
                "extensions": [],
            },
        },
        "renaming": {
            "prefix_separator": "_",
            "skip_if_exists": True,
            "skip_base_directory": True,
        },
        "report": {
            "output_directory": "output",
            "output_file": "report.txt",
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
    """Create temporary directory with duplicate file names."""
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()

    # Create subdirectories with files having same names
    dir1 = test_dir / "dir1"
    dir1.mkdir()
    (dir1 / "file.txt").write_text("content 1")

    dir2 = test_dir / "dir2"
    dir2.mkdir()
    (dir2 / "file.txt").write_text("content 2")

    dir3 = test_dir / "dir3"
    dir3.mkdir()
    (dir3 / "file.txt").write_text("content 3")

    # Create unique file (not a duplicate)
    (test_dir / "unique.txt").write_text("unique")

    return test_dir


class TestDuplicateNameFinder:
    """Test cases for DuplicateNameFinder class."""

    def test_init_loads_config(self, temp_config_file):
        """Test that initialization loads configuration file."""
        finder = DuplicateNameFinder(config_path=temp_config_file)
        assert finder.config is not None
        assert "search" in finder.config

    def test_init_raises_file_not_found(self):
        """Test that initialization raises error for missing config file."""
        with pytest.raises(FileNotFoundError):
            DuplicateNameFinder(config_path="nonexistent.yaml")

    def test_find_duplicate_names(self, temp_config_file, temp_directory):
        """Test finding duplicate file names."""
        finder = DuplicateNameFinder(config_path=temp_config_file)
        duplicates = finder.find_duplicate_names(str(temp_directory))

        assert "file.txt" in duplicates
        assert len(duplicates["file.txt"]) == 3
        assert "unique.txt" not in duplicates

    def test_find_duplicate_names_nonexistent_directory(self, temp_config_file):
        """Test that nonexistent directory raises error."""
        finder = DuplicateNameFinder(config_path=temp_config_file)
        with pytest.raises(FileNotFoundError):
            finder.find_duplicate_names("/nonexistent/path")

    def test_find_duplicate_names_non_recursive(self, temp_config_file, tmp_path):
        """Test non-recursive search."""
        finder = DuplicateNameFinder(config_path=temp_config_file)
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        # Create file in root
        (test_dir / "file.txt").write_text("root")

        # Create subdirectory with same name
        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "file.txt").write_text("nested")

        duplicates = finder.find_duplicate_names(str(test_dir), recursive=False)

        # Should not find nested file
        assert "file.txt" not in duplicates

    def test_get_directory_prefix(self, temp_config_file, tmp_path):
        """Test getting directory prefix."""
        finder = DuplicateNameFinder(config_path=temp_config_file)
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        subdir = base_dir / "subdir"
        subdir.mkdir()
        file_path = subdir / "file.txt"
        file_path.write_text("test")

        prefix = finder._get_directory_prefix(file_path, base_dir)
        assert prefix == "subdir"

    def test_get_directory_prefix_base_directory(self, temp_config_file, tmp_path):
        """Test prefix for file in base directory."""
        finder = DuplicateNameFinder(config_path=temp_config_file)
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        file_path = base_dir / "file.txt"
        file_path.write_text("test")

        prefix = finder._get_directory_prefix(file_path, base_dir)
        assert prefix == ""

    def test_rename_with_prefixes_dry_run(self, temp_config_file, temp_directory):
        """Test renaming with dry-run mode."""
        finder = DuplicateNameFinder(config_path=temp_config_file)
        finder.find_duplicate_names(str(temp_directory))

        renamed = finder.rename_with_prefixes(
            base_directory=str(temp_directory), dry_run=True
        )

        assert renamed > 0
        # Files should not actually be renamed
        assert (temp_directory / "dir1" / "file.txt").exists()

    def test_rename_with_prefixes(self, temp_config_file, temp_directory):
        """Test renaming duplicate files."""
        finder = DuplicateNameFinder(config_path=temp_config_file)
        finder.find_duplicate_names(str(temp_directory))

        renamed = finder.rename_with_prefixes(base_directory=str(temp_directory))

        assert renamed > 0
        # Check that files were renamed
        assert (temp_directory / "dir1" / "dir1_file.txt").exists()
        assert not (temp_directory / "dir1" / "file.txt").exists()

    def test_rename_with_prefixes_no_duplicates(self, temp_config_file):
        """Test renaming raises error when no duplicates found."""
        finder = DuplicateNameFinder(config_path=temp_config_file)
        with pytest.raises(ValueError):
            finder.rename_with_prefixes()

    def test_is_excluded_by_directory(self, temp_config_file):
        """Test directory exclusion."""
        finder = DuplicateNameFinder(config_path=temp_config_file)
        finder.config["search"]["exclude"]["directories"] = [".git"]

        excluded_file = Path("/path/.git/config")
        assert finder._is_excluded(excluded_file) is True

        normal_file = Path("/path/file.txt")
        assert finder._is_excluded(normal_file) is False

    def test_generate_report(self, temp_config_file, temp_directory, tmp_path):
        """Test generating report."""
        finder = DuplicateNameFinder(config_path=temp_config_file)
        finder.find_duplicate_names(str(temp_directory))

        report_file = tmp_path / "report.txt"
        report_content = finder.generate_report(str(report_file))

        assert len(report_content) > 0
        assert "Duplicate File Names Report" in report_content
        assert report_file.exists()

    def test_format_size(self, temp_config_file):
        """Test file size formatting."""
        finder = DuplicateNameFinder(config_path=temp_config_file)

        assert "B" in finder._format_size(500)
        assert "KB" in finder._format_size(5000)
        assert "MB" in finder._format_size(5000000)

    def test_get_statistics(self, temp_config_file):
        """Test getting statistics."""
        finder = DuplicateNameFinder(config_path=temp_config_file)
        stats = finder.get_statistics()

        assert "files_scanned" in stats
        assert "duplicate_names_found" in stats
        assert "files_renamed" in stats
        assert "errors" in stats
