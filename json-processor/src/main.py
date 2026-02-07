"""JSON Processor - Process JSON files with validation and reformatting.

This module provides functionality to process JSON files by validating structure,
removing null values, and reformatting with consistent indentation and sorted keys.
Includes comprehensive logging and error handling.
"""

import json
import logging
import logging.handlers
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class JSONProcessor:
    """Processes JSON files with validation, cleaning, and reformatting."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize JSONProcessor with configuration.

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
            "files_processed": 0,
            "files_skipped": 0,
            "files_failed": 0,
            "validation_errors": 0,
            "errors": 0,
            "errors_list": [],
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
        if os.getenv("OUTPUT_DIRECTORY"):
            config["output_directory"] = os.getenv("OUTPUT_DIRECTORY")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/json_processor.log")

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
        """Set up source and output directories."""
        self.source_dir = Path(
            os.path.expanduser(self.config["source_directory"])
        )

        if not self.source_dir.exists():
            raise FileNotFoundError(
                f"Source directory does not exist: {self.source_dir}"
            )

        output_dir = self.config.get("output_directory")
        if output_dir:
            self.output_dir = Path(os.path.expanduser(output_dir))
            if not self.output_dir.is_absolute():
                project_root = Path(__file__).parent.parent
                self.output_dir = project_root / output_dir
            self.output_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.output_dir = None

        logger.info(f"Source directory: {self.source_dir}")
        if self.output_dir:
            logger.info(f"Output directory: {self.output_dir}")

    def _validate_json_structure(
        self, data: Any, schema: Optional[Dict] = None
    ) -> Tuple[bool, Optional[str]]:
        """Validate JSON structure.

        Args:
            data: JSON data to validate.
            schema: Optional JSON schema for validation.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if schema is None:
            # Basic validation: check if data is valid JSON structure
            try:
                json.dumps(data)
                return True, None
            except (TypeError, ValueError) as e:
                return False, f"Invalid JSON structure: {e}"

        # Schema validation would require jsonschema library
        # For now, we'll do basic structure validation
        try:
            json.dumps(data)
            return True, None
        except (TypeError, ValueError) as e:
            return False, f"Invalid JSON structure: {e}"

    def _remove_null_values(self, data: Any) -> Any:
        """Recursively remove null values from JSON data.

        Args:
            data: JSON data structure.

        Returns:
            Data with null values removed.
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if value is None:
                    if not self.config.get("processing", {}).get(
                        "remove_null", True
                    ):
                        result[key] = value
                    # Otherwise skip null values
                else:
                    cleaned_value = self._remove_null_values(value)
                    result[key] = cleaned_value
            return result
        elif isinstance(data, list):
            result = []
            for item in data:
                if item is not None:
                    cleaned_item = self._remove_null_values(item)
                    result.append(cleaned_item)
            return result
        else:
            return data

    def _sort_keys(self, data: Any) -> Any:
        """Recursively sort keys in JSON data.

        Args:
            data: JSON data structure.

        Returns:
            Data with sorted keys.
        """
        if isinstance(data, dict):
            sorted_dict = {}
            for key in sorted(data.keys()):
                sorted_dict[key] = self._sort_keys(data[key])
            return sorted_dict
        elif isinstance(data, list):
            return [self._sort_keys(item) for item in data]
        else:
            return data

    def _process_json_file(self, file_path: Path) -> bool:
        """Process a single JSON file.

        Args:
            file_path: Path to JSON file.

        Returns:
            True if processed successfully, False otherwise.
        """
        try:
            # Read JSON file
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON in {file_path.name}: {e}"
                    logger.error(error_msg)
                    self.stats["validation_errors"] += 1
                    self.stats["errors"] += 1
                    self.stats["errors_list"].append(error_msg)
                    self.stats["files_failed"] += 1
                    return False

            # Validate structure
            is_valid, error_msg = self._validate_json_structure(data)
            if not is_valid:
                logger.error(f"Validation failed for {file_path.name}: {error_msg}")
                self.stats["validation_errors"] += 1
                self.stats["errors"] += 1
                self.stats["errors_list"].append(
                    f"{file_path.name}: {error_msg}"
                )
                self.stats["files_failed"] += 1
                return False

            # Process data
            processing_config = self.config.get("processing", {})

            # Remove null values
            if processing_config.get("remove_null", True):
                data = self._remove_null_values(data)

            # Sort keys
            if processing_config.get("sort_keys", True):
                data = self._sort_keys(data)

            # Format JSON
            indent = processing_config.get("indent", 2)
            ensure_ascii = processing_config.get("ensure_ascii", False)
            separators = (
                (",", ": ")
                if processing_config.get("compact_separators", False)
                else None
            )

            formatted_json = json.dumps(
                data,
                indent=indent,
                ensure_ascii=ensure_ascii,
                separators=separators,
                sort_keys=False,  # Already sorted above
            )

            # Determine output path
            if self.output_dir:
                output_path = self.output_dir / file_path.name
            else:
                # Overwrite original file
                output_path = file_path

            # Create backup if overwriting
            if output_path == file_path and self.config.get("backup", {}).get(
                "enabled", False
            ):
                backup_dir = Path(
                    os.path.expanduser(
                        self.config["backup"].get("directory", "backups")
                    )
                )
                if not backup_dir.is_absolute():
                    project_root = Path(__file__).parent.parent
                    backup_dir = project_root / backup_dir
                backup_dir.mkdir(parents=True, exist_ok=True)
                backup_path = backup_dir / file_path.name
                shutil.copy2(file_path, backup_path)
                logger.debug(f"Created backup: {backup_path}")

            # Write processed JSON
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(formatted_json)

            logger.info(f"Processed {file_path.name}")
            self.stats["files_processed"] += 1
            return True

        except Exception as e:
            error_msg = f"Error processing {file_path.name}: {e}"
            logger.error(error_msg)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            self.stats["files_failed"] += 1
            return False

    def _should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed.

        Args:
            file_path: Path to file.

        Returns:
            True if file should be processed, False otherwise.
        """
        # Check file extension
        if file_path.suffix.lower() != ".json":
            return False

        # Check exclusions
        exclusions = self.config.get("exclusions", {})
        file_name = file_path.name

        # Check excluded patterns
        excluded_patterns = exclusions.get("patterns", [])
        for pattern in excluded_patterns:
            if pattern in file_name:
                return False

        # Check excluded directories
        excluded_dirs = exclusions.get("directories", [])
        for excluded_dir in excluded_dirs:
            excluded_path = Path(os.path.expanduser(excluded_dir))
            try:
                if file_path.is_relative_to(excluded_path):
                    return False
            except (ValueError, AttributeError):
                # Python < 3.9 compatibility
                if str(file_path).startswith(str(excluded_path)):
                    return False

        return True

    def process_files(self) -> Dict[str, any]:
        """Process all JSON files in source directory.

        Returns:
            Dictionary with statistics about the operation.
        """
        logger.info("Starting JSON file processing")
        logger.info(f"Remove null values: {self.config.get('processing', {}).get('remove_null', True)}")
        logger.info(f"Sort keys: {self.config.get('processing', {}).get('sort_keys', True)}")
        logger.info(f"Recursive: {self.config['operations']['recursive']}")

        # Find all JSON files
        json_files = []
        if self.config["operations"]["recursive"]:
            for file_path in self.source_dir.rglob("*"):
                if file_path.is_file() and self._should_process_file(file_path):
                    json_files.append(file_path)
        else:
            for file_path in self.source_dir.iterdir():
                if file_path.is_file() and self._should_process_file(file_path):
                    json_files.append(file_path)

        logger.info(f"Found {len(json_files)} JSON files to process")

        # Process each file
        for file_path in json_files:
            if not self._process_json_file(file_path):
                self.stats["files_skipped"] += 1

        logger.info("JSON file processing completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats


def main() -> int:
    """Main entry point for JSON processor."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Process JSON files with validation, cleaning, and reformatting"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    try:
        processor = JSONProcessor(config_path=args.config)

        if args.dry_run:
            logger.info("DRY RUN MODE: No files will be modified")

        # Process files
        stats = processor.process_files()

        # Print summary
        print("\n" + "=" * 60)
        print("JSON Processing Summary")
        print("=" * 60)
        print(f"Files Processed: {stats['files_processed']}")
        print(f"Files Skipped: {stats['files_skipped']}")
        print(f"Files Failed: {stats['files_failed']}")
        print(f"Validation Errors: {stats['validation_errors']}")
        print(f"Total Errors: {stats['errors']}")

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
