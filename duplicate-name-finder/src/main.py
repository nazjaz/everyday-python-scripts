"""Duplicate Name Finder - Find files with duplicate names in different directories.

This module provides functionality to find files with duplicate names in
different directories, generate reports, and optionally rename them with
directory prefixes.
"""

import logging
import logging.handlers
import os
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DuplicateNameFinder:
    """Finds files with duplicate names in different directories."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize DuplicateNameFinder with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.duplicate_groups: Dict[str, List[Dict[str, Any]]] = {}
        self.stats = {
            "files_scanned": 0,
            "duplicate_names_found": 0,
            "files_renamed": 0,
            "errors": 0,
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
        if os.getenv("SCAN_DIRECTORY"):
            config["search"]["directory"] = os.getenv("SCAN_DIRECTORY")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/duplicate_finder.log")

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

    def _is_excluded(self, file_path: Path) -> bool:
        """Check if file should be excluded from search.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file should be excluded, False otherwise.
        """
        exclude_config = self.config.get("search", {}).get("exclude", {})
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

    def _get_directory_prefix(self, file_path: Path, base_directory: Path) -> str:
        """Get directory prefix for file based on its path.

        Args:
            file_path: Path to file.
            base_directory: Base directory for relative path calculation.

        Returns:
            Directory prefix string.
        """
        try:
            rel_path = file_path.parent.relative_to(base_directory)
            if str(rel_path) == ".":
                return ""
            # Convert path to prefix (replace separators with underscores)
            prefix = str(rel_path).replace(os.sep, "_").replace("/", "_")
            return prefix
        except ValueError:
            # File is not under base directory
            # Use parent directory name
            return file_path.parent.name

    def find_duplicate_names(
        self,
        directory: Optional[str] = None,
        recursive: bool = True,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Find files with duplicate names in different directories.

        Args:
            directory: Directory to search (overrides config).
            recursive: Whether to search recursively.

        Returns:
            Dictionary mapping filenames to lists of file information.

        Raises:
            FileNotFoundError: If directory doesn't exist.
        """
        search_config = self.config.get("search", {})

        if directory:
            search_dir = Path(directory)
        else:
            search_dir = Path(search_config.get("directory", "."))

        if not search_dir.exists():
            raise FileNotFoundError(f"Directory does not exist: {search_dir}")

        if not search_dir.is_dir():
            raise ValueError(f"Path is not a directory: {search_dir}")

        logger.info(f"Searching for duplicate file names in: {search_dir}")

        # Reset stats
        self.stats = {
            "files_scanned": 0,
            "duplicate_names_found": 0,
            "files_renamed": 0,
            "errors": 0,
        }

        # Collect all files by name
        files_by_name: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # Walk directory
        if recursive:
            iterator = search_dir.rglob("*")
        else:
            iterator = search_dir.glob("*")

        for item_path in iterator:
            if not item_path.is_file():
                continue

            self.stats["files_scanned"] += 1

            # Check exclusions
            if self._is_excluded(item_path):
                continue

            try:
                stat_info = item_path.stat()
                file_name = item_path.name

                file_info = {
                    "path": str(item_path),
                    "name": file_name,
                    "directory": str(item_path.parent),
                    "size": stat_info.st_size,
                    "modified_time": stat_info.st_mtime,
                    "modified_datetime": datetime.fromtimestamp(stat_info.st_mtime),
                }

                files_by_name[file_name].append(file_info)

            except (OSError, PermissionError) as e:
                logger.warning(f"Could not get file info for {item_path}: {e}")
                self.stats["errors"] += 1

        # Filter to only duplicates (files with same name in different directories)
        self.duplicate_groups = {}
        for file_name, file_list in files_by_name.items():
            # Get unique directories
            directories = {f["directory"] for f in file_list}
            # Only consider duplicates if same name appears in different directories
            if len(directories) > 1 and len(file_list) > 1:
                self.duplicate_groups[file_name] = file_list
                self.stats["duplicate_names_found"] += len(file_list)

        logger.info(
            f"Found {len(self.duplicate_groups)} duplicate name(s) "
            f"affecting {self.stats['duplicate_names_found']} file(s)"
        )

        return self.duplicate_groups

    def rename_with_prefixes(
        self,
        base_directory: Optional[str] = None,
        dry_run: bool = False,
    ) -> int:
        """Rename duplicate files with directory prefixes.

        Args:
            base_directory: Base directory for prefix calculation (overrides config).
            dry_run: If True, show what would be renamed without actually renaming.

        Returns:
            Number of files renamed (or would be renamed in dry-run).

        Raises:
            ValueError: If no duplicates found or base directory is invalid.
        """
        if not self.duplicate_groups:
            raise ValueError("No duplicate names found. Run find_duplicate_names() first.")

        search_config = self.config.get("search", {})

        if base_directory:
            base_dir = Path(base_directory)
        else:
            base_dir = Path(search_config.get("directory", "."))

        if not base_dir.exists():
            raise FileNotFoundError(f"Base directory does not exist: {base_dir}")

        rename_config = self.config.get("renaming", {})
        prefix_separator = rename_config.get("prefix_separator", "_")
        skip_if_exists = rename_config.get("skip_if_exists", True)

        renamed_count = 0

        for file_name, file_list in self.duplicate_groups.items():
            for file_info in file_list:
                file_path = Path(file_info["path"])

                # Get directory prefix
                prefix = self._get_directory_prefix(file_path, base_dir)

                if not prefix:
                    # File is in base directory, skip or use different strategy
                    if rename_config.get("skip_base_directory", True):
                        logger.debug(f"Skipping file in base directory: {file_path}")
                        continue
                    prefix = "root"

                # Create new name with prefix
                file_stem = file_path.stem
                file_suffix = file_path.suffix
                new_name = f"{prefix}{prefix_separator}{file_name}"
                new_path = file_path.parent / new_name

                # Skip if new name already exists
                if new_path.exists() and skip_if_exists:
                    logger.warning(f"Target name already exists, skipping: {new_path}")
                    continue

                if dry_run:
                    logger.info(f"[DRY RUN] Would rename: {file_path.name} -> {new_name}")
                    renamed_count += 1
                else:
                    try:
                        file_path.rename(new_path)
                        renamed_count += 1
                        self.stats["files_renamed"] += 1
                        logger.info(f"Renamed: {file_path.name} -> {new_name}")
                    except (OSError, PermissionError) as e:
                        logger.error(f"Error renaming {file_path} to {new_path}: {e}")
                        self.stats["errors"] += 1

        if not dry_run:
            logger.info(f"Renamed {renamed_count} file(s) with directory prefixes")

        return renamed_count

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate text report of duplicate file names.

        Args:
            output_file: Path to output file (overrides config).

        Returns:
            Report content as string.
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("Duplicate File Names Report")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Summary
        report_lines.append("Summary Statistics")
        report_lines.append("-" * 80)
        report_lines.append(f"Files scanned: {self.stats['files_scanned']:,}")
        report_lines.append(f"Duplicate names found: {len(self.duplicate_groups):,}")
        report_lines.append(f"Files with duplicate names: {self.stats['duplicate_names_found']:,}")
        report_lines.append(f"Files renamed: {self.stats['files_renamed']:,}")
        report_lines.append(f"Errors: {self.stats['errors']}")
        report_lines.append("")

        # Duplicate groups
        if not self.duplicate_groups:
            report_lines.append("No duplicate file names found.")
        else:
            report_lines.append("Duplicate File Names")
            report_lines.append("-" * 80)

            for file_name, file_list in sorted(self.duplicate_groups.items()):
                report_lines.append(f"\nFile Name: {file_name}")
                report_lines.append(f"  Found in {len(file_list)} location(s):")
                for i, file_info in enumerate(file_list, 1):
                    size_str = self._format_size(file_info["size"])
                    mod_time = file_info["modified_datetime"].strftime("%Y-%m-%d %H:%M:%S")
                    report_lines.append(
                        f"    {i}. {file_info['directory']}/{file_info['name']}"
                    )
                    report_lines.append(
                        f"       Size: {size_str}, Modified: {mod_time}"
                    )

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

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics.

        Returns:
            Dictionary with statistics.
        """
        return self.stats.copy()


def main() -> int:
    """Main entry point for duplicate name finder."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Find files with duplicate names in different directories"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-d",
        "--directory",
        help="Directory to search (overrides config)",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Disable recursive directory search",
    )
    parser.add_argument(
        "-r",
        "--rename",
        action="store_true",
        help="Rename duplicate files with directory prefixes",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be renamed without actually renaming",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file for report (overrides config)",
    )

    args = parser.parse_args()

    try:
        finder = DuplicateNameFinder(config_path=args.config)

        # Find duplicates
        duplicates = finder.find_duplicate_names(
            directory=args.directory, recursive=not args.no_recursive
        )

        # Rename if requested
        if args.rename or args.dry_run:
            renamed = finder.rename_with_prefixes(dry_run=args.dry_run)
            if args.dry_run:
                print(f"\n[DRY RUN] Would rename {renamed} file(s)")
            else:
                print(f"\nRenamed {renamed} file(s)")

        # Generate report
        output_file = args.output or finder.config.get("report", {}).get("output_file")
        report_content = finder.generate_report(output_file=output_file)

        # Print summary
        print("\n" + "=" * 60)
        print("Duplicate Name Search Summary")
        print("=" * 60)
        print(f"Files scanned: {finder.stats['files_scanned']:,}")
        print(f"Duplicate names found: {len(duplicates):,}")
        print(f"Files with duplicate names: {finder.stats['duplicate_names_found']:,}")
        if args.rename or args.dry_run:
            print(f"Files renamed: {finder.stats['files_renamed']:,}")

        if duplicates:
            print("\nDuplicate file names:")
            for file_name, file_list in sorted(list(duplicates.items())[:10]):
                dirs = {f["directory"] for f in file_list}
                print(f"  {file_name}: found in {len(dirs)} different directory(ies)")

        if output_file:
            print(f"\nReport saved to: {output_file}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
