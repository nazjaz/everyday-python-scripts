"""File Category Organizer - Organize files by extension groups.

This module provides functionality to organize files by extension groups
into categories like Media, Documents, Archives, Code, and Data with
custom mappings.
"""

import hashlib
import logging
import logging.handlers
import os
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FileCategoryOrganizer:
    """Organizes files by extension groups into categories."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize FileCategoryOrganizer with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.category_mappings = self._load_category_mappings()
        self.stats = {
            "files_processed": 0,
            "files_moved": 0,
            "files_skipped": 0,
            "duplicates_found": 0,
            "errors": 0,
            "categories": defaultdict(int),
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
            config["organizer"]["source_directory"] = os.getenv("SOURCE_DIRECTORY")
        if os.getenv("DESTINATION_DIRECTORY"):
            config["organizer"]["destination_directory"] = os.getenv("DESTINATION_DIRECTORY")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/file_organizer.log")

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

    def _load_category_mappings(self) -> Dict[str, str]:
        """Load category mappings from configuration.

        Returns:
            Dictionary mapping file extensions to categories.
        """
        mappings = {}

        # Load default category mappings
        default_categories = self.config.get("categories", {})
        for category, extensions in default_categories.items():
            for ext in extensions:
                # Normalize extension (remove dot, lowercase)
                normalized_ext = ext.lstrip(".").lower()
                mappings[normalized_ext] = category

        # Load custom mappings (override defaults)
        custom_mappings = self.config.get("custom_mappings", {})
        for ext, category in custom_mappings.items():
            normalized_ext = ext.lstrip(".").lower()
            mappings[normalized_ext] = category

        logger.info(f"Loaded {len(mappings)} extension mappings")
        return mappings

    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file.

        Args:
            file_path: Path to file.

        Returns:
            MD5 hash as hexadecimal string.
        """
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (IOError, OSError) as e:
            logger.warning(f"Could not calculate hash for {file_path}: {e}")
            return ""

    def _is_duplicate(self, file_path: Path, destination_dir: Path) -> bool:
        """Check if file is duplicate in destination.

        Args:
            file_path: Source file path.
            destination_dir: Destination directory.

        Returns:
            True if duplicate exists, False otherwise.
        """
        if not self.config.get("organizer", {}).get("check_duplicates", False):
            return False

        source_hash = self._get_file_hash(file_path)
        if not source_hash:
            return False

        # Check all files in destination directory
        for dest_file in destination_dir.rglob("*"):
            if not dest_file.is_file():
                continue
            if dest_file.name == file_path.name:
                dest_hash = self._get_file_hash(dest_file)
                if dest_hash == source_hash:
                    return True

        return False

    def _get_category(self, file_path: Path) -> str:
        """Get category for file based on extension.

        Args:
            file_path: Path to file.

        Returns:
            Category name or 'Other' if not found.
        """
        extension = file_path.suffix.lstrip(".").lower()
        category = self.category_mappings.get(extension, "Other")
        return category

    def _get_destination_path(
        self, file_path: Path, category: str, destination_base: Path
    ) -> Path:
        """Get destination path for file.

        Args:
            file_path: Source file path.
            category: Category name.
            destination_base: Base destination directory.

        Returns:
            Destination path for file.
        """
        category_dir = destination_base / category
        destination = category_dir / file_path.name

        # Handle duplicate names
        if destination.exists():
            handle_duplicates = self.config.get("organizer", {}).get(
                "handle_duplicate_names", "rename"
            )

            if handle_duplicates == "skip":
                return destination  # Will be skipped later

            elif handle_duplicates == "rename":
                counter = 1
                base_name = file_path.stem
                extension = file_path.suffix
                while destination.exists():
                    new_name = f"{base_name}_{counter}{extension}"
                    destination = category_dir / new_name
                    counter += 1

        return destination

    def _should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed.

        Args:
            file_path: Path to file.

        Returns:
            True if file should be processed, False otherwise.
        """
        # Check exclusions
        exclude_config = self.config.get("organizer", {}).get("exclude", {})
        exclude_patterns = exclude_config.get("patterns", [])
        exclude_extensions = exclude_config.get("extensions", [])

        # Check extension exclusion
        if exclude_extensions:
            file_ext = file_path.suffix.lower()
            if file_ext in [ext.lower() for ext in exclude_extensions]:
                return False

        # Check pattern exclusion
        file_str = str(file_path)
        for pattern in exclude_patterns:
            try:
                import re

                if re.search(pattern, file_str):
                    return False
            except Exception:
                pass

        # Check if file is in destination directory
        destination = Path(
            self.config.get("organizer", {}).get("destination_directory", "organized")
        )
        try:
            if file_path.resolve().is_relative_to(destination.resolve()):
                return False
        except (ValueError, AttributeError):
            # Python < 3.9 compatibility
            try:
                if str(file_path.resolve()).startswith(str(destination.resolve())):
                    return False
            except Exception:
                pass

        return True

    def organize_files(
        self,
        source_directory: Optional[str] = None,
        destination_directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Organize files by extension groups into categories.

        Args:
            source_directory: Source directory (overrides config).
            destination_directory: Destination directory (overrides config).

        Returns:
            Dictionary with organization statistics.

        Raises:
            FileNotFoundError: If source directory doesn't exist.
            ValueError: If configuration is invalid.
        """
        organizer_config = self.config.get("organizer", {})

        # Determine directories
        if source_directory:
            source_dir = Path(source_directory)
        else:
            source_dir = Path(organizer_config.get("source_directory", "."))

        if destination_directory:
            dest_dir = Path(destination_directory)
        else:
            dest_dir = Path(organizer_config.get("destination_directory", "organized"))

        if not source_dir.exists():
            raise FileNotFoundError(f"Source directory does not exist: {source_dir}")

        if not source_dir.is_dir():
            raise ValueError(f"Source path is not a directory: {source_dir}")

        logger.info(f"Organizing files from {source_dir} to {dest_dir}")

        # Reset stats
        self.stats = {
            "files_processed": 0,
            "files_moved": 0,
            "files_skipped": 0,
            "duplicates_found": 0,
            "errors": 0,
            "categories": defaultdict(int),
        }

        # Create destination directory
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Process files
        recursive = organizer_config.get("recursive", True)
        if recursive:
            file_iterator = source_dir.rglob("*")
        else:
            file_iterator = source_dir.glob("*")

        for file_path in file_iterator:
            if not file_path.is_file():
                continue

            self.stats["files_processed"] += 1

            # Check if file should be processed
            if not self._should_process_file(file_path):
                self.stats["files_skipped"] += 1
                logger.debug(f"Skipping file: {file_path}")
                continue

            # Get category
            category = self._get_category(file_path)
            self.stats["categories"][category] += 1

            # Get destination path
            destination = self._get_destination_path(file_path, category, dest_dir)

            # Check for duplicates
            if self._is_duplicate(file_path, dest_dir):
                self.stats["duplicates_found"] += 1
                handle_duplicates = organizer_config.get("handle_duplicates", "skip")
                if handle_duplicates == "skip":
                    self.stats["files_skipped"] += 1
                    logger.info(f"Skipping duplicate: {file_path}")
                    continue

            # Create category directory
            destination.parent.mkdir(parents=True, exist_ok=True)

            # Move file
            try:
                if destination.exists() and organizer_config.get("overwrite_existing", False):
                    logger.warning(f"Overwriting existing file: {destination}")
                    destination.unlink()

                shutil.move(str(file_path), str(destination))
                self.stats["files_moved"] += 1
                logger.info(f"Moved: {file_path.name} -> {category}/{destination.name}")

            except (OSError, shutil.Error) as e:
                logger.error(f"Error moving {file_path} to {destination}: {e}")
                self.stats["errors"] += 1

        logger.info(
            f"Organization complete: {self.stats['files_moved']} moved, "
            f"{self.stats['files_skipped']} skipped, {self.stats['errors']} errors"
        )

        return self.stats

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics.

        Returns:
            Dictionary with statistics.
        """
        stats = self.stats.copy()
        stats["categories"] = dict(stats["categories"])
        return stats


def main() -> int:
    """Main entry point for file category organizer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Organize files by extension groups into categories"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-s",
        "--source",
        help="Source directory (overrides config)",
    )
    parser.add_argument(
        "-d",
        "--destination",
        help="Destination directory (overrides config)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually moving files",
    )

    args = parser.parse_args()

    try:
        organizer = FileCategoryOrganizer(config_path=args.config)

        if args.dry_run:
            print("DRY RUN MODE - No files will be moved")
            print("=" * 60)

            source_dir = Path(
                args.source
                or organizer.config.get("organizer", {}).get("source_directory", ".")
            )
            dest_dir = Path(
                args.destination
                or organizer.config.get("organizer", {}).get("destination_directory", "organized")
            )

            recursive = organizer.config.get("organizer", {}).get("recursive", True)
            if recursive:
                files = list(source_dir.rglob("*"))
            else:
                files = list(source_dir.glob("*"))

            file_count = 0
            category_counts = defaultdict(int)

            for file_path in files:
                if not file_path.is_file():
                    continue
                if not organizer._should_process_file(file_path):
                    continue

                category = organizer._get_category(file_path)
                category_counts[category] += 1
                file_count += 1

                destination = organizer._get_destination_path(file_path, category, dest_dir)
                print(f"  {file_path.name} -> {category}/{destination.name}")

            print(f"\nWould process {file_count} file(s)")
            print("\nCategory distribution:")
            for category, count in sorted(category_counts.items()):
                print(f"  {category}: {count}")

            return 0

        # Perform organization
        stats = organizer.organize_files(
            source_directory=args.source, destination_directory=args.destination
        )

        # Print summary
        print("\n" + "=" * 60)
        print("File Organization Summary")
        print("=" * 60)
        print(f"Files processed: {stats['files_processed']}")
        print(f"Files moved: {stats['files_moved']}")
        print(f"Files skipped: {stats['files_skipped']}")
        print(f"Duplicates found: {stats['duplicates_found']}")
        print(f"Errors: {stats['errors']}")

        print("\nCategory distribution:")
        for category, count in sorted(stats["categories"].items()):
            print(f"  {category}: {count} file(s)")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
