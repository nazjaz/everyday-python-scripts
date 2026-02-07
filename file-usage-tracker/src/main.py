"""File Usage Tracker.

A Python script that tracks file usage frequency by monitoring access times,
organizing files by how often they are accessed or modified.
"""

import argparse
import json
import logging
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/tracker.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


class FileUsageTracker:
    """Tracks file usage frequency and organizes files by access patterns."""

    def __init__(
        self,
        database_path: Path,
        tracking_window_days: int = 30,
        organize_by: str = "frequency",
    ) -> None:
        """Initialize the file usage tracker.

        Args:
            database_path: Path to SQLite database for tracking data
            tracking_window_days: Number of days to consider for frequency calculation
            organize_by: Organization method - "frequency", "access", or "modification"

        Raises:
            ValueError: If organize_by is invalid
        """
        if organize_by not in ["frequency", "access", "modification"]:
            raise ValueError(
                "organize_by must be one of: frequency, access, modification"
            )

        self.database_path = Path(database_path).expanduser().resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.tracking_window_days = tracking_window_days
        self.organize_by = organize_by

        self.stats = {
            "files_scanned": 0,
            "access_records_added": 0,
            "files_organized": 0,
            "errors": 0,
        }

        self._init_database()

    def _init_database(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS file_access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                access_time TEXT NOT NULL,
                modification_time TEXT,
                file_size INTEGER,
                UNIQUE(file_path, access_time)
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_file_path ON file_access_log(file_path)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_access_time ON file_access_log(access_time)
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS file_metadata (
                file_path TEXT PRIMARY KEY,
                first_seen TEXT,
                last_accessed TEXT,
                last_modified TEXT,
                access_count INTEGER DEFAULT 0,
                modification_count INTEGER DEFAULT 0
            )
            """
        )

        conn.commit()
        conn.close()

        logger.info(f"Database initialized at {self.database_path}")

    def _record_file_access(self, file_path: Path) -> None:
        """Record file access in database.

        Args:
            file_path: Path to file
        """
        try:
            stat = file_path.stat()
            access_time = datetime.fromtimestamp(stat.st_atime).isoformat()
            modification_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
            file_size = stat.st_size

            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO file_access_log
                    (file_path, access_time, modification_time, file_size)
                    VALUES (?, ?, ?, ?)
                    """,
                    (str(file_path), access_time, modification_time, file_size),
                )

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO file_metadata
                    (file_path, first_seen, last_accessed, last_modified,
                     access_count, modification_count)
                    VALUES (
                        ?,
                        COALESCE((SELECT first_seen FROM file_metadata WHERE file_path = ?), ?),
                        ?,
                        ?,
                        COALESCE((SELECT access_count FROM file_metadata WHERE file_path = ?), 0) + 1,
                        COALESCE((SELECT modification_count FROM file_metadata WHERE file_path = ?), 0) + 1
                    )
                    """,
                    (
                        str(file_path),
                        str(file_path),
                        access_time,
                        str(file_path),
                        access_time,
                        modification_time,
                        str(file_path),
                        str(file_path),
                    ),
                )

                conn.commit()
                self.stats["access_records_added"] += 1

            except sqlite3.Error as e:
                logger.warning(f"Database error recording {file_path}: {e}")
                conn.rollback()
            finally:
                conn.close()

        except (OSError, PermissionError) as e:
            logger.warning(f"Cannot access file {file_path}: {e}")
            self.stats["errors"] += 1

    def _calculate_access_frequency(
        self, file_path: str, days: Optional[int] = None
    ) -> Tuple[int, int]:
        """Calculate access and modification frequency for a file.

        Args:
            file_path: Path to file
            days: Number of days to consider (None = use tracking_window_days)

        Returns:
            Tuple of (access_count, modification_count)
        """
        if days is None:
            days = self.tracking_window_days

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*) FROM file_access_log
            WHERE file_path = ? AND access_time >= ?
            """,
            (file_path, cutoff_date),
        )
        access_count = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(DISTINCT modification_time) FROM file_access_log
            WHERE file_path = ? AND modification_time >= ?
            """,
            (file_path, cutoff_date),
        )
        modification_count = cursor.fetchone()[0]

        conn.close()

        return (access_count, modification_count)

    def _get_frequency_category(
        self, access_count: int, modification_count: int
    ) -> str:
        """Categorize file by usage frequency.

        Args:
            access_count: Number of accesses
            modification_count: Number of modifications

        Returns:
            Frequency category name
        """
        total_activity = access_count + modification_count

        if total_activity >= 50:
            return "very_frequent"
        elif total_activity >= 20:
            return "frequent"
        elif total_activity >= 5:
            return "moderate"
        elif total_activity >= 1:
            return "occasional"
        else:
            return "rare"

    def track_files(
        self, paths: List[Path], recursive: bool = False
    ) -> Dict[str, int]:
        """Track file access times for files in paths.

        Args:
            paths: List of file or directory paths
            recursive: If True, recursively scan directories

        Returns:
            Dictionary with statistics
        """
        all_files: List[Path] = []

        for path in paths:
            path = Path(path).expanduser().resolve()

            if path.is_file():
                all_files.append(path)
            elif path.is_dir():
                if recursive:
                    all_files.extend(path.rglob("*"))
                else:
                    all_files.extend(path.glob("*"))

        logger.info(f"Found {len(all_files)} files to track")

        for file_path in all_files:
            if not file_path.is_file():
                continue

            self._record_file_access(file_path)
            self.stats["files_scanned"] += 1

        logger.info("Tracking complete")
        return self.stats.copy()

    def organize_files(
        self,
        source_paths: List[Path],
        destination_root: Path,
        recursive: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, int]:
        """Organize files by usage frequency.

        Args:
            source_paths: List of source file or directory paths
            destination_root: Root directory for organized files
            recursive: If True, recursively scan directories
            dry_run: If True, simulate without moving files

        Returns:
            Dictionary with statistics
        """
        all_files: List[Path] = []

        for path in source_paths:
            path = Path(path).expanduser().resolve()

            if path.is_file():
                all_files.append(path)
            elif path.is_dir():
                if recursive:
                    all_files.extend(path.rglob("*"))
                else:
                    all_files.extend(path.glob("*"))

        destination_root = Path(destination_root).expanduser().resolve()
        destination_root.mkdir(parents=True, exist_ok=True)

        logger.info(f"Organizing {len(all_files)} files by {self.organize_by}")

        for file_path in all_files:
            if not file_path.is_file():
                continue

            try:
                access_count, modification_count = self._calculate_access_frequency(
                    str(file_path)
                )

                if self.organize_by == "frequency":
                    category = self._get_frequency_category(
                        access_count, modification_count
                    )
                elif self.organize_by == "access":
                    if access_count >= 20:
                        category = "high_access"
                    elif access_count >= 5:
                        category = "medium_access"
                    else:
                        category = "low_access"
                else:
                    if modification_count >= 10:
                        category = "high_modification"
                    elif modification_count >= 3:
                        category = "medium_modification"
                    else:
                        category = "low_modification"

                dest_path = destination_root / category / file_path.name

                if not dry_run:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    if file_path != dest_path:
                        import shutil
                        shutil.move(str(file_path), str(dest_path))
                        logger.info(f"Moved: {file_path} -> {dest_path}")

                self.stats["files_organized"] += 1

            except Exception as e:
                logger.warning(f"Error organizing {file_path}: {e}")
                self.stats["errors"] += 1

        return self.stats.copy()

    def get_usage_report(
        self, paths: List[Path], recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """Generate usage report for files.

        Args:
            paths: List of file or directory paths
            recursive: If True, recursively scan directories

        Returns:
            List of file usage dictionaries
        """
        all_files: List[Path] = []

        for path in paths:
            path = Path(path).expanduser().resolve()

            if path.is_file():
                all_files.append(path)
            elif path.is_dir():
                if recursive:
                    all_files.extend(path.rglob("*"))
                else:
                    all_files.extend(path.glob("*"))

        report_data: List[Dict[str, any]] = []

        for file_path in all_files:
            if not file_path.is_file():
                continue

            try:
                access_count, modification_count = self._calculate_access_frequency(
                    str(file_path)
                )
                category = self._get_frequency_category(access_count, modification_count)

                stat = file_path.stat()
                file_info = {
                    "path": str(file_path),
                    "name": file_path.name,
                    "size": stat.st_size,
                    "access_count": access_count,
                    "modification_count": modification_count,
                    "frequency_category": category,
                    "last_accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
                    "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }

                report_data.append(file_info)

            except (OSError, PermissionError) as e:
                logger.warning(f"Cannot access {file_path}: {e}")

        return sorted(
            report_data, key=lambda x: x["access_count"] + x["modification_count"], reverse=True
        )

    def format_report(self, report_data: List[Dict[str, Any]]) -> str:
        """Format usage report as text.

        Args:
            report_data: List of file usage dictionaries

        Returns:
            Formatted string report
        """
        if not report_data:
            return "No file usage data found."

        lines = [
            "File Usage Frequency Report",
            "=" * 80,
            "",
            f"Files analyzed: {len(report_data)}",
            f"Tracking window: {self.tracking_window_days} days",
            "",
            "-" * 80,
            "",
        ]

        for file_info in report_data:
            lines.append(f"File: {file_info['path']}")
            lines.append(f"  Access count: {file_info['access_count']}")
            lines.append(f"  Modification count: {file_info['modification_count']}")
            lines.append(f"  Frequency category: {file_info['frequency_category']}")
            lines.append(f"  Last accessed: {file_info['last_accessed']}")
            lines.append(f"  Last modified: {file_info['last_modified']}")
            lines.append("")

        return "\n".join(lines)


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


def main() -> int:
    """Main entry point for the script.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        description="Track file usage frequency and organize by access patterns"
    )
    parser.add_argument(
        "paths",
        type=str,
        nargs="+",
        help="File paths or directory paths to track",
    )
    parser.add_argument(
        "--database",
        type=str,
        default="file_usage.db",
        help="Path to SQLite database file (default: file_usage.db)",
    )
    parser.add_argument(
        "--track",
        action="store_true",
        help="Track file access times (record current state)",
    )
    parser.add_argument(
        "--organize",
        type=str,
        default=None,
        help="Organize files to destination directory",
    )
    parser.add_argument(
        "--organize-by",
        type=str,
        choices=["frequency", "access", "modification"],
        default="frequency",
        help="Organization method (default: frequency)",
    )
    parser.add_argument(
        "--window-days",
        type=int,
        default=30,
        help="Tracking window in days (default: 30)",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively scan directories",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate organization without moving files",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate usage frequency report",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path for report",
    )
    parser.add_argument(
        "--json",
        type=str,
        default=None,
        help="Output JSON file path for report",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file (YAML)",
    )

    args = parser.parse_args()

    try:
        database_path = Path(args.database)
        tracking_window_days = args.window_days
        organize_by = args.organize_by
        recursive = args.recursive

        if args.config:
            config = load_config(Path(args.config))
            if "database" in config:
                database_path = Path(config["database"])
            if "tracking_window_days" in config:
                tracking_window_days = config["tracking_window_days"]
            if "organize_by" in config:
                organize_by = config["organize_by"]
            if "recursive" in config:
                recursive = config["recursive"]

        tracker = FileUsageTracker(
            database_path=database_path,
            tracking_window_days=tracking_window_days,
            organize_by=organize_by,
        )

        file_paths = [Path(p) for p in args.paths]

        if args.track:
            stats = tracker.track_files(file_paths, recursive=recursive)
            print("\nTracking Statistics:")
            print(f"  Files scanned: {stats['files_scanned']}")
            print(f"  Access records added: {stats['access_records_added']}")
            print(f"  Errors: {stats['errors']}")

        if args.organize:
            stats = tracker.organize_files(
                file_paths,
                Path(args.organize),
                recursive=recursive,
                dry_run=args.dry_run,
            )
            print("\nOrganization Statistics:")
            print(f"  Files organized: {stats['files_organized']}")
            print(f"  Errors: {stats['errors']}")

        if args.report:
            report_data = tracker.get_usage_report(file_paths, recursive=recursive)
            report_text = tracker.format_report(report_data)

            if args.json:
                json_path = Path(args.json)
                json_path.parent.mkdir(parents=True, exist_ok=True)
                with open(json_path, "w") as f:
                    json.dump(report_data, f, indent=2, default=str)
                logger.info(f"JSON report saved to {json_path}")

            if args.output:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w") as f:
                    f.write(report_text)
                logger.info(f"Report saved to {output_path}")
            else:
                print(report_text)

        if not (args.track or args.organize or args.report):
            stats = tracker.track_files(file_paths, recursive=recursive)
            print("\nTracking Statistics:")
            print(f"  Files scanned: {stats['files_scanned']}")
            print(f"  Access records added: {stats['access_records_added']}")

        return 0

    except (ValueError, FileNotFoundError) as e:
        logger.error(f"Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
