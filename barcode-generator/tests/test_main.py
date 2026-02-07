"""Unit tests for Barcode Generator."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.main import BarcodeGeneratorApp


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config(temp_dir):
    """Create a sample configuration file."""
    config_path = temp_dir / "config.yaml"
    config = {
        "barcode": {
            "additional_formats": [],
            "writer_options": {
                "module_width": 0.5,
                "module_height": 15.0,
                "quiet_zone": 6.5,
                "font_size": 10,
                "text_distance": 5.0,
                "background": "white",
                "foreground": "black",
                "center_text": True,
                "write_text": True,
            },
        },
        "logging": {"level": "INFO", "file": "logs/test.log"},
    }
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return str(config_path)


class TestBarcodeGeneratorApp:
    """Test cases for BarcodeGeneratorApp class."""

    def test_init_loads_config(self, sample_config):
        """Test that app loads configuration correctly."""
        with patch("src.main.Tk"):
            app = BarcodeGeneratorApp(config_path=sample_config)
            assert app.config is not None
            assert "barcode" in app.config

    def test_init_raises_on_missing_config(self):
        """Test that init raises FileNotFoundError for missing config."""
        with patch("src.main.Tk"):
            with pytest.raises(FileNotFoundError):
                BarcodeGeneratorApp(config_path="nonexistent.yaml")

    def test_load_supported_formats(self, sample_config):
        """Test that supported formats are loaded correctly."""
        with patch("src.main.Tk"):
            app = BarcodeGeneratorApp(config_path=sample_config)
            assert "EAN-13" in app.supported_formats
            assert "Code128" in app.supported_formats
            assert "Code39" in app.supported_formats
            assert "EAN-8" in app.supported_formats

    def test_validate_code_ean13_valid(self, sample_config):
        """Test EAN-13 code validation with valid code."""
        with patch("src.main.Tk"):
            app = BarcodeGeneratorApp(config_path=sample_config)
            assert app._validate_code("1234567890123", "EAN-13") is True

    def test_validate_code_ean13_invalid_length(self, sample_config):
        """Test EAN-13 code validation with invalid length."""
        with patch("src.main.Tk"):
            app = BarcodeGeneratorApp(config_path=sample_config)
            assert app._validate_code("123456789012", "EAN-13") is False
            assert app._validate_code("12345678901234", "EAN-13") is False

    def test_validate_code_ean13_invalid_chars(self, sample_config):
        """Test EAN-13 code validation with non-numeric characters."""
        with patch("src.main.Tk"):
            app = BarcodeGeneratorApp(config_path=sample_config)
            assert app._validate_code("123456789012a", "EAN-13") is False

    def test_validate_code_ean8_valid(self, sample_config):
        """Test EAN-8 code validation with valid code."""
        with patch("src.main.Tk"):
            app = BarcodeGeneratorApp(config_path=sample_config)
            assert app._validate_code("12345670", "EAN-8") is True

    def test_validate_code_ean8_invalid(self, sample_config):
        """Test EAN-8 code validation with invalid code."""
        with patch("src.main.Tk"):
            app = BarcodeGeneratorApp(config_path=sample_config)
            assert app._validate_code("1234567", "EAN-8") is False
            assert app._validate_code("123456789", "EAN-8") is False

    def test_validate_code_code39_valid(self, sample_config):
        """Test Code39 validation with valid code."""
        with patch("src.main.Tk"):
            app = BarcodeGeneratorApp(config_path=sample_config)
            assert app._validate_code("ABC123", "Code39") is True
            assert app._validate_code("TEST-123", "Code39") is True

    def test_validate_code_code39_invalid(self, sample_config):
        """Test Code39 validation with invalid characters."""
        with patch("src.main.Tk"):
            app = BarcodeGeneratorApp(config_path=sample_config)
            # Code39 doesn't support lowercase
            assert app._validate_code("abc123", "Code39") is False

    def test_validate_code_code128_valid(self, sample_config):
        """Test Code128 validation with valid code."""
        with patch("src.main.Tk"):
            app = BarcodeGeneratorApp(config_path=sample_config)
            assert app._validate_code("ABC123", "Code128") is True
            assert app._validate_code("Test-123", "Code128") is True

    def test_validate_code_empty(self, sample_config):
        """Test validation with empty code."""
        with patch("src.main.Tk"):
            app = BarcodeGeneratorApp(config_path=sample_config)
            assert app._validate_code("", "EAN-13") is False
            assert app._validate_code("   ", "EAN-13") is False

    @patch("src.main.ImageTk.PhotoImage")
    @patch("src.main.Image.open")
    @patch("src.main.Path")
    def test_generate_barcode_success(
        self, mock_path, mock_image_open, mock_photo, sample_config
    ):
        """Test successful barcode generation."""
        # Mock image
        mock_img = MagicMock()
        mock_img.width = 200
        mock_img.height = 100
        mock_img.resize.return_value = mock_img
        mock_image_open.return_value = mock_img

        # Mock path
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        with patch("src.main.Tk"):
            app = BarcodeGeneratorApp(config_path=sample_config)
            app.code_entry = MagicMock()
            app.code_entry.get.return_value = "1234567890123"
            app.format_var = MagicMock()
            app.format_var.get.return_value = "EAN-13"
            app.preview_label = MagicMock()
            app.status_var = MagicMock()

            with patch("src.main.messagebox") as mock_msgbox:
                with patch.object(
                    app, "_validate_code", return_value=True
                ):
                    with patch("src.main.EAN13") as mock_ean13:
                        mock_barcode = MagicMock()
                        mock_barcode.save = MagicMock()
                        mock_ean13.return_value = mock_barcode

                        app.generate_barcode()

                        # Verify barcode was generated
                        mock_ean13.assert_called_once()

    @patch("src.main.messagebox")
    def test_generate_barcode_empty_code(self, mock_msgbox, sample_config):
        """Test barcode generation with empty code."""
        with patch("src.main.Tk"):
            app = BarcodeGeneratorApp(config_path=sample_config)
            app.code_entry = MagicMock()
            app.code_entry.get.return_value = ""

            app.generate_barcode()

            mock_msgbox.showwarning.assert_called_once()

    @patch("src.main.messagebox")
    def test_generate_barcode_invalid_code(self, mock_msgbox, sample_config):
        """Test barcode generation with invalid code."""
        with patch("src.main.Tk"):
            app = BarcodeGeneratorApp(config_path=sample_config)
            app.code_entry = MagicMock()
            app.code_entry.get.return_value = "invalid"
            app.format_var = MagicMock()
            app.format_var.get.return_value = "EAN-13"
            app.status_var = MagicMock()

            with patch.object(
                app, "_validate_code", return_value=False
            ):
                app.generate_barcode()

                mock_msgbox.showerror.assert_called_once()

    @patch("src.main.filedialog")
    @patch("src.main.messagebox")
    def test_save_barcode_no_barcode(
        self, mock_msgbox, mock_filedialog, sample_config
    ):
        """Test saving when no barcode is generated."""
        with patch("src.main.Tk"):
            app = BarcodeGeneratorApp(config_path=sample_config)
            app.current_barcode_image = None

            app.save_barcode()

            mock_msgbox.showwarning.assert_called_once()
            mock_filedialog.asksaveasfilename.assert_not_called()

    @patch("src.main.filedialog")
    @patch("src.main.messagebox")
    def test_save_barcode_success(
        self, mock_msgbox, mock_filedialog, sample_config
    ):
        """Test successful barcode saving."""
        mock_filedialog.asksaveasfilename.return_value = "/path/to/save.png"

        with patch("src.main.Tk"):
            app = BarcodeGeneratorApp(config_path=sample_config)
            app.current_barcode_image = MagicMock()
            app.current_barcode_image.save = MagicMock()
            app.code_entry = MagicMock()
            app.code_entry.get.return_value = "1234567890123"
            app.status_var = MagicMock()

            app.save_barcode()

            app.current_barcode_image.save.assert_called_once_with(
                "/path/to/save.png"
            )
            mock_msgbox.showinfo.assert_called_once()

    def test_clear_preview(self, sample_config):
        """Test clearing preview."""
        with patch("src.main.Tk"):
            app = BarcodeGeneratorApp(config_path=sample_config)
            app.preview_label = MagicMock()
            app.code_entry = MagicMock()
            app.status_var = MagicMock()
            app.current_barcode_image = MagicMock()

            app.clear_preview()

            app.preview_label.config.assert_called()
            app.code_entry.delete.assert_called_once_with(0, "end")
            assert app.current_barcode_image is None
