"""Priority File Organizer - Organize files by priority levels.

This module provides functionality to organize files into priority-based
folder structures based on importance tags, file patterns, extensions, and
other criteria defined in configuration.
"""

import hashlib
import json
import logging
import logging.handlers
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class PriorityFileOrganizer:
    """Organizes files by priority levels defined in configuration."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize PriorityFileOrganizer with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.priority_levels = self._load_priority_levels()
        self.file_hashes: Dict[str, str] = {}
        self.stats = {
            "files_scanned": 0,
            "files_organized": 0,
            "duplicates_found": 0,
            "errors": 0,
            "priority_distribution": {},
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

        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Configure root logger
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

    def _load_priority_levels(self) -> List[Dict[str, Any]]:
        """Load and validate priority levels from configuration.

        Returns:
            List of priority level dictionaries sorted by priority.

        Raises:
            ValueError: If priority levels are invalid.
        """
        priorities = self.config.get("priorities", [])
        if not priorities:
            raise ValueError("No priority levels defined in configuration")

        # Sort by priority value (higher number = higher priority)
        sorted_priorities = sorted(
            priorities, key=lambda x: x.get("priority", 0), reverse=True
        )

        # Validate priority levels
        for priority in sorted_priorities:
            if "name" not in priority:
                raise ValueError("Priority level missing 'name' field")
            if "priority" not in priority:
                raise ValueError("Priority level missing 'priority' field")
            if "folder" not in priority:
                raise ValueError("Priority level missing 'folder' field")

        logger.info(
            f"Loaded {len(sorted_priorities)} priority levels",
            extra={"priority_count": len(sorted_priorities)},
        )
        return sorted_priorities

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file content.

        Args:
            file_path: Path to file.

        Returns:
            MD5 hash string.

        Raises:
            IOError: If file cannot be read.
        """
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except IOError as e:
            logger.error(f"Cannot read file for hashing: {file_path} - {e}")
            raise

    def _is_duplicate(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Check if file is a duplicate based on content hash.

        Args:
            file_path: Path to file to check.

        Returns:
            Tuple of (is_duplicate, duplicate_path).
        """
        try:
            file_hash = self._calculate_file_hash(file_path)
            for existing_path, existing_hash in self.file_hashes.items():
                if existing_hash == file_hash:
                    return (True, existing_path)
            self.file_hashes[str(file_path)] = file_hash
            return (False, None)
        except IOError:
            return (False, None)

    def _matches_pattern(self, file_path: Path, pattern: str) -> bool:
        """Check if file path matches pattern.

        Args:
            file_path: Path to check.
            pattern: Pattern to match (supports wildcards).

        Returns:
            True if pattern matches, False otherwise.
        """
        import fnmatch

        path_str = str(file_path)
        name_str = file_path.name

        # Check if pattern matches full path or just filename
        return fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(
            name_str, pattern
        )

    def _matches_extension(self, file_path: Path, extensions: List[str]) -> bool:
        """Check if file has matching extension.

        Args:
            file_path: Path to check.
            extensions: List of extensions to match (with or without dot).

        Returns:
            True if extension matches, False otherwise.
        """
        file_ext = file_path.suffix.lower()
        normalized_extensions = [
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in extensions
        ]
        return file_ext in normalized_extensions

    def _matches_keywords(self, file_path: Path, keywords: List[str]) -> bool:
        """Check if file path contains any keywords.

        Args:
            file_path: Path to check.
            keywords: List of keywords to search for.

        Returns:
            True if any keyword is found, False otherwise.
        """
        path_str = str(file_path).lower()
        name_str = file_path.name.lower()

        for keyword in keywords:
            if keyword.lower() in path_str or keyword.lower() in name_str:
                return True
        return False

    def _determine_priority(
        self, file_path: Path
    ) -> Optional[Dict[str, Any]]:
        """Determine priority level for a file.

        Args:
            file_path: Path to file.

        Returns:
            Priority level dictionary or None if no match.
        """
        for priority_level in self.priority_levels:
            criteria = priority_level.get("criteria", {})

            # Check file patterns
            patterns = criteria.get("patterns", [])
            if patterns:
                for pattern in patterns:
                    if self._matches_pattern(file_path, pattern):
                        logger.debug(
                            f"File matches pattern: {file_path} -> "
                            f"{priority_level['name']}"
                        )
                        return priority_level

            # Check file extensions
            extensions = criteria.get("extensions", [])
            if extensions:
                if self._matches_extension(file_path, extensions):
                    logger.debug(
                        f"File matches extension: {file_path} -> "
                        f"{priority_level['name']}"
                    )
                    return priority_level

            # Check keywords
            keywords = criteria.get("keywords", [])
            if keywords:
                if self._matches_keywords(file_path, keywords):
                    logger.debug(
                        f"File matches keyword: {file_path} -> "
                        f"{priority_level['name']}"
                    )
                    return priority_level

            # Check file size range
            size_range = criteria.get("size_range", {})
            if size_range:
                try:
                    file_size = file_path.stat().st_size
                    min_size = size_range.get("min", 0)
                    max_size = size_range.get("max", float("inf"))
                    if min_size <= file_size <= max_size:
                        logger.debug(
                            f"File matches size range: {file_path} -> "
                            f"{priority_level['name']}"
                        )
                        return priority_level
                except OSError:
                    pass

        return None

    def _should_skip_path(self, path: Path) -> bool:
        """Check if a path should be skipped during scanning.

        Args:
            path: Path to check.

        Returns:
            True if path should be skipped, False otherwise.
        """
        skip_patterns = self.config.get("scan", {}).get(
            "skip_patterns", []
        )
        path_str = str(path)

        for pattern in skip_patterns:
            if pattern in path_str:
                return True

        return False

    def _organize_file(
        self, file_path: Path, priority_level: Dict[str, Any], dry_run: bool
    ) -> bool:
        """Organize a single file into priority-based folder.

        Args:
            file_path: Path to file to organize.
            priority_level: Priority level dictionary.
            dry_run: If True, don't actually move files.

        Returns:
            True if file was organized, False otherwise.
        """
        try:
            # Check for duplicates
            is_dup, dup_path = self._is_duplicate(file_path)
            if is_dup:
                logger.warning(
                    f"Duplicate file found: {file_path} "
                    f"(duplicate of {dup_path})"
                )
                self.stats["duplicates_found"] += 1

                duplicate_action = self.config.get("duplicates", {}).get(
                    "action", "skip"
                )
                if duplicate_action == "skip":
                    logger.info(f"Skipping duplicate: {file_path}")
                    return False
                elif duplicate_action == "delete":
                    if not dry_run:
                        file_path.unlink()
                        logger.info(f"Deleted duplicate: {file_path}")
                    else:
                        logger.info(f"[DRY RUN] Would delete duplicate: {file_path}")
                    return True

            # Determine destination folder
            base_folder = Path(
                self.config.get("organization", {}).get(
                    "base_folder", "organized"
                )
            )
            priority_folder = base_folder / priority_level["folder"]
            priority_folder.mkdir(parents=True, exist_ok=True)

            # Handle filename conflicts
            dest_path = priority_folder / file_path.name
            if dest_path.exists() and not is_dup:
                counter = 1
                stem = file_path.stem
                suffix = file_path.suffix
                while dest_path.exists():
                    dest_path = priority_folder / f"{stem}_{counter}{suffix}"
                    counter += 1

            # Move file
            if not dry_run:
                shutil.move(str(file_path), str(dest_path))
                logger.info(
                    f"Moved {file_path} -> {dest_path} "
                    f"(Priority: {priority_level['name']})"
                )
            else:
                logger.info(
                    f"[DRY RUN] Would move {file_path} -> {dest_path} "
                    f"(Priority: {priority_level['name']})"
                )

            self.stats["files_organized"] += 1
            priority_name = priority_level["name"]
            self.stats["priority_distribution"][priority_name] = (
                self.stats["priority_distribution"].get(priority_name, 0) + 1
            )

            return True

        except (OSError, shutil.Error) as e:
            logger.error(
                f"Error organizing file {file_path}: {e}",
                extra={"file_path": str(file_path)},
            )
            self.stats["errors"] += 1
            return False

    def organize_directory(
        self, source_dir: str, dry_run: bool = False
    ) -> None:
        """Organize files in directory by priority levels.

        Args:
            source_dir: Path to directory to organize.
            dry_run: If True, simulate organization without moving files.

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
            f"Starting organization of {source_dir}",
            extra={"source_dir": source_dir, "dry_run": dry_run},
        )

        self.file_hashes = {}
        self.stats = {
            "files_scanned": 0,
            "files_organized": 0,
            "duplicates_found": 0,
            "errors": 0,
            "priority_distribution": {},
        }

        try:
            for root, dirs, files in os.walk(source_path):
                root_path = Path(root)

                # Skip directories based on patterns
                dirs[:] = [
                    d
                    for d in dirs
                    if not self._should_skip_path(root_path / d)
                ]

                if self._should_skip_path(root_path):
                    continue

                for file_name in files:
                    file_path = root_path / file_name

                    if self._should_skip_path(file_path):
                        continue

                    self.stats["files_scanned"] += 1

                    # Determine priority
                    priority_level = self._determine_priority(file_path)
                    if priority_level:
                        self._organize_file(file_path, priority_level, dry_run)
                    else:
                        logger.debug(
                            f"No priority match for file: {file_path}"
                        )

        except PermissionError as e:
            logger.error(
                f"Permission denied accessing {source_dir}: {e}",
                extra={"source_dir": source_dir},
            )
            raise

        logger.info(
            f"Organization completed: {self.stats['files_organized']} "
            f"files organized",
            extra=self.stats,
        )

    def generate_report(self, output_path: Optional[str] = None) -> str:
        """Generate organization report.

        Args:
            output_path: Optional path to save report file. If None,
                uses default from config.

        Returns:
            Report content as string.
        """
        report_config = self.config.get("report", {})
        default_output = report_config.get(
            "output_file", "organization_report.txt"
        )

        output_file = output_path or default_output

        report_lines = [
            "=" * 80,
            "PRIORITY-BASED FILE ORGANIZATION REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY",
            "-" * 80,
            f"Files scanned: {self.stats['files_scanned']:,}",
            f"Files organized: {self.stats['files_organized']:,}",
            f"Duplicates found: {self.stats['duplicates_found']:,}",
            f"Errors encountered: {self.stats['errors']}",
            "",
            "PRIORITY DISTRIBUTION",
            "-" * 80,
        ]

        for priority_name, count in sorted(
            self.stats["priority_distribution"].items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            report_lines.append(f"{priority_name}: {count:,} files")

        if not self.stats["priority_distribution"]:
            report_lines.append("No files were organized.")

        report_content = "\n".join(report_lines)

        # Save report to file
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
        description="Organize files by priority levels defined in "
        "configuration"
    )
    parser.add_argument(
        "directory",
        help="Directory to organize files in",
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
        help="Simulate organization without moving files",
    )
    parser.add_argument(
        "-r",
        "--report",
        help="Output path for organization report (overrides config)",
    )

    args = parser.parse_args()

    try:
        organizer = PriorityFileOrganizer(config_path=args.config)
        organizer.organize_directory(args.directory, dry_run=args.dry_run)
        organizer.generate_report(output_path=args.report)

        print(
            f"\nOrganization complete. "
            f"Organized {organizer.stats['files_organized']} files "
            f"from {organizer.stats['files_scanned']} scanned."
        )
        if organizer.stats["duplicates_found"] > 0:
            print(
                f"Found {organizer.stats['duplicates_found']} duplicate files."
            )

    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
