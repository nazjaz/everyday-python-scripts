"""Script Organizer - CLI tool for organizing script files by programming language.

This module provides a command-line tool for organizing script files by programming
language based on file extensions and shebang lines, creating language-specific
folders for better organization.
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


class ScriptOrganizer:
    """Organizes script files by programming language."""

    def __init__(self, config: Dict) -> None:
        """Initialize ScriptOrganizer.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.language_extensions = config.get("language_extensions", {})
        self.shebang_patterns = config.get("shebang_patterns", {})
        self.default_folder = config.get("default_folder", "Unknown")
        self.options = config.get("options", {})
        self.file_handling = config.get("file_handling", {})
        self.source_dir = Path(config.get("source_dir", "scripts"))
        self.output_base_dir = Path(config.get("output_base_dir", "organized"))

        self.exclude_patterns = [
            re.compile(pattern) for pattern in config.get("exclude_patterns", [])
        ]
        self.exclude_directories = [
            re.compile(pattern) for pattern in config.get("exclude_directories", [])
        ]

        # Build extension to language mapping
        self.extension_to_language = {}
        for language, lang_info in self.language_extensions.items():
            folder = lang_info.get("folder", language.title())
            for ext in lang_info.get("extensions", []):
                self.extension_to_language[ext.lower()] = {
                    "language": language,
                    "folder": folder,
                }

        # Build shebang pattern to language mapping
        self.shebang_to_language = {}
        for language, lang_info in self.shebang_patterns.items():
            folder = lang_info.get("folder", language.title())
            for pattern in lang_info.get("patterns", []):
                self.shebang_to_language[pattern.lower()] = {
                    "language": language,
                    "folder": folder,
                }

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
        dirname = str(dir_path)

        for pattern in self.exclude_directories:
            if pattern.search(dirname):
                return True

        return False

    def get_shebang_language(self, file_path: Path) -> Optional[Dict]:
        """Get language from shebang line.

        Args:
            file_path: Path to file.

        Returns:
            Dictionary with language and folder info, or None if no shebang match.
        """
        try:
            with open(file_path, "rb") as f:
                first_line = f.readline(512).decode("utf-8", errors="ignore").strip()

            if not first_line.startswith("#!"):
                return None

            # Extract interpreter from shebang
            shebang_content = first_line[2:].strip()
            # Remove path, keep just the command
            interpreter = shebang_content.split()[0] if shebang_content else ""
            interpreter = Path(interpreter).name.lower()

            # Check for env pattern (e.g., /usr/bin/env python)
            if "/env" in shebang_content.lower():
                parts = shebang_content.lower().split()
                if len(parts) > 1:
                    interpreter = parts[-1]

            # Match against patterns
            for pattern, lang_info in self.shebang_to_language.items():
                if pattern in interpreter:
                    return lang_info

            return None

        except (IOError, OSError, UnicodeDecodeError):
            return None

    def get_language_by_extension(self, file_path: Path) -> Optional[Dict]:
        """Get language from file extension.

        Args:
            file_path: Path to file.

        Returns:
            Dictionary with language and folder info, or None if no match.
        """
        ext = file_path.suffix.lower().lstrip(".")
        return self.extension_to_language.get(ext)

    def get_language_folder(self, file_path: Path) -> str:
        """Determine language folder for a script file.

        Args:
            file_path: Path to file.

        Returns:
            Language folder name.
        """
        detection_priority = self.options.get("detection_priority", "extension")

        if detection_priority == "shebang":
            # Check shebang first
            lang_info = self.get_shebang_language(file_path)
            if lang_info:
                return lang_info["folder"]

            # Then check extension
            lang_info = self.get_language_by_extension(file_path)
            if lang_info:
                return lang_info["folder"]
        else:
            # Check extension first (default)
            lang_info = self.get_language_by_extension(file_path)
            if lang_info:
                return lang_info["folder"]

            # Then check shebang
            lang_info = self.get_shebang_language(file_path)
            if lang_info:
                return lang_info["folder"]

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

        # Create extension subfolders if enabled
        if self.options.get("create_extension_subfolders"):
            ext = source_path.suffix.lower().lstrip(".") or "no_extension"
            destination_dir = destination_dir / ext

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
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            stem = destination_path.stem
            suffix = destination_path.suffix
            new_name = f"{stem}_{timestamp}{suffix}"
            return destination_path.parent / new_name
        else:
            logger.warning(f"Unknown conflict action: {conflict_action}, using rename")
            return self.handle_file_conflict(destination_path)

    def organize_file(self, file_path: Path) -> Tuple[bool, str]:
        """Organize a single script file.

        Args:
            file_path: Path to file to organize.

        Returns:
            Tuple of (success, message).
        """
        try:
            # Get destination folder
            folder = self.get_language_folder(file_path)
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
                return True, f"{action} {file_path.name} -> {folder}/"
            else:
                if move_files:
                    shutil.move(str(file_path), str(destination_path))
                    action = "Moved"
                else:
                    shutil.copy2(str(file_path), str(destination_path))
                    action = "Copied"

                logger.info(f"{action} {file_path.name} to {folder}/")
                return True, f"{action} {file_path.name} -> {folder}/"

        except Exception as e:
            logger.error(f"Error organizing {file_path}: {e}")
            return False, f"Error: {e}"

    def organize_directory(
        self, directory: Optional[Path] = None, recursive: bool = False
    ) -> Dict[str, int]:
        """Organize all script files in a directory.

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
    log_file = log_config.get("file", "logs/script_organizer.log")
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
        description="Organize script files by programming language"
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
        "--priority",
        choices=["extension", "shebang"],
        help="Detection priority (extension or shebang)",
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
        if args.priority:
            config["options"]["detection_priority"] = args.priority

        organizer = ScriptOrganizer(config)

        print(f"Organizing scripts from: {organizer.source_dir}")
        print(f"Output directory: {organizer.output_base_dir}")
        print(f"Detection priority: {config['options'].get('detection_priority', 'extension')}")
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
