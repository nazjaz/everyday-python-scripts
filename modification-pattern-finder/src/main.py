"""Modification Pattern Finder.

A Python script that finds files with specific modification patterns such as
files modified at certain times of day or on specific days of the week.
"""

import argparse
import logging
import sys
from datetime import datetime, time
from pathlib import Path
from typing import List, Optional, Set

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/finder.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


class ModificationPatternFinder:
    """Finds files matching modification time patterns."""

    DAYS_OF_WEEK = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
        "mon": 0,
        "tue": 1,
        "wed": 2,
        "thu": 3,
        "fri": 4,
        "sat": 5,
        "sun": 6,
    }

    def __init__(
        self,
        time_start: Optional[time] = None,
        time_end: Optional[time] = None,
        days_of_week: Optional[Set[int]] = None,
        file_patterns: Optional[List[str]] = None,
    ) -> None:
        """Initialize the pattern finder.

        Args:
            time_start: Start time of day for filtering (None = no start limit)
            time_end: End time of day for filtering (None = no end limit)
            days_of_week: Set of day numbers (0=Monday, 6=Sunday) to filter
            file_patterns: List of file extensions or patterns to include

        Raises:
            ValueError: If time_start is after time_end
        """
        if time_start and time_end and time_start > time_end:
            raise ValueError("time_start must be before or equal to time_end")

        self.time_start = time_start
        self.time_end = time_end
        self.days_of_week = days_of_week
        self.file_patterns = file_patterns

        self.stats = {
            "files_scanned": 0,
            "files_matched": 0,
            "errors": 0,
        }

    def _matches_time_pattern(self, file_time: time) -> bool:
        """Check if file modification time matches time pattern.

        Args:
            file_time: Time of file modification

        Returns:
            True if time matches pattern, False otherwise
        """
        if self.time_start is None and self.time_end is None:
            return True

        if self.time_start and self.time_end:
            if self.time_start <= self.time_end:
                return self.time_start <= file_time <= self.time_end
            else:
                return file_time >= self.time_start or file_time <= self.time_end

        if self.time_start:
            return file_time >= self.time_start

        if self.time_end:
            return file_time <= self.time_end

        return True

    def _matches_day_pattern(self, file_datetime: datetime) -> bool:
        """Check if file modification day matches day pattern.

        Args:
            file_datetime: Datetime of file modification

        Returns:
            True if day matches pattern, False otherwise
        """
        if self.days_of_week is None:
            return True

        day_of_week = file_datetime.weekday()
        return day_of_week in self.days_of_week

    def _matches_file_pattern(self, file_path: Path) -> bool:
        """Check if file matches file pattern filter.

        Args:
            file_path: Path to file

        Returns:
            True if file matches pattern, False otherwise
        """
        if self.file_patterns is None:
            return True

        suffix = file_path.suffix.lower()
        name = file_path.name.lower()

        for pattern in self.file_patterns:
            if pattern.startswith("."):
                if suffix == pattern.lower():
                    return True
            elif pattern in name:
                return True

        return False

    def find_files(
        self, paths: List[Path], recursive: bool = False
    ) -> List[dict]:
        """Find files matching modification patterns.

        Args:
            paths: List of file or directory paths to scan
            recursive: If True, recursively scan directories

        Returns:
            List of dictionaries with file information
        """
        all_files: List[Path] = []

        for path in paths:
            path = Path(path).expanduser().resolve()

            if path.is_file():
                all_files.append(path)
            elif path.is_dir():
                if recursive:
                    all_files.extend(path.rglob("*"))
                else:
                    all_files.extend(path.glob("*"))

        logger.info(f"Found {len(all_files)} files to scan")

        matching_files: List[dict] = []

        for file_path in all_files:
            if not file_path.is_file():
                continue

            self.stats["files_scanned"] += 1

            if not self._matches_file_pattern(file_path):
                continue

            try:
                modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                file_time = modified_time.time()
                file_date = modified_time.date()

                if not self._matches_time_pattern(file_time):
                    continue

                if not self._matches_day_pattern(modified_time):
                    continue

                file_info = {
                    "path": str(file_path),
                    "name": file_path.name,
                    "size": file_path.stat().st_size,
                    "modified_datetime": modified_time.isoformat(),
                    "modified_date": file_date.isoformat(),
                    "modified_time": file_time.isoformat(),
                    "day_of_week": modified_time.strftime("%A"),
                    "day_of_week_number": modified_time.weekday(),
                }

                matching_files.append(file_info)
                self.stats["files_matched"] += 1

            except (OSError, PermissionError) as e:
                logger.warning(f"Cannot access file {file_path}: {e}")
                self.stats["errors"] += 1
            except Exception as e:
                logger.exception(f"Unexpected error processing {file_path}: {e}")
                self.stats["errors"] += 1

        return matching_files

    def format_report(self, matching_files: List[dict]) -> str:
        """Format matching files as a report.

        Args:
            matching_files: List of file information dictionaries

        Returns:
            Formatted string report
        """
        if not matching_files:
            return "No files found matching the specified patterns."

        lines = [
            "Modification Pattern Analysis Report",
            "=" * 80,
            "",
            f"Files scanned: {self.stats['files_scanned']}",
            f"Files matched: {self.stats['files_matched']}",
            f"Errors: {self.stats['errors']}",
            "",
        ]

        if self.time_start or self.time_end:
            time_filter = "Time filter: "
            if self.time_start:
                time_filter += f"from {self.time_start.strftime('%H:%M:%S')} "
            if self.time_end:
                time_filter += f"to {self.time_end.strftime('%H:%M:%S')}"
            lines.append(time_filter)
            lines.append("")

        if self.days_of_week:
            day_names = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            filtered_days = [day_names[d] for d in sorted(self.days_of_week)]
            lines.append(f"Days of week: {', '.join(filtered_days)}")
            lines.append("")

        lines.append("-" * 80)
        lines.append("")

        for file_info in sorted(matching_files, key=lambda x: x["modified_datetime"]):
            lines.append(f"File: {file_info['path']}")
            lines.append(f"  Name: {file_info['name']}")
            lines.append(f"  Size: {file_info['size']:,} bytes")
            lines.append(f"  Modified: {file_info['modified_datetime']}")
            lines.append(f"  Day: {file_info['day_of_week']}")
            lines.append("")

        return "\n".join(lines)


