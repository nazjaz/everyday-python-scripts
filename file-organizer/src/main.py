"""File Organizer - Automatically organize downloaded files by category.

This module provides functionality to automatically organize files from a
download directory into categorized folders based on file extensions.
Includes duplicate detection using file hashing and comprehensive logging.
"""

import hashlib
import logging
import logging.handlers
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FileOrganizer:
    """Organizes files into categorized folders based on extensions."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize FileOrganizer with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_directories()
        self.file_hashes: Dict[str, str] = {}
        self.stats = {
            "processed": 0,
            "moved": 0,
            "skipped_duplicates": 0,
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
        
        # If relative path, try to find it relative to project root
        if not config_file.is_absolute():
            # Try current directory first
            if not config_file.exists():
                # Try parent directory (if running from src/)
                parent_config = Path(__file__).parent.parent / config_path
                if parent_config.exists():
                    config_file = parent_config
                else:
                    # Try current working directory
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
        if os.getenv("DESTINATION_BASE"):
            config["destination_base"] = os.getenv("DESTINATION_BASE")
        if os.getenv("DRY_RUN"):
            config["operations"]["dry_run"] = (
                os.getenv("DRY_RUN").lower() == "true"
            )

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/file_organizer.log")

        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        # If relative path, make it relative to project root
        if not log_path.is_absolute():
            project_root = Path(__file__).parent.parent
            log_path = project_root / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Remove existing handlers
        root_logger.handlers.clear()

        # File handler with rotation
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

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(
            "%(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        logger.info("Logging configured successfully")

    def _setup_directories(self) -> None:
        """Set up source and destination directories."""
        self.source_dir = Path(
            os.path.expanduser(self.config["source_directory"])
        )
        self.dest_base = Path(
            os.path.expanduser(self.config["destination_base"])
        )

        if not self.source_dir.exists():
            raise FileNotFoundError(
                f"Source directory does not exist: {self.source_dir}"
            )

        if self.config["operations"]["create_directories"]:
            self.dest_base.mkdir(parents=True, exist_ok=True)
            for category in self.config["categories"].values():
                category_path = self.dest_base / category["folder"]
                category_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Source directory: {self.source_dir}")
        logger.info(f"Destination base: {self.dest_base}")

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate hash of file content.

        Args:
            file_path: Path to file.

        Returns:
            Hexadecimal hash string.
        """
        algorithm = self.config["duplicate_detection"]["hash_algorithm"]
        hash_obj = hashlib.new(algorithm)

        try:
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files efficiently
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except (IOError, OSError) as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            raise

    def _is_duplicate(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Check if file is a duplicate.

        Args:
            file_path: Path to file to check.

        Returns:
            Tuple of (is_duplicate, existing_file_path).
        """
        if not self.config["duplicate_detection"]["enabled"]:
            return False, None

        method = self.config["duplicate_detection"]["method"]

        if method in ("hash", "both"):
            file_hash = self._calculate_file_hash(file_path)
            if file_hash in self.file_hashes:
                existing_file = self.file_hashes[file_hash]
                logger.debug(
                    f"Duplicate detected by hash: {file_path.name} "
                    f"matches {existing_file}"
                )
                return True, existing_file
            self.file_hashes[file_hash] = str(file_path)

        if method in ("name", "both"):
            # Check for files with same name in destination
            for category in self.config["categories"].values():
                dest_dir = self.dest_base / category["folder"]
                existing_file = dest_dir / file_path.name
                if existing_file.exists():
                    logger.debug(
                        f"Duplicate detected by name: {file_path.name} "
                        f"exists in {dest_dir}"
                    )
                    return True, str(existing_file)

        return False, None

    def _get_file_category(self, file_path: Path) -> Optional[str]:
        """Determine file category based on extension.

        Args:
            file_path: Path to file.

        Returns:
            Category name or None if no match.
        """
        extension = file_path.suffix.lower()

        for category_name, category_config in self.config["categories"].items():
            if extension in [
                ext.lower() for ext in category_config["extensions"]
            ]:
                return category_name

        return None

    def _handle_duplicate(
        self, file_path: Path, existing_file: str
    ) -> bool:
        """Handle duplicate file based on configuration.

        Args:
            file_path: Path to duplicate file.
            existing_file: Path to existing file.

        Returns:
            True if file should be skipped, False otherwise.
        """
        action = self.config["duplicate_detection"]["action"]

        if action == "skip":
            logger.info(
                f"Skipping duplicate: {file_path.name} "
                f"(matches {existing_file})"
            )
            self.stats["skipped_duplicates"] += 1
            return True

        elif action == "rename":
            # Add timestamp to filename
            stem = file_path.stem
            suffix = file_path.suffix
            timestamp = int(file_path.stat().st_mtime)
            new_name = f"{stem}_{timestamp}{suffix}"
            file_path = file_path.parent / new_name
            logger.info(f"Renaming duplicate to: {new_name}")
            return False

        elif action == "move_to_duplicates":
            duplicates_dir = self.dest_base / "Duplicates"
            duplicates_dir.mkdir(parents=True, exist_ok=True)
            dest_path = duplicates_dir / file_path.name
            logger.info(f"Moving duplicate to: {dest_path}")
            return False

        return False

    def _move_file(
        self, source_path: Path, dest_path: Path
    ) -> bool:
        """Move file to destination, preserving metadata if configured.

        Args:
            source_path: Source file path.
            dest_path: Destination file path.

        Returns:
            True if successful, False otherwise.
        """
        try:
            if self.config["operations"]["dry_run"]:
                logger.info(f"[DRY RUN] Would move: {source_path} -> {dest_path}")
                return True

            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Move file
            shutil.move(str(source_path), str(dest_path))

            # Preserve timestamps if configured
            if self.config["operations"]["preserve_timestamps"]:
                stat = source_path.stat()
                os.utime(dest_path, (stat.st_atime, stat.st_mtime))

            logger.info(f"Moved: {source_path.name} -> {dest_path}")
            self.stats["moved"] += 1
            return True

        except (OSError, shutil.Error) as e:
            error_msg = f"Error moving {source_path}: {e}"
            logger.error(error_msg)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            return False

    def organize_files(self) -> Dict[str, int]:
        """Organize all files in source directory.

        Returns:
            Dictionary with statistics about the operation.
        """
        logger.info("Starting file organization")
        logger.info(f"Dry run mode: {self.config['operations']['dry_run']}")

        # Build hash index of existing files in destination
        if self.config["duplicate_detection"]["enabled"]:
            self._build_hash_index()

        # Process all files in source directory
        for file_path in self.source_dir.iterdir():
            if file_path.is_file():
                self._process_file(file_path)

        logger.info("File organization completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats

    def _build_hash_index(self) -> None:
        """Build hash index of existing files in destination directories."""
        logger.debug("Building hash index of existing files")
        for category in self.config["categories"].values():
            dest_dir = self.dest_base / category["folder"]
            if dest_dir.exists():
                for existing_file in dest_dir.iterdir():
                    if existing_file.is_file():
                        try:
                            file_hash = self._calculate_file_hash(existing_file)
                            self.file_hashes[file_hash] = str(existing_file)
                        except Exception as e:
                            logger.warning(
                                f"Could not hash {existing_file}: {e}"
                            )

    def _process_file(self, file_path: Path) -> None:
        """Process a single file.

        Args:
            file_path: Path to file to process.
        """
        self.stats["processed"] += 1

        try:
            # Check for duplicates
            is_duplicate, existing_file = self._is_duplicate(file_path)
            if is_duplicate and existing_file:
                if self._handle_duplicate(file_path, existing_file):
                    return

            # Determine category
            category = self._get_file_category(file_path)
            if not category:
                logger.debug(
                    f"No category found for {file_path.name}, skipping"
                )
                return

            # Determine destination
            category_config = self.config["categories"][category]
            dest_dir = self.dest_base / category_config["folder"]
            dest_path = dest_dir / file_path.name

            # Handle name conflicts
            if dest_path.exists() and not is_duplicate:
                counter = 1
                stem = file_path.stem
                suffix = file_path.suffix
                while dest_path.exists():
                    new_name = f"{stem}_{counter}{suffix}"
                    dest_path = dest_dir / new_name
                    counter += 1
                logger.debug(
                    f"Name conflict resolved: {file_path.name} -> {dest_path.name}"
                )

            # Move file
            self._move_file(file_path, dest_path)

        except Exception as e:
            error_msg = f"Error processing {file_path}: {e}"
            logger.error(error_msg, exc_info=True)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)


def main() -> None:
    """Main entry point for file organizer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Organize downloaded files into categorized folders"
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
        help="Preview changes without moving files",
    )

    args = parser.parse_args()

    try:
        organizer = FileOrganizer(config_path=args.config)
        if args.dry_run:
            organizer.config["operations"]["dry_run"] = True

        stats = organizer.organize_files()

        # Print summary
        print("\n" + "=" * 50)
        print("File Organization Summary")
        print("=" * 50)
        print(f"Files processed: {stats['processed']}")
        print(f"Files moved: {stats['moved']}")
        print(f"Duplicates skipped: {stats['skipped_duplicates']}")
        print(f"Errors: {stats['errors']}")
        if stats["errors_list"]:
            print("\nErrors:")
            for error in stats["errors_list"]:
                print(f"  - {error}")

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
