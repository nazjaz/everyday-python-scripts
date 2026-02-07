"""Unused File Identifier - Identify files not accessed or modified recently.

This module scans directories to find files that haven't been accessed or
modified within a specified time period, generating a cleanup report for
disk space management and file organization.
"""

import json
import logging
import logging.handlers
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class UnusedFileIdentifier:
    """Identifies unused files based on access and modification times."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize UnusedFileIdentifier with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.unused_files: List[Dict[str, Any]] = []
        self.stats = {
            "files_scanned": 0,
            "unused_files_found": 0,
            "directories_scanned": 0,
            "total_size_bytes": 0,
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

    def _parse_time_period(self, period: str) -> timedelta:
        """Parse time period string into timedelta object.

        Args:
            period: Time period string (e.g., "30d", "2w", "6m", "1y").

        Returns:
            Timedelta object representing the time period.

        Raises:
            ValueError: If period format is invalid.
        """
        period = period.lower().strip()
        if not period:
            raise ValueError("Time period cannot be empty")

        # Extract number and unit
        if period[-1].isdigit():
            raise ValueError(
                "Time period must end with a unit (d, w, m, y)"
            )

        # Find where the number ends
        num_end = len(period) - 1
        while num_end > 0 and period[num_end - 1].isdigit():
            num_end -= 1

        try:
            number = int(period[:num_end]) if num_end > 0 else 1
        except ValueError:
            raise ValueError(f"Invalid number in time period: {period}")

        unit = period[num_end:]

        # Convert to days
        unit_map = {
            "d": 1,
            "w": 7,
            "m": 30,
            "y": 365,
        }

        if unit not in unit_map:
            raise ValueError(
                f"Invalid time unit: {unit}. Use d, w, m, or y"
            )

        days = number * unit_map[unit]
        return timedelta(days=days)

    def _is_file_unused(
        self, file_path: Path, threshold: timedelta
    ) -> Optional[Dict[str, Any]]:
        """Check if a file is unused based on access and modification times.

        Args:
            file_path: Path to the file to check.
            threshold: Time threshold for considering a file unused.

        Returns:
            Dictionary with file information if unused, None otherwise.
        """
        try:
            stat = file_path.stat()
            now = datetime.now()
            mtime = datetime.fromtimestamp(stat.st_mtime)
            atime = datetime.fromtimestamp(stat.st_atime)

            # Check both modification and access times
            time_since_modification = now - mtime
            time_since_access = now - atime

            # File is unused if both modification and access times exceed threshold
            if (
                time_since_modification >= threshold
                and time_since_access >= threshold
            ):
                return {
                    "path": str(file_path),
                    "size_bytes": stat.st_size,
                    "last_modified": mtime.isoformat(),
                    "last_accessed": atime.isoformat(),
                    "days_since_modification": time_since_modification.days,
                    "days_since_access": time_since_access.days,
                }
            return None
        except (OSError, PermissionError) as e:
            logger.warning(
                f"Cannot access file {file_path}: {e}",
                extra={"file_path": str(file_path)},
            )
            self.stats["errors"] += 1
            return None

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

    def scan_directory(self, directory: str) -> None:
        """Scan directory for unused files.

        Args:
            directory: Path to directory to scan.

        Raises:
            FileNotFoundError: If directory doesn't exist.
            PermissionError: If directory is not accessible.
        """
        scan_config = self.config.get("scan", {})
        threshold_str = scan_config.get("unused_threshold", "90d")
        threshold = self._parse_time_period(threshold_str)

        scan_path = Path(directory)
        if not scan_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        if not scan_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        logger.info(
            f"Starting scan of {directory}",
            extra={
                "directory": directory,
                "threshold": threshold_str,
            },
        )

        self.unused_files = []
        self.stats = {
            "files_scanned": 0,
            "unused_files_found": 0,
            "directories_scanned": 0,
            "total_size_bytes": 0,
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

                self.stats["directories_scanned"] += 1

                for file_name in files:
                    file_path = root_path / file_name

                    if self._should_skip_path(file_path):
                        continue

                    self.stats["files_scanned"] += 1

                    file_info = self._is_file_unused(file_path, threshold)
                    if file_info:
                        self.unused_files.append(file_info)
                        self.stats["unused_files_found"] += 1
                        self.stats["total_size_bytes"] += file_info[
                            "size_bytes"
                        ]

        except PermissionError as e:
            logger.error(
                f"Permission denied accessing {directory}: {e}",
                extra={"directory": directory},
            )
            raise

        logger.info(
            f"Scan completed: {self.stats['unused_files_found']} "
            f"unused files found",
            extra=self.stats,
        )

    def generate_report(
        self, output_path: Optional[str] = None
    ) -> str:
        """Generate cleanup report for unused files.

        Args:
            output_path: Optional path to save report file. If None,
                uses default from config.

        Returns:
            Report content as string.
        """
        report_config = self.config.get("report", {})
        default_output = report_config.get("output_file", "cleanup_report.txt")

        output_file = output_path or default_output

        # Sort files by size (largest first) for better prioritization
        sorted_files = sorted(
            self.unused_files,
            key=lambda x: x["size_bytes"],
            reverse=True,
        )

        # Generate report content
        report_lines = [
            "=" * 80,
            "UNUSED FILES CLEANUP REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY",
            "-" * 80,
            f"Total files scanned: {self.stats['files_scanned']:,}",
            f"Unused files found: {self.stats['unused_files_found']:,}",
            f"Directories scanned: {self.stats['directories_scanned']:,}",
            f"Total size of unused files: "
            f"{self._format_size(self.stats['total_size_bytes'])}",
            f"Errors encountered: {self.stats['errors']}",
            "",
            "UNUSED FILES (sorted by size, largest first)",
            "-" * 80,
        ]

        for file_info in sorted_files:
            report_lines.extend(
                [
                    f"Path: {file_info['path']}",
                    f"  Size: {self._format_size(file_info['size_bytes'])}",
                    f"  Last Modified: {file_info['last_modified']}",
                    f"  Last Accessed: {file_info['last_accessed']}",
                    f"  Days since modification: "
                    f"{file_info['days_since_modification']}",
                    f"  Days since access: "
                    f"{file_info['days_since_access']}",
                    "",
                ]
            )

        report_content = "\n".join(report_lines)

        # Save report to file
        try:
            output_path_obj = Path(output_file)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path_obj, "w", encoding="utf-8") as f:
                f.write(report_content)
            logger.info(
                f"Report saved to {output_file}",
                extra={"output_file": output_file},
            )
        except (IOError, PermissionError) as e:
            logger.error(
                f"Failed to save report to {output_file}: {e}",
                extra={"output_file": output_file},
            )
            raise

        return report_content

    def export_json(self, output_path: Optional[str] = None) -> str:
        """Export unused files data to JSON format.

        Args:
            output_path: Optional path to save JSON file. If None,
                uses default from config.

        Returns:
            Path to saved JSON file.
        """
        report_config = self.config.get("report", {})
        default_output = report_config.get(
            "json_output_file", "cleanup_report.json"
        )

        output_file = output_path or default_output

        export_data = {
            "generated": datetime.now().isoformat(),
            "stats": self.stats,
            "unused_files": sorted(
                self.unused_files,
                key=lambda x: x["size_bytes"],
                reverse=True,
            ),
        }

        try:
            output_path_obj = Path(output_file)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path_obj, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)
            logger.info(
                f"JSON export saved to {output_file}",
                extra={"output_file": output_file},
            )
        except (IOError, PermissionError) as e:
            logger.error(
                f"Failed to save JSON export to {output_file}: {e}",
                extra={"output_file": output_file},
            )
            raise

        return output_file

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


def main() -> None:
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Identify unused files based on access and "
        "modification times"
    )
    parser.add_argument(
        "directory",
        help="Directory to scan for unused files",
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output path for cleanup report (overrides config)",
    )
    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="Also export results to JSON format",
    )

    args = parser.parse_args()

    try:
        identifier = UnusedFileIdentifier(config_path=args.config)
        identifier.scan_directory(args.directory)
        identifier.generate_report(output_path=args.output)

        if args.json:
            identifier.export_json()

        print(
            f"\nScan complete. Found "
            f"{identifier.stats['unused_files_found']} unused files "
            f"totaling "
            f"{identifier._format_size(identifier.stats['total_size_bytes'])}"
        )

    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
