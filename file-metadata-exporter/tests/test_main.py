"""Unit tests for file metadata exporter."""

import csv
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.main import FileMetadataExporter


@pytest.fixture
def temp_config_file():
    """Create temporary config file for testing."""
    config_content = """
source:
  directory: "."
  recursive: true

metadata:
  include_owner: false
  include_group: false
  include_inode: false
  include_device: false

checksum:
  enabled: true
  algorithms: ["md5"]
  chunk_size: 8192

include:
  extensions: []
  include_no_extension: true

skip:
  patterns: []
  directories: []
  excluded_paths: []

export:
  output_file: "data/test_metadata.csv"
  encoding: "utf-8"

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
def exporter(temp_config_file):
    """Create FileMetadataExporter instance for testing."""
    exporter = FileMetadataExporter(config_path=temp_config_file)
    yield exporter


@pytest.fixture
def temp_directory():
    """Create temporary directory with test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files
        (temp_path / "file1.txt").write_text("test content 1")
        (temp_path / "file2.txt").write_text("test content 2")
        (temp_path / "subfolder").mkdir()
        (temp_path / "subfolder" / "file3.txt").write_text("test content 3")

        yield temp_path


class TestFileMetadataExporter:
    """Test cases for FileMetadataExporter class."""

    def test_init_loads_config(self, exporter):
        """Test that exporter loads configuration correctly."""
        assert exporter.config is not None
        assert "source" in exporter.config
        assert "checksum" in exporter.config

    def test_calculate_checksum_md5(self, exporter, temp_directory):
        """Test MD5 checksum calculation."""
        test_file = temp_directory / "file1.txt"
        checksum = exporter._calculate_checksum(test_file, "md5")
        
        assert checksum is not None
        assert len(checksum) == 32  # MD5 produces 32 hex characters

    def test_calculate_checksum_sha1(self, exporter, temp_directory):
        """Test SHA1 checksum calculation."""
        test_file = temp_directory / "file1.txt"
        checksum = exporter._calculate_checksum(test_file, "sha1")
        
        assert checksum is not None
        assert len(checksum) == 40  # SHA1 produces 40 hex characters

    def test_calculate_checksum_sha256(self, exporter, temp_directory):
        """Test SHA256 checksum calculation."""
        test_file = temp_directory / "file1.txt"
        checksum = exporter._calculate_checksum(test_file, "sha256")
        
        assert checksum is not None
        assert len(checksum) == 64  # SHA256 produces 64 hex characters

    def test_calculate_checksum_nonexistent(self, exporter):
        """Test checksum calculation for nonexistent file."""
        test_file = Path("/nonexistent/file.txt")
        checksum = exporter._calculate_checksum(test_file)
        
        assert checksum is None

    def test_get_file_permissions(self, exporter, temp_directory):
        """Test file permissions extraction."""
        test_file = temp_directory / "file1.txt"
        permissions = exporter._get_file_permissions(test_file)
        
        assert "mode_octal" in permissions
        assert "mode_readable" in permissions
        assert "is_readable" in permissions
        assert "is_writable" in permissions

    def test_should_skip_path_pattern(self, exporter):
        """Test skip pattern matching."""
        exporter.config["skip"]["patterns"] = [".git"]
        file_path = Path("/path/.git/config")
        assert exporter._should_skip_path(file_path) is True

    def test_should_skip_path_normal(self, exporter):
        """Test that normal paths are not skipped."""
        file_path = Path("/path/normal/file.txt")
        assert exporter._should_skip_path(file_path) is False

    def test_should_include_extension_all(self, exporter):
        """Test extension filtering with all extensions."""
        exporter.config["include"]["extensions"] = []
        file_path = Path("file.txt")
        assert exporter._should_include_extension(file_path) is True

    def test_should_include_extension_filtered(self, exporter):
        """Test extension filtering with specific extensions."""
        exporter.config["include"]["extensions"] = [".txt", ".pdf"]
        file_path = Path("file.txt")
        assert exporter._should_include_extension(file_path) is True
        
        file_path = Path("file.jpg")
        assert exporter._should_include_extension(file_path) is False

    def test_extract_metadata(self, exporter, temp_directory):
        """Test metadata extraction."""
        test_file = temp_directory / "file1.txt"
        metadata = exporter.extract_metadata(test_file)
        
        assert metadata is not None
        assert metadata["path"] == str(test_file)
        assert metadata["name"] == "file1.txt"
        assert "size_bytes" in metadata
        assert "created" in metadata
        assert "modified" in metadata
        assert "accessed" in metadata

    def test_extract_metadata_with_checksum(self, exporter, temp_directory):
        """Test metadata extraction with checksum."""
        exporter.config["checksum"]["enabled"] = True
        exporter.config["checksum"]["algorithms"] = ["md5"]
        
        test_file = temp_directory / "file1.txt"
        metadata = exporter.extract_metadata(test_file)
        
        assert metadata is not None
        assert "checksum_md5" in metadata
        assert metadata["checksum_md5"] is not None

    def test_extract_metadata_nonexistent(self, exporter):
        """Test metadata extraction for nonexistent file."""
        test_file = Path("/nonexistent/file.txt")
        metadata = exporter.extract_metadata(test_file)
        
        assert metadata is None

    def test_scan_directory(self, exporter, temp_directory):
        """Test directory scanning."""
        metadata_list = exporter.scan_directory(directory=str(temp_directory))
        
        assert len(metadata_list) >= 3
        assert exporter.stats["files_scanned"] >= 3
        assert exporter.stats["files_processed"] >= 3

    def test_scan_directory_nonexistent(self, exporter):
        """Test scanning nonexistent directory."""
        with pytest.raises(FileNotFoundError):
            exporter.scan_directory(directory="/nonexistent/path")

    def test_export_to_csv(self, exporter, temp_directory):
        """Test CSV export."""
        metadata_list = exporter.scan_directory(directory=str(temp_directory))
        
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_file = str(Path(temp_dir) / "test_export.csv")
            csv_path = exporter.export_to_csv(metadata_list, output_file=csv_file)
            
            assert Path(csv_path).exists()
            
            # Verify CSV content
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == len(metadata_list)
                assert "path" in rows[0]
                assert "name" in rows[0]
                assert "size_bytes" in rows[0]

    def test_export_to_csv_empty(self, exporter):
        """Test CSV export with empty metadata list."""
        with pytest.raises(ValueError):
            exporter.export_to_csv([])

    def test_print_summary(self, exporter, temp_directory, capsys):
        """Test printing summary to console."""
        exporter.scan_directory(directory=str(temp_directory))
        exporter.print_summary()
        captured = capsys.readouterr()
        
        assert "FILE METADATA EXPORTER SUMMARY" in captured.out
        assert "Files scanned" in captured.out


