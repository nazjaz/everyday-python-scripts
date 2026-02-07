"""Depth File Organizer - Organize files by directory depth.

This module provides functionality to organize files by their depth in the
directory tree, grouping files from the same nesting level together.
"""

import logging
import logging.handlers
import os
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DepthFileOrganizer:
    """Organizes files by their depth in the directory tree."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize DepthFileOrganizer with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.stats = {
            "files_scanned": 0,
            "files_organized": 0,
            "files_skipped": 0,
            "errors": 0,
            "depths_found": set(),
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
            config["source"]["directory"] = os.getenv("SOURCE_DIRECTORY")
        if os.getenv("OUTPUT_DIRECTORY"):
            config["output"]["directory"] = os.getenv("OUTPUT_DIRECTORY")
        if os.getenv("DRY_RUN"):
            config["organization"]["dry_run"] = os.getenv("DRY_RUN").lower() == "true"

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/depth_organizer.log")

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

    def _calculate_depth(self, file_path: Path, base_path: Path) -> int:
        """Calculate depth of file relative to base path.

        Args:
            file_path: Path to file.
            base_path: Base directory path.

        Returns:
            Depth level (0 = base directory, 1 = one level deep, etc.).
        """
        try:
            relative_path = file_path.relative_to(base_path)
            # Depth is number of parent directories
            depth = len(relative_path.parent.parts)
            return depth
        except ValueError:
            # File is not relative to base path
            logger.warning(f"File {file_path} is not relative to base {base_path}")
            return 0

    def _should_skip_path(self, file_path: Path) -> bool:
        """Check if path should be skipped.

        Args:
            file_path: Path to check.

        Returns:
            True if path should be skipped, False otherwise.
        """
        skip_config = self.config.get("skip", {})
        patterns = skip_config.get("patterns", [])
        directories = skip_config.get("directories", [])
        excluded_paths = skip_config.get("excluded_paths", [])

        path_str = str(file_path)

        # Check skip patterns
        for pattern in patterns:
            if pattern in path_str:
                return True

        # Check skip directories
        for skip_dir in directories:
            if skip_dir in path_str:
                return True

        # Check excluded paths
        if path_str in excluded_paths or str(file_path.resolve()) in excluded_paths:
            return True

        return False

    def _should_include_extension(self, file_path: Path) -> bool:
        """Check if file extension should be included.

        Args:
            file_path: Path to file.

        Returns:
            True if extension should be included, False otherwise.
        """
        include_config = self.config.get("include", {})
        extensions = include_config.get("extensions", [])

        if not extensions:
            return True

        file_ext = file_path.suffix.lower()
        if not file_ext:
            return include_config.get("include_no_extension", False)

        return file_ext in [ext.lower() for ext in extensions]

    def _get_depth_folder_name(self, depth: int) -> str:
        """Get folder name for a depth level.

        Args:
            depth: Depth level.

        Returns:
            Folder name for the depth level.
        """
        naming_config = self.config.get("organization", {}).get("depth_naming", {})
        prefix = naming_config.get("prefix", "Depth")
        separator = naming_config.get("separator", "_")
        include_level = naming_config.get("include_level", True)

        if include_level:
            return f"{prefix}{separator}{depth}"
        return prefix

    def scan_files(self, directory: Optional[str] = None) -> Dict[int, List[Dict[str, any]]]:
        """Scan directory and group files by depth.

        Args:
            directory: Directory to scan (default: from config).

        Returns:
            Dictionary mapping depth levels to lists of file information.

        Raises:
            FileNotFoundError: If directory doesn't exist.
            NotADirectoryError: If path is not a directory.
        """
        source_config = self.config.get("source", {})
        scan_dir = directory or source_config.get("directory", ".")

        if not os.path.exists(scan_dir):
            raise FileNotFoundError(f"Directory not found: {scan_dir}")

        if not os.path.isdir(scan_dir):
            raise NotADirectoryError(f"Path is not a directory: {scan_dir}")

        logger.info(f"Starting file scan: {scan_dir}")

        scan_path = Path(scan_dir).resolve()
        recursive = source_config.get("recursive", True)

        files_by_depth: Dict[int, List[Dict[str, any]]] = defaultdict(list)

        try:
            if recursive:
                file_paths = list(scan_path.rglob("*"))
            else:
                file_paths = list(scan_path.iterdir())

            for file_path in file_paths:
                if not file_path.is_file():
                    continue

                # Skip if path matches skip criteria
                if self._should_skip_path(file_path):
                    continue

                # Check extension filter
                if not self._should_include_extension(file_path):
                    continue

                self.stats["files_scanned"] += 1

                # Calculate depth
                depth = self._calculate_depth(file_path, scan_path)
                self.stats["depths_found"].add(depth)

                # Get file information
                try:
                    stat_info = file_path.stat()
                    file_info = {
                        "path": str(file_path),
                        "name": file_path.name,
                        "depth": depth,
                        "size": stat_info.st_size,
                        "extension": file_path.suffix.lower() or "no extension",
                        "relative_path": str(file_path.relative_to(scan_path)),
                    }

                    files_by_depth[depth].append(file_info)

                except (OSError, PermissionError) as e:
                    logger.warning(f"Error accessing file {file_path}: {e}")
                    self.stats["errors"] += 1
                    continue

        except Exception as e:
            logger.error(f"Error during file scan: {e}")
            self.stats["errors"] += 1
            raise

        logger.info(f"File scan completed. Found files at {len(files_by_depth)} depth levels")
        return dict(files_by_depth)

    def organize_files(
        self, files_by_depth: Dict[int, List[Dict[str, any]]], dry_run: bool = False
    ) -> Dict[str, int]:
        """Organize files by moving them to depth-based folders.

        Args:
            files_by_depth: Dictionary mapping depth levels to file lists.
            dry_run: If True, simulate organization without actually moving files.

        Returns:
            Dictionary with organization statistics.
        """
        output_config = self.config.get("output", {})
        output_dir = output_config.get("directory", "organized")
        preserve_structure = output_config.get("preserve_structure", False)

        output_path = Path(output_dir)
        if not output_path.is_absolute():
            project_root = Path(__file__).parent.parent
            output_path = project_root / output_dir

        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Organizing files to: {output_path}")

        for depth, files in sorted(files_by_depth.items()):
            depth_folder = self._get_depth_folder_name(depth)
            depth_path = output_path / depth_folder
            depth_path.mkdir(parents=True, exist_ok=True)

            logger.info(f"Processing depth {depth}: {len(files)} files")

            for file_info in files:
                source_file = Path(file_info["path"])

                if not source_file.exists():
                    logger.warning(f"Source file not found: {source_file}")
                    self.stats["files_skipped"] += 1
                    continue

                try:
                    if preserve_structure:
                        # Preserve relative directory structure
                        relative_path = Path(file_info["relative_path"])
                        dest_file = depth_path / relative_path
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                    else:
                        # Move to depth folder with original name
                        dest_file = depth_path / file_info["name"]

                        # Handle name conflicts
                        if dest_file.exists():
                            conflict_config = self.config.get("organization", {}).get("conflicts", {})
                            conflict_action = conflict_config.get("action", "rename")

                            if conflict_action == "skip":
                                logger.info(f"Skipping duplicate: {dest_file}")
                                self.stats["files_skipped"] += 1
                                continue
                            elif conflict_action == "rename":
                                base_name = file_info["name"]
                                name_parts = base_name.rsplit(".", 1)
                                counter = 1
                                while dest_file.exists():
                                    if len(name_parts) == 2:
                                        new_name = f"{name_parts[0]}_{counter}.{name_parts[1]}"
                                    else:
                                        new_name = f"{base_name}_{counter}"
                                    dest_file = depth_path / new_name
                                    counter += 1
                                logger.debug(f"Renamed to avoid conflict: {dest_file}")

                    if dry_run:
                        logger.info(f"[DRY RUN] Would move: {source_file} -> {dest_file}")
                        self.stats["files_organized"] += 1
                    else:
                        shutil.move(str(source_file), str(dest_file))
                        logger.info(f"Moved: {source_file} -> {dest_file}")
                        self.stats["files_organized"] += 1
                        file_info["new_path"] = str(dest_file)

                except (OSError, PermissionError, shutil.Error) as e:
                    logger.error(f"Error moving file {source_file}: {e}")
                    self.stats["errors"] += 1
                    continue

        logger.info("File organization completed")
        logger.info(f"Statistics: {self.stats}")

        return {
            "files_organized": self.stats["files_organized"],
            "files_skipped": self.stats["files_skipped"],
            "errors": self.stats["errors"],
        }

    def generate_report(
        self, files_by_depth: Dict[int, List[Dict[str, any]]], output_file: Optional[str] = None
    ) -> str:
        """Generate text report of file organization.

        Args:
            files_by_depth: Dictionary mapping depth levels to file lists.
            output_file: Optional path to save report file.

        Returns:
            Report text.
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("DEPTH FILE ORGANIZER REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Statistics
        report_lines.append("STATISTICS")
        report_lines.append("-" * 80)
        report_lines.append(f"Files scanned: {self.stats['files_scanned']}")
        report_lines.append(f"Files organized: {self.stats['files_organized']}")
        report_lines.append(f"Files skipped: {self.stats['files_skipped']}")
        report_lines.append(f"Errors: {self.stats['errors']}")
        report_lines.append(f"Depth levels found: {len(files_by_depth)}")
        report_lines.append("")

        # Files by depth
        report_lines.append("FILES BY DEPTH")
        report_lines.append("-" * 80)

        for depth in sorted(files_by_depth.keys()):
            files = files_by_depth[depth]
            depth_folder = self._get_depth_folder_name(depth)

            report_lines.append(f"\nDepth {depth} ({depth_folder}): {len(files)} files")
            report_lines.append("-" * 80)

            total_size = sum(f["size"] for f in files)
            report_lines.append(f"Total size: {total_size:,} bytes")

            # Show file list
            if self.config.get("report", {}).get("show_file_list", True):
                for file_info in files:
                    report_lines.append(f"  {file_info['relative_path']}")
                    report_lines.append(f"    Size: {file_info['size']:,} bytes")
                    if file_info.get("new_path"):
                        report_lines.append(f"    Moved to: {file_info['new_path']}")

        report_text = "\n".join(report_lines)

        # Save to file if specified
        if output_file:
            output_path = Path(output_file)
            if not output_path.is_absolute():
                project_root = Path(__file__).parent.parent
                output_path = project_root / output_file

            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_text)

            logger.info(f"Report saved to: {output_path}")

        return report_text

    def print_summary(self, files_by_depth: Dict[int, List[Dict[str, any]]]) -> None:
        """Print summary to console.

        Args:
            files_by_depth: Dictionary mapping depth levels to file lists.
        """
        print("\n" + "=" * 80)
        print("DEPTH FILE ORGANIZER SUMMARY")
        print("=" * 80)
        print(f"Files scanned: {self.stats['files_scanned']}")
        print(f"Files organized: {self.stats['files_organized']}")
        print(f"Files skipped: {self.stats['files_skipped']}")
        if self.stats['errors'] > 0:
            print(f"Errors: {self.stats['errors']}")
        print(f"\nDepth levels found: {len(files_by_depth)}")
        print("\nFiles by depth:")
        for depth in sorted(files_by_depth.keys()):
            files = files_by_depth[depth]
            depth_folder = self._get_depth_folder_name(depth)
            total_size = sum(f["size"] for f in files)
            print(f"  Depth {depth} ({depth_folder}): {len(files)} files, {total_size:,} bytes")
        print("=" * 80 + "\n")


