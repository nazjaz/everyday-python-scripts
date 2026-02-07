"""File Metadata Exporter - Generate detailed file list with metadata.

This module provides functionality to generate a detailed file list with
metadata including size, dates, permissions, and checksums, exported to CSV format.
"""

import csv
import hashlib
import logging
import logging.handlers
import os
import platform
import stat
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FileMetadataExporter:
    """Exports file metadata to CSV format."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize FileMetadataExporter with configuration.

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
        if os.getenv("SOURCE_DIRECTORY"):
            config["source"]["directory"] = os.getenv("SOURCE_DIRECTORY")
        if os.getenv("OUTPUT_FILE"):
            config["export"]["output_file"] = os.getenv("OUTPUT_FILE")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/metadata_exporter.log")

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

    def _calculate_checksum(self, file_path: Path, algorithm: str = "md5") -> Optional[str]:
        """Calculate file checksum.

        Args:
            file_path: Path to file.
            algorithm: Hash algorithm (md5, sha1, sha256).

        Returns:
            Checksum string or None if error.
        """
        if algorithm not in ["md5", "sha1", "sha256"]:
            logger.warning(f"Unsupported algorithm: {algorithm}, using md5")
            algorithm = "md5"

        try:
            hash_obj = hashlib.new(algorithm)

            # Read file in chunks to handle large files
            chunk_size = self.config.get("checksum", {}).get("chunk_size", 8192)
            with open(file_path, "rb") as f:
                while chunk := f.read(chunk_size):
                    hash_obj.update(chunk)

            return hash_obj.hexdigest()

        except (IOError, PermissionError) as e:
            logger.warning(f"Error calculating checksum for {file_path}: {e}")
            return None

    def _get_file_permissions(self, file_path: Path) -> Dict[str, any]:
        """Get file permissions information.

        Args:
            file_path: Path to file.

        Returns:
            Dictionary with permission information.
        """
        try:
            file_stat = file_path.stat()
            mode = file_stat.st_mode

            permissions = {
                "mode_octal": oct(stat.S_IMODE(mode)),
                "mode_readable": stat.filemode(mode),
                "is_readable": os.access(file_path, os.R_OK),
                "is_writable": os.access(file_path, os.W_OK),
                "is_executable": os.access(file_path, os.X_OK),
            }

            # Platform-specific permissions
            if platform.system() != "Windows":
                permissions["owner_read"] = bool(mode & stat.S_IRUSR)
                permissions["owner_write"] = bool(mode & stat.S_IWUSR)
                permissions["owner_execute"] = bool(mode & stat.S_IXUSR)
                permissions["group_read"] = bool(mode & stat.S_IRGRP)
                permissions["group_write"] = bool(mode & stat.S_IWGRP)
                permissions["group_execute"] = bool(mode & stat.S_IXGRP)
                permissions["other_read"] = bool(mode & stat.S_IROTH)
                permissions["other_write"] = bool(mode & stat.S_IWOTH)
                permissions["other_execute"] = bool(mode & stat.S_IXOTH)

            return permissions

        except (OSError, PermissionError) as e:
            logger.warning(f"Error getting permissions for {file_path}: {e}")
            return {}

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

    def extract_metadata(self, file_path: Path) -> Optional[Dict[str, any]]:
        """Extract metadata from a file.

        Args:
            file_path: Path to file.

        Returns:
            Dictionary with file metadata or None if error.
        """
        if not file_path.exists() or not file_path.is_file():
            return None

        if self._should_skip_path(file_path):
            return None

        if not self._should_include_extension(file_path):
            return None

        try:
            file_stat = file_path.stat()

            metadata = {
                "path": str(file_path),
                "name": file_path.name,
                "directory": str(file_path.parent),
                "extension": file_path.suffix.lower() or "no extension",
                "size_bytes": file_stat.st_size,
                "size_kb": round(file_stat.st_size / 1024, 2),
                "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(file_stat.st_atime).isoformat(),
            }

            # Add permissions
            permissions = self._get_file_permissions(file_path)
            metadata.update(permissions)

            # Add checksums if enabled
            checksum_config = self.config.get("checksum", {})
            if checksum_config.get("enabled", True):
                algorithms = checksum_config.get("algorithms", ["md5"])
                for algorithm in algorithms:
                    checksum = self._calculate_checksum(file_path, algorithm)
                    if checksum:
                        metadata[f"checksum_{algorithm}"] = checksum

            # Add additional metadata
            metadata_config = self.config.get("metadata", {})
            if metadata_config.get("include_owner", False):
                try:
                    import pwd
                    owner = pwd.getpwuid(file_stat.st_uid).pw_name
                    metadata["owner"] = owner
                except (ImportError, KeyError):
                    pass

            if metadata_config.get("include_group", False):
                try:
                    import grp
                    group = grp.getgrgid(file_stat.st_gid).gr_name
                    metadata["group"] = group
                except (ImportError, KeyError):
                    pass

            if metadata_config.get("include_inode", False):
                metadata["inode"] = file_stat.st_ino

            if metadata_config.get("include_device", False):
                metadata["device"] = file_stat.st_dev

            return metadata

        except (OSError, PermissionError) as e:
            logger.warning(f"Error extracting metadata from {file_path}: {e}")
            self.stats["errors"] += 1
            return None

    def scan_directory(self, directory: Optional[str] = None) -> List[Dict[str, any]]:
        """Scan directory and extract metadata from all files.

        Args:
            directory: Directory to scan (default: from config).

        Returns:
            List of file metadata dictionaries.

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

        logger.info(f"Starting directory scan: {scan_dir}")

        scan_path = Path(scan_dir).resolve()
        recursive = source_config.get("recursive", True)

        metadata_list = []

        try:
            if recursive:
                file_paths = list(scan_path.rglob("*"))
            else:
                file_paths = list(scan_path.iterdir())

            for file_path in file_paths:
                if not file_path.is_file():
                    continue

                self.stats["files_scanned"] += 1

                metadata = self.extract_metadata(file_path)
                if metadata:
                    metadata_list.append(metadata)
                    self.stats["files_processed"] += 1
                else:
                    self.stats["files_skipped"] += 1

        except Exception as e:
            logger.error(f"Error during directory scan: {e}")
            self.stats["errors"] += 1
            raise

        logger.info("Directory scan completed")
        logger.info(f"Statistics: {self.stats}")

        return metadata_list

    def export_to_csv(
        self, metadata_list: List[Dict[str, any]], output_file: Optional[str] = None
    ) -> str:
        """Export metadata to CSV file.

        Args:
            metadata_list: List of file metadata dictionaries.
            output_file: Optional path to output CSV file.

        Returns:
            Path to output CSV file.

        Raises:
            ValueError: If metadata list is empty.
        """
        if not metadata_list:
            raise ValueError("No metadata to export")

        export_config = self.config.get("export", {})
        csv_file = output_file or export_config.get("output_file", "data/file_metadata.csv")

        csv_path = Path(csv_file)
        if not csv_path.is_absolute():
            project_root = Path(__file__).parent.parent
            csv_path = project_root / csv_file

        csv_path.parent.mkdir(parents=True, exist_ok=True)

        # Get all unique keys from metadata dictionaries
        fieldnames = set()
        for metadata in metadata_list:
            fieldnames.update(metadata.keys())

        # Sort fieldnames for consistent column order
        fieldnames = sorted(fieldnames)

        # Reorder to put important fields first
        priority_fields = [
            "path",
            "name",
            "directory",
            "extension",
            "size_bytes",
            "size_kb",
            "size_mb",
            "created",
            "modified",
            "accessed",
        ]

        ordered_fieldnames = []
        for field in priority_fields:
            if field in fieldnames:
                ordered_fieldnames.append(field)
                fieldnames.remove(field)

        ordered_fieldnames.extend(sorted(fieldnames))

        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=ordered_fieldnames)
                writer.writeheader()

                for metadata in metadata_list:
                    # Ensure all fields are present (fill missing with empty string)
                    row = {field: metadata.get(field, "") for field in ordered_fieldnames}
                    writer.writerow(row)

            logger.info(f"Exported {len(metadata_list)} records to CSV: {csv_path}")
            return str(csv_path)

        except IOError as e:
            logger.error(f"Error writing CSV file: {e}")
            raise

    def print_summary(self) -> None:
        """Print summary to console."""
        print("\n" + "=" * 80)
        print("FILE METADATA EXPORTER SUMMARY")
        print("=" * 80)
        print(f"Files scanned: {self.stats['files_scanned']}")
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files skipped: {self.stats['files_skipped']}")
        if self.stats['errors'] > 0:
            print(f"Errors: {self.stats['errors']}")
        print("=" * 80 + "\n")


def main() -> int:
    """Main entry point for file metadata exporter."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate detailed file list with metadata exported to CSV"
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
        "--output",
        help="Output CSV file path (overrides config)",
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Don't print summary to console",
    )

    args = parser.parse_args()

    try:
        exporter = FileMetadataExporter(config_path=args.config)

        # Scan directory
        metadata_list = exporter.scan_directory(directory=args.directory)

        if not metadata_list:
            logger.warning("No files found to export")
            print("No files found to export.")
            return 1

        # Export to CSV
        csv_path = exporter.export_to_csv(metadata_list, output_file=args.output)
        print(f"\nMetadata exported to: {csv_path}")
        print(f"Total records: {len(metadata_list)}")

        # Print summary
        if not args.no_summary:
            exporter.print_summary()

        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration or directory error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Export error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
