"""Unit tests for color picker module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.main import ColorPicker


class TestColorPicker:
    """Test cases for ColorPicker class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def config_file(self, temp_dir):
        """Create temporary config file."""
        config = {
            "window": {"width": 600, "height": 500},
            "palette": {"save_file": "palettes.json"},
            "logging": {"level": "INFO", "file": "logs/app.log"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return str(config_path)

    @pytest.fixture
    def color_picker(self, config_file):
        """Create ColorPicker instance with mocked GUI."""
        with patch("src.main.Tk"):
            picker = ColorPicker(config_path=config_file)
            return picker

    def test_load_config_success(self, temp_dir):
        """Test successful configuration loading."""
        config = {
            "window": {"width": 800},
            "palette": {"save_file": "test.json"},
            "logging": {"level": "DEBUG"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        with patch("src.main.Tk"):
            picker = ColorPicker(config_path=str(config_path))
            assert picker.config["window"]["width"] == 800

    def test_load_config_file_not_found(self):
        """Test FileNotFoundError when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            with patch("src.main.Tk"):
                ColorPicker(config_path="nonexistent.yaml")

    def test_load_config_invalid_yaml(self, temp_dir):
        """Test YAMLError when config file is invalid."""
        config_path = temp_dir / "invalid.yaml"
        with open(config_path, "w") as f:
            f.write("invalid: yaml: content: [unclosed")

        with pytest.raises(yaml.YAMLError):
            with patch("src.main.Tk"):
                ColorPicker(config_path=str(config_path))

    def test_hex_to_rgb_valid(self, color_picker):
        """Test hex to RGB conversion with valid hex."""
        result = color_picker._hex_to_rgb("#FF0000")
        assert result == (255, 0, 0)

    def test_hex_to_rgb_without_hash(self, color_picker):
        """Test hex to RGB conversion without # prefix."""
        result = color_picker._hex_to_rgb("00FF00")
        assert result == (0, 255, 0)

    def test_hex_to_rgb_invalid(self, color_picker):
        """Test hex to RGB conversion with invalid hex."""
        result = color_picker._hex_to_rgb("INVALID")
        assert result == (0, 0, 0)

    def test_hex_to_rgb_short(self, color_picker):
        """Test hex to RGB conversion with short hex."""
        result = color_picker._hex_to_rgb("#FF")
        assert result == (0, 0, 0)

    def test_rgb_to_hex_valid(self, color_picker):
        """Test RGB to hex conversion with valid values."""
        result = color_picker._rgb_to_hex(255, 0, 128)
        assert result == "#FF0080"

    def test_rgb_to_hex_zero(self, color_picker):
        """Test RGB to hex conversion with zero values."""
        result = color_picker._rgb_to_hex(0, 0, 0)
        assert result == "#000000"

    def test_rgb_to_hex_max(self, color_picker):
        """Test RGB to hex conversion with max values."""
        result = color_picker._rgb_to_hex(255, 255, 255)
        assert result == "#FFFFFF"

    def test_update_color_display(self, color_picker):
        """Test updating color display."""
        color_picker.color_canvas = MagicMock()
        color_picker.hex_entry = MagicMock()
        color_picker.rgb_label = MagicMock()

        color_picker._update_color_display("#FF0000")

        assert color_picker.current_color == "#FF0000"
        color_picker.hex_entry.delete.assert_called_once()
        color_picker.hex_entry.insert.assert_called_once()

    def test_add_to_palette_with_color(self, color_picker):
        """Test adding color to palette when color is selected."""
        color_picker.current_color = "#FF0000"
        color_picker._update_palette_display = MagicMock()

        color_picker._add_to_palette()

        assert len(color_picker.palette) == 1
        assert color_picker.palette[0]["hex"] == "#FF0000"

    def test_add_to_palette_no_color(self, color_picker):
        """Test adding to palette when no color is selected."""
        color_picker.current_color = None
        color_picker._update_palette_display = MagicMock()

        with patch("src.main.messagebox") as mock_msg:
            color_picker._add_to_palette()
            mock_msg.showwarning.assert_called_once()

    def test_remove_from_palette(self, color_picker):
        """Test removing color from palette."""
        color_picker.palette = [
            {"hex": "#FF0000", "rgb": "(255, 0, 0)"},
            {"hex": "#00FF00", "rgb": "(0, 255, 0)"},
        ]
        color_picker.palette_listbox = MagicMock()
        color_picker.palette_listbox.curselection.return_value = (0,)
        color_picker._update_palette_display = MagicMock()

        color_picker._remove_from_palette()

        assert len(color_picker.palette) == 1
        assert color_picker.palette[0]["hex"] == "#00FF00"

    def test_clear_palette(self, color_picker):
        """Test clearing palette."""
        color_picker.palette = [
            {"hex": "#FF0000", "rgb": "(255, 0, 0)"},
        ]
        color_picker._update_palette_display = MagicMock()

        with patch("src.main.messagebox") as mock_msg:
            mock_msg.askyesno.return_value = True
            color_picker._clear_palette()
            assert len(color_picker.palette) == 0

    def test_load_palettes_data_existing_file(self, color_picker, temp_dir):
        """Test loading palettes from existing file."""
        palette_file = temp_dir / "palettes.json"
        data = {
            "palettes": {
                "test": {"colors": [{"hex": "#FF0000", "rgb": "(255, 0, 0)"}]}
            },
            "default_palette": None,
        }
        with open(palette_file, "w") as f:
            json.dump(data, f)

        color_picker.palette_file = palette_file
        result = color_picker._load_palettes_data()

        assert "palettes" in result
        assert "test" in result["palettes"]

    def test_load_palettes_data_missing_file(self, color_picker, temp_dir):
        """Test loading palettes when file doesn't exist."""
        palette_file = temp_dir / "nonexistent.json"
        color_picker.palette_file = palette_file

        result = color_picker._load_palettes_data()

        assert result == {"palettes": {}, "default_palette": None}

    def test_load_palettes_data_invalid_json(self, color_picker, temp_dir):
        """Test loading palettes with invalid JSON."""
        palette_file = temp_dir / "invalid.json"
        with open(palette_file, "w") as f:
            f.write("invalid json content")

        color_picker.palette_file = palette_file
        result = color_picker._load_palettes_data()

        assert result == {"palettes": {}, "default_palette": None}

    def test_save_palette(self, color_picker, temp_dir):
        """Test saving palette to file."""
        color_picker.palette = [
            {"hex": "#FF0000", "rgb": "(255, 0, 0)"},
        ]
        color_picker.palette_file = temp_dir / "test_palettes.json"

        with patch("src.main.simpledialog") as mock_dialog:
            mock_dialog.askstring.return_value = "test_palette"
            with patch("src.main.messagebox") as mock_msg:
                color_picker._save_palette()
                mock_msg.showinfo.assert_called_once()

        assert color_picker.palette_file.exists()
        with open(color_picker.palette_file) as f:
            data = json.load(f)
        assert "test_palette" in data["palettes"]

    def test_save_palette_empty(self, color_picker):
        """Test saving empty palette."""
        color_picker.palette = []

        with patch("src.main.messagebox") as mock_msg:
            color_picker._save_palette()
            mock_msg.showwarning.assert_called_once()

    def test_load_palette(self, color_picker, temp_dir):
        """Test loading palette from file."""
        palette_file = temp_dir / "palettes.json"
        data = {
            "palettes": {
                "test": {
                    "colors": [{"hex": "#FF0000", "rgb": "(255, 0, 0)"}]
                }
            },
            "default_palette": None,
        }
        with open(palette_file, "w") as f:
            json.dump(data, f)

        color_picker.palette_file = palette_file
        color_picker._update_palette_display = MagicMock()

        with patch("src.main.simpledialog") as mock_dialog:
            mock_dialog.askstring.return_value = "test"
            with patch("src.main.messagebox") as mock_msg:
                color_picker._load_palette()
                mock_msg.showinfo.assert_called_once()

        assert len(color_picker.palette) == 1
        assert color_picker.palette[0]["hex"] == "#FF0000"
