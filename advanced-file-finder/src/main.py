"""Advanced File Finder - CLI tool for finding files with complex patterns.

This module provides a command-line tool for finding files matching complex
pattern combinations, supporting multiple criteria like size, date, type, and
content patterns with logical operators.
"""

import argparse
import fnmatch
import logging
import logging.handlers
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class PatternMatcher:
    """Matches files against complex pattern combinations."""

    def __init__(self, patterns: Dict) -> None:
        """Initialize PatternMatcher.

        Args:
            patterns: Pattern configuration dictionary.
        """
        self.patterns = patterns
        self.size_patterns = patterns.get("size", {})
        self.date_patterns = patterns.get("date", {})
        self.type_patterns = patterns.get("type", {})
        self.content_patterns = patterns.get("content", {})
        self.filename_patterns = patterns.get("filename", {})
        self.logic_operator = patterns.get("logic_operator", "AND").upper()

    def match_size(self, file_path: Path) -> bool:
        """Check if file matches size criteria.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file matches size criteria, False otherwise.
        """
        if not self.size_patterns:
            return True

        try:
            file_size = file_path.stat().st_size
        except (OSError, PermissionError):
            return False

        # Check minimum size
        min_size = self.size_patterns.get("min_bytes")
        if min_size is not None and file_size < min_size:
            return False

        # Check maximum size
        max_size = self.size_patterns.get("max_bytes")
        if max_size is not None and file_size > max_size:
            return False

        # Check size ranges
        size_ranges = self.size_patterns.get("ranges", [])
        if size_ranges:
            matches_range = False
            for size_range in size_ranges:
                range_min = size_range.get("min_bytes", 0)
                range_max = size_range.get("max_bytes", float("inf"))
                if range_min <= file_size <= range_max:
                    matches_range = True
                    break
            if not matches_range:
                return False

        return True

    def match_date(self, file_path: Path) -> bool:
        """Check if file matches date criteria.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file matches date criteria, False otherwise.
        """
        if not self.date_patterns:
            return True

        try:
            stat = file_path.stat()
        except (OSError, PermissionError):
            return False

        now = datetime.now()

        # Check modification date
        if "modified" in self.date_patterns:
            mod_date = datetime.fromtimestamp(stat.st_mtime)
            mod_pattern = self.date_patterns["modified"]

            if "after" in mod_pattern:
                after_date = self._parse_date_spec(mod_pattern["after"], now)
                if mod_date < after_date:
                    return False

            if "before" in mod_pattern:
                before_date = self._parse_date_spec(mod_pattern["before"], now)
                if mod_date > before_date:
                    return False

            if "days_ago" in mod_pattern:
                days = mod_pattern["days_ago"]
                target_date = now - timedelta(days=days)
                if mod_date > target_date:
                    return False

        # Check creation date
        if "created" in self.date_patterns:
            try:
                created_date = datetime.fromtimestamp(stat.st_ctime)
            except (OSError, AttributeError):
                created_date = datetime.fromtimestamp(stat.st_mtime)

            created_pattern = self.date_patterns["created"]

            if "after" in created_pattern:
                after_date = self._parse_date_spec(created_pattern["after"], now)
                if created_date < after_date:
                    return False

            if "before" in created_pattern:
                before_date = self._parse_date_spec(created_pattern["before"], now)
                if created_date > before_date:
                    return False

        # Check access date
        if "accessed" in self.date_patterns:
            access_date = datetime.fromtimestamp(stat.st_atime)
            access_pattern = self.date_patterns["accessed"]

            if "after" in access_pattern:
                after_date = self._parse_date_spec(access_pattern["after"], now)
                if access_date < after_date:
                    return False

            if "before" in access_pattern:
                before_date = self._parse_date_spec(access_pattern["before"], now)
                if access_date > before_date:
                    return False

        return True

    def _parse_date_spec(self, date_spec: str, reference: datetime) -> datetime:
        """Parse date specification string.

        Args:
            date_spec: Date specification (e.g., "2024-01-01", "30 days ago").
            reference: Reference datetime for relative dates.

        Returns:
            Parsed datetime.
        """
        # Try ISO format
        try:
            return datetime.fromisoformat(date_spec.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass

        # Try relative format (e.g., "30 days ago")
        relative_match = re.match(r"(\d+)\s*(day|days|week|weeks|month|months|year|years)\s*ago", date_spec.lower())
        if relative_match:
            value = int(relative_match.group(1))
            unit = relative_match.group(2)

            if unit in ["day", "days"]:
                return reference - timedelta(days=value)
            elif unit in ["week", "weeks"]:
                return reference - timedelta(weeks=value)
            elif unit in ["month", "months"]:
                return reference - timedelta(days=value * 30)
            elif unit in ["year", "years"]:
                return reference - timedelta(days=value * 365)

        # Default to reference date
        return reference

    def match_type(self, file_path: Path) -> bool:
        """Check if file matches type criteria.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file matches type criteria, False otherwise.
        """
        if not self.type_patterns:
            return True

        file_ext = file_path.suffix.lower()
        file_name = file_path.name.lower()

        # Check extensions
        extensions = self.type_patterns.get("extensions", [])
        if extensions:
            matches = False
            for ext in extensions:
                if file_ext == ext.lower() or file_name.endswith(ext.lower()):
                    matches = True
                    break
            if not matches:
                return False

        # Check excluded extensions
        exclude_extensions = self.type_patterns.get("exclude_extensions", [])
        if exclude_extensions:
            for ext in exclude_extensions:
                if file_ext == ext.lower() or file_name.endswith(ext.lower()):
                    return False

        # Check file type categories
        type_categories = self.type_patterns.get("categories", [])
        if type_categories:
            file_category = self._categorize_file_type(file_ext)
            if file_category not in type_categories:
                return False

        return True

    def _categorize_file_type(self, extension: str) -> str:
        """Categorize file by extension.

        Args:
            extension: File extension.

        Returns:
            File category.
        """
        type_mapping = {
            "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
            "document": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"],
            "spreadsheet": [".xls", ".xlsx", ".csv", ".ods"],
            "video": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv"],
            "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
            "archive": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
            "code": [".py", ".js", ".java", ".cpp", ".c", ".html", ".css"],
        }

        for category, extensions in type_mapping.items():
            if extension in extensions:
                return category

        return "other"

    def match_filename(self, file_path: Path) -> bool:
        """Check if file matches filename criteria.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file matches filename criteria, False otherwise.
        """
        if not self.filename_patterns:
            return True

        file_name = file_path.name

        # Check glob patterns
        glob_patterns = self.filename_patterns.get("glob", [])
        if glob_patterns:
            matches = False
            for pattern in glob_patterns:
                if fnmatch.fnmatch(file_name, pattern):
                    matches = True
                    break
            if not matches:
                return False

        # Check regex patterns
        regex_patterns = self.filename_patterns.get("regex", [])
        if regex_patterns:
            matches = False
            for pattern in regex_patterns:
                try:
                    if re.search(pattern, file_name):
                        matches = True
                        break
                except re.error:
                    logger.warning(f"Invalid regex pattern: {pattern}")
            if not matches:
                return False

        # Check contains patterns
        contains_patterns = self.filename_patterns.get("contains", [])
        if contains_patterns:
            matches = False
            for pattern in contains_patterns:
                if pattern.lower() in file_name.lower():
                    matches = True
                    break
            if not matches:
                return False

        return True

    def match_content(self, file_path: Path) -> bool:
        """Check if file matches content criteria.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file matches content criteria, False otherwise.
        """
        if not self.content_patterns:
            return True

        # Check if file is readable
        try:
            file_size = file_path.stat().st_size
            # Skip very large files
            max_size = self.content_patterns.get("max_file_size_bytes", 10 * 1024 * 1024)
            if file_size > max_size:
                return False
        except (OSError, PermissionError):
            return False

        # Check text patterns
        text_patterns = self.content_patterns.get("text", [])
        if text_patterns:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except (OSError, PermissionError, UnicodeDecodeError):
                return False

            matches = False
            for pattern in text_patterns:
                if pattern.lower() in content.lower():
                    matches = True
                    break
            if not matches:
                return False

        # Check regex patterns
        regex_patterns = self.content_patterns.get("regex", [])
        if regex_patterns:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except (OSError, PermissionError, UnicodeDecodeError):
                return False

            matches = False
            for pattern in regex_patterns:
                try:
                    if re.search(pattern, content, re.IGNORECASE):
                        matches = True
                        break
                except re.error:
                    logger.warning(f"Invalid regex pattern: {pattern}")
            if not matches:
                return False

        return True

    def match_file(self, file_path: Path) -> bool:
        """Check if file matches all pattern criteria.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file matches all criteria, False otherwise.
        """
        results = []

        # Check each pattern type
        if self.size_patterns:
            results.append(self.match_size(file_path))

        if self.date_patterns:
            results.append(self.match_date(file_path))

        if self.type_patterns:
            results.append(self.match_type(file_path))

        if self.filename_patterns:
            results.append(self.match_filename(file_path))

        if self.content_patterns:
            results.append(self.match_content(file_path))

        # Apply logic operator
        if not results:
            return True

        if self.logic_operator == "AND":
            return all(results)
        elif self.logic_operator == "OR":
            return any(results)
        else:
            # Default to AND
            return all(results)


class FileFinder:
    """Finds files matching complex pattern combinations."""

    def __init__(self, config: Dict) -> None:
        """Initialize FileFinder.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.search_config = config.get("search", {})
        self.pattern_config = config.get("patterns", {})
        self.output_config = config.get("output", {})

        # Setup logging
        self._setup_logging()

        # Initialize pattern matcher
        self.matcher = PatternMatcher(self.pattern_config)

    def _setup_logging(self) -> None:
        """Configure logging for the application."""
        log_level = self.config.get("logging", {}).get("level", "INFO")
        log_file = self.config.get("logging", {}).get("file", "logs/finder.log")

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

    def should_exclude_directory(self, dir_path: Path) -> bool:
        """Check if directory should be excluded from search.

        Args:
            dir_path: Path to directory to check.

        Returns:
            True if directory should be excluded, False otherwise.
        """
        exclude_dirs = self.search_config.get("exclude_directories", [])
        dir_name = dir_path.name

        for pattern in exclude_dirs:
            if fnmatch.fnmatch(dir_name, pattern):
                return True

        # Always exclude common system directories
        system_dirs = {".git", "__pycache__", ".pytest_cache", "node_modules"}
        return dir_name in system_dirs

    def find_files(self, search_dir: Path) -> List[Dict]:
        """Find files matching pattern criteria.

        Args:
            search_dir: Directory to search in.

        Returns:
            List of matching file dictionaries with metadata.
        """
        matches = []

        if not search_dir.exists():
            logger.error(f"Search directory does not exist: {search_dir}")
            return matches

        logger.info(f"Searching in directory: {search_dir}")

        try:
            for root, dirs, files in os.walk(search_dir):
                # Filter out excluded directories
                dirs[:] = [
                    d
                    for d in dirs
                    if not self.should_exclude_directory(Path(root) / d)
                ]

                for filename in files:
                    file_path = Path(root) / filename

                    try:
                        if self.matcher.match_file(file_path):
                            stat = file_path.stat()
                            matches.append(
                                {
                                    "path": str(file_path),
                                    "name": filename,
                                    "size": stat.st_size,
                                    "modified": datetime.fromtimestamp(
                                        stat.st_mtime
                                    ).isoformat(),
                                    "extension": file_path.suffix,
                                }
                            )

                    except (OSError, PermissionError) as e:
                        logger.debug(
                            f"Cannot access file {file_path}: {e}",
                            extra={"file_path": str(file_path)},
                        )
                        continue

        except (OSError, PermissionError) as e:
            logger.error(
                f"Cannot search directory {search_dir}: {e}",
                extra={"search_directory": str(search_dir), "error": str(e)},
            )

        logger.info(f"Found {len(matches)} matching files")
        return matches

    def format_output(self, matches: List[Dict], format_type: str = "text") -> str:
        """Format search results for output.

        Args:
            matches: List of matching file dictionaries.
            format_type: Output format (text, json, csv).

        Returns:
            Formatted output string.
        """
        if format_type == "json":
            import json
            return json.dumps(matches, indent=2)

        elif format_type == "csv":
            import csv
            from io import StringIO

            output = StringIO()
            if matches:
                writer = csv.DictWriter(
                    output, fieldnames=matches[0].keys()
                )
                writer.writeheader()
                writer.writerows(matches)
            return output.getvalue()

        else:  # text format
            lines = []
            lines.append("=" * 80)
            lines.append(f"File Search Results: {len(matches)} files found")
            lines.append("=" * 80)
            lines.append("")

            for match in matches:
                lines.append(f"Path: {match['path']}")
                lines.append(f"  Size: {self._format_size(match['size'])}")
                lines.append(f"  Modified: {match['modified']}")
                lines.append(f"  Extension: {match['extension']}")
                lines.append("")

            lines.append("=" * 80)
            return "\n".join(lines)

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
        description="Find files matching complex pattern combinations"
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
        "--directory",
        type=Path,
        help="Directory to search (overrides config)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["text", "json", "csv"],
        help="Output format (overrides config)",
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

    # Override search directory if provided
    if args.directory:
        config.setdefault("search", {})["directory"] = str(args.directory)

    finder = FileFinder(config)

    # Get search directory
    search_dir = Path(
        config.get("search", {}).get("directory", ".")
    )

    # Find files
    matches = finder.find_files(search_dir)

    # Determine output format
    output_format = args.format or config.get("output", {}).get("format", "text")

    # Format output
    output = finder.format_output(matches, format_type=output_format)

    # Output results
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, "w") as f:
                f.write(output)
            logger.info(f"Results written to: {args.output}")
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to write output: {e}")
            sys.exit(1)
    else:
        print(output)


if __name__ == "__main__":
    main()
