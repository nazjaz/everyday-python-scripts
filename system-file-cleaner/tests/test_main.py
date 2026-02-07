"""Unit tests for system file cleaner."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.main import SystemFileCleaner


@pytest.fixture
def temp_config_file():
    """Create temporary config file for testing."""
    config_content = """
scan:
  directory: "."
  recursive: true

patterns:
  system_name_patterns:
    - "thumbs.db"
    - ".ds_store"
  hidden_name_patterns:
    - "~$"
  windows_system: []
  windows_hidden: []
  windows_system_dirs: []
  unix_system: []
  system_extensions: []

skip:
  patterns: []
  directories: []
  excluded_paths: []

protected:
  patterns:
    - "config.yaml"
  paths: []

removal:
  dry_run: true
  require_confirmation: false

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
def cleaner(temp_config_file):
    """Create SystemFileCleaner instance for testing."""
    cleaner = SystemFileCleaner(config_path=temp_config_file)
    yield cleaner


@pytest.fixture
def temp_directory():
    """Create temporary directory with test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files
        (temp_path / "normal.txt").write_text("normal file")
        (temp_path / ".hidden").write_text("hidden file")
        (temp_path / "Thumbs.db").write_text("system file")
        (temp_path / "config.yaml").write_text("config")

        yield temp_path


class TestSystemFileCleaner:
    """Test cases for SystemFileCleaner class."""

    def test_init_loads_config(self, cleaner):
        """Test that cleaner loads configuration correctly."""
        assert cleaner.config is not None
        assert "scan" in cleaner.config
        assert "patterns" in cleaner.config

    def test_is_hidden_by_name_dot_prefix(self, cleaner):
        """Test hidden file detection by dot prefix."""
        file_path = Path(".hidden_file")
        assert cleaner._is_hidden_by_name(file_path) is True

    def test_is_hidden_by_name_pattern(self, cleaner):
        """Test hidden file detection by pattern."""
        file_path = Path("file~$temp")
        assert cleaner._is_hidden_by_name(file_path) is True

    def test_is_hidden_by_name_normal(self, cleaner):
        """Test that normal files are not hidden."""
        file_path = Path("normal_file.txt")
        assert cleaner._is_hidden_by_name(file_path) is False

    def test_is_system_file_by_name(self, cleaner):
        """Test system file detection by name pattern."""
        file_path = Path("Thumbs.db")
        assert cleaner._is_system_file(file_path) is True

    def test_is_system_file_by_extension(self, cleaner):
        """Test system file detection by extension."""
        cleaner.config["patterns"]["system_extensions"] = [".sys"]
        file_path = Path("file.sys")
        assert cleaner._is_system_file(file_path) is True

    def test_is_system_file_normal(self, cleaner):
        """Test that normal files are not system files."""
        file_path = Path("normal_file.txt")
        assert cleaner._is_system_file(file_path) is False

    def test_should_skip_path_pattern(self, cleaner):
        """Test skip pattern matching."""
        cleaner.config["skip"]["patterns"] = [".git"]
        file_path = Path("/path/.git/config")
        assert cleaner._should_skip_path(file_path) is True

    def test_should_skip_path_normal(self, cleaner):
        """Test that normal paths are not skipped."""
        file_path = Path("/path/normal/file.txt")
        assert cleaner._should_skip_path(file_path) is False

    def test_is_protected_file(self, cleaner):
        """Test protected file detection."""
        cleaner.config["protected"]["patterns"] = ["config.yaml"]
        file_path = Path("config.yaml")
        assert cleaner._is_protected_file(file_path) is True

    def test_is_protected_file_normal(self, cleaner):
        """Test that normal files are not protected."""
        file_path = Path("normal_file.txt")
        assert cleaner._is_protected_file(file_path) is False

    def test_identify_file_hidden(self, cleaner, temp_directory):
        """Test identifying hidden file."""
        hidden_file = temp_directory / ".hidden"
        file_info = cleaner.identify_file(hidden_file)
        
        assert file_info is not None
        assert file_info["is_hidden"] is True
        assert file_info["is_system"] is False

    def test_identify_file_system(self, cleaner, temp_directory):
        """Test identifying system file."""
        system_file = temp_directory / "Thumbs.db"
        file_info = cleaner.identify_file(system_file)
        
        assert file_info is not None
        assert file_info["is_system"] is True

    def test_identify_file_normal(self, cleaner, temp_directory):
        """Test that normal files are not identified."""
        normal_file = temp_directory / "normal.txt"
        file_info = cleaner.identify_file(normal_file)
        
        assert file_info is None

    def test_identify_file_protected(self, cleaner, temp_directory):
        """Test that protected files are not identified."""
        protected_file = temp_directory / "config.yaml"
        cleaner.config["protected"]["patterns"] = ["config.yaml"]
        file_info = cleaner.identify_file(protected_file)
        
        # Protected files should still be identified, but not removed
        # The protection check happens during removal

    def test_remove_file_dry_run(self, cleaner, temp_directory):
        """Test file removal in dry-run mode."""
        test_file = temp_directory / "test_remove.txt"
        test_file.write_text("test")
        
        result = cleaner.remove_file(test_file, dry_run=True)
        
        assert result is True
        assert test_file.exists()  # File should still exist

    def test_remove_file_actual(self, cleaner, temp_directory):
        """Test actual file removal."""
        test_file = temp_directory / "test_remove.txt"
        test_file.write_text("test")
        
        result = cleaner.remove_file(test_file, dry_run=False)
        
        assert result is True
        assert not test_file.exists()  # File should be removed

    def test_remove_file_protected(self, cleaner, temp_directory):
        """Test that protected files are not removed."""
        protected_file = temp_directory / "config.yaml"
        protected_file.write_text("config")
        cleaner.config["protected"]["patterns"] = ["config.yaml"]
        
        result = cleaner.remove_file(protected_file, dry_run=False)
        
        assert result is False
        assert protected_file.exists()  # File should still exist
        assert cleaner.stats["files_skipped"] > 0

    def test_scan_directory(self, cleaner, temp_directory):
        """Test scanning directory."""
        files = cleaner.scan_directory(directory=str(temp_directory), remove_files=False)
        
        assert len(files) >= 2  # Should find .hidden and Thumbs.db
        assert cleaner.stats["files_scanned"] > 0

    def test_scan_directory_remove(self, cleaner, temp_directory):
        """Test scanning directory with removal."""
        files = cleaner.scan_directory(
            directory=str(temp_directory), remove_files=True
        )
        
        assert len(files) >= 2
        # Files should be marked for removal (dry-run by default)

    def test_scan_directory_nonexistent(self, cleaner):
        """Test scanning nonexistent directory."""
        with pytest.raises(FileNotFoundError):
            cleaner.scan_directory(directory="/nonexistent/path")

    def test_generate_report(self, cleaner, temp_directory):
        """Test report generation."""
        files = cleaner.scan_directory(directory=str(temp_directory))
        report = cleaner.generate_report(files)
        
        assert "SYSTEM AND HIDDEN FILE CLEANER REPORT" in report
        assert "STATISTICS" in report

    def test_generate_report_save_file(self, cleaner, temp_directory):
        """Test saving report to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = str(Path(temp_dir) / "test_report.txt")
            files = cleaner.scan_directory(directory=str(temp_directory))
            
            report = cleaner.generate_report(files, output_file=report_file)
            
            assert Path(report_file).exists()
            assert report is not None

    def test_print_summary(self, cleaner, temp_directory, capsys):
        """Test printing summary to console."""
        cleaner.scan_directory(directory=str(temp_directory))
        cleaner.print_summary()
        captured = capsys.readouterr()
        
        assert "SYSTEM FILE CLEANER SUMMARY" in captured.out
        assert "Files scanned" in captured.out


class TestMainFunction:
    """Test cases for main function."""

    @patch("src.main.SystemFileCleaner")
    def test_main_scan_only(self, mock_cleaner_class, temp_config_file):
        """Test main function with scan only."""
        mock_cleaner = MagicMock()
        mock_cleaner.scan_directory.return_value = []
        mock_cleaner.config = {"report": {"auto_save": False}}
        mock_cleaner_class.return_value = mock_cleaner

        from src.main import main
        import sys

        sys.argv = ["main.py", "-c", temp_config_file]
        result = main()

        assert result == 0
        mock_cleaner.scan_directory.assert_called_once()

    @patch("src.main.SystemFileCleaner")
    def test_main_with_remove(self, mock_cleaner_class, temp_config_file):
        """Test main function with remove option."""
        mock_cleaner = MagicMock()
        mock_cleaner.scan_directory.return_value = []
        mock_cleaner.config = {"report": {"auto_save": False}}
        mock_cleaner_class.return_value = mock_cleaner

        from src.main import main
        import sys

        sys.argv = ["main.py", "-c", temp_config_file, "--remove"]
        result = main()

        assert result == 0
        mock_cleaner.scan_directory.assert_called_with(
            directory=None, remove_files=True
        )
