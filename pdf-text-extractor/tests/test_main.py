"""Unit tests for PDF Text Extractor."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import PDFTextExtractor


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary config file."""
    source_dir = temp_dir / "source"
    source_dir.mkdir()
    dest_dir = temp_dir / "dest"
    dest_dir.mkdir()

    config = {
        "source_directory": str(source_dir),
        "destination_directory": str(dest_dir),
        "pdf_password": "",
        "skip_encrypted": True,
        "output_encoding": "utf-8",
        "operations": {
            "create_destination": True,
            "recursive": True,
            "preserve_structure": True,
            "dry_run": False,
        },
        "logging": {
            "level": "INFO",
            "file": str(temp_dir / "test.log"),
            "max_bytes": 10485760,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }
    config_path = temp_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return str(config_path)


@pytest.fixture
def test_pdf_file(temp_dir):
    """Create a test PDF file."""
    source_dir = temp_dir / "source"
    source_dir.mkdir(exist_ok=True)
    test_file = source_dir / "test.pdf"
    # Create a minimal PDF file (not a real PDF, but good for testing structure)
    test_file.write_bytes(b"%PDF-1.4\nfake pdf content")
    return test_file


def test_pdf_text_extractor_initialization(config_file):
    """Test PDFTextExtractor initialization."""
    extractor = PDFTextExtractor(config_path=config_file)
    assert extractor.config is not None
    assert extractor.source_dir.exists()
    assert extractor.dest_dir.exists()


def test_load_config_file_not_found():
    """Test that FileNotFoundError is raised when config file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        PDFTextExtractor(config_path="nonexistent.yaml")


def test_is_pdf_file(config_file):
    """Test PDF file detection."""
    extractor = PDFTextExtractor(config_path=config_file)

    assert extractor._is_pdf_file(Path("test.pdf")) is True
    assert extractor._is_pdf_file(Path("test.PDF")) is True
    assert extractor._is_pdf_file(Path("test.txt")) is False
    assert extractor._is_pdf_file(Path("test.doc")) is False


@patch("src.main.PdfReader")
def test_extract_text_from_pdf_success(mock_pdf_reader, config_file, test_pdf_file):
    """Test successful text extraction from PDF."""
    extractor = PDFTextExtractor(config_path=config_file)

    # Mock PDF reader
    mock_reader = Mock()
    mock_reader.is_encrypted = False
    mock_page = Mock()
    mock_page.extract_text.return_value = "Test text content"
    mock_reader.pages = [mock_page]
    mock_reader.__len__ = Mock(return_value=1)
    mock_pdf_reader.return_value = mock_reader

    with patch("builtins.open", create=True):
        text = extractor._extract_text_from_pdf(test_pdf_file)

    assert text is not None
    assert "Test text content" in text


@patch("src.main.PdfReader")
def test_extract_text_from_encrypted_pdf(mock_pdf_reader, config_file, test_pdf_file):
    """Test handling of encrypted PDF."""
    extractor = PDFTextExtractor(config_path=config_file)
    extractor.config["pdf_password"] = "test_password"

    # Mock encrypted PDF reader
    mock_reader = Mock()
    mock_reader.is_encrypted = True
    mock_reader.decrypt.return_value = True
    mock_page = Mock()
    mock_page.extract_text.return_value = "Decrypted text"
    mock_reader.pages = [mock_page]
    mock_reader.__len__ = Mock(return_value=1)
    mock_pdf_reader.return_value = mock_reader

    with patch("builtins.open", create=True):
        text = extractor._extract_text_from_pdf(test_pdf_file, password="test_password")

    assert text is not None
    assert "Decrypted text" in text


@patch("src.main.PdfReader")
def test_extract_text_from_encrypted_pdf_no_password(
    mock_pdf_reader, config_file, test_pdf_file
):
    """Test handling of encrypted PDF without password."""
    extractor = PDFTextExtractor(config_path=config_file)
    extractor.config["skip_encrypted"] = True

    # Mock encrypted PDF reader
    mock_reader = Mock()
    mock_reader.is_encrypted = True
    mock_pdf_reader.return_value = mock_reader

    with patch("builtins.open", create=True):
        text = extractor._extract_text_from_pdf(test_pdf_file)

    assert text is None
    assert extractor.stats["encrypted_skipped"] > 0


@patch("src.main.PdfReader")
def test_extract_text_multi_page(mock_pdf_reader, config_file, test_pdf_file):
    """Test text extraction from multi-page PDF."""
    extractor = PDFTextExtractor(config_path=config_file)

    # Mock multi-page PDF reader
    mock_reader = Mock()
    mock_reader.is_encrypted = False
    mock_page1 = Mock()
    mock_page1.extract_text.return_value = "Page 1 content"
    mock_page2 = Mock()
    mock_page2.extract_text.return_value = "Page 2 content"
    mock_reader.pages = [mock_page1, mock_page2]
    mock_reader.__len__ = Mock(return_value=2)
    mock_pdf_reader.return_value = mock_reader

    with patch("builtins.open", create=True):
        text = extractor._extract_text_from_pdf(test_pdf_file)

    assert text is not None
    assert "Page 1" in text
    assert "Page 2" in text
    assert "--- Page 1 ---" in text
    assert "--- Page 2 ---" in text


def test_save_text_to_file_dry_run(config_file, temp_dir):
    """Test saving text file in dry run mode."""
    extractor = PDFTextExtractor(config_path=config_file)
    extractor.config["operations"]["dry_run"] = True
    extractor.dest_dir = temp_dir

    output_path = temp_dir / "test.txt"
    result = extractor._save_text_to_file("Test content", output_path, "test.pdf")

    assert result is True
    assert not output_path.exists()  # File should not exist in dry run


def test_save_text_to_file_actual(config_file, temp_dir):
    """Test actual text file saving."""
    extractor = PDFTextExtractor(config_path=config_file)
    extractor.config["operations"]["dry_run"] = False
    extractor.dest_dir = temp_dir

    output_path = temp_dir / "test.txt"
    result = extractor._save_text_to_file("Test content", output_path, "test.pdf")

    assert result is True
    assert output_path.exists()
    assert output_path.read_text() == "Test content"


def test_process_pdf_file(config_file, test_pdf_file):
    """Test processing a single PDF file."""
    extractor = PDFTextExtractor(config_path=config_file)
    extractor.config["operations"]["dry_run"] = True

    with patch.object(
        extractor, "_extract_text_from_pdf", return_value="Extracted text"
    ):
        result = extractor._process_pdf_file(test_pdf_file)

        assert result is True
        assert extractor.stats["files_processed"] > 0


def test_process_pdf_file_no_text(config_file, test_pdf_file):
    """Test processing PDF file with no extractable text."""
    extractor = PDFTextExtractor(config_path=config_file)

    with patch.object(extractor, "_extract_text_from_pdf", return_value=None):
        result = extractor._process_pdf_file(test_pdf_file)

        assert result is False
        assert extractor.stats["files_skipped"] > 0


def test_extract_text_from_pdfs(config_file, test_pdf_file):
    """Test extracting text from multiple PDFs."""
    extractor = PDFTextExtractor(config_path=config_file)
    extractor.config["operations"]["dry_run"] = True

    # Create additional test PDFs
    source_dir = test_pdf_file.parent
    (source_dir / "test2.pdf").write_bytes(b"%PDF-1.4\nfake pdf")
    (source_dir / "test3.pdf").write_bytes(b"%PDF-1.4\nfake pdf")

    with patch.object(
        extractor, "_extract_text_from_pdf", return_value="Extracted text"
    ):
        stats = extractor.extract_text_from_pdfs()

        assert stats["files_scanned"] >= 3


def test_environment_variable_overrides(temp_dir):
    """Test that environment variables override config."""
    source_dir = temp_dir / "source"
    source_dir.mkdir()
    dest_dir = temp_dir / "dest"
    dest_dir.mkdir()

    config = {
        "source_directory": str(source_dir),
        "destination_directory": str(dest_dir),
        "pdf_password": "",
        "skip_encrypted": True,
        "output_encoding": "utf-8",
        "operations": {
            "create_destination": True,
            "recursive": True,
            "preserve_structure": True,
            "dry_run": False,
        },
        "logging": {
            "level": "INFO",
            "file": str(temp_dir / "test.log"),
            "max_bytes": 10485760,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }
    config_path = temp_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    with patch.dict(os.environ, {"DRY_RUN": "true"}):
        extractor = PDFTextExtractor(config_path=str(config_path))
        assert extractor.config["operations"]["dry_run"] is True
