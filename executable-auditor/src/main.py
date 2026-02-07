"""Executable File Auditor - CLI tool for finding and auditing executable files.

This module provides a command-line tool for finding all executable files in a
directory tree, categorizing them by type, and generating a security audit report
with file hashes, permissions, and security flags.
"""

import argparse
import csv
import hashlib
import json
import logging
import logging.handlers
import os
import re
import stat
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ExecutableAuditor:
    """Finds and audits executable files in directory trees."""

    def __init__(self, config: Dict) -> None:
        """Initialize ExecutableAuditor.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.detection_config = config.get("detection", {})
        self.categories = config.get("categories", {})
        self.security_config = config.get("security_audit", {})
        self.exclude_patterns = [
            re.compile(pattern) for pattern in config.get("exclude_patterns", [])
        ]
        self.exclude_directories = [
            re.compile(pattern) for pattern in config.get("exclude_directories", [])
        ]

        # Build extension to category mapping
        self.extension_to_category = {}
        for category, category_info in self.categories.items():
            for ext in category_info.get("extensions", []):
                self.extension_to_category[ext.lower()] = category

    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from scanning.

        Args:
            file_path: Path to file.

        Returns:
            True if file should be excluded.
        """
        filename = file_path.name

        for pattern in self.exclude_patterns:
            if pattern.search(filename):
                return True

        return False

    def should_exclude_directory(self, dir_path: Path) -> bool:
        """Check if directory should be excluded from scanning.

        Args:
            dir_path: Path to directory.

        Returns:
            True if directory should be excluded.
        """
        dirname = str(dir_path)

        for pattern in self.exclude_directories:
            if pattern.search(dirname):
                return True

        return False

    def is_executable_by_permission(self, file_path: Path) -> bool:
        """Check if file is executable by permission.

        Args:
            file_path: Path to file.

        Returns:
            True if file has execute permission.
        """
        try:
            file_stat = file_path.stat()
            mode = file_stat.st_mode

            # Check if any execute bit is set
            return bool(
                (mode & stat.S_IXUSR)
                or (mode & stat.S_IXGRP)
                or (mode & stat.S_IXOTH)
            )

        except (OSError, IOError):
            return False

    def is_executable_by_extension(self, file_path: Path) -> bool:
        """Check if file is executable by extension.

        Args:
            file_path: Path to file.

        Returns:
            True if file extension indicates executable.
        """
        ext = file_path.suffix.lower().lstrip(".")
        return ext in self.extension_to_category

    def has_shebang(self, file_path: Path) -> bool:
        """Check if file starts with shebang.

        Args:
            file_path: Path to file.

        Returns:
            True if file starts with shebang.
        """
        try:
            with open(file_path, "rb") as f:
                first_bytes = f.read(2)
                return first_bytes == b"#!"

        except (IOError, OSError):
            return False

    def is_binary_file(self, file_path: Path) -> bool:
        """Check if file is a binary file.

        Args:
            file_path: Path to file.

        Returns:
            True if file appears to be binary.
        """
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(512)
                # Check for null bytes (common in binaries)
                if b"\x00" in chunk:
                    return True
                # Check for common binary magic bytes
                if chunk.startswith((b"\x7fELF", b"MZ", b"\xfe\xed\xfa")):
                    return True
                return False

        except (IOError, OSError):
            return False

    def get_file_category(self, file_path: Path) -> str:
        """Get category for executable file.

        Args:
            file_path: Path to file.

        Returns:
            Category name.
        """
        ext = file_path.suffix.lower().lstrip(".")

        # Check extension first
        if ext in self.extension_to_category:
            return self.extension_to_category[ext]

        # Check shebang for scripts
        if self.detection_config.get("check_shebang", True):
            if self.has_shebang(file_path):
                return "scripts"

        # Check if binary
        if self.detection_config.get("check_magic_bytes", True):
            if self.is_binary_file(file_path):
                return "binaries"

        return "unknown"

    def calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """Calculate hash of a file.

        Args:
            file_path: Path to file.

        Returns:
            Hexadecimal hash string or None if error.
        """
        if not self.security_config.get("calculate_hashes", True):
            return None

        try:
            algorithm = self.security_config.get("hash_algorithm", "sha256").lower()
            hash_obj = hashlib.new(algorithm)

            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    hash_obj.update(chunk)

            return hash_obj.hexdigest()

        except (IOError, OSError) as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return None

    def get_file_permissions(self, file_path: Path) -> Tuple[int, str]:
        """Get file permissions.

        Args:
            file_path: Path to file.

        Returns:
            Tuple of (octal_permissions, string_representation).
        """
        try:
            file_stat = file_path.stat()
            mode = file_stat.st_mode

            octal_perms = stat.filemode(mode)
            octal_value = oct(stat.S_IMODE(mode))[2:]

            return int(octal_value), octal_perms

        except (OSError, IOError):
            return 0, "----------"

    def check_security_flags(self, file_path: Path, file_info: Dict) -> List[str]:
        """Check file for security issues and return flags.

        Args:
            file_path: Path to file.
            file_info: File information dictionary.

        Returns:
            List of security flags.
        """
        flags = []

        if not self.security_config.get("flag_suspicious_permissions", True):
            return flags

        octal_perms, _ = self.get_file_permissions(file_path)
        perm_str = str(octal_perms)

        suspicious_perms = self.security_config.get("suspicious_permissions", [])
        if perm_str in suspicious_perms:
            flags.append(f"Suspicious permissions: {perm_str}")

        # Check file size
        if self.security_config.get("check_file_size", True):
            max_size = self.security_config.get("max_normal_size", 104857600)
            if file_info.get("size", 0) > max_size:
                flags.append(f"Unusually large file: {file_info.get('size', 0) / (1024*1024):.2f} MB")

        # Check modification time
        if self.security_config.get("flag_recent_modifications", True):
            recent_days = self.security_config.get("recent_days", 7)
            modified_time = file_info.get("modified_time")
            if modified_time:
                try:
                    mod_date = datetime.fromisoformat(modified_time)
                    days_ago = (datetime.now() - mod_date).days
                    if days_ago <= recent_days:
                        flags.append(f"Recently modified: {days_ago} days ago")
                except (ValueError, TypeError):
                    pass

        # Check ownership
        if self.security_config.get("check_ownership", True):
            try:
                file_stat = file_path.stat()
                if self.security_config.get("flag_root_owned", False):
                    if file_stat.st_uid == 0:
                        flags.append("Owned by root")
            except (OSError, IOError):
                pass

        return flags

    def find_executables(
        self, directories: List[Path], recursive: bool = True
    ) -> Dict[str, List[Dict]]:
        """Find all executable files in directories.

        Args:
            directories: List of directories to scan.
            recursive: Whether to scan recursively.

        Returns:
            Dictionary mapping category to list of file info dictionaries.
        """
        executables = defaultdict(list)

        for directory in directories:
            directory = directory.resolve()

            if not directory.exists() or not directory.is_dir():
                logger.warning(f"Directory does not exist: {directory}")
                continue

            if self.should_exclude_directory(directory):
                logger.debug(f"Excluding directory: {directory}")
                continue

            if recursive:
                file_paths = directory.rglob("*")
            else:
                file_paths = directory.glob("*")

            for file_path in file_paths:
                if not file_path.is_file():
                    continue

                if self.should_exclude_file(file_path):
                    continue

                # Check if executable
                is_executable = False

                if self.detection_config.get("check_permissions", True):
                    if self.is_executable_by_permission(file_path):
                        is_executable = True

                if not is_executable and self.detection_config.get("check_extensions", True):
                    if self.is_executable_by_extension(file_path):
                        is_executable = True

                if not is_executable:
                    continue

                # Get file information
                try:
                    file_stat = file_path.stat()
                    category = self.get_file_category(file_path)

                    file_info = {
                        "path": str(file_path),
                        "name": file_path.name,
                        "size": file_stat.st_size,
                        "modified_time": datetime.fromtimestamp(
                            file_stat.st_mtime
                        ).isoformat(),
                        "created_time": datetime.fromtimestamp(
                            file_stat.st_ctime
                        ).isoformat(),
                        "category": category,
                    }

                    # Get permissions
                    octal_perms, perm_str = self.get_file_permissions(file_path)
                    file_info["permissions_octal"] = octal_perms
                    file_info["permissions_string"] = perm_str

                    # Calculate hash
                    file_hash = self.calculate_file_hash(file_path)
                    if file_hash:
                        file_info["hash"] = file_hash
                        file_info["hash_algorithm"] = self.security_config.get(
                            "hash_algorithm", "sha256"
                        )

                    # Check security flags
                    security_flags = self.check_security_flags(file_path, file_info)
                    if security_flags:
                        file_info["security_flags"] = security_flags

                    executables[category].append(file_info)

                except (OSError, IOError) as e:
                    logger.error(f"Error processing {file_path}: {e}")

        return dict(executables)

    def generate_report(
        self,
        executables: Dict[str, List[Dict]],
        output_path: Path,
        report_format: str = "json",
    ) -> None:
        """Generate security audit report.

        Args:
            executables: Dictionary mapping category to list of executables.
            output_path: Path where report will be saved.
            report_format: Report format (json, txt, csv).
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if report_format.lower() == "json":
            self._generate_json_report(executables, output_path)
        elif report_format.lower() == "txt":
            self._generate_txt_report(executables, output_path)
        elif report_format.lower() == "csv":
            self._generate_csv_report(executables, output_path)
        else:
            raise ValueError(f"Unsupported report format: {report_format}")

        logger.info(f"Report generated: {output_path}")

    def _generate_json_report(
        self, executables: Dict[str, List[Dict]], output_path: Path
    ) -> None:
        """Generate JSON report."""
        total_count = sum(len(files) for files in executables.values())

        # Count security flags
        total_flags = 0
        for category_files in executables.values():
            for file_info in category_files:
                if "security_flags" in file_info:
                    total_flags += len(file_info["security_flags"])

        report = {
            "generated_at": datetime.now().isoformat(),
            "total_executables": total_count,
            "total_security_flags": total_flags,
            "categories": {},
        }

        for category, files in executables.items():
            report["categories"][category] = {
                "count": len(files),
                "files": files,
            }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def _generate_txt_report(
        self, executables: Dict[str, List[Dict]], output_path: Path
    ) -> None:
        """Generate text report."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("EXECUTABLE FILE SECURITY AUDIT REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")

            total_count = sum(len(files) for files in executables.values())
            f.write(f"Total Executable Files Found: {total_count}\n\n")

            # Summary by category
            f.write("SUMMARY BY CATEGORY\n")
            f.write("-" * 80 + "\n")
            for category, files in sorted(executables.items()):
                f.write(f"{category.capitalize()}: {len(files)} file(s)\n")
            f.write("\n")

            # Detailed listing
            for category, files in sorted(executables.items()):
                f.write(f"{category.upper()} FILES\n")
                f.write("-" * 80 + "\n")

                for file_info in files:
                    f.write(f"Path: {file_info['path']}\n")
                    f.write(f"  Size: {file_info['size'] / 1024:.2f} KB\n")
                    f.write(f"  Permissions: {file_info.get('permissions_string', 'N/A')} ({file_info.get('permissions_octal', 'N/A')})\n")
                    f.write(f"  Modified: {file_info.get('modified_time', 'N/A')}\n")

                    if "hash" in file_info:
                        f.write(f"  Hash ({file_info.get('hash_algorithm', 'sha256')}): {file_info['hash']}\n")

                    if "security_flags" in file_info and file_info["security_flags"]:
                        f.write(f"  Security Flags:\n")
                        for flag in file_info["security_flags"]:
                            f.write(f"    - {flag}\n")

                    f.write("\n")

    def _generate_csv_report(
        self, executables: Dict[str, List[Dict]], output_path: Path
    ) -> None:
        """Generate CSV report."""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Category",
                    "Path",
                    "Name",
                    "Size (bytes)",
                    "Permissions (octal)",
                    "Permissions (string)",
                    "Modified Time",
                    "Hash",
                    "Security Flags",
                ]
            )

            for category, files in sorted(executables.items()):
                for file_info in files:
                    security_flags = "; ".join(
                        file_info.get("security_flags", [])
                    )
                    writer.writerow(
                        [
                            category,
                            file_info["path"],
                            file_info["name"],
                            file_info["size"],
                            file_info.get("permissions_octal", ""),
                            file_info.get("permissions_string", ""),
                            file_info.get("modified_time", ""),
                            file_info.get("hash", ""),
                            security_flags,
                        ]
                    )


