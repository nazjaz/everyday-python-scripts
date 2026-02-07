"""Unit tests for file organizer module."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.main import FileOrganizer


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    base = tempfile.mkdtemp()
    source = Path(base) / "source"
    dest = Path(base) / "dest"
    source.mkdir(parents=True)
    dest.mkdir(parents=True)

    yield {"base": base, "source": source, "dest": dest}

    shutil.rmtree(base)


@pytest.fixture
def config_file(temp_dirs):
    """Create a temporary configuration file."""
    config = {
        "source_directory": str(temp_dirs["source"]),
        "destination_base": str(temp_dirs["dest"]),
        "categories": {
            "pictures": {
                "folder": "Pictures",
                "extensions": [".jpg", ".png"],
            },
            "documents": {
                "folder": "Documents",
                "extensions": [".pdf", ".txt"],
            },
        },
        "duplicate_detection": {
            "enabled": True,
            "method": "hash",
            "hash_algorithm": "sha256",
            "action": "skip",
        },
        "logging": {
            "level": "DEBUG",
            "file": "logs/test.log",
            "max_bytes": 1048576,
            "backup_count": 3,
        },
        "operations": {
            "create_directories": True,
            "preserve_timestamps": True,
            "dry_run": False,
        },
    }

    config_path = Path(temp_dirs["base"]) / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config_path


def test_file_organizer_initialization(config_file):
    """Test FileOrganizer initializes correctly."""
    organizer = FileOrganizer(config_path=str(config_file))
    assert organizer.source_dir.exists()
    assert organizer.dest_base.exists()


def test_file_organizer_missing_config():
    """Test FileOrganizer raises error for missing config."""
    with pytest.raises(FileNotFoundError):
        FileOrganizer(config_path="nonexistent.yaml")


def test_get_file_category(config_file):
    """Test file category detection."""
    organizer = FileOrganizer(config_path=str(config_file))

    jpg_file = Path("test.jpg")
    assert organizer._get_file_category(jpg_file) == "pictures"

    pdf_file = Path("test.pdf")
    assert organizer._get_file_category(pdf_file) == "documents"

    unknown_file = Path("test.xyz")
    assert organizer._get_file_category(unknown_file) is None


def test_organize_files_moves_files(config_file, temp_dirs):
    """Test that files are moved to correct categories."""
    organizer = FileOrganizer(config_path=str(config_file))

    # Create test files
    test_jpg = temp_dirs["source"] / "test.jpg"
    test_pdf = temp_dirs["source"] / "test.pdf"
    test_jpg.write_bytes(b"fake jpg content")
    test_pdf.write_bytes(b"fake pdf content")

    # Organize files
    stats = organizer.organize_files()

    # Verify files moved
    assert (temp_dirs["dest"] / "Pictures" / "test.jpg").exists()
    assert (temp_dirs["dest"] / "Documents" / "test.pdf").exists()
    assert stats["moved"] == 2
    assert stats["processed"] == 2


def test_duplicate_detection_skips_files(config_file, temp_dirs):
    """Test duplicate detection skips duplicate files."""
    organizer = FileOrganizer(config_path=str(config_file))

    # Create original file in destination
    dest_pictures = temp_dirs["dest"] / "Pictures"
    dest_pictures.mkdir(parents=True)
    original_file = dest_pictures / "test.jpg"
    original_file.write_bytes(b"same content")

    # Create duplicate in source
    duplicate_file = temp_dirs["source"] / "test.jpg"
    duplicate_file.write_bytes(b"same content")

    # Organize files
    stats = organizer.organize_files()

    # Verify duplicate was skipped
    assert stats["skipped_duplicates"] == 1
    assert stats["moved"] == 0


def test_dry_run_mode(config_file, temp_dirs):
    """Test dry run mode doesn't move files."""
    organizer = FileOrganizer(config_path=str(config_file))
    organizer.config["operations"]["dry_run"] = True

    test_file = temp_dirs["source"] / "test.jpg"
    test_file.write_bytes(b"test content")

    stats = organizer.organize_files()

    # File should not be moved in dry run
    assert not (temp_dirs["dest"] / "Pictures" / "test.jpg").exists()
    assert stats["moved"] == 0
    assert stats["processed"] == 1


def test_name_conflict_resolution(config_file, temp_dirs):
    """Test that name conflicts are resolved with numbering."""
    organizer = FileOrganizer(config_path=str(config_file))

    # Create existing file in destination
    dest_pictures = temp_dirs["dest"] / "Pictures"
    dest_pictures.mkdir(parents=True)
    existing_file = dest_pictures / "test.jpg"
    existing_file.write_bytes(b"existing content")

    # Create new file with same name in source
    new_file = temp_dirs["source"] / "test.jpg"
    new_file.write_bytes(b"new content")

    # Organize files
    organizer.organize_files()

    # Verify new file was renamed
    assert (temp_dirs["dest"] / "Pictures" / "test_1.jpg").exists()


def test_unknown_file_extensions_skipped(config_file, temp_dirs):
    """Test files with unknown extensions are skipped."""
    organizer = FileOrganizer(config_path=str(config_file))

    unknown_file = temp_dirs["source"] / "test.xyz"
    unknown_file.write_bytes(b"unknown content")

    stats = organizer.organize_files()

    # File should remain in source
    assert unknown_file.exists()
    assert stats["moved"] == 0
    assert stats["processed"] == 1
