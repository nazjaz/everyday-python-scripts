"""Directory Statistics - CLI tool for generating comprehensive directory statistics.

This module provides a command-line tool for analyzing directories and generating
comprehensive statistics including file counts by type, total sizes, oldest and
newest files, and storage breakdown.
"""

import argparse
import csv
import json
import logging
import logging.handlers
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DirectoryStatistics:
    """Generates comprehensive directory statistics."""

    def __init__(self, config: Dict) -> None:
        """Initialize DirectoryStatistics.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.file_type_categories = config.get("file_type_categories", {})
        self.exclude_patterns = [
            re.compile(pattern) for pattern in config.get("exclude_patterns", [])
        ]
        self.exclude_directories = [
            re.compile(pattern) for pattern in config.get("exclude_directories", [])
        ]
        self.options = config.get("options", {})

        # Build extension to category mapping
        self.extension_to_category = {}
        for category, category_info in self.file_type_categories.items():
            for ext in category_info.get("extensions", []):
                self.extension_to_category[ext.lower()] = category

    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from analysis.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file should be excluded, False otherwise.
        """
        filename = file_path.name

        # Check hidden files
        if not self.options.get("include_hidden", False) and filename.startswith("."):
            return True

        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if pattern.search(filename):
                return True

        # Check file size limits
        try:
            file_size = file_path.stat().st_size

            if not self.options.get("include_empty", True) and file_size == 0:
                return True

            min_size = self.options.get("min_file_size", 0)
            if min_size > 0 and file_size < min_size:
                return True

            max_size = self.options.get("max_file_size", 0)
            if max_size > 0 and file_size > max_size:
                return True
        except (OSError, IOError):
            return True

        return False

    def should_exclude_directory(self, dir_path: Path) -> bool:
        """Check if directory should be excluded from analysis.

        Args:
            dir_path: Path to directory to check.

        Returns:
            True if directory should be excluded, False otherwise.
        """
        dirname = dir_path.name

        for pattern in self.exclude_directories:
            if pattern.search(dirname):
                return True

        return False

    def get_file_category(self, file_path: Path) -> str:
        """Get category for a file based on extension.

        Args:
            file_path: Path to file.

        Returns:
            Category name.
        """
        ext = file_path.suffix.lower().lstrip(".")
        return self.extension_to_category.get(ext, "other")

    def analyze_directory(
        self, directory: Path, recursive: bool = True
    ) -> Dict:
        """Analyze a directory and generate statistics.

        Args:
            directory: Directory to analyze.
            recursive: Whether to analyze recursively.

        Returns:
            Dictionary with statistics.
        """
        directory = directory.resolve()

        if not directory.exists() or not directory.is_dir():
            logger.warning(f"Directory does not exist or is not a directory: {directory}")
            return self._empty_statistics()

        stats = {
            "directory": str(directory),
            "analyzed_at": datetime.now().isoformat(),
            "recursive": recursive,
            "total_files": 0,
            "total_directories": 0,
            "total_size": 0,
            "file_types": defaultdict(lambda: {"count": 0, "size": 0}),
            "extensions": defaultdict(lambda: {"count": 0, "size": 0}),
            "categories": defaultdict(lambda: {"count": 0, "size": 0, "name": ""}),
            "files": [],
            "oldest_file": None,
            "newest_file": None,
            "largest_file": None,
        }

        # Find all files
        if recursive:
            file_paths = directory.rglob("*")
            dir_paths = [p for p in directory.rglob("*") if p.is_dir()]
        else:
            file_paths = directory.glob("*")
            dir_paths = [p for p in directory.glob("*") if p.is_dir()]

        # Filter directories
        dir_paths = [
            d for d in dir_paths if not self.should_exclude_directory(d)
        ]
        stats["total_directories"] = len(dir_paths)

        # Process files
        for file_path in file_paths:
            if not file_path.is_file():
                continue

            if self.should_exclude_file(file_path):
                continue

            try:
                stat = file_path.stat()
                file_size = stat.st_size
                modified_time = datetime.fromtimestamp(stat.st_mtime)
                created_time = datetime.fromtimestamp(stat.st_ctime)

                # Update totals
                stats["total_files"] += 1
                stats["total_size"] += file_size

                # Get file info
                ext = file_path.suffix.lower().lstrip(".") or "no_extension"
                category = self.get_file_category(file_path)

                file_info = {
                    "path": str(file_path),
                    "name": file_path.name,
                    "size": file_size,
                    "extension": ext,
                    "category": category,
                    "modified": modified_time.isoformat(),
                    "created": created_time.isoformat(),
                }

                stats["files"].append(file_info)

                # Update type statistics
                stats["file_types"][ext]["count"] += 1
                stats["file_types"][ext]["size"] += file_size

                # Update category statistics
                category_name = self.file_type_categories.get(category, {}).get(
                    "name", category.title()
                )
                stats["categories"][category]["count"] += 1
                stats["categories"][category]["size"] += file_size
                stats["categories"][category]["name"] = category_name

                # Track oldest/newest/largest
                if (
                    stats["oldest_file"] is None
                    or modified_time < datetime.fromisoformat(stats["oldest_file"]["modified"])
                ):
                    stats["oldest_file"] = file_info

                if (
                    stats["newest_file"] is None
                    or modified_time > datetime.fromisoformat(stats["newest_file"]["modified"])
                ):
                    stats["newest_file"] = file_info

                if (
                    stats["largest_file"] is None
                    or file_size > stats["largest_file"]["size"]
                ):
                    stats["largest_file"] = file_info

            except (OSError, IOError) as e:
                logger.error(f"Error processing {file_path}: {e}")

        # Convert defaultdicts to regular dicts for JSON serialization
        stats["file_types"] = dict(stats["file_types"])
        stats["extensions"] = dict(stats["extensions"])
        stats["categories"] = dict(stats["categories"])

        return stats

    def _empty_statistics(self) -> Dict:
        """Return empty statistics structure.

        Returns:
            Empty statistics dictionary.
        """
        return {
            "directory": "",
            "analyzed_at": datetime.now().isoformat(),
            "recursive": False,
            "total_files": 0,
            "total_directories": 0,
            "total_size": 0,
            "file_types": {},
            "extensions": {},
            "categories": {},
            "files": [],
            "oldest_file": None,
            "newest_file": None,
            "largest_file": None,
        }

    def generate_report(
        self, stats: Dict, output_path: Path, report_format: str = "json"
    ) -> None:
        """Generate statistics report.

        Args:
            stats: Statistics dictionary.
            output_path: Path where report will be saved.
            report_format: Report format (json, txt, csv).
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if report_format.lower() == "json":
            self._generate_json_report(stats, output_path)
        elif report_format.lower() == "txt":
            self._generate_txt_report(stats, output_path)
        elif report_format.lower() == "csv":
            self._generate_csv_report(stats, output_path)
        else:
            raise ValueError(f"Unsupported report format: {report_format}")

        logger.info(f"Report generated: {output_path}")

    def _generate_json_report(self, stats: Dict, output_path: Path) -> None:
        """Generate JSON report."""
        # Add top files lists
        top_largest_count = self.options.get("top_largest_count", 10)
        top_oldest_count = self.options.get("top_oldest_count", 10)
        top_newest_count = self.options.get("top_newest_count", 10)

        files = stats["files"]
        files_by_size = sorted(files, key=lambda f: f["size"], reverse=True)
        files_by_modified = sorted(
            files, key=lambda f: f["modified"], reverse=False
        )

        report = {
            **stats,
            "summary": {
                "total_files": stats["total_files"],
                "total_directories": stats["total_directories"],
                "total_size": stats["total_size"],
                "total_size_mb": stats["total_size"] / (1024 * 1024),
                "total_size_gb": stats["total_size"] / (1024 * 1024 * 1024),
            },
            "top_largest_files": files_by_size[:top_largest_count],
            "top_oldest_files": files_by_modified[:top_oldest_count],
            "top_newest_files": sorted(
                files, key=lambda f: f["modified"], reverse=True
            )[:top_newest_count],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def _generate_txt_report(self, stats: Dict, output_path: Path) -> None:
        """Generate text report."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("DIRECTORY STATISTICS REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Directory: {stats['directory']}\n")
            f.write(f"Analyzed: {stats['analyzed_at']}\n")
            f.write(f"Recursive: {stats['recursive']}\n\n")

            # Summary
            f.write("SUMMARY\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Files: {stats['total_files']:,}\n")
            f.write(f"Total Directories: {stats['total_directories']:,}\n")
            f.write(f"Total Size: {self._format_size(stats['total_size'])}\n\n")

            # Categories
            f.write("STORAGE BREAKDOWN BY CATEGORY\n")
            f.write("-" * 80 + "\n")
            categories_sorted = sorted(
                stats["categories"].items(),
                key=lambda x: x[1]["size"],
                reverse=True,
            )
            for category, info in categories_sorted:
                percentage = (
                    (info["size"] / stats["total_size"] * 100)
                    if stats["total_size"] > 0
                    else 0
                )
                f.write(
                    f"{info['name']:20s} {info['count']:6,} files  "
                    f"{self._format_size(info['size']):>12s}  ({percentage:5.1f}%)\n"
                )
            f.write("\n")

            # File types
            f.write("TOP FILE TYPES BY COUNT\n")
            f.write("-" * 80 + "\n")
            types_sorted = sorted(
                stats["file_types"].items(),
                key=lambda x: x[1]["count"],
                reverse=True,
            )[:20]
            for ext, info in types_sorted:
                f.write(
                    f".{ext:15s} {info['count']:6,} files  "
                    f"{self._format_size(info['size']):>12s}\n"
                )
            f.write("\n")

            # Oldest/Newest/Largest
            if stats["oldest_file"]:
                f.write("OLDEST FILE\n")
                f.write("-" * 80 + "\n")
                f.write(f"Path: {stats['oldest_file']['path']}\n")
                f.write(f"Modified: {stats['oldest_file']['modified']}\n")
                f.write(f"Size: {self._format_size(stats['oldest_file']['size'])}\n\n")

            if stats["newest_file"]:
                f.write("NEWEST FILE\n")
                f.write("-" * 80 + "\n")
                f.write(f"Path: {stats['newest_file']['path']}\n")
                f.write(f"Modified: {stats['newest_file']['modified']}\n")
                f.write(f"Size: {self._format_size(stats['newest_file']['size'])}\n\n")

            if stats["largest_file"]:
                f.write("LARGEST FILE\n")
                f.write("-" * 80 + "\n")
                f.write(f"Path: {stats['largest_file']['path']}\n")
                f.write(f"Size: {self._format_size(stats['largest_file']['size'])}\n")
                f.write(f"Modified: {stats['largest_file']['modified']}\n\n")

            # Top largest files
            top_count = self.options.get("top_largest_count", 10)
            files_sorted = sorted(
                stats["files"], key=lambda f: f["size"], reverse=True
            )[:top_count]
            if files_sorted:
                f.write(f"TOP {top_count} LARGEST FILES\n")
                f.write("-" * 80 + "\n")
                for i, file_info in enumerate(files_sorted, 1):
                    f.write(
                        f"{i:2d}. {self._format_size(file_info['size']):>12s}  "
                        f"{file_info['path']}\n"
                    )

    def _generate_csv_report(self, stats: Dict, output_path: Path) -> None:
        """Generate CSV report."""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Summary
            writer.writerow(["Statistic", "Value"])
            writer.writerow(["Directory", stats["directory"]])
            writer.writerow(["Analyzed At", stats["analyzed_at"]])
            writer.writerow(["Total Files", stats["total_files"]])
            writer.writerow(["Total Directories", stats["total_directories"]])
            writer.writerow(["Total Size (bytes)", stats["total_size"]])
            writer.writerow([])

            # Categories
            writer.writerow(["Category", "Count", "Size (bytes)", "Percentage"])
            categories_sorted = sorted(
                stats["categories"].items(),
                key=lambda x: x[1]["size"],
                reverse=True,
            )
            for category, info in categories_sorted:
                percentage = (
                    (info["size"] / stats["total_size"] * 100)
                    if stats["total_size"] > 0
                    else 0
                )
                writer.writerow(
                    [
                        info["name"],
                        info["count"],
                        info["size"],
                        f"{percentage:.2f}%",
                    ]
                )
            writer.writerow([])

            # File types
            writer.writerow(["Extension", "Count", "Size (bytes)"])
            types_sorted = sorted(
                stats["file_types"].items(),
                key=lambda x: x[1]["count"],
                reverse=True,
            )
            for ext, info in types_sorted:
                writer.writerow([f".{ext}", info["count"], info["size"]])

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


