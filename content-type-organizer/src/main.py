"""Content Type Organizer - Organize files by actual content type.

This module provides functionality to identify files by content type using
MIME type detection and magic numbers, organizing files by actual content
rather than file extensions. This helps organize files even when extensions
are missing or incorrect.
"""

import logging
import logging.handlers
import mimetypes
import os
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

# Try to import python-magic for better MIME detection
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    logger.warning(
        "python-magic not available. Using fallback MIME detection."
    )


class ContentTypeOrganizer:
    """Organizes files by actual content type using MIME detection."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize ContentTypeOrganizer with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.magic_numbers = self._load_magic_numbers()
        self.mime_mappings = self._load_mime_mappings()
        self.file_types: Dict[str, Dict[str, Any]] = {}
        self.stats = {
            "files_scanned": 0,
            "files_organized": 0,
            "extension_mismatches": 0,
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

    def _load_magic_numbers(self) -> Dict[str, List[bytes]]:
        """Load file magic number definitions.

        Returns:
            Dictionary mapping MIME types to magic number bytes.
        """
        magic_numbers = {
            "application/pdf": [b"%PDF"],
            "image/png": [b"\x89PNG\r\n\x1a\n"],
            "image/jpeg": [b"\xff\xd8\xff"],
            "image/gif": [b"GIF87a", b"GIF89a"],
            "application/zip": [b"PK\x03\x04", b"PK\x05\x06"],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
                b"PK\x03\x04"
            ],
            "audio/mpeg": [b"ID3", b"\xff\xfb", b"\xff\xf3"],
            "video/mp4": [b"\x00\x00\x00", b"ftyp"],
            "video/x-msvideo": [b"RIFF"],
            "audio/x-wav": [b"RIFF"],
            "application/x-executable": [b"MZ"],
            "text/html": [b"<!DOCTYPE", b"<html", b"<HTML"],
            "text/xml": [b"<?xml"],
            "application/json": [b"{", b"["],
        }

        # Add custom magic numbers from config
        custom_magic = self.config.get("content_detection", {}).get(
            "magic_numbers", {}
        )
        for mime_type, magics in custom_magic.items():
            if isinstance(magics, str):
                magic_numbers[mime_type] = [magics.encode()]
            elif isinstance(magics, list):
                magic_numbers[mime_type] = [
                    m.encode() if isinstance(m, str) else m for m in magics
                ]

        return magic_numbers

    def _load_mime_mappings(self) -> Dict[str, str]:
        """Load MIME type to folder name mappings.

        Returns:
            Dictionary mapping MIME types to folder names.
        """
        mappings = {
            "image/jpeg": "Images",
            "image/png": "Images",
            "image/gif": "Images",
            "image/bmp": "Images",
            "image/webp": "Images",
            "image/svg+xml": "Images",
            "application/pdf": "Documents",
            "application/msword": "Documents",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Documents",
            "application/vnd.ms-excel": "Documents",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Documents",
            "application/vnd.ms-powerpoint": "Documents",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": "Documents",
            "text/plain": "Documents",
            "text/html": "Documents",
            "text/xml": "Documents",
            "application/json": "Documents",
            "video/mp4": "Videos",
            "video/x-msvideo": "Videos",
            "video/quicktime": "Videos",
            "video/x-matroska": "Videos",
            "video/webm": "Videos",
            "audio/mpeg": "Music",
            "audio/x-wav": "Music",
            "audio/flac": "Music",
            "audio/ogg": "Music",
            "application/zip": "Archives",
            "application/x-rar-compressed": "Archives",
            "application/x-7z-compressed": "Archives",
            "application/x-tar": "Archives",
            "application/gzip": "Archives",
        }

        # Add custom mappings from config
        custom_mappings = self.config.get("organization", {}).get(
            "mime_mappings", {}
        )
        mappings.update(custom_mappings)

        return mappings

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

    def _detect_mime_by_magic_number(self, file_path: Path) -> Optional[str]:
        """Detect MIME type using magic numbers.

        Args:
            file_path: Path to file.

        Returns:
            MIME type string or None if not detected.
        """
        try:
            with open(file_path, "rb") as f:
                header = f.read(16)  # Read first 16 bytes

            if not header:
                return None

            # Check against known magic numbers
            for mime_type, magics in self.magic_numbers.items():
                for magic_bytes in magics:
                    if header.startswith(magic_bytes):
                        logger.debug(
                            f"Detected {mime_type} by magic number: {file_path.name}"
                        )
                        return mime_type

            return None
        except (IOError, PermissionError) as e:
            logger.debug(f"Cannot read file for magic number: {file_path} - {e}")
            return None

    def _detect_mime_by_python_magic(self, file_path: Path) -> Optional[str]:
        """Detect MIME type using python-magic library.

        Args:
            file_path: Path to file.

        Returns:
            MIME type string or None if not detected.
        """
        if not HAS_MAGIC:
            return None

        try:
            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(str(file_path))
            logger.debug(
                f"Detected {mime_type} by python-magic: {file_path.name}"
            )
            return mime_type
        except Exception as e:
            logger.debug(f"python-magic detection failed: {e}")
            return None

    def _detect_mime_by_extension(self, file_path: Path) -> Optional[str]:
        """Detect MIME type using file extension (fallback).

        Args:
            file_path: Path to file.

        Returns:
            MIME type string or None if not detected.
        """
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            logger.debug(
                f"Detected {mime_type} by extension: {file_path.name}"
            )
        return mime_type

    def _detect_content_type(self, file_path: Path) -> Tuple[Optional[str], str]:
        """Detect file content type using multiple methods.

        Args:
            file_path: Path to file.

        Returns:
            Tuple of (mime_type, detection_method).
        """
        # Try python-magic first (most accurate)
        mime_type = self._detect_mime_by_python_magic(file_path)
        if mime_type:
            return (mime_type, "python-magic")

        # Try magic numbers
        mime_type = self._detect_mime_by_magic_number(file_path)
        if mime_type:
            return (mime_type, "magic_number")

        # Fallback to extension
        mime_type = self._detect_mime_by_extension(file_path)
        if mime_type:
            return (mime_type, "extension")

        return (None, "unknown")

    def _get_folder_for_mime(self, mime_type: Optional[str]) -> str:
        """Get folder name for MIME type.

        Args:
            mime_type: MIME type string.

        Returns:
            Folder name.
        """
        if not mime_type:
            return self.config.get("organization", {}).get(
                "unknown_folder", "Unknown"
            )

        # Check custom mappings first
        if mime_type in self.mime_mappings:
            return self.mime_mappings[mime_type]

        # Use MIME type category
        main_type = mime_type.split("/")[0]
        type_mapping = {
            "image": "Images",
            "video": "Videos",
            "audio": "Music",
            "text": "Documents",
            "application": "Applications",
        }

        return type_mapping.get(main_type, "Other")

    def scan_directory(self, directory: str) -> None:
        """Scan directory and detect file content types.

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
            f"Starting content type scan of {directory}",
            extra={"directory": directory},
        )

        self.file_types = {}
        self.stats = {
            "files_scanned": 0,
            "files_organized": 0,
            "extension_mismatches": 0,
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
                        mime_type, method = self._detect_content_type(file_path)
                        extension_mime, _ = mimetypes.guess_type(str(file_path))

                        # Check for extension mismatch
                        extension_mismatch = False
                        if mime_type and extension_mime:
                            if mime_type != extension_mime:
                                extension_mismatch = True
                                self.stats["extension_mismatches"] += 1

                        self.file_types[str(file_path)] = {
                            "path": str(file_path),
                            "name": file_path.name,
                            "extension": file_path.suffix,
                            "mime_type": mime_type,
                            "detection_method": method,
                            "extension_mime": extension_mime,
                            "extension_mismatch": extension_mismatch,
                            "folder": self._get_folder_for_mime(mime_type),
                            "size_bytes": file_path.stat().st_size,
                        }

                        if extension_mismatch:
                            logger.warning(
                                f"Extension mismatch: {file_path.name} "
                                f"(extension suggests {extension_mime}, "
                                f"content is {mime_type})",
                                extra={
                                    "file_path": str(file_path),
                                    "extension_mime": extension_mime,
                                    "detected_mime": mime_type,
                                },
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

        logger.info(
            f"Scan completed: {self.stats['files_scanned']} files scanned, "
            f"{self.stats['extension_mismatches']} extension mismatches found",
            extra=self.stats,
        )

    def organize_files(
        self, source_dir: str, dry_run: bool = False
    ) -> None:
        """Organize files into content-type-based folders.

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

        for file_path_str, file_info in self.file_types.items():
            file_path = Path(file_path_str)

            # Skip if file is not in source directory
            if not file_path.exists() or not str(file_path).startswith(
                str(source_path)
            ):
                continue

            # Determine destination folder
            content_folder = base_folder / file_info["folder"]
            content_folder.mkdir(parents=True, exist_ok=True)

            # Determine destination
            dest_path = content_folder / file_path.name

            # Handle filename conflicts
            if dest_path.exists():
                counter = 1
                stem = file_path.stem
                suffix = file_path.suffix
                while dest_path.exists():
                    dest_path = content_folder / f"{stem}_{counter}{suffix}"
                    counter += 1

            # Move file
            try:
                if not dry_run:
                    shutil.move(str(file_path), str(dest_path))
                    logger.info(
                        f"Moved {file_path} -> {dest_path} "
                        f"(Content Type: {file_info['mime_type']}, "
                        f"Folder: {file_info['folder']})"
                    )
                else:
                    logger.info(
                        f"[DRY RUN] Would move {file_path} -> {dest_path} "
                        f"(Content Type: {file_info['mime_type']}, "
                        f"Folder: {file_info['folder']})"
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

        # Count files by content type
        type_counts = defaultdict(int)
        method_counts = defaultdict(int)
        mismatch_files = []

        for file_info in self.file_types.values():
            mime_type = file_info["mime_type"] or "unknown"
            type_counts[mime_type] += 1
            method_counts[file_info["detection_method"]] += 1

            if file_info["extension_mismatch"]:
                mismatch_files.append(file_info)

        report_lines = [
            "=" * 80,
            "CONTENT TYPE ORGANIZATION REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY",
            "-" * 80,
            f"Files scanned: {self.stats['files_scanned']:,}",
            f"Files organized: {self.stats['files_organized']:,}",
            f"Extension mismatches: {self.stats['extension_mismatches']:,}",
            f"Errors encountered: {self.stats['errors']}",
            "",
            "DETECTION METHOD STATISTICS",
            "-" * 80,
        ]

        for method, count in sorted(
            method_counts.items(), key=lambda x: x[1], reverse=True
        ):
            report_lines.append(f"{method:20s}: {count:6,} files")

        report_lines.extend(
            [
                "",
                "CONTENT TYPE DISTRIBUTION",
                "-" * 80,
            ]
        )

        for mime_type, count in sorted(
            type_counts.items(), key=lambda x: x[1], reverse=True
        ):
            report_lines.append(f"{mime_type:40s}: {count:6,} files")

        if mismatch_files:
            report_lines.extend(
                [
                    "",
                    "EXTENSION MISMATCHES",
                    "-" * 80,
                ]
            )
            for file_info in mismatch_files[:20]:
                report_lines.extend(
                    [
                        f"File: {file_info['name']}",
                        f"  Extension suggests: {file_info['extension_mime']}",
                        f"  Actual content: {file_info['mime_type']}",
                        f"  Detection method: {file_info['detection_method']}",
                        "",
                    ]
                )
            if len(mismatch_files) > 20:
                report_lines.append(
                    f"... and {len(mismatch_files) - 20} more mismatches"
                )

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
        description="Organize files by actual content type using MIME detection "
        "and magic numbers"
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
        organizer = ContentTypeOrganizer(config_path=args.config)
        organizer.scan_directory(args.directory)
        organizer.organize_files(args.directory, dry_run=args.dry_run)
        organizer.generate_report(output_path=args.report)

        print(
            f"\nOrganization complete. "
            f"Organized {organizer.stats['files_organized']} files "
            f"from {organizer.stats['files_scanned']} scanned."
        )
        if organizer.stats["extension_mismatches"] > 0:
            print(
                f"Found {organizer.stats['extension_mismatches']} files with "
                f"extension mismatches."
            )

    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
