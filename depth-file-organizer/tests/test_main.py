"""Unit tests for depth file organizer."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.main import DepthFileOrganizer


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

organization:
  dry_run: true
  depth_naming:
    prefix: "Depth"
    separator: "_"
    include_level: true
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
    """Create DepthFileOrganizer instance for testing."""
    organizer = DepthFileOrganizer(config_path=temp_config_file)
    yield organizer


@pytest.fixture
def temp_directory():
    """Create temporary directory with test files at different depths."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Depth 0 files
        (temp_path / "file0.txt").write_text("depth 0")

        # Depth 1 files
        (temp_path / "folder1").mkdir()
        (temp_path / "folder1" / "file1.txt").write_text("depth 1")

        # Depth 2 files
        (temp_path / "folder1" / "subfolder").mkdir()
        (temp_path / "folder1" / "subfolder" / "file2.txt").write_text("depth 2")

        # Depth 1 in different folder
        (temp_path / "folder2").mkdir()
        (temp_path / "folder2" / "file3.txt").write_text("depth 1")

        yield temp_path


class TestDepthFileOrganizer:
    """Test cases for DepthFileOrganizer class."""

    def test_init_loads_config(self, organizer):
        """Test that organizer loads configuration correctly."""
        assert organizer.config is not None
        assert "source" in organizer.config
        assert "output" in organizer.config

    def test_calculate_depth_root(self, organizer, temp_directory):
        """Test depth calculation for root level files."""
        file_path = temp_directory / "file0.txt"
        depth = organizer._calculate_depth(file_path, temp_directory)
        assert depth == 0

    def test_calculate_depth_one(self, organizer, temp_directory):
        """Test depth calculation for one level deep."""
        file_path = temp_directory / "folder1" / "file1.txt"
        depth = organizer._calculate_depth(file_path, temp_directory)
        assert depth == 1

    def test_calculate_depth_two(self, organizer, temp_directory):
        """Test depth calculation for two levels deep."""
        file_path = temp_directory / "folder1" / "subfolder" / "file2.txt"
        depth = organizer._calculate_depth(file_path, temp_directory)
        assert depth == 2

    def test_should_skip_path_pattern(self, organizer):
        """Test skip pattern matching."""
        organizer.config["skip"]["patterns"] = [".git"]
        file_path = Path("/path/.git/config")
        assert organizer._should_skip_path(file_path) is True

    def test_should_skip_path_normal(self, organizer):
        """Test that normal paths are not skipped."""
        file_path = Path("/path/normal/file.txt")
        assert organizer._should_skip_path(file_path) is False

    def test_should_include_extension_all(self, organizer):
        """Test extension filtering with all extensions."""
        organizer.config["include"]["extensions"] = []
        file_path = Path("file.txt")
        assert organizer._should_include_extension(file_path) is True

    def test_should_include_extension_filtered(self, organizer):
        """Test extension filtering with specific extensions."""
        organizer.config["include"]["extensions"] = [".txt", ".pdf"]
        file_path = Path("file.txt")
        assert organizer._should_include_extension(file_path) is True
        
        file_path = Path("file.jpg")
        assert organizer._should_include_extension(file_path) is False

    def test_get_depth_folder_name(self, organizer):
        """Test depth folder name generation."""
        name = organizer._get_depth_folder_name(0)
        assert name == "Depth_0"
        
        name = organizer._get_depth_folder_name(5)
        assert name == "Depth_5"

    def test_get_depth_folder_name_custom(self, organizer):
        """Test custom depth folder naming."""
        organizer.config["organization"]["depth_naming"]["prefix"] = "Level"
        organizer.config["organization"]["depth_naming"]["separator"] = "-"
        name = organizer._get_depth_folder_name(2)
        assert name == "Level-2"

    def test_scan_files(self, organizer, temp_directory):
        """Test scanning files and grouping by depth."""
        files_by_depth = organizer.scan_files(directory=str(temp_directory))
        
        assert 0 in files_by_depth
        assert 1 in files_by_depth
        assert 2 in files_by_depth
        assert len(files_by_depth[0]) == 1
        assert len(files_by_depth[1]) == 2
        assert len(files_by_depth[2]) == 1

    def test_scan_files_nonexistent_directory(self, organizer):
        """Test scanning nonexistent directory."""
        with pytest.raises(FileNotFoundError):
            organizer.scan_files(directory="/nonexistent/path")

    def test_organize_files_dry_run(self, organizer, temp_directory):
        """Test organizing files in dry-run mode."""
        files_by_depth = organizer.scan_files(directory=str(temp_directory))
        
        stats = organizer.organize_files(files_by_depth, dry_run=True)
        
        assert stats["files_organized"] > 0
        # Files should still exist in original location
        assert (temp_directory / "file0.txt").exists()

    def test_organize_files_actual(self, organizer, temp_directory):
        """Test actual file organization."""
        files_by_depth = organizer.scan_files(directory=str(temp_directory))
        
        stats = organizer.organize_files(files_by_depth, dry_run=False)
        
        assert stats["files_organized"] > 0
        # Check that organized directory was created
        organized_path = temp_directory.parent / "organized"
        assert organized_path.exists()

    def test_generate_report(self, organizer, temp_directory):
        """Test report generation."""
        files_by_depth = organizer.scan_files(directory=str(temp_directory))
        report = organizer.generate_report(files_by_depth)
        
        assert "DEPTH FILE ORGANIZER REPORT" in report
        assert "STATISTICS" in report
        assert "FILES BY DEPTH" in report

    def test_generate_report_save_file(self, organizer, temp_directory):
        """Test saving report to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = str(Path(temp_dir) / "test_report.txt")
            files_by_depth = organizer.scan_files(directory=str(temp_directory))
            
            report = organizer.generate_report(files_by_depth, output_file=report_file)
            
            assert Path(report_file).exists()
            assert report is not None

    def test_print_summary(self, organizer, temp_directory, capsys):
        """Test printing summary to console."""
        files_by_depth = organizer.scan_files(directory=str(temp_directory))
        organizer.print_summary(files_by_depth)
        captured = capsys.readouterr()
        
        assert "DEPTH FILE ORGANIZER SUMMARY" in captured.out
        assert "Files scanned" in captured.out
        assert "Depth levels found" in captured.out


class TestMainFunction:
    """Test cases for main function."""

    @patch("src.main.DepthFileOrganizer")
    def test_main_scan_only(self, mock_organizer_class, temp_config_file):
        """Test main function with scan only."""
        mock_organizer = MagicMock()
        mock_organizer.scan_files.return_value = {0: [], 1: []}
        mock_organizer.config = {"report": {"auto_save": False}}
        mock_organizer_class.return_value = mock_organizer

        from src.main import main
        import sys

        sys.argv = ["main.py", "-c", temp_config_file]
        result = main()

        assert result == 0
        mock_organizer.scan_files.assert_called_once()

    @patch("src.main.DepthFileOrganizer")
    def test_main_with_organize(self, mock_organizer_class, temp_config_file):
        """Test main function with organize option."""
        mock_organizer = MagicMock()
        mock_organizer.scan_files.return_value = {0: [], 1: []}
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
