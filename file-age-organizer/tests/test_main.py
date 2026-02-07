"""Unit tests for File Age Organizer."""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import FileAgeOrganizer


@pytest.fixture
def sample_config():
    """Create sample configuration dictionary."""
    return {
        "age_thresholds": {
            "New": {"value": 1, "unit": "days"},
            "Recent": {"value": 7, "unit": "days"},
            "Old": {"value": 30, "unit": "days"},
            "Very-Old": {"value": 365, "unit": "days"},
        },
        "organizer": {
            "source_directory": ".",
            "destination_directory": "organized",
            "recursive": True,
            "handle_duplicate_names": "rename",
            "exclude": {
                "patterns": [],
                "directories": [],
                "extensions": [],
            },
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
    """Create temporary directory with test files of different ages."""
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()

    # Create very new file (just now)
    new_file = test_dir / "new.txt"
    new_file.write_text("new content")
    time.sleep(0.1)

    # Create recent file (2 days ago)
    recent_file = test_dir / "recent.txt"
    recent_file.write_text("recent content")
    recent_mtime = time.time() - (2 * 24 * 60 * 60)
    os.utime(recent_file, (recent_mtime, recent_mtime))
    time.sleep(0.1)

    # Create old file (60 days ago)
    old_file = test_dir / "old.txt"
    old_file.write_text("old content")
    old_mtime = time.time() - (60 * 24 * 60 * 60)
    os.utime(old_file, (old_mtime, old_mtime))
    time.sleep(0.1)

    # Create very old file (400 days ago)
    very_old_file = test_dir / "very_old.txt"
    very_old_file.write_text("very old content")
    very_old_mtime = time.time() - (400 * 24 * 60 * 60)
    os.utime(very_old_file, (very_old_mtime, very_old_mtime))

    return test_dir


class TestFileAgeOrganizer:
    """Test cases for FileAgeOrganizer class."""

    def test_init_loads_config(self, temp_config_file):
        """Test that initialization loads configuration file."""
        organizer = FileAgeOrganizer(config_path=temp_config_file)
        assert organizer.config is not None
        assert "age_thresholds" in organizer.config

    def test_init_raises_file_not_found(self):
        """Test that initialization raises error for missing config file."""
        with pytest.raises(FileNotFoundError):
            FileAgeOrganizer(config_path="nonexistent.yaml")

    def test_load_age_thresholds(self, temp_config_file):
        """Test loading age thresholds."""
        organizer = FileAgeOrganizer(config_path=temp_config_file)
        thresholds = organizer.age_thresholds

        assert "New" in thresholds
        assert "Recent" in thresholds
        assert "Old" in thresholds
        assert "Very-Old" in thresholds

    def test_load_age_thresholds_hours(self, temp_config_file):
        """Test loading age thresholds with hours unit."""
        # Update config
        with open(temp_config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        config["age_thresholds"]["New"] = {"value": 24, "unit": "hours"}
        with open(temp_config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        organizer = FileAgeOrganizer(config_path=temp_config_file)
        assert organizer.age_thresholds["New"] == 1.0  # 24 hours = 1 day

    def test_get_file_age_days(self, temp_config_file, tmp_path):
        """Test getting file age in days."""
        organizer = FileAgeOrganizer(config_path=temp_config_file)
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        age = organizer._get_file_age_days(test_file)
        assert age >= 0
        assert age < 1  # Should be very recent

    def test_categorize_file(self, temp_config_file, tmp_path):
        """Test categorizing file by age."""
        organizer = FileAgeOrganizer(config_path=temp_config_file)

        # Very new file
        new_file = tmp_path / "new.txt"
        new_file.write_text("new")
        category = organizer._categorize_file(new_file)
        assert category == "New"

        # Old file
        old_file = tmp_path / "old.txt"
        old_file.write_text("old")
        old_mtime = time.time() - (60 * 24 * 60 * 60)  # 60 days ago
        os.utime(old_file, (old_mtime, old_mtime))
        category = organizer._categorize_file(old_file)
        assert category in ["Old", "Very-Old"]

    def test_scan_and_categorize(self, temp_config_file, temp_directory):
        """Test scanning and categorizing files."""
        organizer = FileAgeOrganizer(config_path=temp_config_file)
        categorized = organizer.scan_and_categorize(str(temp_directory))

        assert isinstance(categorized, dict)
        assert organizer.stats["files_scanned"] > 0

        # Check that files are categorized
        total_categorized = sum(len(files) for files in categorized.values())
        assert total_categorized > 0

    def test_organize_files_move(self, temp_config_file, temp_directory, tmp_path):
        """Test organizing files by moving."""
        organizer = FileAgeOrganizer(config_path=temp_config_file)
        dest_dir = tmp_path / "organized"

        stats = organizer.organize_files(
            source_directory=str(temp_directory),
            destination_directory=str(dest_dir),
            action="move",
        )

        assert stats["files_organized"] > 0
        assert dest_dir.exists()

        # Check category directories exist
        for category in organizer.age_thresholds.keys():
            category_dir = dest_dir / category
            if stats["categories"].get(category, 0) > 0:
                assert category_dir.exists()

    def test_organize_files_copy(self, temp_config_file, temp_directory, tmp_path):
        """Test organizing files by copying."""
        organizer = FileAgeOrganizer(config_path=temp_config_file)
        dest_dir = tmp_path / "organized"

        stats = organizer.organize_files(
            source_directory=str(temp_directory),
            destination_directory=str(dest_dir),
            action="copy",
        )

        assert stats["files_organized"] > 0
        # Original files should still exist
        assert (temp_directory / "new.txt").exists()

    def test_organize_files_invalid_action(self, temp_config_file):
        """Test that invalid action raises error."""
        organizer = FileAgeOrganizer(config_path=temp_config_file)
        with pytest.raises(ValueError):
            organizer.organize_files(action="invalid")

    def test_is_excluded_by_directory(self, temp_config_file):
        """Test directory exclusion."""
        organizer = FileAgeOrganizer(config_path=temp_config_file)
        organizer.config["organizer"]["exclude"]["directories"] = [".git"]

        excluded_file = Path("/path/.git/config")
        assert organizer._is_excluded(excluded_file) is True

        normal_file = Path("/path/file.txt")
        assert organizer._is_excluded(normal_file) is False

    def test_generate_report(self, temp_config_file, temp_directory, tmp_path):
        """Test generating report."""
        organizer = FileAgeOrganizer(config_path=temp_config_file)
        organizer.scan_and_categorize(str(temp_directory))

        report_file = tmp_path / "report.txt"
        report_content = organizer.generate_report(str(report_file))

        assert len(report_content) > 0
        assert "File Age Organization Report" in report_content
        assert report_file.exists()

    def test_get_statistics(self, temp_config_file):
        """Test getting statistics."""
        organizer = FileAgeOrganizer(config_path=temp_config_file)
        stats = organizer.get_statistics()

        assert "files_scanned" in stats
        assert "files_organized" in stats
        assert "files_skipped" in stats
        assert "errors" in stats
        assert "categories" in stats
