"""Checksum Generator - Generate MD5 or SHA256 checksums for files.

This module provides functionality to generate MD5 or SHA256 checksums for
all files in a directory, saving results to a CSV file with file paths and
hash values. Includes comprehensive logging and error handling.
"""

import csv
import hashlib
import logging
import logging.handlers
import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ChecksumGenerator:
    """Generates checksums for files and saves to CSV."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize ChecksumGenerator with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_directories()
        self.checksums: List[Dict[str, str]] = []
        self.stats = {
            "files_scanned": 0,
            "checksums_generated": 0,
            "files_skipped": 0,
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
        if os.getenv("SCAN_DIRECTORY"):
            config["scan_directory"] = os.getenv("SCAN_DIRECTORY")
        if os.getenv("OUTPUT_FILE"):
            config["output_file"] = os.getenv("OUTPUT_FILE")
        if os.getenv("HASH_ALGORITHM"):
            config["hash_algorithm"] = os.getenv("HASH_ALGORITHM")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/checksum_generator.log")

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
        """Set up scan directory and output file."""
        self.scan_dir = Path(
            os.path.expanduser(self.config["scan_directory"])
        )

        if not self.scan_dir.exists():
            raise FileNotFoundError(
                f"Scan directory does not exist: {self.scan_dir}"
            )

        output_file = self.config.get("output_file", "checksums.csv")
        self.output_path = Path(output_file)

        if not self.output_path.is_absolute():
            project_root = Path(__file__).parent.parent
            self.output_path = project_root / output_file

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Scan directory: {self.scan_dir}")
        logger.info(f"Output file: {self.output_path}")

    def _should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed.

        Args:
            file_path: Path to file.

        Returns:
            True if file should be processed, False otherwise.
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

        # Check minimum file size
        min_size = self.config.get("min_file_size_bytes", 0)
        try:
            if file_path.stat().st_size < min_size:
                return False
        except OSError:
            return False

        return True

    def _calculate_checksum(self, file_path: Path) -> Optional[str]:
        """Calculate checksum for a file.

        Args:
            file_path: Path to file.

        Returns:
            Hexadecimal checksum string, or None if error.
        """
        algorithm = self.config.get("hash_algorithm", "sha256").lower()

        # Validate algorithm
        if algorithm not in ("md5", "sha256"):
            logger.error(f"Unsupported hash algorithm: {algorithm}")
            return None

        try:
            hash_obj = hashlib.new(algorithm)

            with open(file_path, "rb") as f:
                # Read in chunks to handle large files efficiently
                chunk_size = self.config.get("chunk_size", 8192)
                while chunk := f.read(chunk_size):
                    hash_obj.update(chunk)

            checksum = hash_obj.hexdigest()
            logger.debug(f"Calculated {algorithm.upper()} for {file_path.name}")
            return checksum

        except (IOError, OSError) as e:
            error_msg = f"Error calculating checksum for {file_path}: {e}"
            logger.error(error_msg)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            return None

    def _process_file(self, file_path: Path) -> bool:
        """Process a single file and generate checksum.

        Args:
            file_path: Path to file to process.

        Returns:
            True if successful, False otherwise.
        """
        self.stats["files_scanned"] += 1

        if not self._should_process_file(file_path):
            logger.debug(f"Skipping excluded file: {file_path.name}")
            self.stats["files_skipped"] += 1
            return False

        checksum = self._calculate_checksum(file_path)
        if checksum is None:
            self.stats["files_skipped"] += 1
            return False

        # Get relative path for cleaner output
        try:
            relative_path = file_path.relative_to(self.scan_dir)
        except ValueError:
            relative_path = file_path

        checksum_entry = {
            "file_path": str(relative_path),
            "absolute_path": str(file_path),
            "checksum": checksum,
            "algorithm": self.config.get("hash_algorithm", "sha256").upper(),
            "file_size": file_path.stat().st_size,
        }

        self.checksums.append(checksum_entry)
        self.stats["checksums_generated"] += 1

        return True

    def generate_checksums(self) -> Dict[str, any]:
        """Generate checksums for all files in scan directory.

        Returns:
            Dictionary with statistics about the operation.
        """
        logger.info("Starting checksum generation")
        logger.info(f"Algorithm: {self.config.get('hash_algorithm', 'sha256').upper()}")
        logger.info(f"Recursive: {self.config['operations']['recursive']}")

        # Find all files
        files_to_process = []
        if self.config["operations"]["recursive"]:
            for file_path in self.scan_dir.rglob("*"):
                if file_path.is_file():
                    files_to_process.append(file_path)
        else:
            for file_path in self.scan_dir.iterdir():
                if file_path.is_file():
                    files_to_process.append(file_path)

        logger.info(f"Found {len(files_to_process)} files to process")

        # Process each file
        for file_path in files_to_process:
            self._process_file(file_path)

        logger.info("Checksum generation completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats

    def save_to_csv(self, output_file: Optional[str] = None) -> Path:
        """Save checksums to CSV file.

        Args:
            output_file: Optional path to output file.

        Returns:
            Path to saved CSV file.
        """
        if not self.checksums:
            logger.warning("No checksums to save")
            return self.output_path

        if output_file:
            csv_path = Path(output_file)
        else:
            csv_path = self.output_path

        if not csv_path.is_absolute():
            project_root = Path(__file__).parent.parent
            csv_path = project_root / csv_path

        csv_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            fieldnames = ["file_path", "absolute_path", "checksum", "algorithm", "file_size"]

            with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.checksums)

            logger.info(f"Saved {len(self.checksums)} checksums to {csv_path}")
            return csv_path

        except Exception as e:
            error_msg = f"Error saving CSV file: {e}"
            logger.error(error_msg)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            return csv_path


def main() -> int:
    """Main entry point for checksum generator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate MD5 or SHA256 checksums for files and save to CSV"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output CSV file path (overrides config)",
    )
    parser.add_argument(
        "--algorithm",
        choices=["md5", "sha256"],
        help="Hash algorithm to use (overrides config)",
    )

    args = parser.parse_args()

    try:
        generator = ChecksumGenerator(config_path=args.config)

        if args.output:
            generator.output_path = Path(args.output)
            generator.output_path.parent.mkdir(parents=True, exist_ok=True)

        if args.algorithm:
            generator.config["hash_algorithm"] = args.algorithm

        # Generate checksums
        stats = generator.generate_checksums()

        # Save to CSV
        csv_path = generator.save_to_csv()

        # Print summary
        print("\n" + "=" * 60)
        print("Checksum Generation Summary")
        print("=" * 60)
        print(f"Files Scanned: {stats['files_scanned']}")
        print(f"Checksums Generated: {stats['checksums_generated']}")
        print(f"Files Skipped: {stats['files_skipped']}")
        print(f"Output File: {csv_path}")
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
