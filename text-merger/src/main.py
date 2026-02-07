"""Text Merger - Merge multiple text files into a single file.

This module provides functionality to merge multiple text files into a
single file with separators, preserving original filenames as headers and
maintaining order. Includes comprehensive logging and error handling.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class TextMerger:
    """Merges multiple text files into a single file with separators."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize TextMerger with configuration.

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
            "files_scanned": 0,
            "files_merged": 0,
            "files_skipped": 0,
            "errors": 0,
            "errors_list": [],
            "total_lines": 0,
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
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}"
            )

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Override with environment variables if present
        if os.getenv("SOURCE_DIRECTORY"):
            config["source_directory"] = os.getenv("SOURCE_DIRECTORY")
        if os.getenv("OUTPUT_FILE"):
            config["output_file"] = os.getenv("OUTPUT_FILE")
        if os.getenv("DRY_RUN"):
            config["operations"]["dry_run"] = (
                os.getenv("DRY_RUN").lower() == "true"
            )

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/text_merger.log")

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
        """Set up source directory and output file."""
        self.source_dir = Path(
            os.path.expanduser(self.config["source_directory"])
        )

        if not self.source_dir.exists():
            raise FileNotFoundError(
                f"Source directory does not exist: {self.source_dir}"
            )

        output_file = self.config.get("output_file", "merged.txt")
        self.output_path = Path(output_file)

        if not self.output_path.is_absolute():
            project_root = Path(__file__).parent.parent
            self.output_path = project_root / output_file

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Source directory: {self.source_dir}")
        logger.info(f"Output file: {self.output_path}")

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file is a text file based on extension.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file is a text file, False otherwise.
        """
        text_extensions = self.config.get("text_extensions", [".txt", ".md", ".log"])
        return file_path.suffix.lower() in [
            ext.lower() for ext in text_extensions
        ]

    def _should_include_file(self, file_path: Path) -> bool:
        """Check if file should be included in merge.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file should be included, False otherwise.
        """
        exclusions = self.config.get("exclusions", {})
        file_name = file_path.name

        # Check excluded patterns
        excluded_patterns = exclusions.get("patterns", [])
        for pattern in excluded_patterns:
            if pattern in file_name:
                return False

        # Check excluded extensions
        excluded_extensions = exclusions.get("extensions", [])
        if file_path.suffix.lower() in [
            ext.lower() for ext in excluded_extensions
        ]:
            return False

        return True

    def _get_file_list(self) -> List[Path]:
        """Get list of text files to merge.

        Returns:
            List of file paths, sorted according to configuration.
        """
        text_files = []

        if self.config["operations"]["recursive"]:
            for file_path in self.source_dir.rglob("*"):
                if (
                    file_path.is_file()
                    and self._is_text_file(file_path)
                    and self._should_include_file(file_path)
                ):
                    text_files.append(file_path)
        else:
            for file_path in self.source_dir.iterdir():
                if (
                    file_path.is_file()
                    and self._is_text_file(file_path)
                    and self._should_include_file(file_path)
                ):
                    text_files.append(file_path)

        # Sort files
        sort_order = self.config.get("sort_order", "alphabetical")
        if sort_order == "alphabetical":
            text_files.sort(key=lambda x: x.name.lower())
        elif sort_order == "date_modified":
            text_files.sort(key=lambda x: x.stat().st_mtime)
        elif sort_order == "date_created":
            text_files.sort(key=lambda x: x.stat().st_ctime)
        elif sort_order == "size":
            text_files.sort(key=lambda x: x.stat().st_size)

        logger.info(f"Found {len(text_files)} text files to merge")
        return text_files

    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """Read content from a text file.

        Args:
            file_path: Path to file to read.

        Returns:
            File content as string, or None if read failed.
        """
        try:
            encoding = self.config.get("input_encoding", "utf-8")
            with open(file_path, "r", encoding=encoding, errors="replace") as f:
                content = f.read()
            self.stats["total_lines"] += content.count("\n")
            return content
        except Exception as e:
            error_msg = f"Error reading {file_path}: {e}"
            logger.error(error_msg)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            return None

    def _format_header(self, filename: str) -> str:
        """Format filename as header.

        Args:
            filename: Name of file.

        Returns:
            Formatted header string.
        """
        header_format = self.config.get("header_format", "=== {filename} ===")
        return header_format.format(filename=filename)

    def _format_separator(self) -> str:
        """Get separator string between files.

        Returns:
            Separator string.
        """
        separator = self.config.get("separator", "\n" + "=" * 80 + "\n")
        return separator

    def _merge_files(self, file_list: List[Path]) -> str:
        """Merge multiple files into a single string.

        Args:
            file_list: List of file paths to merge.

        Returns:
            Merged content as string.
        """
        merged_content = []
        header_format = self.config.get("header_format", "=== {filename} ===")
        separator = self._format_separator()

        # Add header if configured
        if self.config.get("include_header", True):
            header_text = self.config.get("header_text", "")
            if header_text:
                # Replace {date} placeholder with current date
                header_text = header_text.replace(
                    "{date}", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                merged_content.append(header_text)
                merged_content.append("\n")

        for i, file_path in enumerate(file_list):
            self.stats["files_scanned"] += 1

            content = self._read_file_content(file_path)
            if content is None:
                self.stats["files_skipped"] += 1
                continue

            # Add file header
            filename = file_path.name
            header = self._format_header(filename)
            merged_content.append(header)
            merged_content.append("\n")

            # Add file content
            merged_content.append(content)

            # Add separator (except after last file)
            if i < len(file_list) - 1:
                merged_content.append(separator)

            self.stats["files_merged"] += 1
            logger.debug(f"Merged: {filename}")

        return "".join(merged_content)

    def merge_text_files(self) -> Dict[str, any]:
        """Merge all text files from source directory.

        Returns:
            Dictionary with statistics about the operation.
        """
        logger.info("Starting text file merge")
        logger.info(f"Dry run mode: {self.config['operations']['dry_run']}")

        # Get list of files to merge
        file_list = self._get_file_list()

        if not file_list:
            logger.warning("No text files found to merge")
            return self.stats

        # Merge files
        merged_content = self._merge_files(file_list)

        # Save merged content
        if not self.config["operations"]["dry_run"]:
            try:
                output_encoding = self.config.get("output_encoding", "utf-8")
                with open(self.output_path, "w", encoding=output_encoding) as f:
                    f.write(merged_content)

                logger.info(
                    f"Merged {len(file_list)} files into {self.output_path} "
                    f"({len(merged_content)} characters)"
                )
            except Exception as e:
                error_msg = f"Error writing output file: {e}"
                logger.error(error_msg)
                self.stats["errors"] += 1
                self.stats["errors_list"].append(error_msg)
        else:
            logger.info(
                f"[DRY RUN] Would merge {len(file_list)} files into "
                f"{self.output_path}"
            )

        logger.info("Text file merge completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats


def main() -> int:
    """Main entry point for text merger."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Merge multiple text files into a single file with "
        "separators and headers"
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
        help="Preview changes without creating merged file",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path (overrides config)",
    )

    args = parser.parse_args()

    try:
        merger = TextMerger(config_path=args.config)

        if args.dry_run:
            merger.config["operations"]["dry_run"] = True

        if args.output:
            merger.output_path = Path(args.output)
            merger.output_path.parent.mkdir(parents=True, exist_ok=True)

        stats = merger.merge_text_files()

        # Print summary
        print("\n" + "=" * 60)
        print("Text File Merge Summary")
        print("=" * 60)
        print(f"Files Scanned: {stats['files_scanned']}")
        print(f"Files Merged: {stats['files_merged']}")
        print(f"Files Skipped: {stats['files_skipped']}")
        print(f"Total Lines: {stats['total_lines']}")
        print(f"Output File: {merger.output_path}")
        print(f"Errors: {stats['errors']}")

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
