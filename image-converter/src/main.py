"""Image Converter - CLI tool for converting images between formats.

This module provides a command-line tool for converting images between
different formats (JPG, PNG, WEBP, etc.) with options to preserve metadata
and adjust quality settings. Supports batch processing and comprehensive
logging.
"""

import argparse
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv
from PIL import Image, ExifTags

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ImageConverter:
    """Handles image format conversion with metadata preservation."""

    # Format mappings for PIL
    FORMAT_MAP = {
        "jpg": "JPEG",
        "jpeg": "JPEG",
        "png": "PNG",
        "webp": "WEBP",
        "bmp": "BMP",
        "tiff": "TIFF",
        "tif": "TIFF",
    }

    # Lossy formats that support quality settings
    LOSSY_FORMATS = {"jpg", "jpeg", "webp"}

    def __init__(
        self,
        preserve_metadata: bool = True,
        quality_jpeg: int = 95,
        quality_webp: int = 90,
    ) -> None:
        """Initialize ImageConverter.

        Args:
            preserve_metadata: Whether to preserve EXIF metadata.
            quality_jpeg: JPEG quality (1-100).
            quality_webp: WEBP quality (0-100).
        """
        self.preserve_metadata = preserve_metadata
        self.quality_jpeg = quality_jpeg
        self.quality_webp = quality_webp

    def convert_image(
        self, input_path: Path, output_path: Path, output_format: str
    ) -> bool:
        """Convert a single image to the specified format.

        Args:
            input_path: Path to input image file.
            output_path: Path where converted image will be saved.
            output_format: Target format (jpg, png, webp, etc.).

        Returns:
            True if conversion successful, False otherwise.

        Raises:
            ValueError: If output format is not supported.
            IOError: If file cannot be read or written.
        """
        if output_format.lower() not in self.FORMAT_MAP:
            raise ValueError(f"Unsupported output format: {output_format}")

        try:
            with Image.open(input_path) as img:
                # Get EXIF data if available and metadata preservation is enabled
                exif_data = None
                if self.preserve_metadata:
                    try:
                        # Try to get EXIF data using getexif() (Pillow 6.0+)
                        if hasattr(img, "getexif"):
                            exif = img.getexif()
                            if exif:
                                exif_data = exif.tobytes()
                        # Fallback to old _getexif() method for older Pillow
                        elif hasattr(img, "_getexif") and img._getexif() is not None:
                            exif_data = img.info.get("exif")
                    except (AttributeError, TypeError, KeyError):
                        # Some images may not have EXIF data
                        pass

                # Convert RGBA to RGB for JPEG
                if output_format.lower() in ("jpg", "jpeg") and img.mode == "RGBA":
                    # Create white background for transparent images
                    rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)
                    img = rgb_img
                elif output_format.lower() in ("jpg", "jpeg") and img.mode not in (
                    "RGB",
                    "L",
                ):
                    img = img.convert("RGB")

                # Prepare save parameters
                save_kwargs = {"format": self.FORMAT_MAP[output_format.lower()]}

                # Add quality for lossy formats
                if output_format.lower() in ("jpg", "jpeg"):
                    save_kwargs["quality"] = self.quality_jpeg
                    save_kwargs["optimize"] = True
                elif output_format.lower() == "webp":
                    save_kwargs["quality"] = self.quality_webp
                    save_kwargs["method"] = 6  # Best quality, slower

                # Preserve metadata if available
                if exif_data and self.preserve_metadata:
                    # PIL handles EXIF preservation automatically for supported formats
                    # For formats that don't support EXIF, we skip it
                    if output_format.lower() in ("jpg", "jpeg", "tiff"):
                        try:
                            # Try to get existing exif from info first
                            if "exif" in img.info:
                                save_kwargs["exif"] = img.info["exif"]
                            elif exif_data:
                                save_kwargs["exif"] = exif_data
                        except (AttributeError, KeyError, TypeError):
                            pass

                # Ensure output directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Save converted image
                img.save(output_path, **save_kwargs)

            logger.info(
                f"Converted {input_path.name} to {output_format.upper()}: "
                f"{output_path}"
            )
            return True

        except IOError as e:
            logger.error(f"Error converting {input_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error converting {input_path}: {e}")
            return False

    def get_output_path(
        self, input_path: Path, output_format: str, output_dir: Optional[Path] = None
    ) -> Path:
        """Generate output path for converted image.

        Args:
            input_path: Path to input image file.
            output_format: Target format extension.
            output_dir: Optional output directory. If None, uses input directory.

        Returns:
            Path for output file.
        """
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            return output_dir / f"{input_path.stem}.{output_format.lower()}"
        else:
            return input_path.parent / f"{input_path.stem}.{output_format.lower()}"

    def convert_batch(
        self,
        input_paths: List[Path],
        output_format: str,
        output_dir: Optional[Path] = None,
    ) -> Tuple[int, int]:
        """Convert multiple images.

        Args:
            input_paths: List of input image file paths.
            output_format: Target format.
            output_dir: Optional output directory.

        Returns:
            Tuple of (successful_count, failed_count).
        """
        successful = 0
        failed = 0

        for input_path in input_paths:
            output_path = self.get_output_path(input_path, output_format, output_dir)

            # Skip if output file already exists
            if output_path.exists():
                logger.warning(f"Output file exists, skipping: {output_path}")
                continue

            if self.convert_image(input_path, output_path, output_format):
                successful += 1
            else:
                failed += 1

        return successful, failed


