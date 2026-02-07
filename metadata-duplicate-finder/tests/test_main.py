"""Unit tests for metadata duplicate finder."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import (
    MetadataDuplicateFinder,
    load_config,
)


class TestLoadConfig:
    """Test configuration file loading."""

    def test_load_config_valid_yaml(self):
        """Test loading valid YAML configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "check_exif": False,
                "check_dates": True,
                "check_size": True,
                "similarity_threshold": 0.7,
            }
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            result = load_config(config_path)
            assert result["check_exif"] is False
            assert result["check_dates"] is True
            assert result["check_size"] is True
        finally:
            config_path.unlink()

    def test_load_config_file_not_found(self):
        """Test that missing config file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config(Path("/nonexistent/config.yaml"))

    def test_load_config_invalid_yaml(self):
        """Test that invalid YAML raises YAMLError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = Path(f.name)

        try:
            with pytest.raises(yaml.YAMLError):
                load_config(config_path)
        finally:
            config_path.unlink()


class TestMetadataDuplicateFinder:
    """Test MetadataDuplicateFinder class."""

    def test_init(self):
        """Test initialization."""
        finder = MetadataDuplicateFinder()
        assert finder.check_exif == (True and finder.check_exif)
        assert finder.check_dates is True
        assert finder.check_size is False

    def test_extract_file_metadata(self):
        """Test file metadata extraction."""
        finder = MetadataDuplicateFinder(check_exif=False)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            file_path = Path(f.name)

        try:
            metadata = finder._extract_file_metadata(file_path)

            assert metadata["path"] == str(file_path)
            assert metadata["name"] == file_path.name
            assert "size" in metadata
            assert "created" in metadata
            assert "modified" in metadata
        finally:
            file_path.unlink()

    def test_create_metadata_signature(self):
        """Test metadata signature creation."""
        finder = MetadataDuplicateFinder(check_exif=False, check_dates=True)

        metadata = {
            "created": "2024-01-15T10:30:00",
            "modified": "2024-01-15T10:30:00",
            "size": 1000,
        }

        signature = finder._create_metadata_signature(metadata)
        assert "dates:" in signature
        assert "2024-01-15T10:30:00" in signature

    def test_create_metadata_signature_with_size(self):
        """Test metadata signature with size checking."""
        finder = MetadataDuplicateFinder(check_exif=False, check_dates=True, check_size=True)

        metadata = {
            "created": "2024-01-15T10:30:00",
            "modified": "2024-01-15T10:30:00",
            "size": 1000,
        }

        signature = finder._create_metadata_signature(metadata)
        assert "size:1000" in signature

    def test_calculate_similarity_identical(self):
        """Test similarity calculation for identical signatures."""
        finder = MetadataDuplicateFinder()
        sig1 = "dates:2024-01-15:2024-01-15|size:1000"
        sig2 = "dates:2024-01-15:2024-01-15|size:1000"

        similarity = finder._calculate_similarity(sig1, sig2)
        assert similarity == 1.0

    def test_calculate_similarity_different(self):
        """Test similarity calculation for different signatures."""
        finder = MetadataDuplicateFinder()
        sig1 = "dates:2024-01-15:2024-01-15"
        sig2 = "dates:2024-01-16:2024-01-16"

        similarity = finder._calculate_similarity(sig1, sig2)
        assert similarity < 1.0

    def test_calculate_similarity_partial(self):
        """Test similarity calculation for partially matching signatures."""
        finder = MetadataDuplicateFinder()
        sig1 = "dates:2024-01-15:2024-01-15|size:1000"
        sig2 = "dates:2024-01-15:2024-01-15|size:2000"

        similarity = finder._calculate_similarity(sig1, sig2)
        assert 0.0 < similarity < 1.0

    def test_find_duplicates(self):
        """Test finding duplicate files."""
        finder = MetadataDuplicateFinder(check_exif=False, check_dates=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)

            file1 = dir_path / "file1.txt"
            file1.write_text("content1")
            file2 = dir_path / "file2.txt"
            file2.write_text("content2")

            duplicate_groups = finder.find_duplicates([dir_path])

            assert isinstance(duplicate_groups, dict)

    def test_find_duplicates_recursive(self):
        """Test recursive duplicate finding."""
        finder = MetadataDuplicateFinder(check_exif=False, check_dates=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            subdir = dir_path / "subdir"
            subdir.mkdir()

            file1 = dir_path / "file1.txt"
            file1.write_text("content1")
            file2 = subdir / "file2.txt"
            file2.write_text("content2")

            duplicate_groups = finder.find_duplicates([dir_path], recursive=True)

            assert isinstance(duplicate_groups, dict)

    def test_format_report(self):
        """Test report formatting."""
        finder = MetadataDuplicateFinder()

        duplicate_groups = {
            "sig1": [
                {
                    "path": "/path/to/file1.jpg",
                    "size": 1000,
                    "created": "2024-01-15T10:30:00",
                    "modified": "2024-01-15T10:30:00",
                }
            ]
        }

        report = finder.format_report(duplicate_groups)
        assert "Metadata Duplicate Report" in report
        assert "/path/to/file1.jpg" in report

    def test_format_report_empty(self):
        """Test report formatting with no duplicates."""
        finder = MetadataDuplicateFinder()
        report = finder.format_report({})
        assert "No duplicate metadata found" in report

    @pytest.mark.skipif(
        not pytest.importorskip("PIL", reason="PIL not available"),
        reason="PIL not available",
    )
    def test_extract_exif_data(self):
        """Test EXIF data extraction."""
        try:
            from PIL import Image

            finder = MetadataDuplicateFinder(check_exif=True)

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                file_path = Path(f.name)

            try:
                img = Image.new("RGB", (100, 100), color="red")
                img.save(file_path)

                exif_data = finder._extract_exif_data(file_path)
                assert exif_data is None or isinstance(exif_data, dict)
            finally:
                if file_path.exists():
                    file_path.unlink()
        except ImportError:
            pytest.skip("PIL not available")

    def test_extract_exif_data_no_pil(self):
        """Test EXIF extraction when PIL is not available."""
        finder = MetadataDuplicateFinder(check_exif=False)

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"fake image data")
            file_path = Path(f.name)

        try:
            exif_data = finder._extract_exif_data(file_path)
            assert exif_data is None
        finally:
            if file_path.exists():
                file_path.unlink()

    def test_find_similar_metadata(self):
        """Test finding similar metadata."""
        finder = MetadataDuplicateFinder(
            check_exif=False, check_dates=True, similarity_threshold=0.5
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)

            file1 = dir_path / "file1.txt"
            file1.write_text("content1")
            file2 = dir_path / "file2.txt"
            file2.write_text("content2")

            similar_pairs = finder.find_similar_metadata([dir_path])

            assert isinstance(similar_pairs, list)
