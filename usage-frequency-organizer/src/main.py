"""Usage Frequency Organizer - CLI tool for organizing files by usage frequency.

This module provides a command-line tool for organizing files based on usage
frequency, creating folders for frequently accessed files, occasionally used
files, and rarely accessed archives.
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


class UsageFrequencyAnalyzer:
    """Analyzes file usage frequency based on access times."""

    def __init__(self, config: Dict) -> None:
        """Initialize UsageFrequencyAnalyzer.

        Args:
            config: Configuration dictionary containing analysis settings.
        """
        self.config = config
        self.frequency_config = config.get("frequency_thresholds", {})
        self.analysis_config = config.get("analysis", {})

    def get_file_access_times(self, file_path: Path) -> Optional[Dict]:
        """Get access time information for a file.

        Args:
            file_path: Path to file to analyze.

        Returns:
            Dictionary with access time information, or None if inaccessible.
        """
        try:
            stat = file_path.stat()
            return {
                "access_time": datetime.fromtimestamp(stat.st_atime),
                "modification_time": datetime.fromtimestamp(stat.st_mtime),
                "creation_time": datetime.fromtimestamp(stat.st_ctime),
                "size": stat.st_size,
            }
        except (OSError, PermissionError) as e:
            logger.warning(
                f"Cannot access file {file_path}: {e}",
                extra={"file_path": str(file_path), "error": str(e)},
            )
            return None

    def calculate_access_frequency(
        self, file_path: Path, access_info: Dict, now: datetime
    ) -> Tuple[str, float]:
        """Calculate access frequency category and score.

        Args:
            file_path: Path to file.
            access_info: Dictionary with access time information.
            now: Current datetime for comparison.

        Returns:
            Tuple of (category, frequency_score).
        """
        access_time = access_info["access_time"]
        mod_time = access_info["modification_time"]

        # Use the more recent of access or modification time
        most_recent = max(access_time, mod_time)
        days_since_access = (now - most_recent).days

        # Get thresholds from config
        frequent_days = self.frequency_config.get("frequent_days", 7)
        occasional_days = self.frequency_config.get("occasional_days", 30)
        rare_days = self.frequency_config.get("rare_days", 90)

        # Calculate frequency score (0.0 to 1.0, higher = more frequent)
        if days_since_access <= frequent_days:
            category = "frequent"
            # Score decreases as days increase
            frequency_score = 1.0 - (days_since_access / frequent_days) * 0.3
        elif days_since_access <= occasional_days:
            category = "occasional"
            # Score between 0.4 and 0.7
            days_in_range = days_since_access - frequent_days
            range_size = occasional_days - frequent_days
            frequency_score = 0.7 - (days_in_range / range_size) * 0.3
        elif days_since_access <= rare_days:
            category = "rare"
            # Score between 0.1 and 0.4
            days_in_range = days_since_access - occasional_days
            range_size = rare_days - occasional_days
            frequency_score = 0.4 - (days_in_range / range_size) * 0.3
        else:
            category = "archive"
            # Score below 0.1
            frequency_score = max(0.0, 0.1 - (days_since_access - rare_days) / 365.0)

        return (category, frequency_score)

    def analyze_file_usage(self, file_path: Path, now: datetime) -> Optional[Dict]:
        """Analyze file usage and return categorization.

        Args:
            file_path: Path to file to analyze.
            now: Current datetime for comparison.

        Returns:
            Dictionary with usage analysis, or None if file cannot be accessed.
        """
        access_info = self.get_file_access_times(file_path)
        if not access_info:
            return None

        category, frequency_score = self.calculate_access_frequency(
            file_path, access_info, now
        )

        return {
            "path": file_path,
            "category": category,
            "frequency_score": frequency_score,
            "days_since_access": (now - access_info["access_time"]).days,
            "access_time": access_info["access_time"],
            "size": access_info["size"],
        }


class UsageFrequencyOrganizer:
    """Organizes files by usage frequency."""

    def __init__(self, config: Dict) -> None:
        """Initialize UsageFrequencyOrganizer.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.organize_config = config.get("organization", {})
        self.source_dir = Path(config.get("source_directory", "."))
        self.filter_config = config.get("filtering", {})

        # Setup destination directories
        self.frequent_dir = Path(
            self.organize_config.get("frequent_directory", "./frequent")
        )
        self.occasional_dir = Path(
            self.organize_config.get("occasional_directory", "./occasional")
        )
        self.rare_dir = Path(
            self.organize_config.get("rare_directory", "./rare")
        )
        self.archive_dir = Path(
            self.organize_config.get("archive_directory", "./archive")
        )

        # Setup logging
        self._setup_logging()

        # Initialize analyzer
        self.analyzer = UsageFrequencyAnalyzer(config)

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

        # Always exclude common system directories
        system_dirs = {
            ".git",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            ".venv",
            "venv",
            "logs",
            "frequent",
            "occasional",
            "rare",
            "archive",
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

    def get_destination_path(self, file_path: Path, category: str) -> Path:
        """Get destination path for a file based on usage category.

        Args:
            file_path: Original file path.
            category: Usage frequency category.

        Returns:
            Destination path for the file.
        """
        if category == "frequent":
            dest_dir = self.frequent_dir
        elif category == "occasional":
            dest_dir = self.occasional_dir
        elif category == "rare":
            dest_dir = self.rare_dir
        else:  # archive
            dest_dir = self.archive_dir

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
        self, usage_info: Dict, dry_run: bool = False
    ) -> Tuple[bool, str]:
        """Organize a file based on usage frequency.

        Args:
            usage_info: Dictionary with usage analysis information.
            dry_run: If True, only report what would be done.

        Returns:
            Tuple of (success, category).
        """
        file_path = usage_info["path"]
        category = usage_info["category"]

        # Get destination path
        dest_path = self.get_destination_path(file_path, category)

        # Skip if already in correct location
        if file_path.resolve() == dest_path.resolve():
            return (True, category)

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
                    return (False, category)

        # Handle filename conflicts
        if dest_path.exists() and not dry_run:
            if self.organize_config.get("skip_duplicates", True):
                logger.info(
                    f"Skipping existing file: {dest_path}",
                    extra={"source": str(file_path), "destination": str(dest_path)},
                )
                return (False, category)

            # Add timestamp to filename
            stem = dest_path.stem
            suffix = dest_path.suffix
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_path = dest_path.parent / f"{stem}_{timestamp}{suffix}"

        if dry_run:
            logger.info(
                f"[DRY RUN] Would move {file_path.name} to {category}/ "
                f"(days since access: {usage_info['days_since_access']})",
                extra={
                    "source": str(file_path),
                    "destination": str(dest_path),
                    "category": category,
                    "days_since_access": usage_info["days_since_access"],
                },
            )
            return (True, category)

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
                f"Moved {file_path.name} to {category}/ "
                f"(days since access: {usage_info['days_since_access']})",
                extra={
                    "source": str(file_path),
                    "destination": str(dest_path),
                    "category": category,
                    "days_since_access": usage_info["days_since_access"],
                },
            )
            return (True, category)

        except (OSError, PermissionError, shutil.Error) as e:
            logger.error(
                f"Failed to move file {file_path}: {e}",
                extra={"file_path": str(file_path), "error": str(e)},
            )
            return (False, category)

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
        """Organize all files based on usage frequency.

        Args:
            dry_run: If True, only report what would be done.

        Returns:
            Dictionary with organization statistics.
        """
        results = {
            "scanned": 0,
            "frequent": 0,
            "occasional": 0,
            "rare": 0,
            "archive": 0,
            "duplicates": 0,
            "failed": 0,
        }

        files = self.scan_files()
        results["scanned"] = len(files)

        logger.info(
            f"Found {len(files)} files to organize",
            extra={"file_count": len(files), "dry_run": dry_run},
        )

        now = datetime.now()

        for file_path in files:
            try:
                usage_info = self.analyzer.analyze_file_usage(file_path, now)

                if not usage_info:
                    results["failed"] += 1
                    continue

                success, category = self.organize_file(usage_info, dry_run=dry_run)

                if success:
                    results[category] += 1
                else:
                    results["duplicates"] += 1

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
        description="Organize files by usage frequency into frequent, occasional, "
        "rare, and archive categories"
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

    organizer = UsageFrequencyOrganizer(config)

    if args.dry_run:
        logger.info("Running in dry-run mode - no files will be moved")

    results = organizer.organize_files(dry_run=args.dry_run)

    # Print summary
    print("\n" + "=" * 60)
    print("Usage Frequency Organization Summary")
    print("=" * 60)
    print(f"Files scanned: {results['scanned']}")
    print(f"Files organized as frequent: {results['frequent']}")
    print(f"Files organized as occasional: {results['occasional']}")
    print(f"Files organized as rare: {results['rare']}")
    print(f"Files organized as archive: {results['archive']}")
    print(f"Duplicates skipped: {results['duplicates']}")
    print(f"Files failed: {results['failed']}")
    print("=" * 60)

    if results["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
