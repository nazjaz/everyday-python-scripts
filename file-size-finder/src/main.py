"""File Size Finder - Find files within specified size ranges.

This module provides functionality to scan directories and find files that
match specified size criteria, useful for identifying unusually large or
small files that may need attention.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FileSizeFinder:
    """Finds files within specified size ranges."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize FileSizeFinder with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.results = {
            "files_found": 0,
            "total_size": 0,
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
        if os.getenv("SEARCH_DIRECTORY"):
            config["search"]["directory"] = os.getenv("SEARCH_DIRECTORY")
        if os.getenv("MIN_SIZE"):
            config["size"]["min_bytes"] = self._parse_size(os.getenv("MIN_SIZE"))
        if os.getenv("MAX_SIZE"):
            config["size"]["max_bytes"] = self._parse_size(os.getenv("MAX_SIZE"))

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/file_size_finder.log")

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

    def _parse_size(self, size_str: str) -> int:
        """Parse size string to bytes.

        Args:
            size_str: Size string (e.g., "10MB", "1.5GB", "500KB").

        Returns:
            Size in bytes.

        Raises:
            ValueError: If size string format is invalid.
        """
        size_str = size_str.strip().upper()
        if not size_str:
            raise ValueError("Empty size string")

        # Extract number and unit
        unit = ""
        for u in ["KB", "MB", "GB", "TB"]:
            if size_str.endswith(u):
                unit = u
                break

        if unit:
            number_str = size_str[:-len(unit)]
        else:
            # Assume bytes if no unit
            number_str = size_str
            unit = "B"

        try:
            number = float(number_str)
        except ValueError:
            raise ValueError(f"Invalid number in size string: {size_str}")

        # Convert to bytes
        multipliers = {
            "B": 1,
            "KB": 1024,
            "MB": 1024 ** 2,
            "GB": 1024 ** 3,
            "TB": 1024 ** 4,
        }

        if unit not in multipliers:
            raise ValueError(f"Unknown size unit: {unit}")

        return int(number * multipliers[unit])

    def _format_size(self, size_bytes: int) -> str:
        """Format bytes to human-readable string.

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

    def _matches_size_criteria(self, file_size: int) -> bool:
        """Check if file size matches criteria.

        Args:
            file_size: File size in bytes.

        Returns:
            True if file matches size criteria, False otherwise.
        """
        size_config = self.config.get("size", {})
        min_bytes = size_config.get("min_bytes", 0)
        max_bytes = size_config.get("max_bytes", None)

        if file_size < min_bytes:
            return False

        if max_bytes is not None and file_size > max_bytes:
            return False

        return True

    def _should_skip_path(self, path: Path) -> bool:
        """Check if path should be skipped.

        Args:
            path: Path to check.

        Returns:
            True if path should be skipped, False otherwise.
        """
        skip_config = self.config.get("skip", {})
        skip_patterns = skip_config.get("patterns", [])
        skip_directories = skip_config.get("directories", [])

        path_str = str(path)

        # Check skip patterns
        for pattern in skip_patterns:
            if pattern in path_str:
                return True

        # Check skip directories
        for skip_dir in skip_directories:
            if skip_dir in path_str:
                return True

        # Check if path is in excluded list
        excluded = skip_config.get("excluded_paths", [])
        if path_str in excluded or str(path.resolve()) in excluded:
            return True

        return False

    def _should_include_extension(self, file_path: Path) -> bool:
        """Check if file extension should be included.

        Args:
            file_path: Path to file.

        Returns:
            True if extension should be included, False otherwise.
        """
        include_config = self.config.get("include", {})
        extensions = include_config.get("extensions", [])

        if not extensions:
            return True

        file_ext = file_path.suffix.lower()
        if not file_ext:
            return include_config.get("include_no_extension", False)

        return file_ext in [ext.lower() for ext in extensions]

    def find_files(self, directory: Optional[str] = None) -> List[Dict]:
        """Find files matching size criteria.

        Args:
            directory: Directory to search (default: from config).

        Returns:
            List of file dictionaries with path, size, and metadata.
        """
        search_config = self.config.get("search", {})
        search_dir = directory or search_config.get("directory", ".")

        if not os.path.exists(search_dir):
            raise FileNotFoundError(f"Directory not found: {search_dir}")

        if not os.path.isdir(search_dir):
            raise NotADirectoryError(f"Path is not a directory: {search_dir}")

        logger.info(f"Starting file search in: {search_dir}")

        files_found = []
        search_path = Path(search_dir).resolve()

        try:
            for root, dirs, files in os.walk(search_path):
                root_path = Path(root)

                # Skip directories based on configuration
                dirs[:] = [
                    d for d in dirs
                    if not self._should_skip_path(root_path / d)
                ]

                if self._should_skip_path(root_path):
                    continue

                self.results["directories_scanned"] += 1

                for file_name in files:
                    file_path = root_path / file_name

                    try:
                        # Skip if path matches skip criteria
                        if self._should_skip_path(file_path):
                            continue

                        # Check extension filter
                        if not self._should_include_extension(file_path):
                            continue

                        # Get file size
                        file_size = file_path.stat().st_size

                        # Check if size matches criteria
                        if self._matches_size_criteria(file_size):
                            file_info = {
                                "path": str(file_path),
                                "size": file_size,
                                "size_formatted": self._format_size(file_size),
                                "name": file_name,
                                "directory": str(root_path),
                                "extension": file_path.suffix.lower() or "no extension",
                            }

                            files_found.append(file_info)
                            self.results["files_found"] += 1
                            self.results["total_size"] += file_size

                    except (OSError, PermissionError) as e:
                        logger.warning(f"Error accessing file {file_path}: {e}")
                        self.results["errors"] += 1
                        continue

        except Exception as e:
            logger.error(f"Error during file search: {e}")
            self.results["errors"] += 1
            raise

        logger.info(f"File search completed. Found {len(files_found)} files")
        return files_found

    def generate_report(
        self, files: List[Dict], output_file: Optional[str] = None
    ) -> str:
        """Generate text report of found files.

        Args:
            files: List of file dictionaries.
            output_file: Optional path to save report file.

        Returns:
            Report text.
        """
        report_config = self.config.get("report", {})
        size_config = self.config.get("size", {})

        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("FILE SIZE FINDER REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Search criteria
        report_lines.append("SEARCH CRITERIA")
        report_lines.append("-" * 80)
        min_size = size_config.get("min_bytes", 0)
        max_size = size_config.get("max_bytes")
        report_lines.append(f"Minimum size: {self._format_size(min_size)}")
        if max_size:
            report_lines.append(f"Maximum size: {self._format_size(max_size)}")
        else:
            report_lines.append("Maximum size: No limit")
        report_lines.append("")

        # Statistics
        report_lines.append("STATISTICS")
        report_lines.append("-" * 80)
        report_lines.append(f"Files found: {self.results['files_found']}")
        report_lines.append(
            f"Total size: {self._format_size(self.results['total_size'])}"
        )
        report_lines.append(f"Directories scanned: {self.results['directories_scanned']}")
        report_lines.append(f"Errors encountered: {self.results['errors']}")
        report_lines.append("")

        # File list
        if report_config.get("sort_by_size", True):
            files = sorted(files, key=lambda x: x["size"], reverse=True)

        report_lines.append("FILES FOUND")
        report_lines.append("-" * 80)

        if not files:
            report_lines.append("No files found matching the criteria.")
        else:
            for i, file_info in enumerate(files, 1):
                report_lines.append(f"{i}. {file_info['name']}")
                report_lines.append(f"   Path: {file_info['path']}")
                report_lines.append(f"   Size: {file_info['size_formatted']}")
                report_lines.append(f"   Extension: {file_info['extension']}")
                report_lines.append("")

        report_text = "\n".join(report_lines)

        # Save to file if specified
        if output_file:
            output_path = Path(output_file)
            if not output_path.is_absolute():
                project_root = Path(__file__).parent.parent
                output_path = project_root / output_file

            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_text)

            logger.info(f"Report saved to: {output_path}")

        return report_text

    def print_summary(self, files: List[Dict]) -> None:
        """Print summary of found files to console.

        Args:
            files: List of file dictionaries.
        """
        print("\n" + "=" * 80)
        print("FILE SIZE FINDER SUMMARY")
        print("=" * 80)
        print(f"Files found: {self.results['files_found']}")
        print(f"Total size: {self._format_size(self.results['total_size'])}")
        print(f"Directories scanned: {self.results['directories_scanned']}")
        if self.results['errors'] > 0:
            print(f"Errors: {self.results['errors']}")

        if files:
            print("\nTop 10 largest files:")
            sorted_files = sorted(files, key=lambda x: x["size"], reverse=True)
            for i, file_info in enumerate(sorted_files[:10], 1):
                print(
                    f"  {i}. {file_info['name']} "
                    f"({file_info['size_formatted']})"
                )
        print("=" * 80 + "\n")


def main() -> int:
    """Main entry point for file size finder."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Find files within specified size ranges"
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
        "-m",
        "--min-size",
        help="Minimum file size (e.g., 10MB, 1GB)",
    )
    parser.add_argument(
        "-M",
        "--max-size",
        help="Maximum file size (e.g., 100MB, 5GB)",
    )
    parser.add_argument(
        "-r",
        "--report",
        help="Save report to file",
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Don't print summary to console",
    )

    args = parser.parse_args()

    try:
        finder = FileSizeFinder(config_path=args.config)

        # Override config with command-line arguments
        if args.min_size:
            finder.config["size"]["min_bytes"] = finder._parse_size(args.min_size)
        if args.max_size:
            finder.config["size"]["max_bytes"] = finder._parse_size(args.max_size)

        # Find files
        files = finder.find_files(directory=args.directory)

        # Print summary
        if not args.no_summary:
            finder.print_summary(files)

        # Generate report
        if args.report:
            report = finder.generate_report(files, output_file=args.report)
            print(f"\nReport saved to: {args.report}")
        elif finder.config.get("report", {}).get("auto_save", False):
            report_file = finder.config.get("report", {}).get("output_file", "logs/file_size_report.txt")
            report = finder.generate_report(files, output_file=report_file)
            print(f"\nReport saved to: {report_file}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration or directory error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Invalid size format: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
