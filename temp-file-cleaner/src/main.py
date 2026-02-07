"""Temporary File Cleaner - Clean up temporary download files safely.

This module provides functionality to identify and clean up temporary download
files, incomplete downloads, and files with temporary extensions, with
comprehensive safety checks to prevent accidental deletion of important files.
"""

import logging
import logging.handlers
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class TemporaryFileCleaner:
    """Cleans up temporary files with safety checks."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize TemporaryFileCleaner with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.temp_files: List[Dict[str, Any]] = []
        self.stats = {
            "files_scanned": 0,
            "temp_files_found": 0,
            "files_deleted": 0,
            "space_freed_bytes": 0,
            "errors": 0,
        }

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Dictionary containing configuration settings.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            if not config:
                raise ValueError("Configuration file is empty")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in configuration file: {e}")
            raise

    def _setup_logging(self) -> None:
        """Configure logging based on configuration settings."""
        log_level = self.config.get("logging", {}).get("level", "INFO")
        log_file = self.config.get("logging", {}).get("file", "logs/app.log")
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(message)s"
        )

        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format,
            handlers=[
                logging.handlers.RotatingFileHandler(
                    log_file, maxBytes=10485760, backupCount=5
                ),
                logging.StreamHandler(),
            ],
        )

    def _should_skip_path(self, path: Path) -> bool:
        """Check if a path should be skipped during scanning.

        Args:
            path: Path to check.

        Returns:
            True if path should be skipped, False otherwise.
        """
        skip_patterns = self.config.get("scan", {}).get(
            "skip_patterns", []
        )
        path_str = str(path)

        for pattern in skip_patterns:
            if pattern in path_str:
                return True

        return False

    def _is_temporary_extension(self, file_path: Path) -> bool:
        """Check if file has a temporary extension.

        Args:
            file_path: Path to file.

        Returns:
            True if file has temporary extension, False otherwise.
        """
        temp_extensions = self.config.get("cleanup", {}).get(
            "temp_extensions", []
        )
        extension = file_path.suffix.lower()

        return extension in [ext.lower() for ext in temp_extensions]

    def _is_temporary_filename(self, file_path: Path) -> bool:
        """Check if filename indicates temporary file.

        Args:
            file_path: Path to file.

        Returns:
            True if filename indicates temporary file, False otherwise.
        """
        temp_patterns = self.config.get("cleanup", {}).get(
            "temp_filename_patterns", []
        )
        filename = file_path.name.lower()

        for pattern in temp_patterns:
            if pattern.lower() in filename:
                return True

        return False

    def _is_incomplete_download(self, file_path: Path) -> bool:
        """Check if file appears to be an incomplete download.

        Args:
            file_path: Path to file.

        Returns:
            True if file appears incomplete, False otherwise.
        """
        try:
            stat = file_path.stat()
            now = datetime.now()
            mtime = datetime.fromtimestamp(stat.st_mtime)

            # Check if file hasn't been modified recently
            min_age_days = self.config.get("cleanup", {}).get(
                "incomplete_min_age_days", 1
            )
            age_days = (now - mtime).days

            # Check file size (very small files might be incomplete)
            min_size = self.config.get("cleanup", {}).get(
                "incomplete_min_size_bytes", 1024
            )

            # Check if file is locked (being written to)
            # On Unix, try to open in append mode
            try:
                with open(file_path, "a"):
                    pass
            except (IOError, PermissionError):
                # File might be locked, skip it
                return False

            # Consider incomplete if:
            # 1. Has temporary extension/name AND
            # 2. (Hasn't been modified in X days OR is very small)
            if (self._is_temporary_extension(file_path) or self._is_temporary_filename(file_path)):
                if age_days >= min_age_days or stat.st_size < min_size:
                    return True

            return False

        except (OSError, PermissionError) as e:
            logger.debug(f"Cannot check file {file_path}: {e}")
            return False

    def _is_safe_to_delete(
        self, file_path: Path, file_info: Dict[str, Any]
    ) -> bool:
        """Check if file is safe to delete based on safety rules.

        Args:
            file_path: Path to file.
            file_info: Dictionary with file information.

        Returns:
            True if safe to delete, False otherwise.
        """
        safety_config = self.config.get("safety", {})

        # Check minimum age
        min_age_days = safety_config.get("min_age_days", 0)
        if file_info["age_days"] < min_age_days:
            logger.debug(
                f"File too new to delete: {file_path} "
                f"(age: {file_info['age_days']} days)"
            )
            return False

        # Check maximum size (don't delete very large files)
        max_size = safety_config.get("max_size_bytes", None)
        if max_size and file_info["size_bytes"] > max_size:
            logger.debug(
                f"File too large to delete: {file_path} "
                f"(size: {file_info['size_bytes']} bytes)"
            )
            return False

        # Check protected patterns
        protected_patterns = safety_config.get("protected_patterns", [])
        path_str = str(file_path)
        for pattern in protected_patterns:
            if pattern in path_str:
                logger.debug(
                    f"File matches protected pattern: {file_path}"
                )
                return False

        # Check if file is in protected directories
        protected_dirs = safety_config.get("protected_directories", [])
        for protected_dir in protected_dirs:
            try:
                if file_path.resolve().is_relative_to(Path(protected_dir).resolve()):
                    logger.debug(
                        f"File in protected directory: {file_path}"
                    )
                    return False
            except (ValueError, OSError):
                pass

        return True

    def _collect_file_info(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Collect information about a file.

        Args:
            file_path: Path to file.

        Returns:
            Dictionary with file information or None if error.
        """
        try:
            stat = file_path.stat()
            now = datetime.now()
            mtime = datetime.fromtimestamp(stat.st_mtime)
            age_days = (now - mtime).days

            return {
                "path": str(file_path),
                "name": file_path.name,
                "size_bytes": stat.st_size,
                "age_days": age_days,
                "last_modified": mtime.isoformat(),
                "is_temp_extension": self._is_temporary_extension(file_path),
                "is_temp_filename": self._is_temporary_filename(file_path),
                "is_incomplete": self._is_incomplete_download(file_path),
            }
        except (OSError, PermissionError) as e:
            logger.warning(
                f"Cannot access file {file_path}: {e}",
                extra={"file_path": str(file_path)},
            )
            self.stats["errors"] += 1
            return None

    def scan_directory(self, directory: str) -> None:
        """Scan directory for temporary files.

        Args:
            directory: Path to directory to scan.

        Raises:
            FileNotFoundError: If directory doesn't exist.
            PermissionError: If directory is not accessible.
        """
        scan_path = Path(directory)
        if not scan_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        if not scan_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        logger.info(
            f"Starting scan of {directory}",
            extra={"directory": directory},
        )

        self.temp_files = []
        self.stats = {
            "files_scanned": 0,
            "temp_files_found": 0,
            "files_deleted": 0,
            "space_freed_bytes": 0,
            "errors": 0,
        }

        try:
            for root, dirs, files in os.walk(scan_path):
                root_path = Path(root)

                # Skip directories based on patterns
                dirs[:] = [
                    d
                    for d in dirs
                    if not self._should_skip_path(root_path / d)
                ]

                if self._should_skip_path(root_path):
                    continue

                for file_name in files:
                    file_path = root_path / file_name

                    if self._should_skip_path(file_path):
                        continue

                    self.stats["files_scanned"] += 1

                    file_info = self._collect_file_info(file_path)
                    if not file_info:
                        continue

                    # Check if file is temporary
                    if (
                        file_info["is_temp_extension"]
                        or file_info["is_temp_filename"]
                        or file_info["is_incomplete"]
                    ):
                        if self._is_safe_to_delete(file_path, file_info):
                            self.temp_files.append(file_info)
                            self.stats["temp_files_found"] += 1

        except PermissionError as e:
            logger.error(
                f"Permission denied accessing {directory}: {e}",
                extra={"directory": directory},
            )
            raise

        logger.info(
            f"Scan completed: {self.stats['temp_files_found']} "
            f"temporary files found",
            extra=self.stats,
        )

    def cleanup_files(self, dry_run: bool = False) -> None:
        """Delete temporary files found during scan.

        Args:
            dry_run: If True, simulate cleanup without deleting files.
        """
        logger.info(
            f"Starting cleanup (dry_run={dry_run})",
            extra={"dry_run": dry_run, "files_to_delete": len(self.temp_files)},
        )

        deleted_count = 0
        space_freed = 0

        for file_info in self.temp_files:
            file_path = Path(file_info["path"])

            if not file_path.exists():
                logger.debug(f"File no longer exists: {file_path}")
                continue

            try:
                if not dry_run:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    deleted_count += 1
                    space_freed += file_size
                    logger.info(
                        f"Deleted: {file_path} "
                        f"({self._format_size(file_size)})",
                        extra={"file_path": str(file_path), "size": file_size},
                    )
                else:
                    file_size = file_path.stat().st_size
                    deleted_count += 1
                    space_freed += file_size
                    logger.info(
                        f"[DRY RUN] Would delete: {file_path} "
                        f"({self._format_size(file_size)})",
                        extra={"file_path": str(file_path), "size": file_size},
                    )

            except (OSError, PermissionError) as e:
                logger.error(
                    f"Error deleting file {file_path}: {e}",
                    extra={"file_path": str(file_path)},
                )
                self.stats["errors"] += 1

        self.stats["files_deleted"] = deleted_count
        self.stats["space_freed_bytes"] = space_freed

        logger.info(
            f"Cleanup completed: {deleted_count} files deleted, "
            f"{self._format_size(space_freed)} freed",
            extra=self.stats,
        )

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes.

        Returns:
            Formatted size string (e.g., "1.5 MB").
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def generate_report(self, output_path: Optional[str] = None) -> str:
        """Generate cleanup report.

        Args:
            output_path: Optional path to save report file. If None,
                uses default from config.

        Returns:
            Report content as string.
        """
        report_config = self.config.get("report", {})
        default_output = report_config.get(
            "output_file", "cleanup_report.txt"
        )

        output_file = output_path or default_output

        # Sort files by size (largest first)
        sorted_files = sorted(
            self.temp_files,
            key=lambda x: x["size_bytes"],
            reverse=True,
        )

        report_lines = [
            "=" * 80,
            "TEMPORARY FILE CLEANUP REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY",
            "-" * 80,
            f"Files scanned: {self.stats['files_scanned']:,}",
            f"Temporary files found: {self.stats['temp_files_found']:,}",
            f"Files deleted: {self.stats['files_deleted']:,}",
            f"Space freed: {self._format_size(self.stats['space_freed_bytes'])}",
            f"Errors encountered: {self.stats['errors']}",
            "",
            "TEMPORARY FILES FOUND",
            "-" * 80,
        ]

        if not sorted_files:
            report_lines.append("No temporary files found.")
        else:
            for file_info in sorted_files:
                reasons = []
                if file_info["is_temp_extension"]:
                    reasons.append("temp extension")
                if file_info["is_temp_filename"]:
                    reasons.append("temp filename")
                if file_info["is_incomplete"]:
                    reasons.append("incomplete download")

                report_lines.extend(
                    [
                        f"Path: {file_info['path']}",
                        f"  Size: {self._format_size(file_info['size_bytes'])}",
                        f"  Age: {file_info['age_days']} days",
                        f"  Reasons: {', '.join(reasons)}",
                        "",
                    ]
                )

        report_content = "\n".join(report_lines)

        # Save report
        try:
            output_path_obj = Path(output_file)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path_obj, "w", encoding="utf-8") as f:
                f.write(report_content)
            logger.info(f"Report saved to {output_file}")
        except (IOError, PermissionError) as e:
            logger.error(f"Failed to save report: {e}")
            raise

        return report_content