def setup_logging(config: Dict) -> None:
    """Configure logging based on config file.

    Args:
        config: Configuration dictionary with logging settings.
    """
    log_config = config.get("logging", {})
    log_level = os.getenv("LOG_LEVEL", log_config.get("level", "INFO"))
    log_file = log_config.get("file", "logs/directory_statistics.log")
    max_bytes = log_config.get("max_bytes", 10485760)
    backup_count = log_config.get("backup_count", 5)
    log_format = log_config.get(
        "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    handler.setFormatter(logging.Formatter(log_format))

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.addHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)


def load_config(config_path: Optional[Path] = None) -> Dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. Defaults to config.yaml in project root.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file does not exist.
        yaml.YAMLError: If config file is invalid.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive directory statistics"
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=Path,
        help="Directory to analyze (overrides config)",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Analyze directories recursively (default: true)",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Do not analyze directories recursively",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output report file path (overrides config)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "txt", "csv"],
        help="Report format (overrides config)",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to configuration file",
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config)
        setup_logging(config)

        # Override config with command-line arguments
        if args.directory:
            config["analyze_directories"] = [str(args.directory)]
        if args.no_recursive:
            recursive = False
        else:
            recursive = args.recursive if args.recursive else True
        if args.output:
            config["report_file"] = str(args.output)
        if args.format:
            config["report_format"] = args.format

        # Get directories to analyze
        directories = [
            Path(d).resolve() for d in config.get("analyze_directories", [])
        ]

        if not directories:
            logger.error("No directories specified for analysis")
            print("Error: No directories specified for analysis")
            sys.exit(1)

        print(f"Analyzing directory: {directories[0]}")
        print(f"Recursive: {recursive}")
        print()

        # Analyze directory
        analyzer = DirectoryStatistics(config)
        stats = analyzer.analyze_directory(directories[0], recursive)

        # Generate report
        report_path = Path(config.get("report_file", "data/directory_stats.json"))
        report_format = config.get("report_format", "json")
        analyzer.generate_report(stats, report_path, report_format)

        # Print summary
        print("=" * 60)
        print("DIRECTORY STATISTICS SUMMARY")
        print("=" * 60)
        print(f"Total Files: {stats['total_files']:,}")
        print(f"Total Directories: {stats['total_directories']:,}")
        print(f"Total Size: {analyzer._format_size(stats['total_size'])}")
        print(f"Report saved to: {report_path}")
        print("=" * 60)

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Invalid configuration file: {e}")
        print(f"Error: Invalid configuration file: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
