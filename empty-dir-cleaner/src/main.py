"""Empty Directory Cleaner - Find and remove empty directories recursively.

This module provides functionality to find and remove empty directories recursively,
with options to preserve specific directory patterns and logging of all deletions.
"""

import logging
import logging.handlers
import os
import re
from pathlib import Path
from typing import List, Optional, Set

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class EmptyDirectoryCleaner:
    """Finds and removes empty directories with pattern preservation."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize EmptyDirectoryCleaner with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.stats = {
            "directories_scanned": 0,
            "empty_directories_found": 0,
            "directories_preserved": 0,
            "directories_deleted": 0,
            "directories_failed": 0,
            "deleted_paths": [],
            "preserved_paths": [],
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
        if os.getenv("DRY_RUN"):
            config["safety"]["dry_run"] = os.getenv("DRY_RUN").lower() == "true"
        if os.getenv("TARGET_PATH"):
            config["targets"] = [{"path": os.getenv("TARGET_PATH"), "enabled": True}]
        if os.getenv("PRESERVE_PATTERNS_ENABLED"):
            config["preserve_patterns"]["enabled"] = (
                os.getenv("PRESERVE_PATTERNS_ENABLED").lower() == "true"
            )

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/empty_dir_cleaner.log")

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

    def _should_preserve(self, dir_path: Path) -> bool:
        """Check if directory should be preserved based on patterns.

        Args:
            dir_path: Path to directory to check.

        Returns:
            True if directory should be preserved, False otherwise.
        """
        if not self.config.get("preserve_patterns", {}).get("enabled", True):
            return False

        patterns = self.config.get("preserve_patterns", {}).get("patterns", [])
        match_type = self.config.get("preserve_patterns", {}).get("match_type", "name")

        for pattern in patterns:
            if match_type == "name":
                if dir_path.name == pattern:
                    return True
            elif match_type == "path":
                if pattern in str(dir_path):
                    return True
            elif match_type == "regex":
                try:
                    if re.search(pattern, str(dir_path)):
                        return True
                except re.error:
                    logger.warning(f"Invalid regex pattern: {pattern}")

        return False

    def _is_directory_empty(self, dir_path: Path) -> bool:
        """Check if directory is empty.

        Args:
            dir_path: Path to directory to check.

        Returns:
            True if directory is empty, False otherwise.
        """
        try:
            # Check if directory exists
            if not dir_path.exists() or not dir_path.is_dir():
                return False

            # Check if directory has any contents
            try:
                next(dir_path.iterdir())
                return False
            except StopIteration:
                # Directory is empty
                return True

        except PermissionError:
            logger.warning(f"Permission denied accessing: {dir_path}")
            return False
        except Exception as e:
            logger.warning(f"Error checking directory {dir_path}: {e}")
            return False

    def _find_empty_directories(
        self, root_path: Path, max_depth: Optional[int] = None, current_depth: int = 0
    ) -> List[Path]:
        """Recursively find empty directories.

        Args:
            root_path: Root directory to search.
            max_depth: Maximum depth to search (None = unlimited).
            current_depth: Current depth in recursion.

        Returns:
            List of empty directory paths (sorted deepest first).
        """
        empty_dirs: List[Path] = []

        if max_depth is not None and current_depth >= max_depth:
            return empty_dirs

        try:
            if not root_path.exists() or not root_path.is_dir():
                return empty_dirs

            # Don't follow symlinks if configured
            if not self.config.get("safety", {}).get("follow_symlinks", False):
                if root_path.is_symlink():
                    return empty_dirs

            self.stats["directories_scanned"] += 1

            # Recursively check subdirectories first (bottom-up)
            try:
                for item in root_path.iterdir():
                    if item.is_dir():
                        subdirs = self._find_empty_directories(
                            item, max_depth, current_depth + 1
                        )
                        empty_dirs.extend(subdirs)
            except PermissionError:
                logger.warning(f"Permission denied reading: {root_path}")
                return empty_dirs

            # Check if current directory is empty (after processing children)
            if self._is_directory_empty(root_path):
                empty_dirs.append(root_path)

        except Exception as e:
            logger.error(f"Error processing directory {root_path}: {e}")

        return empty_dirs

    def _delete_directory(self, dir_path: Path) -> bool:
        """Delete an empty directory.

        Args:
            dir_path: Path to directory to delete.

        Returns:
            True if successful, False otherwise.
        """
        dry_run = self.config.get("safety", {}).get("dry_run", False)

        try:
            if dry_run:
                logger.info(f"[DRY RUN] Would delete: {dir_path}")
                return True

            # Double-check directory is still empty before deleting
            if not self._is_directory_empty(dir_path):
                logger.warning(f"Directory not empty, skipping: {dir_path}")
                return False

            dir_path.rmdir()
            logger.info(f"Deleted empty directory: {dir_path}")

            if self.config.get("logging", {}).get("log_deletions", True):
                self.stats["deleted_paths"].append(str(dir_path))

            return True

        except PermissionError:
            logger.error(f"Permission denied deleting: {dir_path}")
            self.stats["directories_failed"] += 1
            return False
        except OSError as e:
            logger.error(f"Error deleting directory {dir_path}: {e}")
            self.stats["directories_failed"] += 1
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting {dir_path}: {e}")
            self.stats["directories_failed"] += 1
            return False

    def clean_directories(self) -> dict:
        """Clean empty directories from configured targets.

        Returns:
            Dictionary with cleaning statistics.
        """
        logger.info("Starting empty directory cleanup")

        targets = self.config.get("targets", [])
        if not targets:
            logger.warning("No target directories configured")
            return self.stats

        dry_run = self.config.get("safety", {}).get("dry_run", False)
        if dry_run:
            logger.info("DRY RUN MODE: No directories will be deleted")

        # Find all empty directories
        all_empty_dirs: List[Path] = []

        for target in targets:
            if not target.get("enabled", True):
                continue

            target_path = Path(target.get("path", "."))
            if not target_path.is_absolute():
                target_path = Path.cwd() / target_path

            logger.info(f"Scanning target: {target_path}")

            max_depth = self.config.get("safety", {}).get("max_depth")
            empty_dirs = self._find_empty_directories(target_path, max_depth)
            all_empty_dirs.extend(empty_dirs)

        # Sort by depth (deepest first) for bottom-up deletion
        all_empty_dirs.sort(key=lambda p: len(p.parts), reverse=True)

        self.stats["empty_directories_found"] = len(all_empty_dirs)

        # Process empty directories
        batch_size = self.config.get("deletion", {}).get("batch_size", 100)
        processed = 0

        for dir_path in all_empty_dirs:
            # Check if should preserve
            if self._should_preserve(dir_path):
                self.stats["directories_preserved"] += 1
                if self.config.get("logging", {}).get("log_preserved", False):
                    logger.debug(f"Preserved directory: {dir_path}")
                    self.stats["preserved_paths"].append(str(dir_path))
                continue

            # Delete directory
            if self._delete_directory(dir_path):
                self.stats["directories_deleted"] += 1
            else:
                self.stats["directories_failed"] += 1

            processed += 1

            # Progress reporting
            if processed % batch_size == 0:
                logger.info(
                    f"Processed {processed}/{len(all_empty_dirs)} directories..."
                )

        # Handle parent directories if configured
        if self.config.get("deletion", {}).get("remove_parent_if_empty", True):
            self._clean_parent_directories()

        # Generate report
        if self.config.get("reporting", {}).get("generate_report", True):
            self._generate_report()

        logger.info("Empty directory cleanup completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats

    def _clean_parent_directories(self) -> None:
        """Check and clean parent directories that became empty after child deletion."""
        # Re-scan for newly empty directories
        targets = self.config.get("targets", [])
        max_depth = self.config.get("safety", {}).get("max_depth")

        for target in targets:
            if not target.get("enabled", True):
                continue

            target_path = Path(target.get("path", "."))
            if not target_path.is_absolute():
                target_path = Path.cwd() / target_path

            empty_dirs = self._find_empty_directories(target_path, max_depth)

            # Sort by depth (deepest first)
            empty_dirs.sort(key=lambda p: len(p.parts), reverse=True)

            for dir_path in empty_dirs:
                if self._should_preserve(dir_path):
                    continue

                if self._is_directory_empty(dir_path):
                    if self._delete_directory(dir_path):
                        self.stats["directories_deleted"] += 1

    def _generate_report(self) -> None:
        """Generate cleanup report."""
        report_config = self.config.get("reporting", {})
        report_file = report_config.get("report_file", "logs/cleanup_report.txt")

        report_path = Path(report_file)
        if not report_path.is_absolute():
            project_root = Path(__file__).parent.parent
            report_path = project_root / report_file

        report_path.parent.mkdir(parents=True, exist_ok=True)

        dry_run = self.config.get("safety", {}).get("dry_run", False)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("Empty Directory Cleanup Report\n")
            f.write("=" * 60 + "\n\n")

            if dry_run:
                f.write("MODE: DRY RUN (No directories were actually deleted)\n\n")

            if report_config.get("include_statistics", True):
                f.write("Statistics\n")
                f.write("-" * 60 + "\n")
                f.write(f"Directories Scanned: {self.stats['directories_scanned']}\n")
                f.write(f"Empty Directories Found: {self.stats['empty_directories_found']}\n")
                f.write(f"Directories Preserved: {self.stats['directories_preserved']}\n")
                f.write(f"Directories Deleted: {self.stats['directories_deleted']}\n")
                f.write(f"Directories Failed: {self.stats['directories_failed']}\n")
                f.write("\n")

            if self.stats["deleted_paths"]:
                f.write("Deleted Directories\n")
                f.write("-" * 60 + "\n")
                for path in self.stats["deleted_paths"]:
                    f.write(f"{path}\n")
                f.write("\n")

            if self.stats["preserved_paths"]:
                f.write("Preserved Directories\n")
                f.write("-" * 60 + "\n")
                for path in self.stats["preserved_paths"]:
                    f.write(f"{path}\n")

        logger.info(f"Report generated: {report_path}")


def main() -> int:
    """Main entry point for empty directory cleaner."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Find and remove empty directories recursively"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Dry run mode (don't actually delete)",
    )
    parser.add_argument(
        "-p",
        "--path",
        help="Target directory path to clean",
    )

    args = parser.parse_args()

    try:
        cleaner = EmptyDirectoryCleaner(config_path=args.config)

        # Override config with command-line arguments
        if args.dry_run:
            cleaner.config["safety"]["dry_run"] = True
        if args.path:
            cleaner.config["targets"] = [{"path": args.path, "enabled": True}]

        stats = cleaner.clean_directories()

        print("\n" + "=" * 50)
        print("Cleanup Summary")
        print("=" * 50)
        print(f"Directories Scanned: {stats['directories_scanned']}")
        print(f"Empty Directories Found: {stats['empty_directories_found']}")
        print(f"Directories Preserved: {stats['directories_preserved']}")
        print(f"Directories Deleted: {stats['directories_deleted']}")
        print(f"Directories Failed: {stats['directories_failed']}")

        if cleaner.config.get("safety", {}).get("dry_run", False):
            print("\n[DRY RUN] No directories were actually deleted")

        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
