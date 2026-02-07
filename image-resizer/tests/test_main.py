"""Unit tests for Image Resizer."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PIL import Image

from src.main import ImageResizer, find_image_files, parse_size


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
    img = Image.new("RGB", (200, 300), color="red")
    img.save(img_path, "PNG")
    return img_path


def test_image_resizer_initialization():
    """Test ImageResizer initialization."""
    resizer = ImageResizer(
        resampling="BILINEAR",
        output_format="jpg",
        jpeg_quality=85,
        webp_quality=80,
        preserve_metadata=False,
    )
    assert resizer.output_format == "jpg"
    assert resizer.jpeg_quality == 85
    assert resizer.webp_quality == 80
    assert resizer.preserve_metadata is False


def test_calculate_dimensions_by_width():
    """Test calculating dimensions from width only."""
    resizer = ImageResizer()
    original_size = (200, 300)

    new_width, new_height = resizer.calculate_dimensions(original_size, width=100)

    assert new_width == 100
    assert new_height == 150  # Maintains 2:3 aspect ratio


def test_calculate_dimensions_by_height():
    """Test calculating dimensions from height only."""
    resizer = ImageResizer()
    original_size = (200, 300)

    new_width, new_height = resizer.calculate_dimensions(original_size, height=150)

    assert new_width == 100
    assert new_height == 150  # Maintains 2:3 aspect ratio


def test_calculate_dimensions_by_width_and_height():
    """Test calculating dimensions from both width and height."""
    resizer = ImageResizer()
    original_size = (200, 300)

    # Both specified - should use the smaller constraint
    new_width, new_height = resizer.calculate_dimensions(
        original_size, width=100, height=200
    )

    # Should maintain aspect ratio using the limiting dimension
    assert new_width == 100
    assert new_height == 150


def test_calculate_dimensions_by_percentage():
    """Test calculating dimensions by percentage."""
    resizer = ImageResizer()
    original_size = (200, 300)

    new_width, new_height = resizer.calculate_dimensions(original_size, percentage=50)

    assert new_width == 100
    assert new_height == 150


def test_calculate_dimensions_invalid_percentage():
    """Test calculating dimensions with invalid percentage."""
    resizer = ImageResizer()
    original_size = (200, 300)

    with pytest.raises(ValueError, match="Percentage must be greater than 0"):
        resizer.calculate_dimensions(original_size, percentage=0)


def test_calculate_dimensions_no_parameters():
    """Test calculating dimensions with no parameters."""
    resizer = ImageResizer()
    original_size = (200, 300)

    with pytest.raises(ValueError, match="Must specify width, height, or percentage"):
        resizer.calculate_dimensions(original_size)


def test_resize_image_by_width(sample_image, temp_dir):
    """Test resizing image by width."""
    resizer = ImageResizer(preserve_metadata=False)
    output_path = temp_dir / "test_resized.png"

    result = resizer.resize_image(sample_image, output_path, width=100)

    assert result is True
    assert output_path.exists()

    # Verify dimensions
    with Image.open(output_path) as img:
        assert img.size[0] == 100
        assert img.size[1] == 150  # Maintains aspect ratio


def test_resize_image_by_height(sample_image, temp_dir):
    """Test resizing image by height."""
    resizer = ImageResizer(preserve_metadata=False)
    output_path = temp_dir / "test_resized.png"

    result = resizer.resize_image(sample_image, output_path, height=150)

    assert result is True
    assert output_path.exists()

    # Verify dimensions
    with Image.open(output_path) as img:
        assert img.size[0] == 100
        assert img.size[1] == 150  # Maintains aspect ratio


def test_resize_image_by_percentage(sample_image, temp_dir):
    """Test resizing image by percentage."""
    resizer = ImageResizer(preserve_metadata=False)
    output_path = temp_dir / "test_resized.png"

    result = resizer.resize_image(sample_image, output_path, percentage=50)

    assert result is True
    assert output_path.exists()

    # Verify dimensions (50% of 200x300 = 100x150)
    with Image.open(output_path) as img:
        assert img.size[0] == 100
        assert img.size[1] == 150


def test_resize_image_with_format_conversion(sample_image, temp_dir):
    """Test resizing with format conversion."""
    resizer = ImageResizer(
        output_format="jpg", jpeg_quality=90, preserve_metadata=False
    )
    output_path = temp_dir / "test_resized.jpg"

    result = resizer.resize_image(sample_image, output_path, width=100)

    assert result is True
    assert output_path.exists()

    # Verify format
    with Image.open(output_path) as img:
        assert img.format == "JPEG"


def test_get_output_path(temp_dir):
    """Test output path generation."""
    resizer = ImageResizer()
    input_path = temp_dir / "test_image.png"

    # Without output directory
    output_path = resizer.get_output_path(input_path, suffix="_resized")
    assert output_path == temp_dir / "test_image_resized.png"

    # With output directory
    output_dir = temp_dir / "resized"
    output_path = resizer.get_output_path(input_path, output_dir, "_resized")
    assert output_path == output_dir / "test_image_resized.png"


def test_get_output_path_with_format(temp_dir):
    """Test output path generation with format conversion."""
    resizer = ImageResizer(output_format="jpg")
    input_path = temp_dir / "test_image.png"

    output_path = resizer.get_output_path(input_path, suffix="_resized")
    assert output_path == temp_dir / "test_image_resized.jpg"


def test_resize_batch(temp_dir):
    """Test batch resizing."""
    # Create multiple test images
    images = []
    for i in range(3):
        img_path = temp_dir / f"test_{i}.png"
        img = Image.new("RGB", (200, 200), color="red")
        img.save(img_path, "PNG")
        images.append(img_path)

    resizer = ImageResizer(preserve_metadata=False)
    successful, failed = resizer.resize_batch(images, width=100, suffix="_resized")

    assert successful == 3
    assert failed == 0

    # Verify all files were resized
    for img_path in images:
        resized_path = img_path.parent / f"{img_path.stem}_resized.png"
        assert resized_path.exists()

        with Image.open(resized_path) as img:
            assert img.size[0] == 100


def test_resize_batch_with_output_dir(temp_dir):
    """Test batch resizing with output directory."""
    # Create test images
    images = []
    for i in range(2):
        img_path = temp_dir / f"test_{i}.png"
        img = Image.new("RGB", (200, 200), color="red")
        img.save(img_path, "PNG")
        images.append(img_path)

    output_dir = temp_dir / "resized"
    resizer = ImageResizer(preserve_metadata=False)
    successful, failed = resizer.resize_batch(
        images, width=100, output_dir=output_dir, suffix="_resized"
    )

    assert successful == 2
    assert failed == 0
    assert output_dir.exists()

    # Verify files in output directory
    for img_path in images:
        resized_path = output_dir / f"{img_path.stem}_resized.png"
        assert resized_path.exists()


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


def test_parse_size_width_only():
    """Test parsing size string with width only."""
    width, height = parse_size("800")
    assert width == 800
    assert height is None


def test_parse_size_width_and_height():
    """Test parsing size string with width and height."""
    width, height = parse_size("800x600")
    assert width == 800
    assert height == 600


def test_parse_size_invalid_format():
    """Test parsing invalid size string."""
    with pytest.raises(ValueError, match="Invalid size format"):
        parse_size("800x600x400")


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
    """Test RGBA to RGB conversion for JPEG output."""
    # Create RGBA image
    rgba_path = temp_dir / "test_rgba.png"
    img = Image.new("RGBA", (50, 50), color=(255, 0, 0, 128))
    img.save(rgba_path, "PNG")

    resizer = ImageResizer(
        output_format="jpg", preserve_metadata=False, jpeg_quality=90
    )
    output_path = temp_dir / "test_rgba_resized.jpg"

    result = resizer.resize_image(rgba_path, output_path, width=25)

    assert result is True
    assert output_path.exists()

    # Verify output is RGB (not RGBA)
    with Image.open(output_path) as img:
        assert img.mode == "RGB"
