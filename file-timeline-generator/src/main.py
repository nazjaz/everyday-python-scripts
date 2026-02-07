"""File Timeline Generator - CLI tool for generating file timelines.

This module provides a command-line tool for generating file timelines showing
when files were created, modified, and accessed, useful for tracking project
evolution.
"""

import argparse
import json
import logging
import logging.handlers
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class FileTimelineEvent:
    """Represents a timeline event for a file."""

    file_path: Path
    event_type: str  # 'created', 'modified', 'accessed'
    timestamp: datetime
    size: int = 0


@dataclass
class FileTimeline:
    """Represents the complete timeline for a file."""

    file_path: Path
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    accessed: Optional[datetime] = None
    size: int = 0
    extension: str = ""
    events: List[FileTimelineEvent] = field(default_factory=list)


class TimelineCollector:
    """Collects file timeline information."""

    def __init__(self, config: Dict) -> None:
        """Initialize TimelineCollector.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.filter_config = config.get("filtering", {})

    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from timeline.

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

        # Always exclude hidden files
        if file_name.startswith(".") and file_name not in [".gitkeep"]:
            return True

        return False

    def should_exclude_directory(self, dir_path: Path) -> bool:
        """Check if directory should be excluded from timeline.

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

    def collect_file_timeline(self, file_path: Path) -> Optional[FileTimeline]:
        """Collect timeline information for a file.

        Args:
            file_path: Path to file to analyze.

        Returns:
            FileTimeline object, or None if file cannot be accessed.
        """
        try:
            stat = file_path.stat()

            timeline = FileTimeline(
                file_path=file_path,
                created=datetime.fromtimestamp(stat.st_ctime),
                modified=datetime.fromtimestamp(stat.st_mtime),
                accessed=datetime.fromtimestamp(stat.st_atime),
                size=stat.st_size,
                extension=file_path.suffix.lower(),
            )

            # Create events
            if timeline.created:
                timeline.events.append(
                    FileTimelineEvent(
                        file_path=file_path,
                        event_type="created",
                        timestamp=timeline.created,
                        size=timeline.size,
                    )
                )

            if timeline.modified:
                timeline.events.append(
                    FileTimelineEvent(
                        file_path=file_path,
                        event_type="modified",
                        timestamp=timeline.modified,
                        size=timeline.size,
                    )
                )

            if timeline.accessed:
                timeline.events.append(
                    FileTimelineEvent(
                        file_path=file_path,
                        event_type="accessed",
                        timestamp=timeline.accessed,
                        size=timeline.size,
                    )
                )

            # Sort events by timestamp
            timeline.events.sort(key=lambda x: x.timestamp)

            return timeline

        except (OSError, PermissionError) as e:
            logger.warning(
                f"Cannot access file {file_path}: {e}",
                extra={"file_path": str(file_path), "error": str(e)},
            )
            return None

    def collect_timelines(self, search_dir: Path) -> List[FileTimeline]:
        """Collect timelines for all files in directory.

        Args:
            search_dir: Directory to search in.

        Returns:
            List of FileTimeline objects.
        """
        timelines = []

        if not search_dir.exists():
            logger.error(f"Search directory does not exist: {search_dir}")
            return timelines

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

                    if self.should_exclude_file(file_path):
                        continue

                    timeline = self.collect_file_timeline(file_path)
                    if timeline:
                        timelines.append(timeline)

        except (OSError, PermissionError) as e:
            logger.error(
                f"Cannot search directory {search_dir}: {e}",
                extra={"search_directory": str(search_dir), "error": str(e)},
            )

        return timelines


