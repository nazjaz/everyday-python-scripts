"""Multi-Attribute File Finder - CLI tool for finding files by attribute combinations.

This module provides a command-line tool for finding files matching multiple
attribute combinations such as large old files, small new files, or executable
documents.
"""

import argparse
import fnmatch
import json
import logging
import logging.handlers
import os
import re
import stat
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AttributeMatcher:
    """Matches files against multiple attribute combinations."""

    def __init__(self, config: Dict) -> None:
        """Initialize AttributeMatcher.

        Args:
            config: Configuration dictionary containing attribute settings.
        """
        self.config = config
        self.attribute_config = config.get("attributes", {})
        self.combination_config = config.get("combinations", [])

    def check_size(self, file_path: Path, size_criteria: Dict) -> bool:
        """Check if file matches size criteria.

        Args:
            file_path: Path to file to check.
            size_criteria: Size criteria dictionary.

        Returns:
            True if file matches size criteria, False otherwise.
        """
        try:
            file_size = file_path.stat().st_size
        except (OSError, PermissionError):
            return False

        # Check minimum size
        min_size = size_criteria.get("min_bytes")
        if min_size is not None and file_size < min_size:
            return False

        # Check maximum size
        max_size = size_criteria.get("max_bytes")
        if max_size is not None and file_size > max_size:
            return False

        # Check size categories
        size_categories = size_criteria.get("categories", [])
        if size_categories:
            category = self._categorize_size(file_size)
            if category not in size_categories:
                return False

        return True

    def _categorize_size(self, size: int) -> str:
        """Categorize file size.

        Args:
            size: File size in bytes.

        Returns:
            Size category string.
        """
        if size == 0:
            return "empty"
        elif size < 1024:  # < 1 KB
            return "tiny"
        elif size < 1024 * 1024:  # < 1 MB
            return "small"
        elif size < 10 * 1024 * 1024:  # < 10 MB
            return "medium"
        elif size < 100 * 1024 * 1024:  # < 100 MB
            return "large"
        else:
            return "very_large"

    def check_age(self, file_path: Path, age_criteria: Dict) -> bool:
        """Check if file matches age criteria.

        Args:
            file_path: Path to file to check.
            age_criteria: Age criteria dictionary.

        Returns:
            True if file matches age criteria, False otherwise.
        """
        try:
            stat_info = file_path.stat()
        except (OSError, PermissionError):
            return False

        now = datetime.now()

        # Check modification date
        if "modified" in age_criteria:
            mod_time = datetime.fromtimestamp(stat_info.st_mtime)
            mod_criteria = age_criteria["modified"]

            if "days_ago_min" in mod_criteria:
                min_days = mod_criteria["days_ago_min"]
                if (now - mod_time).days < min_days:
                    return False

            if "days_ago_max" in mod_criteria:
                max_days = mod_criteria["days_ago_max"]
                if (now - mod_time).days > max_days:
                    return False

            if "after" in mod_criteria:
                after_date = self._parse_date_spec(mod_criteria["after"], now)
                if mod_time < after_date:
                    return False

            if "before" in mod_criteria:
                before_date = self._parse_date_spec(mod_criteria["before"], now)
                if mod_time > before_date:
                    return False

        # Check creation date
        if "created" in age_criteria:
            try:
                created_time = datetime.fromtimestamp(stat_info.st_ctime)
            except (OSError, AttributeError):
                created_time = datetime.fromtimestamp(stat_info.st_mtime)

            created_criteria = age_criteria["created"]

            if "days_ago_min" in created_criteria:
                min_days = created_criteria["days_ago_min"]
                if (now - created_time).days < min_days:
                    return False

            if "days_ago_max" in created_criteria:
                max_days = created_criteria["days_ago_max"]
                if (now - created_time).days > max_days:
                    return False

        # Check age categories
        age_categories = age_criteria.get("categories", [])
        if age_categories:
            mod_time = datetime.fromtimestamp(stat_info.st_mtime)
            days_old = (now - mod_time).days
            category = self._categorize_age(days_old)
            if category not in age_categories:
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

        # Try relative format
        relative_match = re.match(
            r"(\d+)\s*(day|days|week|weeks|month|months|year|years)\s*ago",
            date_spec.lower(),
        )
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

        return reference

    def _categorize_age(self, days_old: int) -> str:
        """Categorize file age.

        Args:
            days_old: Number of days since last modification.

        Returns:
            Age category string.
        """
        if days_old <= 7:
            return "new"
        elif days_old <= 30:
            return "recent"
        elif days_old <= 90:
            return "moderate"
        elif days_old <= 365:
            return "old"
        else:
            return "very_old"

    def check_type(self, file_path: Path, type_criteria: Dict) -> bool:
        """Check if file matches type criteria.

        Args:
            file_path: Path to file to check.
            type_criteria: Type criteria dictionary.

        Returns:
            True if file matches type criteria, False otherwise.
        """
        file_ext = file_path.suffix.lower()
        file_name = file_path.name.lower()

        # Check extensions
        extensions = type_criteria.get("extensions", [])
        if extensions:
            matches = False
            for ext in extensions:
                if file_ext == ext.lower() or file_name.endswith(ext.lower()):
                    matches = True
                    break
            if not matches:
                return False

        # Check excluded extensions
        exclude_extensions = type_criteria.get("exclude_extensions", [])
        if exclude_extensions:
            for ext in exclude_extensions:
                if file_ext == ext.lower() or file_name.endswith(ext.lower()):
                    return False

        # Check file type categories
        type_categories = type_criteria.get("categories", [])
        if type_categories:
            file_category = self._categorize_file_type(file_ext)
            if file_category not in type_categories:
                return False

        # Check executable
        if type_criteria.get("executable", False):
            try:
                file_stat = file_path.stat()
                is_executable = bool(file_stat.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
                if not is_executable:
                    return False
            except (OSError, PermissionError):
                return False

        return True

    def _categorize_file_type(self, extension: str) -> str:
        """Categorize file by extension.

        Args:
            extension: File extension.

        Returns:
            File type category.
        """
        type_mapping = {
            "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
            "document": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".pages"],
            "spreadsheet": [".xls", ".xlsx", ".csv", ".ods", ".numbers"],
            "presentation": [".ppt", ".pptx", ".key"],
            "video": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"],
            "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
            "archive": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
            "code": [".py", ".js", ".java", ".cpp", ".c", ".html", ".css", ".xml"],
            "executable": [".exe", ".app", ".deb", ".rpm", ".dmg", ".bin"],
        }

        for file_type, extensions in type_mapping.items():
            if extension in extensions:
                return file_type

        return "other"

    def check_filename(self, file_path: Path, filename_criteria: Dict) -> bool:
        """Check if file matches filename criteria.

        Args:
            file_path: Path to file to check.
            filename_criteria: Filename criteria dictionary.

        Returns:
            True if file matches filename criteria, False otherwise.
        """
        file_name = file_path.name

        # Check glob patterns
        glob_patterns = filename_criteria.get("glob", [])
        if glob_patterns:
            matches = False
            for pattern in glob_patterns:
                if fnmatch.fnmatch(file_name, pattern):
                    matches = True
                    break
            if not matches:
                return False

        # Check regex patterns
        regex_patterns = filename_criteria.get("regex", [])
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
        contains_patterns = filename_criteria.get("contains", [])
        if contains_patterns:
            matches = False
            for pattern in contains_patterns:
                if pattern.lower() in file_name.lower():
                    matches = True
                    break
            if not matches:
                return False

        return True

    def match_combination(self, file_path: Path, combination: Dict) -> bool:
        """Check if file matches a specific attribute combination.

        Args:
            file_path: Path to file to check.
            combination: Combination dictionary with attribute criteria.

        Returns:
            True if file matches all criteria in combination, False otherwise.
        """
        # Check size
        if "size" in combination:
            if not self.check_size(file_path, combination["size"]):
                return False

        # Check age
        if "age" in combination:
            if not self.check_age(file_path, combination["age"]):
                return False

        # Check type
        if "type" in combination:
            if not self.check_type(file_path, combination["type"]):
                return False

        # Check filename
        if "filename" in combination:
            if not self.check_filename(file_path, combination["filename"]):
                return False

        return True

    def match_file(self, file_path: Path) -> List[str]:
        """Check which combinations a file matches.

        Args:
            file_path: Path to file to check.

        Returns:
            List of combination names that the file matches.
        """
        matching_combinations = []

        for combination in self.combination_config:
            combination_name = combination.get("name", "unnamed")
            if self.match_combination(file_path, combination):
                matching_combinations.append(combination_name)

        return matching_combinations


