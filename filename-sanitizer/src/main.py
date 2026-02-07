"""Filename Sanitizer - Find and rename files with problematic characters.

This module provides functionality to find files with special characters, spaces,
or problematic characters in names and optionally rename them to filesystem-safe names.
"""

import logging
import logging.handlers
import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FilenameSanitizer:
    """Finds and renames files with problematic characters."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize FilenameSanitizer with configuration.

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
            "files_found": 0,
            "files_renamed": 0,
            "files_skipped": 0,
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
            config["scan"]["directory"] = os.getenv("SCAN_DIRECTORY")
        if os.getenv("DRY_RUN"):
            config["renaming"]["dry_run"] = os.getenv("DRY_RUN").lower() == "true"

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/filename_sanitizer.log")

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

    def _has_problematic_characters(self, filename: str) -> Tuple[bool, List[str]]:
        """Check if filename has problematic characters.

        Args:
            filename: File name to check.

        Returns:
            Tuple of (has_problems, list_of_issues).
        """
        issues = []
        sanitize_config = self.config.get("sanitization", {})

        # Check for spaces
        if sanitize_config.get("remove_spaces", True) and " " in filename:
            issues.append("contains_spaces")

        # Check for special characters
        special_chars = sanitize_config.get("problematic_chars", [])
        for char in special_chars:
            if char in filename:
                issues.append(f"contains_{char}")

        # Check for multiple consecutive special characters
        if sanitize_config.get("remove_consecutive", True):
            if re.search(r'[^\w\s-]{2,}', filename):
                issues.append("consecutive_special_chars")

        # Check for leading/trailing special characters
        if sanitize_config.get("remove_leading_trailing", True):
            if filename and filename[0] in ".-_":
                issues.append("leading_special_char")
            if filename and filename[-1] in ".-_":
                issues.append("trailing_special_char")

        # Check for reserved names (Windows)
        reserved_names = sanitize_config.get("reserved_names", [
            "CON", "PRN", "AUX", "NUL",
            "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
            "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
        ])
        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in reserved_names:
            issues.append("reserved_name")

        # Check for control characters
        if any(ord(c) < 32 for c in filename):
            issues.append("control_characters")

        return len(issues) > 0, issues

    def _sanitize_filename(self, filename: str) -> str:
        """Generate filesystem-safe filename.

        Args:
            filename: Original filename.

        Returns:
            Sanitized filename.
        """
        sanitize_config = self.config.get("sanitization", {})
        replacement_config = self.config.get("replacement", {})

        # Get file extension
        path_obj = Path(filename)
        extension = path_obj.suffix
        name_without_ext = path_obj.stem

        # Start with the name without extension
        sanitized = name_without_ext

        # Replace spaces
        if sanitize_config.get("remove_spaces", True):
            space_replacement = replacement_config.get("space_replacement", "_")
            sanitized = sanitized.replace(" ", space_replacement)

        # Replace problematic characters
        problematic_chars = sanitize_config.get("problematic_chars", [])
        char_replacement = replacement_config.get("char_replacement", "_")
        for char in problematic_chars:
            sanitized = sanitized.replace(char, char_replacement)

        # Remove or replace consecutive special characters
        if sanitize_config.get("remove_consecutive", True):
            consecutive_replacement = replacement_config.get("consecutive_replacement", "_")
            sanitized = re.sub(r'[^\w\s-]{2,}', consecutive_replacement, sanitized)

        # Remove leading/trailing special characters
        if sanitize_config.get("remove_leading_trailing", True):
            sanitized = sanitized.strip(".-_")

        # Remove control characters
        sanitized = "".join(c for c in sanitized if ord(c) >= 32)

        # Handle reserved names (Windows)
        reserved_names = sanitize_config.get("reserved_names", [])
        if sanitized.upper() in reserved_names:
            sanitized = f"_{sanitized}"

        # Ensure filename is not empty
        if not sanitized:
            sanitized = "unnamed"

        # Limit length if configured
        max_length = sanitize_config.get("max_length", None)
        if max_length:
            # Reserve space for extension
            ext_length = len(extension)
            max_name_length = max_length - ext_length
            if max_name_length > 0:
                sanitized = sanitized[:max_name_length]

        # Reconstruct filename with extension
        return sanitized + extension

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

    def find_problematic_files(
        self, directory: Optional[str] = None
    ) -> List[Dict[str, any]]:
        """Find files with problematic characters.

        Args:
            directory: Directory to scan (default: from config).

        Returns:
            List of file information dictionaries.

        Raises:
            FileNotFoundError: If directory doesn't exist.
            NotADirectoryError: If path is not a directory.
        """
        scan_config = self.config.get("scan", {})
        scan_dir = directory or scan_config.get("directory", ".")

        if not os.path.exists(scan_dir):
            raise FileNotFoundError(f"Directory not found: {scan_dir}")

        if not os.path.isdir(scan_dir):
            raise NotADirectoryError(f"Path is not a directory: {scan_dir}")

        logger.info(f"Starting file scan: {scan_dir}")

        scan_path = Path(scan_dir).resolve()
        recursive = scan_config.get("recursive", True)

        problematic_files = []

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

                filename = file_path.name
                has_issues, issues = self._has_problematic_characters(filename)

                if has_issues:
                    sanitized_name = self._sanitize_filename(filename)
                    file_info = {
                        "path": str(file_path),
                        "original_name": filename,
                        "sanitized_name": sanitized_name,
                        "directory": str(file_path.parent),
                        "issues": issues,
                        "needs_rename": sanitized_name != filename,
                    }

                    problematic_files.append(file_info)
                    self.stats["files_found"] += 1

        except Exception as e:
            logger.error(f"Error during file scan: {e}")
            self.stats["errors"] += 1
            raise

        logger.info("File scan completed")
        logger.info(f"Statistics: {self.stats}")

        return problematic_files

    def rename_file(
        self, file_path: Path, new_name: str, dry_run: bool = False
    ) -> bool:
        """Rename a file.

        Args:
            file_path: Path to file to rename.
            new_name: New filename.
            dry_run: If True, simulate renaming without actually renaming.

        Returns:
            True if renaming succeeded or was simulated, False otherwise.
        """
        if not file_path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return False

        new_path = file_path.parent / new_name

        # Check if target already exists
        if new_path.exists() and new_path != file_path:
            conflict_config = self.config.get("renaming", {}).get("conflicts", {})
            conflict_action = conflict_config.get("action", "skip")

            if conflict_action == "skip":
                logger.warning(f"Target file exists, skipping: {new_path}")
                self.stats["files_skipped"] += 1
                return False
            elif conflict_action == "overwrite":
                logger.warning(f"Target file exists, will overwrite: {new_path}")
            elif conflict_action == "rename":
                # Generate unique name
                base_name = new_path.stem
                extension = new_path.suffix
                counter = 1
                while new_path.exists():
                    new_name_with_counter = f"{base_name}_{counter}{extension}"
                    new_path = file_path.parent / new_name_with_counter
                    counter += 1
                logger.info(f"Renamed to avoid conflict: {new_path.name}")

        try:
            if dry_run:
                logger.info(f"[DRY RUN] Would rename: {file_path.name} -> {new_path.name}")
                return True

            file_path.rename(new_path)
            logger.info(f"Renamed: {file_path.name} -> {new_path.name}")
            return True

        except (OSError, PermissionError) as e:
            logger.error(f"Error renaming {file_path}: {e}")
            self.stats["errors"] += 1
            return False

    def rename_files(
        self, files: List[Dict[str, any]], dry_run: bool = False
    ) -> Dict[str, int]:
        """Rename multiple files.

        Args:
            files: List of file information dictionaries.
            dry_run: If True, simulate renaming without actually renaming.

        Returns:
            Dictionary with renaming statistics.
        """
        renaming_config = self.config.get("renaming", {})
        dry_run = dry_run or renaming_config.get("dry_run", True)

        logger.info(f"Starting file renaming (dry_run={dry_run})")

        for file_info in files:
            if not file_info.get("needs_rename", False):
                continue

            file_path = Path(file_info["path"])
            new_name = file_info["sanitized_name"]

            if self.rename_file(file_path, new_name, dry_run=dry_run):
                self.stats["files_renamed"] += 1
            else:
                self.stats["files_skipped"] += 1

        logger.info("File renaming completed")
        logger.info(f"Statistics: {self.stats}")

        return {
            "files_renamed": self.stats["files_renamed"],
            "files_skipped": self.stats["files_skipped"],
            "errors": self.stats["errors"],
        }

    def generate_report(
        self, files: List[Dict[str, any]], output_file: Optional[str] = None
    ) -> str:
        """Generate text report of problematic files.

        Args:
            files: List of file information dictionaries.
            output_file: Optional path to save report file.

        Returns:
            Report text.
        """
        from datetime import datetime

        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("FILENAME SANITIZER REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Statistics
        report_lines.append("STATISTICS")
        report_lines.append("-" * 80)
        report_lines.append(f"Files scanned: {self.stats['files_scanned']}")
        report_lines.append(f"Files with problematic names: {self.stats['files_found']}")
        report_lines.append(f"Files renamed: {self.stats['files_renamed']}")
        report_lines.append(f"Files skipped: {self.stats['files_skipped']}")
        report_lines.append(f"Errors: {self.stats['errors']}")
        report_lines.append("")

        # File list
        report_lines.append("PROBLEMATIC FILES")
        report_lines.append("-" * 80)

        if not files:
            report_lines.append("No files with problematic names found.")
        else:
            for file_info in files:
                report_lines.append(f"Path: {file_info['path']}")
                report_lines.append(f"  Original name: {file_info['original_name']}")
                report_lines.append(f"  Sanitized name: {file_info['sanitized_name']}")
                report_lines.append(f"  Issues: {', '.join(file_info['issues'])}")
                if file_info.get("needs_rename"):
                    report_lines.append(f"  Status: Needs rename")
                report_lines.append("")

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

    def print_summary(self) -> None:
        """Print summary to console."""
        print("\n" + "=" * 80)
        print("FILENAME SANITIZER SUMMARY")
        print("=" * 80)
        print(f"Files scanned: {self.stats['files_scanned']}")
        print(f"Files with problematic names: {self.stats['files_found']}")
        print(f"Files renamed: {self.stats['files_renamed']}")
        print(f"Files skipped: {self.stats['files_skipped']}")
        if self.stats['errors'] > 0:
            print(f"Errors: {self.stats['errors']}")
        print("=" * 80 + "\n")


def main() -> int:
    """Main entry point for filename sanitizer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Find and rename files with problematic characters"
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
        "-r",
        "--rename",
        action="store_true",
        help="Rename problematic files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate renaming without actually renaming",
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
        sanitizer = FilenameSanitizer(config_path=args.config)

        # Override dry run setting
        if args.dry_run:
            sanitizer.config["renaming"]["dry_run"] = True

        # Find problematic files
        files = sanitizer.find_problematic_files(directory=args.directory)

        # Rename files if requested
        if args.rename:
            dry_run = sanitizer.config.get("renaming", {}).get("dry_run", True)
            if args.dry_run:
                dry_run = True
            sanitizer.rename_files(files, dry_run=dry_run)

        # Print summary
        if not args.no_summary:
            sanitizer.print_summary()

        # Generate report
        if args.report:
            report = sanitizer.generate_report(files, output_file=args.report)
            print(f"\nReport saved to: {args.report}")
        elif sanitizer.config.get("report", {}).get("auto_save", False):
            report_file = sanitizer.config.get("report", {}).get("output_file", "logs/sanitizer_report.txt")
            report = sanitizer.generate_report(files, output_file=report_file)
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
