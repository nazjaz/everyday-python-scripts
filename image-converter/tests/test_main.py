"""Unit tests for Image Converter."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PIL import Image

from src.main import ImageConverter, find_image_files


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_image(temp_dir):
    """Create a sample test image."""
    img_path = temp_dir / "test_image.png"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(img_path, "PNG")
    return img_path


def test_image_converter_initialization():
    """Test ImageConverter initialization."""
    converter = ImageConverter(
        preserve_metadata=True, quality_jpeg=90, quality_webp=85
    )
    assert converter.preserve_metadata is True
    assert converter.quality_jpeg == 90
    assert converter.quality_webp == 85


def test_convert_image_png_to_jpg(sample_image, temp_dir):
    """Test converting PNG to JPG."""
    converter = ImageConverter(preserve_metadata=False, quality_jpeg=95)
    output_path = temp_dir / "test_image.jpg"

    result = converter.convert_image(sample_image, output_path, "jpg")

    assert result is True
    assert output_path.exists()

    # Verify output is valid JPEG
    with Image.open(output_path) as img:
        assert img.format == "JPEG"


def test_convert_image_jpg_to_png(sample_image, temp_dir):
    """Test converting JPG to PNG."""
    # First create a JPG
    jpg_path = temp_dir / "test.jpg"
    img = Image.new("RGB", (50, 50), color="blue")
    img.save(jpg_path, "JPEG")

    converter = ImageConverter(preserve_metadata=False)
    output_path = temp_dir / "test.png"

    result = converter.convert_image(jpg_path, output_path, "png")

    assert result is True
    assert output_path.exists()

    # Verify output is valid PNG
    with Image.open(output_path) as img:
        assert img.format == "PNG"


def test_convert_image_png_to_webp(sample_image, temp_dir):
    """Test converting PNG to WEBP."""
    converter = ImageConverter(preserve_metadata=False, quality_webp=90)
    output_path = temp_dir / "test_image.webp"

    result = converter.convert_image(sample_image, output_path, "webp")

    assert result is True
    assert output_path.exists()

    # Verify output is valid WEBP
    with Image.open(output_path) as img:
        assert img.format == "WEBP"


def test_convert_image_unsupported_format(sample_image, temp_dir):
    """Test converting to unsupported format."""
    converter = ImageConverter()
    output_path = temp_dir / "test_image.xyz"

    with pytest.raises(ValueError, match="Unsupported output format"):
        converter.convert_image(sample_image, output_path, "xyz")


def test_get_output_path(temp_dir):
    """Test output path generation."""
    converter = ImageConverter()
    input_path = temp_dir / "test_image.png"

    # Without output directory
    output_path = converter.get_output_path(input_path, "jpg")
    assert output_path == temp_dir / "test_image.jpg"

    # With output directory
    output_dir = temp_dir / "converted"
    output_path = converter.get_output_path(input_path, "jpg", output_dir)
    assert output_path == output_dir / "test_image.jpg"


def test_convert_batch(temp_dir):
    """Test batch conversion."""
    # Create multiple test images
    images = []
    for i in range(3):
        img_path = temp_dir / f"test_{i}.png"
        img = Image.new("RGB", (50, 50), color="red")
        img.save(img_path, "PNG")
        images.append(img_path)

    converter = ImageConverter(preserve_metadata=False)
    successful, failed = converter.convert_batch(images, "jpg", None)

    assert successful == 3
    assert failed == 0

    # Verify all files were converted
    for img_path in images:
        jpg_path = img_path.parent / f"{img_path.stem}.jpg"
        assert jpg_path.exists()


def test_convert_batch_with_output_dir(temp_dir):
    """Test batch conversion with output directory."""
    # Create test images
    images = []
    for i in range(2):
        img_path = temp_dir / f"test_{i}.png"
        img = Image.new("RGB", (50, 50), color="red")
        img.save(img_path, "PNG")
        images.append(img_path)

    output_dir = temp_dir / "converted"
    converter = ImageConverter(preserve_metadata=False)
    successful, failed = converter.convert_batch(images, "jpg", output_dir)

    assert successful == 2
    assert failed == 0
    assert output_dir.exists()

    # Verify files in output directory
    for img_path in images:
        jpg_path = output_dir / f"{img_path.stem}.jpg"
        assert jpg_path.exists()


def test_find_image_files(temp_dir):
    """Test finding image files in directory."""
    # Create various image files
    Image.new("RGB", (10, 10)).save(temp_dir / "test1.jpg", "JPEG")
    Image.new("RGB", (10, 10)).save(temp_dir / "test2.png", "PNG")
    Image.new("RGB", (10, 10)).save(temp_dir / "test3.webp", "WEBP")
    (temp_dir / "not_image.txt").write_text("not an image")

    # Find JPG and PNG files
    files = find_image_files(temp_dir, ["jpg", "png"], recursive=False)

    assert len(files) == 2
    assert all(f.suffix.lower() in [".jpg", ".png"] for f in files)


def test_find_image_files_recursive(temp_dir):
    """Test finding image files recursively."""
    subdir = temp_dir / "subdir"
    subdir.mkdir()

    Image.new("RGB", (10, 10)).save(temp_dir / "test1.jpg", "JPEG")
    Image.new("RGB", (10, 10)).save(subdir / "test2.png", "PNG")

    # Non-recursive
    files = find_image_files(temp_dir, ["jpg", "png"], recursive=False)
    assert len(files) == 1

    # Recursive
    files = find_image_files(temp_dir, ["jpg", "png"], recursive=True)
    assert len(files) == 2


def test_quality_validation():
    """Test quality value validation."""
    from src.main import validate_quality

    # JPEG quality should be clamped to 1-100
    assert validate_quality(50, "jpeg") == 50
    assert validate_quality(0, "jpeg") == 1
    assert validate_quality(150, "jpeg") == 100

    # WEBP quality should be clamped to 0-100
    assert validate_quality(50, "webp") == 50
    assert validate_quality(-10, "webp") == 0
    assert validate_quality(150, "webp") == 100


def test_rgba_to_rgb_conversion(temp_dir):
    """Test RGBA to RGB conversion for JPEG."""
    # Create RGBA image
    rgba_path = temp_dir / "test_rgba.png"
    img = Image.new("RGBA", (50, 50), color=(255, 0, 0, 128))
    img.save(rgba_path, "PNG")

    converter = ImageConverter(preserve_metadata=False)
    output_path = temp_dir / "test_rgba.jpg"

    result = converter.convert_image(rgba_path, output_path, "jpg")

    assert result is True
    assert output_path.exists()

    # Verify output is RGB (not RGBA)
    with Image.open(output_path) as img:
        assert img.mode == "RGB"
