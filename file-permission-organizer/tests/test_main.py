"""Unit tests for File Permission Organizer."""

import os
import shutil
import stat
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.main import FilePermissionOrganizer


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
        "permission_folders": {
            "executable": {
                "folder": "executables",
                "check_owner": True,
                "check_group": False,
                "check_other": False,
            },
            "read_only": {
                "folder": "read_only",
                "check_owner": True,
                "check_group": True,
                "check_other": True,
            },
        },
        "permission_patterns": [
            {"pattern": "755", "folder": "permissions_755"},
            {"pattern": "644", "folder": "permissions_644"},
        ],
        "default_folder": "other_permissions",
        "options": {
            "move_files": True,
            "dry_run": False,
        },
        "file_handling": {
            "on_conflict": "rename",
        },
        "exclude_patterns": [],
        "exclude_directories": [],
    }


def test_file_permission_organizer_initialization(sample_config, temp_dir):
    """Test FilePermissionOrganizer initialization."""
    sample_config["source_dir"] = str(temp_dir / "source")
    sample_config["output_base_dir"] = str(temp_dir / "output")

    organizer = FilePermissionOrganizer(sample_config)

    assert organizer.source_dir == temp_dir / "source"
    assert organizer.output_base_dir == temp_dir / "output"


def test_get_file_permissions(sample_config, temp_dir):
    """Test getting file permissions."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")

    organizer = FilePermissionOrganizer(sample_config)
    octal_perms, perm_str = organizer.get_file_permissions(test_file)

    assert isinstance(octal_perms, int)
    assert isinstance(perm_str, str)
    assert len(perm_str) > 0


def test_is_executable(sample_config, temp_dir):
    """Test checking if file is executable."""
    test_file = temp_dir / "test.sh"
    test_file.write_text("#!/bin/bash\necho test")

    # Make file executable
    os.chmod(test_file, 0o755)

    organizer = FilePermissionOrganizer(sample_config)
    is_exec = organizer.is_executable(test_file, check_owner=True)

    assert is_exec is True


def test_is_executable_not_executable(sample_config, temp_dir):
    """Test checking non-executable file."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")

    # Make file non-executable
    os.chmod(test_file, 0o644)

    organizer = FilePermissionOrganizer(sample_config)
    is_exec = organizer.is_executable(test_file, check_owner=True)

    assert is_exec is False


def test_is_read_only(sample_config, temp_dir):
    """Test checking if file is read-only."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")

    # Make file read-only
    os.chmod(test_file, 0o444)

    organizer = FilePermissionOrganizer(sample_config)
    is_ro = organizer.is_read_only(test_file)

    assert is_ro is True


def test_is_read_only_writable(sample_config, temp_dir):
    """Test checking writable file."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")

    # Make file writable
    os.chmod(test_file, 0o644)

    organizer = FilePermissionOrganizer(sample_config)
    is_ro = organizer.is_read_only(test_file)

    assert is_ro is False


def test_get_destination_folder_executable(sample_config, temp_dir):
    """Test getting destination folder for executable file."""
    test_file = temp_dir / "test.sh"
    test_file.write_text("#!/bin/bash")
    os.chmod(test_file, 0o755)

    organizer = FilePermissionOrganizer(sample_config)
    folder = organizer.get_destination_folder(test_file)

    assert folder == "executables"


def test_get_destination_folder_read_only(sample_config, temp_dir):
    """Test getting destination folder for read-only file."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")
    os.chmod(test_file, 0o444)

    organizer = FilePermissionOrganizer(sample_config)
    folder = organizer.get_destination_folder(test_file)

    assert folder == "read_only"


def test_get_destination_folder_pattern_match(sample_config, temp_dir):
    """Test getting destination folder for pattern match."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")
    os.chmod(test_file, 0o755)

    organizer = FilePermissionOrganizer(sample_config)
    folder = organizer.get_destination_folder(test_file)

    # Should match pattern 755 before executable check
    assert folder == "permissions_755"


def test_get_destination_folder_default(sample_config, temp_dir):
    """Test getting default destination folder."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")
    os.chmod(test_file, 0o600)  # Not in patterns, not executable, not read-only

    organizer = FilePermissionOrganizer(sample_config)
    folder = organizer.get_destination_folder(test_file)

    assert folder == "other_permissions"


def test_organize_file_executable(sample_config, temp_dir):
    """Test organizing an executable file."""
    source_dir = temp_dir / "source"
    output_dir = temp_dir / "output"
    source_dir.mkdir()
    output_dir.mkdir()

    sample_config["source_dir"] = str(source_dir)
    sample_config["output_base_dir"] = str(output_dir)
    sample_config["options"]["move_files"] = True
    sample_config["options"]["dry_run"] = False

    test_file = source_dir / "script.sh"
    test_file.write_text("#!/bin/bash")
    os.chmod(test_file, 0o755)

    organizer = FilePermissionOrganizer(sample_config)
    success, message = organizer.organize_file(test_file)

    assert success is True
    assert not test_file.exists()  # File should be moved
    assert (output_dir / "executables" / "script.sh").exists()


def test_organize_file_dry_run(sample_config, temp_dir):
    """Test organizing file in dry run mode."""
    source_dir = temp_dir / "source"
    output_dir = temp_dir / "output"
    source_dir.mkdir()
    output_dir.mkdir()

    sample_config["source_dir"] = str(source_dir)
    sample_config["output_base_dir"] = str(output_dir)
    sample_config["options"]["dry_run"] = True

    test_file = source_dir / "script.sh"
    test_file.write_text("#!/bin/bash")
    os.chmod(test_file, 0o755)

    organizer = FilePermissionOrganizer(sample_config)
    success, message = organizer.organize_file(test_file)

    assert success is True
    assert "Would move" in message or "Would copy" in message
    assert test_file.exists()  # File should not be moved in dry run


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

    # Create test files with different permissions
    exec_file = source_dir / "script.sh"
    exec_file.write_text("#!/bin/bash")
    os.chmod(exec_file, 0o755)

    ro_file = source_dir / "readonly.txt"
    ro_file.write_text("read only")
    os.chmod(ro_file, 0o444)

    normal_file = source_dir / "normal.txt"
    normal_file.write_text("normal")
    os.chmod(normal_file, 0o644)

    organizer = FilePermissionOrganizer(sample_config)
    stats = organizer.organize_directory(source_dir, recursive=False)

    assert stats["organized"] == 3
    assert stats["failed"] == 0
    assert (output_dir / "executables" / "script.sh").exists()
    assert (output_dir / "read_only" / "readonly.txt").exists()
    assert (output_dir / "permissions_644" / "normal.txt").exists()


def test_should_exclude_file(sample_config, temp_dir):
    """Test file exclusion."""
    sample_config["exclude_patterns"] = ["\\.tmp$"]

    organizer = FilePermissionOrganizer(sample_config)

    assert organizer.should_exclude_file(temp_dir / "file.tmp") is True
    assert organizer.should_exclude_file(temp_dir / "file.txt") is False


def test_should_exclude_directory(sample_config, temp_dir):
    """Test directory exclusion."""
    sample_config["exclude_directories"] = ["^\\.git$"]

    organizer = FilePermissionOrganizer(sample_config)

    assert organizer.should_exclude_directory(temp_dir / ".git") is True
    assert organizer.should_exclude_directory(temp_dir / "normal_dir") is False
