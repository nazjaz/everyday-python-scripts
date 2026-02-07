"""Unit tests for Script Organizer."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.main import ScriptOrganizer


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
        "source_dir": "scripts",
        "output_base_dir": "organized",
        "language_extensions": {
            "python": {
                "extensions": ["py"],
                "folder": "Python",
            },
            "javascript": {
                "extensions": ["js"],
                "folder": "JavaScript",
            },
            "shell": {
                "extensions": ["sh"],
                "folder": "Shell",
            },
        },
        "shebang_patterns": {
            "python": {
                "patterns": ["python", "python3"],
                "folder": "Python",
            },
            "shell": {
                "patterns": ["bash", "sh"],
                "folder": "Shell",
            },
        },
        "default_folder": "Unknown",
        "options": {
            "move_files": True,
            "dry_run": False,
            "detection_priority": "extension",
        },
        "file_handling": {
            "on_conflict": "rename",
        },
        "exclude_patterns": [],
        "exclude_directories": [],
    }


def test_script_organizer_initialization(sample_config, temp_dir):
    """Test ScriptOrganizer initialization."""
    sample_config["source_dir"] = str(temp_dir / "source")
    sample_config["output_base_dir"] = str(temp_dir / "output")

    organizer = ScriptOrganizer(sample_config)

    assert "py" in organizer.extension_to_language
    assert organizer.extension_to_language["py"]["folder"] == "Python"


def test_get_language_by_extension(sample_config, temp_dir):
    """Test getting language by extension."""
    organizer = ScriptOrganizer(sample_config)

    lang_info = organizer.get_language_by_extension(Path("script.py"))
    assert lang_info is not None
    assert lang_info["folder"] == "Python"

    lang_info = organizer.get_language_by_extension(Path("script.js"))
    assert lang_info is not None
    assert lang_info["folder"] == "JavaScript"


def test_get_shebang_language(sample_config, temp_dir):
    """Test getting language from shebang."""
    test_file = temp_dir / "script"
    test_file.write_text("#!/usr/bin/python3\nprint('test')")

    organizer = ScriptOrganizer(sample_config)
    lang_info = organizer.get_shebang_language(test_file)

    assert lang_info is not None
    assert lang_info["folder"] == "Python"


def test_get_shebang_language_bash(sample_config, temp_dir):
    """Test getting bash from shebang."""
    test_file = temp_dir / "script"
    test_file.write_text("#!/bin/bash\necho test")

    organizer = ScriptOrganizer(sample_config)
    lang_info = organizer.get_shebang_language(test_file)

    assert lang_info is not None
    assert lang_info["folder"] == "Shell"


def test_get_shebang_language_env_pattern(sample_config, temp_dir):
    """Test getting language from env shebang pattern."""
    test_file = temp_dir / "script"
    test_file.write_text("#!/usr/bin/env python3\nprint('test')")

    organizer = ScriptOrganizer(sample_config)
    lang_info = organizer.get_shebang_language(test_file)

    assert lang_info is not None
    assert lang_info["folder"] == "Python"


def test_get_shebang_language_no_shebang(sample_config, temp_dir):
    """Test file without shebang."""
    test_file = temp_dir / "script.txt"
    test_file.write_text("no shebang here")

    organizer = ScriptOrganizer(sample_config)
    lang_info = organizer.get_shebang_language(test_file)

    assert lang_info is None


def test_get_language_folder_by_extension(sample_config, temp_dir):
    """Test getting language folder by extension."""
    organizer = ScriptOrganizer(sample_config)

    folder = organizer.get_language_folder(Path("script.py"))
    assert folder == "Python"


def test_get_language_folder_by_shebang(sample_config, temp_dir):
    """Test getting language folder by shebang."""
    test_file = temp_dir / "script"
    test_file.write_text("#!/usr/bin/python3\nprint('test')")

    organizer = ScriptOrganizer(sample_config)
    folder = organizer.get_language_folder(test_file)

    assert folder == "Python"


def test_get_language_folder_priority_extension(sample_config, temp_dir):
    """Test detection priority with extension first."""
    test_file = temp_dir / "script.py"
    test_file.write_text("#!/bin/bash\necho test")

    sample_config["options"]["detection_priority"] = "extension"
    organizer = ScriptOrganizer(sample_config)
    folder = organizer.get_language_folder(test_file)

    # Should use extension (Python) not shebang (Shell)
    assert folder == "Python"


def test_get_language_folder_priority_shebang(sample_config, temp_dir):
    """Test detection priority with shebang first."""
    test_file = temp_dir / "script.py"
    test_file.write_text("#!/bin/bash\necho test")

    sample_config["options"]["detection_priority"] = "shebang"
    organizer = ScriptOrganizer(sample_config)
    folder = organizer.get_language_folder(test_file)

    # Should use shebang (Shell) not extension (Python)
    assert folder == "Shell"


def test_get_language_folder_default(sample_config, temp_dir):
    """Test getting default folder for unknown language."""
    test_file = temp_dir / "script.unknown"

    organizer = ScriptOrganizer(sample_config)
    folder = organizer.get_language_folder(test_file)

    assert folder == "Unknown"


def test_organize_file_by_extension(sample_config, temp_dir):
    """Test organizing file by extension."""
    source_dir = temp_dir / "source"
    output_dir = temp_dir / "output"
    source_dir.mkdir()
    output_dir.mkdir()

    sample_config["source_dir"] = str(source_dir)
    sample_config["output_base_dir"] = str(output_dir)
    sample_config["options"]["move_files"] = True
    sample_config["options"]["dry_run"] = False

    test_file = source_dir / "script.py"
    test_file.write_text("print('test')")

    organizer = ScriptOrganizer(sample_config)
    success, message = organizer.organize_file(test_file)

    assert success is True
    assert not test_file.exists()  # File should be moved
    assert (output_dir / "Python" / "script.py").exists()


def test_organize_file_by_shebang(sample_config, temp_dir):
    """Test organizing file by shebang."""
    source_dir = temp_dir / "source"
    output_dir = temp_dir / "output"
    source_dir.mkdir()
    output_dir.mkdir()

    sample_config["source_dir"] = str(source_dir)
    sample_config["output_base_dir"] = str(output_dir)
    sample_config["options"]["move_files"] = True
    sample_config["options"]["dry_run"] = False
    sample_config["options"]["detection_priority"] = "shebang"

    test_file = source_dir / "script"
    test_file.write_text("#!/usr/bin/python3\nprint('test')")

    organizer = ScriptOrganizer(sample_config)
    success, message = organizer.organize_file(test_file)

    assert success is True
    assert (output_dir / "Python" / "script").exists()


def test_organize_file_dry_run(sample_config, temp_dir):
    """Test organizing file in dry run mode."""
    source_dir = temp_dir / "source"
    output_dir = temp_dir / "output"
    source_dir.mkdir()
    output_dir.mkdir()

    sample_config["source_dir"] = str(source_dir)
    sample_config["output_base_dir"] = str(output_dir)
    sample_config["options"]["dry_run"] = True

    test_file = source_dir / "script.py"
    test_file.write_text("print('test')")

    organizer = ScriptOrganizer(sample_config)
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

    # Create test files
    (source_dir / "script1.py").write_text("print('test')")
    (source_dir / "script2.js").write_text("console.log('test')")
    (source_dir / "script3.sh").write_text("#!/bin/bash\necho test")

    organizer = ScriptOrganizer(sample_config)
    stats = organizer.organize_directory(source_dir, recursive=False)

    assert stats["organized"] == 3
    assert stats["failed"] == 0
    assert (output_dir / "Python" / "script1.py").exists()
    assert (output_dir / "JavaScript" / "script2.js").exists()
    assert (output_dir / "Shell" / "script3.sh").exists()


def test_should_exclude_file(sample_config, temp_dir):
    """Test file exclusion."""
    sample_config["exclude_patterns"] = ["\\.tmp$"]

    organizer = ScriptOrganizer(sample_config)

    assert organizer.should_exclude_file(temp_dir / "file.tmp") is True
    assert organizer.should_exclude_file(temp_dir / "file.py") is False


def test_should_exclude_directory(sample_config, temp_dir):
    """Test directory exclusion."""
    sample_config["exclude_directories"] = ["^\\.git$"]

    organizer = ScriptOrganizer(sample_config)

    assert organizer.should_exclude_directory(temp_dir / ".git") is True
    assert organizer.should_exclude_directory(temp_dir / "normal_dir") is False