def parse_time(time_string: str) -> time:
    """Parse time string into time object.

    Args:
        time_string: Time string in format HH:MM or HH:MM:SS

    Returns:
        Time object

    Raises:
        ValueError: If time string format is invalid
    """
    try:
        parts = time_string.split(":")
        if len(parts) == 2:
            return time(int(parts[0]), int(parts[1]))
        elif len(parts) == 3:
            return time(int(parts[0]), int(parts[1]), int(parts[2]))
        else:
            raise ValueError(f"Invalid time format: {time_string}")
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid time format: {time_string}") from e


def parse_days_of_week(day_strings: List[str]) -> Set[int]:
    """Parse day of week strings into set of day numbers.

    Args:
        day_strings: List of day names (e.g., ["monday", "friday"])

    Returns:
        Set of day numbers (0=Monday, 6=Sunday)

    Raises:
        ValueError: If day name is invalid
    """
    days = set()

    for day_str in day_strings:
        day_lower = day_str.lower()
        if day_lower in ModificationPatternFinder.DAYS_OF_WEEK:
            days.add(ModificationPatternFinder.DAYS_OF_WEEK[day_lower])
        else:
            raise ValueError(f"Invalid day of week: {day_str}")

    return days


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Dictionary containing configuration values

    Raises:
        FileNotFoundError: If config file does not exist
        yaml.YAMLError: If config file is invalid YAML
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config if config else {}
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in config file: {e}")
        raise


def main() -> int:
    """Main entry point for the script.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        description="Find files with specific modification time patterns"
    )
    parser.add_argument(
        "paths",
        type=str,
        nargs="+",
        help="File paths or directory paths to scan",
    )
    parser.add_argument(
        "--time-start",
        type=str,
        default=None,
        help="Start time of day (HH:MM or HH:MM:SS)",
    )
    parser.add_argument(
        "--time-end",
        type=str,
        default=None,
        help="End time of day (HH:MM or HH:MM:SS)",
    )
    parser.add_argument(
        "--days",
        type=str,
        nargs="+",
        default=None,
        help="Days of week to filter (e.g., monday friday)",
    )
    parser.add_argument(
        "--file-patterns",
        type=str,
        nargs="+",
        default=None,
        help="File extensions or patterns to include",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively scan directories",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path for report",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file (YAML)",
    )

    args = parser.parse_args()

    try:
        time_start = parse_time(args.time_start) if args.time_start else None
        time_end = parse_time(args.time_end) if args.time_end else None
        days_of_week = (
            parse_days_of_week(args.days) if args.days else None
        )
        file_patterns = args.file_patterns
        recursive = args.recursive

        if args.config:
            config = load_config(Path(args.config))
            if "time_start" in config:
                time_start = parse_time(config["time_start"])
            if "time_end" in config:
                time_end = parse_time(config["time_end"])
            if "days_of_week" in config:
                days_of_week = parse_days_of_week(config["days_of_week"])
            if "file_patterns" in config:
                file_patterns = config["file_patterns"]
            if "recursive" in config:
                recursive = config["recursive"]

        finder = ModificationPatternFinder(
            time_start=time_start,
            time_end=time_end,
            days_of_week=days_of_week,
            file_patterns=file_patterns,
        )

        file_paths = [Path(p) for p in args.paths]
        matching_files = finder.find_files(file_paths, recursive=recursive)

        report = finder.format_report(matching_files)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(report)
            logger.info(f"Report saved to {output_path}")
        else:
            print(report)

        return 0

    except (ValueError, FileNotFoundError) as e:
        logger.error(f"Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
