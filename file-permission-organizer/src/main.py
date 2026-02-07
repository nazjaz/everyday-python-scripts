"""File Permission Organizer - CLI tool for organizing files by permission settings.

This module provides a command-line tool for organizing files based on their
permission settings, grouping executable files, read-only files, and files
with specific permission patterns into categorized folders.
"""

import argparse
import logging
import logging.handlers
import os
import re
import shutil
import stat
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FilePermissionOrganizer:
    """Organizes files based on permission settings."""

    def __init__(self, config: Dict) -> None:
        """Initialize FilePermissionOrganizer.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.permission_folders = config.get("permission_folders", {})
        self.permission_patterns = config.get("permission_patterns", [])
        self.default_folder = config.get("default_folder", "other_permissions")
        self.options = config.get("options", {})
        self.file_handling = config.get("file_handling", {})
        self.source_dir = Path(config.get("source_dir", "downloads"))
        self.output_base_dir = Path(config.get("output_base_dir", "organized"))

        self.exclude_patterns = [
            re.compile(pattern) for pattern in config.get("exclude_patterns", [])
        ]
        self.exclude_directories = [
            re.compile(pattern) for pattern in config.get("exclude_directories", [])
        ]

    def get_file_permissions(self, file_path: Path) -> Tuple[int, str]:
        """Get file permissions as octal and string representation.

        Args:
            file_path: Path to file.

        Returns:
            Tuple of (octal_permissions, string_representation).
        """
        try:
            file_stat = file_path.stat()
            mode = file_stat.st_mode

            # Get octal representation (last 3 digits)
            octal_perms = stat.filemode(mode)
            octal_value = oct(stat.S_IMODE(mode))[2:]  # Remove '0o' prefix

            return int(octal_value), octal_perms

        except (OSError, IOError) as e:
            logger.error(f"Error getting permissions for {file_path}: {e}")
            return 0, "----------"

    def is_executable(
        self, file_path: Path, check_owner: bool = True, check_group: bool = False, check_other: bool = False
    ) -> bool:
        """Check if file is executable.

        Args:
            file_path: Path to file.
            check_owner: Check owner execute permission.
            check_group: Check group execute permission.
            check_other: Check other execute permission.

        Returns:
            True if file is executable based on criteria.
        """
        try:
            file_stat = file_path.stat()
            mode = file_stat.st_mode

            if check_owner and (mode & stat.S_IXUSR):
                return True
            if check_group and (mode & stat.S_IXGRP):
                return True
            if check_other and (mode & stat.S_IXOTH):
                return True

            return False

        except (OSError, IOError):
            return False

    def is_read_only(
        self, file_path: Path, check_owner: bool = True, check_group: bool = True, check_other: bool = True
    ) -> bool:
        """Check if file is read-only (no write permission).

        Args:
            file_path: Path to file.
            check_owner: Check owner write permission.
            check_group: Check group write permission.
            check_other: Check other write permission.

        Returns:
            True if file has no write permission based on criteria.
        """
        try:
            file_stat = file_path.stat()
            mode = file_stat.st_mode

            has_write = False

            if check_owner and (mode & stat.S_IWUSR):
                has_write = True
            if check_group and (mode & stat.S_IWGRP):
                has_write = True
            if check_other and (mode & stat.S_IWOTH):
                has_write = True

            return not has_write

        except (OSError, IOError):
            return False

    def is_write_only(
        self, file_path: Path, check_owner: bool = True, check_group: bool = True, check_other: bool = True
    ) -> bool:
        """Check if file is write-only (write but no read permission).

        Args:
            file_path: Path to file.
            check_owner: Check owner permissions.
            check_group: Check group permissions.
            check_other: Check other permissions.

        Returns:
            True if file has write but no read permission.
        """
        try:
            file_stat = file_path.stat()
            mode = file_stat.st_mode

            has_write = False
            has_read = False

            if check_owner:
                if mode & stat.S_IWUSR:
                    has_write = True
                if mode & stat.S_IRUSR:
                    has_read = True
            if check_group:
                if mode & stat.S_IWGRP:
                    has_write = True
                if mode & stat.S_IRGRP:
                    has_read = True
            if check_other:
                if mode & stat.S_IWOTH:
                    has_write = True
                if mode & stat.S_IROTH:
                    has_read = True

            return has_write and not has_read

        except (OSError, IOError):
            return False

    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from processing.

        Args:
            file_path: Path to file.

        Returns:
            True if file should be excluded.
        """
        filename = file_path.name

        for pattern in self.exclude_patterns:
            if pattern.search(filename):
                return True

        return False

    def should_exclude_directory(self, dir_path: Path) -> bool:
        """Check if directory should be excluded from processing.

        Args:
            dir_path: Path to directory.

        Returns:
            True if directory should be excluded.
        """
        dirname = dir_path.name

        for pattern in self.exclude_directories:
            if pattern.search(dirname):
                return True

        return False

    def get_destination_folder(self, file_path: Path) -> str:
        """Determine destination folder based on file permissions.

        Args:
            file_path: Path to file.

        Returns:
            Destination folder name.
        """
        # Check permission patterns first (more specific)
        octal_perms, _ = self.get_file_permissions(file_path)
        octal_str = str(octal_perms)

        for pattern_config in self.permission_patterns:
            if pattern_config["pattern"] == octal_str:
                return pattern_config["folder"]

        # Check executable files
        if "executable" in self.permission_folders:
            exec_config = self.permission_folders["executable"]
            if self.is_executable(
                file_path,
                check_owner=exec_config.get("check_owner", True),
                check_group=exec_config.get("check_group", False),
                check_other=exec_config.get("check_other", False),
            ):
                return exec_config["folder"]

        # Check read-only files
        if "read_only" in self.permission_folders:
            ro_config = self.permission_folders["read_only"]
            if self.is_read_only(
                file_path,
                check_owner=ro_config.get("check_owner", True),
                check_group=ro_config.get("check_group", True),
                check_other=ro_config.get("check_other", True),
            ):
                return ro_config["folder"]

        # Check write-only files
        if "write_only" in self.permission_folders:
            wo_config = self.permission_folders["write_only"]
            if self.is_write_only(
                file_path,
                check_owner=wo_config.get("check_owner", True),
                check_group=wo_config.get("check_group", True),
                check_other=wo_config.get("check_other", True),
            ):
                return wo_config["folder"]

        return self.default_folder

    def get_destination_path(self, source_path: Path, folder: str) -> Path:
        """Get destination path for a file.

        Args:
            source_path: Source file path.
            folder: Destination folder name.

        Returns:
            Destination path.
        """
        destination_dir = self.output_base_dir / folder

        # Create permission subfolders if enabled
        if self.options.get("create_permission_subfolders"):
            octal_perms, _ = self.get_file_permissions(source_path)
            destination_dir = destination_dir / str(octal_perms)

        destination_dir.mkdir(parents=True, exist_ok=True)

        return destination_dir / source_path.name

    def handle_file_conflict(self, destination_path: Path) -> Optional[Path]:
        """Handle file conflict when destination already exists.

        Args:
            destination_path: Original destination path.

        Returns:
            Resolved destination path or None to skip.
        """
        conflict_action = self.file_handling.get("on_conflict", "rename")

        if conflict_action == "skip":
            return None
        elif conflict_action == "overwrite":
            return destination_path
        elif conflict_action == "rename":
            stem = destination_path.stem
            suffix = destination_path.suffix
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = f"{stem}_{timestamp}{suffix}"
            return destination_path.parent / new_name
        else:
            logger.warning(f"Unknown conflict action: {conflict_action}, using rename")
            return self.handle_file_conflict(destination_path)

    def organize_file(self, file_path: Path) -> Tuple[bool, str]:
        """Organize a single file based on permissions.

        Args:
            file_path: Path to file to organize.

        Returns:
            Tuple of (success, message).
        """
        try:
            # Get destination folder
            folder = self.get_destination_folder(file_path)
            destination_path = self.get_destination_path(file_path, folder)

            # Handle conflicts
            if destination_path.exists():
                destination_path = self.handle_file_conflict(destination_path)
                if destination_path is None:
                    return False, f"Skipped (file exists): {file_path.name}"

            # Check filename length
            max_length = self.file_handling.get("max_filename_length", 0)
            if max_length > 0 and len(destination_path.name) > max_length:
                stem = destination_path.stem[:max_length - len(destination_path.suffix) - 1]
                destination_path = destination_path.parent / f"{stem}{destination_path.suffix}"

            # Move or copy file
            move_files = self.options.get("move_files", True)
            dry_run = self.options.get("dry_run", False)

            if dry_run:
                action = "Would move" if move_files else "Would copy"
                octal_perms, perm_str = self.get_file_permissions(file_path)
                return True, f"{action} {file_path.name} ({perm_str}) -> {folder}/"
            else:
                if move_files:
                    shutil.move(str(file_path), str(destination_path))
                    action = "Moved"
                else:
                    shutil.copy2(str(file_path), str(destination_path))
                    action = "Copied"

                octal_perms, perm_str = self.get_file_permissions(file_path)
                logger.info(f"{action} {file_path.name} ({perm_str}) to {folder}/")
                return True, f"{action} {file_path.name} ({perm_str}) -> {folder}/"

        except Exception as e:
            logger.error(f"Error organizing {file_path}: {e}")
            return False, f"Error: {e}"

    def organize_directory(
        self, directory: Optional[Path] = None, recursive: bool = False
    ) -> Dict[str, int]:
        """Organize all files in a directory.

        Args:
            directory: Directory to organize. If None, uses source_dir from config.
            recursive: Whether to process subdirectories recursively.

        Returns:
            Dictionary with statistics (organized, failed, skipped).
        """
        if directory is None:
            directory = self.source_dir

        directory = directory.resolve()

        if not directory.exists():
            logger.error(f"Source directory does not exist: {directory}")
            return {"organized": 0, "failed": 0, "skipped": 0}

        stats = {"organized": 0, "failed": 0, "skipped": 0}

        # Find all files
        if recursive:
            file_paths = list(directory.rglob("*"))
        else:
            file_paths = list(directory.glob("*"))

        # Filter to only files (not directories)
        file_paths = [p for p in file_paths if p.is_file()]

        # Filter excluded files
        file_paths = [p for p in file_paths if not self.should_exclude_file(p)]

        logger.info(f"Found {len(file_paths)} file(s) to organize")

        for file_path in file_paths:
            success, message = self.organize_file(file_path)

            if success:
                if "Skipped" in message:
                    stats["skipped"] += 1
                else:
                    stats["organized"] += 1
                print(f"✓ {message}")
            else:
                stats["failed"] += 1
                print(f"✗ {message}")

        return stats


