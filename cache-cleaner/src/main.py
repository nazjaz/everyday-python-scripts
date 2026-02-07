"""Cache Cleaner - CLI tool for cleaning system cache files.

This module provides a command-line tool for cleaning cache files from
common cache directories with age-based filtering and size reporting.
"""

import argparse
import logging
import logging.handlers
import os
import platform
import re
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class CacheCleaner:
    """Cleans cache files from system directories."""

    def __init__(self, config: Dict) -> None:
        """Initialize CacheCleaner.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.filter_config = config.get("filtering", {})
        self.safety_config = config.get("safety", {})
        self.report_config = config.get("reporting", {})
        
        # Compile regex patterns
        self.include_patterns = [
            re.compile(pattern) for pattern in config.get("include_patterns", [])
        ]
        self.exclude_patterns = [
            re.compile(pattern) for pattern in config.get("exclude_patterns", [])
        ]
        self.exclude_directories = [
            re.compile(pattern) for pattern in config.get("exclude_directories", [])
        ]

    def get_cache_directories(self) -> List[Path]:
        """Get cache directories for current platform.

        Returns:
            List of cache directory paths.
        """
        system = platform.system().lower()
        cache_dirs_config = self.config.get("cache_directories", {})
        
        directories = []
        
        if system == "darwin":
            dirs = cache_dirs_config.get("macos", [])
        elif system == "linux":
            dirs = cache_dirs_config.get("linux", [])
        elif system == "windows":
            dirs = cache_dirs_config.get("windows", [])
        else:
            logger.warning(f"Unknown platform: {system}, using Linux defaults")
            dirs = cache_dirs_config.get("linux", [])
        
        for dir_path in dirs:
            # Expand environment variables and user home
            expanded = os.path.expanduser(os.path.expandvars(dir_path))
            path = Path(expanded)
            
            if path.exists():
                directories.append(path)
            else:
                logger.debug(f"Cache directory does not exist: {path}")
        
        return directories

    def should_include_file(self, file_path: Path) -> bool:
        """Check if file should be included for cleanup.

        Args:
            file_path: Path to file.

        Returns:
            True if file should be included.
        """
        filename = file_path.name
        
        # Check hidden files
        if not self.filter_config.get("include_hidden", True) and filename.startswith("."):
            return False
        
        # Check empty files
        try:
            if not self.filter_config.get("include_empty", True) and file_path.stat().st_size == 0:
                return False
        except (OSError, IOError):
            return False
        
        # Check include patterns
        if self.include_patterns:
            matches = any(pattern.search(filename) for pattern in self.include_patterns)
            if not matches:
                return False
        
        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if pattern.search(filename):
                return False
        
        return True

    def should_exclude_directory(self, dir_path: Path) -> bool:
        """Check if directory should be excluded.

        Args:
            dir_path: Path to directory.

        Returns:
            True if directory should be excluded.
        """
        dirname = dir_path.name
        
        for pattern in self.exclude_directories:
            if pattern.search(dirname):
                return True
        
        return False

    def is_file_old_enough(self, file_path: Path) -> bool:
        """Check if file is old enough based on age filter.

        Args:
            file_path: Path to file.

        Returns:
            True if file meets age requirements.
        """
        try:
            file_stat = file_path.stat()
            file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
            now = datetime.now()
            age = now - file_mtime
            
            min_age_days = self.filter_config.get("min_age_days", 7)
            max_age_days = self.filter_config.get("max_age_days", 0)
            
            if age.days < min_age_days:
                return False
            
            if max_age_days > 0 and age.days > max_age_days:
                return False
            
            return True
            
        except (OSError, IOError) as e:
            logger.debug(f"Error checking file age for {file_path}: {e}")
            return False

    def is_file_size_acceptable(self, file_path: Path) -> bool:
        """Check if file size is within limits.

        Args:
            file_path: Path to file.

        Returns:
            True if file size is acceptable.
        """
        try:
            file_size = file_path.stat().st_size
            
            min_size = self.filter_config.get("min_file_size", 0)
            if min_size > 0 and file_size < min_size:
                return False
            
            max_size = self.filter_config.get("max_file_size", 0)
            if max_size > 0 and file_size > max_size:
                return False
            
            return True
            
        except (OSError, IOError):
            return False

    def scan_directory(self, directory: Path, recursive: bool = True) -> List[Tuple[Path, int, datetime]]:
        """Scan directory for cache files.

        Args:
            directory: Directory to scan.
            recursive: Whether to scan recursively.

        Returns:
            List of tuples (file_path, size, modification_time).
        """
        files = []
        
        if not directory.exists() or not directory.is_dir():
            logger.warning(f"Directory does not exist or is not a directory: {directory}")
            return files
        
        if self.should_exclude_directory(directory):
            logger.debug(f"Excluding directory: {directory}")
            return files
        
        try:
            if recursive:
                file_paths = directory.rglob("*")
            else:
                file_paths = directory.glob("*")
            
            for file_path in file_paths:
                if not file_path.is_file():
                    continue
                
                # Check if parent directory should be excluded
                if self.should_exclude_directory(file_path.parent):
                    continue
                
                if not self.should_include_file(file_path):
                    continue
                
                if not self.is_file_old_enough(file_path):
                    continue
                
                if not self.is_file_size_acceptable(file_path):
                    continue
                
                try:
                    file_stat = file_path.stat()
                    files.append((
                        file_path,
                        file_stat.st_size,
                        datetime.fromtimestamp(file_stat.st_mtime)
                    ))
                except (OSError, IOError) as e:
                    logger.debug(f"Error getting file stats for {file_path}: {e}")
        
        except PermissionError as e:
            logger.warning(f"Permission denied accessing {directory}: {e}")
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
        
        return files

    def scan_all_directories(self) -> List[Tuple[Path, int, datetime]]:
        """Scan all configured cache directories.

        Returns:
            List of tuples (file_path, size, modification_time).
        """
        all_files = []
        cache_dirs = self.get_cache_directories()
        
        logger.info(f"Scanning {len(cache_dirs)} cache directories")
        
        for cache_dir in cache_dirs:
            logger.info(f"Scanning: {cache_dir}")
            files = self.scan_directory(cache_dir, recursive=True)
            all_files.extend(files)
            logger.info(f"Found {len(files)} files in {cache_dir}")
        
        return all_files

    def delete_file(self, file_path: Path) -> bool:
        """Delete a file.

        Args:
            file_path: Path to file.

        Returns:
            True if deletion was successful.
        """
        try:
            if file_path.is_file():
                file_path.unlink()
                logger.info(f"Deleted file: {file_path}")
                return True
            elif file_path.is_dir():
                shutil.rmtree(file_path)
                logger.info(f"Deleted directory: {file_path}")
                return True
            else:
                logger.warning(f"Path is neither file nor directory: {file_path}")
                return False
        except PermissionError as e:
            logger.error(f"Permission denied deleting {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting {file_path}: {e}")
            return False

    def cleanup_files(
        self, files: List[Tuple[Path, int, datetime]], dry_run: bool = False
    ) -> Tuple[int, int, int]:
        """Clean up cache files.

        Args:
            files: List of files to clean (path, size, mtime).
            dry_run: If True, only simulate deletion.

        Returns:
            Tuple of (deleted_count, failed_count, total_size_deleted).
        """
        deleted_count = 0
        failed_count = 0
        total_size = 0
        
        max_delete_size = self.safety_config.get("max_delete_size", 0)
        current_size = 0
        
        for file_path, file_size, mtime in files:
            if max_delete_size > 0 and current_size + file_size > max_delete_size:
                logger.warning(f"Reached maximum delete size limit: {max_delete_size}")
                break
            
            if dry_run:
                logger.info(f"[DRY RUN] Would delete: {file_path} ({self._format_size(file_size)})")
                deleted_count += 1
                total_size += file_size
                current_size += file_size
            else:
                if self.delete_file(file_path):
                    deleted_count += 1
                    total_size += file_size
                    current_size += file_size
                else:
                    failed_count += 1
        
        return deleted_count, failed_count, total_size

    def generate_report(
        self, files: List[Tuple[Path, int, datetime]], deleted_count: int,
        failed_count: int, total_size: int
    ) -> str:
        """Generate cleanup report.

        Args:
            files: List of files found (path, size, mtime).
            deleted_count: Number of files deleted.
            failed_count: Number of files that failed to delete.
            total_size: Total size of deleted files in bytes.

        Returns:
            Report string.
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("CACHE CLEANUP REPORT")
        report_lines.append("=" * 60)
        report_lines.append(f"Generated: {datetime.now().isoformat()}")
        report_lines.append("")
        
        # Summary
        total_files = len(files)
        total_size_found = sum(size for _, size, _ in files)
        
        report_lines.append("SUMMARY")
        report_lines.append("-" * 60)
        report_lines.append(f"Total files found: {total_files:,}")
        report_lines.append(f"Total size found: {self._format_size(total_size_found)}")
        report_lines.append(f"Files deleted: {deleted_count:,}")
        report_lines.append(f"Files failed: {failed_count:,}")
        report_lines.append(f"Total size deleted: {self._format_size(total_size)}")
        report_lines.append("")
        
        # Directory breakdown
        if self.report_config.get("show_directory_breakdown", True):
            report_lines.append("DIRECTORY BREAKDOWN")
            report_lines.append("-" * 60)
            
            dir_sizes: Dict[Path, int] = {}
            for file_path, size, _ in files:
                dir_path = file_path.parent
                dir_sizes[dir_path] = dir_sizes.get(dir_path, 0) + size
            
            sorted_dirs = sorted(dir_sizes.items(), key=lambda x: x[1], reverse=True)
            for dir_path, size in sorted_dirs[:20]:  # Top 20 directories
                report_lines.append(f"{dir_path}: {self._format_size(size)}")
            report_lines.append("")
        
        # Largest files
        if self.report_config.get("show_largest_files", True):
            report_lines.append("LARGEST FILES")
            report_lines.append("-" * 60)
            
            largest_count = self.report_config.get("largest_files_count", 10)
            sorted_files = sorted(files, key=lambda x: x[1], reverse=True)
            
            for file_path, size, mtime in sorted_files[:largest_count]:
                age = datetime.now() - mtime
                report_lines.append(
                    f"{file_path.name}: {self._format_size(size)} "
                    f"(age: {age.days} days)"
                )
            report_lines.append("")
        
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)

    def save_report(self, report: str) -> None:
        """Save report to file.

        Args:
            report: Report string.
        """
        report_file = self.report_config.get("report_file", "logs/cache_cleanup_report.txt")
        report_path = Path(report_file)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)
            logger.info(f"Report saved to {report_path}")
        except IOError as e:
            logger.error(f"Error saving report: {e}")

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
    log_file = log_config.get("file", "logs/cache_cleaner.log")
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


