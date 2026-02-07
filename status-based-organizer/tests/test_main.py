"""Unit tests for Status-Based File Organizer application."""

import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.main import StatusDetector, StatusOrganizer, load_config


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


class TestStatusDetector:
    """Test cases for StatusDetector class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return {
            "status_indicators": {
                "completed": {
                    "filename_patterns": [".*completed.*", ".*done.*"],
                    "keywords": ["completed", "done"],
                    "content_keywords": ["status: completed"],
                },
                "in_progress": {
                    "filename_patterns": [".*wip.*", ".*in.?progress.*"],
                    "keywords": ["wip", "in progress"],
                    "content_keywords": ["status: in progress"],
                },
                "draft": {
                    "filename_patterns": [".*draft.*", ".*temp.*"],
                    "keywords": ["draft", "temp"],
                    "content_keywords": ["status: draft"],
                },
                "archived": {
                    "filename_patterns": [".*archive.*", ".*old.*"],
                    "keywords": ["archive", "old"],
                    "content_keywords": ["status: archived"],
                },
            },
            "organization": {"default_status": "draft"},
        }

    @pytest.fixture
    def detector(self, config):
        """Create a StatusDetector instance."""
        return StatusDetector(config)

    def test_init(self, config):
        """Test StatusDetector initialization."""
        detector = StatusDetector(config)
        assert detector.config == config

    def test_detect_from_filename_completed(self, detector, temp_dir):
        """Test detecting completed status from filename."""
        test_file = temp_dir / "report_completed.pdf"
        test_file.write_text("content")

        status = detector.detect_from_filename(test_file)
        assert status == "completed"

        test_file2 = temp_dir / "project_done.txt"
        test_file2.write_text("content")
        status2 = detector.detect_from_filename(test_file2)
        assert status2 == "completed"

    def test_detect_from_filename_in_progress(self, detector, temp_dir):
        """Test detecting in-progress status from filename."""
        test_file = temp_dir / "document_wip.docx"
        test_file.write_text("content")

        status = detector.detect_from_filename(test_file)
        assert status == "in_progress"

    def test_detect_from_filename_draft(self, detector, temp_dir):
        """Test detecting draft status from filename."""
        test_file = temp_dir / "notes_draft.txt"
        test_file.write_text("content")

        status = detector.detect_from_filename(test_file)
        assert status == "draft"

    def test_detect_from_filename_archived(self, detector, temp_dir):
        """Test detecting archived status from filename."""
        test_file = temp_dir / "old_backup.zip"
        test_file.write_text("content")

        status = detector.detect_from_filename(test_file)
        assert status == "archived"

    def test_detect_from_metadata(self, detector, temp_dir):
        """Test detecting status from metadata."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        # Set very old modification time
        old_time = (datetime.now() - timedelta(days=400)).timestamp()
        os.utime(test_file, (old_time, old_time))

        # Enable age indicator for archived
        detector.status_config["archived"]["use_age_indicator"] = True

        status = detector.detect_from_metadata(test_file)
        assert status == "archived"

    def test_detect_from_content(self, detector, temp_dir):
        """Test detecting status from content."""
        test_file = temp_dir / "status.txt"
        test_file.write_text("This is a test file.\nStatus: completed\nEnd of file.")

        status = detector.detect_from_content(test_file)
        assert status == "completed"

    def test_detect_status(self, detector, temp_dir):
        """Test complete status detection."""
        # Test filename detection
        test_file = temp_dir / "report_final.pdf"
        test_file.write_text("content")

        status, method = detector.detect_status(test_file)
        assert status is not None
        assert method in ["filename", "metadata", "content", "default"]

        # Test default status
        test_file2 = temp_dir / "normal_file.txt"
        test_file2.write_text("content")

        status2, method2 = detector.detect_status(test_file2)
        assert status2 == "draft"  # Default status
        assert method2 == "default"


