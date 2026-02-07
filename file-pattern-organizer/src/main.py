"""File Pattern Organizer - CLI tool for organizing files by regex patterns.

This module provides a command-line tool for organizing files by matching
filename patterns using regular expressions and moving files to corresponding
folders. Supports multiple patterns, conflict resolution, and comprehensive
logging.
"""

import argparse
import logging
import logging.handlers
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FilePatternOrganizer:
    """Organizes files based on regex pattern matching."""

    def __init__(self, config: Dict) -> None:
        """Initialize FilePatternOrganizer.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.patterns = config.get("patterns", [])
        self.default_folder = config.get("default_folder", "misc")
        self.options = config.get("options", {})
        self.file_handling = config.get("file_handling", {})
        self.source_dir = Path(config.get("source_dir", "downloads"))
        self.output_base_dir = Path(config.get("output_base_dir", "organized"))

        # Compile regex patterns for efficiency
        self.compiled_patterns = []
        for pattern_config in self.patterns:
            try:
                pattern = re.compile(pattern_config["pattern"])
                self.compiled_patterns.append({
                    "pattern": pattern,
                    "folder": pattern_config["folder"],
                    "description": pattern_config.get("description", ""),
                })
            except re.error as e:
                logger.error(f"Invalid regex pattern '{pattern_config['pattern']}': {e}")

    def match_pattern(self, filename: str) -> Optional[Dict]:
        """Match filename against patterns.

        Args:
            filename: Filename to match.

        Returns:
            Dictionary with folder and match info, or None if no match.
        """
        for pattern_info in self.compiled_patterns:
            match = pattern_info["pattern"].search(filename)
            if match:
                return {
                    "folder": pattern_info["folder"],
                    "description": pattern_info["description"],
                    "match": match,
                }
        return None

    def get_destination_path(
        self, source_path: Path, match_info: Optional[Dict] = None
    ) -> Path:
        """Get destination path for a file.

        Args:
            source_path: Source file path.
            match_info: Pattern match information.

        Returns:
            Destination path.
        """
        if match_info:
            folder = match_info["folder"]
        else:
            folder = self.default_folder

        destination_dir = self.output_base_dir / folder

        # Create date subfolders if enabled
        if self.options.get("create_date_subfolders"):
            date_str = datetime.now().strftime("%Y-%m")
            destination_dir = destination_dir / date_str

        # Use capture groups if enabled and available
        if (
            self.options.get("use_capture_groups")
            and match_info
            and match_info["match"].groups()
        ):
            # Use first capture group as subfolder
            subfolder = match_info["match"].group(1)
            if subfolder:
                destination_dir = destination_dir / subfolder

        destination_dir.mkdir(parents=True, exist_ok=True)

        return destination_dir / source_path.name

    def handle_file_conflict(self, destination_path: Path) -> Path:
        """Handle file conflict when destination already exists.

        Args:
            destination_path: Original destination path.

        Returns:
            Resolved destination path.
        """
        conflict_action = self.file_handling.get("on_conflict", "rename")

        if conflict_action == "skip":
            return None  # Signal to skip this file
        elif conflict_action == "overwrite":
            return destination_path
        elif conflict_action == "rename":
            # Add timestamp to filename
            stem = destination_path.stem
            suffix = destination_path.suffix
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = f"{stem}_{timestamp}{suffix}"
            return destination_path.parent / new_name
        else:
            logger.warning(f"Unknown conflict action: {conflict_action}, using rename")
            return self.handle_file_conflict(destination_path)

    def organize_file(self, file_path: Path) -> Tuple[bool, str]:
        """Organize a single file.

        Args:
            file_path: Path to file to organize.

        Returns:
            Tuple of (success, message).
        """
        try:
            # Match pattern
            match_info = self.match_pattern(file_path.name)

            # Get destination path
            destination_path = self.get_destination_path(file_path, match_info)

            # Handle conflicts
            if destination_path.exists():
                destination_path = self.handle_file_conflict(destination_path)
                if destination_path is None:
                    return False, f"Skipped (file exists): {file_path.name}"

            # Check filename length
            max_length = self.file_handling.get("max_filename_length", 0)
            if max_length > 0 and len(destination_path.name) > max_length:
                # Truncate filename
                stem = destination_path.stem[:max_length - len(destination_path.suffix) - 1]
                destination_path = destination_path.parent / f"{stem}{destination_path.suffix}"

            # Move or copy file
            move_files = self.options.get("move_files", True)
            dry_run = self.options.get("dry_run", False)

            if dry_run:
                action = "Would move" if move_files else "Would copy"
                folder = match_info["folder"] if match_info else self.default_folder
                return True, f"{action} {file_path.name} -> {folder}/"
            else:
                if move_files:
                    shutil.move(str(file_path), str(destination_path))
                    action = "Moved"
                else:
                    shutil.copy2(str(file_path), str(destination_path))
                    action = "Copied"

                folder = match_info["folder"] if match_info else self.default_folder
                logger.info(f"{action} {file_path.name} to {folder}/")
                return True, f"{action} {file_path.name} -> {folder}/"

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
    log_file = log_config.get("file", "logs/file_organizer.log")
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
        description="Organize files by matching filename patterns using regex"
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

        organizer = FilePatternOrganizer(config)

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
