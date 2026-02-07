"""Unit tests for Document Organizer."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.main import DocumentOrganizer


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
        "categories": {
            "pdfs": {
                "folder": "PDFs",
                "extensions": [".pdf"],
                "mime_types": ["application/pdf"],
            },
            "word_documents": {
                "folder": "Word-Documents",
                "extensions": [".doc", ".docx"],
                "mime_types": ["application/msword"],
            },
            "spreadsheets": {
                "folder": "Spreadsheets",
                "extensions": [".xls", ".xlsx"],
                "mime_types": ["application/vnd.ms-excel"],
            },
            "presentations": {
                "folder": "Presentations",
                "extensions": [".ppt", ".pptx"],
                "mime_types": ["application/vnd.ms-powerpoint"],
            },
        },
        "duplicate_handling": "rename",
        "exclusions": {"patterns": [], "extensions": []},
        "operations": {
            "create_directories": True,
            "recursive": True,
            "method": "move",
            "preserve_timestamps": True,
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
def test_files(temp_dir):
    """Create test document files."""
    source_dir = temp_dir / "source"
    source_dir.mkdir(exist_ok=True)

    (source_dir / "document.pdf").write_text("fake pdf")
    (source_dir / "document.docx").write_text("fake docx")
    (source_dir / "spreadsheet.xlsx").write_text("fake xlsx")
    (source_dir / "presentation.pptx").write_text("fake pptx")

    return source_dir


def test_document_organizer_initialization(config_file):
    """Test DocumentOrganizer initialization."""
    organizer = DocumentOrganizer(config_path=config_file)
    assert organizer.config is not None
    assert organizer.source_dir.exists()
    assert organizer.dest_base.exists()


def test_load_config_file_not_found():
    """Test that FileNotFoundError is raised when config file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        DocumentOrganizer(config_path="nonexistent.yaml")


def test_get_document_category_by_extension(config_file, test_files):
    """Test document category detection by extension."""
    organizer = DocumentOrganizer(config_path=config_file)

    pdf_file = test_files / "document.pdf"
    category = organizer._get_document_category(pdf_file)
    assert category == "pdfs"

    docx_file = test_files / "document.docx"
    category = organizer._get_document_category(docx_file)
    assert category == "word_documents"

    xlsx_file = test_files / "spreadsheet.xlsx"
    category = organizer._get_document_category(xlsx_file)
    assert category == "spreadsheets"

    pptx_file = test_files / "presentation.pptx"
    category = organizer._get_document_category(pptx_file)
    assert category == "presentations"


def test_get_document_category_unknown(config_file, temp_dir):
    """Test category detection for unknown file type."""
    organizer = DocumentOrganizer(config_path=config_file)

    unknown_file = temp_dir / "unknown.txt"
    unknown_file.write_text("test")
    category = organizer._get_document_category(unknown_file)
    assert category is None


def test_get_mime_type(config_file, test_files):
    """Test MIME type detection."""
    organizer = DocumentOrganizer(config_path=config_file)

    pdf_file = test_files / "document.pdf"
    mime_type = organizer._get_mime_type(pdf_file)
    # Should detect PDF MIME type or return None if python-magic not available
    assert mime_type is None or "pdf" in mime_type.lower()


def test_should_organize_file(config_file, temp_dir):
    """Test file exclusion logic."""
    organizer = DocumentOrganizer(config_path=config_file)

    normal_file = temp_dir / "document.pdf"
    normal_file.write_text("test")
    assert organizer._should_organize_file(normal_file) is True

    # Test exclusion by pattern
    organizer.config["exclusions"]["patterns"] = [".tmp"]
    excluded_file = temp_dir / "document.tmp.pdf"
    excluded_file.write_text("test")
    assert organizer._should_organize_file(excluded_file) is False


def test_handle_duplicate_rename(config_file, temp_dir):
    """Test duplicate handling with rename option."""
    organizer = DocumentOrganizer(config_path=config_file)
    organizer.config["duplicate_handling"] = "rename"

    source_file = temp_dir / "document.pdf"
    source_file.write_text("test")
    dest_dir = temp_dir / "PDFs"
    dest_dir.mkdir()
    existing_file = dest_dir / "document.pdf"
    existing_file.write_text("existing")

    result = organizer._handle_duplicate(source_file, existing_file)

    assert result is not None
    assert result != existing_file
    assert "_1" in result.name


def test_handle_duplicate_skip(config_file, temp_dir):
    """Test duplicate handling with skip option."""
    organizer = DocumentOrganizer(config_path=config_file)
    organizer.config["duplicate_handling"] = "skip"

    source_file = temp_dir / "document.pdf"
    source_file.write_text("test")
    dest_dir = temp_dir / "PDFs"
    dest_dir.mkdir()
    existing_file = dest_dir / "document.pdf"
    existing_file.write_text("existing")

    result = organizer._handle_duplicate(source_file, existing_file)

    assert result is None
    assert organizer.stats["files_skipped"] > 0


def test_organize_file_dry_run(config_file, test_files):
    """Test file organization in dry run mode."""
    organizer = DocumentOrganizer(config_path=config_file)
    organizer.config["operations"]["dry_run"] = True

    pdf_file = test_files / "document.pdf"
    result = organizer._organize_file(pdf_file)

    assert result is True
    assert pdf_file.exists()  # File should still exist in dry run
    assert organizer.stats["files_organized"] > 0


def test_organize_file_actual(config_file, test_files):
    """Test actual file organization."""
    organizer = DocumentOrganizer(config_path=config_file)
    organizer.config["operations"]["dry_run"] = False
    organizer.config["operations"]["method"] = "move"

    pdf_file = test_files / "document.pdf"
    result = organizer._organize_file(pdf_file)

    assert result is True
    assert not pdf_file.exists()  # File should be moved
    dest_file = organizer.dest_base / "PDFs" / "document.pdf"
    assert dest_file.exists()


def test_organize_documents(config_file, test_files):
    """Test organizing multiple documents."""
    organizer = DocumentOrganizer(config_path=config_file)
    organizer.config["operations"]["dry_run"] = True

    stats = organizer.organize_documents()

    assert stats["files_scanned"] >= 4
    assert stats["files_organized"] >= 0


def test_environment_variable_overrides(temp_dir):
    """Test that environment variables override config."""
    source_dir = temp_dir / "source"
    source_dir.mkdir()
    dest_dir = temp_dir / "dest"
    dest_dir.mkdir()

    config = {
        "source_directory": str(source_dir),
        "destination_directory": str(dest_dir),
        "categories": {
            "pdfs": {
                "folder": "PDFs",
                "extensions": [".pdf"],
                "mime_types": [],
            },
        },
        "duplicate_handling": "rename",
        "exclusions": {"patterns": [], "extensions": []},
        "operations": {
            "create_directories": True,
            "recursive": True,
            "method": "move",
            "preserve_timestamps": True,
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
        organizer = DocumentOrganizer(config_path=str(config_path))
        assert organizer.config["operations"]["dry_run"] is True
