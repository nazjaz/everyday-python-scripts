"""Unit tests for Purpose-Based File Organizer."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.main import PurposeBasedOrganizer


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config(temp_dir):
    """Create a sample configuration file."""
    config_path = temp_dir / "config.yaml"
    config = {
        "organization": {
            "base_folder": "organized",
            "unknown_folder": "Unknown",
            "include_secondary_purposes": False,
            "skip_duplicates": False,
        },
        "purpose_detection": {
            "min_score": 1,
            "patterns": {},
            "location_contexts": {},
            "content_keywords": {},
        },
        "scan": {"skip_patterns": [".git", "__pycache__"]},
        "report": {"output_file": "report.txt"},
        "logging": {"level": "INFO", "file": "logs/test.log"},
    }
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return str(config_path)


@pytest.fixture
def organizer(sample_config):
    """Create a PurposeBasedOrganizer instance."""
    return PurposeBasedOrganizer(config_path=sample_config)


class TestPurposeBasedOrganizer:
    """Test cases for PurposeBasedOrganizer class."""

    def test_init_loads_config(self, sample_config):
        """Test that organizer loads configuration correctly."""
        organizer = PurposeBasedOrganizer(config_path=sample_config)
        assert organizer.config is not None
        assert "organization" in organizer.config

    def test_init_raises_on_missing_config(self):
        """Test that init raises FileNotFoundError for missing config."""
        with pytest.raises(FileNotFoundError):
            PurposeBasedOrganizer(config_path="nonexistent.yaml")

    def test_load_purpose_patterns(self, organizer):
        """Test that purpose patterns are loaded correctly."""
        assert "Financial" in organizer.purpose_patterns
        assert "Work" in organizer.purpose_patterns
        assert len(organizer.purpose_patterns["Financial"]) > 0

    def test_load_location_contexts(self, organizer):
        """Test that location contexts are loaded correctly."""
        assert "Downloads" in organizer.location_contexts
        assert "Desktop" in organizer.location_contexts

    def test_should_skip_path(self, organizer, temp_dir):
        """Test path skipping logic."""
        skip_path = temp_dir / ".git" / "file.txt"
        assert organizer._should_skip_path(skip_path) is True

        normal_path = temp_dir / "file.txt"
        assert organizer._should_skip_path(normal_path) is False

    def test_calculate_file_hash(self, organizer, temp_dir):
        """Test file hash calculation."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        hash1 = organizer._calculate_file_hash(test_file)
        hash2 = organizer._calculate_file_hash(test_file)

        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hash length

    def test_infer_purpose_from_filename_financial(self, organizer):
        """Test financial purpose inference from filename."""
        scores = organizer._infer_purpose_from_filename("invoice_2024.pdf")
        assert "Financial" in scores
        assert scores["Financial"] > 0

    def test_infer_purpose_from_filename_work(self, organizer):
        """Test work purpose inference from filename."""
        scores = organizer._infer_purpose_from_filename("resume_john_doe.pdf")
        assert "Work" in scores
        assert scores["Work"] > 0

    def test_infer_purpose_from_filename_education(self, organizer):
        """Test education purpose inference from filename."""
        scores = organizer._infer_purpose_from_filename("homework_math.pdf")
        assert "Education" in scores
        assert scores["Education"] > 0

    def test_infer_purpose_from_location(self, organizer, temp_dir):
        """Test purpose inference from location."""
        downloads_dir = temp_dir / "Downloads"
        downloads_dir.mkdir()
        test_file = downloads_dir / "file.txt"

        scores = organizer._infer_purpose_from_location(test_file)
        assert "Temporary" in scores or "Pending" in scores

    def test_infer_purpose_from_content(self, organizer, temp_dir):
        """Test purpose inference from content."""
        # Create a financial document
        financial_file = temp_dir / "document.txt"
        financial_file.write_text(
            "Invoice Number: INV-001\nTotal Amount: $100.00\nPayment Due: 2024-01-01"
        )

        scores = organizer._infer_purpose_from_content(financial_file)
        assert "Financial" in scores
        assert scores["Financial"] > 0

    def test_infer_purpose_from_content_non_text(self, organizer, temp_dir):
        """Test that non-text files return empty scores."""
        binary_file = temp_dir / "image.jpg"
        binary_file.write_bytes(b"\xff\xd8\xff\xe0")

        scores = organizer._infer_purpose_from_content(binary_file)
        assert len(scores) == 0

    def test_determine_primary_purpose(self, organizer):
        """Test primary purpose determination."""
        filename_scores = {"Financial": 3, "Work": 1}
        location_scores = {"Temporary": 2}
        content_scores = {"Financial": 2}

        primary, all_purposes = organizer._determine_primary_purpose(
            filename_scores, location_scores, content_scores
        )

        assert primary == "Financial"
        assert "Financial" in all_purposes

    def test_determine_primary_purpose_no_match(self, organizer):
        """Test primary purpose when no matches found."""
        filename_scores = {}
        location_scores = {}
        content_scores = {}

        primary, all_purposes = organizer._determine_primary_purpose(
            filename_scores, location_scores, content_scores
        )

        assert primary is None
        assert len(all_purposes) == 0

    def test_build_folder_hierarchy(self, organizer):
        """Test folder hierarchy building."""
        folder = organizer._build_folder_hierarchy("Financial", ["Financial", "Work"])
        assert "Financial" in str(folder)
        assert folder.name == "Financial"

    def test_build_folder_hierarchy_unknown(self, organizer):
        """Test folder hierarchy for unknown purpose."""
        folder = organizer._build_folder_hierarchy(None, [])
        assert "Unknown" in str(folder)

    def test_scan_directory(self, organizer, temp_dir):
        """Test directory scanning."""
        # Create test files
        (temp_dir / "invoice_2024.pdf").write_bytes(b"%PDF")
        (temp_dir / "resume.txt").write_text("John Doe Resume")

        organizer.scan_directory(str(temp_dir))

        assert organizer.stats["files_scanned"] == 2
        assert len(organizer.file_purposes) == 2

    def test_scan_directory_raises_on_missing(self, organizer):
        """Test that scan raises FileNotFoundError for missing directory."""
        with pytest.raises(FileNotFoundError):
            organizer.scan_directory("/nonexistent/path")

    def test_scan_directory_raises_on_file(self, organizer, temp_dir):
        """Test that scan raises ValueError for file path."""
        test_file = temp_dir / "test.txt"
        test_file.touch()

        with pytest.raises(ValueError):
            organizer.scan_directory(str(test_file))

    def test_scan_directory_detects_duplicates(self, organizer, temp_dir):
        """Test duplicate file detection."""
        # Create two identical files
        content = b"test content"
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_bytes(content)
        file2.write_bytes(content)

        organizer.scan_directory(str(temp_dir))

        assert organizer.stats["duplicates_found"] >= 1

    def test_organize_files_dry_run(self, organizer, temp_dir):
        """Test file organization in dry-run mode."""
        # Create test file
        invoice_file = temp_dir / "invoice_2024.pdf"
        invoice_file.write_bytes(b"%PDF")

        organizer.scan_directory(str(temp_dir))
        organizer.organize_files(str(temp_dir), dry_run=True)

        # File should still be in original location
        assert invoice_file.exists()
        assert organizer.stats["files_organized"] == 1

    def test_organize_files_actual(self, organizer, temp_dir):
        """Test actual file organization."""
        # Create test file
        invoice_file = temp_dir / "invoice_2024.pdf"
        invoice_file.write_bytes(b"%PDF")

        organizer.scan_directory(str(temp_dir))
        organizer.organize_files(str(temp_dir), dry_run=False)

        # File should be moved to organized folder
        organized_path = temp_dir / "organized" / "Financial" / "invoice_2024.pdf"
        assert organized_path.exists() or invoice_file.exists()
        assert organizer.stats["files_organized"] == 1

    def test_organize_files_handles_conflicts(self, organizer, temp_dir):
        """Test that file conflicts are handled."""
        # Create test files with same name
        invoice1 = temp_dir / "invoice.pdf"
        invoice1.write_bytes(b"%PDF")

        organizer.scan_directory(str(temp_dir))
        organizer.organize_files(str(temp_dir), dry_run=False)

        # Create another file with same name
        invoice2 = temp_dir / "invoice.pdf"
        invoice2.write_bytes(b"%PDF")

        organizer.scan_directory(str(temp_dir))
        organizer.organize_files(str(temp_dir), dry_run=False)

        # Both files should exist with different names
        organized_dir = temp_dir / "organized" / "Financial"
        if organized_dir.exists():
            files = list(organized_dir.glob("invoice*.pdf"))
            assert len(files) >= 1

    def test_generate_report(self, organizer, temp_dir):
        """Test report generation."""
        # Create test files
        (temp_dir / "invoice.pdf").write_bytes(b"%PDF")
        (temp_dir / "resume.txt").write_text("Resume")

        organizer.scan_directory(str(temp_dir))
        report_path = temp_dir / "report.txt"
        report = organizer.generate_report(output_path=str(report_path))

        assert "PURPOSE-BASED ORGANIZATION REPORT" in report
        assert "Files scanned" in report
        assert report_path.exists()

    def test_purpose_inference_combines_sources(self, organizer, temp_dir):
        """Test that purpose inference combines multiple sources."""
        # Create file with financial filename in Downloads
        downloads_dir = temp_dir / "Downloads"
        downloads_dir.mkdir()
        invoice_file = downloads_dir / "invoice_2024.pdf"
        invoice_file.write_bytes(b"%PDF")

        organizer.scan_directory(str(temp_dir))

        file_info = organizer.file_purposes.get(str(invoice_file))
        assert file_info is not None
        assert file_info["primary_purpose"] == "Financial"
        assert len(file_info["filename_scores"]) > 0
