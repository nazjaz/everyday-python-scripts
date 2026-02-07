"""Photo GPS Organizer - Organize photos by GPS location from EXIF data.

This module provides functionality to organize photos by GPS location extracted
from EXIF data, creating folders named by location or coordinates when available.
Includes comprehensive logging and error handling.
"""

import logging
import logging.handlers
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv
from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class PhotoGPSOrganizer:
    """Organizes photos by GPS location from EXIF data."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize PhotoGPSOrganizer with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_directories()
        self.stats = {
            "photos_scanned": 0,
            "photos_organized": 0,
            "photos_without_gps": 0,
            "photos_skipped": 0,
            "errors": 0,
            "errors_list": [],
        }
        self._init_geocoding()

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Configuration dictionary.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid.
        """
        config_file = Path(config_path)

        if not config_file.is_absolute():
            if not config_file.exists():
                parent_config = Path(__file__).parent.parent / config_path
                if parent_config.exists():
                    config_file = parent_config
                else:
                    cwd_config = Path.cwd() / config_path
                    if cwd_config.exists():
                        config_file = cwd_config

        if not config_file.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}"
            )

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Override with environment variables if present
        if os.getenv("SOURCE_DIRECTORY"):
            config["source_directory"] = os.getenv("SOURCE_DIRECTORY")
        if os.getenv("DESTINATION_DIRECTORY"):
            config["destination_directory"] = os.getenv("DESTINATION_DIRECTORY")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/photo_gps_organizer.log")

        log_path = Path(log_file)
        if not log_path.is_absolute():
            project_root = Path(__file__).parent.parent
            log_path = project_root / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.handlers.clear()

        file_handler = logging.handlers.RotatingFileHandler(
            str(log_path),
            maxBytes=log_config.get("max_bytes", 10485760),
            backupCount=log_config.get("backup_count", 5),
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            log_config.get(
                "format",
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter("%(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        logger.info("Logging configured successfully")

    def _setup_directories(self) -> None:
        """Set up source and destination directories."""
        self.source_dir = Path(
            os.path.expanduser(self.config["source_directory"])
        )

        if not self.source_dir.exists():
            raise FileNotFoundError(
                f"Source directory does not exist: {self.source_dir}"
            )

        dest_dir = self.config.get("destination_directory", "organized_photos")
        self.dest_dir = Path(os.path.expanduser(dest_dir))

        if not self.dest_dir.is_absolute():
            project_root = Path(__file__).parent.parent
            self.dest_dir = project_root / dest_dir

        self.dest_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Source directory: {self.source_dir}")
        logger.info(f"Destination directory: {self.dest_dir}")

    def _init_geocoding(self) -> None:
        """Initialize reverse geocoding if enabled."""
        self.use_geocoding = self.config.get("geocoding", {}).get(
            "enabled", False
        )
        self.geocoder = None

        if self.use_geocoding:
            try:
                from geopy.geocoders import Nominatim

                self.geocoder = Nominatim(user_agent="photo-gps-organizer")
                logger.info("Reverse geocoding enabled")
            except ImportError:
                logger.warning(
                    "geopy not installed. Reverse geocoding disabled. "
                    "Install with: pip install geopy"
                )
                self.use_geocoding = False

    def _get_exif_data(self, image_path: Path) -> Optional[Dict]:
        """Extract EXIF data from image.

        Args:
            image_path: Path to image file.

        Returns:
            Dictionary of EXIF data, or None if error.
        """
        try:
            with Image.open(image_path) as img:
                exif_data = img._getexif()
                if exif_data is None:
                    return None

                exif = {}
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif[tag] = value

                return exif

        except Exception as e:
            error_msg = f"Error reading EXIF from {image_path.name}: {e}"
            logger.error(error_msg)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            return None

    def _get_gps_coordinates(self, exif_data: Dict) -> Optional[Tuple[float, float]]:
        """Extract GPS coordinates from EXIF data.

        Args:
            exif_data: Dictionary of EXIF data.

        Returns:
            Tuple of (latitude, longitude) in decimal degrees, or None.
        """
        if "GPSInfo" not in exif_data:
            return None

        gps_info = exif_data["GPSInfo"]
        gps_data = {}

        for key, value in gps_info.items():
            tag = GPSTAGS.get(key, key)
            gps_data[tag] = value

        try:
            lat = self._convert_to_degrees(gps_data.get("GPSLatitude"))
            lon = self._convert_to_degrees(gps_data.get("GPSLongitude"))

            if lat is None or lon is None:
                return None

            # Handle GPSLatitudeRef and GPSLongitudeRef
            lat_ref = gps_data.get("GPSLatitudeRef", "N")
            lon_ref = gps_data.get("GPSLongitudeRef", "E")

            if lat_ref == "S":
                lat = -lat
            if lon_ref == "W":
                lon = -lon

            return (lat, lon)

        except Exception as e:
            logger.warning(f"Error converting GPS coordinates: {e}")
            return None

    def _convert_to_degrees(self, value: Optional[Tuple]) -> Optional[float]:
        """Convert GPS coordinate tuple to decimal degrees.

        Args:
            value: Tuple of (degrees, minutes, seconds) or None.

        Returns:
            Decimal degrees, or None if invalid.
        """
        if value is None:
            return None

        try:
            degrees, minutes, seconds = value
            decimal = float(degrees) + float(minutes) / 60.0 + float(seconds) / 3600.0
            return decimal
        except (ValueError, TypeError, IndexError):
            return None

    def _get_location_name(self, latitude: float, longitude: float) -> Optional[str]:
        """Get location name from coordinates using reverse geocoding.

        Args:
            latitude: Latitude in decimal degrees.
            longitude: Longitude in decimal degrees.

        Returns:
            Location name string, or None if geocoding fails.
        """
        if not self.use_geocoding or self.geocoder is None:
            return None

        try:
            location = self.geocoder.reverse(
                (latitude, longitude), timeout=10, language="en"
            )
            if location:
                address = location.raw.get("address", {})
                # Try to get a meaningful location name
                location_name = (
                    address.get("city")
                    or address.get("town")
                    or address.get("village")
                    or address.get("county")
                    or address.get("state")
                    or address.get("country")
                )
                return location_name
        except Exception as e:
            logger.warning(f"Geocoding failed for ({latitude}, {longitude}): {e}")

        return None

    def _format_coordinates(self, latitude: float, longitude: float) -> str:
        """Format coordinates as folder name.

        Args:
            latitude: Latitude in decimal degrees.
            longitude: Longitude in decimal degrees.

        Returns:
            Formatted coordinate string.
        """
        format_type = self.config.get("folder_naming", {}).get(
            "coordinate_format", "decimal"
        )

        if format_type == "decimal":
            # Round to reasonable precision
            precision = self.config.get("folder_naming", {}).get(
                "coordinate_precision", 4
            )
            return f"Lat{latitude:.{precision}f}_Lon{longitude:.{precision}f}"
        else:
            # DMS format
            lat_deg = int(abs(latitude))
            lat_min = int((abs(latitude) - lat_deg) * 60)
            lat_sec = (abs(latitude) - lat_deg - lat_min / 60) * 3600
            lat_dir = "N" if latitude >= 0 else "S"

            lon_deg = int(abs(longitude))
            lon_min = int((abs(longitude) - lon_deg) * 60)
            lon_sec = (abs(longitude) - lon_deg - lon_min / 60) * 3600
            lon_dir = "E" if longitude >= 0 else "W"

            return (
                f"{lat_deg}d{lat_min}m{lat_sec:.2f}s{lat_dir}_"
                f"{lon_deg}d{lon_min}m{lon_sec:.2f}s{lon_dir}"
            )

    def _get_folder_name(self, latitude: float, longitude: float) -> str:
        """Get folder name for GPS coordinates.

        Args:
            latitude: Latitude in decimal degrees.
            longitude: Longitude in decimal degrees.

        Returns:
            Folder name string.
        """
        # Try to get location name first
        location_name = self._get_location_name(latitude, longitude)

        if location_name:
            # Sanitize location name for filesystem
            location_name = "".join(
                c if c.isalnum() or c in (" ", "-", "_") else "_"
                for c in location_name
            )
            location_name = location_name.strip().replace(" ", "_")

            # Add coordinates to location name if configured
            if self.config.get("folder_naming", {}).get("include_coordinates", False):
                coords = self._format_coordinates(latitude, longitude)
                return f"{location_name}_{coords}"

            return location_name

        # Fallback to coordinates
        return self._format_coordinates(latitude, longitude)

    def _should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed.

        Args:
            file_path: Path to file.

        Returns:
            True if file should be processed, False otherwise.
        """
        # Check file extensions
        image_extensions = self.config.get("image_extensions", [".jpg", ".jpeg", ".png", ".tiff", ".tif"])
        if file_path.suffix.lower() not in [ext.lower() for ext in image_extensions]:
            return False

        # Check exclusions
        exclusions = self.config.get("exclusions", {})
        file_name = file_path.name

        # Check excluded patterns
        excluded_patterns = exclusions.get("patterns", [])
        for pattern in excluded_patterns:
            if pattern in file_name:
                return False

        # Check excluded directories
        excluded_dirs = exclusions.get("directories", [])
        for excluded_dir in excluded_dirs:
            excluded_path = Path(os.path.expanduser(excluded_dir))
            try:
                if file_path.is_relative_to(excluded_path):
                    return False
            except (ValueError, AttributeError):
                # Python < 3.9 compatibility
                if str(file_path).startswith(str(excluded_path)):
                    return False

        return True

    def _organize_photo(self, photo_path: Path) -> bool:
        """Organize a single photo by GPS location.

        Args:
            photo_path: Path to photo file.

        Returns:
            True if organized successfully, False otherwise.
        """
        self.stats["photos_scanned"] += 1

        if not self._should_process_file(photo_path):
            logger.debug(f"Skipping file: {photo_path.name}")
            self.stats["photos_skipped"] += 1
            return False

        # Extract EXIF data
        exif_data = self._get_exif_data(photo_path)
        if exif_data is None:
            logger.debug(f"No EXIF data in {photo_path.name}")
            self.stats["photos_without_gps"] += 1
            return False

        # Get GPS coordinates
        coordinates = self._get_gps_coordinates(exif_data)
        if coordinates is None:
            logger.debug(f"No GPS data in {photo_path.name}")
            self.stats["photos_without_gps"] += 1
            return False

        latitude, longitude = coordinates

        # Get folder name
        folder_name = self._get_folder_name(latitude, longitude)
        target_folder = self.dest_dir / folder_name
        target_folder.mkdir(parents=True, exist_ok=True)

        # Determine target file path
        target_file = target_folder / photo_path.name

        # Handle duplicates
        duplicate_action = self.config.get("duplicate_handling", "skip")
        if target_file.exists() and duplicate_action == "skip":
            logger.debug(f"Duplicate file, skipping: {photo_path.name}")
            self.stats["photos_skipped"] += 1
            return False

        # Handle duplicate naming
        counter = 1
        original_target = target_file
        while target_file.exists() and duplicate_action == "rename":
            stem = original_target.stem
            suffix = original_target.suffix
            target_file = target_folder / f"{stem}_{counter}{suffix}"
            counter += 1

        # Move or copy file
        operation = self.config.get("operation", "move")
        try:
            if operation == "move":
                shutil.move(str(photo_path), str(target_file))
                logger.info(f"Moved {photo_path.name} to {folder_name}/")
            else:
                shutil.copy2(str(photo_path), str(target_file))
                logger.info(f"Copied {photo_path.name} to {folder_name}/")

            self.stats["photos_organized"] += 1
            return True

        except Exception as e:
            error_msg = f"Error organizing {photo_path.name}: {e}"
            logger.error(error_msg)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            return False

    def organize_photos(self) -> Dict[str, any]:
        """Organize all photos in source directory.

        Returns:
            Dictionary with statistics about the operation.
        """
        logger.info("Starting photo organization by GPS location")
        logger.info(f"Operation mode: {self.config.get('operation', 'move')}")
        logger.info(f"Recursive: {self.config['operations']['recursive']}")

        # Find all image files
        photos_to_process = []
        if self.config["operations"]["recursive"]:
            for file_path in self.source_dir.rglob("*"):
                if file_path.is_file():
                    photos_to_process.append(file_path)
        else:
            for file_path in self.source_dir.iterdir():
                if file_path.is_file():
                    photos_to_process.append(file_path)

        logger.info(f"Found {len(photos_to_process)} files to process")

        # Process each photo
        for photo_path in photos_to_process:
            self._organize_photo(photo_path)

        logger.info("Photo organization completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats


def main() -> int:
    """Main entry point for photo GPS organizer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Organize photos by GPS location from EXIF data"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    try:
        organizer = PhotoGPSOrganizer(config_path=args.config)

        if args.dry_run:
            organizer.config["operation"] = "copy"
            logger.info("DRY RUN MODE: Files will be copied instead of moved")

        # Organize photos
        stats = organizer.organize_photos()

        # Print summary
        print("\n" + "=" * 60)
        print("Photo GPS Organization Summary")
        print("=" * 60)
        print(f"Photos Scanned: {stats['photos_scanned']}")
        print(f"Photos Organized: {stats['photos_organized']}")
        print(f"Photos Without GPS: {stats['photos_without_gps']}")
        print(f"Photos Skipped: {stats['photos_skipped']}")
        print(f"Destination: {organizer.dest_dir}")
        print(f"Errors: {stats['errors']}")

        if stats["errors_list"]:
            print("\nErrors:")
            for error in stats["errors_list"][:10]:
                print(f"  - {error}")
            if len(stats["errors_list"]) > 10:
                print(f"  ... and {len(stats['errors_list']) - 10} more")

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
