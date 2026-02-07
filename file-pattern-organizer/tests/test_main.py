"""Unit tests for File Pattern Organizer."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import FilePatternOrganizer


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_config():
    """Create a sample configuration."""
    return {
        "source_dir": "downloads",
        "output_base_dir": "organized",
        "patterns": [
            {
                "pattern": "(?i)invoice",
                "folder": "invoices",
                "description": "Invoice files",
            },
            {
                "pattern": "(?i)receipt",
                "folder": "receipts",
                "description": "Receipt files",
            },
            {
                "pattern": "^\\d{4}-\\d{2}-\\d{2}",
                "folder": "by_date",
                "description": "Date-prefixed files",
            },
        ],
        "default_folder": "misc",
        "options": {
            "move_files": True,
            "dry_run": False,
            "use_capture_groups": False,
            "create_date_subfolders": False,
        },
        "file_handling": {
            "on_conflict": "rename",
            "max_filename_length": 255,
        },
    }


def test_file_pattern_organizer_initialization(sample_config, temp_dir):
    """Test FilePatternOrganizer initialization."""
    sample_config["source_dir"] = str(temp_dir / "source")
    sample_config["output_base_dir"] = str(temp_dir / "output")

    organizer = FilePatternOrganizer(sample_config)

    assert len(organizer.compiled_patterns) == 3
    assert organizer.default_folder == "misc"


def test_match_pattern_invoice(sample_config, temp_dir):
    """Test matching invoice pattern."""
    sample_config["source_dir"] = str(temp_dir / "source")
    sample_config["output_base_dir"] = str(temp_dir / "output")

    organizer = FilePatternOrganizer(sample_config)

    match_info = organizer.match_pattern("invoice_2024.pdf")
    assert match_info is not None
    assert match_info["folder"] == "invoices"

    match_info = organizer.match_pattern("INVOICE_123.pdf")
    assert match_info is not None
    assert match_info["folder"] == "invoices"


def test_match_pattern_receipt(sample_config, temp_dir):
    """Test matching receipt pattern."""
    sample_config["source_dir"] = str(temp_dir / "source")
    sample_config["output_base_dir"] = str(temp_dir / "output")

    organizer = FilePatternOrganizer(sample_config)

    match_info = organizer.match_pattern("receipt_2024.pdf")
    assert match_info is not None
    assert match_info["folder"] == "receipts"


def test_match_pattern_date(sample_config, temp_dir):
    """Test matching date pattern."""
    sample_config["source_dir"] = str(temp_dir / "source")
    sample_config["output_base_dir"] = str(temp_dir / "output")

    organizer = FilePatternOrganizer(sample_config)

    match_info = organizer.match_pattern("2024-01-15_report.pdf")
    assert match_info is not None
    assert match_info["folder"] == "by_date"

    match_info = organizer.match_pattern("2024-12-31_document.pdf")
    assert match_info is not None
    assert match_info["folder"] == "by_date"


def test_match_pattern_no_match(sample_config, temp_dir):
    """Test pattern matching with no match."""
    sample_config["source_dir"] = str(temp_dir / "source")
    sample_config["output_base_dir"] = str(temp_dir / "output")

    organizer = FilePatternOrganizer(sample_config)

    match_info = organizer.match_pattern("random_file.pdf")
    assert match_info is None


def test_get_destination_path_with_match(sample_config, temp_dir):
    """Test getting destination path with pattern match."""
    sample_config["source_dir"] = str(temp_dir / "source")
    sample_config["output_base_dir"] = str(temp_dir / "output")

    organizer = FilePatternOrganizer(sample_config)

    source_path = Path("invoice_123.pdf")
    match_info = organizer.match_pattern("invoice_123.pdf")

    dest_path = organizer.get_destination_path(source_path, match_info)

    assert dest_path.parent.name == "invoices"
    assert dest_path.name == "invoice_123.pdf"


def test_get_destination_path_no_match(sample_config, temp_dir):
    """Test getting destination path with no match."""
    sample_config["source_dir"] = str(temp_dir / "source")
    sample_config["output_base_dir"] = str(temp_dir / "output")

    organizer = FilePatternOrganizer(sample_config)

    source_path = Path("random_file.pdf")

    dest_path = organizer.get_destination_path(source_path, None)

    assert dest_path.parent.name == "misc"
    assert dest_path.name == "random_file.pdf"


def test_get_destination_path_with_date_subfolders(sample_config, temp_dir):
    """Test getting destination path with date subfolders."""
    sample_config["source_dir"] = str(temp_dir / "source")
    sample_config["output_base_dir"] = str(temp_dir / "output")
    sample_config["options"]["create_date_subfolders"] = True

    organizer = FilePatternOrganizer(sample_config)

    source_path = Path("invoice_123.pdf")
    match_info = organizer.match_pattern("invoice_123.pdf")

    dest_path = organizer.get_destination_path(source_path, match_info)

    # Should have date subfolder (YYYY-MM format)
    assert "invoices" in str(dest_path.parent)
    assert len(dest_path.parent.parts) > 1


def test_handle_file_conflict_rename(sample_config, temp_dir):
    """Test handling file conflict with rename."""
    sample_config["source_dir"] = str(temp_dir / "source")
    sample_config["output_base_dir"] = str(temp_dir / "output")
    sample_config["file_handling"]["on_conflict"] = "rename"

    organizer = FilePatternOrganizer(sample_config)

    dest_path = Path(temp_dir / "output" / "invoices" / "invoice.pdf")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.touch()

    new_path = organizer.handle_file_conflict(dest_path)

    assert new_path != dest_path
    assert "invoice" in new_path.name
    assert new_path.suffix == ".pdf"


def test_handle_file_conflict_skip(sample_config, temp_dir):
    """Test handling file conflict with skip."""
    sample_config["source_dir"] = str(temp_dir / "source")
    sample_config["output_base_dir"] = str(temp_dir / "output")
    sample_config["file_handling"]["on_conflict"] = "skip"

    organizer = FilePatternOrganizer(sample_config)

    dest_path = Path(temp_dir / "output" / "invoices" / "invoice.pdf")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.touch()

    new_path = organizer.handle_file_conflict(dest_path)

    assert new_path is None


def test_handle_file_conflict_overwrite(sample_config, temp_dir):
    """Test handling file conflict with overwrite."""
    sample_config["source_dir"] = str(temp_dir / "source")
    sample_config["output_base_dir"] = str(temp_dir / "output")
    sample_config["file_handling"]["on_conflict"] = "overwrite"

    organizer = FilePatternOrganizer(sample_config)

    dest_path = Path(temp_dir / "output" / "invoices" / "invoice.pdf")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.touch()

    new_path = organizer.handle_file_conflict(dest_path)

    assert new_path == dest_path


def test_organize_file_success(sample_config, temp_dir):
    """Test organizing a single file successfully."""
    source_dir = temp_dir / "source"
    output_dir = temp_dir / "output"
    source_dir.mkdir()
    output_dir.mkdir()

    sample_config["source_dir"] = str(source_dir)
    sample_config["output_base_dir"] = str(output_dir)
    sample_config["options"]["move_files"] = True
    sample_config["options"]["dry_run"] = False

    organizer = FilePatternOrganizer(sample_config)

    # Create test file
    test_file = source_dir / "invoice_123.pdf"
    test_file.write_text("test content")

    success, message = organizer.organize_file(test_file)

    assert success is True
    assert "Moved" in message or "invoice_123.pdf" in message
    assert not test_file.exists()  # File should be moved
    assert (output_dir / "invoices" / "invoice_123.pdf").exists()


def test_organize_file_dry_run(sample_config, temp_dir):
    """Test organizing a file in dry run mode."""
    source_dir = temp_dir / "source"
    output_dir = temp_dir / "output"
    source_dir.mkdir()
    output_dir.mkdir()

    sample_config["source_dir"] = str(source_dir)
    sample_config["output_base_dir"] = str(output_dir)
    sample_config["options"]["dry_run"] = True

    organizer = FilePatternOrganizer(sample_config)

    # Create test file
    test_file = source_dir / "invoice_123.pdf"
    test_file.write_text("test content")

    success, message = organizer.organize_file(test_file)

    assert success is True
    assert "Would move" in message or "Would copy" in message
    assert test_file.exists()  # File should not be moved in dry run
    assert not (output_dir / "invoices" / "invoice_123.pdf").exists()


def test_organize_file_copy_mode(sample_config, temp_dir):
    """Test organizing a file in copy mode."""
    source_dir = temp_dir / "source"
    output_dir = temp_dir / "output"
    source_dir.mkdir()
    output_dir.mkdir()

    sample_config["source_dir"] = str(source_dir)
    sample_config["output_base_dir"] = str(output_dir)
    sample_config["options"]["move_files"] = False
    sample_config["options"]["dry_run"] = False

    organizer = FilePatternOrganizer(sample_config)

    # Create test file
    test_file = source_dir / "invoice_123.pdf"
    test_file.write_text("test content")

    success, message = organizer.organize_file(test_file)

    assert success is True
    assert "Copied" in message
    assert test_file.exists()  # File should still exist
    assert (output_dir / "invoices" / "invoice_123.pdf").exists()


def test_organize_directory(sample_config, temp_dir):
    """Test organizing a directory."""
    source_dir = temp_dir / "source"
    output_dir = temp_dir / "output"
    source_dir.mkdir()
    output_dir.mkdir()

    sample_config["source_dir"] = str(source_dir)
    sample_config["output_base_dir"] = str(output_dir)
    sample_config["options"]["move_files"] = True
    sample_config["options"]["dry_run"] = False

    # Create test files
    (source_dir / "invoice_1.pdf").write_text("invoice 1")
    (source_dir / "receipt_1.pdf").write_text("receipt 1")
    (source_dir / "random_file.txt").write_text("random")

    organizer = FilePatternOrganizer(sample_config)
    stats = organizer.organize_directory(source_dir, recursive=False)

    assert stats["organized"] == 3
    assert stats["failed"] == 0
    assert (output_dir / "invoices" / "invoice_1.pdf").exists()
    assert (output_dir / "receipts" / "receipt_1.pdf").exists()
    assert (output_dir / "misc" / "random_file.txt").exists()


def test_invalid_regex_pattern(temp_dir):
    """Test handling invalid regex pattern."""
    config = {
        "source_dir": str(temp_dir / "source"),
        "output_base_dir": str(temp_dir / "output"),
        "patterns": [
            {
                "pattern": "[invalid regex",
                "folder": "test",
                "description": "Invalid pattern",
            },
        ],
        "default_folder": "misc",
        "options": {},
        "file_handling": {},
    }

    organizer = FilePatternOrganizer(config)

    # Should handle invalid pattern gracefully
    assert len(organizer.compiled_patterns) == 0
