"""Status-Based File Organizer - CLI tool for organizing files by status indicators.

This module provides a command-line tool for organizing files by status indicators
like completed, in-progress, draft, or archived based on naming conventions or
metadata.
"""

import argparse
import hashlib
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


class StatusDetector:
    """Detects file status from naming conventions and metadata."""

    def __init__(self, config: Dict) -> None:
        """Initialize StatusDetector.

        Args:
            config: Configuration dictionary containing status detection settings.
        """
        self.config = config
        self.status_config = config.get("status_indicators", {})

    def detect_from_filename(self, file_path: Path) -> Optional[str]:
        """Detect status from filename patterns.

        Args:
            file_path: Path to file to analyze.

        Returns:
            Status string or None if not detected.
        """
        filename = file_path.name.lower()
        stem = file_path.stem.lower()

        # Check each status category
        for status, indicators in self.status_config.items():
            patterns = indicators.get("filename_patterns", [])
            keywords = indicators.get("keywords", [])

            # Check patterns
            for pattern in patterns:
                if re.search(pattern, filename) or re.search(pattern, stem):
                    return status

            # Check keywords
            for keyword in keywords:
                if keyword.lower() in filename or keyword.lower() in stem:
                    return status

        return None

    def detect_from_metadata(self, file_path: Path) -> Optional[str]:
        """Detect status from file metadata.

        Args:
            file_path: Path to file to analyze.

        Returns:
            Status string or None if not detected.
        """
        try:
            stat_info = file_path.stat()
        except (OSError, PermissionError):
            return None

        # Check modification time patterns
        mod_time = datetime.fromtimestamp(stat_info.st_mtime)
        now = datetime.now()
        days_since_mod = (now - mod_time).days

        # Very old files might be archived
        if days_since_mod > 365:
            archived_config = self.status_config.get("archived", {})
            if archived_config.get("use_age_indicator", False):
                return "archived"

        # Check file size (very small might be draft)
        file_size = stat_info.st_size
        if file_size < 100:  # Very small files
            draft_config = self.status_config.get("draft", {})
            if draft_config.get("use_size_indicator", False):
                return "draft"

        return None

    def detect_from_content(self, file_path: Path) -> Optional[str]:
        """Detect status from file content (for text files).

        Args:
            file_path: Path to file to analyze.

        Returns:
            Status string or None if not detected.
        """
        # Only check text files
        text_extensions = [".txt", ".md", ".rst", ".log"]
        if file_path.suffix.lower() not in text_extensions:
            return None

        try:
            file_size = file_path.stat().st_size
            # Skip very large files
            if file_size > 1024 * 1024:  # 1 MB
                return None

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(5000).lower()  # Read first 5KB

            # Check for status keywords in content
            for status, indicators in self.status_config.items():
                content_keywords = indicators.get("content_keywords", [])
                for keyword in content_keywords:
                    if keyword.lower() in content:
                        return status

        except (OSError, PermissionError, UnicodeDecodeError):
            pass

        return None

    def detect_status(self, file_path: Path) -> Tuple[Optional[str], str]:
        """Detect file status using all available methods.

        Args:
            file_path: Path to file to analyze.

        Returns:
            Tuple of (status, detection_method).
        """
        # Try filename first (most reliable)
        status = self.detect_from_filename(file_path)
        if status:
            return (status, "filename")

        # Try metadata
        status = self.detect_from_metadata(file_path)
        if status:
            return (status, "metadata")

        # Try content
        status = self.detect_from_content(file_path)
        if status:
            return (status, "content")

        # Default to draft if configured
        default_status = self.config.get("organization", {}).get("default_status")
        if default_status:
            return (default_status, "default")

        return (None, "none")


