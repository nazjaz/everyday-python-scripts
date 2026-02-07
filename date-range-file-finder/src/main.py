"""File Date Range Finder.

A Python script that finds files modified within a specific date range.
Useful for locating files created or changed during particular time periods.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/file_finder.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


class DateRangeFileFinder:
    """Finds files modified within a specified date range."""

    def __init__(
        self,
        start_date: datetime,
        end_date: datetime,
        search_path: Path,
        recursive: bool = True,
        file_pattern: Optional[str] = None,
    ) -> None:
        """Initialize the file finder with search parameters.

        Args:
            start_date: Start of the date range (inclusive)
            end_date: End of the date range (inclusive)
            search_path: Directory path to search in
            recursive: Whether to search subdirectories recursively
            file_pattern: Optional glob pattern to filter files (e.g., "*.txt")
        """
        if start_date > end_date:
            raise ValueError("Start date must be before or equal to end date")

        self.start_date = start_date
        self.end_date = end_date
        self.search_path = Path(search_path)
        self.recursive = recursive
        self.file_pattern = file_pattern

        if not self.search_path.exists():
            raise FileNotFoundError(f"Search path does not exist: {search_path}")
        if not self.search_path.is_dir():
            raise NotADirectoryError(f"Search path is not a directory: {search_path}")

    def find_files(self) -> List[Path]:
        """Find all files modified within the date range.

        Returns:
            List of Path objects for files matching the criteria

        Raises:
            PermissionError: If access to directory is denied
        """
        matching_files: List[Path] = []

        try:
            if self.recursive:
                search_pattern = "**/*" if self.file_pattern is None else f"**/{self.file_pattern}"
                files = self.search_path.glob(search_pattern)
            else:
                search_pattern = "*" if self.file_pattern is None else self.file_pattern
                files = self.search_path.glob(search_pattern)

            for file_path in files:
                if file_path.is_file():
                    try:
                        modified_time = datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        )
                        if self.start_date <= modified_time <= self.end_date:
                            matching_files.append(file_path)
                    except (OSError, PermissionError) as e:
                        logger.warning(
                            f"Cannot access file {file_path}: {e}",
                            extra={"file_path": str(file_path)},
                        )

        except PermissionError as e:
            logger.error(
                f"Permission denied accessing directory: {self.search_path}",
                extra={"path": str(self.search_path)},
            )
            raise

        logger.info(
            f"Found {len(matching_files)} files in date range",
            extra={
                "file_count": len(matching_files),
                "start_date": self.start_date.isoformat(),
                "end_date": self.end_date.isoformat(),
            },
        )

        return matching_files

    def format_results(self, files: List[Path]) -> str:
        """Format file list as a readable string.

        Args:
            files: List of file paths to format

        Returns:
            Formatted string with file information
        """
        if not files:
            return "No files found in the specified date range."

        result_lines = [f"Found {len(files)} file(s) modified between"]
        result_lines.append(f"  Start: {self.start_date.strftime('%Y-%m-%d %H:%M:%S')}")
        result_lines.append(f"  End: {self.end_date.strftime('%Y-%m-%d %H:%M:%S')}")
        result_lines.append("")
        result_lines.append("Files:")

        for file_path in sorted(files):
            try:
                modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                size = file_path.stat().st_size
                result_lines.append(
                    f"  {file_path} | "
                    f"Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')} | "
                    f"Size: {size:,} bytes"
                )
            except (OSError, PermissionError):
                result_lines.append(f"  {file_path} | (Unable to read metadata)")

        return "\n".join(result_lines)


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


def parse_date(date_string: str) -> datetime:
    """Parse date string into datetime object.

    Supports formats: YYYY-MM-DD, YYYY-MM-DD HH:MM:SS

    Args:
        date_string: Date string to parse

    Returns:
        Datetime object

    Raises:
        ValueError: If date string format is invalid
    """
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue

    raise ValueError(
        f"Invalid date format: {date_string}. "
        f"Expected formats: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
    )


def main() -> int:
    """Main entry point for the script.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        description="Find files modified within a specific date range"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="Start date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        required=True,
        help="End date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)",
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Directory path to search (default: current directory)",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Disable recursive directory search",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default=None,
        help="File pattern to match (e.g., '*.txt', '*.py')",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file (YAML)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path to save results",
    )

    args = parser.parse_args()

    try:
        start_date = parse_date(args.start_date)
        end_date = parse_date(args.end_date)

        search_path = Path(args.path).expanduser().resolve()
        recursive = not args.no_recursive
        file_pattern = args.pattern

        if args.config:
            config = load_config(Path(args.config))
            if "search_path" in config:
                search_path = Path(config["search_path"]).expanduser().resolve()
            if "recursive" in config:
                recursive = config["recursive"]
            if "file_pattern" in config:
                file_pattern = config.get("file_pattern")

        finder = DateRangeFileFinder(
            start_date=start_date,
            end_date=end_date,
            search_path=search_path,
            recursive=recursive,
            file_pattern=file_pattern,
        )

        files = finder.find_files()
        results = finder.format_results(files)

        print(results)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(results)
            logger.info(f"Results saved to {output_path}")

        return 0

    except (ValueError, FileNotFoundError, NotADirectoryError, PermissionError) as e:
        logger.error(f"Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
