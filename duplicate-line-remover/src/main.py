"""Duplicate Line Remover - Remove duplicate lines from text files.

This module provides functionality to remove duplicate lines from text files
while preserving line order, with options to ignore case and whitespace differences.
"""

import logging
import logging.handlers
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DuplicateLineRemover:
    """Removes duplicate lines from text files with various options."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize DuplicateLineRemover with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.stats = {
            "files_processed": 0,
            "total_lines_read": 0,
            "duplicate_lines_removed": 0,
            "unique_lines_kept": 0,
            "files_failed": 0,
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
        if os.getenv("IGNORE_CASE"):
            config["processing"]["ignore_case"] = os.getenv("IGNORE_CASE").lower() == "true"
        if os.getenv("IGNORE_WHITESPACE"):
            config["processing"]["ignore_whitespace"] = (
                os.getenv("IGNORE_WHITESPACE").lower() == "true"
            )

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/duplicate_remover.log")

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

    def _normalize_line(self, line: str) -> str:
        """Normalize line for comparison based on configuration.

        Args:
            line: Original line to normalize.

        Returns:
            Normalized line for comparison.
        """
        normalized = line

        # Trim leading/trailing whitespace if configured
        if self.config.get("processing", {}).get("trim_lines", False):
            normalized = normalized.strip()

        # Normalize whitespace (multiple spaces to single space)
        if self.config.get("processing", {}).get("normalize_whitespace", False):
            normalized = re.sub(r"\s+", " ", normalized)

        # Ignore case if configured
        if self.config.get("processing", {}).get("ignore_case", False):
            normalized = normalized.lower()

        # Ignore whitespace differences if configured
        if self.config.get("processing", {}).get("ignore_whitespace", False):
            # Remove all whitespace for comparison
            normalized = re.sub(r"\s+", "", normalized)

        return normalized

    def _should_preserve_line(self, line: str, normalized: str, seen: Set[str]) -> bool:
        """Check if line should be preserved (not a duplicate).

        Args:
            line: Original line.
            normalized: Normalized line for comparison.
            seen: Set of seen normalized lines.

        Returns:
            True if line should be preserved, False if duplicate.
        """
        # Handle empty lines
        preserve_empty = self.config.get("processing", {}).get("preserve_empty_lines", True)
        if not line.strip() and preserve_empty:
            # Only preserve first empty line if configured
            if normalized not in seen:
                seen.add(normalized)
                return True
            return False

        # Check if normalized line has been seen
        if normalized in seen:
            return False

        # Add to seen set and preserve
        seen.add(normalized)
        return True

    def _remove_duplicates(self, input_path: Path) -> Tuple[List[str], int]:
        """Remove duplicate lines from file.

        Args:
            input_path: Path to input file.

        Returns:
            Tuple of (deduplicated_lines, duplicates_removed_count).
        """
        file_config = self.config.get("file_handling", {})
        input_encoding = file_config.get("input_encoding", "utf-8")

        seen: Set[str] = set()
        deduplicated_lines: List[str] = []
        duplicates_removed = 0

        try:
            with open(input_path, "r", encoding=input_encoding) as f:
                for line in f:
                    original_line = line
                    # Preserve line ending (newline)
                    has_newline = line.endswith("\n")
                    if has_newline:
                        line_content = line.rstrip("\n\r")
                    else:
                        line_content = line

                    normalized = self._normalize_line(line_content)

                    if self._should_preserve_line(line_content, normalized, seen):
                        # Preserve original line with newline
                        if has_newline:
                            deduplicated_lines.append(line_content + "\n")
                        else:
                            deduplicated_lines.append(line_content)
                    else:
                        duplicates_removed += 1

            return deduplicated_lines, duplicates_removed

        except UnicodeDecodeError as e:
            logger.error(f"Encoding error reading {input_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading file {input_path}: {e}")
            raise

    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """Create backup of file.

        Args:
            file_path: Path to file to backup.

        Returns:
            Path to backup file or None if backup disabled.
        """
        if not self.config.get("file_handling", {}).get("backup_original", True):
            return None

        backup_suffix = self.config.get("file_handling", {}).get("backup_suffix", ".bak")
        backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)

        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
            return None

    def _get_output_path(self, input_path: Path) -> Path:
        """Get output file path.

        Args:
            input_path: Input file path.

        Returns:
            Output file path.
        """
        overwrite = self.config.get("file_handling", {}).get("overwrite_original", False)

        if overwrite:
            return input_path

        output_suffix = self.config.get("output", {}).get("output_suffix", ".deduplicated")
        return input_path.with_suffix(input_path.suffix + output_suffix)

    def process_file(self, input_path: Path) -> bool:
        """Process a single file to remove duplicates.

        Args:
            input_path: Path to input file.

        Returns:
            True if successful, False otherwise.
        """
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            self.stats["files_failed"] += 1
            return False

        if not input_path.is_file():
            logger.error(f"Path is not a file: {input_path}")
            self.stats["files_failed"] += 1
            return False

        logger.info(f"Processing file: {input_path}")

        try:
            # Remove duplicates
            deduplicated_lines, duplicates_removed = self._remove_duplicates(input_path)

            total_lines = len(deduplicated_lines) + duplicates_removed
            unique_lines = len(deduplicated_lines)

            self.stats["total_lines_read"] += total_lines
            self.stats["duplicate_lines_removed"] += duplicates_removed
            self.stats["unique_lines_kept"] += unique_lines

            # Create backup
            self._create_backup(input_path)

            # Write output
            if self.config.get("output", {}).get("create_output_file", True):
                output_path = self._get_output_path(input_path)
                file_config = self.config.get("file_handling", {})
                output_encoding = file_config.get("output_encoding", "utf-8")

                with open(output_path, "w", encoding=output_encoding) as f:
                    f.writelines(deduplicated_lines)

                logger.info(
                    f"Processed {input_path}: {total_lines} lines -> {unique_lines} unique "
                    f"({duplicates_removed} duplicates removed)"
                )
                logger.info(f"Output written to: {output_path}")

            self.stats["files_processed"] += 1
            return True

        except Exception as e:
            logger.error(f"Error processing file {input_path}: {e}", exc_info=True)
            self.stats["files_failed"] += 1
            return False

    def process_directory(self, directory_path: Path) -> dict:
        """Process all matching files in a directory.

        Args:
            directory_path: Directory to process.

        Returns:
            Dictionary with processing statistics.
        """
        if not directory_path.exists() or not directory_path.is_dir():
            logger.error(f"Directory not found: {directory_path}")
            return self.stats

        batch_config = self.config.get("batch", {})
        patterns = batch_config.get("file_patterns", ["*.txt"])
        recursive = batch_config.get("recursive", False)

        logger.info(f"Processing directory: {directory_path} (recursive: {recursive})")

        files_processed = 0
        for pattern in patterns:
            if recursive:
                files = list(directory_path.rglob(pattern))
            else:
                files = list(directory_path.glob(pattern))

            for file_path in files:
                if file_path.is_file():
                    if self.process_file(file_path):
                        files_processed += 1

        logger.info(f"Processed {files_processed} file(s) from directory")
        return self.stats

    def _generate_report(self) -> None:
        """Generate processing report."""
        report_config = self.config.get("reporting", {})
        report_file = report_config.get("report_file", "logs/deduplication_report.txt")

        report_path = Path(report_file)
        if not report_path.is_absolute():
            project_root = Path(__file__).parent.parent
            report_path = project_root / report_file

        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("Duplicate Line Removal Report\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")

            if report_config.get("include_statistics", True):
                f.write("Statistics\n")
                f.write("-" * 60 + "\n")
                f.write(f"Files Processed: {self.stats['files_processed']}\n")
                f.write(f"Total Lines Read: {self.stats['total_lines_read']}\n")
                f.write(f"Duplicate Lines Removed: {self.stats['duplicate_lines_removed']}\n")
                f.write(f"Unique Lines Kept: {self.stats['unique_lines_kept']}\n")
                f.write(f"Files Failed: {self.stats['files_failed']}\n")

                if self.stats["total_lines_read"] > 0:
                    duplicate_percent = (
                        self.stats["duplicate_lines_removed"]
                        / self.stats["total_lines_read"]
                        * 100
                    )
                    f.write(f"Duplicate Percentage: {duplicate_percent:.2f}%\n")

                f.write("\n")

            f.write("Processing Options\n")
            f.write("-" * 60 + "\n")
            processing = self.config.get("processing", {})
            f.write(f"Ignore Case: {processing.get('ignore_case', False)}\n")
            f.write(f"Ignore Whitespace: {processing.get('ignore_whitespace', False)}\n")
            f.write(f"Preserve Empty Lines: {processing.get('preserve_empty_lines', True)}\n")
            f.write(f"Trim Lines: {processing.get('trim_lines', False)}\n")
            f.write(f"Normalize Whitespace: {processing.get('normalize_whitespace', False)}\n")

        logger.info(f"Report generated: {report_path}")


def main() -> int:
    """Main entry point for duplicate line remover."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Remove duplicate lines from text files while preserving order"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-i",
        "--input",
        help="Input file path",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path (overrides config)",
    )
    parser.add_argument(
        "--ignore-case",
        action="store_true",
        help="Ignore case differences",
    )
    parser.add_argument(
        "--ignore-whitespace",
        action="store_true",
        help="Ignore whitespace differences",
    )
    parser.add_argument(
        "-d",
        "--directory",
        help="Process all matching files in directory",
    )

    args = parser.parse_args()

    try:
        remover = DuplicateLineRemover(config_path=args.config)

        # Override config with command-line arguments
        if args.ignore_case:
            remover.config["processing"]["ignore_case"] = True
        if args.ignore_whitespace:
            remover.config["processing"]["ignore_whitespace"] = True
        if args.output:
            remover.config["file_handling"]["overwrite_original"] = False
            remover.config["output"]["output_suffix"] = ""
            # Will be handled in process_file

        if args.directory:
            remover.process_directory(Path(args.directory))
        elif args.input:
            input_path = Path(args.input)
            if args.output:
                # Custom output path
                output_path = Path(args.output)
                # Process and write to custom output
                deduplicated_lines, _ = remover._remove_duplicates(input_path)
                file_config = remover.config.get("file_handling", {})
                output_encoding = file_config.get("output_encoding", "utf-8")
                with open(output_path, "w", encoding=output_encoding) as f:
                    f.writelines(deduplicated_lines)
                remover.stats["files_processed"] += 1
            else:
                remover.process_file(input_path)
        else:
            logger.error("No input file or directory specified. Use -i or -d option.")
            return 1

        # Generate report
        if remover.config.get("reporting", {}).get("generate_report", True):
            remover._generate_report()

        print("\n" + "=" * 50)
        print("Processing Summary")
        print("=" * 50)
        print(f"Files Processed: {remover.stats['files_processed']}")
        print(f"Total Lines Read: {remover.stats['total_lines_read']}")
        print(f"Duplicate Lines Removed: {remover.stats['duplicate_lines_removed']}")
        print(f"Unique Lines Kept: {remover.stats['unique_lines_kept']}")
        print(f"Files Failed: {remover.stats['files_failed']}")

        if remover.stats["total_lines_read"] > 0:
            duplicate_percent = (
                remover.stats["duplicate_lines_removed"]
                / remover.stats["total_lines_read"]
                * 100
            )
            print(f"Duplicate Percentage: {duplicate_percent:.2f}%")

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