class TestStatusOrganizer:
    """Test cases for StatusOrganizer class."""

    @pytest.fixture
    def config(self, temp_dir):
        """Create a test configuration."""
        source_dir = temp_dir / "source"
        source_dir.mkdir()

        return {
            "source_directory": str(source_dir),
            "status_indicators": {
                "completed": {
                    "filename_patterns": [".*completed.*"],
                    "keywords": ["completed"],
                },
                "draft": {
                    "filename_patterns": [".*draft.*"],
                    "keywords": ["draft"],
                },
            },
            "organization": {
                "completed_directory": str(temp_dir / "completed"),
                "draft_directory": str(temp_dir / "draft"),
                "default_status": "draft",
                "check_duplicates": True,
                "skip_duplicates": True,
            },
            "filtering": {
                "exclude_directories": [".git"],
                "exclude_files": [".DS_Store"],
            },
            "logging": {"level": "INFO", "file": str(temp_dir / "test.log")},
        }

    @pytest.fixture
    def organizer(self, config):
        """Create a StatusOrganizer instance."""
        return StatusOrganizer(config)

    def test_init(self, config):
        """Test StatusOrganizer initialization."""
        organizer = StatusOrganizer(config)
        assert organizer.config == config
        assert organizer.source_dir == Path(config["source_directory"])

    def test_should_exclude_file(self, organizer):
        """Test file exclusion logic."""
        excluded = Path("/some/.DS_Store")
        assert organizer.should_exclude_file(excluded) is True

        included = Path("/some/file.txt")
        assert organizer.should_exclude_file(included) is False

    def test_should_exclude_directory(self, organizer):
        """Test directory exclusion logic."""
        excluded = Path("/some/.git")
        assert organizer.should_exclude_directory(excluded) is True

        excluded = Path("/some/completed")
        assert organizer.should_exclude_directory(excluded) is True

        included = Path("/some/normal_dir")
        assert organizer.should_exclude_directory(included) is False

    def test_get_destination_path(self, organizer, temp_dir):
        """Test destination path generation."""
        test_file = temp_dir / "test.txt"

        dest_path = organizer.get_destination_path(test_file, "completed")
        assert "completed" in str(dest_path)

        dest_path = organizer.get_destination_path(test_file, "draft")
        assert "draft" in str(dest_path)

    def test_organize_file_dry_run(self, organizer, temp_dir):
        """Test organizing file in dry-run mode."""
        source_dir = Path(organizer.source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)

        test_file = source_dir / "report_completed.pdf"
        test_file.write_text("content")

        success, status, method = organizer.organize_file(test_file, dry_run=True)
        assert success is True
        assert status == "completed"
        assert test_file.exists()  # Should still exist in dry-run

    def test_organize_file(self, organizer, temp_dir):
        """Test organizing file."""
        source_dir = Path(organizer.source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)

        test_file = source_dir / "notes_draft.txt"
        test_file.write_text("content")

        success, status, method = organizer.organize_file(test_file, dry_run=False)
        assert success is True
        assert status == "draft"
        assert not test_file.exists()  # Should be moved

        # Check destination
        dest_file = organizer.status_dirs["draft"] / "notes_draft.txt"
        assert dest_file.exists()

    def test_scan_files(self, organizer, temp_dir):
        """Test scanning files."""
        source_dir = Path(organizer.source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)

        # Create test files
        file1 = source_dir / "file1.txt"
        file1.write_text("content 1")
        file2 = source_dir / "file2.txt"
        file2.write_text("content 2")

        files = organizer.scan_files()
        assert len(files) >= 2

    def test_organize_files_dry_run(self, organizer, temp_dir):
        """Test organizing files in dry-run mode."""
        source_dir = Path(organizer.source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)

        # Create files with different status indicators
        completed_file = source_dir / "report_completed.pdf"
        completed_file.write_text("content")

        draft_file = source_dir / "notes_draft.txt"
        draft_file.write_text("content")

        results = organizer.organize_files(dry_run=True)
        assert results["scanned"] >= 2
        assert completed_file.exists()  # Should still exist in dry-run
        assert draft_file.exists()  # Should still exist in dry-run


class TestLoadConfig:
    """Test cases for load_config function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    def test_load_config_valid(self, temp_dir):
        """Test loading a valid configuration file."""
        config_file = temp_dir / "config.yaml"
        config_file.write_text(
            "source_directory: /test\nstatus_indicators:\n  completed:\n    keywords: [done]\n"
        )

        config = load_config(config_file)
        assert config["source_directory"] == "/test"
        assert "completed" in config["status_indicators"]

    def test_load_config_nonexistent(self):
        """Test loading a nonexistent configuration file."""
        nonexistent = Path("/nonexistent/config.yaml")
        with pytest.raises(FileNotFoundError):
            load_config(nonexistent)

    def test_load_config_invalid_yaml(self, temp_dir):
        """Test loading an invalid YAML file."""
        config_file = temp_dir / "config.yaml"
        config_file.write_text("invalid: yaml: content: [unclosed")

        with pytest.raises(Exception):  # yaml.YAMLError
            load_config(config_file)