def main() -> None:
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Clean up temporary download files, incomplete downloads, "
        "and files with temporary extensions"
    )
    parser.add_argument(
        "directory",
        help="Directory to scan for temporary files",
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
        help="Simulate cleanup without deleting files",
    )
    parser.add_argument(
        "-r",
        "--report",
        help="Output path for cleanup report (overrides config)",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Automatically delete files without confirmation",
    )

    args = parser.parse_args()

    try:
        cleaner = TemporaryFileCleaner(config_path=args.config)
        cleaner.scan_directory(args.directory)

        if cleaner.stats["temp_files_found"] == 0:
            print("\nNo temporary files found.")
            return

        # Show summary
        print(
            f"\nFound {cleaner.stats['temp_files_found']} temporary files "
            f"totaling {cleaner._format_size(sum(f['size_bytes'] for f in cleaner.temp_files))}"
        )

        # Confirm before deleting (unless auto or dry-run)
        if not args.dry_run and not args.auto:
            response = input(
                "\nDo you want to delete these files? (yes/no): "
            )
            if response.lower() not in ["yes", "y"]:
                print("Cleanup cancelled.")
                return

        cleaner.cleanup_files(dry_run=args.dry_run)
        cleaner.generate_report(output_path=args.report)

        print(
            f"\nCleanup complete. "
            f"Deleted {cleaner.stats['files_deleted']} files, "
            f"freed {cleaner._format_size(cleaner.stats['space_freed_bytes'])}."
        )

    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
