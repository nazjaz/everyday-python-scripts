"""File Statistics Generator - Generate comprehensive file statistics.

This module provides functionality to generate file statistics including total count,
average size, most common extensions, and storage usage trends.
"""

import logging
import logging.handlers
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FileStatisticsGenerator:
    """Generates comprehensive file statistics."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize FileStatisticsGenerator with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.statistics: Dict[str, Any] = {}
        self.file_data: List[Dict[str, Any]] = []

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
            config["scan"]["directory"] = os.getenv("SCAN_DIRECTORY")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/statistics.log")

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
        """Check if file should be excluded from statistics.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file should be excluded, False otherwise.
        """
        exclude_config = self.config.get("scan", {}).get("exclude", {})
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

    def scan_files(
        self,
        directory: Optional[str] = None,
        recursive: bool = True,
    ) -> List[Dict[str, Any]]:
        """Scan directory and collect file information.

        Args:
            directory: Directory to scan (overrides config).
            recursive: Whether to search recursively.

        Returns:
            List of file information dictionaries.

        Raises:
            FileNotFoundError: If directory doesn't exist.
        """
        scan_config = self.config.get("scan", {})

        if directory:
            scan_dir = Path(directory)
        else:
            scan_dir = Path(scan_config.get("directory", "."))

        if not scan_dir.exists():
            raise FileNotFoundError(f"Directory does not exist: {scan_dir}")

        if not scan_dir.is_dir():
            raise ValueError(f"Path is not a directory: {scan_dir}")

        logger.info(f"Scanning files in: {scan_dir} (recursive={recursive})")

        self.file_data = []

        # Walk directory
        if recursive:
            iterator = scan_dir.rglob("*")
        else:
            iterator = scan_dir.glob("*")

        for item_path in iterator:
            if not item_path.is_file():
                continue

            # Check exclusions
            if self._is_excluded(item_path):
                continue

            try:
                stat_info = item_path.stat()
                file_info = {
                    "path": str(item_path),
                    "name": item_path.name,
                    "extension": item_path.suffix.lower() or ".no_extension",
                    "size": stat_info.st_size,
                    "modified_time": stat_info.st_mtime,
                    "modified_datetime": datetime.fromtimestamp(stat_info.st_mtime),
                    "created_time": stat_info.st_ctime if hasattr(stat_info, "st_ctime") else stat_info.st_mtime,
                    "created_datetime": datetime.fromtimestamp(
                        stat_info.st_ctime if hasattr(stat_info, "st_ctime") else stat_info.st_mtime
                    ),
                    "directory": str(item_path.parent),
                }
                self.file_data.append(file_info)

            except (OSError, PermissionError) as e:
                logger.warning(f"Could not get file info for {item_path}: {e}")

        logger.info(f"Scanned {len(self.file_data)} file(s)")
        return self.file_data

    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate comprehensive file statistics.

        Returns:
            Dictionary containing all calculated statistics.
        """
        if not self.file_data:
            raise ValueError("No file data available. Run scan_files() first.")

        logger.info("Calculating file statistics")

        # Basic statistics
        total_files = len(self.file_data)
        total_size = sum(f["size"] for f in self.file_data)
        average_size = total_size / total_files if total_files > 0 else 0

        # Size statistics
        sizes = [f["size"] for f in self.file_data]
        sizes.sort()
        median_size = sizes[len(sizes) // 2] if sizes else 0
        min_size = min(sizes) if sizes else 0
        max_size = max(sizes) if sizes else 0

        # Extension statistics
        extensions = [f["extension"] for f in self.file_data]
        extension_counts = Counter(extensions)
        most_common_extensions = extension_counts.most_common(
            self.config.get("statistics", {}).get("top_extensions", 10)
        )

        extension_sizes = defaultdict(int)
        for file_info in self.file_data:
            extension_sizes[file_info["extension"]] += file_info["size"]

        # Size distribution
        size_ranges = self._calculate_size_distribution(sizes)

        # Date-based trends
        date_trends = self._calculate_date_trends()

        # Directory statistics
        directory_stats = self._calculate_directory_statistics()

        # File age statistics
        age_statistics = self._calculate_age_statistics()

        self.statistics = {
            "summary": {
                "total_files": total_files,
                "total_size": total_size,
                "total_size_formatted": self._format_size(total_size),
                "average_size": average_size,
                "average_size_formatted": self._format_size(average_size),
                "median_size": median_size,
                "median_size_formatted": self._format_size(median_size),
                "min_size": min_size,
                "min_size_formatted": self._format_size(min_size),
                "max_size": max_size,
                "max_size_formatted": self._format_size(max_size),
            },
            "extensions": {
                "total_unique": len(extension_counts),
                "most_common": [
                    {
                        "extension": ext,
                        "count": count,
                        "percentage": (count / total_files * 100) if total_files > 0 else 0,
                        "total_size": extension_sizes[ext],
                        "total_size_formatted": self._format_size(extension_sizes[ext]),
                        "average_size": extension_sizes[ext] / count if count > 0 else 0,
                        "average_size_formatted": self._format_size(
                            extension_sizes[ext] / count if count > 0 else 0
                        ),
                    }
                    for ext, count in most_common_extensions
                ],
            },
            "size_distribution": size_ranges,
            "date_trends": date_trends,
            "directory_statistics": directory_stats,
            "age_statistics": age_statistics,
            "scan_timestamp": datetime.now().isoformat(),
        }

        logger.info("Statistics calculation complete")
        return self.statistics

    def _calculate_size_distribution(self, sizes: List[int]) -> List[Dict[str, Any]]:
        """Calculate distribution of files by size ranges.

        Args:
            sizes: List of file sizes in bytes.

        Returns:
            List of size range statistics.
        """
        ranges_config = self.config.get("statistics", {}).get("size_ranges", [
            {"name": "Tiny", "max": 1024},  # < 1 KB
            {"name": "Small", "max": 1024 * 1024},  # < 1 MB
            {"name": "Medium", "max": 10 * 1024 * 1024},  # < 10 MB
            {"name": "Large", "max": 100 * 1024 * 1024},  # < 100 MB
            {"name": "Very Large", "max": float("inf")},  # >= 100 MB
        ])

        distribution = []
        total_files = len(sizes)

        for i, range_config in enumerate(ranges_config):
            min_size = ranges_config[i - 1]["max"] if i > 0 else 0
            max_size = range_config["max"]

            matching_sizes = [s for s in sizes if min_size <= s < max_size]
            count = len(matching_sizes)
            total_size = sum(matching_sizes)

            distribution.append({
                "name": range_config["name"],
                "min_size": min_size,
                "max_size": max_size,
                "min_size_formatted": self._format_size(min_size),
                "max_size_formatted": self._format_size(max_size),
                "count": count,
                "percentage": (count / total_files * 100) if total_files > 0 else 0,
                "total_size": total_size,
                "total_size_formatted": self._format_size(total_size),
                "average_size": total_size / count if count > 0 else 0,
                "average_size_formatted": self._format_size(total_size / count if count > 0 else 0),
            })

        return distribution

    def _calculate_date_trends(self) -> Dict[str, Any]:
        """Calculate storage usage trends by date.

        Returns:
            Dictionary with date-based trend statistics.
        """
        if not self.file_data:
            return {}

        trends_config = self.config.get("statistics", {}).get("trends", {})
        group_by = trends_config.get("group_by", "month")  # day, week, month, year

        # Group files by date
        date_groups = defaultdict(lambda: {"count": 0, "size": 0})

        for file_info in self.file_data:
            mod_date = file_info["modified_datetime"]

            if group_by == "day":
                key = mod_date.strftime("%Y-%m-%d")
            elif group_by == "week":
                week_start = mod_date - timedelta(days=mod_date.weekday())
                key = week_start.strftime("%Y-W%W")
            elif group_by == "month":
                key = mod_date.strftime("%Y-%m")
            elif group_by == "year":
                key = mod_date.strftime("%Y")
            else:
                key = mod_date.strftime("%Y-%m")

            date_groups[key]["count"] += 1
            date_groups[key]["size"] += file_info["size"]

        # Convert to sorted list
        trends = sorted(
            [
                {
                    "period": period,
                    "count": data["count"],
                    "total_size": data["size"],
                    "total_size_formatted": self._format_size(data["size"]),
                }
                for period, data in date_groups.items()
            ],
            key=lambda x: x["period"],
        )

        return {
            "group_by": group_by,
            "periods": trends,
            "total_periods": len(trends),
        }

    def _calculate_directory_statistics(self) -> Dict[str, Any]:
        """Calculate statistics by directory.

        Returns:
            Dictionary with directory statistics.
        """
        if not self.file_data:
            return {}

        top_dirs = self.config.get("statistics", {}).get("top_directories", 10)

        dir_counts = Counter()
        dir_sizes = defaultdict(int)

        for file_info in self.file_data:
            dir_path = file_info["directory"]
            dir_counts[dir_path] += 1
            dir_sizes[dir_path] += file_info["size"]

        # Get top directories by file count
        top_by_count = [
            {
                "directory": dir_path,
                "count": count,
                "total_size": dir_sizes[dir_path],
                "total_size_formatted": self._format_size(dir_sizes[dir_path]),
            }
            for dir_path, count in dir_counts.most_common(top_dirs)
        ]

        # Get top directories by size
        top_by_size = sorted(
            [
                {
                    "directory": dir_path,
                    "count": dir_counts[dir_path],
                    "total_size": size,
                    "total_size_formatted": self._format_size(size),
                }
                for dir_path, size in dir_sizes.items()
            ],
            key=lambda x: x["total_size"],
            reverse=True,
        )[:top_dirs]

        return {
            "total_directories": len(dir_counts),
            "top_by_count": top_by_count,
            "top_by_size": top_by_size,
        }

    def _calculate_age_statistics(self) -> Dict[str, Any]:
        """Calculate file age statistics.

        Returns:
            Dictionary with age-based statistics.
        """
        if not self.file_data:
            return {}

        now = datetime.now()
        age_ranges = [
            {"name": "Very Recent", "max_days": 1},
            {"name": "Recent", "max_days": 7},
            {"name": "This Month", "max_days": 30},
            {"name": "This Year", "max_days": 365},
            {"name": "Old", "max_days": float("inf")},
        ]

        age_stats = []
        total_files = len(self.file_data)

        for i, age_range in enumerate(age_ranges):
            min_days = age_ranges[i - 1]["max_days"] if i > 0 else 0
            max_days = age_range["max_days"]

            matching_files = []
            for file_info in self.file_data:
                age_delta = now - file_info["modified_datetime"]
                age_days = age_delta.total_seconds() / 86400

                if min_days <= age_days < max_days:
                    matching_files.append(file_info)

            count = len(matching_files)
            total_size = sum(f["size"] for f in matching_files)

            age_stats.append({
                "name": age_range["name"],
                "min_days": min_days,
                "max_days": max_days,
                "count": count,
                "percentage": (count / total_files * 100) if total_files > 0 else 0,
                "total_size": total_size,
                "total_size_formatted": self._format_size(total_size),
            })

        return {
            "ranges": age_stats,
            "oldest_file": min(
                (f["modified_datetime"] for f in self.file_data),
                default=None,
            ),
            "newest_file": max(
                (f["modified_datetime"] for f in self.file_data),
                default=None,
            ),
        }

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes.

        Returns:
            Formatted size string.
        """
        for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def generate_report(self, output_file: Optional[str] = None, format: str = "text") -> str:
        """Generate text report of file statistics.

        Args:
            output_file: Path to output file (overrides config).
            format: Report format ("text" or "json").

        Returns:
            Report content as string.
        """
        if not self.statistics:
            raise ValueError("No statistics available. Run calculate_statistics() first.")

        if format == "json":
            import json

            report_content = json.dumps(self.statistics, indent=2, default=str)
        else:
            report_content = self._generate_text_report()

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

    def _generate_text_report(self) -> str:
        """Generate human-readable text report.

        Returns:
            Report content as string.
        """
        stats = self.statistics
        report_lines = []

        report_lines.append("=" * 80)
        report_lines.append("File Statistics Report")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {stats['scan_timestamp']}")
        report_lines.append("")

        # Summary
        summary = stats["summary"]
        report_lines.append("Summary Statistics")
        report_lines.append("-" * 80)
        report_lines.append(f"Total Files: {summary['total_files']:,}")
        report_lines.append(f"Total Size: {summary['total_size_formatted']}")
        report_lines.append(f"Average Size: {summary['average_size_formatted']}")
        report_lines.append(f"Median Size: {summary['median_size_formatted']}")
        report_lines.append(f"Min Size: {summary['min_size_formatted']}")
        report_lines.append(f"Max Size: {summary['max_size_formatted']}")
        report_lines.append("")

        # Extensions
        ext_stats = stats["extensions"]
        report_lines.append("Most Common Extensions")
        report_lines.append("-" * 80)
        report_lines.append(f"Total Unique Extensions: {ext_stats['total_unique']}")
        report_lines.append("")
        for ext_info in ext_stats["most_common"]:
            report_lines.append(
                f"  {ext_info['extension']:20s} "
                f"Count: {ext_info['count']:6,} "
                f"({ext_info['percentage']:5.1f}%) "
                f"Size: {ext_info['total_size_formatted']:>10s} "
                f"Avg: {ext_info['average_size_formatted']:>10s}"
            )
        report_lines.append("")

        # Size Distribution
        report_lines.append("Size Distribution")
        report_lines.append("-" * 80)
        for size_range in stats["size_distribution"]:
            report_lines.append(
                f"  {size_range['name']:15s} "
                f"({size_range['min_size_formatted']:>8s} - {size_range['max_size_formatted']:>8s}): "
                f"Count: {size_range['count']:6,} "
                f"({size_range['percentage']:5.1f}%) "
                f"Size: {size_range['total_size_formatted']:>10s}"
            )
        report_lines.append("")

        # Date Trends
        trends = stats["date_trends"]
        if trends and trends.get("periods"):
            report_lines.append(f"Storage Usage Trends (by {trends['group_by']})")
            report_lines.append("-" * 80)
            for period in trends["periods"][-12:]:  # Last 12 periods
                report_lines.append(
                    f"  {period['period']:15s} "
                    f"Files: {period['count']:6,} "
                    f"Size: {period['total_size_formatted']:>10s}"
                )
            report_lines.append("")

        # Directory Statistics
        dir_stats = stats["directory_statistics"]
        if dir_stats.get("top_by_size"):
            report_lines.append("Top Directories by Size")
            report_lines.append("-" * 80)
            for dir_info in dir_stats["top_by_size"][:10]:
                report_lines.append(
                    f"  {dir_info['directory'][:60]:60s} "
                    f"Files: {dir_info['count']:6,} "
                    f"Size: {dir_info['total_size_formatted']:>10s}"
                )
            report_lines.append("")

        # Age Statistics
        age_stats = stats["age_statistics"]
        if age_stats.get("ranges"):
            report_lines.append("File Age Distribution")
            report_lines.append("-" * 80)
            for age_range in age_stats["ranges"]:
                report_lines.append(
                    f"  {age_range['name']:20s} "
                    f"Count: {age_range['count']:6,} "
                    f"({age_range['percentage']:5.1f}%) "
                    f"Size: {age_range['total_size_formatted']:>10s}"
                )
            report_lines.append("")

        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    def get_statistics(self) -> Dict[str, Any]:
        """Get calculated statistics.

        Returns:
            Dictionary with all statistics.
        """
        return self.statistics.copy()


def main() -> int:
    """Main entry point for file statistics generator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate comprehensive file statistics"
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
        help="Directory to scan (overrides config)",
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
        "--format",
        choices=["text", "json"],
        default="text",
        help="Report format (default: text)",
    )

    args = parser.parse_args()

    try:
        generator = FileStatisticsGenerator(config_path=args.config)

        # Scan files
        generator.scan_files(
            directory=args.directory, recursive=not args.no_recursive
        )

        # Calculate statistics
        statistics = generator.calculate_statistics()

        # Generate report
        output_file = args.output or generator.config.get("report", {}).get("output_file")
        report_content = generator.generate_report(output_file=output_file, format=args.format)

        # Print summary
        print("\n" + "=" * 60)
        print("File Statistics Summary")
        print("=" * 60)
        summary = statistics["summary"]
        print(f"Total Files: {summary['total_files']:,}")
        print(f"Total Size: {summary['total_size_formatted']}")
        print(f"Average Size: {summary['average_size_formatted']}")
        print(f"Unique Extensions: {statistics['extensions']['total_unique']}")

        if output_file:
            print(f"\nReport saved to: {output_file}")

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