class MultiAttributeFileFinder:
    """Finds files matching multiple attribute combinations."""

    def __init__(self, config: Dict) -> None:
        """Initialize MultiAttributeFileFinder.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.search_config = config.get("search", {})
        self.output_config = config.get("output", {})

        # Setup logging
        self._setup_logging()

        # Initialize matcher
        self.matcher = AttributeMatcher(config)

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

    def find_files(self, search_dir: Path) -> Dict[str, List[Dict]]:
        """Find files matching attribute combinations.

        Args:
            search_dir: Directory to search in.

        Returns:
            Dictionary mapping combination names to lists of matching files.
        """
        results = defaultdict(list)

        if not search_dir.exists():
            logger.error(f"Search directory does not exist: {search_dir}")
            return dict(results)

        logger.info(f"Searching in directory: {search_dir}")

        try:
            for root, dirs, filenames in os.walk(search_dir):
                # Filter out excluded directories
                dirs[:] = [
                    d
                    for d in dirs
                    if not self.should_exclude_directory(Path(root) / d)
                ]

                for filename in filenames:
                    file_path = Path(root) / filename

                    try:
                        matching_combinations = self.matcher.match_file(file_path)

                        if matching_combinations:
                            stat_info = file_path.stat()
                            file_info = {
                                "path": str(file_path),
                                "name": filename,
                                "size": stat_info.st_size,
                                "modified": datetime.fromtimestamp(
                                    stat_info.st_mtime
                                ).isoformat(),
                                "extension": file_path.suffix,
                            }

                            for combination_name in matching_combinations:
                                results[combination_name].append(file_info)

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

        logger.info(f"Found files matching {len(results)} combinations")
        return dict(results)

    def format_output(
        self, results: Dict[str, List[Dict]], format_type: str = "text"
    ) -> str:
        """Format search results for output.

        Args:
            results: Dictionary of combination names to file lists.
            format_type: Output format (text, json, csv).

        Returns:
            Formatted output string.
        """
        if format_type == "json":
            return json.dumps(results, indent=2)

        elif format_type == "csv":
            import csv
            from io import StringIO

            output = StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow(["Combination", "Path", "Name", "Size", "Modified", "Extension"])

            # Data
            for combination_name, files in results.items():
                for file_info in files:
                    writer.writerow(
                        [
                            combination_name,
                            file_info["path"],
                            file_info["name"],
                            file_info["size"],
                            file_info["modified"],
                            file_info["extension"],
                        ]
                    )

            return output.getvalue()

        else:  # text format
            lines = []
            lines.append("=" * 80)
            lines.append("Multi-Attribute File Search Results")
            lines.append("=" * 80)
            lines.append("")

            total_files = sum(len(files) for files in results.values())
            lines.append(f"Total files found: {total_files}")
            lines.append(f"Combinations matched: {len(results)}")
            lines.append("")

            for combination_name, files in sorted(results.items()):
                lines.append(f"Combination: {combination_name}")
                lines.append(f"Files matched: {len(files)}")
                lines.append("-" * 80)

                for file_info in files[:20]:  # Limit to 20 per combination
                    size_str = self._format_size(file_info["size"])
                    lines.append(
                        f"  {file_info['path']:<50s} {size_str:>10s} "
                        f"{file_info['modified'][:10]}"
                    )

                if len(files) > 20:
                    lines.append(f"  ... and {len(files) - 20} more files")

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
        description="Find files matching multiple attribute combinations"
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

    finder = MultiAttributeFileFinder(config)

    # Get search directory
    search_dir = Path(config.get("search", {}).get("directory", "."))

    # Find files
    results = finder.find_files(search_dir)

    # Determine output format
    output_format = args.format or config.get("output", {}).get("format", "text")

    # Format output
    output = finder.format_output(results, format_type=output_format)

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
