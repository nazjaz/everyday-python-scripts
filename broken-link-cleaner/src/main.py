"""Broken Link Cleaner - Find and remove broken symbolic links.

This module provides functionality to find and remove broken symbolic links,
logging all removed links with their original target paths for reference.
Includes comprehensive logging and error handling.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class BrokenLinkCleaner:
    """Finds and removes broken symbolic links."""

    def __init__( self, config_path: str = "config.yaml") -> None:
        """Initialize BrokenLinkCleaner with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_directories()
        self.stats = {
            "links_scanned": 0,
            "broken_links_found": 0,
            "links_removed": 0,
            "links_skipped": 0,
            "errors": 0,
            "errors_list": [],
        }
        self.removed_links: List[Dict[str, str]] = []

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
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}"
            )

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Override with environment variables if present
        if os.getenv("SCAN_DIRECTORY"):
            config["scan_directory"] = os.getenv("SCAN_DIRECTORY")
        if os.getenv("DRY_RUN"):
            config["operations"]["dry_run"] = (
                os.getenv("DRY_RUN").lower() == "true"
            )

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/broken_link_cleaner.log")

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

    def _setup_directories(self) -> None:
        """Set up scan directory."""
        scan_dir = self.config.get("scan_directory", ".")
        self.scan_dir = Path(os.path.expanduser(scan_dir))

        if not self.scan_dir.exists():
            raise FileNotFoundError(
                f"Scan directory does not exist: {self.scan_dir}"
            )

        logger.info(f"Scan directory: {self.scan_dir}")

    def _is_broken_symlink(self, link_path: Path) -> bool:
        """Check if a path is a broken symbolic link.

        Args:
            link_path: Path to check.

        Returns:
            True if path is a broken symbolic link, False otherwise.
        """
        try:
            # Check if it's a symlink
            if not link_path.is_symlink():
                return False

            # Check if target exists
            target = link_path.readlink()
            # Resolve target relative to link's parent directory
            if target.is_absolute():
                target_path = target
            else:
                target_path = link_path.parent / target

            # Check if target exists
            return not target_path.exists()

        except (OSError, ValueError) as e:
            logger.debug(f"Error checking symlink {link_path}: {e}")
            return False

    def _get_symlink_target(self, link_path: Path) -> Optional[str]:
        """Get target path of a symbolic link.

        Args:
            link_path: Path to symbolic link.

        Returns:
            Target path as string, or None if error.
        """
        try:
            target = link_path.readlink()
            return str(target)
        except (OSError, ValueError) as e:
            logger.debug(f"Error reading symlink target {link_path}: {e}")
            return None

    def _should_process_link(self, link_path: Path) -> bool:
        """Check if symbolic link should be processed.

        Args:
            link_path: Path to symbolic link.

        Returns:
            True if link should be processed, False otherwise.
        """
        exclusions = self.config.get("exclusions", {})
        link_name = link_path.name
        link_str = str(link_path)

        # Check excluded patterns
        excluded_patterns = exclusions.get("patterns", [])
        for pattern in excluded_patterns:
            if pattern in link_name or pattern in link_str:
                return False

        # Check excluded directories
        excluded_dirs = exclusions.get("directories", [])
        for excluded_dir in excluded_dirs:
            excluded_path = Path(os.path.expanduser(excluded_dir))
            try:
                if link_path.is_relative_to(excluded_path):
                    return False
            except (ValueError, AttributeError):
                # Python < 3.9 compatibility
                if str(link_path).startswith(str(excluded_path)):
                    return False

        return True

    def _remove_symlink(self, link_path: Path) -> bool:
        """Remove a symbolic link.

        Args:
            link_path: Path to symbolic link to remove.

        Returns:
            True if successful, False otherwise.
        """
        try:
            target = self._get_symlink_target(link_path)

            if self.config["operations"]["dry_run"]:
                logger.info(
                    f"[DRY RUN] Would remove broken symlink: {link_path} "
                    f"(target: {target})"
                )
                self.removed_links.append(
                    {
                        "link_path": str(link_path),
                        "target_path": target or "unknown",
                    }
                )
                return True

            link_path.unlink()
            logger.info(
                f"Removed broken symlink: {link_path} (target: {target})"
            )
            self.removed_links.append(
                {
                    "link_path": str(link_path),
                    "target_path": target or "unknown",
                }
            )
            return True

        except (OSError, PermissionError) as e:
            error_msg = f"Error removing symlink {link_path}: {e}"
            logger.error(error_msg)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            return False

    def _scan_directory(self, directory: Path) -> None:
        """Recursively scan directory for broken symbolic links.

        Args:
            directory: Directory to scan.
        """
        if not directory.exists() or not directory.is_dir():
            return

        try:
            for item in directory.iterdir():
                self.stats["links_scanned"] += 1

                # Check if should be excluded
                if not self._should_process_link(item):
                    logger.debug(f"Skipping excluded path: {item}")
                    continue

                # Check if it's a broken symlink
                if self._is_broken_symlink(item):
                    self.stats["broken_links_found"] += 1
                    target = self._get_symlink_target(item)

                    logger.info(
                        f"Found broken symlink: {item} -> {target or 'unknown'}"
                    )

                    if self._remove_symlink(item):
                        self.stats["links_removed"] += 1
                    else:
                        self.stats["links_skipped"] += 1

                elif item.is_dir() and self.config["operations"]["recursive"]:
                    # Recursively scan subdirectories
                    self._scan_directory(item)

        except (PermissionError, OSError) as e:
            error_msg = f"Error scanning directory {directory}: {e}"
            logger.warning(error_msg)
            self.stats["errors"] += 1
            if error_msg not in self.stats["errors_list"]:
                self.stats["errors_list"].append(error_msg)

    def clean_broken_links(self) -> Dict[str, any]:
        """Find and remove all broken symbolic links.

        Returns:
            Dictionary with statistics about the operation.
        """
        logger.info("Starting broken symlink cleanup")
        logger.info(f"Scan directory: {self.scan_dir}")
        logger.info(f"Recursive: {self.config['operations']['recursive']}")
        logger.info(f"Dry run mode: {self.config['operations']['dry_run']}")

        self.removed_links = []
        self._scan_directory(self.scan_dir)

        logger.info("Broken symlink cleanup completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats

    def save_removal_log(self, output_file: Optional[str] = None) -> Path:
        """Save log of removed links to file.

        Args:
            output_file: Optional path to output file.

        Returns:
            Path to saved log file.
        """
        if not self.removed_links:
            logger.info("No removed links to log")
            return Path()

        if output_file:
            log_path = Path(output_file)
        else:
            log_path = Path(
                self.config.get("removal_log_file", "logs/removed_links.txt")
            )

        if not log_path.is_absolute():
            project_root = Path(__file__).parent.parent
            log_path = project_root / log_path

        log_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("Broken Symbolic Links Removed\n")
                f.write("=" * 80 + "\n\n")

                for link_info in self.removed_links:
                    f.write(f"Link: {link_info['link_path']}\n")
                    f.write(f"Target: {link_info['target_path']}\n")
                    f.write("-" * 80 + "\n")

            logger.info(f"Removal log saved to: {log_path}")
            return log_path

        except Exception as e:
            error_msg = f"Error saving removal log: {e}"
            logger.error(error_msg)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            return Path()


def main() -> int:
    """Main entry point for broken link cleaner."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Find and remove broken symbolic links"
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
        help="Preview changes without removing links",
    )
    parser.add_argument(
        "-o",
        "--output-log",
        help="Path to save removal log file",
    )

    args = parser.parse_args()

    try:
        cleaner = BrokenLinkCleaner(config_path=args.config)

        if args.dry_run:
            cleaner.config["operations"]["dry_run"] = True

        stats = cleaner.clean_broken_links()

        # Save removal log
        if args.output_log:
            log_path = cleaner.save_removal_log(output_file=args.output_log)
        else:
            log_path = cleaner.save_removal_log()

        # Print summary
        print("\n" + "=" * 60)
        print("Broken Link Cleanup Summary")
        print("=" * 60)
        print(f"Links Scanned: {stats['links_scanned']}")
        print(f"Broken Links Found: {stats['broken_links_found']}")
        print(f"Links Removed: {stats['links_removed']}")
        print(f"Links Skipped: {stats['links_skipped']}")
        print(f"Errors: {stats['errors']}")

        if log_path and log_path.exists():
            print(f"Removal Log: {log_path}")

        if stats["errors_list"]:
            print("\nErrors:")
            for error in stats["errors_list"][:10]:
                print(f"  - {error}")
            if len(stats["errors_list"]) > 10:
                print(f"  ... and {len(stats['errors_list']) - 10} more")

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
