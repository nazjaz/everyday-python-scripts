"""System Cleanup - CLI tool for identifying and removing system artifacts.

This module provides a command-line tool for identifying and removing system
artifacts, cache files, and temporary system files that are safe to delete.
"""

import argparse
import logging
import logging.handlers
import os
import platform
import shutil
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


class SystemCleanup:
    """Identifies and removes system artifacts and cache files."""

    def __init__(self, config: Dict) -> None:
        """Initialize SystemCleanup.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.cleanup_config = config.get("cleanup", {})
        self.safety_config = config.get("safety", {})
        self.platform_name = platform.system().lower()

        # Setup logging
        self._setup_logging()

        # Get platform-specific paths
        self.cache_paths = self._get_cache_paths()
        self.temp_paths = self._get_temp_paths()
        self.artifact_paths = self._get_artifact_paths()

    def _setup_logging(self) -> None:
        """Configure logging for the application."""
        log_level = self.config.get("logging", {}).get("level", "INFO")
        log_file = self.config.get("logging", {}).get("file", "logs/cleanup.log")

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

    def _get_cache_paths(self) -> List[Path]:
        """Get platform-specific cache directory paths.

        Returns:
            List of cache directory paths.
        """
        cache_paths = []

        if self.platform_name == "darwin":  # macOS
            cache_paths.extend(
                [
                    Path.home() / "Library" / "Caches",
                    Path("/Library/Caches"),
                    Path("/System/Library/Caches"),
                ]
            )
        elif self.platform_name == "windows":
            cache_paths.extend(
                [
                    Path(os.environ.get("LOCALAPPDATA", "")) / "Temp",
                    Path(os.environ.get("TEMP", "")),
                    Path(os.environ.get("TMP", "")),
                ]
            )
        else:  # Linux and others
            cache_paths.extend(
                [
                    Path.home() / ".cache",
                    Path("/var/cache"),
                    Path("/tmp"),
                ]
            )

        # Filter out non-existent paths
        return [p for p in cache_paths if p and p.exists()]

    def _get_temp_paths(self) -> List[Path]:
        """Get platform-specific temporary directory paths.

        Returns:
            List of temporary directory paths.
        """
        temp_paths = []

        # Standard temp directory
        temp_dir = Path(os.environ.get("TEMP", os.environ.get("TMP", "/tmp")))
        if temp_dir.exists():
            temp_paths.append(temp_dir)

        if self.platform_name == "darwin":  # macOS
            temp_paths.extend(
                [
                    Path("/private/var/folders"),
                    Path("/private/var/tmp"),
                ]
            )
        elif self.platform_name == "windows":
            temp_paths.extend(
                [
                    Path(os.environ.get("LOCALAPPDATA", "")) / "Temp",
                    Path(os.environ.get("TEMP", "")),
                ]
            )
        else:  # Linux
            temp_paths.extend(
                [
                    Path("/tmp"),
                    Path("/var/tmp"),
                ]
            )

        return [p for p in temp_paths if p and p.exists()]

    def _get_artifact_paths(self) -> List[Path]:
        """Get platform-specific system artifact paths.

        Returns:
            List of artifact directory paths.
        """
        artifact_paths = []

        if self.platform_name == "darwin":  # macOS
            artifact_paths.extend(
                [
                    Path.home() / "Library" / "Logs",
                    Path.home() / ".Trash",
                    Path("/private/var/log"),
                ]
            )
        elif self.platform_name == "windows":
            artifact_paths.extend(
                [
                    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "INetCache",
                    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "History",
                    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Temporary Internet Files",
                ]
            )
        else:  # Linux
            artifact_paths.extend(
                [
                    Path("/var/log"),
                    Path.home() / ".local" / "share" / "Trash",
                ]
            )

        return [p for p in artifact_paths if p and p.exists()]

    def is_safe_to_delete(self, file_path: Path) -> bool:
        """Check if file is safe to delete.

        Args:
            file_path: Path to file to check.

        Returns:
            True if safe to delete, False otherwise.
        """
        # Never delete certain file types
        unsafe_extensions = self.safety_config.get("unsafe_extensions", [])
        if file_path.suffix.lower() in unsafe_extensions:
            return False

        # Never delete files matching unsafe patterns
        unsafe_patterns = self.safety_config.get("unsafe_patterns", [])
        for pattern in unsafe_patterns:
            if pattern in file_path.name.lower():
                return False

        # Never delete files in protected directories
        protected_dirs = self.safety_config.get("protected_directories", [])
        for protected in protected_dirs:
            if protected in str(file_path):
                return False

        # Check minimum age requirement
        min_age_days = self.safety_config.get("min_age_days", 0)
        if min_age_days > 0:
            try:
                stat_info = file_path.stat()
                mod_time = datetime.fromtimestamp(stat_info.st_mtime)
                age_days = (datetime.now() - mod_time).days
                if age_days < min_age_days:
                    return False
            except (OSError, PermissionError):
                return False

        return True

    def scan_cache_files(self) -> List[Tuple[Path, int]]:
        """Scan for cache files.

        Returns:
            List of tuples (file_path, size_bytes).
        """
        cache_files = []
        cache_patterns = self.cleanup_config.get("cache_patterns", [])

        for cache_dir in self.cache_paths:
            try:
                for root, dirs, filenames in os.walk(cache_dir):
                    # Skip certain directories
                    dirs[:] = [d for d in dirs if d not in [".git", "__pycache__"]]

                    for filename in filenames:
                        file_path = Path(root) / filename

                        # Check if matches cache patterns
                        matches = False
                        for pattern in cache_patterns:
                            if pattern in filename.lower() or file_path.suffix.lower() in [".cache", ".tmp"]:
                                matches = True
                                break

                        if matches and self.is_safe_to_delete(file_path):
                            try:
                                size = file_path.stat().st_size
                                cache_files.append((file_path, size))
                            except (OSError, PermissionError):
                                continue

            except (OSError, PermissionError) as e:
                logger.warning(
                    f"Cannot scan cache directory {cache_dir}: {e}",
                    extra={"directory": str(cache_dir), "error": str(e)},
                )

        return cache_files

    def scan_temp_files(self) -> List[Tuple[Path, int]]:
        """Scan for temporary files.

        Returns:
            List of tuples (file_path, size_bytes).
        """
        temp_files = []
        temp_patterns = self.cleanup_config.get("temp_patterns", [".tmp", ".temp", ".swp", ".bak"])

        for temp_dir in self.temp_paths:
            try:
                for root, dirs, filenames in os.walk(temp_dir):
                    # Limit depth for temp directories
                    depth = root.replace(str(temp_dir), "").count(os.sep)
                    if depth > 3:  # Limit to 3 levels deep
                        dirs[:] = []
                        continue

                    for filename in filenames:
                        file_path = Path(root) / filename

                        # Check if matches temp patterns
                        matches = False
                        for pattern in temp_patterns:
                            if pattern in filename.lower() or file_path.suffix.lower() in temp_patterns:
                                matches = True
                                break

                        if matches and self.is_safe_to_delete(file_path):
                            try:
                                size = file_path.stat().st_size
                                temp_files.append((file_path, size))
                            except (OSError, PermissionError):
                                continue

            except (OSError, PermissionError) as e:
                logger.warning(
                    f"Cannot scan temp directory {temp_dir}: {e}",
                    extra={"directory": str(temp_dir), "error": str(e)},
                )

        return temp_files

    def scan_artifact_files(self) -> List[Tuple[Path, int]]:
        """Scan for system artifact files.

        Returns:
            List of tuples (file_path, size_bytes).
        """
        artifact_files = []
        artifact_patterns = self.cleanup_config.get("artifact_patterns", [".log", ".old", ".bak"])

        for artifact_dir in self.artifact_paths:
            try:
                for root, dirs, filenames in os.walk(artifact_dir):
                    # Skip certain directories
                    dirs[:] = [d for d in dirs if d not in [".git", "__pycache__"]]

                    for filename in filenames:
                        file_path = Path(root) / filename

                        # Check if matches artifact patterns
                        matches = False
                        for pattern in artifact_patterns:
                            if pattern in filename.lower() or file_path.suffix.lower() in artifact_patterns:
                                matches = True
                                break

                        if matches and self.is_safe_to_delete(file_path):
                            try:
                                size = file_path.stat().st_size
                                artifact_files.append((file_path, size))
                            except (OSError, PermissionError):
                                continue

            except (OSError, PermissionError) as e:
                logger.warning(
                    f"Cannot scan artifact directory {artifact_dir}: {e}",
                    extra={"directory": str(artifact_dir), "error": str(e)},
                )

        return artifact_files

    def delete_file(self, file_path: Path, dry_run: bool = False) -> Tuple[bool, str]:
        """Delete a file safely.

        Args:
            file_path: Path to file to delete.
            dry_run: If True, only report what would be deleted.

        Returns:
            Tuple of (success, message).
        """
        if not self.is_safe_to_delete(file_path):
            return (False, "File not safe to delete")

        if dry_run:
            return (True, f"[DRY RUN] Would delete: {file_path}")

        try:
            if file_path.is_file():
                file_path.unlink()
                return (True, f"Deleted file: {file_path}")
            elif file_path.is_dir():
                shutil.rmtree(file_path)
                return (True, f"Deleted directory: {file_path}")
            else:
                return (False, f"Path is not a file or directory: {file_path}")

        except (OSError, PermissionError) as e:
            error_msg = f"Failed to delete {file_path}: {e}"
            logger.error(error_msg, extra={"file_path": str(file_path), "error": str(e)})
            return (False, error_msg)

    def cleanup(
        self, dry_run: bool = False, max_size_mb: Optional[int] = None
    ) -> Dict[str, any]:
        """Perform system cleanup.

        Args:
            dry_run: If True, only report what would be deleted.
            max_size_mb: Maximum total size to delete in MB (None for no limit).

        Returns:
            Dictionary with cleanup statistics.
        """
        results = {
            "scanned": {"cache": 0, "temp": 0, "artifacts": 0},
            "found": {"cache": 0, "temp": 0, "artifacts": 0},
            "deleted": {"cache": 0, "temp": 0, "artifacts": 0},
            "failed": {"cache": 0, "temp": 0, "artifacts": 0},
            "size_freed": {"cache": 0, "temp": 0, "artifacts": 0},
            "total_size_freed": 0,
        }

        logger.info("Starting system cleanup scan")

        # Scan for files
        cache_files = self.scan_cache_files()
        temp_files = self.scan_temp_files()
        artifact_files = self.scan_artifact_files()

        results["scanned"]["cache"] = len(cache_files)
        results["scanned"]["temp"] = len(temp_files)
        results["scanned"]["artifacts"] = len(artifact_files)

        results["found"]["cache"] = len(cache_files)
        results["found"]["temp"] = len(temp_files)
        results["found"]["artifacts"] = len(artifact_files)

        # Process files
        all_files = [
            ("cache", cache_files),
            ("temp", temp_files),
            ("artifacts", artifact_files),
        ]

        total_size = 0
        for category, files in all_files:
            for file_path, size in files:
                if max_size_mb and total_size / (1024 * 1024) >= max_size_mb:
                    break

                success, message = self.delete_file(file_path, dry_run=dry_run)

                if success:
                    results["deleted"][category] += 1
                    results["size_freed"][category] += size
                    results["total_size_freed"] += size
                    total_size += size
                    logger.info(message, extra={"file_path": str(file_path), "category": category})
                else:
                    results["failed"][category] += 1
                    logger.warning(message, extra={"file_path": str(file_path), "category": category})

        return results

    def format_size(self, size_bytes: int) -> str:
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
        description="Identify and remove system artifacts, cache files, "
        "and temporary system files that are safe to delete"
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
        "--dry-run",
        action="store_true",
        help="Perform a dry run without deleting files",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        help="Maximum total size to delete in MB (default: no limit)",
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

    cleanup = SystemCleanup(config)

    if args.dry_run:
        logger.info("Running in dry-run mode - no files will be deleted")

    results = cleanup.cleanup(dry_run=args.dry_run, max_size_mb=args.max_size)

    # Print summary
    print("\n" + "=" * 60)
    print("System Cleanup Summary")
    print("=" * 60)
    print(f"\nCache Files:")
    print(f"  Scanned: {results['scanned']['cache']}")
    print(f"  Found: {results['found']['cache']}")
    print(f"  Deleted: {results['deleted']['cache']}")
    print(f"  Failed: {results['failed']['cache']}")
    print(f"  Size freed: {cleanup.format_size(results['size_freed']['cache'])}")

    print(f"\nTemporary Files:")
    print(f"  Scanned: {results['scanned']['temp']}")
    print(f"  Found: {results['found']['temp']}")
    print(f"  Deleted: {results['deleted']['temp']}")
    print(f"  Failed: {results['failed']['temp']}")
    print(f"  Size freed: {cleanup.format_size(results['size_freed']['temp'])}")

    print(f"\nSystem Artifacts:")
    print(f"  Scanned: {results['scanned']['artifacts']}")
    print(f"  Found: {results['found']['artifacts']}")
    print(f"  Deleted: {results['deleted']['artifacts']}")
    print(f"  Failed: {results['failed']['artifacts']}")
    print(f"  Size freed: {cleanup.format_size(results['size_freed']['artifacts'])}")

    print(f"\nTotal Size Freed: {cleanup.format_size(results['total_size_freed'])}")
    print("=" * 60)

    if results["failed"]["cache"] + results["failed"]["temp"] + results["failed"]["artifacts"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
