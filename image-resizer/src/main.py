"""Image Resizer - CLI tool for resizing images with aspect ratio preservation.

This module provides a command-line tool for resizing images to specified
dimensions or percentages while maintaining aspect ratios. Supports batch
processing, multiple resampling algorithms, and web optimization features.
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
from PIL import Image

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ImageResizer:
    """Handles image resizing with aspect ratio preservation."""

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

    # Resampling algorithms
    RESAMPLING_MAP = {
        "LANCZOS": Image.Resampling.LANCZOS,
        "BILINEAR": Image.Resampling.BILINEAR,
        "BICUBIC": Image.Resampling.BICUBIC,
        "NEAREST": Image.Resampling.NEAREST,
    }

    # Lossy formats that support quality settings
    LOSSY_FORMATS = {"jpg", "jpeg", "webp"}

    def __init__(
        self,
        resampling: str = "LANCZOS",
        output_format: Optional[str] = None,
        jpeg_quality: int = 90,
        webp_quality: int = 90,
        preserve_metadata: bool = True,
    ) -> None:
        """Initialize ImageResizer.

        Args:
            resampling: Resampling algorithm (LANCZOS, BILINEAR, BICUBIC, NEAREST).
            output_format: Output format (None = same as input).
            jpeg_quality: JPEG quality (1-100).
            webp_quality: WEBP quality (0-100).
            preserve_metadata: Whether to preserve EXIF metadata.
        """
        self.resampling = self.RESAMPLING_MAP.get(resampling.upper(), Image.Resampling.LANCZOS)
        self.output_format = output_format
        self.jpeg_quality = jpeg_quality
        self.webp_quality = webp_quality
        self.preserve_metadata = preserve_metadata

    def calculate_dimensions(
        self, original_size: Tuple[int, int], width: Optional[int] = None,
        height: Optional[int] = None, percentage: Optional[float] = None
    ) -> Tuple[int, int]:
        """Calculate new dimensions while maintaining aspect ratio.

        Args:
            original_size: Original image size as (width, height).
            width: Target width (None to calculate from height).
            height: Target height (None to calculate from width).
            percentage: Resize percentage (0.0-1.0 or >1.0).

        Returns:
            New dimensions as (width, height).

        Raises:
            ValueError: If invalid parameters provided.
        """
        orig_width, orig_height = original_size

        if percentage is not None:
            if percentage <= 0:
                raise ValueError("Percentage must be greater than 0")
            new_width = int(orig_width * percentage / 100.0)
            new_height = int(orig_height * percentage / 100.0)
            return new_width, new_height

        if width is not None and height is not None:
            # Both specified - maintain aspect ratio using the smaller constraint
            aspect_ratio = orig_width / orig_height
            if width / height > aspect_ratio:
                # Height is the limiting factor
                new_width = int(height * aspect_ratio)
                new_height = height
            else:
                # Width is the limiting factor
                new_width = width
                new_height = int(width / aspect_ratio)
            return new_width, new_height

        if width is not None:
            # Calculate height from width
            aspect_ratio = orig_height / orig_width
            new_height = int(width * aspect_ratio)
            return width, new_height

        if height is not None:
            # Calculate width from height
            aspect_ratio = orig_width / orig_height
            new_width = int(height * aspect_ratio)
            return new_width, height

        raise ValueError("Must specify width, height, or percentage")

    def resize_image(
        self, input_path: Path, output_path: Path, width: Optional[int] = None,
        height: Optional[int] = None, percentage: Optional[float] = None
    ) -> bool:
        """Resize a single image.

        Args:
            input_path: Path to input image file.
            output_path: Path where resized image will be saved.
            width: Target width in pixels.
            height: Target height in pixels.
            percentage: Resize percentage (e.g., 50 for 50%).

        Returns:
            True if resizing successful, False otherwise.

        Raises:
            ValueError: If invalid resize parameters provided.
            IOError: If file cannot be read or written.
        """
        try:
            with Image.open(input_path) as img:
                original_size = img.size
                logger.info(f"Original size: {original_size[0]}x{original_size[1]}")

                # Calculate new dimensions
                new_size = self.calculate_dimensions(
                    original_size, width=width, height=height, percentage=percentage
                )
                logger.info(f"New size: {new_size[0]}x{new_size[1]}")

                # Resize image
                resized_img = img.resize(new_size, self.resampling)

                # Determine output format
                if self.output_format:
                    output_format = self.FORMAT_MAP.get(
                        self.output_format.lower(), "JPEG"
                    )
                else:
                    # Use same format as input
                    output_format = img.format or "JPEG"

                # Convert RGBA to RGB for JPEG
                if output_format == "JPEG" and resized_img.mode == "RGBA":
                    rgb_img = Image.new("RGB", resized_img.size, (255, 255, 255))
                    rgb_img.paste(resized_img, mask=resized_img.split()[3])
                    resized_img = rgb_img
                elif output_format == "JPEG" and resized_img.mode not in ("RGB", "L"):
                    resized_img = resized_img.convert("RGB")

                # Prepare save parameters
                save_kwargs = {"format": output_format}

                # Add quality for lossy formats
                if output_format == "JPEG":
                    save_kwargs["quality"] = self.jpeg_quality
                    save_kwargs["optimize"] = True
                elif output_format == "WEBP":
                    save_kwargs["quality"] = self.webp_quality
                    save_kwargs["method"] = 6

                # Preserve metadata if available
                if self.preserve_metadata:
                    try:
                        if "exif" in img.info:
                            save_kwargs["exif"] = img.info["exif"]
                    except (AttributeError, KeyError, TypeError):
                        pass

                # Ensure output directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Save resized image
                resized_img.save(output_path, **save_kwargs)

            logger.info(
                f"Resized {input_path.name} from {original_size[0]}x{original_size[1]} "
                f"to {new_size[0]}x{new_size[1]}: {output_path}"
            )
            return True

        except IOError as e:
            logger.error(f"Error resizing {input_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error resizing {input_path}: {e}")
            return False

    def get_output_path(
        self, input_path: Path, output_dir: Optional[Path] = None,
        suffix: str = "_resized"
    ) -> Path:
        """Generate output path for resized image.

        Args:
            input_path: Path to input image file.
            output_dir: Optional output directory. If None, uses input directory.
            suffix: Suffix to add to filename before extension.

        Returns:
            Path for output file.
        """
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            if self.output_format:
                ext = self.output_format.lower()
            else:
                ext = input_path.suffix.lower().lstrip(".")
            return output_dir / f"{input_path.stem}{suffix}.{ext}"
        else:
            if self.output_format:
                ext = self.output_format.lower()
            else:
                ext = input_path.suffix.lower().lstrip(".")
            return input_path.parent / f"{input_path.stem}{suffix}.{ext}"

    def resize_batch(
        self,
        input_paths: List[Path],
        width: Optional[int] = None,
        height: Optional[int] = None,
        percentage: Optional[float] = None,
        output_dir: Optional[Path] = None,
        suffix: str = "_resized",
    ) -> Tuple[int, int]:
        """Resize multiple images.

        Args:
            input_paths: List of input image file paths.
            width: Target width in pixels.
            height: Target height in pixels.
            percentage: Resize percentage.
            output_dir: Optional output directory.
            suffix: Suffix to add to output filenames.

        Returns:
            Tuple of (successful_count, failed_count).
        """
        successful = 0
        failed = 0

        for input_path in input_paths:
            output_path = self.get_output_path(input_path, output_dir, suffix)

            # Skip if output file already exists
            if output_path.exists():
                logger.warning(f"Output file exists, skipping: {output_path}")
                continue

            if self.resize_image(input_path, output_path, width, height, percentage):
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
    log_file = log_config.get("file", "logs/image_resizer.log")
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


def parse_size(size_str: str) -> Tuple[Optional[int], Optional[int]]:
    """Parse size string (e.g., "800x600" or "800").

    Args:
        size_str: Size string to parse.

    Returns:
        Tuple of (width, height). Either can be None.

    Raises:
        ValueError: If size string is invalid.
    """
    if "x" in size_str.lower():
        parts = size_str.lower().split("x")
        if len(parts) != 2:
            raise ValueError(f"Invalid size format: {size_str}")
        width = int(parts[0]) if parts[0] else None
        height = int(parts[1]) if parts[1] else None
        return width, height
    else:
        return int(size_str), None


def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Resize images to specified dimensions or percentages "
        "while maintaining aspect ratios"
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Input file or directory containing images",
    )
    parser.add_argument(
        "-w",
        "--width",
        type=int,
        help="Target width in pixels",
    )
    parser.add_argument(
        "-H",
        "--height",
        type=int,
        help="Target height in pixels",
    )
    parser.add_argument(
        "-s",
        "--size",
        type=str,
        help="Target size as WIDTHxHEIGHT or WIDTH (e.g., 800x600 or 800)",
    )
    parser.add_argument(
        "-p",
        "--percentage",
        type=float,
        help="Resize percentage (e.g., 50 for 50% of original size)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output directory (default: same as input)",
    )
    parser.add_argument(
        "--suffix",
        type=str,
        default="_resized",
        help="Suffix for output filenames (default: _resized)",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Process directories recursively",
    )
    parser.add_argument(
        "--resampling",
        choices=["LANCZOS", "BILINEAR", "BICUBIC", "NEAREST"],
        help="Resampling algorithm (default: LANCZOS)",
    )
    parser.add_argument(
        "--format",
        choices=["jpg", "jpeg", "png", "webp", "bmp", "tiff"],
        help="Output format (default: same as input)",
    )
    parser.add_argument(
        "--quality-jpeg",
        type=int,
        help="JPEG quality (1-100, default: 90)",
    )
    parser.add_argument(
        "--quality-webp",
        type=int,
        help="WEBP quality (0-100, default: 90)",
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Do not preserve EXIF metadata",
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

        # Validate resize parameters
        width = args.width
        height = args.height
        percentage = args.percentage

        if args.size:
            width, height = parse_size(args.size)

        if not any([width, height, percentage]):
            logger.error("Must specify width, height, size, or percentage")
            print("Error: Must specify width (-w), height (-H), size (-s), or percentage (-p)")
            sys.exit(1)

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

        # Configure resizer
        resampling = args.resampling or config.get("resampling", "LANCZOS")
        output_format = args.format or config.get("output_format")
        preserve_metadata = not args.no_metadata
        if preserve_metadata is None:
            preserve_metadata = config.get("preserve_metadata", True)

        quality_jpeg = args.quality_jpeg
        if quality_jpeg is None:
            quality_jpeg = config.get("jpeg_quality", 90)
        quality_jpeg = validate_quality(quality_jpeg, "jpeg")

        quality_webp = args.quality_webp
        if quality_webp is None:
            quality_webp = config.get("webp_quality", 90)
        quality_webp = validate_quality(quality_webp, "webp")

        # Create resizer and process files
        resizer = ImageResizer(
            resampling=resampling,
            output_format=output_format,
            jpeg_quality=quality_jpeg,
            webp_quality=quality_webp,
            preserve_metadata=preserve_metadata,
        )

        size_desc = ""
        if percentage:
            size_desc = f"{percentage}% of original"
        elif width and height:
            size_desc = f"{width}x{height}px"
        elif width:
            size_desc = f"{width}px width"
        elif height:
            size_desc = f"{height}px height"

        print(f"Resizing {len(input_files)} image(s) to {size_desc}...")
        if output_dir:
            print(f"Output directory: {output_dir}")

        successful, failed = resizer.resize_batch(
            input_files, width=width, height=height, percentage=percentage,
            output_dir=output_dir, suffix=args.suffix
        )

        print(f"\nResizing complete:")
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
    except ValueError as e:
        logger.error(f"Invalid parameter: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Resizing interrupted by user")
        print("\nResizing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
