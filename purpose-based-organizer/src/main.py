"""Purpose-Based File Organizer - Organize files by inferred purpose.

This module provides functionality to organize files by purpose tags inferred
from filenames, locations, and content analysis. Creates purpose-based folder
hierarchies to help users organize files by their intended use rather than
just file type.
"""

import hashlib
import logging
import logging.handlers
import os
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class PurposeBasedOrganizer:
    """Organizes files by purpose tags inferred from various sources."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize PurposeBasedOrganizer with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.purpose_patterns = self._load_purpose_patterns()
        self.location_contexts = self._load_location_contexts()
        self.content_keywords = self._load_content_keywords()
        self.file_purposes: Dict[str, Dict[str, Any]] = {}
        self.file_hashes: Dict[str, str] = {}
        self.stats = {
            "files_scanned": 0,
            "files_organized": 0,
            "duplicates_found": 0,
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

    def _load_purpose_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load purpose patterns from configuration.

        Returns:
            Dictionary mapping purpose names to pattern definitions.
        """
        patterns = {
            "Financial": [
                {"keywords": ["invoice", "bill", "receipt", "payment"], "weight": 3},
                {"keywords": ["tax", "irs", "w2", "1099"], "weight": 3},
                {"keywords": ["bank", "statement", "transaction"], "weight": 2},
                {"keywords": ["expense", "budget", "finance"], "weight": 2},
            ],
            "Work": [
                {"keywords": ["resume", "cv", "cover_letter"], "weight": 3},
                {"keywords": ["project", "proposal", "report"], "weight": 2},
                {"keywords": ["meeting", "agenda", "minutes"], "weight": 2},
                {"keywords": ["contract", "agreement", "nda"], "weight": 3},
            ],
            "Personal": [
                {"keywords": ["photo", "picture", "image"], "weight": 2},
                {"keywords": ["diary", "journal", "note"], "weight": 2},
                {"keywords": ["personal", "private"], "weight": 1},
            ],
            "Education": [
                {"keywords": ["homework", "assignment", "essay"], "weight": 3},
                {"keywords": ["course", "lecture", "notes"], "weight": 2},
                {"keywords": ["exam", "test", "quiz"], "weight": 3},
                {"keywords": ["certificate", "diploma", "degree"], "weight": 3},
            ],
            "Health": [
                {"keywords": ["medical", "health", "prescription"], "weight": 3},
                {"keywords": ["insurance", "claim", "benefits"], "weight": 2},
                {"keywords": ["lab", "test", "result"], "weight": 2},
            ],
            "Travel": [
                {"keywords": ["trip", "travel", "vacation"], "weight": 3},
                {"keywords": ["itinerary", "booking", "reservation"], "weight": 3},
                {"keywords": ["passport", "visa", "ticket"], "weight": 3},
            ],
            "Legal": [
                {"keywords": ["legal", "law", "court"], "weight": 2},
                {"keywords": ["will", "estate", "trust"], "weight": 3},
                {"keywords": ["license", "permit"], "weight": 2},
            ],
        }

        # Add custom patterns from config
        custom_patterns = self.config.get("purpose_detection", {}).get(
            "patterns", {}
        )
        patterns.update(custom_patterns)

        return patterns

    def _load_location_contexts(self) -> Dict[str, List[str]]:
        """Load location-based context mappings.

        Returns:
            Dictionary mapping folder names to purpose tags.
        """
        contexts = {
            "Downloads": ["Temporary", "Pending"],
            "Desktop": ["Active", "Current"],
            "Documents": ["Archive", "Reference"],
            "Projects": ["Work", "Development"],
            "Pictures": ["Personal", "Media"],
            "Videos": ["Personal", "Media"],
        }

        # Add custom contexts from config
        custom_contexts = self.config.get("purpose_detection", {}).get(
            "location_contexts", {}
        )
        contexts.update(custom_contexts)

        return contexts

    def _load_content_keywords(self) -> Dict[str, List[str]]:
        """Load content-based keyword mappings.

        Returns:
            Dictionary mapping purpose names to content keywords.
        """
        keywords = {
            "Financial": [
                "total amount",
                "invoice number",
                "payment due",
                "account balance",
            ],
            "Work": [
                "project objectives",
                "meeting agenda",
                "action items",
                "deadline",
            ],
            "Education": [
                "assignment",
                "course syllabus",
                "grading rubric",
                "learning objectives",
            ],
            "Health": [
                "medical record",
                "prescription",
                "diagnosis",
                "treatment plan",
            ],
        }

        # Add custom keywords from config
        custom_keywords = self.config.get("purpose_detection", {}).get(
            "content_keywords", {}
        )
        keywords.update(custom_keywords)

        return keywords

    def _should_skip_path(self, path: Path) -> bool:
        """Check if a path should be skipped during scanning.

        Args:
            path: Path to check.

        Returns:
            True if path should be skipped, False otherwise.
        """
        skip_patterns = self.config.get("scan", {}).get("skip_patterns", [])
        path_str = str(path)

        for pattern in skip_patterns:
            if pattern in path_str:
                return True

        return False

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file for duplicate detection.

        Args:
            file_path: Path to file.

        Returns:
            MD5 hash as hexadecimal string.
        """
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (IOError, PermissionError) as e:
            logger.debug(f"Cannot read file for hashing: {file_path} - {e}")
            return ""

    def _infer_purpose_from_filename(
        self, filename: str
    ) -> Dict[str, int]:
        """Infer purpose tags from filename.

        Args:
            filename: Name of the file.

        Returns:
            Dictionary mapping purpose names to confidence scores.
        """
        filename_lower = filename.lower()
        purpose_scores: Dict[str, int] = defaultdict(int)

        for purpose, patterns in self.purpose_patterns.items():
            for pattern in patterns:
                keywords = pattern["keywords"]
                weight = pattern.get("weight", 1)

                for keyword in keywords:
                    if keyword in filename_lower:
                        purpose_scores[purpose] += weight

        return purpose_scores

    def _infer_purpose_from_location(
        self, file_path: Path
    ) -> Dict[str, int]:
        """Infer purpose tags from file location.

        Args:
            file_path: Path to file.

        Returns:
            Dictionary mapping purpose names to confidence scores.
        """
        purpose_scores: Dict[str, int] = defaultdict(int)
        path_parts = file_path.parts

        for part in path_parts:
            part_lower = part.lower()
            for location, purposes in self.location_contexts.items():
                if location.lower() in part_lower:
                    for purpose in purposes:
                        purpose_scores[purpose] += 2

        return purpose_scores

    def _infer_purpose_from_content(
        self, file_path: Path
    ) -> Dict[str, int]:
        """Infer purpose tags from file content (for text files).

        Args:
            file_path: Path to file.

        Returns:
            Dictionary mapping purpose names to confidence scores.
        """
        purpose_scores: Dict[str, int] = defaultdict(int)

        # Only analyze text-based files
        text_extensions = {
            ".txt",
            ".md",
            ".doc",
            ".docx",
            ".pdf",
            ".rtf",
            ".html",
            ".htm",
        }

        if file_path.suffix.lower() not in text_extensions:
            return purpose_scores

        try:
            # Try to read as text
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(10000).lower()  # Read first 10KB

            for purpose, keywords in self.content_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in content:
                        purpose_scores[purpose] += 1

        except (IOError, PermissionError, UnicodeDecodeError) as e:
            logger.debug(f"Cannot read content: {file_path} - {e}")

        return purpose_scores

    def _determine_primary_purpose(
        self, filename_scores: Dict[str, int], location_scores: Dict[str, int],
        content_scores: Dict[str, int]
    ) -> Tuple[Optional[str], List[str]]:
        """Determine primary purpose from all scores.

        Args:
            filename_scores: Purpose scores from filename analysis.
            location_scores: Purpose scores from location analysis.
            content_scores: Purpose scores from content analysis.

        Returns:
            Tuple of (primary_purpose, all_purposes).
        """
        # Combine scores with weights
        combined_scores: Dict[str, float] = defaultdict(float)

        # Filename is most reliable (weight: 3)
        for purpose, score in filename_scores.items():
            combined_scores[purpose] += score * 3

        # Location provides context (weight: 2)
        for purpose, score in location_scores.items():
            combined_scores[purpose] += score * 2

        # Content provides additional evidence (weight: 1)
        for purpose, score in content_scores.items():
            combined_scores[purpose] += score * 1

        if not combined_scores:
            return (None, [])

        # Sort by score
        sorted_purposes = sorted(
            combined_scores.items(), key=lambda x: x[1], reverse=True
        )

        # Get primary purpose (highest score)
        primary_purpose = sorted_purposes[0][0] if sorted_purposes else None

        # Get all purposes above threshold
        threshold = self.config.get("purpose_detection", {}).get(
            "min_score", 1
        )
        all_purposes = [
            purpose
            for purpose, score in sorted_purposes
            if score >= threshold
        ]

        return (primary_purpose, all_purposes)

    def _build_folder_hierarchy(
        self, primary_purpose: Optional[str], all_purposes: List[str]
    ) -> Path:
        """Build folder hierarchy path based on purposes.

        Args:
            primary_purpose: Primary purpose tag.
            all_purposes: All detected purpose tags.

        Returns:
            Path object representing folder hierarchy.
        """
        base_folder = Path(
            self.config.get("organization", {}).get(
                "base_folder", "organized"
            )
        )

        if not primary_purpose:
            return base_folder / self.config.get("organization", {}).get(
                "unknown_folder", "Unknown"
            )

        # Build hierarchy: base / primary / secondary / ...
        folder_path = base_folder / primary_purpose

        # Add secondary purposes as subfolders if configured
        if self.config.get("organization", {}).get(
            "include_secondary_purposes", False
        ):
            for secondary in all_purposes[1:]:
                folder_path = folder_path / secondary

        return folder_path

    def scan_directory(self, directory: str) -> None:
        """Scan directory and infer file purposes.

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
            f"Starting purpose-based scan of {directory}",
            extra={"directory": directory},
        )

        self.file_purposes = {}
        self.file_hashes = {}
        self.stats = {
            "files_scanned": 0,
            "files_organized": 0,
            "duplicates_found": 0,
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
                        # Calculate file hash for duplicate detection
                        file_hash = self._calculate_file_hash(file_path)

                        # Check for duplicates
                        is_duplicate = False
                        if file_hash and file_hash in self.file_hashes.values():
                            is_duplicate = True
                            self.stats["duplicates_found"] += 1
                            logger.warning(
                                f"Duplicate file detected: {file_path}",
                                extra={"file_path": str(file_path)},
                            )

                        # Infer purposes
                        filename_scores = self._infer_purpose_from_filename(
                            file_path.name
                        )
                        location_scores = self._infer_purpose_from_location(
                            file_path
                        )
                        content_scores = self._infer_purpose_from_content(
                            file_path
                        )

                        primary_purpose, all_purposes = (
                            self._determine_primary_purpose(
                                filename_scores, location_scores,
                                content_scores
                            )
                        )

                        folder_path = self._build_folder_hierarchy(
                            primary_purpose, all_purposes
                        )

                        self.file_purposes[str(file_path)] = {
                            "path": str(file_path),
                            "name": file_path.name,
                            "extension": file_path.suffix,
                            "primary_purpose": primary_purpose,
                            "all_purposes": all_purposes,
                            "folder": str(folder_path),
                            "filename_scores": dict(filename_scores),
                            "location_scores": dict(location_scores),
                            "content_scores": dict(content_scores),
                            "is_duplicate": is_duplicate,
                            "file_hash": file_hash,
                            "size_bytes": file_path.stat().st_size,
                        }

                        if primary_purpose:
                            logger.debug(
                                f"File {file_path.name} -> "
                                f"Purpose: {primary_purpose}, "
                                f"Folder: {folder_path}"
                            )

                    except Exception as e:
                        logger.warning(
                            f"Error processing file {file_path}: {e}",
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
            f"Scan completed: {self.stats['files_scanned']} files scanned, "
            f"{self.stats['duplicates_found']} duplicates found",
            extra=self.stats,
        )

    def organize_files(
        self, source_dir: str, dry_run: bool = False
    ) -> None:
        """Organize files into purpose-based folder hierarchies.

        Args:
            source_dir: Source directory containing files.
            dry_run: If True, simulate organization without moving files.
        """
        source_path = Path(source_dir)

        logger.info(
            f"Organizing files from {source_dir}",
            extra={"source_dir": source_dir, "dry_run": dry_run},
        )

        organized_count = 0

        for file_path_str, file_info in self.file_purposes.items():
            file_path = Path(file_path_str)

            # Skip if file is not in source directory
            if not file_path.exists() or not str(file_path).startswith(
                str(source_path)
            ):
                continue

            # Skip duplicates if configured
            if (
                file_info["is_duplicate"]
                and self.config.get("organization", {}).get(
                    "skip_duplicates", False
                )
            ):
                logger.info(
                    f"Skipping duplicate file: {file_path}",
                    extra={"file_path": str(file_path)},
                )
                continue

            # Determine destination folder
            folder_path = Path(file_info["folder"])
            folder_path.mkdir(parents=True, exist_ok=True)

            # Determine destination
            dest_path = folder_path / file_path.name

            # Handle filename conflicts
            if dest_path.exists():
                counter = 1
                stem = file_path.stem
                suffix = file_path.suffix
                while dest_path.exists():
                    dest_path = folder_path / f"{stem}_{counter}{suffix}"
                    counter += 1

            # Move file
            try:
                if not dry_run:
                    shutil.move(str(file_path), str(dest_path))
                    logger.info(
                        f"Moved {file_path} -> {dest_path} "
                        f"(Purpose: {file_info['primary_purpose']}, "
                        f"Folder: {file_info['folder']})"
                    )
                else:
                    logger.info(
                        f"[DRY RUN] Would move {file_path} -> {dest_path} "
                        f"(Purpose: {file_info['primary_purpose']}, "
                        f"Folder: {file_info['folder']})"
                    )

                organized_count += 1

            except (OSError, shutil.Error) as e:
                logger.error(
                    f"Error organizing file {file_path}: {e}",
                    extra={"file_path": str(file_path)},
                )
                self.stats["errors"] += 1

        self.stats["files_organized"] = organized_count

        logger.info(
            f"Organization completed: {organized_count} files organized",
            extra={"organized": organized_count},
        )

    def generate_report(self, output_path: Optional[str] = None) -> str:
        """Generate organization report.

        Args:
            output_path: Optional path to save report file.

        Returns:
            Report content as string.
        """
        report_config = self.config.get("report", {})
        default_output = report_config.get(
            "output_file", "organization_report.txt"
        )

        output_file = output_path or default_output

        # Count files by purpose
        purpose_counts = defaultdict(int)
        duplicate_files = []

        for file_info in self.file_purposes.values():
            purpose = file_info["primary_purpose"] or "Unknown"
            purpose_counts[purpose] += 1

            if file_info["is_duplicate"]:
                duplicate_files.append(file_info)

        report_lines = [
            "=" * 80,
            "PURPOSE-BASED ORGANIZATION REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY",
            "-" * 80,
            f"Files scanned: {self.stats['files_scanned']:,}",
            f"Files organized: {self.stats['files_organized']:,}",
            f"Duplicates found: {self.stats['duplicates_found']:,}",
            f"Errors encountered: {self.stats['errors']}",
            "",
            "PURPOSE DISTRIBUTION",
            "-" * 80,
        ]

        for purpose, count in sorted(
            purpose_counts.items(), key=lambda x: x[1], reverse=True
        ):
            report_lines.append(f"{purpose:30s}: {count:6,} files")

        if duplicate_files:
            report_lines.extend(
                [
                    "",
                    "DUPLICATE FILES",
                    "-" * 80,
                ]
            )
            for file_info in duplicate_files[:20]:
                report_lines.extend(
                    [
                        f"File: {file_info['name']}",
                        f"  Path: {file_info['path']}",
                        f"  Hash: {file_info['file_hash'][:16]}...",
                        "",
                    ]
                )
            if len(duplicate_files) > 20:
                report_lines.append(
                    f"... and {len(duplicate_files) - 20} more duplicates"
                )

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


def main() -> None:
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Organize files by purpose tags inferred from filenames, "
        "locations, and content"
    )
    parser.add_argument(
        "directory",
        help="Directory to scan and organize",
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
        help="Simulate organization without moving files",
    )
    parser.add_argument(
        "-r",
        "--report",
        help="Output path for organization report (overrides config)",
    )

    args = parser.parse_args()

    try:
        organizer = PurposeBasedOrganizer(config_path=args.config)
        organizer.scan_directory(args.directory)
        organizer.organize_files(args.directory, dry_run=args.dry_run)
        organizer.generate_report(output_path=args.report)

        print(
            f"\nOrganization complete. "
            f"Organized {organizer.stats['files_organized']} files "
            f"from {organizer.stats['files_scanned']} scanned."
        )
        if organizer.stats["duplicates_found"] > 0:
            print(
                f"Found {organizer.stats['duplicates_found']} duplicate files."
            )

    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
