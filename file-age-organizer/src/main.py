"""File Age Organizer - Organize files by age into categories.

This module provides functionality to organize files by age into categories
like New, Recent, Old, and Very-Old based on configurable time thresholds.
"""

import logging
import logging.handlers
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FileAgeOrganizer:
    """Organizes files by age into configurable categories."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize FileAgeOrganizer with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.age_thresholds = self._load_age_thresholds()
        self.file_data: List[Dict[str, Any]] = []
        self.stats = {
            "files_scanned": 0,
            "files_organized": 0,
            "files_skipped": 0,
            "errors": 0,
            "categories": {},
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
        if os.getenv("SOURCE_DIRECTORY"):
            config["organizer"]["source_directory"] = os.getenv("SOURCE_DIRECTORY")
        if os.getenv("DESTINATION_DIRECTORY"):
            config["organizer"]["destination_directory"] = os.getenv("DESTINATION_DIRECTORY")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/file_age_organizer.log")

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

    def _load_age_thresholds(self) -> Dict[str, int]:
        """Load age thresholds from configuration.

        Returns:
            Dictionary mapping category names to age in days.
        """
        thresholds_config = self.config.get("age_thresholds", {})
        thresholds = {}

        # Convert all thresholds to days for consistency
        for category, threshold in thresholds_config.items():
            if isinstance(threshold, dict):
                value = threshold.get("value", 0)
                unit = threshold.get("unit", "days")

                if unit == "days":
                    thresholds[category] = value
                elif unit == "hours":
                    thresholds[category] = value / 24
                elif unit == "minutes":
                    thresholds[category] = value / (24 * 60)
                else:
                    logger.warning(f"Unknown unit '{unit}' for category '{category}', using days")
                    thresholds[category] = value
            else:
                # Assume days if just a number
                thresholds[category] = threshold

        logger.info(f"Loaded age thresholds: {thresholds}")
        return thresholds

    def _get_file_age_days(self, file_path: Path) -> float:
        """Get file age in days.

        Args:
            file_path: Path to file.

        Returns:
            Age in days.
        """
        try:
            mtime = file_path.stat().st_mtime
            age_seconds = datetime.now().timestamp() - mtime
            age_days = age_seconds / (24 * 60 * 60)
            return age_days
        except (OSError, PermissionError) as e:
            logger.warning(f"Could not get file age for {file_path}: {e}")
            return 0.0

    def _categorize_file(self, file_path: Path) -> str:
        """Categorize file by age.

        Args:
            file_path: Path to file.

        Returns:
            Category name.
        """
        age_days = self._get_file_age_days(file_path)

        # Check thresholds in order (newest to oldest)
        # This assumes thresholds are ordered from smallest to largest
        sorted_categories = sorted(
            self.age_thresholds.items(), key=lambda x: x[1], reverse=False
        )

        for category, threshold_days in sorted_categories:
            if age_days <= threshold_days:
                return category

        # If file is older than all thresholds, use the oldest category
        if sorted_categories:
            return sorted_categories[-1][0]

        # Default category
        return "Other"

    def _is_excluded(self, file_path: Path) -> bool:
        """Check if file should be excluded from organization.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file should be excluded, False otherwise.
        """
        exclude_config = self.config.get("organizer", {}).get("exclude", {})
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

    def scan_and_categorize(
        self,
        source_directory: Optional[str] = None,
        recursive: bool = True,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Scan directory and categorize files by age.

        Args:
            source_directory: Source directory (overrides config).
            recursive: Whether to scan recursively.

        Returns:
            Dictionary mapping category names to lists of file information.

        Raises:
            FileNotFoundError: If source directory doesn't exist.
        """
        organizer_config = self.config.get("organizer", {})

        if source_directory:
            source_dir = Path(source_directory)
        else:
            source_dir = Path(organizer_config.get("source_directory", "."))

        if not source_dir.exists():
            raise FileNotFoundError(f"Source directory does not exist: {source_dir}")

        if not source_dir.is_dir():
            raise ValueError(f"Source path is not a directory: {source_dir}")

        logger.info(f"Scanning and categorizing files in: {source_dir}")

        self.file_data = []
        categorized_files: Dict[str, List[Dict[str, Any]]] = {}

        # Initialize category lists
        for category in self.age_thresholds.keys():
            categorized_files[category] = []

        self.stats = {
            "files_scanned": 0,
            "files_organized": 0,
            "files_skipped": 0,
            "errors": 0,
            "categories": {cat: 0 for cat in self.age_thresholds.keys()},
        }

        # Walk directory
        if recursive:
            iterator = source_dir.rglob("*")
        else:
            iterator = source_dir.glob("*")

        for item_path in iterator:
            if not item_path.is_file():
                continue

            self.stats["files_scanned"] += 1

            # Check exclusions
            if self._is_excluded(item_path):
                self.stats["files_skipped"] += 1
                continue

            try:
                stat_info = item_path.stat()
                age_days = self._get_file_age_days(item_path)
                category = self._categorize_file(item_path)

                file_info = {
                    "path": str(item_path),
                    "name": item_path.name,
                    "size": stat_info.st_size,
                    "age_days": age_days,
                    "modified_time": stat_info.st_mtime,
                    "modified_datetime": datetime.fromtimestamp(stat_info.st_mtime),
                    "category": category,
                }

                self.file_data.append(file_info)
                categorized_files[category].append(file_info)
                self.stats["categories"][category] += 1
                self.stats["files_organized"] += 1

            except (OSError, PermissionError) as e:
                logger.warning(f"Could not process file {item_path}: {e}")
                self.stats["errors"] += 1

        logger.info(
            f"Categorized {self.stats['files_organized']} file(s) into "
            f"{len([c for c in categorized_files.values() if c])} category(ies)"
        )

        return categorized_files

    def organize_files(
        self,
        source_directory: Optional[str] = None,
        destination_directory: Optional[str] = None,
        action: str = "move",
    ) -> Dict[str, Any]:
        """Organize files by moving or copying them to category folders.

        Args:
            source_directory: Source directory (overrides config).
            destination_directory: Destination directory (overrides config).
            action: Action to perform - "move" or "copy".

        Returns:
            Dictionary with organization statistics.

        Raises:
            ValueError: If action is invalid.
        """
        if action not in ["move", "copy"]:
            raise ValueError("action must be 'move' or 'copy'")

        organizer_config = self.config.get("organizer", {})

        if source_directory:
            source_dir = Path(source_directory)
        else:
            source_dir = Path(organizer_config.get("source_directory", "."))

        if destination_directory:
            dest_dir = Path(destination_directory)
        else:
            dest_dir = Path(organizer_config.get("destination_directory", "organized"))

        if not source_dir.exists():
            raise FileNotFoundError(f"Source directory does not exist: {source_dir}")

        logger.info(f"Organizing files from {source_dir} to {dest_dir} (action: {action})")

        # Scan and categorize
        categorized_files = self.scan_and_categorize(source_directory, recursive=True)

        # Create destination directory
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Organize files
        for category, files in categorized_files.items():
            if not files:
                continue

            category_dir = dest_dir / category
            category_dir.mkdir(parents=True, exist_ok=True)

            for file_info in files:
                source_path = Path(file_info["path"])

                # Skip if source is in destination
                try:
                    if source_path.resolve().is_relative_to(dest_dir.resolve()):
                        continue
                except (ValueError, AttributeError):
                    # Python < 3.9 compatibility
                    try:
                        if str(source_path.resolve()).startswith(str(dest_dir.resolve())):
                            continue
                    except Exception:
                        pass

                dest_path = category_dir / source_path.name

                # Handle duplicate names
                if dest_path.exists():
                    handle_duplicates = organizer_config.get("handle_duplicate_names", "rename")
                    if handle_duplicates == "skip":
                        logger.debug(f"Skipping duplicate: {dest_path}")
                        continue
                    elif handle_duplicates == "rename":
                        counter = 1
                        base_name = source_path.stem
                        extension = source_path.suffix
                        while dest_path.exists():
                            dest_path = category_dir / f"{base_name}_{counter}{extension}"
                            counter += 1

                try:
                    if action == "move":
                        shutil.move(str(source_path), str(dest_path))
                        logger.info(f"Moved: {source_path.name} -> {category}/{dest_path.name}")
                    else:  # copy
                        shutil.copy2(source_path, dest_path)
                        logger.info(f"Copied: {source_path.name} -> {category}/{dest_path.name}")

                except (OSError, shutil.Error) as e:
                    logger.error(f"Error {action}ing {source_path} to {dest_path}: {e}")
                    self.stats["errors"] += 1

        logger.info(
            f"Organization complete: {self.stats['files_organized']} file(s) "
            f"{action}ed to {len([c for c in categorized_files.values() if c])} category(ies)"
        )

        return self.stats

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate text report of file organization.

        Args:
            output_file: Path to output file (overrides config).

        Returns:
            Report content as string.
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("File Age Organization Report")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Summary
        report_lines.append("Summary Statistics")
        report_lines.append("-" * 80)
        report_lines.append(f"Files scanned: {self.stats['files_scanned']:,}")
        report_lines.append(f"Files organized: {self.stats['files_organized']:,}")
        report_lines.append(f"Files skipped: {self.stats['files_skipped']:,}")
        report_lines.append(f"Errors: {self.stats['errors']}")
        report_lines.append("")

        # Category breakdown
        report_lines.append("Category Distribution")
        report_lines.append("-" * 80)
        for category, count in sorted(self.stats["categories"].items()):
            threshold = self.age_thresholds.get(category, 0)
            report_lines.append(f"  {category:15s}: {count:6,} file(s) (threshold: {threshold} days)")
        report_lines.append("")

        # Age thresholds
        report_lines.append("Age Thresholds")
        report_lines.append("-" * 80)
        sorted_thresholds = sorted(
            self.age_thresholds.items(), key=lambda x: x[1], reverse=False
        )
        for category, threshold_days in sorted_thresholds:
            report_lines.append(f"  {category:15s}: {threshold_days:6.2f} days")
        report_lines.append("")

        # Files by category
        categorized_files: Dict[str, List[Dict[str, Any]]] = {}
        for file_info in self.file_data:
            category = file_info.get("category", "Other")
            if category not in categorized_files:
                categorized_files[category] = []
            categorized_files[category].append(file_info)

        for category, files in sorted(categorized_files.items()):
            if not files:
                continue

            report_lines.append(f"Files in '{category}' Category ({len(files)} file(s))")
            report_lines.append("-" * 80)
            for file_info in sorted(files, key=lambda x: x["age_days"], reverse=True)[:20]:
                age_str = f"{file_info['age_days']:.2f} days"
                mod_time = file_info["modified_datetime"].strftime("%Y-%m-%d %H:%M:%S")
                report_lines.append(
                    f"  {age_str:>12s}  {mod_time:<20s}  {file_info['path']}"
                )
            if len(files) > 20:
                report_lines.append(f"  ... and {len(files) - 20} more file(s)")
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
        """Get organization statistics.

        Returns:
            Dictionary with statistics.
        """
        return self.stats.copy()


