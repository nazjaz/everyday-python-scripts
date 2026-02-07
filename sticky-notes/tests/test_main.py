"""Unit tests for sticky notes manager module."""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.main import StickyNotesManager


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    return tempfile.mkdtemp()


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary configuration file."""
    db_file = Path(temp_dir) / "test.db"
    config = {
        "database": {
            "file": str(db_file),
            "create_tables": True,
        },
        "defaults": {
            "width": 300,
            "height": 200,
            "font_family": "Arial",
            "font_size": 10,
            "default_color": "#FFEB3B",
            "default_category": "General",
        },
        "colors": [
            {"name": "Yellow", "code": "#FFEB3B"},
            {"name": "Green", "code": "#4CAF50"},
        ],
        "categories": ["General", "Work", "Personal"],
        "gui": {
            "window_title": "Test Sticky Notes",
            "window_width": 800,
            "window_height": 600,
        },
        "auto_save": {
            "enabled": True,
            "interval": 5,
        },
        "logging": {
            "level": "DEBUG",
            "file": f"{temp_dir}/test.log",
            "max_bytes": 1048576,
            "backup_count": 3,
        },
    }

    config_path = Path(temp_dir) / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config_path


def test_sticky_notes_manager_initialization(config_file):
    """Test StickyNotesManager initializes correctly."""
    manager = StickyNotesManager(config_path=str(config_file))
    assert manager.db_path.exists()
    assert len(manager.notes) == 0


def test_sticky_notes_manager_missing_config():
    """Test StickyNotesManager raises error for missing config."""
    with pytest.raises(FileNotFoundError):
        StickyNotesManager(config_path="nonexistent.yaml")


def test_create_tables(config_file):
    """Test database table creation."""
    manager = StickyNotesManager(config_path=str(config_file))

    # Verify tables exist
    conn = sqlite3.connect(manager.db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='notes'
    """)
    result = cursor.fetchone()
    conn.close()

    assert result is not None
    assert result[0] == "notes"


def test_save_note_new(config_file):
    """Test saving a new note."""
    manager = StickyNotesManager(config_path=str(config_file))

    note_id = manager._save_note(
        None,
        "Test Note",
        "Test content",
        "#FFEB3B",
        "General",
    )

    assert note_id is not None

    # Verify note was saved
    conn = sqlite3.connect(manager.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    result = cursor.fetchone()
    conn.close()

    assert result is not None
    assert result[1] == "Test Note"
    assert result[2] == "Test content"


def test_save_note_update(config_file):
    """Test updating an existing note."""
    manager = StickyNotesManager(config_path=str(config_file))

    # Create note
    note_id = manager._save_note(
        None,
        "Original Title",
        "Original content",
        "#FFEB3B",
        "General",
    )

    # Update note
    manager._save_note(
        note_id,
        "Updated Title",
        "Updated content",
        "#4CAF50",
        "Work",
    )

    # Verify update
    conn = sqlite3.connect(manager.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    result = cursor.fetchone()
    conn.close()

    assert result[1] == "Updated Title"
    assert result[2] == "Updated content"
    assert result[3] == "#4CAF50"
    assert result[4] == "Work"


def test_delete_note(config_file):
    """Test deleting a note."""
    manager = StickyNotesManager(config_path=str(config_file))

    # Create note
    note_id = manager._save_note(
        None,
        "Note to Delete",
        "Content",
        "#FFEB3B",
        "General",
    )

    # Delete note
    result = manager._delete_note(note_id)
    assert result is True

    # Verify deletion
    conn = sqlite3.connect(manager.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM notes WHERE id = ?", (note_id,))
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 0


def test_load_notes(config_file):
    """Test loading notes from database."""
    manager = StickyNotesManager(config_path=str(config_file))

    # Create test notes
    manager._save_note(None, "Note 1", "Content 1", "#FFEB3B", "General")
    manager._save_note(None, "Note 2", "Content 2", "#4CAF50", "Work")

    # Load notes
    manager._load_notes()

    assert len(manager.notes) == 2
    assert any(note["title"] == "Note 1" for note in manager.notes.values())
    assert any(note["title"] == "Note 2" for note in manager.notes.values())


def test_filter_notes(config_file):
    """Test filtering notes by category."""
    manager = StickyNotesManager(config_path=str(config_file))

    # Create notes in different categories
    manager._save_note(None, "Work Note", "Content", "#FFEB3B", "Work")
    manager._save_note(None, "Personal Note", "Content", "#4CAF50", "Personal")

    manager._load_notes()

    # Mock listbox
    manager.note_listbox = MagicMock()
    manager._current_filter = "All"

    # Filter by Work
    manager._filter_notes("Work")

    # Verify listbox was updated
    assert manager.note_listbox.delete.called
    assert manager.note_listbox.insert.called
