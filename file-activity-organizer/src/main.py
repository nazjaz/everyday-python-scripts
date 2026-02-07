"""File Activity Organizer - CLI tool for organizing files by activity level.

This module provides a command-line tool for tracking file modification and
access frequencies, categorizing files as active, archived, or dormant, and
organizing them into appropriate directories.
"""

import argparse
import hashlib
import logging
import logging.handlers
import os
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FileActivityTracker:
    """Tracks file activity levels based on modification and access times."""

    def __init__(self, config: Dict) -> None:
        """Initialize FileActivityTracker.

        Args:
            config: Configuration dictionary containing activity settings.
        """
        self.config = config
        self.source_dir = Path(config.get("source_directory", "."))
        self.organize_config = config.get("organization", {})
        self.activity_config = config.get("activity_thresholds", {})
        self.filter_config = config.get("filtering", {})

        # Setup logging
        self._setup_logging()

        # Activity categories
        self.active_dir = Path(
            self.organize_config.get("active_directory", "./active")
        )
        self.archived_dir = Path(
            self.organize_config.get("archived_directory", "./archived")
        )
        self.dormant_dir = Path(
            self.organize_config.get("dormant_directory", "./dormant")
        )

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

    def get_file_statistics(self, file_path: Path) -> Optional[Dict]:
        """Get modification and access statistics for a file.

        Args:
            file_path: Path to the file.

        Returns:
            Dictionary with modification_time, access_time, and size, or None
            if file cannot be accessed.
        """
        try:
            stat = file_path.stat()
            return {
                "modification_time": datetime.fromtimestamp(stat.st_mtime),
                "access_time": datetime.fromtimestamp(stat.st_atime),
                "size": stat.st_size,
                "path": file_path,
            }
        except (OSError, PermissionError) as e:
            logger.warning(
                f"Cannot access file {file_path}: {e}",
                extra={"file_path": str(file_path), "error": str(e)},
            )
            return None

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

        # Always exclude hidden files and system files
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

        # Always exclude common system directories
        system_dirs = {
            ".git",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            ".venv",
            "venv",
        }
        return dir_name in system_dirs

    def categorize_file_activity(
        self, file_stats: Dict, now: datetime
    ) -> str:
        """Categorize file activity level based on thresholds.

        Args:
            file_stats: Dictionary with modification_time and access_time.
            now: Current datetime for comparison.

        Returns:
            Activity category: 'active', 'archived', or 'dormant'.
        """
        mod_time = file_stats["modification_time"]
        access_time = file_stats["access_time"]

        # Get thresholds from config
        active_days = self.activity_config.get("active_days", 30)
        archived_days = self.activity_config.get("archived_days", 90)
        dormant_days = self.activity_config.get("dormant_days", 365)

        # Calculate days since last modification and access
        days_since_mod = (now - mod_time).days
        days_since_access = (now - access_time).days

        # Use the more recent of modification or access time
        most_recent_days = min(days_since_mod, days_since_access)

        # Categorize based on most recent activity
        if most_recent_days <= active_days:
            return "active"
        elif most_recent_days <= archived_days:
            return "archived"
        elif most_recent_days <= dormant_days:
            return "dormant"
        else:
            # Very old files are also considered dormant
            return "dormant"

    def scan_files(self) -> List[Dict]:
        """Scan source directory for files to process.

        Returns:
            List of file statistics dictionaries.
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

                    stats = self.get_file_statistics(file_path)
                    if stats:
                        files.append(stats)

        except (OSError, PermissionError) as e:
            logger.error(
                f"Cannot scan source directory {self.source_dir}: {e}",
                extra={"source_directory": str(self.source_dir), "error": str(e)},
            )

        return files

    def detect_duplicates(self, files: List[Dict]) -> Dict[str, List[Dict]]:
        """Detect duplicate files by hash.

        Args:
            files: List of file statistics dictionaries.

        Returns:
            Dictionary mapping file hashes to lists of duplicate files.
        """
        hash_map: Dict[str, List[Dict]] = defaultdict(list)
        duplicates: Dict[str, List[Dict]] = {}

        logger.info("Calculating file hashes for duplicate detection...")

        for file_stats in files:
            file_path = file_stats["path"]
            file_hash = self.calculate_file_hash(file_path)

            if file_hash:
                hash_map[file_hash].append(file_stats)

        # Filter to only include hashes with multiple files
        for file_hash, file_list in hash_map.items():
            if len(file_list) > 1:
                duplicates[file_hash] = file_list

        return duplicates

    def get_destination_path(
        self, file_path: Path, category: str
    ) -> Path:
        """Get destination path for a file based on category.

        Args:
            file_path: Original file path.
            category: Activity category ('active', 'archived', or 'dormant').

        Returns:
            Destination path for the file.
        """
        if category == "active":
            dest_dir = self.active_dir
        elif category == "archived":
            dest_dir = self.archived_dir
        else:  # dormant
            dest_dir = self.dormant_dir

        # Preserve relative path structure if configured
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
        self, file_stats: Dict, category: str, dry_run: bool = False
    ) -> bool:
        """Organize a file into its activity category directory.

        Args:
            file_stats: File statistics dictionary.
            category: Activity category.
            dry_run: If True, only report what would be done.

        Returns:
            True if organization succeeded, False otherwise.
        """
        file_path = file_stats["path"]
        dest_path = self.get_destination_path(file_path, category)

        # Skip if already in correct location
        if file_path.resolve() == dest_path.resolve():
            return True

        # Create destination directory
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Handle file name conflicts
        if dest_path.exists() and not dry_run:
            if self.organize_config.get("skip_duplicates", True):
                logger.info(
                    f"Skipping duplicate destination: {dest_path}",
                    extra={"source": str(file_path), "destination": str(dest_path)},
                )
                return True

            # Add timestamp to filename
            stem = dest_path.stem
            suffix = dest_path.suffix
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_path = dest_path.parent / f"{stem}_{timestamp}{suffix}"

        if dry_run:
            logger.info(
                f"[DRY RUN] Would move {file_path.name} to {category}/"
                f"{dest_path.name}",
                extra={
                    "source": str(file_path),
                    "destination": str(dest_path),
                    "category": category,
                },
            )
            return True

        try:
            shutil.move(str(file_path), str(dest_path))
            logger.info(
                f"Moved {file_path.name} to {category}/",
                extra={
                    "source": str(file_path),
                    "destination": str(dest_path),
                    "category": category,
                },
            )
            return True

        except (OSError, PermissionError, shutil.Error) as e:
            logger.error(
                f"Failed to move file {file_path}: {e}",
                extra={"file_path": str(file_path), "error": str(e)},
            )
            return False

    def process_files(
        self, dry_run: bool = False, detect_dups: bool = True
    ) -> Dict[str, int]:
        """Process all files and organize by activity level.

        Args:
            dry_run: If True, only report what would be done.
            detect_dups: If True, detect and report duplicate files.

        Returns:
            Dictionary with counts of processed files.
        """
        results = {
            "scanned": 0,
            "active": 0,
            "archived": 0,
            "dormant": 0,
            "duplicates": 0,
            "failed": 0,
        }

        # Scan files
        files = self.scan_files()
        results["scanned"] = len(files)

        logger.info(
            f"Found {len(files)} files to process",
            extra={"file_count": len(files), "dry_run": dry_run},
        )

        # Detect duplicates if requested
        if detect_dups:
            duplicates = self.detect_duplicates(files)
            results["duplicates"] = len(duplicates)

            if duplicates:
                logger.warning(
                    f"Found {len(duplicates)} groups of duplicate files",
                    extra={"duplicate_groups": len(duplicates)},
                )
                for file_hash, dup_files in list(duplicates.items())[:5]:
                    logger.debug(
                        f"Duplicate group (hash: {file_hash[:8]}...): "
                        f"{len(dup_files)} files"
                    )

        # Categorize and organize files
        now = datetime.now()
        category_counts = defaultdict(int)

        for file_stats in files:
            try:
                category = self.categorize_file_activity(file_stats, now)
                category_counts[category] += 1

                if self.organize_file(file_stats, category, dry_run):
                    results[category] += 1
                else:
                    results["failed"] += 1

            except Exception as e:
                logger.error(
                    f"Error processing file {file_stats['path']}: {e}",
                    extra={
                        "file_path": str(file_stats["path"]),
                        "error": str(e),
                    },
                    exc_info=True,
                )
                results["failed"] += 1

        logger.info(
            "File categorization complete",
            extra={
                "active": category_counts["active"],
                "archived": category_counts["archived"],
                "dormant": category_counts["dormant"],
            },
        )

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
        description="Organize files by activity level based on modification "
        "and access frequencies"
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
    parser.add_argument(
        "--no-duplicates",
        action="store_true",
        help="Skip duplicate detection",
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

    tracker = FileActivityTracker(config)

    if args.dry_run:
        logger.info("Running in dry-run mode - no changes will be made")

    results = tracker.process_files(
        dry_run=args.dry_run, detect_dups=not args.no_duplicates
    )

    # Print summary
    print("\n" + "=" * 60)
    print("File Activity Organization Summary")
    print("=" * 60)
    print(f"Files scanned: {results['scanned']}")
    print(f"Files categorized as active: {results['active']}")
    print(f"Files categorized as archived: {results['archived']}")
    print(f"Files categorized as dormant: {results['dormant']}")
    print(f"Duplicate groups found: {results['duplicates']}")
    print(f"Files failed to process: {results['failed']}")
    print("=" * 60)

    if results["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
