"""File Usage Analytics - Generate file usage analytics with visualizations.

This module provides functionality to analyze file usage patterns including
access patterns, modification trends, and storage growth over time with
visualizations.
"""

import json
import logging
import logging.handlers
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FileUsageAnalytics:
    """Analyzes file usage patterns and generates visualizations."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize FileUsageAnalytics with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.analytics_data: Dict[str, Any] = {}
        self.stats = {
            "files_analyzed": 0,
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

        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

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
        skip_patterns = self.config.get("scan", {}).get("skip_patterns", [])
        path_str = str(path)

        for pattern in skip_patterns:
            if pattern in path_str:
                return True

        return False

    def _collect_file_metadata(
        self, file_path: Path
    ) -> Optional[Dict[str, Any]]:
        """Collect metadata for a single file.

        Args:
            file_path: Path to file.

        Returns:
            Dictionary with file metadata or None if error.
        """
        try:
            stat = file_path.stat()
            return {
                "path": str(file_path),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "accessed": datetime.fromtimestamp(stat.st_atime),
                "created": datetime.fromtimestamp(stat.st_ctime),
                "extension": file_path.suffix.lower(),
            }
        except (OSError, PermissionError) as e:
            logger.debug(f"Cannot access file {file_path}: {e}")
            self.stats["errors"] += 1
            return None

    def analyze_directory(self, source_dir: str) -> None:
        """Analyze file usage patterns in directory.

        Args:
            source_dir: Path to directory to analyze.

        Raises:
            FileNotFoundError: If directory doesn't exist.
            PermissionError: If directory is not accessible.
        """
        source_path = Path(source_dir)
        if not source_path.exists():
            raise FileNotFoundError(f"Directory not found: {source_dir}")
        if not source_path.is_dir():
            raise ValueError(f"Path is not a directory: {source_dir}")

        logger.info(
            f"Starting analysis of {source_dir}",
            extra={"source_dir": source_dir},
        )

        self.analytics_data = {
            "files": [],
            "access_patterns": defaultdict(int),
            "modification_trends": defaultdict(int),
            "storage_growth": defaultdict(int),
            "extension_distribution": defaultdict(int),
            "size_distribution": defaultdict(int),
        }

        self.stats = {
            "files_analyzed": 0,
            "directories_scanned": 0,
            "errors": 0,
        }

        try:
            for root, dirs, files in source_path.rglob("*"):
                root_path = Path(root)

                if self._should_skip_path(root_path):
                    dirs[:] = []
                    continue

                if root_path.is_dir():
                    self.stats["directories_scanned"] += 1

                for file_name in files:
                    file_path = root_path / file_name

                    if self._should_skip_path(file_path):
                        continue

                    metadata = self._collect_file_metadata(file_path)
                    if metadata:
                        self.analytics_data["files"].append(metadata)
                        self.stats["files_analyzed"] += 1

                        # Track access patterns by hour
                        access_hour = metadata["accessed"].hour
                        self.analytics_data["access_patterns"][access_hour] += 1

                        # Track modification trends by date
                        mod_date = metadata["modified"].date()
                        self.analytics_data["modification_trends"][mod_date] += 1

                        # Track storage growth by date
                        created_date = metadata["created"].date()
                        self.analytics_data["storage_growth"][created_date] += (
                            metadata["size"]
                        )

                        # Track extension distribution
                        ext = metadata["extension"] or "no_extension"
                        self.analytics_data["extension_distribution"][ext] += 1

                        # Track size distribution (in MB buckets)
                        size_mb = metadata["size"] / (1024 * 1024)
                        size_bucket = int(size_mb // 10) * 10
                        self.analytics_data["size_distribution"][size_bucket] += 1

        except PermissionError as e:
            logger.error(
                f"Permission denied accessing {source_dir}: {e}",
                extra={"source_dir": source_dir},
            )
            raise

        logger.info(
            f"Analysis completed: {self.stats['files_analyzed']} files analyzed",
            extra=self.stats,
        )

    def _generate_access_patterns_chart(
        self, output_path: Path
    ) -> None:
        """Generate access patterns visualization.

        Args:
            output_path: Path to save chart.
        """
        access_data = self.analytics_data["access_patterns"]
        if not access_data:
            logger.warning("No access pattern data available")
            return

        hours = sorted(access_data.keys())
        counts = [access_data[h] for h in hours]

        plt.figure(figsize=(12, 6))
        plt.bar(hours, counts, color="steelblue", alpha=0.7)
        plt.xlabel("Hour of Day", fontsize=12)
        plt.ylabel("Number of File Accesses", fontsize=12)
        plt.title("File Access Patterns by Hour", fontsize=14, fontweight="bold")
        plt.xticks(hours)
        plt.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"Access patterns chart saved to {output_path}")

    def _generate_modification_trends_chart(
        self, output_path: Path
    ) -> None:
        """Generate modification trends visualization.

        Args:
            output_path: Path to save chart.
        """
        mod_data = self.analytics_data["modification_trends"]
        if not mod_data:
            logger.warning("No modification trend data available")
            return

        dates = sorted(mod_data.keys())
        counts = [mod_data[d] for d in dates]

        plt.figure(figsize=(14, 6))
        plt.plot(dates, counts, marker="o", linewidth=2, markersize=4)
        plt.xlabel("Date", fontsize=12)
        plt.ylabel("Number of File Modifications", fontsize=12)
        plt.title("File Modification Trends Over Time", fontsize=14, fontweight="bold")
        plt.grid(alpha=0.3)
        plt.xticks(rotation=45)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"Modification trends chart saved to {output_path}")

    def _generate_storage_growth_chart(self, output_path: Path) -> None:
        """Generate storage growth visualization.

        Args:
            output_path: Path to save chart.
        """
        growth_data = self.analytics_data["storage_growth"]
        if not growth_data:
            logger.warning("No storage growth data available")
            return

        dates = sorted(growth_data.keys())
        sizes_mb = [growth_data[d] / (1024 * 1024) for d in dates]

        # Calculate cumulative growth
        cumulative = np.cumsum(sizes_mb)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

        # Daily growth
        ax1.bar(dates, sizes_mb, color="green", alpha=0.6)
        ax1.set_xlabel("Date", fontsize=12)
        ax1.set_ylabel("Storage Added (MB)", fontsize=12)
        ax1.set_title("Daily Storage Growth", fontsize=13, fontweight="bold")
        ax1.grid(axis="y", alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

        # Cumulative growth
        ax2.plot(dates, cumulative, color="darkgreen", linewidth=2, marker="o")
        ax2.set_xlabel("Date", fontsize=12)
        ax2.set_ylabel("Cumulative Storage (MB)", fontsize=12)
        ax2.set_title("Cumulative Storage Growth", fontsize=13, fontweight="bold")
        ax2.grid(alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"Storage growth chart saved to {output_path}")

    def _generate_extension_distribution_chart(
        self, output_path: Path
    ) -> None:
        """Generate file extension distribution visualization.

        Args:
            output_path: Path to save chart.
        """
        ext_data = self.analytics_data["extension_distribution"]
        if not ext_data:
            logger.warning("No extension distribution data available")
            return

        sorted_exts = sorted(ext_data.items(), key=lambda x: x[1], reverse=True)
        top_exts = sorted_exts[:15]
        extensions = [ext if ext else "no_extension" for ext, _ in top_exts]
        counts = [count for _, count in top_exts]

        plt.figure(figsize=(12, 6))
        plt.barh(extensions, counts, color="coral", alpha=0.7)
        plt.xlabel("Number of Files", fontsize=12)
        plt.ylabel("File Extension", fontsize=12)
        plt.title("Top 15 File Extensions Distribution", fontsize=14, fontweight="bold")
        plt.grid(axis="x", alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"Extension distribution chart saved to {output_path}")

    def _generate_size_distribution_chart(self, output_path: Path) -> None:
        """Generate file size distribution visualization.

        Args:
            output_path: Path to save chart.
        """
        size_data = self.analytics_data["size_distribution"]
        if not size_data:
            logger.warning("No size distribution data available")
            return

        buckets = sorted(size_data.keys())
        counts = [size_data[b] for b in buckets]
        labels = [f"{b}-{b+9} MB" for b in buckets]

        plt.figure(figsize=(12, 6))
        plt.bar(range(len(buckets)), counts, color="purple", alpha=0.7)
        plt.xlabel("File Size Range (MB)", fontsize=12)
        plt.ylabel("Number of Files", fontsize=12)
        plt.title("File Size Distribution", fontsize=14, fontweight="bold")
        plt.xticks(range(len(buckets)), labels, rotation=45, ha="right")
        plt.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"Size distribution chart saved to {output_path}")

    def generate_visualizations(
        self, output_dir: Optional[str] = None
    ) -> Dict[str, Path]:
        """Generate all visualization charts.

        Args:
            output_dir: Optional directory to save charts. If None, uses
                default from config.

        Returns:
            Dictionary mapping chart names to output file paths.

        Raises:
            ValueError: If no analytics data is available.
        """
        if not self.analytics_data or not self.analytics_data["files"]:
            raise ValueError(
                "No analytics data available. Run analyze_directory() first."
            )

        viz_config = self.config.get("visualizations", {})
        default_output = viz_config.get("output_dir", "analytics_charts")

        output_path = Path(output_dir or default_output)
        output_path.mkdir(parents=True, exist_ok=True)

        charts = {}

        charts["access_patterns"] = output_path / "access_patterns.png"
        self._generate_access_patterns_chart(charts["access_patterns"])

        charts["modification_trends"] = output_path / "modification_trends.png"
        self._generate_modification_trends_chart(charts["modification_trends"])

        charts["storage_growth"] = output_path / "storage_growth.png"
        self._generate_storage_growth_chart(charts["storage_growth"])

        charts["extension_distribution"] = (
            output_path / "extension_distribution.png"
        )
        self._generate_extension_distribution_chart(
            charts["extension_distribution"]
        )

        charts["size_distribution"] = output_path / "size_distribution.png"
        self._generate_size_distribution_chart(charts["size_distribution"])

        logger.info(
            f"Generated {len(charts)} visualization charts",
            extra={"output_dir": str(output_path)},
        )

        return charts

    def generate_report(self, output_path: Optional[str] = None) -> str:
        """Generate analytics report.

        Args:
            output_path: Optional path to save report file. If None, uses
                default from config.

        Returns:
            Report content as string.

        Raises:
            ValueError: If no analytics data is available.
        """
        if not self.analytics_data or not self.analytics_data["files"]:
            raise ValueError(
                "No analytics data available. Run analyze_directory() first."
            )

        report_config = self.config.get("report", {})
        default_output = report_config.get(
            "output_file", "analytics_report.txt"
        )

        output_file = output_path or default_output

        total_size = sum(f["size"] for f in self.analytics_data["files"])
        total_size_mb = total_size / (1024 * 1024)
        total_size_gb = total_size_mb / 1024

        avg_file_size = (
            total_size / len(self.analytics_data["files"])
            if self.analytics_data["files"]
            else 0
        )

        report_lines = [
            "=" * 80,
            "FILE USAGE ANALYTICS REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY",
            "-" * 80,
            f"Files analyzed: {self.stats['files_analyzed']:,}",
            f"Directories scanned: {self.stats['directories_scanned']:,}",
            f"Total storage: {total_size_gb:.2f} GB ({total_size_mb:.2f} MB)",
            f"Average file size: {avg_file_size / 1024:.2f} KB",
            f"Errors encountered: {self.stats['errors']}",
            "",
            "ACCESS PATTERNS",
            "-" * 80,
        ]

        access_data = self.analytics_data["access_patterns"]
        if access_data:
            peak_hour = max(access_data.items(), key=lambda x: x[1])
            report_lines.append(f"Peak access hour: {peak_hour[0]}:00 ({peak_hour[1]} accesses)")
            report_lines.append("")
            for hour in sorted(access_data.keys()):
                report_lines.append(f"  {hour:02d}:00 - {access_data[hour]:,} accesses")
        else:
            report_lines.append("No access pattern data available.")

        report_lines.extend([
            "",
            "MODIFICATION TRENDS",
            "-" * 80,
        ])

        mod_data = self.analytics_data["modification_trends"]
        if mod_data:
            recent_mods = sorted(mod_data.items(), reverse=True)[:10]
            report_lines.append("Most recent modification dates:")
            for date, count in recent_mods:
                report_lines.append(f"  {date}: {count:,} files modified")
        else:
            report_lines.append("No modification trend data available.")

        report_lines.extend([
            "",
            "STORAGE GROWTH",
            "-" * 80,
        ])

        growth_data = self.analytics_data["storage_growth"]
        if growth_data:
            total_growth_mb = sum(growth_data.values()) / (1024 * 1024)
            report_lines.append(f"Total storage growth: {total_growth_mb:.2f} MB")
            recent_growth = sorted(growth_data.items(), reverse=True)[:10]
            report_lines.append("Most recent storage additions:")
            for date, size_bytes in recent_growth:
                size_mb = size_bytes / (1024 * 1024)
                report_lines.append(f"  {date}: {size_mb:.2f} MB added")
        else:
            report_lines.append("No storage growth data available.")

        report_lines.extend([
            "",
            "EXTENSION DISTRIBUTION",
            "-" * 80,
        ])

        ext_data = self.analytics_data["extension_distribution"]
        if ext_data:
            sorted_exts = sorted(ext_data.items(), key=lambda x: x[1], reverse=True)[:10]
            for ext, count in sorted_exts:
                ext_display = ext if ext else "no_extension"
                report_lines.append(f"  {ext_display}: {count:,} files")
        else:
            report_lines.append("No extension distribution data available.")

        report_content = "\n".join(report_lines)

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


def main() -> None:
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate file usage analytics with visualizations"
    )
    parser.add_argument(
        "directory",
        help="Directory to analyze",
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-v",
        "--visualizations",
        action="store_true",
        help="Generate visualization charts",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        help="Output directory for visualizations (overrides config)",
    )
    parser.add_argument(
        "-r",
        "--report",
        help="Output path for analytics report (overrides config)",
    )

    args = parser.parse_args()

    try:
        analytics = FileUsageAnalytics(config_path=args.config)
        analytics.analyze_directory(args.directory)

        if args.visualizations:
            charts = analytics.generate_visualizations(
                output_dir=args.output_dir
            )
            print(f"\nGenerated {len(charts)} visualization charts:")
            for name, path in charts.items():
                print(f"  {name}: {path}")

        report_path = analytics.generate_report(output_path=args.report)
        print(f"\nAnalytics report generated: {report_path}")

        print(
            f"\nAnalysis complete. Analyzed {analytics.stats['files_analyzed']} "
            f"files in {analytics.stats['directories_scanned']} directories."
        )

    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
