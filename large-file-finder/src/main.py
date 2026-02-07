"""Large File Finder - Find and archive files larger than a specified size.

This module provides functionality to scan directories for files exceeding
a size threshold, generate detailed reports sorted by size, and optionally
move large files to an archive folder. Includes comprehensive logging and
error handling.
"""

import logging
import logging.handlers
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class LargeFileFinder:
    """Finds files larger than a specified size threshold and archives them."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize LargeFileFinder with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_directories()
        self.large_files: List[Dict[str, any]] = []
        self.stats = {
            "scanned": 0,
            "found": 0,
            "archived": 0,
            "errors": 0,
            "errors_list": [],
            "total_size": 0,
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

        # If relative path, try to find it relative to project root
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
        if os.getenv("SCAN_DIRECTORY"):
            config["scan_directory"] = os.getenv("SCAN_DIRECTORY")
        if os.getenv("ARCHIVE_DIRECTORY"):
            config["archive_directory"] = os.getenv("ARCHIVE_DIRECTORY")
        if os.getenv("SIZE_THRESHOLD_MB"):
            config["size_threshold_mb"] = int(os.getenv("SIZE_THRESHOLD_MB"))
        if os.getenv("DRY_RUN"):
            config["operations"]["dry_run"] = (
                os.getenv("DRY_RUN").lower() == "true"
            )

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/large_file_finder.log")

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
        """Set up scan and archive directories."""
        self.scan_dir = Path(
            os.path.expanduser(self.config["scan_directory"])
        )
        self.archive_dir = Path(
            os.path.expanduser(self.config["archive_directory"])
        )

        if not self.scan_dir.exists():
            raise FileNotFoundError(
                f"Scan directory does not exist: {self.scan_dir}"
            )

        if self.config["operations"]["create_archive_directory"]:
            self.archive_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Scan directory: {self.scan_dir}")
        logger.info(f"Archive directory: {self.archive_dir}")

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: File size in bytes.

        Returns:
            Formatted size string (e.g., "1.5 MB").
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def _get_size_threshold_bytes(self) -> int:
        """Convert size threshold from MB to bytes.

        Returns:
            Size threshold in bytes.
        """
        return self.config["size_threshold_mb"] * 1024 * 1024

    def _should_scan_path(self, path: Path) -> bool:
        """Check if path should be scanned based on exclusions.

        Args:
            path: Path to check.

        Returns:
            True if path should be scanned, False otherwise.
        """
        exclusions = self.config.get("exclusions", {})
        path_str = str(path)

        # Check excluded directories
        excluded_dirs = exclusions.get("directories", [])
        for excluded_dir in excluded_dirs:
            excluded_path = Path(os.path.expanduser(excluded_dir))
            try:
                if path.is_relative_to(excluded_path):
                    return False
            except (ValueError, AttributeError):
                # Python < 3.9 compatibility
                if str(path).startswith(str(excluded_path)):
                    return False

        # Check excluded patterns
        excluded_patterns = exclusions.get("patterns", [])
        for pattern in excluded_patterns:
            if pattern in path_str:
                return False

        return True

    def _scan_directory(self, directory: Path) -> None:
        """Recursively scan directory for large files.

        Args:
            directory: Directory to scan.
        """
        try:
            for item in directory.iterdir():
                if not self._should_scan_path(item):
                    logger.debug(f"Skipping excluded path: {item}")
                    continue

                if item.is_file():
                    self.stats["scanned"] += 1
                    try:
                        file_size = item.stat().st_size
                        threshold = self._get_size_threshold_bytes()

                        if file_size > threshold:
                            file_info = {
                                "path": str(item),
                                "size": file_size,
                                "size_formatted": self._format_size(file_size),
                                "parent": str(item.parent),
                            }
                            self.large_files.append(file_info)
                            self.stats["found"] += 1
                            self.stats["total_size"] += file_size
                            logger.debug(
                                f"Found large file: {item} "
                                f"({self._format_size(file_size)})"
                            )
                    except (OSError, PermissionError) as e:
                        error_msg = f"Error accessing {item}: {e}"
                        logger.warning(error_msg)
                        self.stats["errors"] += 1
                        self.stats["errors_list"].append(error_msg)

                elif item.is_dir():
                    if self.config["scan_options"]["recursive"]:
                        self._scan_directory(item)

        except (PermissionError, OSError) as e:
            error_msg = f"Error scanning directory {directory}: {e}"
            logger.warning(error_msg)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)

    def find_large_files(self) -> List[Dict[str, any]]:
        """Find all files larger than the size threshold.

        Returns:
            List of dictionaries containing file information, sorted by size.
        """
        logger.info("Starting large file scan")
        logger.info(
            f"Size threshold: {self.config['size_threshold_mb']} MB "
            f"({self._format_size(self._get_size_threshold_bytes())})"
        )
        logger.info(f"Recursive scan: {self.config['scan_options']['recursive']}")

        self.large_files = []
        self._scan_directory(self.scan_dir)

        # Sort by size (largest first)
        self.large_files.sort(key=lambda x: x["size"], reverse=True)

        logger.info(f"Scan completed. Found {len(self.large_files)} large files")
        return self.large_files

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate a text report of large files.

        Args:
            output_file: Optional path to save report file.

        Returns:
            Report content as string.
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("Large File Finder Report")
        report_lines.append("=" * 80)
        report_lines.append(f"Scan Directory: {self.scan_dir}")
        report_lines.append(
            f"Size Threshold: {self.config['size_threshold_mb']} MB "
            f"({self._format_size(self._get_size_threshold_bytes())})"
        )
        report_lines.append(f"Files Found: {len(self.large_files)}")
        report_lines.append(
            f"Total Size: {self._format_size(self.stats['total_size'])}"
        )
        report_lines.append("=" * 80)
        report_lines.append("")

        if not self.large_files:
            report_lines.append("No large files found.")
        else:
            report_lines.append(
                f"{'Size':<15} {'Path':<50}"
            )
            report_lines.append("-" * 80)

            for file_info in self.large_files:
                path = file_info["path"]
                # Truncate long paths for display
                if len(path) > 50:
                    path = "..." + path[-47:]
                report_lines.append(
                    f"{file_info['size_formatted']:<15} {path:<50}"
                )

        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("Statistics")
        report_lines.append("=" * 80)
        report_lines.append(f"Files Scanned: {self.stats['scanned']}")
        report_lines.append(f"Large Files Found: {self.stats['found']}")
        report_lines.append(f"Files Archived: {self.stats['archived']}")
        report_lines.append(f"Errors: {self.stats['errors']}")

        if self.stats["errors_list"]:
            report_lines.append("")
            report_lines.append("Errors:")
            for error in self.stats["errors_list"]:
                report_lines.append(f"  - {error}")

        report_content = "\n".join(report_lines)

        if output_file:
            report_path = Path(output_file)
            if not report_path.is_absolute():
                project_root = Path(__file__).parent.parent
                report_path = project_root / output_file
            report_path.parent.mkdir(parents=True, exist_ok=True)

            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            logger.info(f"Report saved to: {report_path}")

        return report_content

    def _archive_file(self, file_path: Path) -> bool:
        """Archive a single file to archive directory.

        Args:
            file_path: Path to file to archive.

        Returns:
            True if successful, False otherwise.
        """
        try:
            if self.config["operations"]["dry_run"]:
                logger.info(
                    f"[DRY RUN] Would archive: {file_path} -> "
                    f"{self.archive_dir / file_path.name}"
                )
                return True

            # Determine destination path
            dest_path = self.archive_dir / file_path.name

            # Handle name conflicts
            if dest_path.exists():
                if self.config["archive_options"]["handle_conflicts"] == "skip":
                    logger.info(
                        f"Skipping {file_path.name}: already exists in archive"
                    )
                    return False
                elif (
                    self.config["archive_options"]["handle_conflicts"]
                    == "rename"
                ):
                    counter = 1
                    stem = file_path.stem
                    suffix = file_path.suffix
                    while dest_path.exists():
                        new_name = f"{stem}_{counter}{suffix}"
                        dest_path = self.archive_dir / new_name
                        counter += 1
                    logger.debug(
                        f"Name conflict resolved: {file_path.name} -> "
                        f"{dest_path.name}"
                    )

            # Move or copy file
            if self.config["archive_options"]["method"] == "move":
                shutil.move(str(file_path), str(dest_path))
                logger.info(f"Moved: {file_path} -> {dest_path}")
            else:
                shutil.copy2(str(file_path), str(dest_path))
                logger.info(f"Copied: {file_path} -> {dest_path}")

            # Preserve timestamps
            if self.config["archive_options"]["preserve_timestamps"]:
                stat = file_path.stat()
                os.utime(dest_path, (stat.st_atime, stat.st_mtime))

            self.stats["archived"] += 1
            return True

        except (OSError, shutil.Error) as e:
            error_msg = f"Error archiving {file_path}: {e}"
            logger.error(error_msg)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            return False

    def archive_files(self) -> Dict[str, int]:
        """Archive all found large files.

        Returns:
            Dictionary with statistics about the operation.
        """
        if not self.large_files:
            logger.warning("No large files to archive")
            return self.stats

        logger.info(f"Starting archive operation for {len(self.large_files)} files")
        logger.info(
            f"Archive method: {self.config['archive_options']['method']}"
        )
        logger.info(f"Dry run mode: {self.config['operations']['dry_run']}")

        for file_info in self.large_files:
            file_path = Path(file_info["path"])
            if file_path.exists():
                self._archive_file(file_path)
            else:
                error_msg = f"File no longer exists: {file_path}"
                logger.warning(error_msg)
                self.stats["errors"] += 1
                self.stats["errors_list"].append(error_msg)

        logger.info("Archive operation completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats


def main() -> int:
    """Main entry point for large file finder."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Find files larger than a specified size threshold "
        "and optionally archive them"
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
        help="Preview changes without archiving files",
    )
    parser.add_argument(
        "-r",
        "--report-only",
        action="store_true",
        help="Generate report only, do not archive files",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path to save report file",
    )

    args = parser.parse_args()

    try:
        finder = LargeFileFinder(config_path=args.config)
        if args.dry_run:
            finder.config["operations"]["dry_run"] = True

        # Find large files
        large_files = finder.find_large_files()

        # Generate report
        report = finder.generate_report(
            output_file=args.output or finder.config.get("report_file")
        )
        print("\n" + report)

        # Archive files if requested
        if not args.report_only and finder.config["operations"]["auto_archive"]:
            stats = finder.archive_files()
            print(f"\nArchived {stats['archived']} files")

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
