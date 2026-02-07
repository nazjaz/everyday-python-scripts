"""System File Cleaner - Identify and remove system/hidden files.

This module provides functionality to identify system files and hidden files
based on naming patterns and attributes, with optional removal capabilities.
"""

import logging
import logging.handlers
import os
import platform
import stat
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class SystemFileCleaner:
    """Identifies and optionally removes system and hidden files."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize SystemFileCleaner with configuration.

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
            "system_files_found": 0,
            "hidden_files_found": 0,
            "files_removed": 0,
            "files_skipped": 0,
            "errors": 0,
        }
        self.system_name = platform.system().lower()

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
            config["removal"]["dry_run"] = os.getenv("DRY_RUN").lower() == "true"

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/system_file_cleaner.log")

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

    def _is_hidden_by_name(self, file_path: Path) -> bool:
        """Check if file is hidden by naming convention.

        Args:
            file_path: Path to file.

        Returns:
            True if file is hidden by name, False otherwise.
        """
        name = file_path.name

        # Check if name starts with dot (Unix/Linux/macOS)
        if name.startswith("."):
            return True

        # Check Windows hidden file patterns
        if self.system_name == "windows":
            # Check for common Windows hidden file patterns
            hidden_patterns = self.config.get("patterns", {}).get("windows_hidden", [])
            for pattern in hidden_patterns:
                if pattern in name.lower():
                    return True

        # Check custom patterns
        hidden_patterns = self.config.get("patterns", {}).get("hidden_name_patterns", [])
        for pattern in hidden_patterns:
            if pattern in name:
                return True

        return False

    def _is_hidden_by_attribute(self, file_path: Path) -> bool:
        """Check if file is hidden by file attributes.

        Args:
            file_path: Path to file.

        Returns:
            True if file is hidden by attribute, False otherwise.
        """
        if not file_path.exists():
            return False

        try:
            if self.system_name == "windows":
                # On Windows, check file attributes
                import win32file
                import win32con
                attrs = win32file.GetFileAttributes(str(file_path))
                return bool(attrs & win32con.FILE_ATTRIBUTE_HIDDEN)
            else:
                # On Unix/Linux/macOS, check if name starts with dot
                # This is handled by _is_hidden_by_name
                return False
        except ImportError:
            # win32file not available, fall back to name-based detection
            logger.debug("win32file not available, using name-based detection")
            return False
        except Exception as e:
            logger.warning(f"Error checking hidden attribute for {file_path}: {e}")
            return False

    def _is_system_file(self, file_path: Path) -> bool:
        """Check if file is a system file.

        Args:
            file_path: Path to file.

        Returns:
            True if file is a system file, False otherwise.
        """
        name = file_path.name.lower()
        name_patterns = self.config.get("patterns", {}).get("system_name_patterns", [])

        # Check system file name patterns
        for pattern in name_patterns:
            if pattern.lower() in name:
                return True

        # Platform-specific system file checks
        if self.system_name == "windows":
            windows_patterns = self.config.get("patterns", {}).get("windows_system", [])
            for pattern in windows_patterns:
                if pattern.lower() in name:
                    return True

            # Check Windows system directories
            windows_dirs = self.config.get("patterns", {}).get("windows_system_dirs", [])
            for sys_dir in windows_dirs:
                if sys_dir.lower() in str(file_path).lower():
                    return True

        elif self.system_name in ["linux", "darwin"]:
            unix_patterns = self.config.get("patterns", {}).get("unix_system", [])
            for pattern in unix_patterns:
                if pattern.lower() in name:
                    return True

        # Check file extension patterns
        extension = file_path.suffix.lower()
        system_extensions = self.config.get("patterns", {}).get("system_extensions", [])
        if extension in system_extensions:
            return True

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

    def _is_protected_file(self, file_path: Path) -> bool:
        """Check if file is protected and should not be removed.

        Args:
            file_path: Path to file.

        Returns:
            True if file is protected, False otherwise.
        """
        protected_config = self.config.get("protected", {})
        protected_patterns = protected_config.get("patterns", [])
        protected_paths = protected_config.get("paths", [])

        name = file_path.name
        path_str = str(file_path)

        # Check protected patterns
        for pattern in protected_patterns:
            if pattern in name or pattern in path_str:
                return True

        # Check protected paths
        if path_str in protected_paths or str(file_path.resolve()) in protected_paths:
            return True

        return False

    def identify_file(self, file_path: Path) -> Optional[Dict[str, any]]:
        """Identify if file is system or hidden file.

        Args:
            file_path: Path to file.

        Returns:
            Dictionary with file information or None if not system/hidden.
        """
        if not file_path.exists() or not file_path.is_file():
            return None

        if self._should_skip_path(file_path):
            return None

        file_info = {
            "path": str(file_path),
            "name": file_path.name,
            "size": file_path.stat().st_size,
            "is_system": False,
            "is_hidden": False,
            "hidden_reason": None,
            "system_reason": None,
        }

        # Check if hidden
        if self._is_hidden_by_name(file_path):
            file_info["is_hidden"] = True
            file_info["hidden_reason"] = "name_pattern"
        elif self._is_hidden_by_attribute(file_path):
            file_info["is_hidden"] = True
            file_info["hidden_reason"] = "file_attribute"

        # Check if system file
        if self._is_system_file(file_path):
            file_info["is_system"] = True
            file_info["system_reason"] = "pattern_match"

        # Return only if system or hidden
        if file_info["is_system"] or file_info["is_hidden"]:
            return file_info

        return None

    def remove_file(self, file_path: Path, dry_run: bool = False) -> bool:
        """Remove a file.

        Args:
            file_path: Path to file to remove.
            dry_run: If True, simulate removal without actually deleting.

        Returns:
            True if removal succeeded or was simulated, False otherwise.
        """
        if not file_path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return False

        if self._is_protected_file(file_path):
            logger.warning(f"File is protected, skipping: {file_path}")
            self.stats["files_skipped"] += 1
            return False

        try:
            if dry_run:
                logger.info(f"[DRY RUN] Would remove: {file_path}")
                return True

            file_path.unlink()
            logger.info(f"Removed file: {file_path}")
            return True

        except PermissionError as e:
            logger.error(f"Permission denied removing {file_path}: {e}")
            self.stats["errors"] += 1
            return False
        except Exception as e:
            logger.error(f"Error removing {file_path}: {e}")
            self.stats["errors"] += 1
            return False

    def scan_directory(
        self, directory: Optional[str] = None, remove_files: bool = False
    ) -> List[Dict[str, any]]:
        """Scan directory for system and hidden files.

        Args:
            directory: Directory to scan (default: from config).
            remove_files: If True, remove identified files.

        Returns:
            List of file information dictionaries.
        """
        scan_config = self.config.get("scan", {})
        scan_dir = directory or scan_config.get("directory", ".")

        if not os.path.exists(scan_dir):
            raise FileNotFoundError(f"Directory not found: {scan_dir}")

        if not os.path.isdir(scan_dir):
            raise NotADirectoryError(f"Path is not a directory: {scan_dir}")

        logger.info(f"Starting directory scan: {scan_dir}")

        scan_path = Path(scan_dir).resolve()
        recursive = scan_config.get("recursive", True)

        files_found = []
        removal_config = self.config.get("removal", {})
        dry_run = removal_config.get("dry_run", True)

        try:
            if recursive:
                file_paths = list(scan_path.rglob("*"))
            else:
                file_paths = list(scan_path.iterdir())

            for file_path in file_paths:
                if not file_path.is_file():
                    continue

                self.stats["files_scanned"] += 1

                file_info = self.identify_file(file_path)
                if file_info:
                    if file_info["is_system"]:
                        self.stats["system_files_found"] += 1
                    if file_info["is_hidden"]:
                        self.stats["hidden_files_found"] += 1

                    files_found.append(file_info)

                    # Remove file if requested
                    if remove_files:
                        if self.remove_file(file_path, dry_run=dry_run):
                            self.stats["files_removed"] += 1
                            file_info["removed"] = True
                        else:
                            file_info["removed"] = False

        except Exception as e:
            logger.error(f"Error during directory scan: {e}")
            self.stats["errors"] += 1
            raise

        logger.info("Directory scan completed")
        logger.info(f"Statistics: {self.stats}")

        return files_found

    def generate_report(
        self, files: List[Dict[str, any]], output_file: Optional[str] = None
    ) -> str:
        """Generate text report of found files.

        Args:
            files: List of file information dictionaries.
            output_file: Optional path to save report file.

        Returns:
            Report text.
        """
        from datetime import datetime

        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("SYSTEM AND HIDDEN FILE CLEANER REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Platform: {platform.system()}")
        report_lines.append("")

        # Statistics
        report_lines.append("STATISTICS")
        report_lines.append("-" * 80)
        report_lines.append(f"Files scanned: {self.stats['files_scanned']}")
        report_lines.append(f"System files found: {self.stats['system_files_found']}")
        report_lines.append(f"Hidden files found: {self.stats['hidden_files_found']}")
        report_lines.append(f"Files removed: {self.stats['files_removed']}")
        report_lines.append(f"Files skipped: {self.stats['files_skipped']}")
        report_lines.append(f"Errors: {self.stats['errors']}")
        report_lines.append("")

        # System files
        system_files = [f for f in files if f.get("is_system")]
        if system_files:
            report_lines.append("SYSTEM FILES")
            report_lines.append("-" * 80)
            for file_info in system_files:
                report_lines.append(f"Path: {file_info['path']}")
                report_lines.append(f"  Name: {file_info['name']}")
                report_lines.append(f"  Size: {file_info['size']:,} bytes")
                report_lines.append(f"  Reason: {file_info.get('system_reason', 'unknown')}")
                if file_info.get("removed"):
                    report_lines.append(f"  Status: REMOVED")
                report_lines.append("")

        # Hidden files
        hidden_files = [f for f in files if f.get("is_hidden")]
        if hidden_files:
            report_lines.append("HIDDEN FILES")
            report_lines.append("-" * 80)
            for file_info in hidden_files:
                report_lines.append(f"Path: {file_info['path']}")
                report_lines.append(f"  Name: {file_info['name']}")
                report_lines.append(f"  Size: {file_info['size']:,} bytes")
                report_lines.append(f"  Reason: {file_info.get('hidden_reason', 'unknown')}")
                if file_info.get("removed"):
                    report_lines.append(f"  Status: REMOVED")
                report_lines.append("")

        if not system_files and not hidden_files:
            report_lines.append("No system or hidden files found.")

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
        print("SYSTEM FILE CLEANER SUMMARY")
        print("=" * 80)
        print(f"Files scanned: {self.stats['files_scanned']}")
        print(f"System files found: {self.stats['system_files_found']}")
        print(f"Hidden files found: {self.stats['hidden_files_found']}")
        print(f"Files removed: {self.stats['files_removed']}")
        print(f"Files skipped: {self.stats['files_skipped']}")
        if self.stats['errors'] > 0:
            print(f"Errors: {self.stats['errors']}")
        print("=" * 80 + "\n")


def main() -> int:
    """Main entry point for system file cleaner."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Identify and remove system/hidden files"
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
        "--remove",
        action="store_true",
        help="Remove identified files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate removal without actually deleting",
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
        cleaner = SystemFileCleaner(config_path=args.config)

        # Override dry run setting
        if args.dry_run:
            cleaner.config["removal"]["dry_run"] = True

        # Scan directory
        files = cleaner.scan_directory(
            directory=args.directory, remove_files=args.remove
        )

        # Print summary
        if not args.no_summary:
            cleaner.print_summary()

        # Generate report
        if args.report:
            report = cleaner.generate_report(files, output_file=args.report)
            print(f"\nReport saved to: {args.report}")
        elif cleaner.config.get("report", {}).get("auto_save", False):
            report_file = cleaner.config.get("report", {}).get("output_file", "logs/system_file_report.txt")
            report = cleaner.generate_report(files, output_file=report_file)
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
