"""Encoding File Organizer - Organize files by encoding type.

This module provides functionality to detect text file encodings and organize
files by grouping files with the same encoding together.
"""

import logging
import logging.handlers
import os
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class EncodingFileOrganizer:
    """Organizes files by their encoding type."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize EncodingFileOrganizer with configuration.

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
            "files_processed": 0,
            "files_organized": 0,
            "files_skipped": 0,
            "errors": 0,
            "encodings_found": set(),
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
        log_file = log_config.get("file", "logs/encoding_organizer.log")

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

    def _detect_encoding(self, file_path: Path) -> Tuple[Optional[str], float]:
        """Detect file encoding.

        Args:
            file_path: Path to file.

        Returns:
            Tuple of (encoding, confidence) or (None, 0.0) if detection fails.
        """
        detection_config = self.config.get("encoding_detection", {})
        use_chardet = detection_config.get("use_chardet", False)

        if use_chardet:
            try:
                import chardet
                with open(file_path, "rb") as f:
                    raw_data = f.read(detection_config.get("sample_size", 10000))
                    result = chardet.detect(raw_data)
                    if result and result.get("encoding"):
                        encoding = result["encoding"]
                        confidence = result.get("confidence", 0.0)
                        logger.debug(
                            f"Detected encoding: {encoding} "
                            f"(confidence: {confidence:.2f}) for {file_path}"
                        )
                        return encoding, confidence
            except ImportError:
                logger.warning("chardet not available, using fallback detection")
            except Exception as e:
                logger.warning(f"Error using chardet for {file_path}: {e}")

        # Fallback: try common encodings
        encodings_to_try = detection_config.get(
            "encoding_order",
            ["utf-8", "utf-16", "utf-32", "latin-1", "cp1252", "iso-8859-1", "ascii"],
        )

        for encoding in encodings_to_try:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    f.read()
                logger.debug(f"Detected encoding: {encoding} for {file_path}")
                return encoding, 1.0
            except (UnicodeDecodeError, LookupError):
                continue

        logger.warning(f"Could not detect encoding for {file_path}")
        return None, 0.0

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file is likely a text file.

        Args:
            file_path: Path to file.

        Returns:
            True if file appears to be text, False otherwise.
        """
        # Check extension
        text_extensions = self.config.get("text_file", {}).get("extensions", [
            ".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".xml",
            ".yaml", ".yml", ".csv", ".log", ".conf", ".config", ".ini",
            ".sh", ".bat", ".ps1", ".sql", ".r", ".java", ".cpp", ".c",
            ".h", ".hpp", ".go", ".rs", ".swift", ".kt", ".php", ".rb",
        ])

        if file_path.suffix.lower() in text_extensions:
            return True

        # Check if extension filtering is enabled
        if not self.config.get("text_file", {}).get("check_content", True):
            return False

        # Try to read first bytes to check for text
        try:
            with open(file_path, "rb") as f:
                sample = f.read(512)
                # Check if sample contains null bytes (binary indicator)
                if b"\x00" in sample:
                    return False
                # Check if sample is mostly printable ASCII
                printable_ratio = sum(32 <= b < 127 or b in [9, 10, 13] for b in sample) / len(sample) if sample else 0
                return printable_ratio > 0.7
        except Exception:
            return False

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

    def _get_encoding_folder_name(self, encoding: str) -> str:
        """Get folder name for an encoding.

        Args:
            encoding: Encoding name.

        Returns:
            Folder name for the encoding.
        """
        naming_config = self.config.get("organization", {}).get("encoding_naming", {})
        prefix = naming_config.get("prefix", "Encoding")
        separator = naming_config.get("separator", "_")
        normalize_case = naming_config.get("normalize_case", True)

        if normalize_case:
            encoding = encoding.upper()

        # Replace problematic characters in encoding name
        encoding_clean = encoding.replace("-", "_").replace("/", "_")

        return f"{prefix}{separator}{encoding_clean}"

    def scan_files(self, directory: Optional[str] = None) -> Dict[str, List[Dict[str, any]]]:
        """Scan directory and group files by encoding.

        Args:
            directory: Directory to scan (default: from config).

        Returns:
            Dictionary mapping encoding names to lists of file information.

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

        files_by_encoding: Dict[str, List[Dict[str, any]]] = defaultdict(list)

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

                # Check if file is text file
                if not self._is_text_file(file_path):
                    continue

                self.stats["files_scanned"] += 1

                # Detect encoding
                encoding, confidence = self._detect_encoding(file_path)

                if encoding is None:
                    encoding = "unknown"
                    self.stats["errors"] += 1

                self.stats["encodings_found"].add(encoding)

                # Get file information
                try:
                    stat_info = file_path.stat()
                    file_info = {
                        "path": str(file_path),
                        "name": file_path.name,
                        "encoding": encoding,
                        "confidence": confidence,
                        "size": stat_info.st_size,
                        "extension": file_path.suffix.lower() or "no extension",
                        "relative_path": str(file_path.relative_to(scan_path)),
                    }

                    files_by_encoding[encoding].append(file_info)
                    self.stats["files_processed"] += 1

                except (OSError, PermissionError) as e:
                    logger.warning(f"Error accessing file {file_path}: {e}")
                    self.stats["errors"] += 1
                    continue

        except Exception as e:
            logger.error(f"Error during file scan: {e}")
            self.stats["errors"] += 1
            raise

        logger.info(
            f"File scan completed. Found files with {len(files_by_encoding)} encodings"
        )
        return dict(files_by_encoding)

    def organize_files(
        self, files_by_encoding: Dict[str, List[Dict[str, any]]], dry_run: bool = False
    ) -> Dict[str, int]:
        """Organize files by moving them to encoding-based folders.

        Args:
            files_by_encoding: Dictionary mapping encoding names to file lists.
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

        for encoding, files in sorted(files_by_encoding.items()):
            encoding_folder = self._get_encoding_folder_name(encoding)
            encoding_path = output_path / encoding_folder
            encoding_path.mkdir(parents=True, exist_ok=True)

            logger.info(f"Processing encoding {encoding}: {len(files)} files")

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
                        dest_file = encoding_path / relative_path
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                    else:
                        # Move to encoding folder with original name
                        dest_file = encoding_path / file_info["name"]

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
                                    dest_file = encoding_path / new_name
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
        self, files_by_encoding: Dict[str, List[Dict[str, any]]], output_file: Optional[str] = None
    ) -> str:
        """Generate text report of file organization.

        Args:
            files_by_encoding: Dictionary mapping encoding names to file lists.
            output_file: Optional path to save report file.

        Returns:
            Report text.
        """
        from datetime import datetime

        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("ENCODING FILE ORGANIZER REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Statistics
        report_lines.append("STATISTICS")
        report_lines.append("-" * 80)
        report_lines.append(f"Files scanned: {self.stats['files_scanned']}")
        report_lines.append(f"Files processed: {self.stats['files_processed']}")
        report_lines.append(f"Files organized: {self.stats['files_organized']}")
        report_lines.append(f"Files skipped: {self.stats['files_skipped']}")
        report_lines.append(f"Errors: {self.stats['errors']}")
        report_lines.append(f"Encodings found: {len(files_by_encoding)}")
        report_lines.append("")

        # Files by encoding
        report_lines.append("FILES BY ENCODING")
        report_lines.append("-" * 80)

        for encoding in sorted(files_by_encoding.keys()):
            files = files_by_encoding[encoding]
            encoding_folder = self._get_encoding_folder_name(encoding)

            report_lines.append(f"\nEncoding: {encoding} ({encoding_folder}): {len(files)} files")
            report_lines.append("-" * 80)

            total_size = sum(f["size"] for f in files)
            avg_confidence = sum(f.get("confidence", 0.0) for f in files) / len(files) if files else 0.0
            report_lines.append(f"Total size: {total_size:,} bytes")
            report_lines.append(f"Average confidence: {avg_confidence:.2f}")

            # Show file list
            if self.config.get("report", {}).get("show_file_list", True):
                for file_info in files:
                    report_lines.append(f"  {file_info['relative_path']}")
                    report_lines.append(f"    Size: {file_info['size']:,} bytes")
                    if file_info.get("confidence", 0.0) > 0:
                        report_lines.append(f"    Confidence: {file_info['confidence']:.2f}")
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

    def print_summary(self, files_by_encoding: Dict[str, List[Dict[str, any]]]) -> None:
        """Print summary to console.

        Args:
            files_by_encoding: Dictionary mapping encoding names to file lists.
        """
        print("\n" + "=" * 80)
        print("ENCODING FILE ORGANIZER SUMMARY")
        print("=" * 80)
        print(f"Files scanned: {self.stats['files_scanned']}")
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files organized: {self.stats['files_organized']}")
        print(f"Files skipped: {self.stats['files_skipped']}")
        if self.stats['errors'] > 0:
            print(f"Errors: {self.stats['errors']}")
        print(f"\nEncodings found: {len(files_by_encoding)}")
        print("\nFiles by encoding:")
        for encoding in sorted(files_by_encoding.keys()):
            files = files_by_encoding[encoding]
            encoding_folder = self._get_encoding_folder_name(encoding)
            total_size = sum(f["size"] for f in files)
            print(
                f"  {encoding} ({encoding_folder}): "
                f"{len(files)} files, {total_size:,} bytes"
            )
        print("=" * 80 + "\n")


def main() -> int:
    """Main entry point for encoding file organizer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Organize files by encoding type"
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
        help="Organize files by moving them to encoding folders",
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
        organizer = EncodingFileOrganizer(config_path=args.config)

        # Override dry run setting
        if args.dry_run:
            organizer.config["organization"]["dry_run"] = True

        # Scan files
        files_by_encoding = organizer.scan_files(directory=args.directory)

        # Organize files if requested
        if args.organize:
            dry_run = organizer.config.get("organization", {}).get("dry_run", True)
            if args.dry_run:
                dry_run = True
            organizer.organize_files(files_by_encoding, dry_run=dry_run)

        # Print summary
        if not args.no_summary:
            organizer.print_summary(files_by_encoding)

        # Generate report
        if args.report:
            report = organizer.generate_report(files_by_encoding, output_file=args.report)
            print(f"\nReport saved to: {args.report}")
        elif organizer.config.get("report", {}).get("auto_save", False):
            report_file = organizer.config.get("report", {}).get("output_file", "logs/encoding_report.txt")
            report = organizer.generate_report(files_by_encoding, output_file=report_file)
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
