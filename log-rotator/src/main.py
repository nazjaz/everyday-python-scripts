"""Log Rotator - Rotate and archive old log files.

This module provides functionality to rotate and archive old log files,
keeping a specified number of recent logs and compressing older ones
with date stamps.
"""

import gzip
import logging
import logging.handlers
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class LogRotator:
    """Rotates and archives old log files."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize LogRotator with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.stats = {
            "files_processed": 0,
            "files_kept": 0,
            "files_archived": 0,
            "files_compressed": 0,
            "files_deleted": 0,
            "errors": 0,
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
        if os.getenv("LOG_DIRECTORY"):
            config["rotation"]["log_directory"] = os.getenv("LOG_DIRECTORY")
        if os.getenv("ARCHIVE_DIRECTORY"):
            config["rotation"]["archive_directory"] = os.getenv("ARCHIVE_DIRECTORY")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/log_rotator.log")

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

    def _get_log_files(
        self, log_directory: Path, patterns: List[str]
    ) -> List[Tuple[Path, float]]:
        """Get log files matching patterns with modification times.

        Args:
            log_directory: Directory to search for log files.
            patterns: List of file patterns to match (e.g., ["*.log", "*.txt"]).

        Returns:
            List of tuples (file_path, modification_time).
        """
        log_files = []

        if not log_directory.exists():
            logger.warning(f"Log directory does not exist: {log_directory}")
            return log_files

        if not log_directory.is_dir():
            logger.warning(f"Log path is not a directory: {log_directory}")
            return log_files

        # Collect files matching patterns
        for pattern in patterns:
            for file_path in log_directory.glob(pattern):
                if file_path.is_file():
                    try:
                        mtime = file_path.stat().st_mtime
                        log_files.append((file_path, mtime))
                    except OSError as e:
                        logger.warning(f"Could not get file info for {file_path}: {e}")
                        self.stats["errors"] += 1

        # Sort by modification time (newest first)
        log_files.sort(key=lambda x: x[1], reverse=True)

        logger.debug(f"Found {len(log_files)} log file(s) matching patterns")
        return log_files

    def _add_date_stamp(self, file_path: Path, date_format: str = "%Y%m%d") -> Path:
        """Add date stamp to filename.

        Args:
            file_path: Path to file.
            date_format: Date format string.

        Returns:
            New path with date stamp added.
        """
        file_stem = file_path.stem
        file_suffix = file_path.suffix
        date_str = datetime.now().strftime(date_format)
        new_name = f"{file_stem}_{date_str}{file_suffix}"
        return file_path.parent / new_name

    def _compress_file(self, source_path: Path, dest_path: Optional[Path] = None) -> Path:
        """Compress file using gzip.

        Args:
            source_path: Path to file to compress.
            dest_path: Destination path (default: source_path + .gz).

        Returns:
            Path to compressed file.

        Raises:
            OSError: If compression fails.
        """
        if dest_path is None:
            dest_path = Path(f"{source_path}.gz")

        try:
            with open(source_path, "rb") as f_in:
                with gzip.open(dest_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            logger.debug(f"Compressed: {source_path} -> {dest_path}")
            return dest_path

        except (OSError, IOError) as e:
            logger.error(f"Error compressing {source_path}: {e}")
            self.stats["errors"] += 1
            raise

    def _archive_file(
        self,
        file_path: Path,
        archive_directory: Path,
        compress: bool = True,
        add_date_stamp: bool = True,
    ) -> Optional[Path]:
        """Archive a log file.

        Args:
            file_path: Path to log file to archive.
            archive_directory: Directory to move archived file to.
            compress: Whether to compress the archived file.
            add_date_stamp: Whether to add date stamp to filename.

        Returns:
            Path to archived file or None if archiving failed.
        """
        try:
            # Create archive directory if it doesn't exist
            archive_directory.mkdir(parents=True, exist_ok=True)

            # Determine destination filename
            if add_date_stamp:
                date_format = self.config.get("rotation", {}).get("date_format", "%Y%m%d")
                dest_name = self._add_date_stamp(file_path, date_format).name
            else:
                dest_name = file_path.name

            dest_path = archive_directory / dest_name

            # Handle duplicate names
            if dest_path.exists():
                counter = 1
                base_name = dest_path.stem
                extension = dest_path.suffix
                while dest_path.exists():
                    dest_path = archive_directory / f"{base_name}_{counter}{extension}"
                    counter += 1
                logger.debug(f"Renamed to avoid overwrite: {dest_path}")

            # Copy file to archive directory
            shutil.copy2(file_path, dest_path)

            # Compress if requested
            if compress:
                compressed_path = self._compress_file(dest_path)
                # Remove uncompressed file
                dest_path.unlink()
                dest_path = compressed_path
                self.stats["files_compressed"] += 1

            # Remove original file
            file_path.unlink()

            self.stats["files_archived"] += 1
            logger.info(f"Archived: {file_path} -> {dest_path}")

            return dest_path

        except (OSError, IOError, shutil.Error) as e:
            logger.error(f"Error archiving {file_path}: {e}")
            self.stats["errors"] += 1
            return None

    def _delete_old_files(
        self, archive_directory: Path, max_age_days: int
    ) -> int:
        """Delete files older than specified days from archive.

        Args:
            archive_directory: Directory containing archived files.
            max_age_days: Maximum age in days before deletion.

        Returns:
            Number of files deleted.
        """
        if not archive_directory.exists():
            return 0

        deleted_count = 0
        cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)

        try:
            for file_path in archive_directory.iterdir():
                if not file_path.is_file():
                    continue

                try:
                    mtime = file_path.stat().st_mtime
                    if mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
                        self.stats["files_deleted"] += 1
                        logger.info(f"Deleted old archive: {file_path}")
                except OSError as e:
                    logger.warning(f"Could not delete {file_path}: {e}")
                    self.stats["errors"] += 1

        except OSError as e:
            logger.error(f"Error scanning archive directory: {e}")
            self.stats["errors"] += 1

        return deleted_count

    def rotate_logs(
        self,
        log_directory: Optional[str] = None,
        archive_directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Rotate log files: keep recent, archive old.

        Args:
            log_directory: Directory containing log files (overrides config).
            archive_directory: Directory for archived logs (overrides config).

        Returns:
            Dictionary with rotation statistics.

        Raises:
            ValueError: If configuration is invalid.
        """
        rotation_config = self.config.get("rotation", {})

        # Determine directories
        if log_directory:
            log_dir = Path(log_directory)
        else:
            log_dir = Path(rotation_config.get("log_directory", "."))

        if archive_directory:
            archive_dir = Path(archive_directory)
        else:
            archive_dir = Path(rotation_config.get("archive_directory", "archive"))

        if not log_dir.exists():
            raise FileNotFoundError(f"Log directory does not exist: {log_dir}")

        logger.info(f"Starting log rotation: {log_dir} -> {archive_dir}")

        # Reset stats
        self.stats = {
            "files_processed": 0,
            "files_kept": 0,
            "files_archived": 0,
            "files_compressed": 0,
            "files_deleted": 0,
            "errors": 0,
        }

        # Get log file patterns
        patterns = rotation_config.get("patterns", ["*.log"])
        keep_count = rotation_config.get("keep_count", 5)
        compress = rotation_config.get("compress", True)
        add_date_stamp = rotation_config.get("add_date_stamp", True)

        # Get all log files
        log_files = self._get_log_files(log_dir, patterns)

        if not log_files:
            logger.info("No log files found to rotate")
            return self.stats

        self.stats["files_processed"] = len(log_files)

        # Keep the N most recent files
        files_to_keep = log_files[:keep_count]
        files_to_archive = log_files[keep_count:]

        # Keep recent files
        for file_path, _ in files_to_keep:
            self.stats["files_kept"] += 1
            logger.debug(f"Keeping: {file_path}")

        # Archive old files
        for file_path, _ in files_to_archive:
            archived_path = self._archive_file(
                file_path, archive_dir, compress=compress, add_date_stamp=add_date_stamp
            )
            if archived_path:
                logger.debug(f"Archived: {file_path} -> {archived_path}")

        # Delete very old archived files if configured
        max_age_days = rotation_config.get("max_age_days")
        if max_age_days and max_age_days > 0:
            deleted = self._delete_old_files(archive_dir, max_age_days)
            logger.info(f"Deleted {deleted} old archived file(s)")

        logger.info(
            f"Rotation complete: {self.stats['files_kept']} kept, "
            f"{self.stats['files_archived']} archived, "
            f"{self.stats['files_compressed']} compressed"
        )

        return self.stats

    def get_statistics(self) -> Dict[str, Any]:
        """Get rotation statistics.

        Returns:
            Dictionary with statistics.
        """
        return self.stats.copy()


