"""Unit tests for metadata extractor."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import (
    MetadataExtractor,
    load_config,
)


class TestLoadConfig:
    """Test configuration file loading."""

    def test_load_config_valid_yaml(self):
        """Test loading valid YAML configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "recursive": True,
                "file_types": ["images", "audio"],
                "output_format": "json",
            }
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            result = load_config(config_path)
            assert result["recursive"] is True
            assert result["file_types"] == ["images", "audio"]
            assert result["output_format"] == "json"
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


class TestMetadataExtractor:
    """Test MetadataExtractor class."""

    def test_init(self):
        """Test initialization."""
        extractor = MetadataExtractor()
        assert extractor.stats["processed"] == 0
        assert extractor.stats["images"] == 0
        assert extractor.stats["audio"] == 0
        assert extractor.stats["office"] == 0
        assert extractor.stats["errors"] == 0

    def test_extract_metadata_unsupported_file(self):
        """Test extracting metadata from unsupported file type."""
        extractor = MetadataExtractor()
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test content")
            file_path = Path(f.name)

        try:
            result = extractor.extract_metadata(file_path)
            assert result is None
        finally:
            file_path.unlink()

    @pytest.mark.skipif(
        not pytest.importorskip("PIL", reason="PIL not available"),
        reason="PIL not available",
    )
    def test_extract_image_metadata(self):
        """Test image metadata extraction."""
        try:
            from PIL import Image

            extractor = MetadataExtractor()
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                file_path = Path(f.name)

            try:
                img = Image.new("RGB", (100, 200), color="red")
                img.save(file_path)

                metadata = extractor.extract_image_metadata(file_path)

                assert metadata["file_type"] == "image"
                assert metadata["size"]["width"] == 100
                assert metadata["size"]["height"] == 200
                assert "file_size" in metadata
            finally:
                if file_path.exists():
                    file_path.unlink()
        except ImportError:
            pytest.skip("PIL not available")

    def test_extract_image_metadata_no_pil(self):
        """Test image metadata extraction when PIL is not available."""
        extractor = MetadataExtractor()
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"fake image data")
            file_path = Path(f.name)

        try:
            with patch("src.main.PIL_AVAILABLE", False):
                with pytest.raises(ImportError):
                    extractor.extract_image_metadata(file_path)
        finally:
            file_path.unlink()

    def test_process_files_single_file(self):
        """Test processing a single file."""
        extractor = MetadataExtractor()
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test content")
            file_path = Path(f.name)

        try:
            metadata_list = extractor.process_files([file_path])
            assert isinstance(metadata_list, list)
        finally:
            file_path.unlink()

    def test_process_files_directory(self):
        """Test processing files in a directory."""
        extractor = MetadataExtractor()
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            test_file = dir_path / "test.txt"
            test_file.write_text("test content")

            metadata_list = extractor.process_files([dir_path])
            assert isinstance(metadata_list, list)

    def test_process_files_recursive(self):
        """Test recursive directory processing."""
        extractor = MetadataExtractor()
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            subdir = dir_path / "subdir"
            subdir.mkdir()
            test_file = subdir / "test.txt"
            test_file.write_text("test content")

            metadata_list = extractor.process_files([dir_path], recursive=True)
            assert isinstance(metadata_list, list)

    def test_format_report_empty(self):
        """Test formatting report with no metadata."""
        extractor = MetadataExtractor()
        report = extractor.format_report([])
        assert "No metadata extracted" in report

    def test_format_report_with_metadata(self):
        """Test formatting report with metadata."""
        extractor = MetadataExtractor()
        metadata = {
            "file_path": "/test/file.jpg",
            "file_type": "image",
            "file_size": 12345,
            "size": {"width": 100, "height": 200},
        }
        report = extractor.format_report([metadata])
        assert "Metadata Extraction Report" in report
        assert "/test/file.jpg" in report
        assert "image" in report

    def test_file_type_detection(self):
        """Test file type detection based on extension."""
        extractor = MetadataExtractor()

        assert ".jpg" in extractor.IMAGE_EXTENSIONS
        assert ".png" in extractor.IMAGE_EXTENSIONS
        assert ".mp3" in extractor.AUDIO_EXTENSIONS
        assert ".flac" in extractor.AUDIO_EXTENSIONS
        assert ".docx" in extractor.OFFICE_EXTENSIONS
        assert ".xlsx" in extractor.OFFICE_EXTENSIONS


class TestImageMetadata:
    """Test image metadata extraction (requires PIL)."""

    @pytest.mark.skipif(
        not pytest.importorskip("PIL", reason="PIL not available"),
        reason="PIL not available",
    )
    def test_image_dimensions(self):
        """Test extracting image dimensions."""
        try:
            from PIL import Image

            extractor = MetadataExtractor()
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                file_path = Path(f.name)

            try:
                img = Image.new("RGB", (800, 600), color="blue")
                img.save(file_path)

                metadata = extractor.extract_image_metadata(file_path)

                assert metadata["size"]["width"] == 800
                assert metadata["size"]["height"] == 600
            finally:
                if file_path.exists():
                    file_path.unlink()
        except ImportError:
            pytest.skip("PIL not available")


class TestAudioMetadata:
    """Test audio metadata extraction (requires mutagen)."""

    @pytest.mark.skipif(
        not pytest.importorskip("mutagen", reason="mutagen not available"),
        reason="mutagen not available",
    )
    def test_audio_metadata_extraction(self):
        """Test audio metadata extraction."""
        extractor = MetadataExtractor()
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            file_path = Path(f.name)

        try:
            f.write(b"fake mp3 data")
            f.flush()

            metadata = extractor.extract_audio_metadata(file_path)
            assert metadata["file_type"] == "audio"
            assert "file_size" in metadata
        except ImportError:
            pytest.skip("mutagen not available")
        finally:
            if file_path.exists():
                file_path.unlink()

    def test_audio_metadata_no_mutagen(self):
        """Test audio metadata extraction when mutagen is not available."""
        extractor = MetadataExtractor()
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"fake mp3 data")
            file_path = Path(f.name)

        try:
            with patch("src.main.MUTAGEN_AVAILABLE", False):
                with pytest.raises(ImportError):
                    extractor.extract_audio_metadata(file_path)
        finally:
            if file_path.exists():
                file_path.unlink()


class TestOfficeMetadata:
    """Test office document metadata extraction."""

    def test_docx_metadata_no_library(self):
        """Test DOCX metadata extraction when library is not available."""
        extractor = MetadataExtractor()
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            f.write(b"fake docx data")
            file_path = Path(f.name)

        try:
            with patch("src.main.DOCX_AVAILABLE", False):
                with pytest.raises(ImportError):
                    extractor.extract_docx_metadata(file_path)
        finally:
            if file_path.exists():
                file_path.unlink()

    def test_xlsx_metadata_no_library(self):
        """Test XLSX metadata extraction when library is not available."""
        extractor = MetadataExtractor()
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            f.write(b"fake xlsx data")
            file_path = Path(f.name)

        try:
            with patch("src.main.OPENPYXL_AVAILABLE", False):
                with pytest.raises(ImportError):
                    extractor.extract_xlsx_metadata(file_path)
        finally:
            if file_path.exists():
                file_path.unlink()
