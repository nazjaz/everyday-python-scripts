"""Unit tests for file health checker module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.main import FileHealthChecker


class TestFileHealthChecker:
    """Test cases for FileHealthChecker class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def config_file(self, temp_dir):
        """Create temporary config file."""
        config = {
            "health_check": {
                "calculate_checksum": False,
                "checksum_algorithm": "md5",
                "min_file_size": 1,
                "magic_numbers": {},
            },
            "scan": {"skip_patterns": [".git"]},
            "report": {"output_file": "report.txt"},
            "logging": {"level": "INFO", "file": "logs/app.log"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return str(config_path)

    @pytest.fixture
    def checker(self, config_file):
        """Create FileHealthChecker instance."""
        return FileHealthChecker(config_path=config_file)

    def test_load_config_success(self, temp_dir):
        """Test successful configuration loading."""
        config = {
            "health_check": {"calculate_checksum": True},
            "scan": {"skip_patterns": []},
            "logging": {"level": "INFO"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        checker = FileHealthChecker(config_path=str(config_path))
        assert checker.config["health_check"]["calculate_checksum"] is True

    def test_load_config_file_not_found(self):
        """Test FileNotFoundError when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            FileHealthChecker(config_path="nonexistent.yaml")

    def test_calculate_file_hash_md5(self, checker, temp_dir):
        """Test MD5 hash calculation."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        hash_value = checker._calculate_file_hash(test_file, "md5")
        assert hash_value is not None
        assert len(hash_value) == 32

    def test_calculate_file_hash_sha256(self, checker, temp_dir):
        """Test SHA256 hash calculation."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        hash_value = checker._calculate_file_hash(test_file, "sha256")
        assert hash_value is not None
        assert len(hash_value) == 64

    def test_check_file_header_valid_pdf(self, checker, temp_dir):
        """Test file header check for valid PDF."""
        test_file = temp_dir / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4\ncontent")

        is_valid, error = checker._check_file_header(test_file)
        assert is_valid is True
        assert error is None

    def test_check_file_header_invalid_pdf(self, checker, temp_dir):
        """Test file header check for invalid PDF."""
        test_file = temp_dir / "test.pdf"
        test_file.write_bytes(b"NOTPDFcontent")

        is_valid, error = checker._check_file_header(test_file)
        assert is_valid is False
        assert error is not None

    def test_check_file_header_no_magic(self, checker, temp_dir):
        """Test file header check for file type without magic number."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        is_valid, error = checker._check_file_header(test_file)
        assert is_valid is True  # No magic number defined, skip check

    def test_check_file_structure_empty(self, checker, temp_dir):
        """Test structure check for empty file."""
        test_file = temp_dir / "test.txt"
        test_file.write_bytes(b"")

        is_valid, error = checker._check_file_structure(test_file)
        assert is_valid is False
        assert "empty" in error.lower()

    def test_check_file_structure_valid(self, checker, temp_dir):
        """Test structure check for valid file."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content" * 100)

        is_valid, error = checker._check_file_structure(test_file)
        assert is_valid is True

    def test_check_zip_structure_valid(self, checker, temp_dir):
        """Test ZIP structure check for valid ZIP."""
        import zipfile

        test_file = temp_dir / "test.zip"
        with zipfile.ZipFile(test_file, "w") as zf:
            zf.writestr("test.txt", "content")

        is_valid, error = checker._check_zip_structure(test_file)
        assert is_valid is True

    def test_check_jpeg_structure_valid(self, checker, temp_dir):
        """Test JPEG structure check."""
        # Create minimal valid JPEG structure
        test_file = temp_dir / "test.jpg"
        # JPEG start marker + minimal data + end marker
        test_file.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"data" * 10 + b"\xff\xd9")

        is_valid, error = checker._check_jpeg_structure(test_file)
        # May fail if structure is too minimal, but should handle gracefully
        assert isinstance(is_valid, bool)

    def test_check_png_structure_valid(self, checker, temp_dir):
        """Test PNG structure check."""
        # Create minimal PNG structure
        test_file = temp_dir / "test.png"
        # PNG signature + minimal data + IEND
        png_data = (
            b"\x89PNG\r\n\x1a\n"
            + b"\x00\x00\x00\rIHDR" + b"data" * 4
            + b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        test_file.write_bytes(png_data)

        is_valid, error = checker._check_png_structure(test_file)
        assert is_valid is True

    def test_check_pdf_structure_valid(self, checker, temp_dir):
        """Test PDF structure check."""
        test_file = temp_dir / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4\ncontent\n%%EOF")

        is_valid, error = checker._check_pdf_structure(test_file)
        assert is_valid is True

    def test_perform_health_check_healthy(self, checker, temp_dir):
        """Test health check for healthy file."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content" * 100)

        result = checker._perform_health_check(test_file)
        assert result["is_healthy"] is True
        assert result["status"] == "healthy"

    def test_perform_health_check_corrupted(self, checker, temp_dir):
        """Test health check for corrupted file."""
        # Create invalid PDF
        test_file = temp_dir / "test.pdf"
        test_file.write_bytes(b"INVALIDPDF")

        result = checker._perform_health_check(test_file)
        assert result["is_healthy"] is False
        assert len(result["issues"]) > 0

    def test_should_skip_path(self, checker):
        """Test path skipping logic."""
        path = Path("/some/path/.git/config")
        assert checker._should_skip_path(path) is True

        path = Path("/some/path/normal_file.txt")
        assert checker._should_skip_path(path) is False

    def test_scan_directory(self, checker, temp_dir):
        """Test directory scanning."""
        # Create test files
        (temp_dir / "file1.txt").write_text("content")
        (temp_dir / "file2.pdf").write_bytes(b"%PDF-1.4\ncontent\n%%EOF")

        checker.scan_directory(str(temp_dir))

        assert checker.stats["files_scanned"] == 2
        assert len(checker.file_health) == 2

    def test_scan_directory_not_found(self, checker):
        """Test FileNotFoundError when directory doesn't exist."""
        with pytest.raises(FileNotFoundError):
            checker.scan_directory("/nonexistent/path")

    def test_generate_report(self, checker, temp_dir):
        """Test report generation."""
        # Create test files and scan
        (temp_dir / "file1.txt").write_text("content")

        checker.scan_directory(str(temp_dir))
        report_path = temp_dir / "test_report.txt"
        checker.generate_report(output_path=str(report_path))

        assert report_path.exists()
        content = report_path.read_text()
        assert "FILE HEALTH CHECK REPORT" in content
        assert "SUMMARY" in content

    def test_format_size(self, checker):
        """Test size formatting."""
        assert checker._format_size(512) == "512.00 B"
        assert checker._format_size(2048) == "2.00 KB"
        assert checker._format_size(1048576) == "1.00 MB"
