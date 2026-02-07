"""Unit tests for Content Type Organizer."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.main import ContentTypeOrganizer


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
            "mime_mappings": {},
        },
        "content_detection": {"magic_numbers": {}},
        "scan": {"skip_patterns": [".git", "__pycache__"]},
        "report": {"output_file": "report.txt"},
        "logging": {"level": "INFO", "file": "logs/test.log"},
    }
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return str(config_path)


@pytest.fixture
def organizer(sample_config):
    """Create a ContentTypeOrganizer instance."""
    return ContentTypeOrganizer(config_path=sample_config)


class TestContentTypeOrganizer:
    """Test cases for ContentTypeOrganizer class."""

    def test_init_loads_config(self, sample_config):
        """Test that organizer loads configuration correctly."""
        organizer = ContentTypeOrganizer(config_path=sample_config)
        assert organizer.config is not None
        assert "organization" in organizer.config

    def test_init_raises_on_missing_config(self):
        """Test that init raises FileNotFoundError for missing config."""
        with pytest.raises(FileNotFoundError):
            ContentTypeOrganizer(config_path="nonexistent.yaml")

    def test_load_magic_numbers(self, organizer):
        """Test that magic numbers are loaded correctly."""
        assert "application/pdf" in organizer.magic_numbers
        assert b"%PDF" in organizer.magic_numbers["application/pdf"]

    def test_load_mime_mappings(self, organizer):
        """Test that MIME mappings are loaded correctly."""
        assert "image/jpeg" in organizer.mime_mappings
        assert organizer.mime_mappings["image/jpeg"] == "Images"

    def test_get_folder_for_mime(self, organizer):
        """Test folder name retrieval for MIME types."""
        assert organizer._get_folder_for_mime("image/jpeg") == "Images"
        assert organizer._get_folder_for_mime("video/mp4") == "Videos"
        assert organizer._get_folder_for_mime("audio/mpeg") == "Music"
        assert organizer._get_folder_for_mime(None) == "Unknown"

    def test_should_skip_path(self, organizer, temp_dir):
        """Test path skipping logic."""
        skip_path = temp_dir / ".git" / "file.txt"
        assert organizer._should_skip_path(skip_path) is True

        normal_path = temp_dir / "file.txt"
        assert organizer._should_skip_path(normal_path) is False

    def test_detect_mime_by_magic_number_pdf(self, organizer, temp_dir):
        """Test PDF detection by magic number."""
        pdf_file = temp_dir / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        mime_type = organizer._detect_mime_by_magic_number(pdf_file)
        assert mime_type == "application/pdf"

    def test_detect_mime_by_magic_number_png(self, organizer, temp_dir):
        """Test PNG detection by magic number."""
        png_file = temp_dir / "test.png"
        png_file.write_bytes(b"\x89PNG\r\n\x1a\n")

        mime_type = organizer._detect_mime_by_magic_number(png_file)
        assert mime_type == "image/png"

    def test_detect_mime_by_magic_number_jpeg(self, organizer, temp_dir):
        """Test JPEG detection by magic number."""
        jpeg_file = temp_dir / "test.jpg"
        jpeg_file.write_bytes(b"\xff\xd8\xff\xe0")

        mime_type = organizer._detect_mime_by_magic_number(jpeg_file)
        assert mime_type == "image/jpeg"

    def test_detect_mime_by_extension(self, organizer, temp_dir):
        """Test MIME detection by file extension."""
        pdf_file = temp_dir / "test.pdf"
        pdf_file.touch()

        mime_type = organizer._detect_mime_by_extension(pdf_file)
        assert mime_type == "application/pdf"

    def test_detect_content_type_with_magic_number(self, organizer, temp_dir):
        """Test content type detection using magic numbers."""
        pdf_file = temp_dir / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        mime_type, method = organizer._detect_content_type(pdf_file)
        assert mime_type == "application/pdf"
        assert method in ["magic_number", "python-magic", "extension"]

    def test_detect_content_type_unknown(self, organizer, temp_dir):
        """Test content type detection for unknown file."""
        unknown_file = temp_dir / "test.unknown"
        unknown_file.write_bytes(b"random content")

        mime_type, method = organizer._detect_content_type(unknown_file)
        assert mime_type is None or method == "unknown"

    def test_scan_directory(self, organizer, temp_dir):
        """Test directory scanning."""
        # Create test files
        (temp_dir / "test1.pdf").write_bytes(b"%PDF-1.4\n")
        (temp_dir / "test2.txt").write_text("Hello World")

        organizer.scan_directory(str(temp_dir))

        assert organizer.stats["files_scanned"] == 2
        assert len(organizer.file_types) == 2

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

    def test_organize_files_dry_run(self, organizer, temp_dir):
        """Test file organization in dry-run mode."""
        # Create test files
        pdf_file = temp_dir / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        organizer.scan_directory(str(temp_dir))
        organizer.organize_files(str(temp_dir), dry_run=True)

        # File should still be in original location
        assert pdf_file.exists()
        assert organizer.stats["files_organized"] == 1

    def test_organize_files_actual(self, organizer, temp_dir):
        """Test actual file organization."""
        # Create test files
        pdf_file = temp_dir / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        organizer.scan_directory(str(temp_dir))
        organizer.organize_files(str(temp_dir), dry_run=False)

        # File should be moved to organized folder
        organized_path = temp_dir / "organized" / "Documents" / "test.pdf"
        assert organized_path.exists()
        assert not pdf_file.exists()
        assert organizer.stats["files_organized"] == 1

    def test_organize_files_handles_conflicts(self, organizer, temp_dir):
        """Test that file conflicts are handled."""
        # Create test files with same name
        pdf1 = temp_dir / "test.pdf"
        pdf1.write_bytes(b"%PDF-1.4\n")

        organizer.scan_directory(str(temp_dir))
        organizer.organize_files(str(temp_dir), dry_run=False)

        # Create another file with same name
        pdf2 = temp_dir / "test.pdf"
        pdf2.write_bytes(b"%PDF-1.4\n")

        organizer.scan_directory(str(temp_dir))
        organizer.organize_files(str(temp_dir), dry_run=False)

        # Both files should exist with different names
        organized_dir = temp_dir / "organized" / "Documents"
        files = list(organized_dir.glob("test*.pdf"))
        assert len(files) >= 2

    def test_generate_report(self, organizer, temp_dir):
        """Test report generation."""
        # Create test files
        (temp_dir / "test.pdf").write_bytes(b"%PDF-1.4\n")
        (temp_dir / "test.txt").write_text("Hello")

        organizer.scan_directory(str(temp_dir))
        report_path = temp_dir / "report.txt"
        report = organizer.generate_report(output_path=str(report_path))

        assert "CONTENT TYPE ORGANIZATION REPORT" in report
        assert "Files scanned" in report
        assert report_path.exists()

    def test_extension_mismatch_detection(self, organizer, temp_dir):
        """Test detection of extension mismatches."""
        # Create a PDF file with .txt extension
        fake_txt = temp_dir / "fake.txt"
        fake_txt.write_bytes(b"%PDF-1.4\n")

        organizer.scan_directory(str(temp_dir))

        file_info = organizer.file_types.get(str(fake_txt))
        assert file_info is not None
        assert file_info["extension_mismatch"] is True
        assert organizer.stats["extension_mismatches"] == 1

    @patch("src.main.HAS_MAGIC", True)
    @patch("src.main.magic.Magic")
    def test_python_magic_detection(self, mock_magic_class, organizer, temp_dir):
        """Test python-magic library integration."""
        mock_magic = MagicMock()
        mock_magic.from_file.return_value = "application/pdf"
        mock_magic_class.return_value = mock_magic

        pdf_file = temp_dir / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        mime_type = organizer._detect_mime_by_python_magic(pdf_file)
        assert mime_type == "application/pdf"
        mock_magic.from_file.assert_called_once()