def main() -> int:
    """Main entry point for log rotator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Rotate and archive old log files"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-d",
        "--directory",
        help="Log directory to rotate (overrides config)",
    )
    parser.add_argument(
        "-a",
        "--archive",
        help="Archive directory (overrides config)",
    )
    parser.add_argument(
        "-k",
        "--keep",
        type=int,
        help="Number of recent logs to keep (overrides config)",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        action="append",
        help="File pattern to match (e.g., *.log). Can be specified multiple times.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually rotating",
    )

    args = parser.parse_args()

    try:
        rotator = LogRotator(config_path=args.config)

        # Override config with command line arguments
        if args.keep:
            rotator.config["rotation"]["keep_count"] = args.keep
        if args.pattern:
            rotator.config["rotation"]["patterns"] = args.pattern

        if args.dry_run:
            print("DRY RUN MODE - No files will be modified")
            print("=" * 60)

            log_dir = Path(args.directory or rotator.config["rotation"]["log_directory"])
            patterns = rotator.config["rotation"]["patterns"]
            keep_count = rotator.config["rotation"]["keep_count"]

            log_files = rotator._get_log_files(log_dir, patterns)
            files_to_keep = log_files[:keep_count]
            files_to_archive = log_files[keep_count:]

            print(f"\nFound {len(log_files)} log file(s)")
            print(f"Would keep {len(files_to_keep)} most recent:")
            for file_path, mtime in files_to_keep:
                mod_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                print(f"  {file_path.name} (modified: {mod_time})")

            print(f"\nWould archive {len(files_to_archive)} file(s):")
            for file_path, mtime in files_to_archive:
                mod_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                print(f"  {file_path.name} (modified: {mod_time})")

            return 0

        # Perform rotation
        stats = rotator.rotate_logs(
            log_directory=args.directory, archive_directory=args.archive
        )

        # Print summary
        print("\n" + "=" * 60)
        print("Log Rotation Summary")
        print("=" * 60)
        print(f"Files processed: {stats['files_processed']}")
        print(f"Files kept: {stats['files_kept']}")
        print(f"Files archived: {stats['files_archived']}")
        print(f"Files compressed: {stats['files_compressed']}")
        print(f"Files deleted: {stats['files_deleted']}")
        print(f"Errors: {stats['errors']}")

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
