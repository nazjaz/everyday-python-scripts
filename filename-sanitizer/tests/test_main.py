"""Unit tests for filename sanitizer."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.main import FilenameSanitizer


@pytest.fixture
def temp_config_file():
    """Create temporary config file for testing."""
    config_content = """
scan:
  directory: "."
  recursive: true

sanitization:
  remove_spaces: true
  remove_consecutive: true
  remove_leading_trailing: true
  max_length: null
  problematic_chars:
    - "<"
    - ">"
    - ":"
    - "/"
    - "\\"
    - "|"
    - "?"
    - "*"
  reserved_names:
    - "CON"
    - "PRN"

replacement:
  space_replacement: "_"
  char_replacement: "_"
  consecutive_replacement: "_"

renaming:
  dry_run: true
  conflicts:
    action: "rename"

include:
  extensions: []
  include_no_extension: true

skip:
  patterns: []
  directories: []
  excluded_paths: []

report:
  auto_save: false
  output_file: "logs/test_report.txt"

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
def sanitizer(temp_config_file):
    """Create FilenameSanitizer instance for testing."""
    sanitizer = FilenameSanitizer(config_path=temp_config_file)
    yield sanitizer


@pytest.fixture
def temp_directory():
    """Create temporary directory with test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files with problematic names
        (temp_path / "normal_file.txt").write_text("normal")
        (temp_path / "file with spaces.txt").write_text("spaces")
        (temp_path / "file:with:colons.txt").write_text("colons")
        (temp_path / "file<>special.txt").write_text("special")
        (temp_path / "CON.txt").write_text("reserved")

        yield temp_path


class TestFilenameSanitizer:
    """Test cases for FilenameSanitizer class."""

    def test_init_loads_config(self, sanitizer):
        """Test that sanitizer loads configuration correctly."""
        assert sanitizer.config is not None
        assert "scan" in sanitizer.config
        assert "sanitization" in sanitizer.config

    def test_has_problematic_characters_spaces(self, sanitizer):
        """Test detection of spaces in filename."""
        has_issues, issues = sanitizer._has_problematic_characters("file with spaces.txt")
        assert has_issues is True
        assert "contains_spaces" in issues

    def test_has_problematic_characters_special(self, sanitizer):
        """Test detection of special characters."""
        has_issues, issues = sanitizer._has_problematic_characters("file:name.txt")
        assert has_issues is True

    def test_has_problematic_characters_reserved(self, sanitizer):
        """Test detection of reserved names."""
        has_issues, issues = sanitizer._has_problematic_characters("CON.txt")
        assert has_issues is True
        assert "reserved_name" in issues

    def test_has_problematic_characters_normal(self, sanitizer):
        """Test that normal filenames are not problematic."""
        has_issues, issues = sanitizer._has_problematic_characters("normal_file.txt")
        assert has_issues is False

    def test_sanitize_filename_spaces(self, sanitizer):
        """Test sanitizing filename with spaces."""
        result = sanitizer._sanitize_filename("file with spaces.txt")
        assert " " not in result
        assert "_" in result

    def test_sanitize_filename_special_chars(self, sanitizer):
        """Test sanitizing filename with special characters."""
        result = sanitizer._sanitize_filename("file:name.txt")
        assert ":" not in result
        assert "_" in result

    def test_sanitize_filename_reserved(self, sanitizer):
        """Test sanitizing reserved name."""
        result = sanitizer._sanitize_filename("CON.txt")
        assert result.startswith("_")

    def test_sanitize_filename_preserves_extension(self, sanitizer):
        """Test that file extension is preserved."""
        result = sanitizer._sanitize_filename("file name.txt")
        assert result.endswith(".txt")

    def test_sanitize_filename_normal(self, sanitizer):
        """Test that normal filenames are unchanged."""
        result = sanitizer._sanitize_filename("normal_file.txt")
        assert result == "normal_file.txt"

    def test_find_problematic_files(self, sanitizer, temp_directory):
        """Test finding problematic files."""
        files = sanitizer.find_problematic_files(directory=str(temp_directory))
        
        assert len(files) >= 4  # Should find files with spaces, colons, special chars, reserved
        assert sanitizer.stats["files_scanned"] >= 5
        assert sanitizer.stats["files_found"] >= 4

    def test_find_problematic_files_nonexistent_directory(self, sanitizer):
        """Test finding files in nonexistent directory."""
        with pytest.raises(FileNotFoundError):
            sanitizer.find_problematic_files(directory="/nonexistent/path")

    def test_rename_file_dry_run(self, sanitizer, temp_directory):
        """Test file renaming in dry-run mode."""
        test_file = temp_directory / "file with spaces.txt"
        new_name = "file_with_spaces.txt"
        
        result = sanitizer.rename_file(test_file, new_name, dry_run=True)
        
        assert result is True
        assert test_file.exists()  # File should still exist with original name

    def test_rename_file_actual(self, sanitizer, temp_directory):
        """Test actual file renaming."""
        test_file = temp_directory / "file with spaces.txt"
        new_name = "file_with_spaces.txt"
        
        result = sanitizer.rename_file(test_file, new_name, dry_run=False)
        
        assert result is True
        assert not test_file.exists()  # Original file should not exist
        assert (temp_directory / new_name).exists()  # New file should exist

    def test_rename_file_conflict_skip(self, sanitizer, temp_directory):
        """Test file renaming with conflict (skip action)."""
        test_file = temp_directory / "normal_file.txt"
        new_name = "normal_file.txt"  # Same name
        
        sanitizer.config["renaming"]["conflicts"]["action"] = "skip"
        result = sanitizer.rename_file(test_file, new_name, dry_run=False)
        
        # Should skip if name is the same
        assert result is True

    def test_rename_files(self, sanitizer, temp_directory):
        """Test renaming multiple files."""
        files = sanitizer.find_problematic_files(directory=str(temp_directory))
        
        stats = sanitizer.rename_files(files, dry_run=True)
        
        assert stats["files_renamed"] > 0

    def test_generate_report(self, sanitizer, temp_directory):
        """Test report generation."""
        files = sanitizer.find_problematic_files(directory=str(temp_directory))
        report = sanitizer.generate_report(files)
        
        assert "FILENAME SANITIZER REPORT" in report
        assert "STATISTICS" in report
        assert "PROBLEMATIC FILES" in report

    def test_generate_report_save_file(self, sanitizer, temp_directory):
        """Test saving report to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = str(Path(temp_dir) / "test_report.txt")
            files = sanitizer.find_problematic_files(directory=str(temp_directory))
            
            report = sanitizer.generate_report(files, output_file=report_file)
            
            assert Path(report_file).exists()
            assert report is not None

    def test_print_summary(self, sanitizer, temp_directory, capsys):
        """Test printing summary to console."""
        sanitizer.find_problematic_files(directory=str(temp_directory))
        sanitizer.print_summary()
        captured = capsys.readouterr()
        
        assert "FILENAME SANITIZER SUMMARY" in captured.out
        assert "Files scanned" in captured.out


