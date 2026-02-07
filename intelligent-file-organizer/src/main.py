"""Intelligent File Organizer - Organize files by category tags from content analysis.

This module provides functionality to organize files by extracting category tags
from file content analysis, filename patterns, and directory context, creating
intelligent categorization and folder structures.
"""

import logging
import logging.handlers
import os
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class IntelligentFileOrganizer:
    """Organizes files using intelligent categorization based on content, filename, and context."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize IntelligentFileOrganizer with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.categories = self._load_categories()
        self.file_tags: Dict[str, List[str]] = {}
        self.stats = {
            "files_scanned": 0,
            "files_organized": 0,
            "tags_extracted": 0,
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

    def _load_categories(self) -> Dict[str, Dict[str, Any]]:
        """Load category definitions from configuration.

        Returns:
            Dictionary mapping category names to their definitions.
        """
        categories = self.config.get("categories", {})
        if not categories:
            raise ValueError("No categories defined in configuration")

        logger.info(f"Loaded {len(categories)} categories")
        return categories

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

    def _extract_keywords_from_text(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text content.

        Args:
            text: Text content to analyze.
            max_keywords: Maximum number of keywords to extract.

        Returns:
            List of extracted keywords.
        """
        # Common stop words to filter out
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "as", "is", "was", "are",
            "were", "been", "be", "have", "has", "had", "do", "does", "did",
            "will", "would", "could", "should", "may", "might", "must",
            "can", "this", "that", "these", "those", "i", "you", "he", "she",
            "it", "we", "they", "what", "which", "who", "when", "where",
            "why", "how", "all", "each", "every", "both", "few", "more",
            "most", "other", "some", "such", "no", "nor", "not", "only",
        }

        # Extract words (alphanumeric, at least 3 characters)
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        
        # Filter stop words and count frequency
        word_freq = Counter(
            word for word in words if word not in stop_words
        )

        # Return top keywords
        return [word for word, _ in word_freq.most_common(max_keywords)]

    def _extract_tags_from_filename(self, file_path: Path) -> List[str]:
        """Extract category tags from filename.

        Args:
            file_path: Path to file.

        Returns:
            List of extracted tags.
        """
        tags = []
        filename = file_path.stem.lower()

        # Check against category keywords
        for category_name, category_def in self.categories.items():
            keywords = category_def.get("keywords", [])
            patterns = category_def.get("patterns", [])

            # Check keywords
            for keyword in keywords:
                if keyword.lower() in filename:
                    tags.append(category_name)
                    break

            # Check patterns
            for pattern in patterns:
                if re.search(pattern, filename, re.IGNORECASE):
                    tags.append(category_name)
                    break

        return tags

    def _extract_tags_from_directory(self, file_path: Path) -> List[str]:
        """Extract category tags from directory context.

        Args:
            file_path: Path to file.

        Returns:
            List of extracted tags.
        """
        tags = []
        parent_dirs = file_path.parent.parts

        # Check parent directory names
        for category_name, category_def in self.categories.items():
            keywords = category_def.get("keywords", [])
            directory_keywords = category_def.get("directory_keywords", [])

            # Check all directory keywords
            all_keywords = keywords + directory_keywords

            for dir_name in parent_dirs:
                dir_lower = dir_name.lower()
                for keyword in all_keywords:
                    if keyword.lower() in dir_lower:
                        tags.append(category_name)
                        break

        return tags

    def _extract_tags_from_content(self, file_path: Path) -> List[str]:
        """Extract category tags from file content.

        Args:
            file_path: Path to file.

        Returns:
            List of extracted tags.
        """
        tags = []
        max_content_size = self.config.get("analysis", {}).get(
            "max_content_size", 100000
        )

        # Only analyze text files
        text_extensions = self.config.get("analysis", {}).get(
            "text_extensions", [".txt", ".md", ".py", ".js", ".html", ".css"]
        )

        if file_path.suffix.lower() not in text_extensions:
            return tags

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(max_content_size)
                keywords = self._extract_keywords_from_text(content)

                # Match keywords against category definitions
                for category_name, category_def in self.categories.items():
                    category_keywords = category_def.get("content_keywords", [])
                    
                    # Check if any extracted keywords match category keywords
                    for keyword in keywords:
                        if any(
                            cat_kw.lower() in keyword.lower()
                            or keyword.lower() in cat_kw.lower()
                            for cat_kw in category_keywords
                        ):
                            tags.append(category_name)
                            break

        except (IOError, UnicodeDecodeError) as e:
            logger.debug(f"Cannot read content from {file_path}: {e}")

        return tags

    def _determine_category(
        self, file_path: Path, tags: List[str]
    ) -> Optional[str]:
        """Determine primary category from tags.

        Args:
            file_path: Path to file.
            tags: List of category tags.

        Returns:
            Primary category name or None.
        """
        if not tags:
            return None

        # Count tag occurrences
        tag_counts = Counter(tags)

        # Get most common tag
        most_common = tag_counts.most_common(1)
        if most_common:
            return most_common[0][0]

        return None

    def _extract_all_tags(self, file_path: Path) -> List[str]:
        """Extract all tags from filename, directory, and content.

        Args:
            file_path: Path to file.

        Returns:
            List of all extracted tags.
        """
        all_tags = []

        # Extract from filename
        if self.config.get("analysis", {}).get("use_filename", True):
            filename_tags = self._extract_tags_from_filename(file_path)
            all_tags.extend(filename_tags)

        # Extract from directory context
        if self.config.get("analysis", {}).get("use_directory", True):
            dir_tags = self._extract_tags_from_directory(file_path)
            all_tags.extend(dir_tags)

        # Extract from content
        if self.config.get("analysis", {}).get("use_content", True):
            content_tags = self._extract_tags_from_content(file_path)
            all_tags.extend(content_tags)

        return list(set(all_tags))  # Remove duplicates

    def scan_directory(self, directory: str) -> None:
        """Scan directory and extract tags from files.

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
            f"Starting scan of {directory}",
            extra={"directory": directory},
        )

        self.file_tags = {}
        self.stats = {
            "files_scanned": 0,
            "files_organized": 0,
            "tags_extracted": 0,
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

                    try:
                        tags = self._extract_all_tags(file_path)
                        self.file_tags[str(file_path)] = tags
                        self.stats["files_scanned"] += 1
                        self.stats["tags_extracted"] += len(tags)

                        if tags:
                            logger.debug(
                                f"File {file_path.name}: tags={tags}",
                                extra={"file": str(file_path), "tags": tags},
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
            f"{self.stats['tags_extracted']} tags extracted",
            extra=self.stats,
        )

    def organize_files(
        self, source_dir: str, dry_run: bool = False
    ) -> None:
        """Organize files into category-based folders.

        Args:
            source_dir: Source directory containing files.
            dry_run: If True, simulate organization without moving files.
        """
        source_path = Path(source_dir)
        base_folder = Path(
            self.config.get("organization", {}).get(
                "base_folder", "organized"
            )
        )

        logger.info(
            f"Organizing files from {source_dir}",
            extra={"source_dir": source_dir, "dry_run": dry_run},
        )

        organized_count = 0

        for file_path_str, tags in self.file_tags.items():
            file_path = Path(file_path_str)

            # Skip if file is not in source directory
            if not file_path.exists() or not str(file_path).startswith(
                str(source_path)
            ):
                continue

            # Determine category
            category = self._determine_category(file_path, tags)

            if not category:
                logger.debug(f"No category found for {file_path}")
                continue

            # Get category folder
            category_folder = base_folder / self.categories[category].get(
                "folder", category
            )
            category_folder.mkdir(parents=True, exist_ok=True)

            # Determine destination
            dest_path = category_folder / file_path.name

            # Handle filename conflicts
            if dest_path.exists():
                counter = 1
                stem = file_path.stem
                suffix = file_path.suffix
                while dest_path.exists():
                    dest_path = category_folder / f"{stem}_{counter}{suffix}"
                    counter += 1

            # Move file
            try:
                if not dry_run:
                    shutil.move(str(file_path), str(dest_path))
                    logger.info(
                        f"Moved {file_path} -> {dest_path} "
                        f"(Category: {category}, Tags: {tags})"
                    )
                else:
                    logger.info(
                        f"[DRY RUN] Would move {file_path} -> {dest_path} "
                        f"(Category: {category}, Tags: {tags})"
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

        # Count files by category
        category_counts = defaultdict(int)
        for tags in self.file_tags.values():
            if tags:
                category = self._determine_category(Path("dummy"), tags)
                if category:
                    category_counts[category] += 1

        report_lines = [
            "=" * 80,
            "INTELLIGENT FILE ORGANIZATION REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY",
            "-" * 80,
            f"Files scanned: {self.stats['files_scanned']:,}",
            f"Files organized: {self.stats['files_organized']:,}",
            f"Tags extracted: {self.stats['tags_extracted']:,}",
            f"Errors encountered: {self.stats['errors']}",
            "",
            "CATEGORY DISTRIBUTION",
            "-" * 80,
        ]

        for category, count in sorted(
            category_counts.items(), key=lambda x: x[1], reverse=True
        ):
            report_lines.append(f"{category:30s}: {count:6,} files")

        if not category_counts:
            report_lines.append("No files categorized.")

        report_lines.extend(
            [
                "",
                "TAG EXTRACTION EXAMPLES",
                "-" * 80,
            ]
        )

        # Show examples of tagged files
        example_count = 0
        for file_path_str, tags in list(self.file_tags.items())[:10]:
            if tags:
                report_lines.append(f"File: {Path(file_path_str).name}")
                report_lines.append(f"  Tags: {', '.join(tags)}")
                report_lines.append("")
                example_count += 1
                if example_count >= 5:
                    break

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
        description="Organize files using intelligent categorization based on "
        "content, filename, and directory context"
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
        organizer = IntelligentFileOrganizer(config_path=args.config)
        organizer.scan_directory(args.directory)
        organizer.organize_files(args.directory, dry_run=args.dry_run)
        organizer.generate_report(output_path=args.report)

        print(
            f"\nOrganization complete. "
            f"Organized {organizer.stats['files_organized']} files "
            f"from {organizer.stats['files_scanned']} scanned."
        )
        print(f"Extracted {organizer.stats['tags_extracted']} tags total.")

    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