def find_image_files(
    directory: Path, extensions: List[str], recursive: bool = False
) -> List[Path]:
    """Find all image files in a directory.

    Args:
        directory: Directory to search.
        extensions: List of file extensions to search for (e.g., ['jpg', 'png']).
        recursive: Whether to search recursively.

    Returns:
        List of image file paths.
    """
    image_files = []
    extensions_lower = [ext.lower().lstrip(".") for ext in extensions]

    if recursive:
        pattern = "**/*"
    else:
        pattern = "*"

    for file_path in directory.glob(pattern):
        if file_path.is_file():
            if file_path.suffix.lower().lstrip(".") in extensions_lower:
                image_files.append(file_path)

    return sorted(image_files)


def setup_logging(config: Dict) -> None:
    """Configure logging based on config file.

    Args:
        config: Configuration dictionary with logging settings.
    """
    log_config = config.get("logging", {})
    log_level = os.getenv("LOG_LEVEL", log_config.get("level", "INFO"))
    log_file = log_config.get("file", "logs/image_converter.log")
    max_bytes = log_config.get("max_bytes", 10485760)
    backup_count = log_config.get("backup_count", 5)
    log_format = log_config.get(
        "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    handler.setFormatter(logging.Formatter(log_format))

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.addHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)


def load_config(config_path: Optional[Path] = None) -> Dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. Defaults to config.yaml in project root.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file does not exist.
        yaml.YAMLError: If config file is invalid.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Override with environment variables if present
    output_dir_env = os.getenv("OUTPUT_DIR")
    if output_dir_env:
        config["output_dir"] = output_dir_env

    return config


def validate_quality(quality: int, format_name: str) -> int:
    """Validate and clamp quality value for a format.

    Args:
        quality: Quality value to validate.
        format_name: Format name (jpeg or webp).

    Returns:
        Clamped quality value.
    """
    if format_name.lower() == "jpeg":
        return max(1, min(100, quality))
    elif format_name.lower() == "webp":
        return max(0, min(100, quality))
    return quality


def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Convert images between formats (JPG, PNG, WEBP, etc.)"
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Input file or directory containing images",
    )
    parser.add_argument(
        "output_format",
        choices=["jpg", "jpeg", "png", "webp", "bmp", "tiff"],
        help="Target output format",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output directory (default: same as input)",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Process directories recursively",
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Do not preserve EXIF metadata",
    )
    parser.add_argument(
        "--quality-jpeg",
        type=int,
        help="JPEG quality (1-100, default: 95)",
    )
    parser.add_argument(
        "--quality-webp",
        type=int,
        help="WEBP quality (0-100, default: 90)",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to configuration file",
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config)
        setup_logging(config)

        # Determine input paths
        input_path = args.input.resolve()

        if input_path.is_file():
            input_files = [input_path]
        elif input_path.is_dir():
            input_formats = config.get("input_formats", ["jpg", "jpeg", "png", "webp"])
            input_files = find_image_files(input_path, input_formats, args.recursive)

            if not input_files:
                logger.error(f"No image files found in {input_path}")
                print(f"Error: No image files found in {input_path}")
                sys.exit(1)
        else:
            logger.error(f"Input path does not exist: {input_path}")
            print(f"Error: Input path does not exist: {input_path}")
            sys.exit(1)

        # Determine output directory
        output_dir = args.output
        if output_dir is None:
            output_dir_str = config.get("output_dir")
            if output_dir_str:
                output_dir = Path(output_dir_str)
            else:
                output_dir = None

        if output_dir:
            output_dir = output_dir.resolve()

        # Configure converter
        preserve_metadata = not args.no_metadata
        if preserve_metadata is None:
            preserve_metadata = config.get("preserve_metadata", True)

        quality_jpeg = args.quality_jpeg
        if quality_jpeg is None:
            quality_jpeg = config.get("quality", {}).get("jpeg", 95)
        quality_jpeg = validate_quality(quality_jpeg, "jpeg")

        quality_webp = args.quality_webp
        if quality_webp is None:
            quality_webp = config.get("quality", {}).get("webp", 90)
        quality_webp = validate_quality(quality_webp, "webp")

        # Create converter and process files
        converter = ImageConverter(
            preserve_metadata=preserve_metadata,
            quality_jpeg=quality_jpeg,
            quality_webp=quality_webp,
        )

        print(f"Converting {len(input_files)} image(s) to {args.output_format.upper()}...")
        if output_dir:
            print(f"Output directory: {output_dir}")

        successful, failed = converter.convert_batch(
            input_files, args.output_format, output_dir
        )

        print(f"\nConversion complete:")
        print(f"  Successful: {successful}")
        if failed > 0:
            print(f"  Failed: {failed}")
            sys.exit(1)

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Invalid configuration file: {e}")
        print(f"Error: Invalid configuration file: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Conversion interrupted by user")
        print("\nConversion interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