class TestMainFunction:
    """Test cases for main function."""

    @patch("src.main.FilenameSanitizer")
    def test_main_find_only(self, mock_sanitizer_class, temp_config_file):
        """Test main function with find only."""
        mock_sanitizer = MagicMock()
        mock_sanitizer.find_problematic_files.return_value = []
        mock_sanitizer.config = {"report": {"auto_save": False}}
        mock_sanitizer_class.return_value = mock_sanitizer

        from src.main import main
        import sys

        sys.argv = ["main.py", "-c", temp_config_file]
        result = main()

        assert result == 0
        mock_sanitizer.find_problematic_files.assert_called_once()

    @patch("src.main.FilenameSanitizer")
    def test_main_with_rename(self, mock_sanitizer_class, temp_config_file):
        """Test main function with rename option."""
        mock_sanitizer = MagicMock()
        mock_sanitizer.find_problematic_files.return_value = [
            {"path": "/test/file.txt", "original_name": "file name.txt", "sanitized_name": "file_name.txt", "needs_rename": True}
        ]
        mock_sanitizer.rename_files.return_value = {"files_renamed": 1, "files_skipped": 0, "errors": 0}
        mock_sanitizer.config = {"report": {"auto_save": False}, "renaming": {"dry_run": True}}
        mock_sanitizer_class.return_value = mock_sanitizer

        from src.main import main
        import sys

        sys.argv = ["main.py", "-c", temp_config_file, "--rename"]
        result = main()

        assert result == 0
        mock_sanitizer.find_problematic_files.assert_called_once()
        mock_sanitizer.rename_files.assert_called_once()
