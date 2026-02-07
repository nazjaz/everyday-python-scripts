"""Recent Files Finder - Find files modified within time period.

This module provides functionality to find files modified within the last
N days, hours, or minutes, useful for tracking recent activity and changes.
"""

import logging
import logging.handlers
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class RecentFilesFinder:
    """Finds files modified within specified time period."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize RecentFilesFinder with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.matched_files: List[Dict[str, Any]] = []
        self.stats = {
            "files_scanned": 0,
            "files_matched": 0,
            "directories_scanned": 0,
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
        if os.getenv("SCAN_DIRECTORY"):
            config["search"]["directory"] = os.getenv("SCAN_DIRECTORY")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/recent_files_finder.log")

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

    def _is_excluded(self, file_path: Path) -> bool:
        """Check if file should be excluded from search.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file should be excluded, False otherwise.
        """
        exclude_config = self.config.get("search", {}).get("exclude", {})
        exclude_patterns = exclude_config.get("patterns", [])
        exclude_dirs = exclude_config.get("directories", [])
        exclude_extensions = exclude_config.get("extensions", [])

        # Check directory exclusion
        for exclude_dir in exclude_dirs:
            if exclude_dir in file_path.parts:
                return True

        # Check extension exclusion
        if exclude_extensions:
            file_ext = file_path.suffix.lower()
            if file_ext in [ext.lower() for ext in exclude_extensions]:
                return True

        # Check pattern exclusion
        file_str = str(file_path)
        for pattern in exclude_patterns:
            try:
                import re

                if re.search(pattern, file_str):
                    return True
            except Exception:
                pass

        return False

    def _matches_pattern(self, file_path: Path, patterns: Optional[List[str]]) -> bool:
        """Check if file matches specified patterns.

        Args:
            file_path: Path to file.
            patterns: List of glob patterns to match.

        Returns:
            True if file matches any pattern, False otherwise.
        """
        if not patterns:
            return True

        for pattern in patterns:
            if file_path.match(pattern):
                return True
            # Also check if pattern matches filename
            if file_path.name == pattern or pattern in file_path.name:
                return True

        return False

    def find_recent_files(
        self,
        time_value: int,
        time_unit: str = "days",
        directory: Optional[str] = None,
        patterns: Optional[List[str]] = None,
        recursive: bool = True,
    ) -> List[Dict[str, Any]]:
        """Find files modified within specified time period.

        Args:
            time_value: Number of time units (e.g., 7 for 7 days).
            time_unit: Time unit - "days", "hours", or "minutes".
            directory: Directory to search (overrides config).
            patterns: File patterns to match (overrides config).
            recursive: Whether to search recursively (overrides config).

        Returns:
            List of dictionaries with file information.

        Raises:
            ValueError: If time_unit is invalid or time_value is negative.
            FileNotFoundError: If directory doesn't exist.
        """
        valid_units = ["days", "hours", "minutes"]
        if time_unit not in valid_units:
            raise ValueError(f"time_unit must be one of: {', '.join(valid_units)}")

        if time_value < 0:
            raise ValueError("time_value must be non-negative")

        # Calculate cutoff time
        if time_unit == "days":
            cutoff_time = datetime.now() - timedelta(days=time_value)
        elif time_unit == "hours":
            cutoff_time = datetime.now() - timedelta(hours=time_value)
        else:  # minutes
            cutoff_time = datetime.now() - timedelta(minutes=time_value)

        cutoff_timestamp = cutoff_time.timestamp()

        # Determine search directory
        if directory:
            search_dir = Path(directory)
        else:
            search_dir = Path(self.config.get("search", {}).get("directory", "."))

        if not search_dir.exists():
            raise FileNotFoundError(f"Directory does not exist: {search_dir}")

        if not search_dir.is_dir():
            raise ValueError(f"Path is not a directory: {search_dir}")

        # Determine patterns
        if patterns is None:
            patterns = self.config.get("search", {}).get("patterns")

        # Determine recursive
        if recursive is None:
            recursive = self.config.get("search", {}).get("recursive", True)

        logger.info(
            f"Searching for files modified within last {time_value} {time_unit} "
            f"in {search_dir}"
        )

        self.matched_files = []
        self.stats = {
            "files_scanned": 0,
            "files_matched": 0,
            "directories_scanned": 0,
            "errors": 0,
        }

        # Walk directory
        if recursive:
            iterator = search_dir.rglob("*")
        else:
            iterator = search_dir.glob("*")

        for item_path in iterator:
            if not item_path.is_file():
                if item_path.is_dir():
                    self.stats["directories_scanned"] += 1
                continue

            self.stats["files_scanned"] += 1

            # Check exclusions
            if self._is_excluded(item_path):
                continue

            # Check patterns
            if not self._matches_pattern(item_path, patterns):
                continue

            # Check modification time
            try:
                mtime = item_path.stat().st_mtime
                if mtime >= cutoff_timestamp:
                    # Get file information
                    file_info = {
                        "path": str(item_path),
                        "name": item_path.name,
                        "size": item_path.stat().st_size,
                        "modified_time": mtime,
                        "modified_datetime": datetime.fromtimestamp(mtime),
                        "extension": item_path.suffix.lower() or "no_extension",
                        "directory": str(item_path.parent),
                    }

                    # Calculate time since modification
                    time_diff = datetime.now() - file_info["modified_datetime"]
                    if time_unit == "days":
                        file_info["age_days"] = time_diff.days
                        file_info["age_hours"] = time_diff.total_seconds() / 3600
                        file_info["age_minutes"] = time_diff.total_seconds() / 60
                    elif time_unit == "hours":
                        file_info["age_hours"] = time_diff.total_seconds() / 3600
                        file_info["age_minutes"] = time_diff.total_seconds() / 60
                    else:
                        file_info["age_minutes"] = time_diff.total_seconds() / 60

                    self.matched_files.append(file_info)
                    self.stats["files_matched"] += 1

            except (OSError, PermissionError) as e:
                logger.warning(f"Could not get file info for {item_path}: {e}")
                self.stats["errors"] += 1

        # Sort by modification time (newest first)
        self.matched_files.sort(key=lambda x: x["modified_time"], reverse=True)

        logger.info(
            f"Found {self.stats['files_matched']} file(s) modified within "
            f"last {time_value} {time_unit}"
        )

        return self.matched_files

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate text report of recent files.

        Args:
            output_file: Path to output file (overrides config).

        Returns:
            Report content as string.
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("Recent Files Report")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Summary
        report_lines.append("Summary Statistics")
        report_lines.append("-" * 80)
        report_lines.append(f"Files scanned: {self.stats['files_scanned']:,}")
        report_lines.append(f"Files matched: {self.stats['files_matched']:,}")
        report_lines.append(f"Directories scanned: {self.stats['directories_scanned']:,}")
        report_lines.append(f"Errors: {self.stats['errors']}")
        report_lines.append("")

        # File list
        if self.matched_files:
            report_lines.append("Recent Files (Newest First)")
            report_lines.append("-" * 80)
            report_lines.append(
                f"{'Modified':<20s} {'Size':>12s} {'Age':>15s} {'File':<40s}"
            )
            report_lines.append("-" * 80)

            for file_info in self.matched_files:
                mod_time = file_info["modified_datetime"].strftime("%Y-%m-%d %H:%M:%S")
                size_str = self._format_size(file_info["size"])

                # Format age
                if "age_minutes" in file_info:
                    if file_info["age_minutes"] < 60:
                        age_str = f"{file_info['age_minutes']:.1f} min"
                    elif file_info["age_minutes"] < 1440:
                        age_str = f"{file_info['age_minutes'] / 60:.1f} hours"
                    else:
                        age_str = f"{file_info['age_minutes'] / 1440:.1f} days"
                else:
                    age_str = "N/A"

                file_path = file_info["path"]
                if len(file_path) > 40:
                    file_path = "..." + file_path[-37:]

                report_lines.append(
                    f"{mod_time:<20s} {size_str:>12s} {age_str:>15s} {file_path:<40s}"
                )
        else:
            report_lines.append("No recent files found.")

        report_lines.append("")
        report_lines.append("=" * 80)

        report_content = "\n".join(report_lines)

        # Write to file if specified
        if output_file:
            output_path = Path(output_file)
            if not output_path.is_absolute():
                output_dir = self.config.get("report", {}).get("output_directory", "output")
                output_path = Path(output_dir) / output_file
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            logger.info(f"Report saved to: {output_path}")

        return report_content

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes.

        Returns:
            Formatted size string.
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def get_statistics(self) -> Dict[str, Any]:
        """Get search statistics.

        Returns:
            Dictionary with statistics.
        """
        return self.stats.copy()


def main() -> int:
    """Main entry point for recent files finder."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Find files modified within specified time period"
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
        help="Directory to search (overrides config)",
    )
    parser.add_argument(
        "-t",
        "--time",
        type=int,
        required=True,
        help="Time value (e.g., 7 for 7 days)",
    )
    parser.add_argument(
        "-u",
        "--unit",
        choices=["days", "hours", "minutes"],
        default="days",
        help="Time unit: days, hours, or minutes (default: days)",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        action="append",
        help="File pattern to match (can be specified multiple times)",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Disable recursive directory search",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file for report (overrides config)",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Only list file paths, no detailed report",
    )

    args = parser.parse_args()

    try:
        finder = RecentFilesFinder(config_path=args.config)

        files = finder.find_recent_files(
            time_value=args.time,
            time_unit=args.unit,
            directory=args.directory,
            patterns=args.pattern,
            recursive=not args.no_recursive,
        )

        if args.list_only:
            # Simple list output
            for file_info in files:
                print(file_info["path"])
        else:
            # Generate and print report
            output_file = args.output or finder.config.get("report", {}).get("output_file")
            report_content = finder.generate_report(output_file=output_file)
            print(report_content)

            # Print summary
            print(f"\nFound {len(files)} file(s) modified within last {args.time} {args.unit}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
