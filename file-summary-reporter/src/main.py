"""File Summary Reporter - CLI tool for generating file summary reports.

This module provides a command-line tool for analyzing file systems, collecting
statistics, identifying trends, and generating recommendations for organization
and cleanup strategies.
"""

import argparse
import json
import logging
import logging.handlers
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FileStatisticsCollector:
    """Collects file system statistics and metadata."""

    def __init__(self, config: Dict) -> None:
        """Initialize FileStatisticsCollector.

        Args:
            config: Configuration dictionary containing analysis settings.
        """
        self.config = config
        self.source_dir = Path(config.get("source_directory", "."))
        self.filter_config = config.get("filtering", {})
        self.analysis_config = config.get("analysis", {})

        # Setup logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging for the application."""
        log_level = self.config.get("logging", {}).get("level", "INFO")
        log_file = self.config.get("logging", {}).get("file", "logs/reporter.log")

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

    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from analysis.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file should be excluded, False otherwise.
        """
        exclude_patterns = self.filter_config.get("exclude_files", [])
        exclude_extensions = self.filter_config.get("exclude_extensions", [])

        file_name = file_path.name
        file_ext = file_path.suffix.lower()

        # Check exclude patterns
        for pattern in exclude_patterns:
            if pattern in file_name or file_name.startswith(pattern):
                return True

        # Check exclude extensions
        if file_ext in exclude_extensions:
            return True

        # Always exclude hidden files except .gitkeep
        if file_name.startswith(".") and file_name not in [".gitkeep"]:
            return True

        return False

    def should_exclude_directory(self, dir_path: Path) -> bool:
        """Check if directory should be excluded from analysis.

        Args:
            dir_path: Path to directory to check.

        Returns:
            True if directory should be excluded, False otherwise.
        """
        exclude_patterns = self.filter_config.get("exclude_directories", [])
        dir_name = dir_path.name

        for pattern in exclude_patterns:
            if pattern in dir_name or dir_name.startswith(pattern):
                return True

        # Always exclude common system directories
        system_dirs = {
            ".git",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            ".venv",
            "venv",
            "logs",
        }
        return dir_name in system_dirs

    def collect_file_statistics(self) -> Dict:
        """Collect comprehensive file statistics.

        Returns:
            Dictionary containing collected statistics.
        """
        stats = {
            "total_files": 0,
            "total_directories": 0,
            "total_size": 0,
            "file_types": Counter(),
            "file_extensions": Counter(),
            "size_distribution": defaultdict(int),
            "age_distribution": defaultdict(int),
            "largest_files": [],
            "oldest_files": [],
            "recent_files": [],
            "empty_files": 0,
            "duplicate_extensions": [],
            "directory_structure": defaultdict(int),
        }

        if not self.source_dir.exists():
            logger.error(f"Source directory does not exist: {self.source_dir}")
            return stats

        logger.info(f"Scanning directory: {self.source_dir}")

        try:
            for root, dirs, filenames in os.walk(self.source_dir):
                # Filter out excluded directories
                dirs[:] = [
                    d
                    for d in dirs
                    if not self.should_exclude_directory(Path(root) / d)
                ]

                # Count directories
                stats["total_directories"] += len(dirs)

                # Calculate directory depth
                try:
                    depth = len(Path(root).relative_to(self.source_dir).parts)
                    stats["directory_structure"][depth] += 1
                except ValueError:
                    pass

                for filename in filenames:
                    file_path = Path(root) / filename

                    if self.should_exclude_file(file_path):
                        continue

                    try:
                        file_stat = file_path.stat()
                        file_size = file_stat.st_size
                        mod_time = datetime.fromtimestamp(file_stat.st_mtime)
                        access_time = datetime.fromtimestamp(file_stat.st_atime)

                        # Basic counts
                        stats["total_files"] += 1
                        stats["total_size"] += file_size

                        # File type and extension
                        file_ext = file_path.suffix.lower()
                        if file_ext:
                            stats["file_extensions"][file_ext] += 1
                            # Map to file type category
                            file_type = self._categorize_file_type(file_ext)
                            stats["file_types"][file_type] += 1
                        else:
                            stats["file_types"]["no_extension"] += 1

                        # Size distribution
                        size_category = self._categorize_size(file_size)
                        stats["size_distribution"][size_category] += 1

                        # Age distribution
                        now = datetime.now()
                        days_old = (now - mod_time).days
                        age_category = self._categorize_age(days_old)
                        stats["age_distribution"][age_category] += 1

                        # Track largest files
                        stats["largest_files"].append(
                            {
                                "path": str(file_path.relative_to(self.source_dir)),
                                "size": file_size,
                                "modified": mod_time.isoformat(),
                            }
                        )

                        # Track oldest files
                        stats["oldest_files"].append(
                            {
                                "path": str(file_path.relative_to(self.source_dir)),
                                "age_days": days_old,
                                "modified": mod_time.isoformat(),
                            }
                        )

                        # Track recent files
                        if days_old <= 7:
                            stats["recent_files"].append(
                                {
                                    "path": str(
                                        file_path.relative_to(self.source_dir)
                                    ),
                                    "days_old": days_old,
                                    "modified": mod_time.isoformat(),
                                }
                            )

                        # Count empty files
                        if file_size == 0:
                            stats["empty_files"] += 1

                    except (OSError, PermissionError) as e:
                        logger.warning(
                            f"Cannot access file {file_path}: {e}",
                            extra={"file_path": str(file_path), "error": str(e)},
                        )
                        continue

        except (OSError, PermissionError) as e:
            logger.error(
                f"Cannot scan source directory {self.source_dir}: {e}",
                extra={"source_directory": str(self.source_dir), "error": str(e)},
            )

        # Sort and limit lists
        stats["largest_files"].sort(key=lambda x: x["size"], reverse=True)
        stats["largest_files"] = stats["largest_files"][:20]

        stats["oldest_files"].sort(key=lambda x: x["age_days"], reverse=True)
        stats["oldest_files"] = stats["oldest_files"][:20]

        stats["recent_files"].sort(key=lambda x: x["days_old"])

        # Find duplicate extensions (same extension, multiple files)
        for ext, count in stats["file_extensions"].items():
            if count > 10:  # Threshold for "many files"
                stats["duplicate_extensions"].append({"extension": ext, "count": count})

        stats["duplicate_extensions"].sort(key=lambda x: x["count"], reverse=True)

        return stats

    def _categorize_file_type(self, extension: str) -> str:
        """Categorize file by extension into type groups.

        Args:
            extension: File extension (with dot).

        Returns:
            File type category.
        """
        type_mapping = {
            "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
            "document": [
                ".pdf",
                ".doc",
                ".docx",
                ".txt",
                ".rtf",
                ".odt",
                ".pages",
            ],
            "spreadsheet": [".xls", ".xlsx", ".csv", ".ods", ".numbers"],
            "video": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"],
            "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
            "archive": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
            "code": [
                ".py",
                ".js",
                ".java",
                ".cpp",
                ".c",
                ".html",
                ".css",
                ".xml",
                ".json",
            ],
            "executable": [".exe", ".app", ".deb", ".rpm", ".dmg"],
        }

        for file_type, extensions in type_mapping.items():
            if extension in extensions:
                return file_type

        return "other"

    def _categorize_size(self, size: int) -> str:
        """Categorize file size into groups.

        Args:
            size: File size in bytes.

        Returns:
            Size category string.
        """
        if size == 0:
            return "empty"
        elif size < 1024:  # < 1 KB
            return "tiny (<1KB)"
        elif size < 1024 * 1024:  # < 1 MB
            return "small (<1MB)"
        elif size < 10 * 1024 * 1024:  # < 10 MB
            return "medium (<10MB)"
        elif size < 100 * 1024 * 1024:  # < 100 MB
            return "large (<100MB)"
        else:
            return "very_large (>100MB)"

    def _categorize_age(self, days_old: int) -> str:
        """Categorize file age into groups.

        Args:
            days_old: Number of days since last modification.

        Returns:
            Age category string.
        """
        if days_old <= 7:
            return "recent (0-7 days)"
        elif days_old <= 30:
            return "active (8-30 days)"
        elif days_old <= 90:
            return "moderate (31-90 days)"
        elif days_old <= 365:
            return "old (91-365 days)"
        else:
            return "very_old (>365 days)"


class TrendAnalyzer:
    """Analyzes trends in file statistics."""

    def __init__(self, stats: Dict, config: Dict) -> None:
        """Initialize TrendAnalyzer.

        Args:
            stats: File statistics dictionary.
            config: Configuration dictionary.
        """
        self.stats = stats
        self.config = config

    def analyze_trends(self) -> Dict:
        """Analyze trends from statistics.

        Returns:
            Dictionary containing trend analysis.
        """
        trends = {
            "file_distribution": {},
            "size_trends": {},
            "age_trends": {},
            "growth_indicators": {},
            "organization_opportunities": [],
        }

        # File type distribution
        total_files = self.stats["total_files"]
        if total_files > 0:
            trends["file_distribution"] = {
                file_type: {
                    "count": count,
                    "percentage": round((count / total_files) * 100, 2),
                }
                for file_type, count in self.stats["file_types"].most_common()
            }

        # Size trends
        trends["size_trends"] = {
            category: count
            for category, count in sorted(
                self.stats["size_distribution"].items()
            )
        }

        # Age trends
        trends["age_trends"] = {
            category: count
            for category, count in sorted(
                self.stats["age_distribution"].items()
            )
        }

        # Growth indicators
        trends["growth_indicators"] = {
            "total_files": total_files,
            "total_size_gb": round(self.stats["total_size"] / (1024**3), 2),
            "average_file_size_kb": round(
                (self.stats["total_size"] / total_files / 1024)
                if total_files > 0
                else 0,
                2,
            ),
            "empty_files_count": self.stats["empty_files"],
            "empty_files_percentage": round(
                (self.stats["empty_files"] / total_files * 100)
                if total_files > 0
                else 0,
                2,
            ),
        }

        # Organization opportunities
        trends["organization_opportunities"] = self._identify_opportunities()

        return trends

    def _identify_opportunities(self) -> List[str]:
        """Identify organization opportunities.

        Returns:
            List of opportunity descriptions.
        """
        opportunities = []

        # Check for many files of same type
        for file_type, count in self.stats["file_types"].most_common(5):
            if count > 10:
                opportunities.append(
                    f"Consider organizing {count} {file_type} files into a "
                    f"dedicated {file_type} directory"
                )

        # Check for old files
        very_old_count = self.stats["age_distribution"].get("very_old (>365 days)", 0)
        if very_old_count > 20:
            opportunities.append(
                f"Found {very_old_count} files older than 365 days. "
                "Consider archiving or removing inactive files."
            )

        # Check for empty files
        if self.stats["empty_files"] > 0:
            opportunities.append(
                f"Found {self.stats['empty_files']} empty files. "
                "Consider removing them to free up directory space."
            )

        # Check for large files
        very_large_count = self.stats["size_distribution"].get(
            "very_large (>100MB)", 0
        )
        if very_large_count > 0:
            opportunities.append(
                f"Found {very_large_count} very large files (>100MB). "
                "Consider moving them to external storage or compressing."
            )

        # Check for duplicate extensions
        if len(self.stats["duplicate_extensions"]) > 0:
            top_dup = self.stats["duplicate_extensions"][0]
            opportunities.append(
                f"Found {top_dup['count']} files with extension "
                f"{top_dup['extension']}. Consider organizing by type."
            )

        # Check directory structure depth
        max_depth = max(self.stats["directory_structure"].keys()) if self.stats["directory_structure"] else 0
        if max_depth > 5:
            opportunities.append(
                f"Deep directory structure detected (max depth: {max_depth}). "
                "Consider flattening or reorganizing."
            )

        return opportunities


class RecommendationGenerator:
    """Generates recommendations for organization and cleanup."""

    def __init__(self, stats: Dict, trends: Dict, config: Dict) -> None:
        """Initialize RecommendationGenerator.

        Args:
            stats: File statistics dictionary.
            trends: Trend analysis dictionary.
            config: Configuration dictionary.
        """
        self.stats = stats
        self.trends = trends
        self.config = config

    def generate_recommendations(self) -> Dict:
        """Generate organization and cleanup recommendations.

        Returns:
            Dictionary containing recommendations.
        """
        recommendations = {
            "cleanup": [],
            "organization": [],
            "optimization": [],
            "priority": "medium",
        }

        # Cleanup recommendations
        if self.stats["empty_files"] > 0:
            recommendations["cleanup"].append(
                {
                    "action": "Remove empty files",
                    "description": f"Delete {self.stats['empty_files']} empty files",
                    "impact": "low",
                    "effort": "low",
                }
            )

        very_old_count = self.stats["age_distribution"].get(
            "very_old (>365 days)", 0
        )
        if very_old_count > 50:
            recommendations["cleanup"].append(
                {
                    "action": "Archive old files",
                    "description": f"Archive {very_old_count} files older than 1 year",
                    "impact": "medium",
                    "effort": "medium",
                }
            )

        # Organization recommendations
        for file_type, data in list(
            self.trends["file_distribution"].items())[:5]:
            if data["count"] > 20:
                recommendations["organization"].append(
                    {
                        "action": f"Organize {file_type} files",
                        "description": f"Create {file_type} directory and move "
                        f"{data['count']} files",
                        "impact": "high",
                        "effort": "low",
                    }
                )

        # Optimization recommendations
        total_size_gb = self.trends["growth_indicators"]["total_size_gb"]
        if total_size_gb > 10:
            recommendations["optimization"].append(
                {
                    "action": "Review large files",
                    "description": f"Total size is {total_size_gb} GB. "
                    "Review and compress or archive large files.",
                    "impact": "high",
                    "effort": "medium",
                }
            )

        very_large_count = self.stats["size_distribution"].get(
            "very_large (>100MB)", 0
        )
        if very_large_count > 0:
            recommendations["optimization"].append(
                {
                    "action": "Move large files",
                    "description": f"Move {very_large_count} files >100MB to "
                    "external storage",
                    "impact": "medium",
                    "effort": "low",
                }
            )

        # Set priority based on recommendations
        if len(recommendations["cleanup"]) > 2:
            recommendations["priority"] = "high"
        elif len(recommendations["organization"]) > 0:
            recommendations["priority"] = "medium"
        else:
            recommendations["priority"] = "low"

        return recommendations


class ReportGenerator:
    """Generates formatted reports from statistics and recommendations."""

    def __init__(self, stats: Dict, trends: Dict, recommendations: Dict) -> None:
        """Initialize ReportGenerator.

        Args:
            stats: File statistics dictionary.
            trends: Trend analysis dictionary.
            recommendations: Recommendations dictionary.
        """
        self.stats = stats
        self.trends = trends
        self.recommendations = recommendations

    def generate_text_report(self) -> str:
        """Generate a text format report.

        Returns:
            Formatted text report string.
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("FILE SUMMARY REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Overview
        report_lines.append("OVERVIEW")
        report_lines.append("-" * 80)
        report_lines.append(f"Total Files: {self.stats['total_files']:,}")
        report_lines.append(f"Total Directories: {self.stats['total_directories']:,}")
        total_size_gb = self.stats["total_size"] / (1024**3)
        report_lines.append(f"Total Size: {total_size_gb:.2f} GB")
        report_lines.append("")

        # File Types
        report_lines.append("FILE TYPE DISTRIBUTION")
        report_lines.append("-" * 80)
        for file_type, data in self.trends["file_distribution"].items():
            report_lines.append(
                f"  {file_type:20s}: {data['count']:6d} files "
                f"({data['percentage']:5.2f}%)"
            )
        report_lines.append("")

        # Size Distribution
        report_lines.append("SIZE DISTRIBUTION")
        report_lines.append("-" * 80)
        for category, count in self.trends["size_trends"].items():
            report_lines.append(f"  {category:25s}: {count:6d} files")
        report_lines.append("")

        # Age Distribution
        report_lines.append("AGE DISTRIBUTION")
        report_lines.append("-" * 80)
        for category, count in self.trends["age_trends"].items():
            report_lines.append(f"  {category:25s}: {count:6d} files")
        report_lines.append("")

        # Top Largest Files
        if self.stats["largest_files"]:
            report_lines.append("TOP 10 LARGEST FILES")
            report_lines.append("-" * 80)
            for i, file_info in enumerate(self.stats["largest_files"][:10], 1):
                size_mb = file_info["size"] / (1024**2)
                report_lines.append(
                    f"  {i:2d}. {file_info['path'][:50]:50s} "
                    f"{size_mb:8.2f} MB"
                )
            report_lines.append("")

        # Recommendations
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("-" * 80)
        report_lines.append(f"Priority: {self.recommendations['priority'].upper()}")
        report_lines.append("")

        if self.recommendations["cleanup"]:
            report_lines.append("Cleanup Actions:")
            for rec in self.recommendations["cleanup"]:
                report_lines.append(f"  - {rec['action']}: {rec['description']}")
            report_lines.append("")

        if self.recommendations["organization"]:
            report_lines.append("Organization Actions:")
            for rec in self.recommendations["organization"]:
                report_lines.append(f"  - {rec['action']}: {rec['description']}")
            report_lines.append("")

        if self.recommendations["optimization"]:
            report_lines.append("Optimization Actions:")
            for rec in self.recommendations["optimization"]:
                report_lines.append(f"  - {rec['action']}: {rec['description']}")
            report_lines.append("")

        # Opportunities
        if self.trends["organization_opportunities"]:
            report_lines.append("Organization Opportunities")
            report_lines.append("-" * 80)
            for opp in self.trends["organization_opportunities"]:
                report_lines.append(f"  - {opp}")
            report_lines.append("")

        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    def generate_json_report(self) -> str:
        """Generate a JSON format report.

        Returns:
            JSON formatted report string.
        """
        report = {
            "generated": datetime.now().isoformat(),
            "statistics": {
                "total_files": self.stats["total_files"],
                "total_directories": self.stats["total_directories"],
                "total_size_bytes": self.stats["total_size"],
                "total_size_gb": round(self.stats["total_size"] / (1024**3), 2),
            },
            "file_types": dict(self.stats["file_types"]),
            "file_extensions": dict(self.stats["file_extensions"].most_common(20)),
            "size_distribution": dict(self.trends["size_trends"]),
            "age_distribution": dict(self.trends["age_trends"]),
            "trends": self.trends,
            "recommendations": self.recommendations,
            "top_largest_files": self.stats["largest_files"][:10],
            "top_oldest_files": self.stats["oldest_files"][:10],
        }

        return json.dumps(report, indent=2)


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
        description="Generate file summary reports with statistics, trends, "
        "and recommendations"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to configuration file (default: config.yaml)",
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
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
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

    # Collect statistics
    collector = FileStatisticsCollector(config)
    logger.info("Collecting file statistics...")
    stats = collector.collect_file_statistics()

    # Analyze trends
    analyzer = TrendAnalyzer(stats, config)
    logger.info("Analyzing trends...")
    trends = analyzer.analyze_trends()

    # Generate recommendations
    recommender = RecommendationGenerator(stats, trends, config)
    logger.info("Generating recommendations...")
    recommendations = recommender.generate_recommendations()

    # Generate report
    report_gen = ReportGenerator(stats, trends, recommendations)
    if args.format == "json":
        report = report_gen.generate_json_report()
    else:
        report = report_gen.generate_text_report()

    # Output report
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, "w") as f:
                f.write(report)
            logger.info(f"Report written to: {args.output}")
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to write report: {e}")
            sys.exit(1)
    else:
        print(report)


if __name__ == "__main__":
    main()