class TimelineAnalyzer:
    """Analyzes file timelines for patterns and evolution."""

    def __init__(self, timelines: List[FileTimeline]) -> None:
        """Initialize TimelineAnalyzer.

        Args:
            timelines: List of file timelines to analyze.
        """
        self.timelines = timelines

    def get_timeline_statistics(self) -> Dict:
        """Get statistics about the timelines.

        Returns:
            Dictionary with timeline statistics.
        """
        if not self.timelines:
            return {}

        all_events = []
        for timeline in self.timelines:
            all_events.extend(timeline.events)

        if not all_events:
            return {}

        # Find earliest and latest events
        earliest = min(event.timestamp for event in all_events)
        latest = max(event.timestamp for event in all_events)

        # Count events by type
        event_counts = defaultdict(int)
        for event in all_events:
            event_counts[event.event_type] += 1

        # Count files by extension
        extension_counts = defaultdict(int)
        for timeline in self.timelines:
            if timeline.extension:
                extension_counts[timeline.extension] += 1

        # Calculate total size
        total_size = sum(timeline.size for timeline in self.timelines)

        return {
            "total_files": len(self.timelines),
            "total_events": len(all_events),
            "earliest_event": earliest.isoformat(),
            "latest_event": latest.isoformat(),
            "time_span_days": (latest - earliest).days if earliest != latest else 0,
            "event_counts": dict(event_counts),
            "extension_counts": dict(extension_counts),
            "total_size_bytes": total_size,
        }

    def get_chronological_timeline(self) -> List[FileTimelineEvent]:
        """Get all events in chronological order.

        Returns:
            List of events sorted by timestamp.
        """
        all_events = []
        for timeline in self.timelines:
            all_events.extend(timeline.events)

        all_events.sort(key=lambda x: x.timestamp)
        return all_events

    def get_events_by_date(self) -> Dict[str, List[FileTimelineEvent]]:
        """Group events by date.

        Returns:
            Dictionary mapping date strings to lists of events.
        """
        events_by_date = defaultdict(list)

        for timeline in self.timelines:
            for event in timeline.events:
                date_key = event.timestamp.date().isoformat()
                events_by_date[date_key].append(event)

        # Sort events within each date
        for date_key in events_by_date:
            events_by_date[date_key].sort(key=lambda x: x.timestamp)

        return dict(events_by_date)

    def get_project_evolution(self) -> List[Dict]:
        """Get project evolution timeline showing file activity over time.

        Returns:
            List of evolution snapshots.
        """
        events_by_date = self.get_events_by_date()
        evolution = []

        cumulative_files = set()
        for date in sorted(events_by_date.keys()):
            date_events = events_by_date[date]

            # Track files created/modified on this date
            created_count = sum(
                1 for e in date_events if e.event_type == "created"
            )
            modified_count = sum(
                1 for e in date_events if e.event_type == "modified"
            )
            accessed_count = sum(
                1 for e in date_events if e.event_type == "accessed"
            )

            # Update cumulative files
            for event in date_events:
                cumulative_files.add(event.file_path)

            evolution.append(
                {
                    "date": date,
                    "created": created_count,
                    "modified": modified_count,
                    "accessed": accessed_count,
                    "total_files": len(cumulative_files),
                }
            )

        return evolution


