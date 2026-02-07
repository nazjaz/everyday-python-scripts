"""Unit tests for Note Taker application."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import NoteTakerApp


@pytest.fixture
def sample_config():
    """Create sample configuration dictionary."""
    return {
        "data": {"directory": "data"},
        "app": {"title": "Note Taker", "window_size": "1000x700"},
        "logging": {
            "level": "INFO",
            "file": "logs/test.log",
            "max_bytes": 10485760,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }


@pytest.fixture
def temp_config_file(sample_config, tmp_path):
    """Create temporary configuration file."""
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(sample_config, f)
    return str(config_path)


@pytest.fixture
def temp_data_directory(tmp_path):
    """Create temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


class TestNoteTakerApp:
    """Test cases for NoteTakerApp class."""

    @patch("src.main.Tk")
    def test_init_loads_config(self, mock_tk, temp_config_file, tmp_path):
        """Test that initialization loads configuration file."""
        # Mock Tk to avoid GUI initialization
        mock_root = Mock()
        mock_tk.return_value = mock_root

        app = NoteTakerApp(config_path=temp_config_file)
        assert app.config is not None
        assert "data" in app.config

    @patch("src.main.Tk")
    def test_init_uses_default_config(self, mock_tk):
        """Test that initialization uses default config if file not found."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        app = NoteTakerApp(config_path="nonexistent.yaml")
        assert app.config is not None
        assert "data" in app.config

    @patch("src.main.Tk")
    def test_generate_note_id(self, mock_tk, temp_config_file):
        """Test note ID generation."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        app = NoteTakerApp(config_path=temp_config_file)
        note_id1 = app._generate_note_id()
        note_id2 = app._generate_note_id()

        assert note_id1.startswith("note_")
        assert note_id2.startswith("note_")
        assert note_id1 != note_id2

    @patch("src.main.Tk")
    def test_load_notes_existing_file(
        self, mock_tk, temp_config_file, tmp_path
    ):
        """Test loading notes from existing file."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # Create notes file
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        notes_file = data_dir / "notes.json"
        test_notes = {
            "note_1": {
                "title": "Test Note",
                "content": "Test content",
                "tags": ["test"],
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }
        }
        with open(notes_file, "w", encoding="utf-8") as f:
            json.dump(test_notes, f)

        # Update config to use temp directory
        with open(temp_config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        config["data"]["directory"] = str(data_dir)
        with open(temp_config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        app = NoteTakerApp(config_path=temp_config_file)
        assert len(app.notes) == 1
        assert "note_1" in app.notes

    @patch("src.main.Tk")
    def test_load_notes_no_file(self, mock_tk, temp_config_file, tmp_path):
        """Test loading notes when file doesn't exist."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # Update config to use temp directory
        with open(temp_config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        config["data"]["directory"] = str(tmp_path / "data")
        with open(temp_config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        app = NoteTakerApp(config_path=temp_config_file)
        assert len(app.notes) == 0

    @patch("src.main.Tk")
    def test_save_notes(self, mock_tk, temp_config_file, tmp_path):
        """Test saving notes."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # Update config to use temp directory
        with open(temp_config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        config["data"]["directory"] = str(data_dir)
        with open(temp_config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        app = NoteTakerApp(config_path=temp_config_file)
        app.notes["test_note"] = {
            "title": "Test",
            "content": "Content",
            "tags": [],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        app._save_notes()

        notes_file = data_dir / "notes.json"
        assert notes_file.exists()
        with open(notes_file, "r", encoding="utf-8") as f:
            saved_notes = json.load(f)
        assert "test_note" in saved_notes

    @patch("src.main.Tk")
    def test_refresh_note_list(self, mock_tk, temp_config_file):
        """Test refreshing note list."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        app = NoteTakerApp(config_path=temp_config_file)
        app.notes = {
            "note_1": {
                "title": "Note 1",
                "content": "Content 1",
                "tags": ["tag1"],
            },
            "note_2": {
                "title": "Note 2",
                "content": "Content 2",
                "tags": ["tag2"],
            },
        }

        # Mock listbox
        app.note_listbox = Mock()
        app.search_entry = Mock()
        app.search_entry.get.return_value = ""
        app.tag_filter = Mock()
        app.tag_filter.get.return_value = "All"

        app._refresh_note_list()

        # Verify listbox was updated
        assert app.note_listbox.delete.called
        assert app.note_listbox.insert.called

    @patch("src.main.Tk")
    def test_load_note(self, mock_tk, temp_config_file):
        """Test loading a note into editor."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        app = NoteTakerApp(config_path=temp_config_file)
        app.notes = {
            "note_1": {
                "title": "Test Note",
                "content": "Test content",
                "tags": ["test", "example"],
            }
        }

        # Mock GUI elements
        app.title_entry = Mock()
        app.tags_entry = Mock()
        app.content_text = Mock()
        app.preview_text = Mock()

        app._load_note("note_1")

        assert app.current_note_id == "note_1"
        assert app.title_entry.insert.called
        assert app.tags_entry.insert.called
        assert app.content_text.insert.called

    @patch("src.main.Tk")
    def test_new_note(self, mock_tk, temp_config_file):
        """Test creating a new note."""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        app = NoteTakerApp(config_path=temp_config_file)
        app.current_note_id = "old_note"

        # Mock GUI elements
        app.title_entry = Mock()
        app.tags_entry = Mock()
        app.content_text = Mock()
        app.preview_text = Mock()

        app._new_note()

        assert app.current_note_id is None
        assert app.title_entry.delete.called
        assert app.tags_entry.delete.called
        assert app.content_text.delete.called
