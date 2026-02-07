"""Temp Cleaner - Clean up temporary files older than specified age.

This module provides functionality to clean up temporary files from system
temp directories that are older than a specified number of days. Includes
exclusions for active processes, configurable patterns, and comprehensive
logging with dry-run mode.
"""

import logging
import logging.handlers
import os
import platform
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Set

import psutil
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class TempCleaner:
    """Cleans up temporary files older than specified age."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize TempCleaner with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_directories()
        self.stats = {
            "files_scanned": 0,
            "files_deleted": 0,
            "files_skipped_in_use": 0,
            "files_skipped_excluded": 0,
            "errors": 0,
            "errors_list": [],
            "space_freed": 0,
        }
        self.active_file_handles: Set[str] = self._get_active_file_handles()

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
        if os.getenv("MIN_AGE_DAYS"):
            config["min_age_days"] = int(os.getenv("MIN_AGE_DAYS"))
        if os.getenv("DRY_RUN"):
            config["operations"]["dry_run"] = (
                os.getenv("DRY_RUN").lower() == "true"
            )

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/temp_cleaner.log")

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
        """Set up temporary directories to clean."""
        temp_dirs = self.config.get("temp_directories", [])

        if not temp_dirs:
            # Use system default temp directories
            system = platform.system()
            if system == "Windows":
                default_dirs = [
                    os.getenv("TEMP", ""),
                    os.getenv("TMP", ""),
                    os.path.join(os.getenv("LOCALAPPDATA", ""), "Temp"),
                ]
            elif system == "Darwin":  # macOS
                default_dirs = [
                    os.getenv("TMPDIR", "/tmp"),
                    os.path.expanduser("~/Library/Caches"),
                ]
            else:  # Linux and others
                default_dirs = [
                    "/tmp",
                    "/var/tmp",
                    os.getenv("TMPDIR", "/tmp"),
                ]

            temp_dirs = [d for d in default_dirs if d and os.path.exists(d)]

        self.temp_directories = [
            Path(os.path.expanduser(d)) for d in temp_dirs if d
        ]

        # Filter to only existing directories
        self.temp_directories = [
            d for d in self.temp_directories if d.exists() and d.is_dir()
        ]

        logger.info(f"Temp directories to clean: {len(self.temp_directories)}")
        for temp_dir in self.temp_directories:
            logger.info(f"  - {temp_dir}")

    def _get_active_file_handles(self) -> Set[str]:
        """Get set of file paths currently open by processes.

        Returns:
            Set of absolute file paths.
        """
        active_files = set()

        try:
            for proc in psutil.process_iter(["pid", "name", "open_files"]):
                try:
                    if proc.info["open_files"]:
                        for file_info in proc.info["open_files"]:
                            if file_info.path:
                                active_files.add(
                                    os.path.abspath(file_info.path)
                                )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.warning(f"Error getting active file handles: {e}")

        logger.debug(f"Found {len(active_files)} active file handles")
        return active_files

    def _is_file_in_use(self, file_path: Path) -> bool:
        """Check if file is currently in use by a process.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file is in use, False otherwise.
        """
        abs_path = str(file_path.resolve())

        # Check against cached active file handles
        if abs_path in self.active_file_handles:
            return True

        # Try to open file in exclusive mode as additional check
        try:
            with open(file_path, "r+b"):
                pass
            return False
        except (IOError, PermissionError):
            return True

    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from cleanup.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file should be excluded, False otherwise.
        """
        exclusions = self.config.get("exclusions", {})
        file_name = file_path.name
        file_str = str(file_path)

        # Check excluded directories
        excluded_dirs = exclusions.get("directories", [])
        for excluded_dir in excluded_dirs:
            excluded_path = Path(os.path.expanduser(excluded_dir))
            try:
                if file_path.is_relative_to(excluded_path):
                    return True
            except (ValueError, AttributeError):
                # Python < 3.9 compatibility
                if str(file_path).startswith(str(excluded_path)):
                    return True

        # Check excluded patterns
        excluded_patterns = exclusions.get("patterns", [])
        for pattern in excluded_patterns:
            if pattern in file_name or pattern in file_str:
                return True

        # Check excluded extensions
        excluded_extensions = exclusions.get("extensions", [])
        if file_path.suffix.lower() in [
            ext.lower() for ext in excluded_extensions
        ]:
            return True

        # Check excluded process names
        excluded_processes = exclusions.get("processes", [])
        if excluded_processes:
            try:
                for proc in psutil.process_iter(["name"]):
                    try:
                        proc_name = proc.info["name"].lower()
                        for excluded_proc in excluded_processes:
                            if excluded_proc.lower() in proc_name:
                                # Check if this process has file open
                                if self._is_file_in_use(file_path):
                                    return True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except Exception as e:
                logger.debug(f"Error checking excluded processes: {e}")

        return False

    def _is_file_old_enough(self, file_path: Path) -> bool:
        """Check if file is older than minimum age.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file is old enough, False otherwise.
        """
        try:
            file_stat = file_path.stat()
            file_age_seconds = time.time() - file_stat.st_mtime
            min_age_seconds = self.config.get("min_age_days", 7) * 24 * 60 * 60

            return file_age_seconds >= min_age_seconds
        except (OSError, AttributeError) as e:
            logger.debug(f"Error checking file age for {file_path}: {e}")
            return False

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: File size in bytes.

        Returns:
            Formatted size string (e.g., "1.5 MB").
        """
        if size_bytes == 0:
            return "0 B"

        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def _delete_file(self, file_path: Path) -> bool:
        """Delete a file or directory.

        Args:
            file_path: Path to file or directory to delete.

        Returns:
            True if successful, False otherwise.
        """
        try:
            if self.config["operations"]["dry_run"]:
                size = file_path.stat().st_size if file_path.is_file() else 0
                if file_path.is_dir():
                    logger.info(f"[DRY RUN] Would delete directory: {file_path}")
                else:
                    logger.info(
                        f"[DRY RUN] Would delete file: {file_path} "
                        f"({self._format_size(size)})"
                    )
                return True

            if file_path.is_file():
                size = file_path.stat().st_size
                file_path.unlink()
                self.stats["space_freed"] += size
                logger.info(
                    f"Deleted file: {file_path} ({self._format_size(size)})"
                )
                return True
            elif file_path.is_dir():
                shutil.rmtree(file_path)
                logger.info(f"Deleted directory: {file_path}")
                return True

        except (OSError, PermissionError, shutil.Error) as e:
            error_msg = f"Error deleting {file_path}: {e}"
            logger.error(error_msg)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            return False

        return False

    def _clean_directory(self, directory: Path) -> None:
        """Clean temporary files in a directory.

        Args:
            directory: Directory to clean.
        """
        if not directory.exists() or not directory.is_dir():
            return

        logger.info(f"Cleaning directory: {directory}")

        try:
            for item in directory.iterdir():
                self.stats["files_scanned"] += 1

                # Check if should be excluded
                if self._should_exclude_file(item):
                    self.stats["files_skipped_excluded"] += 1
                    logger.debug(f"Excluded: {item}")
                    continue

                # Check if file is in use
                if self._is_file_in_use(item):
                    self.stats["files_skipped_in_use"] += 1
                    logger.debug(f"In use, skipping: {item}")
                    continue

                # Check if old enough
                if not self._is_file_old_enough(item):
                    logger.debug(f"Too new, skipping: {item}")
                    continue

                # Delete file or directory
                if self._delete_file(item):
                    self.stats["files_deleted"] += 1

        except (PermissionError, OSError) as e:
            error_msg = f"Error accessing directory {directory}: {e}"
            logger.warning(error_msg)
            self.stats["errors"] += 1
            if error_msg not in self.stats["errors_list"]:
                self.stats["errors_list"].append(error_msg)

    def clean_temp_files(self) -> Dict[str, any]:
        """Clean temporary files from all configured directories.

        Returns:
            Dictionary with statistics about the operation.
        """
        logger.info("Starting temporary file cleanup")
        logger.info(
            f"Min age: {self.config.get('min_age_days', 7)} days"
        )
        logger.info(f"Dry run mode: {self.config['operations']['dry_run']}")

        # Refresh active file handles
        self.active_file_handles = self._get_active_file_handles()

        for temp_dir in self.temp_directories:
            self._clean_directory(temp_dir)

        logger.info("Temporary file cleanup completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats


def main() -> int:
    """Main entry point for temp cleaner."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Clean up temporary files older than specified age "
        "from system temp directories"
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
        help="Preview changes without deleting files",
    )
    parser.add_argument(
        "--min-age",
        type=int,
        help="Minimum age in days (overrides config)",
    )

    args = parser.parse_args()

    try:
        cleaner = TempCleaner(config_path=args.config)

        if args.dry_run:
            cleaner.config["operations"]["dry_run"] = True

        if args.min_age:
            cleaner.config["min_age_days"] = args.min_age

        stats = cleaner.clean_temp_files()

        # Print summary
        print("\n" + "=" * 60)
        print("Temporary File Cleanup Summary")
        print("=" * 60)
        print(f"Files Scanned: {stats['files_scanned']}")
        print(f"Files Deleted: {stats['files_deleted']}")
        print(f"Files Skipped (In Use): {stats['files_skipped_in_use']}")
        print(f"Files Skipped (Excluded): {stats['files_skipped_excluded']}")
        print(f"Space Freed: {cleaner._format_size(stats['space_freed'])}")
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