class TimelineReporter:
    """Generates reports from file timelines."""

    def __init__(self, analyzer: TimelineAnalyzer) -> None:
        """Initialize TimelineReporter.

        Args:
            analyzer: TimelineAnalyzer instance.
        """
        self.analyzer = analyzer

    def generate_text_report(self) -> str:
        """Generate a text format timeline report.

        Returns:
            Formatted text report string.
        """
        lines = []
        lines.append("=" * 80)
        lines.append("FILE TIMELINE REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Statistics
        stats = self.analyzer.get_timeline_statistics()
        if stats:
            lines.append("STATISTICS")
            lines.append("-" * 80)
            lines.append(f"Total Files: {stats['total_files']:,}")
            lines.append(f"Total Events: {stats['total_events']:,}")
            lines.append(f"Earliest Event: {stats['earliest_event']}")
            lines.append(f"Latest Event: {stats['latest_event']}")
            lines.append(f"Time Span: {stats['time_span_days']} days")
            lines.append("")

            # Event counts
            lines.append("Event Counts:")
            for event_type, count in stats["event_counts"].items():
                lines.append(f"  {event_type.capitalize()}: {count:,}")
            lines.append("")

            # Extension counts
            if stats["extension_counts"]:
                lines.append("Files by Extension (Top 10):")
                for ext, count in sorted(
                    stats["extension_counts"].items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:10]:
                    lines.append(f"  {ext or '(no extension)'}: {count:,}")
                lines.append("")

        # Chronological timeline
        lines.append("CHRONOLOGICAL TIMELINE")
        lines.append("-" * 80)
        chronological = self.analyzer.get_chronological_timeline()

        # Group by date for readability
        events_by_date = self.analyzer.get_events_by_date()
        for date in sorted(events_by_date.keys()):
            date_events = events_by_date[date]
            lines.append(f"\n{date}")
            lines.append("-" * 40)

            for event in date_events:
                time_str = event.timestamp.strftime("%H:%M:%S")
                relative_path = event.file_path.name
                lines.append(
                    f"  {time_str} [{event.event_type.upper():8s}] {relative_path}"
                )

        # Project evolution
        lines.append("")
        lines.append("=" * 80)
        lines.append("PROJECT EVOLUTION")
        lines.append("=" * 80)
        evolution = self.analyzer.get_project_evolution()

        lines.append(f"{'Date':<12} {'Created':<10} {'Modified':<10} {'Accessed':<10} {'Total Files':<12}")
        lines.append("-" * 80)

        for snapshot in evolution[-30:]:  # Last 30 days
            lines.append(
                f"{snapshot['date']:<12} "
                f"{snapshot['created']:<10} "
                f"{snapshot['modified']:<10} "
                f"{snapshot['accessed']:<10} "
                f"{snapshot['total_files']:<12}"
            )

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def generate_json_report(self) -> str:
        """Generate a JSON format timeline report.

        Returns:
            JSON formatted report string.
        """
        stats = self.analyzer.get_timeline_statistics()
        chronological = self.analyzer.get_chronological_timeline()
        evolution = self.analyzer.get_project_evolution()

        report = {
            "generated": datetime.now().isoformat(),
            "statistics": stats,
            "timeline": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "type": event.event_type,
                    "file": str(event.file_path),
                    "size": event.size,
                }
                for event in chronological
            ],
            "evolution": evolution,
        }

        return json.dumps(report, indent=2)

    def generate_csv_report(self) -> str:
        """Generate a CSV format timeline report.

        Returns:
            CSV formatted report string.
        """
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["Timestamp", "Type", "File", "Size", "Extension"])

        # Events
        chronological = self.analyzer.get_chronological_timeline()
        for event in chronological:
            writer.writerow(
                [
                    event.timestamp.isoformat(),
                    event.event_type,
                    str(event.file_path),
                    event.size,
                    event.file_path.suffix.lower(),
                ]
            )

        return output.getvalue()


class FileTimelineGenerator:
    """Main class for generating file timelines."""

    def __init__(self, config: Dict) -> None:
        """Initialize FileTimelineGenerator.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.search_config = config.get("search", {})

        # Setup logging
        self._setup_logging()

        # Initialize collector
        self.collector = TimelineCollector(config)

    def _setup_logging(self) -> None:
        """Configure logging for the application."""
        log_level = self.config.get("logging", {}).get("level", "INFO")
        log_file = self.config.get("logging", {}).get("file", "logs/timeline.log")

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

    def generate_timeline(self, search_dir: Path) -> List[FileTimeline]:
        """Generate timeline for files in directory.

        Args:
            search_dir: Directory to analyze.

        Returns:
            List of FileTimeline objects.
        """
        logger.info(f"Collecting timelines from: {search_dir}")
        timelines = self.collector.collect_timelines(search_dir)
        logger.info(f"Collected {len(timelines)} file timelines")
        return timelines


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
        description="Generate file timelines showing creation, modification, "
        "and access times"
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
        help="Directory to analyze (overrides config)",
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

    generator = FileTimelineGenerator(config)

    # Get search directory
    search_dir = Path(config.get("search", {}).get("directory", "."))

    # Generate timelines
    timelines = generator.generate_timeline(search_dir)

    if not timelines:
        print("No files found to generate timeline.")
        sys.exit(0)

    # Analyze timelines
    analyzer = TimelineAnalyzer(timelines)
    reporter = TimelineReporter(analyzer)

    # Determine output format
    output_format = args.format or config.get("output", {}).get("format", "text")

    # Generate report
    if output_format == "json":
        report = reporter.generate_json_report()
    elif output_format == "csv":
        report = reporter.generate_csv_report()
    else:
        report = reporter.generate_text_report()

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
