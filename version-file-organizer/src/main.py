"""Version File Organizer - Organize files by format version.

This module provides functionality to detect version numbers in filenames or
metadata, identify compatible versions, and organize files into version-based
folder structures for better file management.
"""

import logging
import logging.handlers
import os
import re
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class VersionFileOrganizer:
    """Organizes files by detecting and grouping format versions."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize VersionFileOrganizer with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.file_versions: Dict[str, Dict[str, Any]] = {}
        self.version_groups: Dict[str, List[str]] = defaultdict(list)
        self.stats = {
            "files_scanned": 0,
            "files_with_versions": 0,
            "files_organized": 0,
            "version_groups_created": 0,
            "errors": 0,
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

    def _parse_version_from_filename(self, file_path: Path) -> Optional[str]:
        """Extract version number from filename.

        Args:
            file_path: Path to file.

        Returns:
            Version string if found, None otherwise.
        """
        filename = file_path.stem
        version_patterns = self.config.get("version", {}).get(
            "filename_patterns", []
        )

        # Try configured patterns first
        for pattern in version_patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                version = match.group(1) if match.groups() else match.group(0)
                logger.debug(
                    f"Found version in filename: {file_path.name} -> {version}"
                )
                return version

        # Default patterns
        default_patterns = [
            r"v(\d+\.\d+\.\d+)",  # v1.2.3
            r"v(\d+\.\d+)",  # v1.2
            r"v(\d+)",  # v1
            r"[-_](\d+\.\d+\.\d+)",  # -1.2.3 or _1.2.3
            r"[-_](\d+\.\d+)",  # -1.2 or _1.2
            r"[-_](\d+)",  # -1 or _1
            r"(\d+\.\d+\.\d+)",  # 1.2.3
            r"(\d+\.\d+)",  # 1.2
        ]

        for pattern in default_patterns:
            match = re.search(pattern, filename)
            if match:
                version = match.group(1)
                logger.debug(
                    f"Found version in filename: {file_path.name} -> {version}"
                )
                return version

        return None

    def _normalize_version(self, version: str) -> str:
        """Normalize version string for comparison.

        Args:
            version: Version string.

        Returns:
            Normalized version string.
        """
        # Remove leading/trailing whitespace and common prefixes
        version = version.strip().lstrip("vV").lstrip("rR")

        # Ensure it's a valid version format
        if re.match(r"^\d+(\.\d+)*$", version):
            return version

        # Try to extract numeric version
        match = re.search(r"(\d+(?:\.\d+)*)", version)
        if match:
            return match.group(1)

        return version

    def _are_versions_compatible(
        self, version1: str, version2: str
    ) -> bool:
        """Check if two versions are compatible based on compatibility rules.

        Args:
            version1: First version string.
            version2: Second version string.

        Returns:
            True if versions are compatible, False otherwise.
        """
        compat_config = self.config.get("version", {}).get(
            "compatibility", {}
        )
        compat_mode = compat_config.get("mode", "major")

        v1_parts = self._normalize_version(version1).split(".")
        v2_parts = self._normalize_version(version2).split(".")

        # Pad to same length
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend(["0"] * (max_len - len(v1_parts)))
        v2_parts.extend(["0"] * (max_len - len(v2_parts)))

        try:
            v1_nums = [int(p) for p in v1_parts]
            v2_nums = [int(p) for p in v2_parts]
        except ValueError:
            # Non-numeric versions, compare as strings
            return version1 == version2

        if compat_mode == "exact":
            return v1_nums == v2_nums
        elif compat_mode == "major":
            return v1_nums[0] == v2_nums[0]
        elif compat_mode == "minor":
            return v1_nums[0] == v2_nums[0] and v1_nums[1] == v2_nums[1]
        elif compat_mode == "patch":
            return (
                v1_nums[0] == v2_nums[0]
                and v1_nums[1] == v2_nums[1]
                and v1_nums[2] == v2_nums[2]
            )
        else:
            return v1_nums == v2_nums

    def _get_version_group_key(self, version: str) -> str:
        """Get group key for version based on compatibility mode.

        Args:
            version: Version string.

        Returns:
            Group key string.
        """
        compat_config = self.config.get("version", {}).get(
            "compatibility", {}
        )
        compat_mode = compat_config.get("mode", "major")

        normalized = self._normalize_version(version)
        parts = normalized.split(".")

        if compat_mode == "exact":
            return normalized
        elif compat_mode == "major":
            return parts[0] if parts else normalized
        elif compat_mode == "minor":
            return ".".join(parts[:2]) if len(parts) >= 2 else normalized
        elif compat_mode == "patch":
            return ".".join(parts[:3]) if len(parts) >= 3 else normalized
        else:
            return normalized

    def _detect_file_version(self, file_path: Path) -> Optional[str]:
        """Detect version from filename or metadata.

        Args:
            file_path: Path to file.

        Returns:
            Version string if found, None otherwise.
        """
        # Try filename first
        version = self._parse_version_from_filename(file_path)
        if version:
            return version

        # Try metadata if enabled
        if self.config.get("version", {}).get("use_metadata", False):
            version = self._parse_version_from_metadata(file_path)
            if version:
                return version

        return None

    def _parse_version_from_metadata(self, file_path: Path) -> Optional[str]:
        """Extract version from file metadata.

        Args:
            file_path: Path to file.

        Returns:
            Version string if found, None otherwise.
        """
        # This is a placeholder for metadata extraction
        # In a real implementation, you might use libraries like
        # exifread for images, or file-specific parsers
        logger.debug(f"Metadata extraction not implemented for {file_path}")
        return None

    def scan_directory(self, directory: str) -> None:
        """Scan directory and detect file versions.

        Args:
            directory: Path to directory to scan.

        Raises:
            FileNotFoundError: If directory doesn't exist.
            PermissionError: If directory is not accessible.
        """
        scan_path = Path(directory)
        if not scan_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        if not scan_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        logger.info(
            f"Starting scan of {directory}",
            extra={"directory": directory},
        )

        self.file_versions = {}
        self.version_groups = defaultdict(list)
        self.stats = {
            "files_scanned": 0,
            "files_with_versions": 0,
            "files_organized": 0,
            "version_groups_created": 0,
            "errors": 0,
        }

        try:
            for root, dirs, files in os.walk(scan_path):
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

                    try:
                        version = self._detect_file_version(file_path)
                        if version:
                            normalized_version = self._normalize_version(version)
                            group_key = self._get_version_group_key(
                                normalized_version
                            )

                            self.file_versions[str(file_path)] = {
                                "path": str(file_path),
                                "name": file_path.name,
                                "version": version,
                                "normalized_version": normalized_version,
                                "group_key": group_key,
                                "size_bytes": file_path.stat().st_size,
                            }

                            self.version_groups[group_key].append(
                                str(file_path)
                            )

                            self.stats["files_with_versions"] += 1
                            logger.debug(
                                f"File {file_path.name}: version={version}, "
                                f"group={group_key}"
                            )

                    except Exception as e:
                        logger.warning(
                            f"Error processing file {file_path}: {e}",
                            extra={"file_path": str(file_path)},
                        )
                        self.stats["errors"] += 1

        except PermissionError as e:
            logger.error(
                f"Permission denied accessing {directory}: {e}",
                extra={"directory": directory},
            )
            raise

        self.stats["version_groups_created"] = len(self.version_groups)

        logger.info(
            f"Scan completed: {self.stats['files_with_versions']} files "
            f"with versions found in {self.stats['version_groups_created']} groups",
            extra=self.stats,
        )

    def organize_files(
        self, source_dir: str, dry_run: bool = False
    ) -> None:
        """Organize files into version-based folder structures.

        Args:
            source_dir: Source directory containing files.
            dry_run: If True, simulate organization without moving files.
        """
        source_path = Path(source_dir)
        base_folder = Path(
            self.config.get("organization", {}).get(
                "base_folder", "organized"
            )
        )

        logger.info(
            f"Organizing files from {source_dir}",
            extra={"source_dir": source_dir, "dry_run": dry_run},
        )

        organized_count = 0

        for file_path_str, file_info in self.file_versions.items():
            file_path = Path(file_path_str)

            # Skip if file is not in source directory
            if not file_path.exists() or not str(file_path).startswith(
                str(source_path)
            ):
                continue

            # Determine destination folder
            group_key = file_info["group_key"]
            version_folder = base_folder / f"v{group_key}"

            # Alternative: organize by exact version
            if self.config.get("organization", {}).get(
                "group_by_exact_version", False
            ):
                version_folder = base_folder / f"v{file_info['normalized_version']}"

            version_folder.mkdir(parents=True, exist_ok=True)

            # Determine destination
            dest_path = version_folder / file_path.name

            # Handle filename conflicts
            if dest_path.exists():
                counter = 1
                stem = file_path.stem
                suffix = file_path.suffix
                while dest_path.exists():
                    dest_path = version_folder / f"{stem}_{counter}{suffix}"
                    counter += 1

            # Move file
            try:
                if not dry_run:
                    shutil.move(str(file_path), str(dest_path))
                    logger.info(
                        f"Moved {file_path} -> {dest_path} "
                        f"(Version: {file_info['version']}, "
                        f"Group: {group_key})"
                    )
                else:
                    logger.info(
                        f"[DRY RUN] Would move {file_path} -> {dest_path} "
                        f"(Version: {file_info['version']}, "
                        f"Group: {group_key})"
                    )

                organized_count += 1

            except (OSError, shutil.Error) as e:
                logger.error(
                    f"Error organizing file {file_path}: {e}",
                    extra={"file_path": str(file_path)},
                )
                self.stats["errors"] += 1

        self.stats["files_organized"] = organized_count

        logger.info(
            f"Organization completed: {organized_count} files organized",
            extra={"organized": organized_count},
        )

    def generate_report(self, output_path: Optional[str] = None) -> str:
        """Generate organization report.

        Args:
            output_path: Optional path to save report file.

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
            "VERSION-BASED FILE ORGANIZATION REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY",
            "-" * 80,
            f"Files scanned: {self.stats['files_scanned']:,}",
            f"Files with versions: {self.stats['files_with_versions']:,}",
            f"Files organized: {self.stats['files_organized']:,}",
            f"Version groups created: {self.stats['version_groups_created']:,}",
            f"Errors encountered: {self.stats['errors']}",
            "",
            "VERSION GROUPS",
            "-" * 80,
        ]

        # Sort groups by key
        for group_key in sorted(self.version_groups.keys()):
            files = self.version_groups[group_key]
            report_lines.append(f"Group: v{group_key} ({len(files)} files)")
            for file_path_str in files[:5]:  # Show first 5 files
                file_info = self.file_versions[file_path_str]
                report_lines.append(
                    f"  - {Path(file_info['path']).name} "
                    f"(version: {file_info['version']})"
                )
            if len(files) > 5:
                report_lines.append(f"  ... and {len(files) - 5} more files")
            report_lines.append("")

        if not self.version_groups:
            report_lines.append("No version groups found.")

        report_content = "\n".join(report_lines)

        # Save report
        try:
            output_path_obj = Path(output_file)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path_obj, "w", encoding="utf-8") as f:
                f.write(report_content)
            logger.info(f"Report saved to {output_file}")
        except (IOError, PermissionError) as e:
            logger.error(f"Failed to save report: {e}")
            raise

        return report_content


def main() -> None:
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Organize files by format version, detecting version "
        "numbers and grouping compatible versions"
    )
    parser.add_argument(
        "directory",
        help="Directory to scan and organize",
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
        organizer = VersionFileOrganizer(config_path=args.config)
        organizer.scan_directory(args.directory)
        organizer.organize_files(args.directory, dry_run=args.dry_run)
        organizer.generate_report(output_path=args.report)

        print(
            f"\nOrganization complete. "
            f"Organized {organizer.stats['files_organized']} files "
            f"from {organizer.stats['files_with_versions']} files with versions."
        )
        print(
            f"Created {organizer.stats['version_groups_created']} version groups."
        )

    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
