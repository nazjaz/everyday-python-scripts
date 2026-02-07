"""Log Compressor - Compress old log files using gzip.

This module provides functionality to compress old log files using gzip,
keeping original files for a specified retention period and organizing
compressed files by date.
"""

import gzip
import logging
import logging.handlers
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Set

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class LogCompressor:
    """Compresses log files with retention and date-based organization."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize LogCompressor with configuration.

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
            "files_compressed": 0,
            "files_skipped": 0,
            "files_failed": 0,
            "files_deleted": 0,
            "space_saved_mb": 0.0,
            "compressed_files": [],
            "deleted_files": [],
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
        if os.getenv("DRY_RUN"):
            config["safety"]["dry_run"] = os.getenv("DRY_RUN").lower() == "true"
        if os.getenv("TARGET_PATH"):
            config["targets"] = [{"path": os.getenv("TARGET_PATH"), "enabled": True, "recursive": True}]
        if os.getenv("MIN_AGE_DAYS"):
            config["compression"]["min_age_days"] = int(os.getenv("MIN_AGE_DAYS"))
        if os.getenv("KEEP_ORIGINAL_DAYS"):
            config["retention"]["keep_original_days"] = int(os.getenv("KEEP_ORIGINAL_DAYS"))

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/log_compressor.log")

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

    def _matches_pattern(self, file_path: Path) -> bool:
        """Check if file matches any configured pattern.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file matches a pattern, False otherwise.
        """
        patterns = self.config.get("file_patterns", [])
        file_name = file_path.name

        for pattern in patterns:
            # Simple glob-like pattern matching
            if pattern.startswith("*."):
                extension = pattern[1:]  # Remove *
                if file_name.endswith(extension):
                    return True
            elif pattern == file_name:
                return True

        return False

    def _should_compress(self, file_path: Path) -> bool:
        """Check if file should be compressed.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file should be compressed, False otherwise.
        """
        try:
            # Skip if already compressed
            if file_path.suffix == ".gz":
                return False

            # Check file size limit
            max_size_mb = self.config.get("safety", {}).get("max_file_size_mb", 0)
            if max_size_mb > 0:
                file_size_mb = file_path.stat().st_size / (1024 ** 2)
                if file_size_mb > max_size_mb:
                    logger.debug(f"Skipping large file: {file_path} ({file_size_mb:.2f} MB)")
                    return False

            # Check minimum age
            min_age_days = self.config.get("compression", {}).get("min_age_days", 7)
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            age_days = (datetime.now() - file_mtime).days

            if age_days < min_age_days:
                logger.debug(f"File too recent: {file_path} (age: {age_days} days)")
                return False

            # Skip recently modified files if configured
            if self.config.get("safety", {}).get("skip_recently_modified", True):
                if age_days < 1:
                    logger.debug(f"Skipping recently modified file: {file_path}")
                    return False

            return True

        except (OSError, ValueError) as e:
            logger.warning(f"Error checking file {file_path}: {e}")
            return False

    def _get_compressed_path(self, file_path: Path) -> Path:
        """Get path for compressed file with date-based organization.

        Args:
            file_path: Original file path.

        Returns:
            Path for compressed file.
        """
        organization = self.config.get("organization", {})
        if not organization.get("enabled", True):
            # Simple compression in same directory
            return file_path.with_suffix(file_path.suffix + ".gz")

        # Get file modification date
        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        organize_by = organization.get("organize_by", "date")

        # Build output directory structure
        output_dir = Path(organization.get("output_directory", "compressed_logs"))
        if not output_dir.is_absolute():
            project_root = Path(__file__).parent.parent
            output_dir = project_root / output_dir

        if organize_by == "year_month":
            date_str = file_mtime.strftime("%Y-%m")
            output_dir = output_dir / date_str
        elif organize_by == "year":
            date_str = file_mtime.strftime("%Y")
            output_dir = output_dir / date_str
        elif organize_by == "date":
            structure = organization.get("structure", "year/month")
            if structure == "year/month":
                year = file_mtime.strftime("%Y")
                month = file_mtime.strftime("%m")
                output_dir = output_dir / year / month
            elif structure == "year":
                year = file_mtime.strftime("%Y")
                output_dir = output_dir / year
            else:
                # Flat structure
                pass
        else:
            # No organization, use flat structure
            pass

        output_dir.mkdir(parents=True, exist_ok=True)

        # Compressed filename
        compressed_name = file_path.name + ".gz"
        return output_dir / compressed_name

    def _compress_file(self, file_path: Path) -> bool:
        """Compress a file using gzip.

        Args:
            file_path: Path to file to compress.

        Returns:
            True if successful, False otherwise.
        """
        dry_run = self.config.get("safety", {}).get("dry_run", False)
        compression_level = self.config.get("compression", {}).get("compression_level", 6)

        try:
            compressed_path = self._get_compressed_path(file_path)

            if dry_run:
                logger.info(f"[DRY RUN] Would compress: {file_path} -> {compressed_path}")
                return True

            # Get original size
            original_size = file_path.stat().st_size

            # Compress file
            with open(file_path, "rb") as f_in:
                with gzip.open(compressed_path, "wb", compresslevel=compression_level) as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Verify compression if configured
            if self.config.get("compression", {}).get("verify_compression", True):
                try:
                    with gzip.open(compressed_path, "rb") as f:
                        f.read()
                except Exception as e:
                    logger.error(f"Compression verification failed for {compressed_path}: {e}")
                    compressed_path.unlink()
                    return False

            compressed_size = compressed_path.stat().st_size
            space_saved = original_size - compressed_size
            self.stats["space_saved_mb"] += space_saved / (1024 ** 2)

            logger.info(
                f"Compressed: {file_path} -> {compressed_path} "
                f"({original_size / 1024:.2f} KB -> {compressed_size / 1024:.2f} KB)"
            )

            if self.config.get("logging", {}).get("log_compressions", True):
                self.stats["compressed_files"].append({
                    "original": str(file_path),
                    "compressed": str(compressed_path),
                    "original_size": original_size,
                    "compressed_size": compressed_size,
                    "space_saved": space_saved,
                })

            # Remove original if configured
            if self.config.get("compression", {}).get("remove_original_after", True):
                # Check retention period
                keep_days = self.config.get("retention", {}).get("keep_original_days", 30)
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                age_days = (datetime.now() - file_mtime).days

                if age_days >= keep_days:
                    file_path.unlink()
                    logger.info(f"Removed original file: {file_path}")
                    if self.config.get("logging", {}).get("log_deletions", True):
                        self.stats["deleted_files"].append(str(file_path))
                    self.stats["files_deleted"] += 1
                else:
                    logger.debug(
                        f"Keeping original for retention period: {file_path} "
                        f"(age: {age_days} days, keep: {keep_days} days)"
                    )

            return True

        except PermissionError:
            logger.error(f"Permission denied: {file_path}")
            self.stats["files_failed"] += 1
            return False
        except Exception as e:
            logger.error(f"Error compressing {file_path}: {e}", exc_info=True)
            self.stats["files_failed"] += 1
            return False

    def _find_log_files(self, root_path: Path, recursive: bool = True) -> List[Path]:
        """Find log files matching patterns.

        Args:
            root_path: Root directory to search.
            recursive: Whether to search recursively.

        Returns:
            List of matching file paths.
        """
        log_files: List[Path] = []

        try:
            if not root_path.exists() or not root_path.is_dir():
                return log_files

            if recursive:
                for file_path in root_path.rglob("*"):
                    if file_path.is_file() and self._matches_pattern(file_path):
                        log_files.append(file_path)
            else:
                for file_path in root_path.iterdir():
                    if file_path.is_file() and self._matches_pattern(file_path):
                        log_files.append(file_path)

        except PermissionError:
            logger.warning(f"Permission denied reading: {root_path}")
        except Exception as e:
            logger.error(f"Error finding files in {root_path}: {e}")

        return log_files

    def _cleanup_old_files(self) -> None:
        """Clean up old compressed files based on retention policy."""
        if not self.config.get("retention", {}).get("auto_cleanup", True):
            return

        keep_days = self.config.get("retention", {}).get("keep_compressed_days", 365)
        cutoff_date = datetime.now() - timedelta(days=keep_days)

        organization = self.config.get("organization", {})
        output_dir = Path(organization.get("output_directory", "compressed_logs"))
        if not output_dir.is_absolute():
            project_root = Path(__file__).parent.parent
            output_dir = project_root / output_dir

        if not output_dir.exists():
            return

        dry_run = self.config.get("safety", {}).get("dry_run", False)

        try:
            for compressed_file in output_dir.rglob("*.gz"):
                try:
                    file_mtime = datetime.fromtimestamp(compressed_file.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        if dry_run:
                            logger.info(f"[DRY RUN] Would delete old compressed file: {compressed_file}")
                        else:
                            compressed_file.unlink()
                            logger.info(f"Deleted old compressed file: {compressed_file}")
                            self.stats["files_deleted"] += 1
                            if self.config.get("logging", {}).get("log_deletions", True):
                                self.stats["deleted_files"].append(str(compressed_file))
                except Exception as e:
                    logger.warning(f"Error checking file {compressed_file}: {e}")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def compress_logs(self) -> dict:
        """Compress log files from configured targets.

        Returns:
            Dictionary with compression statistics.
        """
        logger.info("Starting log file compression")

        targets = self.config.get("targets", [])
        if not targets:
            logger.warning("No target directories configured")
            return self.stats

        dry_run = self.config.get("safety", {}).get("dry_run", False)
        if dry_run:
            logger.info("DRY RUN MODE: No files will be compressed")

        # Find and compress log files
        for target in targets:
            if not target.get("enabled", True):
                continue

            target_path = Path(target.get("path", "."))
            if not target_path.is_absolute():
                target_path = Path.cwd() / target_path

            recursive = target.get("recursive", True)
            logger.info(f"Scanning target: {target_path} (recursive: {recursive})")

            log_files = self._find_log_files(target_path, recursive)
            self.stats["files_scanned"] += len(log_files)

            for file_path in log_files:
                if self._should_compress(file_path):
                    if self._compress_file(file_path):
                        self.stats["files_compressed"] += 1
                    else:
                        self.stats["files_failed"] += 1
                else:
                    self.stats["files_skipped"] += 1

        # Cleanup old compressed files
        self._cleanup_old_files()

        # Generate report
        if self.config.get("reporting", {}).get("generate_report", True):
            self._generate_report()

        logger.info("Log file compression completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats

    def _generate_report(self) -> None:
        """Generate compression report."""
        report_config = self.config.get("reporting", {})
        report_file = report_config.get("report_file", "logs/compression_report.txt")

        report_path = Path(report_file)
        if not report_path.is_absolute():
            project_root = Path(__file__).parent.parent
            report_path = project_root / report_path

        report_path.parent.mkdir(parents=True, exist_ok=True)

        dry_run = self.config.get("safety", {}).get("dry_run", False)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("Log Compression Report\n")
            f.write("=" * 60 + "\n\n")

            if dry_run:
                f.write("MODE: DRY RUN (No files were actually compressed)\n\n")

            if report_config.get("include_statistics", True):
                f.write("Statistics\n")
                f.write("-" * 60 + "\n")
                f.write(f"Files Scanned: {self.stats['files_scanned']}\n")
                f.write(f"Files Compressed: {self.stats['files_compressed']}\n")
                f.write(f"Files Skipped: {self.stats['files_skipped']}\n")
                f.write(f"Files Failed: {self.stats['files_failed']}\n")
                f.write(f"Files Deleted: {self.stats['files_deleted']}\n")
                f.write(f"Space Saved: {self.stats['space_saved_mb']:.2f} MB\n")
                f.write("\n")

            if report_config.get("include_file_list", True) and self.stats["compressed_files"]:
                f.write("Compressed Files\n")
                f.write("-" * 60 + "\n")
                for file_info in self.stats["compressed_files"]:
                    f.write(f"Original: {file_info['original']}\n")
                    f.write(f"Compressed: {file_info['compressed']}\n")
                    f.write(
                        f"Size: {file_info['original_size'] / 1024:.2f} KB -> "
                        f"{file_info['compressed_size'] / 1024:.2f} KB "
                        f"(saved: {file_info['space_saved'] / 1024:.2f} KB)\n"
                    )
                    f.write("\n")

        logger.info(f"Report generated: {report_path}")


def main() -> int:
    """Main entry point for log compressor."""
    import argparse

    parser = argparse.ArgumentParser(description="Compress old log files using gzip")
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
        help="Dry run mode (don't actually compress)",
    )
    parser.add_argument(
        "-p",
        "--path",
        help="Target directory path to process",
    )

    args = parser.parse_args()

    try:
        compressor = LogCompressor(config_path=args.config)

        # Override config with command-line arguments
        if args.dry_run:
            compressor.config["safety"]["dry_run"] = True
        if args.path:
            compressor.config["targets"] = [{"path": args.path, "enabled": True, "recursive": True}]

        stats = compressor.compress_logs()

        print("\n" + "=" * 50)
        print("Compression Summary")
        print("=" * 50)
        print(f"Files Scanned: {stats['files_scanned']}")
        print(f"Files Compressed: {stats['files_compressed']}")
        print(f"Files Skipped: {stats['files_skipped']}")
        print(f"Files Failed: {stats['files_failed']}")
        print(f"Files Deleted: {stats['files_deleted']}")
        print(f"Space Saved: {stats['space_saved_mb']:.2f} MB")

        if compressor.config.get("safety", {}).get("dry_run", False):
            print("\n[DRY RUN] No files were actually compressed")

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
