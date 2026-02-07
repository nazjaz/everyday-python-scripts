"""File Health Checker - Verify file integrity and detect corruption.

This module provides functionality to perform comprehensive file health checks
by verifying file integrity, detecting corruption, and validating file headers
and structures. It helps identify damaged, corrupted, or invalid files.
"""

import hashlib
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FileHealthChecker:
    """Performs health checks on files to detect corruption and verify integrity."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize FileHealthChecker with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.file_health: List[Dict[str, Any]] = []
        self.magic_numbers = self._load_magic_numbers()
        self.stats = {
            "files_scanned": 0,
            "healthy_files": 0,
            "corrupted_files": 0,
            "suspicious_files": 0,
            "errors": 0,
        }

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Dictionary containing configuration settings.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            if not config:
                raise ValueError("Configuration file is empty")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in configuration file: {e}")
            raise

    def _setup_logging(self) -> None:
        """Configure logging based on configuration settings."""
        log_level = self.config.get("logging", {}).get("level", "INFO")
        log_file = self.config.get("logging", {}).get("file", "logs/app.log")
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(message)s"
        )

        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format,
            handlers=[
                logging.handlers.RotatingFileHandler(
                    log_file, maxBytes=10485760, backupCount=5
                ),
                logging.StreamHandler(),
            ],
        )

    def _load_magic_numbers(self) -> Dict[str, List[bytes]]:
        """Load file magic number definitions.

        Returns:
            Dictionary mapping file extensions to magic number bytes.
        """
        # Common file magic numbers (first few bytes)
        magic_numbers = {
            ".pdf": [b"%PDF"],
            ".png": [b"\x89PNG\r\n\x1a\n"],
            ".jpg": [b"\xff\xd8\xff"],
            ".jpeg": [b"\xff\xd8\xff"],
            ".gif": [b"GIF87a", b"GIF89a"],
            ".zip": [b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"],
            ".docx": [b"PK\x03\x04"],  # DOCX is a ZIP file
            ".xlsx": [b"PK\x03\x04"],  # XLSX is a ZIP file
            ".pptx": [b"PK\x03\x04"],  # PPTX is a ZIP file
            ".mp3": [b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"],
            ".mp4": [b"\x00\x00\x00", b"ftyp"],
            ".avi": [b"RIFF"],
            ".wav": [b"RIFF"],
            ".exe": [b"MZ"],
            ".dll": [b"MZ"],
            ".pyc": [b"\x16\r\r\n"],  # Python 3.x bytecode
        }

        # Add custom magic numbers from config
        custom_magic = self.config.get("health_check", {}).get(
            "magic_numbers", {}
        )
        for ext, magics in custom_magic.items():
            if isinstance(magics, str):
                magic_numbers[ext] = [magics.encode()]
            elif isinstance(magics, list):
                magic_numbers[ext] = [m.encode() if isinstance(m, str) else m for m in magics]

        return magic_numbers

    def _should_skip_path(self, path: Path) -> bool:
        """Check if a path should be skipped during scanning.

        Args:
            path: Path to check.

        Returns:
            True if path should be skipped, False otherwise.
        """
        skip_patterns = self.config.get("scan", {}).get(
            "skip_patterns", []
        )
        path_str = str(path)

        for pattern in skip_patterns:
            if pattern in path_str:
                return True

        return False

    def _calculate_file_hash(self, file_path: Path, algorithm: str = "md5") -> Optional[str]:
        """Calculate file hash for integrity verification.

        Args:
            file_path: Path to file.
            algorithm: Hash algorithm to use (md5, sha1, sha256).

        Returns:
            Hash string or None if error.
        """
        try:
            if algorithm == "md5":
                hash_obj = hashlib.md5()
            elif algorithm == "sha1":
                hash_obj = hashlib.sha1()
            elif algorithm == "sha256":
                hash_obj = hashlib.sha256()
            else:
                hash_obj = hashlib.md5()

            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)

            return hash_obj.hexdigest()
        except (IOError, PermissionError) as e:
            logger.warning(f"Cannot calculate hash for {file_path}: {e}")
            return None

    def _check_file_header(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Check if file header matches expected magic number.

        Args:
            file_path: Path to file.

        Returns:
            Tuple of (is_valid, error_message).
        """
        extension = file_path.suffix.lower()
        if extension not in self.magic_numbers:
            return (True, None)  # No magic number defined, skip check

        try:
            with open(file_path, "rb") as f:
                header = f.read(16)  # Read first 16 bytes

            if not header:
                return (False, "File is empty")

            expected_magics = self.magic_numbers[extension]
            for magic in expected_magics:
                if header.startswith(magic):
                    return (True, None)

            return (
                False,
                f"File header does not match expected magic number for {extension}",
            )
        except (IOError, PermissionError) as e:
            return (False, f"Cannot read file header: {e}")

    def _check_file_structure(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Check file structure for common issues.

        Args:
            file_path: Path to file.

        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            stat = file_path.stat()
            file_size = stat.st_size

            # Check if file is empty
            if file_size == 0:
                return (False, "File is empty (0 bytes)")

            # Check if file is suspiciously small
            min_size = self.config.get("health_check", {}).get(
                "min_file_size", 1
            )
            if file_size < min_size:
                return (False, f"File is suspiciously small ({file_size} bytes)")

            # Check if file can be read completely
            try:
                with open(file_path, "rb") as f:
                    # Try to read entire file to detect truncation
                    chunk_size = 1024 * 1024  # 1 MB chunks
                    total_read = 0
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        total_read += len(chunk)

                    # If we couldn't read the full size, file might be truncated
                    if total_read < file_size:
                        return (
                            False,
                            f"File appears truncated (read {total_read} of {file_size} bytes)",
                        )
            except (IOError, OSError) as e:
                return (False, f"Cannot read file completely: {e}")

            # File-specific structure checks
            extension = file_path.suffix.lower()
            if extension == ".zip":
                return self._check_zip_structure(file_path)
            elif extension in [".jpg", ".jpeg"]:
                return self._check_jpeg_structure(file_path)
            elif extension == ".png":
                return self._check_png_structure(file_path)
            elif extension == ".pdf":
                return self._check_pdf_structure(file_path)

            return (True, None)

        except (OSError, PermissionError) as e:
            return (False, f"Cannot access file: {e}")

    def _check_zip_structure(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Check ZIP file structure.

        Args:
            file_path: Path to ZIP file.

        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            with open(file_path, "rb") as f:
                # Check for ZIP end of central directory record
                f.seek(0, os.SEEK_END)
                file_size = f.tell()

                # Search backwards for EOCD signature
                search_size = min(65536, file_size)  # Max comment size
                f.seek(max(0, file_size - search_size))

                data = f.read()
                if b"PK\x05\x06" not in data:
                    return (False, "ZIP file missing end of central directory record")

            return (True, None)
        except Exception as e:
            return (False, f"ZIP structure check failed: {e}")

    def _check_jpeg_structure(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Check JPEG file structure.

        Args:
            file_path: Path to JPEG file.

        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            with open(file_path, "rb") as f:
                # Check for JPEG start marker
                header = f.read(2)
                if header != b"\xff\xd8":
                    return (False, "JPEG file missing start marker")

                # Check for JPEG end marker
                f.seek(-2, os.SEEK_END)
                footer = f.read(2)
                if footer != b"\xff\xd9":
                    return (False, "JPEG file missing end marker")

            return (True, None)
        except Exception as e:
            return (False, f"JPEG structure check failed: {e}")

    def _check_png_structure(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Check PNG file structure.

        Args:
            file_path: Path to PNG file.

        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            with open(file_path, "rb") as f:
                # Check PNG signature
                signature = f.read(8)
                expected = b"\x89PNG\r\n\x1a\n"
                if signature != expected:
                    return (False, "PNG file has invalid signature")

                # Check for IEND chunk at end
                f.seek(-12, os.SEEK_END)
                iend = f.read(12)
                if not iend.endswith(b"IEND\xaeB`\x82"):
                    return (False, "PNG file missing IEND chunk")

            return (True, None)
        except Exception as e:
            return (False, f"PNG structure check failed: {e}")

    def _check_pdf_structure(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Check PDF file structure.

        Args:
            file_path: Path to PDF file.

        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            with open(file_path, "rb") as f:
                # Check PDF header
                header = f.read(8)
                if not header.startswith(b"%PDF"):
                    return (False, "PDF file missing header")

                # Check for PDF end marker
                f.seek(-1024, os.SEEK_END)  # Last 1KB
                tail = f.read()
                if b"%%EOF" not in tail:
                    return (False, "PDF file missing end marker (%%EOF)")

            return (True, None)
        except Exception as e:
            return (False, f"PDF structure check failed: {e}")

    def _perform_health_check(self, file_path: Path) -> Dict[str, Any]:
        """Perform comprehensive health check on a file.

        Args:
            file_path: Path to file.

        Returns:
            Dictionary with health check results.
        """
        health_result = {
            "path": str(file_path),
            "name": file_path.name,
            "extension": file_path.suffix,
            "size_bytes": 0,
            "is_healthy": True,
            "issues": [],
            "checksum": None,
        }

        try:
            stat = file_path.stat()
            health_result["size_bytes"] = stat.st_size

            # Check file header
            header_valid, header_error = self._check_file_header(file_path)
            if not header_valid:
                health_result["is_healthy"] = False
                health_result["issues"].append(f"Header: {header_error}")

            # Check file structure
            structure_valid, structure_error = self._check_file_structure(file_path)
            if not structure_valid:
                health_result["is_healthy"] = False
                health_result["issues"].append(f"Structure: {structure_error}")

            # Calculate checksum if enabled
            if self.config.get("health_check", {}).get("calculate_checksum", False):
                algorithm = self.config.get("health_check", {}).get(
                    "checksum_algorithm", "md5"
                )
                checksum = self._calculate_file_hash(file_path, algorithm)
                health_result["checksum"] = checksum

            # Determine health status
            if len(health_result["issues"]) == 0:
                health_result["status"] = "healthy"
            elif len(health_result["issues"]) == 1:
                health_result["status"] = "suspicious"
            else:
                health_result["status"] = "corrupted"

        except (OSError, PermissionError) as e:
            health_result["is_healthy"] = False
            health_result["status"] = "error"
            health_result["issues"].append(f"Access error: {e}")

        return health_result

    def scan_directory(self, directory: str) -> None:
        """Scan directory and perform health checks on files.

        Args:
            directory: Path to directory to scan.

        Raises:
            FileNotFoundError: If directory doesn't exist.
            PermissionError: If directory is not accessible.
        """
        scan_path = Path(directory)
        if not scan_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        if not scan_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        logger.info(
            f"Starting health check scan of {directory}",
            extra={"directory": directory},
        )

        self.file_health = []
        self.stats = {
            "files_scanned": 0,
            "healthy_files": 0,
            "corrupted_files": 0,
            "suspicious_files": 0,
            "errors": 0,
        }

        try:
            for root, dirs, files in os.walk(scan_path):
                root_path = Path(root)

                # Skip directories based on patterns
                dirs[:] = [
                    d
                    for d in dirs
                    if not self._should_skip_path(root_path / d)
                ]

                if self._should_skip_path(root_path):
                    continue

                for file_name in files:
                    file_path = root_path / file_name

                    if self._should_skip_path(file_path):
                        continue

                    self.stats["files_scanned"] += 1

                    try:
                        health_result = self._perform_health_check(file_path)
                        self.file_health.append(health_result)

                        # Update statistics
                        if health_result["status"] == "healthy":
                            self.stats["healthy_files"] += 1
                        elif health_result["status"] == "corrupted":
                            self.stats["corrupted_files"] += 1
                        elif health_result["status"] == "suspicious":
                            self.stats["suspicious_files"] += 1
                        else:
                            self.stats["errors"] += 1

                        if not health_result["is_healthy"]:
                            logger.warning(
                                f"File health issue: {file_path} - "
                                f"{', '.join(health_result['issues'])}",
                                extra={
                                    "file_path": str(file_path),
                                    "issues": health_result["issues"],
                                },
                            )

                    except Exception as e:
                        logger.error(
                            f"Error checking file {file_path}: {e}",
                            extra={"file_path": str(file_path)},
                        )
                        self.stats["errors"] += 1

        except PermissionError as e:
            logger.error(
                f"Permission denied accessing {directory}: {e}",
                extra={"directory": directory},
            )
            raise

        logger.info(
            f"Health check completed: {self.stats['files_scanned']} files scanned, "
            f"{self.stats['healthy_files']} healthy, "
            f"{self.stats['corrupted_files']} corrupted, "
            f"{self.stats['suspicious_files']} suspicious",
            extra=self.stats,
        )

    def generate_report(self, output_path: Optional[str] = None) -> str:
        """Generate health check report.

        Args:
            output_path: Optional path to save report file.

        Returns:
            Report content as string.
        """
        report_config = self.config.get("report", {})
        default_output = report_config.get(
            "output_file", "health_check_report.txt"
        )

        output_file = output_path or default_output

        # Sort files by status
        corrupted = [f for f in self.file_health if f["status"] == "corrupted"]
        suspicious = [f for f in self.file_health if f["status"] == "suspicious"]
        healthy = [f for f in self.file_health if f["status"] == "healthy"]
        errors = [f for f in self.file_health if f["status"] == "error"]

        report_lines = [
            "=" * 80,
            "FILE HEALTH CHECK REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY",
            "-" * 80,
            f"Files scanned: {self.stats['files_scanned']:,}",
            f"Healthy files: {self.stats['healthy_files']:,}",
            f"Corrupted files: {self.stats['corrupted_files']:,}",
            f"Suspicious files: {self.stats['suspicious_files']:,}",
            f"Errors: {self.stats['errors']:,}",
            "",
        ]

        # Corrupted files
        if corrupted:
            report_lines.extend(
                [
                    "CORRUPTED FILES",
                    "-" * 80,
                ]
            )
            for file_info in corrupted:
                report_lines.extend(
                    [
                        f"Path: {file_info['path']}",
                        f"  Size: {self._format_size(file_info['size_bytes'])}",
                        f"  Issues:",
                    ]
                )
                for issue in file_info["issues"]:
                    report_lines.append(f"    - {issue}")
                report_lines.append("")

        # Suspicious files
        if suspicious:
            report_lines.extend(
                [
                    "SUSPICIOUS FILES",
                    "-" * 80,
                ]
            )
            for file_info in suspicious:
                report_lines.extend(
                    [
                        f"Path: {file_info['path']}",
                        f"  Size: {self._format_size(file_info['size_bytes'])}",
                        f"  Issues:",
                    ]
                )
                for issue in file_info["issues"]:
                    report_lines.append(f"    - {issue}")
                report_lines.append("")

        # Files with errors
        if errors:
            report_lines.extend(
                [
                    "FILES WITH ERRORS",
                    "-" * 80,
                ]
            )
            for file_info in errors:
                report_lines.extend(
                    [
                        f"Path: {file_info['path']}",
                        f"  Issues:",
                    ]
                )
                for issue in file_info["issues"]:
                    report_lines.append(f"    - {issue}")
                report_lines.append("")

        if not corrupted and not suspicious and not errors:
            report_lines.append("All files are healthy!")

        report_content = "\n".join(report_lines)

        # Save report
        try:
            output_path_obj = Path(output_file)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path_obj, "w", encoding="utf-8") as f:
                f.write(report_content)
            logger.info(f"Report saved to {output_file}")
        except (IOError, PermissionError) as e:
            logger.error(f"Failed to save report: {e}")
            raise

        return report_content

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes.

        Returns:
            Formatted size string (e.g., "1.5 MB").
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


def main() -> None:
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Perform file health checks by verifying integrity, "
        "detecting corruption, and validating file headers"
    )
    parser.add_argument(
        "directory",
        help="Directory to scan for health checks",
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
        help="Output path for health check report (overrides config)",
    )

    args = parser.parse_args()

    try:
        checker = FileHealthChecker(config_path=args.config)
        checker.scan_directory(args.directory)
        checker.generate_report(output_path=args.output)

        print(
            f"\nHealth check complete. "
            f"Scanned {checker.stats['files_scanned']} files: "
            f"{checker.stats['healthy_files']} healthy, "
            f"{checker.stats['corrupted_files']} corrupted, "
            f"{checker.stats['suspicious_files']} suspicious."
        )

    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
