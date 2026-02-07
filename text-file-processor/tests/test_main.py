"""Unit tests for text file processor."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.main import TextFileProcessor


@pytest.fixture
def temp_config_file():
    """Create temporary config file for testing."""
    config_content = """
input:
  directory: "."
  recursive: true

output:
  in_place: true
  directory: "processed"

processing:
  encoding_detection_order:
    - "utf-8"
    - "latin-1"
  line_ending: "unix"
  remove_trailing_whitespace: true
  remove_leading_whitespace: false
  normalize_spaces: true
  remove_empty_lines: false
  remove_trailing_newlines: false

include:
  extensions: []
  include_no_extension: true

skip:
  patterns: []
  directories: []

backup:
  enabled: false
  directory: "backups"

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
def processor(temp_config_file):
    """Create TextFileProcessor instance for testing."""
    processor = TextFileProcessor(config_path=temp_config_file)
    yield processor


@pytest.fixture
def temp_text_file():
    """Create temporary text file for testing."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write("Test content with   multiple   spaces\n")
        f.write("Line with trailing spaces   \n")
        f.write("\n")
        f.write("  Line with leading spaces\n")
        temp_path = f.name

    yield Path(temp_path)

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


class TestTextFileProcessor:
    """Test cases for TextFileProcessor class."""

    def test_init_loads_config(self, processor):
        """Test that processor loads configuration correctly."""
        assert processor.config is not None
        assert "input" in processor.config
        assert "processing" in processor.config

    def test_normalize_line_endings_unix(self, processor):
        """Test line ending normalization to Unix format."""
        processor.config["processing"]["line_ending"] = "unix"
        text = "Line 1\r\nLine 2\r\nLine 3"
        result = processor._normalize_line_endings(text)
        assert result == "Line 1\nLine 2\nLine 3"
        assert "\r" not in result

    def test_normalize_line_endings_windows(self, processor):
        """Test line ending normalization to Windows format."""
        processor.config["processing"]["line_ending"] = "windows"
        text = "Line 1\nLine 2\nLine 3"
        result = processor._normalize_line_endings(text)
        assert result == "Line 1\r\nLine 2\r\nLine 3"

    def test_normalize_line_endings_mac(self, processor):
        """Test line ending normalization to Mac format."""
        processor.config["processing"]["line_ending"] = "mac"
        text = "Line 1\nLine 2\nLine 3"
        result = processor._normalize_line_endings(text)
        assert result == "Line 1\rLine 2\rLine 3"

    def test_remove_extra_whitespace_trailing(self, processor):
        """Test removal of trailing whitespace."""
        processor.config["processing"]["remove_trailing_whitespace"] = True
        text = "Line 1   \nLine 2\t\nLine 3"
        result = processor._remove_extra_whitespace(text)
        assert result == "Line 1\nLine 2\nLine 3"

    def test_remove_extra_whitespace_leading(self, processor):
        """Test removal of leading whitespace."""
        processor.config["processing"]["remove_leading_whitespace"] = True
        text = "  Line 1\n\tLine 2\nLine 3"
        result = processor._remove_extra_whitespace(text)
        assert result == "Line 1\nLine 2\nLine 3"

    def test_remove_extra_whitespace_normalize_spaces(self, processor):
        """Test normalization of multiple spaces."""
        processor.config["processing"]["normalize_spaces"] = True
        text = "Line 1   with    multiple     spaces"
        result = processor._remove_extra_whitespace(text)
        assert "   " not in result
        assert "    " not in result

    def test_remove_extra_whitespace_empty_lines(self, processor):
        """Test removal of empty lines."""
        processor.config["processing"]["remove_empty_lines"] = True
        text = "Line 1\n\n\nLine 2\n\nLine 3"
        result = processor._remove_extra_whitespace(text)
        assert "\n\n" not in result

    def test_should_process_file_with_extensions(self, processor):
        """Test file processing check with extension filter."""
        processor.config["include"]["extensions"] = [".txt", ".md"]
        
        assert processor._should_process_file(Path("file.txt")) is True
        assert processor._should_process_file(Path("file.md")) is True
        assert processor._should_process_file(Path("file.py")) is False

    def test_should_process_file_no_extensions(self, processor):
        """Test file processing check without extension filter."""
        processor.config["include"]["extensions"] = []
        
        # Should process common text file extensions
        assert processor._should_process_file(Path("file.txt")) is True
        assert processor._should_process_file(Path("file.md")) is True
        assert processor._should_process_file(Path("file.py")) is True

    def test_should_skip_path_pattern(self, processor):
        """Test skip pattern matching."""
        processor.config["skip"]["patterns"] = [".git", "node_modules"]
        
        assert processor._should_skip_path(Path("/path/.git/config")) is True
        assert processor._should_skip_path(Path("/path/node_modules/package")) is True
        assert processor._should_skip_path(Path("/path/normal/file.txt")) is False

    def test_detect_encoding_utf8(self, processor):
        """Test encoding detection for UTF-8 file."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            content = "Test content with émojis 🎉".encode("utf-8")
            f.write(content)
            temp_path = f.name

        try:
            encoding, content_bytes = processor._detect_encoding(Path(temp_path))
            assert encoding == "utf-8"
            assert content_bytes == content
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_process_file_success(self, processor, temp_text_file):
        """Test successful file processing."""
        processor.config["backup"]["enabled"] = False
        
        result = processor.process_file(temp_text_file)
        
        assert result is True
        assert processor.stats["files_processed"] == 1
        
        # Verify file was processed
        with open(temp_text_file, "rb") as f:
            content = f.read()
            assert content.decode("utf-8") is not None

    def test_process_file_nonexistent(self, processor):
        """Test processing nonexistent file."""
        result = processor.process_file(Path("/nonexistent/file.txt"))
        assert result is False
        assert processor.stats["files_failed"] > 0

    def test_process_file_skip_extension(self, processor):
        """Test skipping file based on extension."""
        import tempfile
        processor.config["include"]["extensions"] = [".txt"]
        
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            result = processor.process_file(temp_path)
            assert processor.stats["files_skipped"] > 0
        finally:
            temp_path.unlink(missing_ok=True)

    def test_process_directory(self, processor, tempfile):
        """Test processing directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "file1.txt").write_text("Content 1")
            (temp_path / "file2.txt").write_text("Content 2")
            
            processor.config["backup"]["enabled"] = False
            stats = processor.process_directory(directory=str(temp_path))
            
            assert stats["files_processed"] >= 2

    def test_process_directory_nonexistent(self, processor):
        """Test processing nonexistent directory."""
        with pytest.raises(FileNotFoundError):
            processor.process_directory(directory="/nonexistent/directory")

    def test_process_directory_not_directory(self, processor):
        """Test processing path that is not a directory."""
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            with pytest.raises(NotADirectoryError):
                processor.process_directory(directory=temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_backup_file(self, processor, temp_text_file):
        """Test backup file creation."""
        processor.config["backup"]["enabled"] = True
        
        backup_path = processor._backup_file(temp_text_file)
        
        if backup_path:
            assert backup_path.exists()
            backup_path.unlink(missing_ok=True)

    def test_backup_file_disabled(self, processor, temp_text_file):
        """Test backup file creation when disabled."""
        processor.config["backup"]["enabled"] = False
        
        backup_path = processor._backup_file(temp_text_file)
        
        assert backup_path is None

    def test_print_summary(self, processor, capsys):
        """Test printing summary to console."""
        processor.stats = {
            "files_processed": 10,
            "files_skipped": 2,
            "files_failed": 1,
            "bytes_processed": 1000,
            "bytes_saved": 100,
        }
        
        processor.print_summary()
        captured = capsys.readouterr()
        
        assert "TEXT FILE PROCESSOR SUMMARY" in captured.out
        assert "Files processed: 10" in captured.out


class TestMainFunction:
    """Test cases for main function."""

    @patch("src.main.TextFileProcessor")
    def test_main_process_directory(self, mock_processor_class, temp_config_file):
        """Test main function processing directory."""
        mock_processor = MagicMock()
        mock_processor.process_directory.return_value = {
            "files_processed": 5,
            "files_skipped": 1,
            "files_failed": 0,
        }
        mock_processor.config = {"backup": {"enabled": True}}
        mock_processor_class.return_value = mock_processor

        from src.main import main
        import sys

        sys.argv = ["main.py", "-c", temp_config_file, "-d", "/test/dir"]
        result = main()

        assert result == 0
        mock_processor.process_directory.assert_called_with(directory="/test/dir")

    @patch("src.main.TextFileProcessor")
    def test_main_process_file(self, mock_processor_class, temp_config_file):
        """Test main function processing single file."""
        mock_processor = MagicMock()
        mock_processor.process_file.return_value = True
        mock_processor.config = {"backup": {"enabled": True}}
        mock_processor_class.return_value = mock_processor

        from src.main import main
        import sys

        sys.argv = ["main.py", "-c", temp_config_file, "-f", "/test/file.txt"]
        result = main()

        assert result == 0
        mock_processor.process_file.assert_called_once()
