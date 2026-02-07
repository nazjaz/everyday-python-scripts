"""Duplicate File Finder - CLI tool for finding duplicate files by hash comparison.

This module provides a command-line tool for finding duplicate files by comparing
file hashes, grouping duplicates, and generating reports with recommendations
for which files to keep or delete.
"""

import argparse
import csv
import hashlib
import json
import logging
import logging.handlers
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DuplicateFinder:
    """Finds duplicate files by comparing file hashes."""

    def __init__(self, config: Dict) -> None:
        """Initialize DuplicateFinder.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.hash_algorithm = config.get("hash_algorithm", "md5").lower()
        self.min_file_size = config.get("min_file_size", 0)
        self.max_file_size = config.get("max_file_size", 0)
        self.chunk_size = config.get("chunk_size", 8192)
        self.exclude_patterns = [
            re.compile(pattern) for pattern in config.get("exclude_patterns", [])
        ]
        self.exclude_directories = [
            re.compile(pattern) for pattern in config.get("exclude_directories", [])
        ]
        self.recommendations_config = config.get("recommendations", {})

        # Validate hash algorithm
        if self.hash_algorithm not in ("md5", "sha1", "sha256"):
            logger.warning(f"Invalid hash algorithm: {self.hash_algorithm}, using md5")
            self.hash_algorithm = "md5"

    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from scanning.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file should be excluded, False otherwise.
        """
        filename = file_path.name

        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if pattern.search(filename):
                return True

        # Check file size limits
        try:
            file_size = file_path.stat().st_size
            if self.min_file_size > 0 and file_size < self.min_file_size:
                return True
            if self.max_file_size > 0 and file_size > self.max_file_size:
                return True
        except (OSError, IOError):
            return True

        return False

    def should_exclude_directory(self, dir_path: Path) -> bool:
        """Check if directory should be excluded from scanning.

        Args:
            dir_path: Path to directory to check.

        Returns:
            True if directory should be excluded, False otherwise.
        """
        dirname = dir_path.name

        for pattern in self.exclude_directories:
            if pattern.search(dirname):
                return True

        return False

    def calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """Calculate hash of a file.

        Args:
            file_path: Path to file.

        Returns:
            Hexadecimal hash string or None if error.
        """
        try:
            hash_obj = hashlib.new(self.hash_algorithm)

            with open(file_path, "rb") as f:
                while chunk := f.read(self.chunk_size):
                    hash_obj.update(chunk)

            return hash_obj.hexdigest()

        except (IOError, OSError) as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return None

    def find_files(self, directories: List[Path], recursive: bool = True) -> List[Path]:
        """Find all files in directories.

        Args:
            directories: List of directories to scan.
            recursive: Whether to scan recursively.

        Returns:
            List of file paths.
        """
        files = []

        for directory in directories:
            directory = directory.resolve()

            if not directory.exists() or not directory.is_dir():
                logger.warning(f"Directory does not exist or is not a directory: {directory}")
                continue

            if self.should_exclude_directory(directory):
                logger.debug(f"Excluding directory: {directory}")
                continue

            if recursive:
                file_paths = directory.rglob("*")
            else:
                file_paths = directory.glob("*")

            for file_path in file_paths:
                if file_path.is_file() and not self.should_exclude_file(file_path):
                    files.append(file_path)

        return files

    def find_duplicates(
        self, directories: List[Path], recursive: bool = True
    ) -> Dict[str, List[Dict]]:
        """Find duplicate files by comparing hashes.

        Args:
            directories: List of directories to scan.
            recursive: Whether to scan recursively.

        Returns:
            Dictionary mapping hash to list of file info dictionaries.
        """
        logger.info("Finding files...")
        files = self.find_files(directories, recursive)
        logger.info(f"Found {len(files)} file(s) to check")

        hash_to_files: Dict[str, List[Dict]] = defaultdict(list)

        for i, file_path in enumerate(files, 1):
            if i % 100 == 0:
                logger.info(f"Processing file {i}/{len(files)}...")

            file_hash = self.calculate_file_hash(file_path)

            if file_hash:
                try:
                    stat = file_path.stat()
                    file_info = {
                        "path": str(file_path),
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "hash": file_hash,
                    }
                    hash_to_files[file_hash].append(file_info)
                except (OSError, IOError) as e:
                    logger.error(f"Error getting file info for {file_path}: {e}")

        # Filter to only duplicates (groups with more than one file)
        duplicates = {
            hash_val: files
            for hash_val, files in hash_to_files.items()
            if len(files) > 1
        }

        logger.info(f"Found {len(duplicates)} duplicate group(s)")
        total_duplicate_files = sum(len(files) for files in duplicates.values())
        logger.info(f"Total duplicate files: {total_duplicate_files}")

        return duplicates

    def generate_recommendations(
        self, duplicates: Dict[str, List[Dict]]
    ) -> Dict[str, Dict]:
        """Generate recommendations for duplicate files.

        Args:
            duplicates: Dictionary mapping hash to list of duplicate files.

        Returns:
            Dictionary with recommendations for each duplicate group.
        """
        recommendations = {}

        keep_directories = self.recommendations_config.get("keep_directories", [])
        keep_oldest = self.recommendations_config.get("keep_oldest", True)
        keep_shortest_path = self.recommendations_config.get("keep_shortest_path", False)

        for file_hash, files in duplicates.items():
            # Sort files by various criteria
            files_sorted = sorted(files, key=lambda f: (
                # Priority: files in keep_directories first
                -sum(1 for dir_name in keep_directories if dir_name in f["path"]),
                # Then by modification time (oldest first if keep_oldest)
                datetime.fromisoformat(f["modified"]).timestamp() if keep_oldest else -datetime.fromisoformat(f["modified"]).timestamp(),
                # Then by path length (shortest first if keep_shortest_path)
                len(f["path"]) if keep_shortest_path else -len(f["path"]),
            ))

            keep_file = files_sorted[0]
            delete_files = files_sorted[1:]

            recommendations[file_hash] = {
                "keep": keep_file,
                "delete": delete_files,
                "total_size": keep_file["size"] * len(delete_files),
                "space_savings": f"{keep_file['size'] * len(delete_files) / (1024 * 1024):.2f} MB",
            }

        return recommendations

    def generate_report(
        self,
        duplicates: Dict[str, List[Dict]],
        recommendations: Dict[str, Dict],
        output_path: Path,
        report_format: str = "json",
    ) -> None:
        """Generate duplicate file report.

        Args:
            duplicates: Dictionary mapping hash to list of duplicate files.
            recommendations: Recommendations dictionary.
            output_path: Path where report will be saved.
            report_format: Report format (json, txt, csv).
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if report_format.lower() == "json":
            self._generate_json_report(duplicates, recommendations, output_path)
        elif report_format.lower() == "txt":
            self._generate_txt_report(duplicates, recommendations, output_path)
        elif report_format.lower() == "csv":
            self._generate_csv_report(duplicates, recommendations, output_path)
        else:
            raise ValueError(f"Unsupported report format: {report_format}")

        logger.info(f"Report generated: {output_path}")

    def _generate_json_report(
        self,
        duplicates: Dict[str, List[Dict]],
        recommendations: Dict[str, Dict],
        output_path: Path,
    ) -> None:
        """Generate JSON report."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_duplicate_groups": len(duplicates),
            "total_duplicate_files": sum(len(files) for files in duplicates.values()),
            "total_space_wasted": sum(
                rec["total_size"] for rec in recommendations.values()
            ),
            "duplicates": duplicates,
            "recommendations": recommendations,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def _generate_txt_report(
        self,
        duplicates: Dict[str, List[Dict]],
        recommendations: Dict[str, Dict],
        output_path: Path,
    ) -> None:
        """Generate text report."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("DUPLICATE FILE REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Total duplicate groups: {len(duplicates)}\n")
            f.write(
                f"Total duplicate files: {sum(len(files) for files in duplicates.values())}\n"
            )
            f.write(
                f"Total space wasted: {sum(rec['total_size'] for rec in recommendations.values()) / (1024 * 1024):.2f} MB\n"
            )
            f.write("\n" + "=" * 80 + "\n\n")

            for i, (file_hash, files) in enumerate(duplicates.items(), 1):
                rec = recommendations[file_hash]
                f.write(f"Group {i} (Hash: {file_hash[:16]}...)\n")
                f.write(f"  File size: {files[0]['size'] / 1024:.2f} KB\n")
                f.write(f"  Duplicates: {len(files)}\n")
                f.write(f"  Space wasted: {rec['space_savings']}\n\n")

                f.write("  KEEP:\n")
                f.write(f"    {rec['keep']['path']}\n")
                f.write(f"    Modified: {rec['keep']['modified']}\n\n")

                f.write("  DELETE:\n")
                for delete_file in rec["delete"]:
                    f.write(f"    {delete_file['path']}\n")
                    f.write(f"    Modified: {delete_file['modified']}\n")

                f.write("\n" + "-" * 80 + "\n\n")

    def _generate_csv_report(
        self,
        duplicates: Dict[str, List[Dict]],
        recommendations: Dict[str, Dict],
        output_path: Path,
    ) -> None:
        """Generate CSV report."""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Hash",
                    "Action",
                    "Path",
                    "Size (bytes)",
                    "Modified",
                    "Group Size",
                    "Space Wasted (bytes)",
                ]
            )

            for file_hash, files in duplicates.items():
                rec = recommendations[file_hash]

                # Write keep file
                writer.writerow(
                    [
                        file_hash[:16] + "...",
                        "KEEP",
                        rec["keep"]["path"],
                        rec["keep"]["size"],
                        rec["keep"]["modified"],
                        len(files),
                        rec["total_size"],
                    ]
                )

                # Write delete files
                for delete_file in rec["delete"]:
                    writer.writerow(
                        [
                            file_hash[:16] + "...",
                            "DELETE",
                            delete_file["path"],
                            delete_file["size"],
                            delete_file["modified"],
                            len(files),
                            rec["total_size"],
                        ]
                    )


def setup_logging(config: Dict) -> None:
    """Configure logging based on config file.

    Args:
        config: Configuration dictionary with logging settings.
    """
    log_config = config.get("logging", {})
    log_level = os.getenv("LOG_LEVEL", log_config.get("level", "INFO"))
    log_file = log_config.get("file", "logs/duplicate_finder.log")
    max_bytes = log_config.get("max_bytes", 10485760)
    backup_count = log_config.get("backup_count", 5)
    log_format = log_config.get(
        "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    handler.setFormatter(logging.Formatter(log_format))

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.addHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)


def load_config(config_path: Optional[Path] = None) -> Dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. Defaults to config.yaml in project root.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file does not exist.
        yaml.YAMLError: If config file is invalid.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Find duplicate files by comparing file hashes"
    )
    parser.add_argument(
        "-d",
        "--directories",
        nargs="+",
        type=Path,
        help="Directories to scan (overrides config)",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Scan directories recursively (default: true)",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Do not scan directories recursively",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output report file path (overrides config)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "txt", "csv"],
        help="Report format (overrides config)",
    )
    parser.add_argument(
        "--hash",
        choices=["md5", "sha1", "sha256"],
        help="Hash algorithm (overrides config)",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to configuration file",
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config)
        setup_logging(config)

        # Override config with command-line arguments
        if args.directories:
            config["scan_directories"] = [str(d) for d in args.directories]
        if args.no_recursive:
            recursive = False
        else:
            recursive = args.recursive if args.recursive else True
        if args.output:
            config["report_file"] = str(args.output)
        if args.format:
            config["report_format"] = args.format
        if args.hash:
            config["hash_algorithm"] = args.hash

        # Get directories to scan
        directories = [Path(d).resolve() for d in config.get("scan_directories", [])]

        if not directories:
            logger.error("No directories specified for scanning")
            print("Error: No directories specified for scanning")
            sys.exit(1)

        print(f"Scanning directories: {', '.join(str(d) for d in directories)}")
        print(f"Recursive: {recursive}")
        print(f"Hash algorithm: {config.get('hash_algorithm', 'md5')}")
        print()

        # Find duplicates
        finder = DuplicateFinder(config)
        duplicates = finder.find_duplicates(directories, recursive)

        if not duplicates:
            print("No duplicate files found!")
            return

        # Generate recommendations
        print("Generating recommendations...")
        recommendations = finder.generate_recommendations(duplicates)

        # Generate report
        report_path = Path(config.get("report_file", "data/duplicate_report.json"))
        report_format = config.get("report_format", "json")
        finder.generate_report(duplicates, recommendations, report_path, report_format)

        # Print summary
        total_groups = len(duplicates)
        total_files = sum(len(files) for files in duplicates.values())
        total_space = sum(rec["total_size"] for rec in recommendations.values())

        print()
        print("=" * 60)
        print("DUPLICATE FILE SUMMARY")
        print("=" * 60)
        print(f"Duplicate groups found: {total_groups}")
        print(f"Total duplicate files: {total_files}")
        print(f"Space that could be freed: {total_space / (1024 * 1024):.2f} MB")
        print(f"Report saved to: {report_path}")
        print("=" * 60)

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Invalid configuration file: {e}")
        print(f"Error: Invalid configuration file: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Scan interrupted by user")
        print("\nScan interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
