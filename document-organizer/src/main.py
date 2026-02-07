"""Document Organizer - Organize document files by type.

This module provides functionality to organize document files by type into
folders like PDFs, Word-Documents, Spreadsheets, and Presentations based
on file extensions and MIME types. Includes comprehensive logging and
duplicate handling.
"""

import logging
import logging.handlers
import mimetypes
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DocumentOrganizer:
    """Organizes document files by type into categorized folders."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize DocumentOrganizer with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_directories()
        self._init_mime_types()
        self.stats = {
            "files_scanned": 0,
            "files_organized": 0,
            "files_skipped": 0,
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
        if os.getenv("DRY_RUN"):
            config["operations"]["dry_run"] = (
                os.getenv("DRY_RUN").lower() == "true"
            )

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/document_organizer.log")

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
        self.dest_base = Path(
            os.path.expanduser(self.config["destination_directory"])
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

    def _init_mime_types(self) -> None:
        """Initialize MIME type mappings."""
        mimetypes.init()

    def _get_mime_type(self, file_path: Path) -> Optional[str]:
        """Get MIME type of a file.

        Args:
            file_path: Path to file.

        Returns:
            MIME type string, or None if cannot be determined.
        """
        # Try to guess from extension first
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            return mime_type

        # Try to read file content for more accurate detection
        try:
            import magic
            mime_type = magic.from_file(str(file_path), mime=True)
            if mime_type:
                return mime_type
        except ImportError:
            # python-magic not available, use extension only
            logger.debug("python-magic not available, using extension-based detection")
        except Exception as e:
            logger.debug(f"Error detecting MIME type for {file_path}: {e}")

        return None

    def _get_document_category(
        self, file_path: Path
    ) -> Optional[str]:
        """Determine document category based on extension and MIME type.

        Args:
            file_path: Path to file.

        Returns:
            Category name or None if not a recognized document type.
        """
        extension = file_path.suffix.lower()
        mime_type = self._get_mime_type(file_path)

        # Check categories
        for category_name, category_config in self.config["categories"].items():
            # Check extensions
            if extension in [
                ext.lower() for ext in category_config.get("extensions", [])
            ]:
                return category_name

            # Check MIME types
            if mime_type:
                category_mime_types = category_config.get("mime_types", [])
                if mime_type in category_mime_types:
                    return category_name

                # Check MIME type patterns (e.g., "application/pdf")
                for mime_pattern in category_mime_types:
                    if mime_pattern in mime_type:
                        return category_name

        return None

    def _should_organize_file(self, file_path: Path) -> bool:
        """Check if file should be organized.

        Args:
            file_path: Path to file.

        Returns:
            True if file should be organized, False otherwise.
        """
        exclusions = self.config.get("exclusions", {})
        file_name = file_path.name

        # Check excluded patterns
        excluded_patterns = exclusions.get("patterns", [])
        for pattern in excluded_patterns:
            if pattern in file_name:
                return False

        # Check excluded extensions
        excluded_extensions = exclusions.get("extensions", [])
        if file_path.suffix.lower() in [
            ext.lower() for ext in excluded_extensions
        ]:
            return False

        return True

    def _handle_duplicate(
        self, source_path: Path, dest_path: Path
    ) -> Optional[Path]:
        """Handle duplicate file names.

        Args:
            source_path: Source file path.
            dest_path: Intended destination path.

        Returns:
            Final destination path (may be modified if duplicate).
        """
        if not dest_path.exists():
            return dest_path

        action = self.config.get("duplicate_handling", "rename")

        if action == "skip":
            logger.info(f"Skipping duplicate: {dest_path.name}")
            self.stats["files_skipped"] += 1
            return None

        elif action == "rename":
            counter = 1
            stem = dest_path.stem
            suffix = dest_path.suffix
            parent = dest_path.parent

            while dest_path.exists():
                new_name = f"{stem}_{counter}{suffix}"
                dest_path = parent / new_name
                counter += 1

            logger.debug(f"Renamed duplicate to: {dest_path.name}")
            return dest_path

        elif action == "overwrite":
            logger.warning(f"Overwriting existing file: {dest_path}")
            return dest_path

        return dest_path

    def _organize_file(self, file_path: Path) -> bool:
        """Organize a single document file.

        Args:
            file_path: Path to file to organize.

        Returns:
            True if successful, False otherwise.
        """
        self.stats["files_scanned"] += 1

        if not self._should_organize_file(file_path):
            logger.debug(f"Skipping excluded file: {file_path.name}")
            self.stats["files_skipped"] += 1
            return False

        category = self._get_document_category(file_path)
        if not category:
            logger.debug(f"No category found for {file_path.name}, skipping")
            self.stats["files_skipped"] += 1
            return False

        category_config = self.config["categories"][category]
        dest_dir = self.dest_base / category_config["folder"]
        dest_path = dest_dir / file_path.name

        # Handle duplicates
        dest_path = self._handle_duplicate(file_path, dest_path)
        if dest_path is None:
            return False

        try:
            if self.config["operations"]["dry_run"]:
                logger.info(
                    f"[DRY RUN] Would move: {file_path.name} -> "
                    f"{dest_path.relative_to(self.dest_base)}"
                )
                self.stats["files_organized"] += 1
                return True

            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Move or copy file
            if self.config["operations"]["method"] == "move":
                shutil.move(str(file_path), str(dest_path))
                logger.info(
                    f"Moved: {file_path.name} -> "
                    f"{dest_path.relative_to(self.dest_base)}"
                )
            else:
                shutil.copy2(str(file_path), str(dest_path))
                logger.info(
                    f"Copied: {file_path.name} -> "
                    f"{dest_path.relative_to(self.dest_base)}"
                )

            # Preserve timestamps
            if self.config["operations"]["preserve_timestamps"]:
                stat = file_path.stat()
                os.utime(dest_path, (stat.st_atime, stat.st_mtime))

            self.stats["files_organized"] += 1
            return True

        except (OSError, shutil.Error) as e:
            error_msg = f"Error organizing {file_path}: {e}"
            logger.error(error_msg)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            return False

    def organize_documents(self) -> Dict[str, any]:
        """Organize all document files in source directory.

        Returns:
            Dictionary with statistics about the operation.
        """
        logger.info("Starting document organization")
        logger.info(f"Dry run mode: {self.config['operations']['dry_run']}")

        # Scan source directory
        document_files = []
        if self.config["operations"]["recursive"]:
            for file_path in self.source_dir.rglob("*"):
                if file_path.is_file():
                    document_files.append(file_path)
        else:
            for file_path in self.source_dir.iterdir():
                if file_path.is_file():
                    document_files.append(file_path)

        logger.info(f"Found {len(document_files)} files to process")

        # Organize each file
        for file_path in document_files:
            self._organize_file(file_path)

        logger.info("Document organization completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats


def main() -> int:
    """Main entry point for document organizer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Organize document files by type into categorized folders"
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
        organizer = DocumentOrganizer(config_path=args.config)

        if args.dry_run:
            organizer.config["operations"]["dry_run"] = True

        stats = organizer.organize_documents()

        # Print summary
        print("\n" + "=" * 60)
        print("Document Organization Summary")
        print("=" * 60)
        print(f"Files Scanned: {stats['files_scanned']}")
        print(f"Files Organized: {stats['files_organized']}")
        print(f"Files Skipped: {stats['files_skipped']}")
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