def confirm_deletion(file_count: int, total_size: int) -> bool:
    """Ask user for confirmation before deletion.

    Args:
        file_count: Number of files to delete.
        total_size: Total size of files to delete.

    Returns:
        True if user confirms.
    """
    cleaner = CacheCleaner({})  # Temporary instance for formatting
    size_str = cleaner._format_size(total_size)
    
    print(f"\nAbout to delete {file_count:,} files ({size_str})")
    response = input("Do you want to continue? (yes/no): ").strip().lower()
    
    return response in ["yes", "y"]


def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Clean system cache files with age-based filtering"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview files to be deleted without actually deleting",
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompt",
    )
    parser.add_argument(
        "--min-age",
        type=int,
        help="Minimum file age in days (overrides config)",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        help="Maximum total size to delete in MB (overrides config)",
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config)
        setup_logging(config)

        # Override config with command-line arguments
        if args.dry_run:
            config["safety"]["dry_run"] = True
        
        if args.min_age:
            config["filtering"]["min_age_days"] = args.min_age
        
        if args.max_size:
            config["safety"]["max_delete_size"] = args.max_size * 1024 * 1024  # Convert MB to bytes

        cleaner = CacheCleaner(config)

        print("Scanning cache directories...")
        files = cleaner.scan_all_directories()

        if not files:
            print("No cache files found matching the criteria.")
            return

        total_size = sum(size for _, size, _ in files)
        print(f"\nFound {len(files):,} files ({cleaner._format_size(total_size)})")

        # Show preview
        if config["reporting"].get("show_largest_files", True):
            print("\nLargest files found:")
            sorted_files = sorted(files, key=lambda x: x[1], reverse=True)
            for file_path, size, mtime in sorted_files[:5]:
                age = datetime.now() - mtime
                print(f"  {file_path.name}: {cleaner._format_size(size)} (age: {age.days} days)")

        # Confirmation
        dry_run = config["safety"].get("dry_run", False) or args.dry_run
        require_confirm = config["safety"].get("require_confirmation", True) and not args.no_confirm

        if dry_run:
            print("\n[DRY RUN MODE - No files will be deleted]")
        elif require_confirm:
            if not confirm_deletion(len(files), total_size):
                print("Operation cancelled.")
                return

        # Cleanup
        print("\nCleaning cache files...")
        deleted_count, failed_count, deleted_size = cleaner.cleanup_files(files, dry_run=dry_run)

        # Generate report
        if config["reporting"].get("detailed_report", True):
            report = cleaner.generate_report(files, deleted_count, failed_count, deleted_size)
            cleaner.save_report(report)
            print(f"\nDetailed report saved to {config['reporting']['report_file']}")

        # Summary
        print("\n" + "=" * 60)
        print("CLEANUP SUMMARY")
        print("=" * 60)
        print(f"Files deleted: {deleted_count:,}")
        print(f"Files failed: {failed_count:,}")
        print(f"Total size freed: {cleaner._format_size(deleted_size)}")
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
        logger.info("Operation interrupted by user")
        print("\nOperation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
