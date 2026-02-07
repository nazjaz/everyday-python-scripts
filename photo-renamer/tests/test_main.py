"""Unit tests for photo renamer module."""

import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from PIL import Image
from PIL.ExifTags import TAGS

from src.main import PhotoRenamer


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    return tempfile.mkdtemp()


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary configuration file."""
    config = {
        "source_directory": temp_dir,
        "supported_formats": [".jpg", ".jpeg", ".png"],
        "naming": {
            "date_format": "%Y-%m-%d",
            "time_format": "%H-%M-%S",
            "preserve_extension": True,
        },
        "exif_date_fields": ["DateTimeOriginal", "DateTimeDigitized", "DateTime"],
        "sequential_numbering": {
            "enabled": True,
            "start_number": 1,
            "padding": 3,
        },
        "fallback": {
            "use_file_modification_date": True,
            "use_file_creation_date": False,
            "skip_if_no_date": False,
            "prefix": "NO_DATE_",
        },
        "operations": {
            "dry_run": False,
            "create_backup": False,
            "preserve_timestamps": True,
        },
        "logging": {
            "level": "DEBUG",
            "file": f"{temp_dir}/test.log",
            "max_bytes": 1048576,
            "backup_count": 3,
        },
    }

    config_path = Path(temp_dir) / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config_path


def test_photo_renamer_initialization(config_file):
    """Test PhotoRenamer initializes correctly."""
    renamer = PhotoRenamer(config_path=str(config_file))
    assert renamer.source_dir.exists()
    assert renamer.stats["processed"] == 0


def test_photo_renamer_missing_config():
    """Test PhotoRenamer raises error for missing config."""
    with pytest.raises(FileNotFoundError):
        PhotoRenamer(config_path="nonexistent.yaml")


def test_parse_exif_date(config_file):
    """Test EXIF date parsing."""
    renamer = PhotoRenamer(config_path=str(config_file))

    # Valid EXIF date format
    date_str = "2024:02:07 14:30:45"
    parsed = renamer._parse_exif_date(date_str)
    assert parsed is not None
    assert parsed.year == 2024
    assert parsed.month == 2
    assert parsed.day == 7
    assert parsed.hour == 14
    assert parsed.minute == 30
    assert parsed.second == 45

    # Invalid date format
    invalid_date = "invalid-date"
    assert renamer._parse_exif_date(invalid_date) is None


def test_generate_new_filename(config_file):
    """Test filename generation."""
    renamer = PhotoRenamer(config_path=str(config_file))
    image_path = Path("test_photo.jpg")
    date_taken = datetime(2024, 2, 7, 14, 30, 45)

    # Without counter
    new_name = renamer._generate_new_filename(image_path, date_taken)
    assert new_name == "2024-02-07_14-30-45_test_photo.jpg"

    # With counter
    new_name = renamer._generate_new_filename(image_path, date_taken, counter=5)
    assert new_name == "2024-02-07_14-30-45_005_test_photo.jpg"


def test_get_timestamp_key(config_file):
    """Test timestamp key generation."""
    renamer = PhotoRenamer(config_path=str(config_file))
    date_taken = datetime(2024, 2, 7, 14, 30, 45)

    key = renamer._get_timestamp_key(date_taken)
    assert key == "2024-02-07_14-30-45"


def test_get_next_counter(config_file):
    """Test sequential counter functionality."""
    renamer = PhotoRenamer(config_path=str(config_file))

    # First call should return start number
    counter1 = renamer._get_next_counter("2024-02-07_14-30-45")
    assert counter1 == 1

    # Second call should increment
    counter2 = renamer._get_next_counter("2024-02-07_14-30-45")
    assert counter2 == 2

    # Different timestamp should start from beginning
    counter3 = renamer._get_next_counter("2024-02-07_15-00-00")
    assert counter3 == 1


@patch("src.main.Image.open")
def test_get_exif_data(mock_image_open, config_file):
    """Test EXIF data extraction."""
    # Create mock image with EXIF data
    mock_img = MagicMock()
    mock_exif = MagicMock()
    mock_exif.items.return_value = [
        (306, "2024:02:07 14:30:45"),  # DateTime tag
    ]
    mock_img.getexif.return_value = mock_exif
    mock_image_open.return_value.__enter__.return_value = mock_img

    renamer = PhotoRenamer(config_path=str(config_file))
    image_path = Path("test.jpg")

    exif_data = renamer._get_exif_data(image_path)
    assert exif_data is not None
    assert "DateTime" in exif_data


@patch("src.main.PhotoRenamer._get_exif_data")
def test_get_date_taken_from_exif(mock_get_exif, config_file):
    """Test getting date taken from EXIF."""
    mock_get_exif.return_value = {
        "DateTimeOriginal": "2024:02:07 14:30:45",
    }

    renamer = PhotoRenamer(config_path=str(config_file))
    image_path = Path("test.jpg")

    date_taken = renamer._get_date_taken(image_path)
    assert date_taken is not None
    assert date_taken.year == 2024


@patch("src.main.PhotoRenamer._get_exif_data")
def test_get_date_taken_fallback(mock_get_exif, config_file, temp_dir):
    """Test fallback to file modification date."""
    mock_get_exif.return_value = None

    renamer = PhotoRenamer(config_path=str(config_file))
    test_file = Path(temp_dir) / "test.jpg"
    test_file.touch()

    date_taken = renamer._get_date_taken(test_file)
    assert date_taken is not None


def test_rename_photos_dry_run(config_file, temp_dir):
    """Test photo renaming in dry run mode."""
    renamer = PhotoRenamer(config_path=str(config_file))
    renamer.config["operations"]["dry_run"] = True

    # Create test image file
    test_image = Path(temp_dir) / "test_photo.jpg"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(test_image)

    # Set modification time
    import time
    test_time = time.mktime(datetime(2024, 2, 7, 14, 30, 45).timetuple())
    os.utime(test_image, (test_time, test_time))

    stats = renamer.rename_photos()

    # File should not be renamed in dry run
    assert test_image.exists()
    assert stats["processed"] == 1


def test_sequential_numbering(config_file, temp_dir):
    """Test sequential numbering for same timestamp."""
    renamer = PhotoRenamer(config_path=str(config_file))
    renamer.config["operations"]["dry_run"] = True

    # Create multiple test images with same modification time
    test_time = time.mktime(datetime(2024, 2, 7, 14, 30, 45).timetuple())
    for i in range(3):
        test_image = Path(temp_dir) / f"photo_{i}.jpg"
        img = Image.new("RGB", (100, 100), color="red")
        img.save(test_image)
        os.utime(test_image, (test_time, test_time))

    stats = renamer.rename_photos()

    assert stats["processed"] == 3
    # All should be processed (dry run doesn't actually rename)
