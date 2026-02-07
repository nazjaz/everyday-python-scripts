"""Photo Renamer - Rename photos using EXIF date taken metadata.

This module provides functionality to automatically rename photo files based on
their EXIF date taken metadata, formatting filenames as YYYY-MM-DD_HH-MM-SS_original-name
with sequential numbering for photos with the same timestamp.
"""

import logging
import logging.handlers
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv
from PIL import Image
from PIL.ExifTags import TAGS

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class PhotoRenamer:
    """Renames photos based on EXIF date taken metadata."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize PhotoRenamer with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_directories()
        self.timestamp_counter: Dict[str, int] = {}
        self.stats = {
            "processed": 0,
            "renamed": 0,
            "skipped_no_exif": 0,
            "skipped_no_date": 0,
            "errors": 0,
            "errors_list": [],
        }

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
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Override with environment variables if present
        if os.getenv("SOURCE_DIRECTORY"):
            config["source_directory"] = os.getenv("SOURCE_DIRECTORY")
        if os.getenv("DRY_RUN"):
            config["operations"]["dry_run"] = (
                os.getenv("DRY_RUN").lower() == "true"
            )
        if os.getenv("CREATE_BACKUP"):
            config["operations"]["create_backup"] = (
                os.getenv("CREATE_BACKUP").lower() == "true"
            )

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/photo_renamer.log")

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
        """Set up source and backup directories."""
        self.source_dir = Path(
            os.path.expanduser(self.config["source_directory"])
        )

        if not self.source_dir.exists():
            raise FileNotFoundError(
                f"Source directory does not exist: {self.source_dir}"
            )

        if self.config["operations"]["create_backup"]:
            backup_dir = self.source_dir / self.config["operations"]["backup_directory"]
            backup_dir.mkdir(parents=True, exist_ok=True)
            self.backup_dir = backup_dir
        else:
            self.backup_dir = None

        logger.info(f"Source directory: {self.source_dir}")

    def _get_exif_data(self, image_path: Path) -> Optional[Dict]:
        """Extract EXIF data from image file.

        Args:
            image_path: Path to image file.

        Returns:
            Dictionary of EXIF data or None if not available.
        """
        try:
            with Image.open(image_path) as img:
                exif_data = img.getexif()
                if exif_data is None:
                    return None

                exif_dict = {}
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_dict[tag] = value

                return exif_dict

        except Exception as e:
            logger.warning(f"Error reading EXIF from {image_path}: {e}")
            return None

    def _parse_exif_date(self, date_string: str) -> Optional[datetime]:
        """Parse EXIF date string to datetime object.

        Args:
            date_string: EXIF date string (format: "YYYY:MM:DD HH:MM:SS").

        Returns:
            Datetime object or None if parsing fails.
        """
        try:
            # EXIF date format: "YYYY:MM:DD HH:MM:SS"
            return datetime.strptime(date_string, "%Y:%m:%d %H:%M:%S")
        except ValueError:
            try:
                # Try alternative format without seconds
                return datetime.strptime(date_string, "%Y:%m:%d %H:%M")
            except ValueError:
                logger.warning(f"Could not parse date string: {date_string}")
                return None

    def _get_date_taken(self, image_path: Path) -> Optional[datetime]:
        """Get date taken from EXIF data or file metadata.

        Args:
            image_path: Path to image file.

        Returns:
            Datetime object representing date taken, or None.
        """
        # Try EXIF data first
        exif_data = self._get_exif_data(image_path)
        if exif_data:
            date_fields = self.config.get("exif_date_fields", [])
            for field in date_fields:
                if field in exif_data:
                    date_str = exif_data[field]
                    if date_str:
                        parsed_date = self._parse_exif_date(str(date_str))
                        if parsed_date:
                            logger.debug(
                                f"Found EXIF date in {field}: {parsed_date}"
                            )
                            return parsed_date

        # Fallback to file modification date
        fallback_config = self.config.get("fallback", {})
        if fallback_config.get("use_file_modification_date", True):
            try:
                stat = image_path.stat()
                mod_time = datetime.fromtimestamp(stat.st_mtime)
                logger.debug(f"Using file modification date: {mod_time}")
                return mod_time
            except Exception as e:
                logger.warning(f"Error getting file modification date: {e}")

        # Fallback to file creation date (if available)
        if fallback_config.get("use_file_creation_date", False):
            try:
                stat = image_path.stat()
                # On Unix, st_birthtime may not be available
                if hasattr(stat, "st_birthtime"):
                    create_time = datetime.fromtimestamp(stat.st_birthtime)
                    logger.debug(f"Using file creation date: {create_time}")
                    return create_time
            except Exception as e:
                logger.warning(f"Error getting file creation date: {e}")

        return None

    def _generate_new_filename(
        self, image_path: Path, date_taken: datetime, counter: Optional[int] = None
    ) -> str:
        """Generate new filename based on date taken.

        Args:
            image_path: Original image path.
            date_taken: Datetime when photo was taken.
            counter: Optional sequential number for same timestamp.

        Returns:
            New filename string.
        """
        naming_config = self.config.get("naming", {})
        date_format = naming_config.get("date_format", "%Y-%m-%d")
        time_format = naming_config.get("time_format", "%H-%M-%S")

        date_str = date_taken.strftime(date_format)
        time_str = date_taken.strftime(time_format)

        original_name = image_path.stem
        extension = image_path.suffix if naming_config.get("preserve_extension", True) else ""

        if counter is not None and self.config.get("sequential_numbering", {}).get("enabled", True):
            padding = self.config.get("sequential_numbering", {}).get("padding", 3)
            counter_str = f"{counter:0{padding}d}"
            new_name = f"{date_str}_{time_str}_{counter_str}_{original_name}{extension}"
        else:
            new_name = f"{date_str}_{time_str}_{original_name}{extension}"

        return new_name

    def _get_timestamp_key(self, date_taken: datetime) -> str:
        """Generate timestamp key for sequential numbering.

        Args:
            date_taken: Datetime when photo was taken.

        Returns:
            String key representing the timestamp.
        """
        date_format = self.config.get("naming", {}).get("date_format", "%Y-%m-%d")
        time_format = self.config.get("naming", {}).get("time_format", "%H-%M-%S")
        return f"{date_taken.strftime(date_format)}_{date_taken.strftime(time_format)}"

    def _get_next_counter(self, timestamp_key: str) -> int:
        """Get next sequential counter for timestamp.

        Args:
            timestamp_key: Timestamp key string.

        Returns:
            Next counter value.
        """
        if timestamp_key not in self.timestamp_counter:
            start_number = self.config.get("sequential_numbering", {}).get("start_number", 1)
            self.timestamp_counter[timestamp_key] = start_number
        else:
            self.timestamp_counter[timestamp_key] += 1

        return self.timestamp_counter[timestamp_key]

    def _create_backup(self, file_path: Path) -> bool:
        """Create backup of file before renaming.

        Args:
            file_path: Path to file to backup.

        Returns:
            True if backup successful, False otherwise.
        """
        if not self.backup_dir:
            return False

        try:
            backup_path = self.backup_dir / file_path.name
            shutil.copy2(file_path, backup_path)
            logger.debug(f"Backup created: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating backup for {file_path}: {e}")
            return False

    def _rename_file(self, old_path: Path, new_path: Path) -> bool:
        """Rename file from old path to new path.

        Args:
            old_path: Current file path.
            new_path: New file path.

        Returns:
            True if successful, False otherwise.
        """
        try:
            if self.config["operations"]["dry_run"]:
                logger.info(f"[DRY RUN] Would rename: {old_path.name} -> {new_path.name}")
                return True

            # Create backup if enabled
            if self.config["operations"]["create_backup"]:
                self._create_backup(old_path)

            # Rename file
            old_path.rename(new_path)

            # Preserve timestamps if configured
            if self.config["operations"]["preserve_timestamps"]:
                stat = old_path.stat() if old_path.exists() else new_path.stat()
                os.utime(new_path, (stat.st_atime, stat.st_mtime))

            logger.info(f"Renamed: {old_path.name} -> {new_path.name}")
            self.stats["renamed"] += 1
            return True

        except FileExistsError:
            error_msg = f"Target file already exists: {new_path}"
            logger.warning(error_msg)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            return False
        except Exception as e:
            error_msg = f"Error renaming {old_path}: {e}"
            logger.error(error_msg)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            return False

    def _process_file(self, image_path: Path) -> None:
        """Process a single image file.

        Args:
            image_path: Path to image file to process.
        """
        self.stats["processed"] += 1

        try:
            # Get date taken
            date_taken = self._get_date_taken(image_path)

            if not date_taken:
                fallback_config = self.config.get("fallback", {})
                if fallback_config.get("skip_if_no_date", False):
                    logger.info(f"Skipping {image_path.name}: No date available")
                    self.stats["skipped_no_date"] += 1
                    return

                # Use fallback prefix
                prefix = fallback_config.get("prefix", "NO_DATE_")
                new_name = f"{prefix}{image_path.name}"
                new_path = image_path.parent / new_name
                self._rename_file(image_path, new_path)
                return

            # Generate timestamp key for sequential numbering
            timestamp_key = self._get_timestamp_key(date_taken)

            # Get counter for this timestamp
            counter = None
            if self.config.get("sequential_numbering", {}).get("enabled", True):
                counter = self._get_next_counter(timestamp_key)

            # Generate new filename
            new_name = self._generate_new_filename(image_path, date_taken, counter)
            new_path = image_path.parent / new_name

            # Handle name conflicts
            if new_path.exists() and new_path != image_path:
                # Increment counter and try again
                if counter is None:
                    counter = self.config.get("sequential_numbering", {}).get("start_number", 1)
                else:
                    counter += 1

                while new_path.exists():
                    new_name = self._generate_new_filename(image_path, date_taken, counter)
                    new_path = image_path.parent / new_name
                    counter += 1

                # Update counter for this timestamp
                self.timestamp_counter[timestamp_key] = counter - 1

            # Rename file
            if new_path != image_path:
                self._rename_file(image_path, new_path)
            else:
                logger.debug(f"File already has correct name: {image_path.name}")

        except Exception as e:
            error_msg = f"Error processing {image_path}: {e}"
            logger.error(error_msg, exc_info=True)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)

    def rename_photos(self) -> Dict[str, int]:
        """Rename all photos in source directory.

        Returns:
            Dictionary with statistics about the operation.
        """
        logger.info("Starting photo renaming")
        logger.info(f"Dry run mode: {self.config['operations']['dry_run']}")

        supported_formats = [
            ext.lower() for ext in self.config.get("supported_formats", [])
        ]

        # Process all image files
        for file_path in self.source_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_formats:
                self._process_file(file_path)

        logger.info("Photo renaming completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats


def main() -> int:
    """Main entry point for photo renamer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Rename photos using EXIF date taken metadata"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Preview changes without renaming files",
    )

    args = parser.parse_args()

    try:
        renamer = PhotoRenamer(config_path=args.config)
        if args.dry_run:
            renamer.config["operations"]["dry_run"] = True

        stats = renamer.rename_photos()

        # Print summary
        print("\n" + "=" * 50)
        print("Photo Renaming Summary")
        print("=" * 50)
        print(f"Photos processed: {stats['processed']}")
        print(f"Photos renamed: {stats['renamed']}")
        print(f"Skipped (no date): {stats['skipped_no_date']}")
        print(f"Errors: {stats['errors']}")
        if stats["errors_list"]:
            print("\nErrors:")
            for error in stats["errors_list"]:
                print(f"  - {error}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
