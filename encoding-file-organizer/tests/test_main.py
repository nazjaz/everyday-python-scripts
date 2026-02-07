"""Unit tests for encoding file organizer."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.main import EncodingFileOrganizer


@pytest.fixture
def temp_config_file():
    """Create temporary config file for testing."""
    config_content = """
source:
  directory: "."
  recursive: true

output:
  directory: "organized"
  preserve_structure: false

text_file:
  extensions:
    - ".txt"
    - ".py"
  check_content: true

encoding_detection:
  use_chardet: false
  sample_size: 10000
  encoding_order:
    - "utf-8"
    - "latin-1"

organization:
  dry_run: true
  encoding_naming:
    prefix: "Encoding"
    separator: "_"
    normalize_case: true
  conflicts:
    action: "rename"

skip:
  patterns: []
  directories: []
  excluded_paths: []

report:
  auto_save: false
  output_file: "logs/test_report.txt"
  show_file_list: true

logging:
  level: "DEBUG"
  file: "logs/test.log"
  max_bytes: 10485760
  backup_count: 5
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        f.write(config_content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def organizer(temp_config_file):
    """Create EncodingFileOrganizer instance for testing."""
    organizer = EncodingFileOrganizer(config_path=temp_config_file)
    yield organizer


@pytest.fixture
def temp_directory():
    """Create temporary directory with test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files with different encodings
        (temp_path / "utf8_file.txt").write_text("UTF-8 content", encoding="utf-8")
        (temp_path / "latin1_file.txt").write_text("Latin-1 content", encoding="latin-1")
        (temp_path / "ascii_file.txt").write_text("ASCII content", encoding="ascii")

        yield temp_path


class TestEncodingFileOrganizer:
    """Test cases for EncodingFileOrganizer class."""

    def test_init_loads_config(self, organizer):
        """Test that organizer loads configuration correctly."""
        assert organizer.config is not None
        assert "source" in organizer.config
        assert "encoding_detection" in organizer.config

    def test_detect_encoding_utf8(self, organizer, temp_directory):
        """Test UTF-8 encoding detection."""
        test_file = temp_directory / "utf8_file.txt"
        encoding, confidence = organizer._detect_encoding(test_file)
        
        assert encoding is not None
        assert encoding.lower() in ["utf-8", "utf8"]

    def test_detect_encoding_latin1(self, organizer, temp_directory):
        """Test Latin-1 encoding detection."""
        test_file = temp_directory / "latin1_file.txt"
        encoding, confidence = organizer._detect_encoding(test_file)
        
        assert encoding is not None

    def test_detect_encoding_nonexistent(self, organizer):
        """Test encoding detection for nonexistent file."""
        test_file = Path("/nonexistent/file.txt")
        encoding, confidence = organizer._detect_encoding(test_file)
        
        # Should handle gracefully
        assert encoding is None or confidence == 0.0

    def test_is_text_file_by_extension(self, organizer):
        """Test text file detection by extension."""
        file_path = Path("file.txt")
        assert organizer._is_text_file(file_path) is True
        
        file_path = Path("file.jpg")
        assert organizer._is_text_file(file_path) is False

    def test_is_text_file_by_content(self, organizer, temp_directory):
        """Test text file detection by content."""
        # Create a text file
        text_file = temp_directory / "test.txt"
        text_file.write_text("Text content")
        assert organizer._is_text_file(text_file) is True

    def test_get_encoding_folder_name(self, organizer):
        """Test encoding folder name generation."""
        name = organizer._get_encoding_folder_name("utf-8")
        assert name == "Encoding_UTF-8"
        
        name = organizer._get_encoding_folder_name("latin-1")
        assert name == "Encoding_LATIN-1"

    def test_get_encoding_folder_name_custom(self, organizer):
        """Test custom encoding folder naming."""
        organizer.config["organization"]["encoding_naming"]["prefix"] = "Enc"
        organizer.config["organization"]["encoding_naming"]["separator"] = "-"
        name = organizer._get_encoding_folder_name("utf-8")
        assert name == "Enc-UTF-8"

    def test_scan_files(self, organizer, temp_directory):
        """Test scanning files and grouping by encoding."""
        files_by_encoding = organizer.scan_files(directory=str(temp_directory))
        
        assert len(files_by_encoding) > 0
        assert organizer.stats["files_scanned"] >= 3
        assert organizer.stats["files_processed"] >= 3

    def test_scan_files_nonexistent_directory(self, organizer):
        """Test scanning nonexistent directory."""
        with pytest.raises(FileNotFoundError):
            organizer.scan_files(directory="/nonexistent/path")

    def test_organize_files_dry_run(self, organizer, temp_directory):
        """Test organizing files in dry-run mode."""
        files_by_encoding = organizer.scan_files(directory=str(temp_directory))
        
        stats = organizer.organize_files(files_by_encoding, dry_run=True)
        
        assert stats["files_organized"] > 0
        # Files should still exist in original location
        assert (temp_directory / "utf8_file.txt").exists()

    def test_organize_files_actual(self, organizer, temp_directory):
        """Test actual file organization."""
        files_by_encoding = organizer.scan_files(directory=str(temp_directory))
        
        stats = organizer.organize_files(files_by_encoding, dry_run=False)
        
        assert stats["files_organized"] > 0
        # Check that organized directory was created
        organized_path = temp_directory.parent / "organized"
        assert organized_path.exists()

    def test_generate_report(self, organizer, temp_directory):
        """Test report generation."""
        files_by_encoding = organizer.scan_files(directory=str(temp_directory))
        report = organizer.generate_report(files_by_encoding)
        
        assert "ENCODING FILE ORGANIZER REPORT" in report
        assert "STATISTICS" in report
        assert "FILES BY ENCODING" in report

    def test_generate_report_save_file(self, organizer, temp_directory):
        """Test saving report to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = str(Path(temp_dir) / "test_report.txt")
            files_by_encoding = organizer.scan_files(directory=str(temp_directory))
            
            report = organizer.generate_report(files_by_encoding, output_file=report_file)
            
            assert Path(report_file).exists()
            assert report is not None

    def test_print_summary(self, organizer, temp_directory, capsys):
        """Test printing summary to console."""
        files_by_encoding = organizer.scan_files(directory=str(temp_directory))
        organizer.print_summary(files_by_encoding)
        captured = capsys.readouterr()
        
        assert "ENCODING FILE ORGANIZER SUMMARY" in captured.out
        assert "Files scanned" in captured.out
        assert "Encodings found" in captured.out


class TestMainFunction:
    """Test cases for main function."""

    @patch("src.main.EncodingFileOrganizer")
    def test_main_scan_only(self, mock_organizer_class, temp_config_file):
        """Test main function with scan only."""
        mock_organizer = MagicMock()
        mock_organizer.scan_files.return_value = {"utf-8": [], "latin-1": []}
        mock_organizer.config = {"report": {"auto_save": False}}
        mock_organizer_class.return_value = mock_organizer

        from src.main import main
        import sys

        sys.argv = ["main.py", "-c", temp_config_file]
        result = main()

        assert result == 0
        mock_organizer.scan_files.assert_called_once()

    @patch("src.main.EncodingFileOrganizer")
    def test_main_with_organize(self, mock_organizer_class, temp_config_file):
        """Test main function with organize option."""
        mock_organizer = MagicMock()
        mock_organizer.scan_files.return_value = {"utf-8": [], "latin-1": []}
        mock_organizer.organize_files.return_value = {"files_organized": 5}
        mock_organizer.config = {
            "report": {"auto_save": False},
            "organization": {"dry_run": True},
        }
        mock_organizer_class.return_value = mock_organizer

        from src.main import main
        import sys

        sys.argv = ["main.py", "-c", temp_config_file, "--organize"]
        result = main()

        assert result == 0
        mock_organizer.scan_files.assert_called_once()
        mock_organizer.organize_files.assert_called_once()
