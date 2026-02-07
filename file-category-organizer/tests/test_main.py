"""Unit tests for File Category Organizer."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import FileCategoryOrganizer


@pytest.fixture
def sample_config():
    """Create sample configuration dictionary."""
    return {
        "organizer": {
            "source_directory": ".",
            "destination_directory": "organized",
            "recursive": True,
            "overwrite_existing": False,
            "check_duplicates": False,
            "handle_duplicates": "skip",
            "handle_duplicate_names": "rename",
            "exclude": {
                "patterns": [],
                "extensions": [],
            },
        },
        "categories": {
            "Media": [".jpg", ".png", ".mp4"],
            "Documents": [".pdf", ".doc", ".txt"],
            "Archives": [".zip", ".rar"],
            "Code": [".py", ".js", ".html"],
            "Data": [".csv", ".json"],
        },
        "custom_mappings": {},
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
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()

    # Create test files with different extensions
    (test_dir / "photo.jpg").write_text("image content")
    (test_dir / "document.pdf").write_text("pdf content")
    (test_dir / "archive.zip").write_text("zip content")
    (test_dir / "script.py").write_text("python code")
    (test_dir / "data.csv").write_text("csv data")

    return test_dir


class TestFileCategoryOrganizer:
    """Test cases for FileCategoryOrganizer class."""

    def test_init_loads_config(self, temp_config_file):
        """Test that initialization loads configuration file."""
        organizer = FileCategoryOrganizer(config_path=temp_config_file)
        assert organizer.config is not None
        assert "organizer" in organizer.config

    def test_init_raises_file_not_found(self):
        """Test that initialization raises error for missing config file."""
        with pytest.raises(FileNotFoundError):
            FileCategoryOrganizer(config_path="nonexistent.yaml")

    def test_load_category_mappings(self, temp_config_file):
        """Test loading category mappings."""
        organizer = FileCategoryOrganizer(config_path=temp_config_file)
        mappings = organizer.category_mappings

        assert "jpg" in mappings
        assert mappings["jpg"] == "Media"
        assert "pdf" in mappings
        assert mappings["pdf"] == "Documents"
        assert "py" in mappings
        assert mappings["py"] == "Code"

    def test_load_custom_mappings(self, temp_config_file):
        """Test loading custom mappings override defaults."""
        # Update config with custom mapping
        with open(temp_config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        config["custom_mappings"] = {".jpg": "Documents"}
        with open(temp_config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        organizer = FileCategoryOrganizer(config_path=temp_config_file)
        assert organizer.category_mappings["jpg"] == "Documents"

    def test_get_category(self, temp_config_file):
        """Test getting category for file."""
        organizer = FileCategoryOrganizer(config_path=temp_config_file)
        test_file = Path("photo.jpg")

        category = organizer._get_category(test_file)
        assert category == "Media"

    def test_get_category_unknown(self, temp_config_file):
        """Test getting category for unknown extension."""
        organizer = FileCategoryOrganizer(config_path=temp_config_file)
        test_file = Path("file.unknown")

        category = organizer._get_category(test_file)
        assert category == "Other"

    def test_get_destination_path(self, temp_config_file, tmp_path):
        """Test getting destination path."""
        organizer = FileCategoryOrganizer(config_path=temp_config_file)
        source_file = Path("photo.jpg")
        dest_base = tmp_path / "organized"

        destination = organizer._get_destination_path(source_file, "Media", dest_base)
        assert destination.parent.name == "Media"
        assert destination.name == "photo.jpg"

    def test_get_destination_path_duplicate(self, temp_config_file, tmp_path):
        """Test getting destination path with duplicate name."""
        organizer = FileCategoryOrganizer(config_path=temp_config_file)
        source_file = Path("photo.jpg")
        dest_base = tmp_path / "organized"
        dest_base.mkdir()
        (dest_base / "Media").mkdir()
        (dest_base / "Media" / "photo.jpg").write_text("existing")

        destination = organizer._get_destination_path(source_file, "Media", dest_base)
        assert destination.name == "photo_1.jpg"

    def test_should_process_file(self, temp_config_file):
        """Test file processing check."""
        organizer = FileCategoryOrganizer(config_path=temp_config_file)
        test_file = Path("test.jpg")

        assert organizer._should_process_file(test_file) is True

    def test_should_process_file_excluded_extension(self, temp_config_file):
        """Test file processing check with excluded extension."""
        # Update config with exclusion
        with open(temp_config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        config["organizer"]["exclude"]["extensions"] = [".tmp"]
        with open(temp_config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        organizer = FileCategoryOrganizer(config_path=temp_config_file)
        test_file = Path("test.tmp")

        assert organizer._should_process_file(test_file) is False

    def test_organize_files(self, temp_config_file, temp_directory, tmp_path):
        """Test organizing files."""
        organizer = FileCategoryOrganizer(config_path=temp_config_file)
        dest_dir = tmp_path / "organized"

        stats = organizer.organize_files(
            source_directory=str(temp_directory), destination_directory=str(dest_dir)
        )

        assert stats["files_moved"] > 0
        assert (dest_dir / "Media").exists()
        assert (dest_dir / "Documents").exists()
        assert (dest_dir / "Archives").exists()
        assert (dest_dir / "Code").exists()
        assert (dest_dir / "Data").exists()

    def test_organize_files_nonexistent_source(self, temp_config_file):
        """Test organizing files with nonexistent source raises error."""
        organizer = FileCategoryOrganizer(config_path=temp_config_file)
        with pytest.raises(FileNotFoundError):
            organizer.organize_files(source_directory="/nonexistent/path")

    def test_get_statistics(self, temp_config_file):
        """Test getting statistics."""
        organizer = FileCategoryOrganizer(config_path=temp_config_file)
        stats = organizer.get_statistics()

        assert "files_processed" in stats
        assert "files_moved" in stats
        assert "files_skipped" in stats
        assert "duplicates_found" in stats
        assert "errors" in stats
        assert "categories" in stats

    def test_get_file_hash(self, temp_config_file, tmp_path):
        """Test calculating file hash."""
        organizer = FileCategoryOrganizer(config_path=temp_config_file)
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        hash1 = organizer._get_file_hash(test_file)
        hash2 = organizer._get_file_hash(test_file)

        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hash length

    def test_is_duplicate(self, temp_config_file, tmp_path):
        """Test duplicate detection."""
        # Update config to enable duplicate checking
        with open(temp_config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        config["organizer"]["check_duplicates"] = True
        with open(temp_config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        organizer = FileCategoryOrganizer(config_path=temp_config_file)
        source_file = tmp_path / "source.txt"
        source_file.write_text("same content")
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        dest_file = dest_dir / "dest.txt"
        dest_file.write_text("same content")

        is_dup = organizer._is_duplicate(source_file, dest_dir)
        assert is_dup is True
