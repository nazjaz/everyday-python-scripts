"""Download Cleanup Script.

A Python script that cleans up old download files based on age and type,
moving them to archive folders or deleting them after a retention period.
"""

import argparse
import logging
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/cleanup.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


class DownloadCleanup:
    """Cleans up old download files based on age and type."""

    FILE_TYPE_CATEGORIES = {
        "images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"},
        "documents": {
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".txt",
            ".rtf",
            ".odt",
            ".ods",
            ".odp",
        },
        "videos": {".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mkv", ".m4v"},
        "audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"},
        "archives": {
            ".zip",
            ".rar",
            ".7z",
            ".tar",
            ".gz",
            ".bz2",
            ".xz",
            ".tar.gz",
            ".tar.bz2",
        },
        "executables": {".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".app"},
        "code": {
            ".py",
            ".js",
            ".html",
            ".css",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".json",
            ".xml",
            ".yaml",
            ".yml",
        },
    }

    def __init__(
        self,
        download_folders: List[Path],
        retention_days: int,
        archive_root: Optional[Path] = None,
        action: str = "archive",
        file_types: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        dry_run: bool = False,
    ) -> None:
        """Initialize the cleanup with configuration.

        Args:
            download_folders: List of download folder paths to clean
            retention_days: Number of days to retain files before cleanup
            archive_root: Root directory for archived files (required if action is archive)
            action: Action to take - "archive" or "delete" (default: archive)
            file_types: List of file type categories to process (None = all)
            exclude_patterns: List of filename patterns to exclude
            dry_run: If True, simulate operations without moving/deleting files

        Raises:
            ValueError: If action is invalid or archive_root missing for archive action
        """
        if action not in ["archive", "delete"]:
            raise ValueError("action must be either 'archive' or 'delete'")

        if action == "archive" and archive_root is None:
            raise ValueError("archive_root is required when action is 'archive'")

        self.download_folders = [
            Path(f).expanduser().resolve() for f in download_folders
        ]
        self.retention_days = retention_days
        self.archive_root = (
            Path(archive_root).expanduser().resolve() if archive_root else None
        )
        self.action = action
        self.file_types = set(file_types) if file_types else None
        self.exclude_patterns = exclude_patterns or []
        self.dry_run = dry_run

        self.cutoff_date = datetime.now() - timedelta(days=retention_days)

        self.stats = {
            "scanned": 0,
            "archived": 0,
            "deleted": 0,
            "skipped": 0,
            "errors": 0,
        }

        self._validate_paths()

    def _validate_paths(self) -> None:
        """Validate that download folders exist.

        Raises:
            FileNotFoundError: If download folder does not exist
            PermissionError: If archive root is not writable
        """
        for download_folder in self.download_folders:
            if not download_folder.exists():
                raise FileNotFoundError(
                    f"Download folder does not exist: {download_folder}"
                )
            if not download_folder.is_dir():
                raise NotADirectoryError(
                    f"Download path is not a directory: {download_folder}"
                )

        if self.archive_root:
            self.archive_root.mkdir(parents=True, exist_ok=True)

            if not self.archive_root.is_dir():
                raise NotADirectoryError(
                    f"Archive root is not a directory: {self.archive_root}"
                )

            try:
                test_file = self.archive_root / ".write_test"
                test_file.touch()
                test_file.unlink()
            except (PermissionError, OSError) as e:
                raise PermissionError(
                    f"Archive root is not writable: {self.archive_root}"
                ) from e

    def _get_file_category(self, file_path: Path) -> Optional[str]:
        """Determine file category based on extension.

        Args:
            file_path: Path to file

        Returns:
            Category name or None if not categorized
        """
        suffix = file_path.suffix.lower()
        if not suffix:
            return None

        for category, extensions in self.FILE_TYPE_CATEGORIES.items():
            if suffix in extensions:
                return category

        return "other"

    def _should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed based on filters.

        Args:
            file_path: Path to file

        Returns:
            True if file should be processed, False otherwise
        """
        if self.file_types:
            category = self._get_file_category(file_path)
            if category not in self.file_types:
                return False

        for pattern in self.exclude_patterns:
            if pattern in file_path.name:
                return False

        return True

    def _is_file_old(self, file_path: Path) -> bool:
        """Check if file is older than retention period.

        Args:
            file_path: Path to file

        Returns:
            True if file is older than retention period, False otherwise
        """
        try:
            modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            return modified_time < self.cutoff_date
        except (OSError, PermissionError) as e:
            logger.warning(
                f"Cannot access file modification time: {file_path} - {e}",
                extra={"file": str(file_path)},
            )
            return False

    def _get_archive_path(self, file_path: Path, category: str) -> Path:
        """Generate archive path for file based on category.

        Args:
            file_path: Source file path
            category: File category

        Returns:
            Destination archive path
        """
        if not self.archive_root:
            raise ValueError("Archive root not set")

        year_month = datetime.fromtimestamp(file_path.stat().st_mtime).strftime(
            "%Y-%m"
        )
        archive_dir = self.archive_root / category / year_month
        return archive_dir / file_path.name

    def _archive_file(self, file_path: Path) -> bool:
        """Archive file to organized archive directory.

        Args:
            file_path: Path to file to archive

        Returns:
            True if archive was successful, False otherwise
        """
        try:
            category = self._get_file_category(file_path) or "other"
            archive_path = self._get_archive_path(file_path, category)

            if self.dry_run:
                logger.info(
                    f"[DRY RUN] Would archive: {file_path} -> {archive_path}",
                    extra={
                        "source": str(file_path),
                        "destination": str(archive_path),
                        "category": category,
                    },
                )
                return True

            archive_path.parent.mkdir(parents=True, exist_ok=True)

            if archive_path.exists():
                counter = 1
                stem = archive_path.stem
                suffix = archive_path.suffix
                parent = archive_path.parent
                while archive_path.exists():
                    archive_path = parent / f"{stem}_copy{counter}{suffix}"
                    counter += 1

            shutil.move(str(file_path), str(archive_path))
            logger.info(
                f"Archived file: {file_path} -> {archive_path}",
                extra={
                    "source": str(file_path),
                    "destination": str(archive_path),
                    "category": category,
                },
            )
            return True

        except (shutil.Error, OSError, PermissionError) as e:
            error_msg = f"Failed to archive {file_path}: {e}"
            logger.error(error_msg, extra={"file": str(file_path), "error": str(e)})
            return False

    def _delete_file(self, file_path: Path) -> bool:
        """Delete file permanently.

        Args:
            file_path: Path to file to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            if self.dry_run:
                logger.info(
                    f"[DRY RUN] Would delete: {file_path}",
                    extra={"file": str(file_path)},
                )
                return True

            file_path.unlink()
            logger.info(f"Deleted file: {file_path}", extra={"file": str(file_path)})
            return True

        except (OSError, PermissionError) as e:
            error_msg = f"Failed to delete {file_path}: {e}"
            logger.error(error_msg, extra={"file": str(file_path), "error": str(e)})
            return False

    def _process_file(self, file_path: Path) -> None:
        """Process a single file for cleanup.

        Args:
            file_path: Path to file to process
        """
        self.stats["scanned"] += 1

        if not self._should_process_file(file_path):
            self.stats["skipped"] += 1
            logger.debug(f"Skipped file (filtered): {file_path}")
            return

        if not self._is_file_old(file_path):
            self.stats["skipped"] += 1
            logger.debug(f"Skipped file (not old enough): {file_path}")
            return

        try:
            if self.action == "archive":
                if self._archive_file(file_path):
                    self.stats["archived"] += 1
                else:
                    self.stats["errors"] += 1
            elif self.action == "delete":
                if self._delete_file(file_path):
                    self.stats["deleted"] += 1
                else:
                    self.stats["errors"] += 1

        except Exception as e:
            self.stats["errors"] += 1
            logger.exception(
                f"Unexpected error processing {file_path}: {e}",
                extra={"file": str(file_path)},
            )

    def cleanup(self) -> Dict[str, int]:
        """Perform cleanup of old download files.

        Returns:
            Dictionary with statistics:
                - scanned: Number of files scanned
                - archived: Number of files archived
                - deleted: Number of files deleted
                - skipped: Number of files skipped
                - errors: Number of files with errors
        """
        logger.info(
            f"Starting cleanup of {len(self.download_folders)} download folder(s)",
            extra={
                "download_folders": [str(f) for f in self.download_folders],
                "retention_days": self.retention_days,
                "cutoff_date": self.cutoff_date.isoformat(),
                "action": self.action,
            },
        )

        for download_folder in self.download_folders:
            logger.info(f"Processing download folder: {download_folder}")

            for file_path in download_folder.rglob("*"):
                if file_path.is_file():
                    self._process_file(file_path)

        logger.info(
            "Cleanup complete",
            extra={
                "scanned": self.stats["scanned"],
                "archived": self.stats["archived"],
                "deleted": self.stats["deleted"],
                "skipped": self.stats["skipped"],
                "errors": self.stats["errors"],
            },
        )

        return self.stats.copy()

    def get_summary(self) -> str:
        """Generate a summary report of cleanup operations.

        Returns:
            Formatted string summary
        """
        lines = [
            "Cleanup Summary",
            "=" * 80,
            f"Retention Period: {self.retention_days} days",
            f"Cutoff Date: {self.cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Action: {self.action}",
            "",
            "Statistics:",
            f"  Files Scanned: {self.stats['scanned']}",
            f"  Files Archived: {self.stats['archived']}",
            f"  Files Deleted: {self.stats['deleted']}",
            f"  Files Skipped: {self.stats['skipped']}",
            f"  Errors: {self.stats['errors']}",
        ]

        if self.dry_run:
            lines.append("")
            lines.append("NOTE: This was a dry run - no files were actually moved or deleted.")

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
        description="Clean up old download files based on age and type"
    )
    parser.add_argument(
        "--download-folders",
        type=str,
        nargs="+",
        required=True,
        help="Download folder paths to clean (space-separated)",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        required=True,
        help="Number of days to retain files before cleanup",
    )
    parser.add_argument(
        "--archive-root",
        type=str,
        default=None,
        help="Root directory for archived files (required if action is archive)",
    )
    parser.add_argument(
        "--action",
        type=str,
        choices=["archive", "delete"],
        default="archive",
        help="Action to take: archive or delete (default: archive)",
    )
    parser.add_argument(
        "--file-types",
        type=str,
        nargs="+",
        default=None,
        help="File type categories to process (e.g., images documents)",
    )
    parser.add_argument(
        "--exclude-patterns",
        type=str,
        nargs="+",
        default=None,
        help="Filename patterns to exclude from cleanup",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate operations without moving/deleting files",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file (YAML)",
    )

    args = parser.parse_args()

    try:
        download_folders = [Path(f) for f in args.download_folders]
        retention_days = args.retention_days
        archive_root = Path(args.archive_root) if args.archive_root else None
        action = args.action
        file_types = args.file_types
        exclude_patterns = args.exclude_patterns
        dry_run = args.dry_run

        if args.config:
            config = load_config(Path(args.config))
            if "download_folders" in config:
                download_folders = [Path(f) for f in config["download_folders"]]
            if "retention_days" in config:
                retention_days = config["retention_days"]
            if "archive_root" in config:
                archive_root = Path(config["archive_root"]) if config["archive_root"] else None
            if "action" in config:
                action = config["action"]
            if "file_types" in config:
                file_types = config["file_types"]
            if "exclude_patterns" in config:
                exclude_patterns = config["exclude_patterns"]

        cleanup = DownloadCleanup(
            download_folders=download_folders,
            retention_days=retention_days,
            archive_root=archive_root,
            action=action,
            file_types=file_types,
            exclude_patterns=exclude_patterns,
            dry_run=dry_run,
        )

        stats = cleanup.cleanup()
        summary = cleanup.get_summary()

        print("\n" + summary)

        return 0

    except (
        ValueError,
        FileNotFoundError,
        NotADirectoryError,
        PermissionError,
    ) as e:
        logger.error(f"Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