def main() -> int:
    """Main entry point for depth file organizer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Organize files by directory depth"
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
        help="Directory to scan (overrides config)",
    )
    parser.add_argument(
        "-o",
        "--organize",
        action="store_true",
        help="Organize files by moving them to depth folders",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate organization without actually moving files",
    )
    parser.add_argument(
        "--report",
        help="Save report to file",
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Don't print summary to console",
    )

    args = parser.parse_args()

    try:
        organizer = DepthFileOrganizer(config_path=args.config)

        # Override dry run setting
        if args.dry_run:
            organizer.config["organization"]["dry_run"] = True

        # Scan files
        files_by_depth = organizer.scan_files(directory=args.directory)

        # Organize files if requested
        if args.organize:
            dry_run = organizer.config.get("organization", {}).get("dry_run", True)
            if args.dry_run:
                dry_run = True
            organizer.organize_files(files_by_depth, dry_run=dry_run)

        # Print summary
        if not args.no_summary:
            organizer.print_summary(files_by_depth)

        # Generate report
        if args.report:
            report = organizer.generate_report(files_by_depth, output_file=args.report)
            print(f"\nReport saved to: {args.report}")
        elif organizer.config.get("report", {}).get("auto_save", False):
            report_file = organizer.config.get("report", {}).get("output_file", "logs/depth_report.txt")
            report = organizer.generate_report(files_by_depth, output_file=report_file)
            print(f"\nReport saved to: {report_file}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration or directory error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
