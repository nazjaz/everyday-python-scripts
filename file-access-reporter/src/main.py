"""File Access Reporter - Generate file access and modification reports.

This module provides functionality to scan directories, collect file access
and modification statistics, and generate comprehensive reports showing
access patterns, modification frequencies, and temporal analysis.
"""

import json
import logging
import logging.handlers
import os
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FileAccessReporter:
    """Generates reports on file access and modification patterns."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize FileAccessReporter with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.file_data: List[Dict[str, Any]] = []
        self.access_patterns: Dict[str, int] = defaultdict(int)
        self.modification_patterns: Dict[str, int] = defaultdict(int)
        self.stats = {
            "files_scanned": 0,
            "directories_scanned": 0,
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

    def _get_time_bucket(self, timestamp: datetime, bucket_size: str) -> str:
        """Get time bucket string for grouping.

        Args:
            timestamp: Datetime object.
            bucket_size: Bucket size ('day', 'week', 'month', 'year').

        Returns:
            Time bucket string.
        """
        if bucket_size == "day":
            return timestamp.strftime("%Y-%m-%d")
        elif bucket_size == "week":
            # Get ISO week
            year, week, _ = timestamp.isocalendar()
            return f"{year}-W{week:02d}"
        elif bucket_size == "month":
            return timestamp.strftime("%Y-%m")
        elif bucket_size == "year":
            return timestamp.strftime("%Y")
        else:
            return timestamp.strftime("%Y-%m-%d")

    def _calculate_days_since(self, timestamp: datetime) -> int:
        """Calculate days since timestamp.

        Args:
            timestamp: Datetime object.

        Returns:
            Number of days since timestamp.
        """
        now = datetime.now()
        delta = now - timestamp
        return delta.days

    def _collect_file_data(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Collect access and modification data for a file.

        Args:
            file_path: Path to file.

        Returns:
            Dictionary with file data or None if error.
        """
        try:
            stat = file_path.stat()
            atime = datetime.fromtimestamp(stat.st_atime)
            mtime = datetime.fromtimestamp(stat.st_mtime)
            ctime = datetime.fromtimestamp(stat.st_ctime)

            days_since_access = self._calculate_days_since(atime)
            days_since_modification = self._calculate_days_since(mtime)

            return {
                "path": str(file_path),
                "name": file_path.name,
                "extension": file_path.suffix,
                "size_bytes": stat.st_size,
                "last_accessed": atime.isoformat(),
                "last_modified": mtime.isoformat(),
                "created": ctime.isoformat(),
                "days_since_access": days_since_access,
                "days_since_modification": days_since_modification,
                "access_bucket": self._get_time_bucket(
                    atime,
                    self.config.get("report", {}).get(
                        "time_bucket", "day"
                    ),
                ),
                "modification_bucket": self._get_time_bucket(
                    mtime,
                    self.config.get("report", {}).get(
                        "time_bucket", "day"
                    ),
                ),
            }
        except (OSError, PermissionError) as e:
            logger.warning(
                f"Cannot access file {file_path}: {e}",
                extra={"file_path": str(file_path)},
            )
            self.stats["errors"] += 1
            return None

    def scan_directory(self, directory: str) -> None:
        """Scan directory and collect file access data.

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

        self.file_data = []
        self.access_patterns = defaultdict(int)
        self.modification_patterns = defaultdict(int)
        self.stats = {
            "files_scanned": 0,
            "directories_scanned": 0,
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

                    file_info = self._collect_file_data(file_path)
                    if file_info:
                        self.file_data.append(file_info)
                        self.access_patterns[file_info["access_bucket"]] += 1
                        self.modification_patterns[
                            file_info["modification_bucket"]
                        ] += 1

        except PermissionError as e:
            logger.error(
                f"Permission denied accessing {directory}: {e}",
                extra={"directory": directory},
            )
            raise

        logger.info(
            f"Scan completed: {self.stats['files_scanned']} files scanned",
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

    def _get_access_frequency_category(self, days: int) -> str:
        """Categorize access frequency based on days since access.

        Args:
            days: Days since last access.

        Returns:
            Frequency category string.
        """
        if days == 0:
            return "Today"
        elif days <= 7:
            return "This Week"
        elif days <= 30:
            return "This Month"
        elif days <= 90:
            return "Last 3 Months"
        elif days <= 180:
            return "Last 6 Months"
        elif days <= 365:
            return "Last Year"
        else:
            return "Over 1 Year"

    def generate_report(self, output_path: Optional[str] = None) -> str:
        """Generate comprehensive file access report.

        Args:
            output_path: Optional path to save report file. If None,
                uses default from config.

        Returns:
            Report content as string.
        """
        report_config = self.config.get("report", {})
        default_output = report_config.get(
            "output_file", "file_access_report.txt"
        )

        output_file = output_path or default_output

        # Sort files by last access time (most recent first)
        sorted_files = sorted(
            self.file_data,
            key=lambda x: x["days_since_access"],
        )

        # Calculate statistics
        total_size = sum(f["size_bytes"] for f in self.file_data)
        access_frequency = defaultdict(int)
        modification_frequency = defaultdict(int)

        for file_info in self.file_data:
            access_cat = self._get_access_frequency_category(
                file_info["days_since_access"]
            )
            access_frequency[access_cat] += 1

            mod_cat = self._get_access_frequency_category(
                file_info["days_since_modification"]
            )
            modification_frequency[mod_cat] += 1

        # Generate report content
        report_lines = [
            "=" * 80,
            "FILE ACCESS AND MODIFICATION REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY",
            "-" * 80,
            f"Total files scanned: {self.stats['files_scanned']:,}",
            f"Directories scanned: {self.stats['directories_scanned']:,}",
            f"Total size: {self._format_size(total_size)}",
            f"Errors encountered: {self.stats['errors']}",
            "",
            "ACCESS FREQUENCY DISTRIBUTION",
            "-" * 80,
        ]

        for category in [
            "Today",
            "This Week",
            "This Month",
            "Last 3 Months",
            "Last 6 Months",
            "Last Year",
            "Over 1 Year",
        ]:
            count = access_frequency.get(category, 0)
            if count > 0:
                percentage = (count / len(self.file_data)) * 100
                report_lines.append(
                    f"{category:20s}: {count:6,} files ({percentage:5.1f}%)"
                )

        report_lines.extend(
            [
                "",
                "MODIFICATION FREQUENCY DISTRIBUTION",
                "-" * 80,
            ]
        )

        for category in [
            "Today",
            "This Week",
            "This Month",
            "Last 3 Months",
            "Last 6 Months",
            "Last Year",
            "Over 1 Year",
        ]:
            count = modification_frequency.get(category, 0)
            if count > 0:
                percentage = (count / len(self.file_data)) * 100
                report_lines.append(
                    f"{category:20s}: {count:6,} files ({percentage:5.1f}%)"
                )

        # Access patterns over time
        report_lines.extend(
            [
                "",
                "ACCESS PATTERNS OVER TIME",
                "-" * 80,
            ]
        )

        sorted_access = sorted(self.access_patterns.items())
        for bucket, count in sorted_access[-20:]:  # Last 20 buckets
            report_lines.append(f"{bucket:20s}: {count:6,} files")

        # Modification patterns over time
        report_lines.extend(
            [
                "",
                "MODIFICATION PATTERNS OVER TIME",
                "-" * 80,
            ]
        )

        sorted_mod = sorted(self.modification_patterns.items())
        for bucket, count in sorted_mod[-20:]:  # Last 20 buckets
            report_lines.append(f"{bucket:20s}: {count:6,} files")

        # Most recently accessed files
        report_lines.extend(
            [
                "",
                "MOST RECENTLY ACCESSED FILES (Top 20)",
                "-" * 80,
            ]
        )

        for file_info in sorted_files[:20]:
            report_lines.append(
                f"Path: {file_info['path']}",
            )
            report_lines.append(
                f"  Last Accessed: {file_info['last_accessed']} "
                f"({file_info['days_since_access']} days ago)"
            )
            report_lines.append(
                f"  Last Modified: {file_info['last_modified']} "
                f"({file_info['days_since_modification']} days ago)"
            )
            report_lines.append(
                f"  Size: {self._format_size(file_info['size_bytes'])}"
            )
            report_lines.append("")

        # Least recently accessed files
        report_lines.extend(
            [
                "LEAST RECENTLY ACCESSED FILES (Top 20)",
                "-" * 80,
            ]
        )

        for file_info in sorted_files[-20:]:
            report_lines.append(
                f"Path: {file_info['path']}",
            )
            report_lines.append(
                f"  Last Accessed: {file_info['last_accessed']} "
                f"({file_info['days_since_access']} days ago)"
            )
            report_lines.append(
                f"  Last Modified: {file_info['last_modified']} "
                f"({file_info['days_since_modification']} days ago)"
            )
            report_lines.append(
                f"  Size: {self._format_size(file_info['size_bytes'])}"
            )
            report_lines.append("")

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
        """Export file access data to JSON format.

        Args:
            output_path: Optional path to save JSON file. If None,
                uses default from config.

        Returns:
            Path to saved JSON file.
        """
        report_config = self.config.get("report", {})
        default_output = report_config.get(
            "json_output_file", "file_access_report.json"
        )

        output_file = output_path or default_output

        export_data = {
            "generated": datetime.now().isoformat(),
            "stats": self.stats,
            "access_patterns": dict(self.access_patterns),
            "modification_patterns": dict(self.modification_patterns),
            "files": sorted(
                self.file_data,
                key=lambda x: x["days_since_access"],
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


def main() -> None:
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate file access and modification reports"
    )
    parser.add_argument(
        "directory",
        help="Directory to scan for file access data",
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
        help="Output path for text report (overrides config)",
    )
    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="Also export results to JSON format",
    )

    args = parser.parse_args()

    try:
        reporter = FileAccessReporter(config_path=args.config)
        reporter.scan_directory(args.directory)
        reporter.generate_report(output_path=args.output)

        if args.json:
            reporter.export_json()

        print(
            f"\nReport generated. Scanned {reporter.stats['files_scanned']} "
            f"files in {reporter.stats['directories_scanned']} directories."
        )

    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