def setup_logging(config: Dict) -> None:
    """Configure logging based on config file.

    Args:
        config: Configuration dictionary with logging settings.
    """
    log_config = config.get("logging", {})
    log_level = os.getenv("LOG_LEVEL", log_config.get("level", "INFO"))
    log_file = log_config.get("file", "logs/file_permission_organizer.log")
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
    source_dir_env = os.getenv("SOURCE_DIR")
    if source_dir_env:
        config["source_dir"] = source_dir_env

    output_dir_env = os.getenv("OUTPUT_DIR")
    if output_dir_env:
        config["output_base_dir"] = output_dir_env

    return config


def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Organize files by permission settings"
    )
    parser.add_argument(
        "-s",
        "--source",
        type=Path,
        help="Source directory to organize (overrides config)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output base directory (overrides config)",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Process directories recursively",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (don't actually move files)",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy files instead of moving them",
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

        # Override config with command-line arguments
        if args.source:
            config["source_dir"] = str(args.source)
        if args.output:
            config["output_base_dir"] = str(args.output)
        if args.dry_run:
            config["options"]["dry_run"] = True
        if args.copy:
            config["options"]["move_files"] = False

        organizer = FilePermissionOrganizer(config)

        print(f"Organizing files from: {organizer.source_dir}")
        print(f"Output directory: {organizer.output_base_dir}")
        if config["options"].get("dry_run", False):
            print("DRY RUN MODE: No files will be moved")
        print()

        stats = organizer.organize_directory(recursive=args.recursive)

        print()
        print("Organization complete:")
        print(f"  Organized: {stats['organized']}")
        print(f"  Skipped: {stats['skipped']}")
        print(f"  Failed: {stats['failed']}")

        if stats["failed"] > 0:
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
        logger.info("Organization interrupted by user")
        print("\nOrganization interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
