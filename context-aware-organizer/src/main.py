"""Context-Aware File Organizer - CLI tool for context-based file organization.

This module provides a command-line tool for organizing files by analyzing
context clues from parent directories, filenames, and nearby files to create
intelligent, context-aware organization.
"""

import argparse
import hashlib
import logging
import logging.handlers
import os
import re
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ContextAnalyzer:
    """Analyzes context clues from directories, filenames, and nearby files."""

    def __init__(self, config: Dict) -> None:
        """Initialize ContextAnalyzer.

        Args:
            config: Configuration dictionary containing analysis settings.
        """
        self.config = config
        self.analysis_config = config.get("analysis", {})
        self.context_keywords = config.get("context_keywords", {})

    def analyze_parent_directories(self, file_path: Path) -> Dict[str, float]:
        """Analyze parent directory names for context clues.

        Args:
            file_path: Path to file to analyze.

        Returns:
            Dictionary mapping context categories to confidence scores.
        """
        context_scores = defaultdict(float)
        path_parts = file_path.parent.parts

        # Analyze each directory level
        for part in path_parts:
            part_lower = part.lower()

            # Check against context keywords
            for category, keywords in self.context_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in part_lower:
                        # Higher weight for closer directories
                        weight = 1.0 / (len(path_parts) - path_parts.index(part) + 1)
                        context_scores[category] += weight

            # Check for common patterns
            if any(word in part_lower for word in ["project", "work", "job"]):
                context_scores["work"] += 0.5
            if any(word in part_lower for word in ["personal", "home", "private"]):
                context_scores["personal"] += 0.5
            if any(word in part_lower for word in ["download", "temp", "tmp"]):
                context_scores["temporary"] += 0.5

        return dict(context_scores)

    def analyze_filename(self, file_path: Path) -> Dict[str, float]:
        """Analyze filename for context clues.

        Args:
            file_path: Path to file to analyze.

        Returns:
            Dictionary mapping context categories to confidence scores.
        """
        context_scores = defaultdict(float)
        filename = file_path.stem.lower()
        extension = file_path.suffix.lower()

        # Check filename against context keywords
        for category, keywords in self.context_keywords.items():
            for keyword in keywords:
                if keyword.lower() in filename:
                    context_scores[category] += 1.0

        # Analyze filename patterns
        if re.search(r"\d{4}[-_]\d{2}[-_]\d{2}", filename):
            context_scores["dated"] += 0.5
        if re.search(r"backup|bak|copy|old", filename):
            context_scores["backup"] += 0.5
        if re.search(r"draft|temp|tmp|scratch", filename):
            context_scores["temporary"] += 0.5
        if re.search(r"final|complete|done", filename):
            context_scores["final"] += 0.5

        # Analyze extension for type hints
        type_context = self._get_type_context(extension)
        if type_context:
            context_scores[type_context] += 0.3

        return dict(context_scores)

    def _get_type_context(self, extension: str) -> Optional[str]:
        """Get context category from file extension.

        Args:
            extension: File extension.

        Returns:
            Context category or None.
        """
        type_mapping = {
            "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"],
            "document": [".pdf", ".doc", ".docx", ".txt", ".rtf"],
            "spreadsheet": [".xls", ".xlsx", ".csv"],
            "presentation": [".ppt", ".pptx"],
            "code": [".py", ".js", ".java", ".cpp", ".c", ".html"],
            "data": [".json", ".xml", ".yaml", ".csv"],
        }

        for category, extensions in type_mapping.items():
            if extension in extensions:
                return category

        return None

    def analyze_nearby_files(self, file_path: Path) -> Dict[str, float]:
        """Analyze nearby files in the same directory for context.

        Args:
            file_path: Path to file to analyze.

        Returns:
            Dictionary mapping context categories to confidence scores.
        """
        context_scores = defaultdict(float)
        directory = file_path.parent

        if not directory.exists():
            return {}

        try:
            # Get files in the same directory
            nearby_files = [
                f for f in directory.iterdir()
                if f.is_file() and f != file_path
            ]

            if not nearby_files:
                return {}

            # Analyze file types in directory
            extensions = Counter(f.suffix.lower() for f in nearby_files)
            total_files = len(nearby_files)

            # If most files are of a certain type, add context
            for ext, count in extensions.most_common(3):
                if count / total_files > 0.5:  # More than 50% of files
                    type_context = self._get_type_context(ext)
                    if type_context:
                        context_scores[type_context] += 0.4

            # Analyze filenames in directory
            filename_keywords = Counter()
            for nearby_file in nearby_files[:20]:  # Limit analysis
                filename_parts = re.findall(r"\w+", nearby_file.stem.lower())
                filename_keywords.update(filename_parts)

            # Check if common keywords match context categories
            for category, keywords in self.context_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in filename_keywords:
                        weight = filename_keywords[keyword.lower()] / total_files
                        context_scores[category] += weight * 0.3

            # Check for project indicators
            project_indicators = ["readme", "package.json", "requirements.txt", "setup.py"]
            for indicator in project_indicators:
                if any(indicator in f.name.lower() for f in nearby_files):
                    context_scores["project"] += 0.5
                    break

        except (OSError, PermissionError) as e:
            logger.debug(
                f"Cannot analyze nearby files for {file_path}: {e}",
                extra={"file_path": str(file_path)},
            )

        return dict(context_scores)

    def combine_context(self, file_path: Path) -> Tuple[str, float]:
        """Combine all context clues to determine organization category.

        Args:
            file_path: Path to file to analyze.

        Returns:
            Tuple of (category, confidence_score).
        """
        # Get context from all sources
        parent_context = self.analyze_parent_directories(file_path)
        filename_context = self.analyze_filename(file_path)
        nearby_context = self.analyze_nearby_files(file_path)

        # Combine scores with weights
        weights = self.analysis_config.get("weights", {
            "parent_directories": 0.4,
            "filename": 0.4,
            "nearby_files": 0.2,
        })

        combined_scores = defaultdict(float)

        for category, score in parent_context.items():
            combined_scores[category] += score * weights.get("parent_directories", 0.4)

        for category, score in filename_context.items():
            combined_scores[category] += score * weights.get("filename", 0.4)

        for category, score in nearby_context.items():
            combined_scores[category] += score * weights.get("nearby_files", 0.2)

        # If no strong context found, use file type
        if not combined_scores:
            file_type = self._get_type_context(file_path.suffix.lower())
            if file_type:
                return (file_type, 0.3)
            return ("miscellaneous", 0.1)

        # Get category with highest score
        best_category = max(combined_scores.items(), key=lambda x: x[1])
        return best_category