class StatusOrganizer:
    """Organizes files by detected status."""

    def __init__(self, config: Dict) -> None:
        """Initialize StatusOrganizer.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.organize_config = config.get("organization", {})
        self.source_dir = Path(config.get("source_directory", "."))
        self.filter_config = config.get("filtering", {})

        # Setup destination directories
        self.status_dirs = {}
        for status in ["completed", "in_progress", "draft", "archived"]:
            dir_name = self.organize_config.get(
                f"{status}_directory", f"./{status.replace(' ', '_')}"
            )
            self.status_dirs[status] = Path(dir_name)

        # Setup logging
        self._setup_logging()

        # Initialize detector
        self.detector = StatusDetector(config)

    def _setup_logging(self) -> None:
        """Configure logging for the application."""
        log_level = self.config.get("logging", {}).get("level", "INFO")
        log_file = self.config.get("logging", {}).get("file", "logs/organizer.log")

        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.handlers.RotatingFileHandler(
                    log_file, maxBytes=10485760, backupCount=5
                ),
                logging.StreamHandler(sys.stdout),
            ],
        )

    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from processing.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file should be excluded, False otherwise.
        """
        exclude_patterns = self.filter_config.get("exclude_files", [])
        exclude_extensions = self.filter_config.get("exclude_extensions", [])

        file_name = file_path.name
        file_ext = file_path.suffix.lower()

        # Check exclude patterns
        for pattern in exclude_patterns:
            if pattern in file_name or file_name.startswith(pattern):
                return True

        # Check exclude extensions
        if file_ext in exclude_extensions:
            return True

        # Always exclude hidden files
        if file_name.startswith(".") and file_name not in [".gitkeep"]:
            return True

        return False

    def should_exclude_directory(self, dir_path: Path) -> bool:
        """Check if directory should be excluded from processing.

        Args:
            dir_path: Path to directory to check.

        Returns:
            True if directory should be excluded, False otherwise.
        """
        exclude_patterns = self.filter_config.get("exclude_directories", [])
        dir_name = dir_path.name

        for pattern in exclude_patterns:
            if pattern in dir_name or dir_name.startswith(pattern):
                return True

        # Always exclude common system directories and status directories
        system_dirs = {
            ".git",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            ".venv",
            "venv",
            "logs",
            "completed",
            "in_progress",
            "in_progress",
            "draft",
            "archived",
        }
        return dir_name in system_dirs

    def calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """Calculate MD5 hash of a file for duplicate detection.

        Args:
            file_path: Path to the file.

        Returns:
            MD5 hash string, or None if file cannot be read.
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (OSError, PermissionError) as e:
            logger.warning(
                f"Cannot calculate hash for {file_path}: {e}",
                extra={"file_path": str(file_path), "error": str(e)},
            )
            return None

    def get_destination_path(self, file_path: Path, status: str) -> Path:
        """Get destination path for a file based on status.

        Args:
            file_path: Original file path.
            status: Detected status.

        Returns:
            Destination path for the file.
        """
        # Normalize status name
        status_normalized = status.replace(" ", "_").lower()

        # Get destination directory
        if status_normalized in self.status_dirs:
            dest_dir = self.status_dirs[status_normalized]
        else:
            # Use status as directory name
            dest_dir = Path(f"./{status_normalized}")

        # Preserve structure if configured
        if self.organize_config.get("preserve_structure", False):
            try:
                relative_path = file_path.relative_to(self.source_dir)
                return dest_dir / relative_path
            except ValueError:
                # File is not under source_dir, use just filename
                return dest_dir / file_path.name
        else:
            return dest_dir / file_path.name

    def organize_file(
        self, file_path: Path, dry_run: bool = False
    ) -> Tuple[bool, Optional[str], str]:
        """Organize a file based on detected status.

        Args:
            file_path: Path to file to organize.
            dry_run: If True, only report what would be done.

        Returns:
            Tuple of (success, status, detection_method).
        """
        # Detect status
        status, method = self.detector.detect_status(file_path)

        if not status:
            return (False, None, method)

        # Get destination path
        dest_path = self.get_destination_path(file_path, status)

        # Skip if already in correct location
        if file_path.resolve() == dest_path.resolve():
            return (True, status, method)

        # Check for duplicates
        if self.organize_config.get("check_duplicates", True):
            file_hash = self.calculate_file_hash(file_path)
            if file_hash:
                hash_file = dest_path.parent / ".hashes.txt"
                existing_hashes = set()
                if hash_file.exists():
                    try:
                        with open(hash_file, "r") as f:
                            existing_hashes = set(line.strip() for line in f)
                    except (OSError, IOError):
                        pass

                if file_hash in existing_hashes:
                    logger.info(
                        f"Skipping duplicate: {file_path.name}",
                        extra={"file_path": str(file_path)},
                    )
                    return (False, status, method)

        # Handle filename conflicts
        if dest_path.exists() and not dry_run:
            if self.organize_config.get("skip_duplicates", True):
                logger.info(
                    f"Skipping existing file: {dest_path}",
                    extra={"source": str(file_path), "destination": str(dest_path)},
                )
                return (False, status, method)

            # Add timestamp to filename
            stem = dest_path.stem
            suffix = dest_path.suffix
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_path = dest_path.parent / f"{stem}_{timestamp}{suffix}"

        if dry_run:
            logger.info(
                f"[DRY RUN] Would move {file_path.name} to {status}/ "
                f"(detected via {method})",
                extra={
                    "source": str(file_path),
                    "destination": str(dest_path),
                    "status": status,
                    "method": method,
                },
            )
            return (True, status, method)

        try:
            # Create destination directory
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Move file
            shutil.move(str(file_path), str(dest_path))

            # Update hash file
            file_hash = self.calculate_file_hash(dest_path)
            if file_hash and self.organize_config.get("check_duplicates", True):
                hash_file = dest_path.parent / ".hashes.txt"
                with open(hash_file, "a") as f:
                    f.write(f"{file_hash}\n")

            logger.info(
                f"Moved {file_path.name} to {status}/ (detected via {method})",
                extra={
                    "source": str(file_path),
                    "destination": str(dest_path),
                    "status": status,
                    "method": method,
                },
            )
            return (True, status, method)

        except (OSError, PermissionError, shutil.Error) as e:
            logger.error(
                f"Failed to move file {file_path}: {e}",
                extra={"file_path": str(file_path), "error": str(e)},
            )
            return (False, status, method)

    def scan_files(self) -> List[Path]:
        """Scan source directory for files to organize.

        Returns:
            List of file paths.
        """
        files = []
        if not self.source_dir.exists():
            logger.error(f"Source directory does not exist: {self.source_dir}")
            return files

        try:
            for root, dirs, filenames in os.walk(self.source_dir):
                # Filter out excluded directories
                dirs[:] = [
                    d
                    for d in dirs
                    if not self.should_exclude_directory(Path(root) / d)
                ]

                for filename in filenames:
                    file_path = Path(root) / filename

                    if self.should_exclude_file(file_path):
                        continue

                    files.append(file_path)

        except (OSError, PermissionError) as e:
            logger.error(
                f"Cannot scan source directory {self.source_dir}: {e}",
                extra={"source_directory": str(self.source_dir), "error": str(e)},
            )

        return files

    def organize_files(self, dry_run: bool = False) -> Dict[str, int]:
        """Organize all files based on detected status.

        Args:
            dry_run: If True, only report what would be done.

        Returns:
            Dictionary with organization statistics.
        """
        results = {
            "scanned": 0,
            "completed": 0,
            "in_progress": 0,
            "draft": 0,
            "archived": 0,
            "unknown": 0,
            "duplicates": 0,
            "failed": 0,
            "detection_methods": defaultdict(int),
        }

        files = self.scan_files()
        results["scanned"] = len(files)

        logger.info(
            f"Found {len(files)} files to organize",
            extra={"file_count": len(files), "dry_run": dry_run},
        )

        for file_path in files:
            try:
                success, status, method = self.organize_file(file_path, dry_run=dry_run)

                if success and status:
                    results[status.replace(" ", "_")] += 1
                    results["detection_methods"][method] += 1
                elif status:
                    results["duplicates"] += 1
                else:
                    results["unknown"] += 1

            except Exception as e:
                logger.error(
                    f"Error organizing file {file_path}: {e}",
                    extra={"file_path": str(file_path), "error": str(e)},
                    exc_info=True,
                )
                results["failed"] += 1

        return results


def load_config(config_path: Path) -> Dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to configuration file.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        yaml.YAMLError: If config file is invalid YAML.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config or {}
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in config file: {e}") from e


def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Organize files by status indicators (completed, in-progress, "
        "draft, archived) based on naming conventions or metadata"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making changes",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(str(e))
        sys.exit(1)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    organizer = StatusOrganizer(config)

    if args.dry_run:
        logger.info("Running in dry-run mode - no files will be moved")

    results = organizer.organize_files(dry_run=args.dry_run)

    # Print summary
    print("\n" + "=" * 60)
    print("Status-Based Organization Summary")
    print("=" * 60)
    print(f"Files scanned: {results['scanned']}")
    print(f"Files organized as completed: {results['completed']}")
    print(f"Files organized as in_progress: {results['in_progress']}")
    print(f"Files organized as draft: {results['draft']}")
    print(f"Files organized as archived: {results['archived']}")
    print(f"Files with unknown status: {results['unknown']}")
    print(f"Duplicates skipped: {results['duplicates']}")
    print(f"Files failed: {results['failed']}")
    print("\nDetection Methods:")
    for method, count in results["detection_methods"].items():
        print(f"  {method}: {count}")
    print("=" * 60)

    if results["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
