"""Text File Processor - Process text files by cleaning whitespace and encoding.

This module provides functionality to process text files by removing extra
whitespace, normalizing line endings, and standardizing encoding to UTF-8.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class TextFileProcessor:
    """Processes text files by cleaning whitespace and standardizing encoding."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize TextFileProcessor with configuration.

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
            "files_skipped": 0,
            "files_failed": 0,
            "bytes_processed": 0,
            "bytes_saved": 0,
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
        if os.getenv("INPUT_DIRECTORY"):
            config["input"]["directory"] = os.getenv("INPUT_DIRECTORY")
        if os.getenv("OUTPUT_DIRECTORY"):
            config["output"]["directory"] = os.getenv("OUTPUT_DIRECTORY")
        if os.getenv("BACKUP_ENABLED"):
            config["backup"]["enabled"] = os.getenv("BACKUP_ENABLED").lower() == "true"

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/text_processor.log")

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

    def _detect_encoding(self, file_path: Path) -> Tuple[str, bytes]:
        """Detect file encoding and read content.

        Args:
            file_path: Path to file.

        Returns:
            Tuple of (encoding, file_content_bytes).

        Raises:
            UnicodeDecodeError: If encoding cannot be determined.
        """
        encodings_to_try = self.config.get("processing", {}).get(
            "encoding_detection_order", ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
        )

        with open(file_path, "rb") as f:
            content = f.read()

        for encoding in encodings_to_try:
            try:
                # Try to decode to verify encoding
                content.decode(encoding)
                logger.debug(f"Detected encoding: {encoding} for {file_path}")
                return encoding, content
            except (UnicodeDecodeError, LookupError):
                continue

        # If all encodings fail, try with error handling
        logger.warning(f"Could not detect encoding for {file_path}, using utf-8 with errors='replace'")
        return "utf-8", content

    def _normalize_line_endings(self, text: str) -> str:
        """Normalize line endings to specified format.

        Args:
            text: Text content.

        Returns:
            Text with normalized line endings.
        """
        line_ending = self.config.get("processing", {}).get("line_ending", "unix")
        
        # First, normalize all line endings to \n
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        
        # Then convert to desired format
        if line_ending == "windows":
            text = text.replace("\n", "\r\n")
        elif line_ending == "mac":
            text = text.replace("\n", "\r")
        # else: unix (keep \n)

        return text

    def _remove_extra_whitespace(self, text: str) -> str:
        """Remove extra whitespace from text.

        Args:
            text: Text content.

        Returns:
            Text with extra whitespace removed.
        """
        processing_config = self.config.get("processing", {})
        
        # Remove trailing whitespace from each line
        if processing_config.get("remove_trailing_whitespace", True):
            lines = text.splitlines()
            lines = [line.rstrip() for line in lines]
            text = "\n".join(lines)
        
        # Remove leading whitespace from each line (optional)
        if processing_config.get("remove_leading_whitespace", False):
            lines = text.splitlines()
            lines = [line.lstrip() for line in lines]
            text = "\n".join(lines)
        
        # Normalize multiple spaces to single space (within lines)
        if processing_config.get("normalize_spaces", True):
            lines = text.splitlines()
            normalized_lines = []
            for line in lines:
                # Replace multiple spaces with single space, but preserve indentation
                normalized_line = " ".join(line.split())
                # If original line had leading spaces, preserve them
                if line and line[0] == " ":
                    leading_spaces = len(line) - len(line.lstrip())
                    normalized_line = " " * leading_spaces + normalized_line.lstrip()
                normalized_lines.append(normalized_line)
            text = "\n".join(normalized_lines)
        
        # Remove empty lines (optional)
        if processing_config.get("remove_empty_lines", False):
            lines = text.splitlines()
            lines = [line for line in lines if line.strip()]
            text = "\n".join(lines)
        
        # Remove trailing newlines at end of file (optional)
        if processing_config.get("remove_trailing_newlines", False):
            text = text.rstrip("\n\r")

        return text

    def _should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed.

        Args:
            file_path: Path to file.

        Returns:
            True if file should be processed, False otherwise.
        """
        include_config = self.config.get("include", {})
        extensions = include_config.get("extensions", [])

        # If extensions list is empty, process all text files
        if not extensions:
            # Default to common text file extensions
            text_extensions = [".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".xml", ".yaml", ".yml"]
            return file_path.suffix.lower() in text_extensions

        return file_path.suffix.lower() in [ext.lower() for ext in extensions]

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

        path_str = str(file_path)

        # Check skip patterns
        for pattern in patterns:
            if pattern in path_str:
                return True

        # Check skip directories
        for skip_dir in directories:
            if skip_dir in path_str:
                return True

        return False

    def _backup_file(self, file_path: Path) -> Optional[Path]:
        """Create backup of file before processing.

        Args:
            file_path: Path to file.

        Returns:
            Path to backup file or None if backup failed.
        """
        backup_config = self.config.get("backup", {})
        if not backup_config.get("enabled", True):
            return None

        backup_dir = backup_config.get("directory", "backups")
        backup_path = Path(backup_dir)
        if not backup_path.is_absolute():
            project_root = Path(__file__).parent.parent
            backup_path = project_root / backup_dir

        backup_path.mkdir(parents=True, exist_ok=True)

        # Create backup path preserving directory structure
        relative_path = file_path.relative_to(file_path.anchor)
        backup_file = backup_path / relative_path
        backup_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            import shutil
            shutil.copy2(file_path, backup_file)
            logger.debug(f"Backup created: {backup_file}")
            return backup_file
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            return None

    def process_file(self, file_path: Path) -> bool:
        """Process a single text file.

        Args:
            file_path: Path to file to process.

        Returns:
            True if processing succeeded, False otherwise.
        """
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            self.stats["files_failed"] += 1
            return False

        if not file_path.is_file():
            logger.warning(f"Path is not a file: {file_path}")
            self.stats["files_skipped"] += 1
            return False

        if not self._should_process_file(file_path):
            logger.debug(f"Skipping file (not in include list): {file_path}")
            self.stats["files_skipped"] += 1
            return False

        if self._should_skip_path(file_path):
            logger.debug(f"Skipping file (matches skip pattern): {file_path}")
            self.stats["files_skipped"] += 1
            return False

        try:
            # Detect encoding and read file
            encoding, original_content = self._detect_encoding(file_path)
            original_size = len(original_content)

            # Decode content
            try:
                text = original_content.decode(encoding)
            except UnicodeDecodeError:
                logger.warning(f"Decoding error for {file_path}, using errors='replace'")
                text = original_content.decode(encoding, errors="replace")

            # Process text
            processed_text = self._remove_extra_whitespace(text)
            processed_text = self._normalize_line_endings(processed_text)

            # Encode to UTF-8
            processed_content = processed_text.encode("utf-8")
            new_size = len(processed_content)

            # Create backup if enabled
            if self.config.get("backup", {}).get("enabled", True):
                self._backup_file(file_path)

            # Write processed content
            output_config = self.config.get("output", {})
            if output_config.get("in_place", True):
                output_path = file_path
            else:
                output_dir = output_config.get("directory", "processed")
                output_path = Path(output_dir)
                if not output_path.is_absolute():
                    project_root = Path(__file__).parent.parent
                    output_path = project_root / output_dir

                output_path.mkdir(parents=True, exist_ok=True)
                output_path = output_path / file_path.name

            with open(output_path, "wb") as f:
                f.write(processed_content)

            self.stats["files_processed"] += 1
            self.stats["bytes_processed"] += original_size
            self.stats["bytes_saved"] += (original_size - new_size)

            logger.info(
                f"Processed: {file_path} "
                f"({original_size} -> {new_size} bytes, "
                f"encoding: {encoding} -> UTF-8)"
            )

            return True

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}", exc_info=True)
            self.stats["files_failed"] += 1
            return False

    def process_directory(self, directory: Optional[str] = None) -> Dict[str, int]:
        """Process all text files in a directory.

        Args:
            directory: Directory to process (default: from config).

        Returns:
            Dictionary with processing statistics.
        """
        input_config = self.config.get("input", {})
        search_dir = directory or input_config.get("directory", ".")

        if not os.path.exists(search_dir):
            raise FileNotFoundError(f"Directory not found: {search_dir}")

        if not os.path.isdir(search_dir):
            raise NotADirectoryError(f"Path is not a directory: {search_dir}")

        logger.info(f"Starting directory processing: {search_dir}")

        search_path = Path(search_dir).resolve()
        recursive = input_config.get("recursive", True)

        files_to_process = []

        if recursive:
            for file_path in search_path.rglob("*"):
                if file_path.is_file():
                    files_to_process.append(file_path)
        else:
            for file_path in search_path.iterdir():
                if file_path.is_file():
                    files_to_process.append(file_path)

        logger.info(f"Found {len(files_to_process)} files to process")

        for file_path in files_to_process:
            self.process_file(file_path)

        logger.info("Directory processing completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats

    def print_summary(self) -> None:
        """Print processing summary to console."""
        print("\n" + "=" * 80)
        print("TEXT FILE PROCESSOR SUMMARY")
        print("=" * 80)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files skipped: {self.stats['files_skipped']}")
        print(f"Files failed: {self.stats['files_failed']}")
        print(f"Bytes processed: {self.stats['bytes_processed']:,}")
        print(f"Bytes saved: {self.stats['bytes_saved']:,}")
        print("=" * 80 + "\n")


def main() -> int:
    """Main entry point for text file processor."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Process text files by cleaning whitespace and encoding"
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
        help="Directory to process (overrides config)",
    )
    parser.add_argument(
        "-f",
        "--file",
        help="Single file to process",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Disable backup creation",
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Don't print summary to console",
    )

    args = parser.parse_args()

    try:
        processor = TextFileProcessor(config_path=args.config)

        # Override backup setting
        if args.no_backup:
            processor.config["backup"]["enabled"] = False

        # Process single file or directory
        if args.file:
            file_path = Path(args.file)
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return 1

            success = processor.process_file(file_path)
            if not success:
                return 1
        else:
            processor.process_directory(directory=args.directory)

        # Print summary
        if not args.no_summary:
            processor.print_summary()

        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration or file error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