class TestMainFunction:
    """Test cases for main function."""

    @patch("src.main.FileMetadataExporter")
    def test_main_basic(self, mock_exporter_class, temp_config_file):
        """Test main function with basic arguments."""
        mock_exporter = MagicMock()
        mock_exporter.scan_directory.return_value = [
            {"path": "/test/file.txt", "name": "file.txt"}
        ]
        mock_exporter.export_to_csv.return_value = "/test/output.csv"
        mock_exporter_class.return_value = mock_exporter

        from src.main import main
        import sys

        sys.argv = ["main.py", "-c", temp_config_file]
        result = main()

        assert result == 0
        mock_exporter.scan_directory.assert_called_once()
        mock_exporter.export_to_csv.assert_called_once()

    @patch("src.main.FileMetadataExporter")
    def test_main_with_directory(self, mock_exporter_class, temp_config_file):
        """Test main function with directory argument."""
        mock_exporter = MagicMock()
        mock_exporter.scan_directory.return_value = [
            {"path": "/test/file.txt", "name": "file.txt"}
        ]
        mock_exporter.export_to_csv.return_value = "/test/output.csv"
        mock_exporter_class.return_value = mock_exporter

        from src.main import main
        import sys

        sys.argv = ["main.py", "-c", temp_config_file, "-d", "/test/dir"]
        result = main()

        assert result == 0
        mock_exporter.scan_directory.assert_called_with(directory="/test/dir")