class ContextOrganizer:
    """Organizes files based on context analysis."""

    def __init__(self, config: Dict) -> None:
        """Initialize ContextOrganizer.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.organize_config = config.get("organization", {})
        self.source_dir = Path(config.get("source_directory", "."))
        self.destination_dir = Path(
            self.organize_config.get("destination_directory", "./organized")
        )
        self.destination_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self._setup_logging()

        # Initialize context analyzer
        self.analyzer = ContextAnalyzer(config)

    def _setup_logging(self) -> None:
        """Configure logging for the application."""
        log_level = self.config.get("logging", {}).get("level", "INFO")
        log_file = self.config.get("logging", {}).get("file", "logs/organizer.log")

        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.handlers.RotatingFileHandler(
                    log_file, maxBytes=10485760, backupCount=5
                ),
                logging.StreamHandler(sys.stdout),
            ],
        )

    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from processing.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file should be excluded, False otherwise.
        """
        exclude_patterns = self.organize_config.get("exclude_files", [])
        exclude_extensions = self.organize_config.get("exclude_extensions", [])

        file_name = file_path.name
        file_ext = file_path.suffix.lower()

        # Check exclude patterns
        for pattern in exclude_patterns:
            if pattern in file_name or file_name.startswith(pattern):
                return True

        # Check exclude extensions
        if file_ext in exclude_extensions:
            return True

        # Always exclude hidden files
        if file_name.startswith(".") and file_name not in [".gitkeep"]:
            return True

        return False

    def should_exclude_directory(self, dir_path: Path) -> bool:
        """Check if directory should be excluded from processing.

        Args:
            dir_path: Path to directory to check.

        Returns:
            True if directory should be excluded, False otherwise.
        """
        exclude_patterns = self.organize_config.get("exclude_directories", [])
        dir_name = dir_path.name

        for pattern in exclude_patterns:
            if pattern in dir_name or dir_name.startswith(pattern):
                return True

        # Always exclude common system directories
        system_dirs = {
            ".git",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            ".venv",
            "venv",
        }
        return dir_name in system_dirs

    def calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """Calculate MD5 hash of a file for duplicate detection.

        Args:
            file_path: Path to the file.

        Returns:
            MD5 hash string, or None if file cannot be read.
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (OSError, PermissionError) as e:
            logger.warning(
                f"Cannot calculate hash for {file_path}: {e}",
                extra={"file_path": str(file_path), "error": str(e)},
            )
            return None

    def get_destination_path(
        self, file_path: Path, category: str, confidence: float
    ) -> Path:
        """Get destination path for a file based on context category.

        Args:
            file_path: Original file path.
            category: Context category.
            confidence: Confidence score.

        Returns:
            Destination path for the file.
        """
        # Create category directory
        category_dir = self.destination_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)

        # If confidence is low, add to "uncertain" subdirectory
        if confidence < self.organize_config.get("min_confidence", 0.3):
            category_dir = category_dir / "uncertain"
            category_dir.mkdir(parents=True, exist_ok=True)

        return category_dir / file_path.name

    def organize_file(
        self, file_path: Path, dry_run: bool = False
    ) -> Tuple[bool, str, float]:
        """Organize a file based on context analysis.

        Args:
            file_path: Path to file to organize.
            dry_run: If True, only report what would be done.

        Returns:
            Tuple of (success, category, confidence).
        """
        # Analyze context
        category, confidence = self.analyzer.combine_context(file_path)

        # Get destination path
        dest_path = self.get_destination_path(file_path, category, confidence)

        # Skip if already in correct location
        if file_path.resolve() == dest_path.resolve():
            return (True, category, confidence)

        # Check for duplicates
        if self.organize_config.get("check_duplicates", True):
            file_hash = self.calculate_file_hash(file_path)
            if file_hash:
                hash_file = dest_path.parent / ".hashes.txt"
                existing_hashes = set()
                if hash_file.exists():
                    try:
                        with open(hash_file, "r") as f:
                            existing_hashes = set(line.strip() for line in f)
                    except (OSError, IOError):
                        pass

                if file_hash in existing_hashes:
                    logger.info(
                        f"Skipping duplicate: {file_path.name}",
                        extra={"file_path": str(file_path)},
                    )
                    return (False, category, confidence)

        # Handle filename conflicts
        if dest_path.exists() and not dry_run:
            if self.organize_config.get("skip_duplicates", True):
                logger.info(
                    f"Skipping existing file: {dest_path}",
                    extra={"source": str(file_path), "destination": str(dest_path)},
                )
                return (False, category, confidence)

            # Add timestamp to filename
            stem = dest_path.stem
            suffix = dest_path.suffix
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_path = dest_path.parent / f"{stem}_{timestamp}{suffix}"

        if dry_run:
            logger.info(
                f"[DRY RUN] Would move {file_path.name} to {category}/ "
                f"(confidence: {confidence:.2f})",
                extra={
                    "source": str(file_path),
                    "destination": str(dest_path),
                    "category": category,
                    "confidence": confidence,
                },
            )
            return (True, category, confidence)

        try:
            # Create destination directory
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Move file
            shutil.move(str(file_path), str(dest_path))

            # Update hash file
            if file_hash and self.organize_config.get("check_duplicates", True):
                hash_file = dest_path.parent / ".hashes.txt"
                with open(hash_file, "a") as f:
                    f.write(f"{file_hash}\n")

            logger.info(
                f"Moved {file_path.name} to {category}/ "
                f"(confidence: {confidence:.2f})",
                extra={
                    "source": str(file_path),
                    "destination": str(dest_path),
                    "category": category,
                    "confidence": confidence,
                },
            )
            return (True, category, confidence)

        except (OSError, PermissionError, shutil.Error) as e:
            logger.error(
                f"Failed to move file {file_path}: {e}",
                extra={"file_path": str(file_path), "error": str(e)},
            )
            return (False, category, confidence)

    def scan_files(self) -> List[Path]:
        """Scan source directory for files to organize.

        Returns:
            List of file paths.
        """
        files = []
        if not self.source_dir.exists():
            logger.error(f"Source directory does not exist: {self.source_dir}")
            return files

        try:
            for root, dirs, filenames in os.walk(self.source_dir):
                # Filter out excluded directories
                dirs[:] = [
                    d
                    for d in dirs
                    if not self.should_exclude_directory(Path(root) / d)
                ]

                for filename in filenames:
                    file_path = Path(root) / filename

                    if self.should_exclude_file(file_path):
                        continue

                    files.append(file_path)

        except (OSError, PermissionError) as e:
            logger.error(
                f"Cannot scan source directory {self.source_dir}: {e}",
                extra={"source_directory": str(self.source_dir), "error": str(e)},
            )

        return files

    def organize_files(self, dry_run: bool = False) -> Dict[str, int]:
        """Organize all files based on context analysis.

        Args:
            dry_run: If True, only report what would be done.

        Returns:
            Dictionary with organization statistics.
        """
        results = {
            "scanned": 0,
            "organized": 0,
            "duplicates": 0,
            "failed": 0,
            "categories": defaultdict(int),
        }

        files = self.scan_files()
        results["scanned"] = len(files)

        logger.info(
            f"Found {len(files)} files to organize",
            extra={"file_count": len(files), "dry_run": dry_run},
        )

        for file_path in files:
            try:
                success, category, confidence = self.organize_file(
                    file_path, dry_run=dry_run
                )

                if success:
                    results["organized"] += 1
                    results["categories"][category] += 1
                elif confidence > 0:
                    results["duplicates"] += 1
                else:
                    results["failed"] += 1

            except Exception as e:
                logger.error(
                    f"Error organizing file {file_path}: {e}",
                    extra={"file_path": str(file_path), "error": str(e)},
                    exc_info=True,
                )
                results["failed"] += 1

        return results


def load_config(config_path: Path) -> Dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to configuration file.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        yaml.YAMLError: If config file is invalid YAML.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config or {}
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in config file: {e}") from e


def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Organize files by context clues from parent directories, "
        "filenames, and nearby files"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making changes",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(str(e))
        sys.exit(1)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    organizer = ContextOrganizer(config)

    if args.dry_run:
        logger.info("Running in dry-run mode - no files will be moved")

    results = organizer.organize_files(dry_run=args.dry_run)

    # Print summary
    print("\n" + "=" * 60)
    print("Context-Aware Organization Summary")
    print("=" * 60)
    print(f"Files scanned: {results['scanned']}")
    print(f"Files organized: {results['organized']}")
    print(f"Duplicates skipped: {results['duplicates']}")
    print(f"Files failed: {results['failed']}")
    print("\nCategories:")
    for category, count in sorted(results["categories"].items()):
        print(f"  {category}: {count}")
    print("=" * 60)

    if results["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