def setup_logging(config: Dict) -> None:
    """Configure logging based on config file.

    Args:
        config: Configuration dictionary with logging settings.
    """
    log_config = config.get("logging", {})
    log_level = os.getenv("LOG_LEVEL", log_config.get("level", "INFO"))
    log_file = log_config.get("file", "logs/executable_auditor.log")
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
        description="Find and audit executable files in directory trees"
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

        # Get directories to scan
        directories = [Path(d).resolve() for d in config.get("scan_directories", [])]

        if not directories:
            logger.error("No directories specified for scanning")
            print("Error: No directories specified for scanning")
            sys.exit(1)

        print(f"Scanning directories: {', '.join(str(d) for d in directories)}")
        print(f"Recursive: {recursive}")
        print()

        # Find executables
        auditor = ExecutableAuditor(config)
        executables = auditor.find_executables(directories, recursive)

        if not executables:
            print("No executable files found!")
            return

        # Generate report
        report_path = Path(config.get("report_file", "data/executable_audit.json"))
        report_format = config.get("report_format", "json")
        auditor.generate_report(executables, report_path, report_format)

        # Print summary
        total_count = sum(len(files) for files in executables.values())
        total_flags = 0
        for category_files in executables.values():
            for file_info in category_files:
                if "security_flags" in file_info:
                    total_flags += len(file_info["security_flags"])

        print()
        print("=" * 60)
        print("EXECUTABLE FILE AUDIT SUMMARY")
        print("=" * 60)
        print(f"Total executables found: {total_count}")
        print(f"Total security flags: {total_flags}")
        print("\nBy category:")
        for category, files in sorted(executables.items()):
            print(f"  {category.capitalize()}: {len(files)}")
        print(f"\nReport saved to: {report_path}")
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