def main() -> int:
    """Main entry point for file age organizer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Organize files by age into categories"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-s",
        "--source",
        help="Source directory (overrides config)",
    )
    parser.add_argument(
        "-d",
        "--destination",
        help="Destination directory (overrides config)",
    )
    parser.add_argument(
        "-a",
        "--action",
        choices=["move", "copy"],
        default="move",
        help="Action to perform: move or copy (default: move)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually organizing",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Generate report to file",
    )

    args = parser.parse_args()

    try:
        organizer = FileAgeOrganizer(config_path=args.config)

        if args.dry_run:
            print("DRY RUN MODE - No files will be moved or copied")
            print("=" * 60)

            categorized_files = organizer.scan_and_categorize(
                source_directory=args.source, recursive=True
            )

            print(f"\nFound {organizer.stats['files_scanned']} file(s)")
            print("\nCategory Distribution:")
            for category, files in sorted(categorized_files.items()):
                if files:
                    threshold = organizer.age_thresholds.get(category, 0)
                    print(f"  {category:15s}: {len(files):6,} file(s) (threshold: {threshold} days)")

            print("\nSample files by category:")
            for category, files in sorted(categorized_files.items()):
                if files:
                    print(f"\n  {category}:")
                    for file_info in files[:5]:
                        age_str = f"{file_info['age_days']:.2f} days"
                        print(f"    {age_str:>12s}  {file_info['path']}")

            return 0

        # Organize files
        stats = organizer.organize_files(
            source_directory=args.source,
            destination_directory=args.destination,
            action=args.action,
        )

        # Generate report
        if args.output:
            report_content = organizer.generate_report(output_file=args.output)
        else:
            report_content = organizer.generate_report()

        # Print summary
        print("\n" + "=" * 60)
        print("File Organization Summary")
        print("=" * 60)
        print(f"Files scanned: {stats['files_scanned']}")
        print(f"Files organized: {stats['files_organized']}")
        print(f"Files skipped: {stats['files_skipped']}")
        print(f"Errors: {stats['errors']}")

        print("\nCategory Distribution:")
        for category, count in sorted(stats["categories"].items()):
            if count > 0:
                threshold = organizer.age_thresholds.get(category, 0)
                print(f"  {category:15s}: {count:6,} file(s) (threshold: {threshold} days)")

        if args.output:
            print(f"\nReport saved to: {args.output}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
