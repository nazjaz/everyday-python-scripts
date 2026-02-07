"""File Size Analyzer - Generate detailed file size reports.

This module provides functionality to analyze file sizes, identify largest
files, calculate size distribution by type, and generate cleanup recommendations.
"""

import logging
import logging.handlers
import os
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FileSizeAnalyzer:
    """Analyzes file sizes and generates detailed reports."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize FileSizeAnalyzer with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.file_data: List[Dict[str, Any]] = []
        self.stats = {
            "total_files": 0,
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
        if os.getenv("SCAN_DIRECTORY"):
            config["analysis"]["scan_directory"] = os.getenv("SCAN_DIRECTORY")
        if os.getenv("OUTPUT_DIRECTORY"):
            config["report"]["output_directory"] = os.getenv("OUTPUT_DIRECTORY")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/file_analyzer.log")

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

    def _is_excluded(self, file_path: Path) -> bool:
        """Check if file should be excluded from analysis.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file should be excluded, False otherwise.
        """
        exclude_config = self.config.get("analysis", {}).get("exclude", {})
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

    def scan_directory(
        self, directory: Optional[str] = None, recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """Scan directory and collect file size information.

        Args:
            directory: Directory to scan (overrides config).
            recursive: Whether to scan recursively.

        Returns:
            List of file information dictionaries.

        Raises:
            FileNotFoundError: If directory doesn't exist.
            PermissionError: If directory is not accessible.
        """
        analysis_config = self.config.get("analysis", {})

        if directory:
            scan_dir = Path(directory)
        else:
            scan_dir = Path(analysis_config.get("scan_directory", "."))

        if not scan_dir.exists():
            raise FileNotFoundError(f"Directory does not exist: {scan_dir}")

        if not scan_dir.is_dir():
            raise ValueError(f"Path is not a directory: {scan_dir}")

        logger.info(f"Scanning directory: {scan_dir} (recursive: {recursive})")

        self.file_data = []
        self.stats = {
            "total_files": 0,
            "total_size": 0,
            "directories_scanned": 0,
            "errors": 0,
        }

        # Walk directory
        if recursive:
            iterator = scan_dir.rglob("*")
        else:
            iterator = scan_dir.glob("*")

        for item_path in iterator:
            if not item_path.is_file():
                if item_path.is_dir():
                    self.stats["directories_scanned"] += 1
                continue

            # Check exclusions
            if self._is_excluded(item_path):
                continue

            self.stats["total_files"] += 1

            try:
                stat_info = item_path.stat()
                file_size = stat_info.st_size
                self.stats["total_size"] += file_size

                file_info = {
                    "path": str(item_path),
                    "name": item_path.name,
                    "size": file_size,
                    "extension": item_path.suffix.lower() or "no_extension",
                    "modified_time": stat_info.st_mtime,
                    "directory": str(item_path.parent),
                }

                self.file_data.append(file_info)

            except (OSError, PermissionError) as e:
                logger.warning(f"Could not get file info for {item_path}: {e}")
                self.stats["errors"] += 1

        logger.info(
            f"Scanned {self.stats['total_files']} file(s) "
            f"({self._format_size(self.stats['total_size'])})"
        )

        return self.file_data

    def get_largest_files(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get largest files.

        Args:
            count: Number of largest files to return.

        Returns:
            List of file information dictionaries, sorted by size (largest first).
        """
        sorted_files = sorted(self.file_data, key=lambda x: x["size"], reverse=True)
        return sorted_files[:count]

    def get_size_distribution_by_type(self) -> Dict[str, Dict[str, Any]]:
        """Calculate size distribution by file type.

        Returns:
            Dictionary mapping file extensions to size statistics.
        """
        distribution: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "total_size": 0, "files": []}
        )

        for file_info in self.file_data:
            ext = file_info["extension"]
            distribution[ext]["count"] += 1
            distribution[ext]["total_size"] += file_info["size"]
            distribution[ext]["files"].append(file_info)

        # Convert to regular dict and add percentages
        result = {}
        total_size = self.stats["total_size"]
        total_files = self.stats["total_files"]

        for ext, data in distribution.items():
            result[ext] = {
                "count": data["count"],
                "total_size": data["total_size"],
                "percentage_of_total_size": (
                    (data["total_size"] / total_size * 100) if total_size > 0 else 0
                ),
                "percentage_of_total_files": (
                    (data["count"] / total_files * 100) if total_files > 0 else 0
                ),
                "average_size": (
                    data["total_size"] / data["count"] if data["count"] > 0 else 0
                ),
            }

        return result

    def generate_cleanup_recommendations(self) -> List[Dict[str, Any]]:
        """Generate cleanup recommendations based on analysis.

        Returns:
            List of recommendation dictionaries.
        """
        recommendations = []
        analysis_config = self.config.get("analysis", {})
        cleanup_rules = self.config.get("cleanup", {})

        # Large file threshold
        large_file_threshold = cleanup_rules.get("large_file_threshold_mb", 100) * 1024 * 1024

        # Old file threshold (days)
        old_file_threshold_days = cleanup_rules.get("old_file_threshold_days", 365)
        cutoff_date = datetime.now() - timedelta(days=old_file_threshold_days)

        # Extension-based recommendations
        extension_rules = cleanup_rules.get("extension_recommendations", {})
        distribution = self.get_size_distribution_by_type()

        for ext, data in distribution.items():
            ext_clean = ext.lstrip(".")
            if ext_clean in extension_rules:
                rule = extension_rules[ext_clean]
                if data["total_size"] > (rule.get("size_threshold_mb", 0) * 1024 * 1024):
                    recommendations.append(
                        {
                            "type": "extension",
                            "priority": rule.get("priority", "medium"),
                            "extension": ext,
                            "reason": rule.get("reason", f"Large amount of {ext} files"),
                            "size": data["total_size"],
                            "count": data["count"],
                            "suggestion": rule.get("suggestion", "Consider archiving or deleting"),
                        }
                    )

        # Large files recommendation
        large_files = [f for f in self.file_data if f["size"] > large_file_threshold]
        if large_files:
            total_large_size = sum(f["size"] for f in large_files)
            recommendations.append(
                {
                    "type": "large_files",
                    "priority": "high",
                    "reason": f"Found {len(large_files)} file(s) larger than {self._format_size(large_file_threshold)}",
                    "size": total_large_size,
                    "count": len(large_files),
                    "suggestion": "Review large files and consider archiving or moving to external storage",
                    "files": large_files[:10],  # Include top 10 for reference
                }
            )

        # Old files recommendation
        old_files = [
            f
            for f in self.file_data
            if datetime.fromtimestamp(f["modified_time"]) < cutoff_date
        ]
        if old_files:
            total_old_size = sum(f["size"] for f in old_files)
            recommendations.append(
                {
                    "type": "old_files",
                    "priority": "medium",
                    "reason": f"Found {len(old_files)} file(s) older than {old_file_threshold_days} days",
                    "size": total_old_size,
                    "count": len(old_files),
                    "suggestion": "Consider archiving old files that are no longer needed",
                }
            )

        # Duplicate extensions (many files of same type)
        for ext, data in distribution.items():
            if data["count"] > cleanup_rules.get("duplicate_extension_threshold", 100):
                recommendations.append(
                    {
                        "type": "many_files",
                        "priority": "low",
                        "extension": ext,
                        "reason": f"Many files with extension {ext} ({data['count']} files)",
                        "size": data["total_size"],
                        "count": data["count"],
                        "suggestion": "Consider organizing or archiving files of this type",
                    }
                )

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 2))

        return recommendations

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate detailed file size report.

        Args:
            output_file: Path to output file (overrides config).

        Returns:
            Report content as string.
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("File Size Analysis Report")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Summary
        report_lines.append("Summary Statistics")
        report_lines.append("-" * 80)
        report_lines.append(f"Total files scanned: {self.stats['total_files']:,}")
        report_lines.append(f"Total size: {self._format_size(self.stats['total_size'])}")
        report_lines.append(f"Directories scanned: {self.stats['directories_scanned']:,}")
        report_lines.append(f"Errors encountered: {self.stats['errors']}")
        report_lines.append("")

        # Largest files
        report_lines.append("Largest Files (Top 20)")
        report_lines.append("-" * 80)
        largest_files = self.get_largest_files(20)
        for i, file_info in enumerate(largest_files, 1):
            size_str = self._format_size(file_info["size"])
            report_lines.append(
                f"{i:2d}. {size_str:>12s}  {file_info['name']:<50s}  {file_info['path']}"
            )
        report_lines.append("")

        # Size distribution by type
        report_lines.append("Size Distribution by File Type")
        report_lines.append("-" * 80)
        distribution = self.get_size_distribution_by_type()

        # Sort by total size
        sorted_dist = sorted(
            distribution.items(), key=lambda x: x[1]["total_size"], reverse=True
        )

        report_lines.append(
            f"{'Extension':<20s} {'Count':>10s} {'Total Size':>15s} "
            f"{'% of Total':>12s} {'Avg Size':>15s}"
        )
        report_lines.append("-" * 80)

        for ext, data in sorted_dist[:30]:  # Top 30 types
            ext_display = ext if ext != "no_extension" else "(no extension)"
            report_lines.append(
                f"{ext_display:<20s} {data['count']:>10,} "
                f"{self._format_size(data['total_size']):>15s} "
                f"{data['percentage_of_total_size']:>11.2f}% "
                f"{self._format_size(data['average_size']):>15s}"
            )
        report_lines.append("")

        # Cleanup recommendations
        report_lines.append("Cleanup Recommendations")
        report_lines.append("-" * 80)
        recommendations = self.generate_cleanup_recommendations()

        if not recommendations:
            report_lines.append("No specific cleanup recommendations at this time.")
        else:
            for i, rec in enumerate(recommendations, 1):
                priority = rec.get("priority", "medium").upper()
                report_lines.append(f"\n{i}. [{priority}] {rec.get('reason', 'N/A')}")
                report_lines.append(f"   Size: {self._format_size(rec.get('size', 0))}")
                report_lines.append(f"   Files: {rec.get('count', 0):,}")
                report_lines.append(f"   Suggestion: {rec.get('suggestion', 'N/A')}")

                if "files" in rec:
                    report_lines.append("   Sample files:")
                    for file_info in rec["files"][:5]:
                        report_lines.append(
                            f"     - {self._format_size(file_info['size']):>12s}  {file_info['path']}"
                        )

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

    def get_statistics(self) -> Dict[str, Any]:
        """Get analysis statistics.

        Returns:
            Dictionary with statistics.
        """
        return self.stats.copy()


def main() -> int:
    """Main entry point for file size analyzer."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze file sizes and generate reports")
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-d",
        "--directory",
        help="Directory to analyze (overrides config)",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Disable recursive directory scanning",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file for report (overrides config)",
    )
    parser.add_argument(
        "--largest",
        type=int,
        default=10,
        help="Number of largest files to display (default: 10)",
    )

    args = parser.parse_args()

    try:
        analyzer = FileSizeAnalyzer(config_path=args.config)

        # Scan directory
        analyzer.scan_directory(directory=args.directory, recursive=not args.no_recursive)

        # Generate report
        output_file = args.output or analyzer.config.get("report", {}).get("output_file")
        report_content = analyzer.generate_report(output_file=output_file)

        # Print to console
        print(report_content)

        # Print largest files summary
        print("\n" + "=" * 80)
        print(f"Top {args.largest} Largest Files:")
        print("=" * 80)
        largest = analyzer.get_largest_files(args.largest)
        for i, file_info in enumerate(largest, 1):
            size_str = analyzer._format_size(file_info["size"])
            print(f"{i:2d}. {size_str:>12s}  {file_info['path']}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        return 1
    except PermissionError as e:
        logger.error(f"Permission error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
