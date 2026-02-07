"""Unit tests for QR code generator module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.main import QRCodeGenerator


class TestQRCodeGenerator:
    """Test cases for QRCodeGenerator class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def config_file(self, temp_dir):
        """Create temporary config file."""
        config = {
            "window": {"width": 600, "height": 700},
            "qr_code": {
                "box_size": 10,
                "border": 4,
                "error_correction": "M",
                "fill_color": "black",
                "back_color": "white",
            },
            "save": {"default_directory": "."},
            "logging": {"level": "INFO", "file": "logs/app.log"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return str(config_path)

    @pytest.fixture
    def generator(self, config_file):
        """Create QRCodeGenerator instance with mocked GUI."""
        with patch("src.main.Tk"):
            gen = QRCodeGenerator(config_path=config_file)
            return gen

    def test_load_config_success(self, temp_dir):
        """Test successful configuration loading."""
        config = {
            "window": {"width": 800},
            "qr_code": {"box_size": 15},
            "logging": {"level": "INFO"},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        with patch("src.main.Tk"):
            gen = QRCodeGenerator(config_path=str(config_path))
            assert gen.config["window"]["width"] == 800

    def test_load_config_file_not_found(self):
        """Test FileNotFoundError when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            with patch("src.main.Tk"):
                QRCodeGenerator(config_path="nonexistent.yaml")

    def test_format_vcard(self, generator):
        """Test vCard formatting."""
        generator.name_entry = MagicMock()
        generator.name_entry.get.return_value = "John Doe"
        generator.phone_entry = MagicMock()
        generator.phone_entry.get.return_value = "123-456-7890"
        generator.email_entry = MagicMock()
        generator.email_entry.get.return_value = "john@example.com"
        generator.org_entry = MagicMock()
        generator.org_entry.get.return_value = "Company"

        vcard = generator._format_vcard()

        assert "BEGIN:VCARD" in vcard
        assert "END:VCARD" in vcard
        assert "FN:John Doe" in vcard
        assert "TEL:123-456-7890" in vcard
        assert "EMAIL:john@example.com" in vcard
        assert "ORG:Company" in vcard

    def test_format_vcard_empty(self, generator):
        """Test vCard formatting with empty fields."""
        generator.name_entry = MagicMock()
        generator.name_entry.get.return_value = ""
        generator.phone_entry = MagicMock()
        generator.phone_entry.get.return_value = ""
        generator.email_entry = MagicMock()
        generator.email_entry.get.return_value = ""
        generator.org_entry = MagicMock()
        generator.org_entry.get.return_value = ""

        vcard = generator._format_vcard()

        assert "BEGIN:VCARD" in vcard
        assert "END:VCARD" in vcard

    def test_generate_qr_code_text(self, generator):
        """Test QR code generation from text."""
        generator.qr_type = MagicMock()
        generator.qr_type.get.return_value = "text"
        generator.text_entry = MagicMock()
        generator.text_entry.get.return_value = "Test text"
        generator.qr_canvas = MagicMock()
        generator.status_label = MagicMock()

        with patch("src.main.qrcode.QRCode") as mock_qr:
            mock_qr_instance = MagicMock()
            mock_qr.return_value = mock_qr_instance
            mock_qr_instance.make_image.return_value = MagicMock()

            generator._generate_qr_code()

            mock_qr_instance.add_data.assert_called_once()
            mock_qr_instance.make.assert_called_once()

    def test_generate_qr_code_url(self, generator):
        """Test QR code generation from URL."""
        generator.qr_type = MagicMock()
        generator.qr_type.get.return_value = "url"
        generator.text_entry = MagicMock()
        generator.text_entry.get.return_value = "https://example.com"
        generator.qr_canvas = MagicMock()
        generator.status_label = MagicMock()

        with patch("src.main.qrcode.QRCode") as mock_qr:
            mock_qr_instance = MagicMock()
            mock_qr.return_value = mock_qr_instance
            mock_qr_instance.make_image.return_value = MagicMock()

            generator._generate_qr_code()

            mock_qr_instance.add_data.assert_called_once()

    def test_generate_qr_code_contact(self, generator):
        """Test QR code generation from contact."""
        generator.qr_type = MagicMock()
        generator.qr_type.get.return_value = "contact"
        generator.name_entry = MagicMock()
        generator.name_entry.get.return_value = "John Doe"
        generator.phone_entry = MagicMock()
        generator.phone_entry.get.return_value = ""
        generator.email_entry = MagicMock()
        generator.email_entry.get.return_value = ""
        generator.qr_canvas = MagicMock()
        generator.status_label = MagicMock()

        with patch("src.main.qrcode.QRCode") as mock_qr:
            mock_qr_instance = MagicMock()
            mock_qr.return_value = mock_qr_instance
            mock_qr_instance.make_image.return_value = MagicMock()

            generator._generate_qr_code()

            mock_qr_instance.add_data.assert_called_once()

    def test_generate_qr_code_empty_text(self, generator):
        """Test QR code generation with empty text."""
        generator.qr_type = MagicMock()
        generator.qr_type.get.return_value = "text"
        generator.text_entry = MagicMock()
        generator.text_entry.get.return_value = ""

        with patch("src.main.messagebox") as mock_msg:
            generator._generate_qr_code()
            mock_msg.showwarning.assert_called_once()

    def test_save_qr_code_no_image(self, generator):
        """Test saving QR code when no image exists."""
        generator.current_qr_image = None

        with patch("src.main.messagebox") as mock_msg:
            generator._save_qr_code()
            mock_msg.showwarning.assert_called_once()

    def test_save_qr_code_with_image(self, generator, temp_dir):
        """Test saving QR code with image."""
        from PIL import Image

        generator.current_qr_image = Image.new("RGB", (100, 100), color="white")
        generator.status_label = MagicMock()

        with patch("src.main.filedialog") as mock_dialog:
            mock_dialog.asksaveasfilename.return_value = str(
                temp_dir / "test_qr.png"
            )

            generator._save_qr_code()

            assert (temp_dir / "test_qr.png").exists()
