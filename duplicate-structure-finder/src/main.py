"""Duplicate Structure Finder - CLI tool for finding duplicate directory structures.

This module provides a command-line tool for identifying duplicate directory
structures with similar file arrangements, helping consolidate redundant folder
hierarchies.
"""

import argparse
import hashlib
import logging
import logging.handlers
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class DirectoryStructure:
    """Represents the structure of a directory."""

    path: Path
    depth: int
    file_count: int
    subdirectory_count: int
    file_names: Set[str] = field(default_factory=set)
    file_extensions: Set[str] = field(default_factory=set)
    subdirectory_names: Set[str] = field(default_factory=set)
    structure_hash: str = ""
    total_size: int = 0


class StructureAnalyzer:
    """Analyzes directory structures for comparison."""

    def __init__(self, config: Dict) -> None:
        """Initialize StructureAnalyzer.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.analysis_config = config.get("analysis", {})
        self.filter_config = config.get("filtering", {})

    def should_exclude_directory(self, dir_path: Path) -> bool:
        """Check if directory should be excluded from analysis.

        Args:
            dir_path: Path to directory to check.

        Returns:
            True if directory should be excluded, False otherwise.
        """
        exclude_patterns = self.filter_config.get("exclude_directories", [])
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
            "logs",
        }
        return dir_name in system_dirs

    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from analysis.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file should be excluded, False otherwise.
        """
        exclude_patterns = self.filter_config.get("exclude_files", [])
        exclude_extensions = self.filter_config.get("exclude_extensions", [])

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

    def analyze_directory_structure(self, dir_path: Path) -> DirectoryStructure:
        """Analyze the structure of a directory.

        Args:
            dir_path: Path to directory to analyze.

        Returns:
            DirectoryStructure object.
        """
        structure = DirectoryStructure(
            path=dir_path,
            depth=0,
            file_count=0,
            subdirectory_count=0,
        )

        if not dir_path.exists() or not dir_path.is_dir():
            return structure

        try:
            items = list(dir_path.iterdir())
            max_depth = 0

            for item in items:
                if item.is_file():
                    if not self.should_exclude_file(item):
                        structure.file_count += 1
                        structure.file_names.add(item.name)
                        structure.file_extensions.add(item.suffix.lower())

                        try:
                            structure.total_size += item.stat().st_size
                        except (OSError, PermissionError):
                            pass

                elif item.is_dir():
                    if not self.should_exclude_directory(item):
                        structure.subdirectory_count += 1
                        structure.subdirectory_names.add(item.name)

                        # Recursively analyze subdirectory
                        sub_structure = self.analyze_directory_structure(item)
                        max_depth = max(max_depth, sub_structure.depth + 1)

            structure.depth = max_depth

            # Calculate structure hash based on arrangement
            structure.structure_hash = self._calculate_structure_hash(structure)

        except (OSError, PermissionError) as e:
            logger.warning(
                f"Cannot analyze directory {dir_path}: {e}",
                extra={"directory": str(dir_path), "error": str(e)},
            )

        return structure

    def _calculate_structure_hash(self, structure: DirectoryStructure) -> str:
        """Calculate hash representing directory structure.

        Args:
            structure: DirectoryStructure to hash.

        Returns:
            Hash string representing the structure.
        """
        # Create a normalized representation of the structure
        normalized = []
        normalized.append(f"files:{structure.file_count}")
        normalized.append(f"dirs:{structure.subdirectory_count}")
        normalized.append(f"depth:{structure.depth}")

        # Sort for consistency
        normalized.append(f"extensions:{','.join(sorted(structure.file_extensions))}")
        normalized.append(
            f"subdirs:{','.join(sorted(structure.subdirectory_names))}"
        )

        # Create hash
        hash_obj = hashlib.md5()
        hash_obj.update("|".join(normalized).encode("utf-8"))
        return hash_obj.hexdigest()

    def calculate_similarity(
        self, structure1: DirectoryStructure, structure2: DirectoryStructure
    ) -> float:
        """Calculate similarity score between two directory structures.

        Args:
            structure1: First directory structure.
            structure2: Second directory structure.

        Returns:
            Similarity score between 0.0 and 1.0.
        """
        if structure1.structure_hash == structure2.structure_hash:
            return 1.0

        # Calculate various similarity metrics
        scores = []

        # File count similarity
        if structure1.file_count > 0 or structure2.file_count > 0:
            file_ratio = min(structure1.file_count, structure2.file_count) / max(
                structure1.file_count, structure2.file_count
            )
            scores.append(file_ratio * 0.2)

        # Subdirectory count similarity
        if structure1.subdirectory_count > 0 or structure2.subdirectory_count > 0:
            dir_ratio = min(
                structure1.subdirectory_count, structure2.subdirectory_count
            ) / max(structure1.subdirectory_count, structure2.subdirectory_count)
            scores.append(dir_ratio * 0.2)

        # Extension similarity
        if structure1.file_extensions or structure2.file_extensions:
            common_exts = structure1.file_extensions & structure2.file_extensions
            all_exts = structure1.file_extensions | structure2.file_extensions
            if all_exts:
                ext_similarity = len(common_exts) / len(all_exts)
                scores.append(ext_similarity * 0.3)

        # Subdirectory name similarity
        if structure1.subdirectory_names or structure2.subdirectory_names:
            common_dirs = structure1.subdirectory_names & structure2.subdirectory_names
            all_dirs = structure1.subdirectory_names | structure2.subdirectory_names
            if all_dirs:
                dir_name_similarity = len(common_dirs) / len(all_dirs)
                scores.append(dir_name_similarity * 0.2)

        # Depth similarity
        if structure1.depth > 0 or structure2.depth > 0:
            depth_ratio = min(structure1.depth, structure2.depth) / max(
                structure1.depth, structure2.depth
            )
            scores.append(depth_ratio * 0.1)

        return sum(scores) if scores else 0.0


class DuplicateStructureFinder:
    """Finds duplicate directory structures."""

    def __init__(self, config: Dict) -> None:
        """Initialize DuplicateStructureFinder.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.search_config = config.get("search", {})
        self.comparison_config = config.get("comparison", {})

        # Setup logging
        self._setup_logging()

        # Initialize analyzer
        self.analyzer = StructureAnalyzer(config)

    def _setup_logging(self) -> None:
        """Configure logging for the application."""
        log_level = self.config.get("logging", {}).get("level", "INFO")
        log_file = self.config.get("logging", {}).get("file", "logs/finder.log")

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

    def find_directories(self, search_dir: Path) -> List[Path]:
        """Find all directories to analyze.

        Args:
            search_dir: Directory to search in.

        Returns:
            List of directory paths.
        """
        directories = []

        if not search_dir.exists():
            logger.error(f"Search directory does not exist: {search_dir}")
            return directories

        try:
            for root, dirs, filenames in os.walk(search_dir):
                # Filter out excluded directories
                dirs[:] = [
                    d
                    for d in dirs
                    if not self.analyzer.should_exclude_directory(Path(root) / d)
                ]

                current_dir = Path(root)

                # Add current directory if it has content
                if current_dir != search_dir or self.search_config.get(
                    "include_root", False
                ):
                    try:
                        items = list(current_dir.iterdir())
                        if items:
                            directories.append(current_dir)
                    except (OSError, PermissionError):
                        pass

        except (OSError, PermissionError) as e:
            logger.error(
                f"Cannot search directory {search_dir}: {e}",
                extra={"search_directory": str(search_dir), "error": str(e)},
            )

        return directories

    def find_duplicate_structures(
        self, search_dir: Path
    ) -> List[Tuple[DirectoryStructure, DirectoryStructure, float]]:
        """Find duplicate directory structures.

        Args:
            search_dir: Directory to search in.

        Returns:
            List of tuples (structure1, structure2, similarity_score).
        """
        # Find all directories
        directories = self.find_directories(search_dir)
        logger.info(f"Found {len(directories)} directories to analyze")

        # Analyze each directory
        structures: List[DirectoryStructure] = []
        for directory in directories:
            structure = self.analyzer.analyze_directory_structure(directory)
            if structure.file_count > 0 or structure.subdirectory_count > 0:
                structures.append(structure)

        logger.info(f"Analyzed {len(structures)} directory structures")

        # Find duplicates
        duplicates = []
        similarity_threshold = self.comparison_config.get(
            "similarity_threshold", 0.8
        )

        # Compare all pairs
        for i, structure1 in enumerate(structures):
            for structure2 in structures[i + 1 :]:
                similarity = self.analyzer.calculate_similarity(
                    structure1, structure2
                )

                if similarity >= similarity_threshold:
                    duplicates.append((structure1, structure2, similarity))

        # Sort by similarity (highest first)
        duplicates.sort(key=lambda x: x[2], reverse=True)

        return duplicates

    def generate_report(
        self, duplicates: List[Tuple[DirectoryStructure, DirectoryStructure, float]]
    ) -> str:
        """Generate a report of duplicate structures.

        Args:
            duplicates: List of duplicate structure tuples.

        Returns:
            Formatted report string.
        """
        lines = []
        lines.append("=" * 80)
        lines.append("Duplicate Directory Structure Report")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Total duplicate pairs found: {len(duplicates)}")
        lines.append("")

        if not duplicates:
            lines.append("No duplicate directory structures found.")
            lines.append("=" * 80)
            return "\n".join(lines)

        # Group by similarity score ranges
        high_similarity = [
            d for d in duplicates if d[2] >= 0.9
        ]  # 90%+ similarity
        medium_similarity = [
            d for d in duplicates if 0.7 <= d[2] < 0.9
        ]  # 70-90% similarity

        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(f"High similarity (90%+): {len(high_similarity)} pairs")
        lines.append(f"Medium similarity (70-90%): {len(medium_similarity)} pairs")
        lines.append("")

        # Detailed report
        lines.append("DETAILED FINDINGS")
        lines.append("-" * 80)

        for i, (struct1, struct2, similarity) in enumerate(duplicates, 1):
            lines.append(f"\nPair {i} (Similarity: {similarity:.2%})")
            lines.append(f"  Directory 1: {struct1.path}")
            lines.append(f"    Files: {struct1.file_count}")
            lines.append(f"    Subdirectories: {struct1.subdirectory_count}")
            lines.append(f"    Depth: {struct1.depth}")
            lines.append(f"    Extensions: {', '.join(sorted(struct1.file_extensions))}")
            lines.append(f"    Total size: {self._format_size(struct1.total_size)}")

            lines.append(f"  Directory 2: {struct2.path}")
            lines.append(f"    Files: {struct2.file_count}")
            lines.append(f"    Subdirectories: {struct2.subdirectory_count}")
            lines.append(f"    Depth: {struct2.depth}")
            lines.append(f"    Extensions: {', '.join(sorted(struct2.file_extensions))}")
            lines.append(f"    Total size: {self._format_size(struct2.total_size)}")

            # Recommendations
            lines.append("  Recommendation:")
            if similarity >= 0.95:
                lines.append(
                    "    Consider consolidating these directories - they are "
                    "nearly identical."
                )
            elif similarity >= 0.8:
                lines.append(
                    "    These directories are very similar - review for "
                    "consolidation."
                )
            else:
                lines.append(
                    "    These directories have similar structure - consider "
                    "reviewing for potential consolidation."
                )

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes.

        Returns:
            Formatted size string.
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


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
        description="Find duplicate directory structures with similar file "
        "arrangements"
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
        "--directory",
        type=Path,
        help="Directory to search (overrides config)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file path (default: stdout)",
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

    # Override search directory if provided
    if args.directory:
        config.setdefault("search", {})["directory"] = str(args.directory)

    finder = DuplicateStructureFinder(config)

    # Get search directory
    search_dir = Path(config.get("search", {}).get("directory", "."))

    # Find duplicates
    duplicates = finder.find_duplicate_structures(search_dir)

    # Generate report
    report = finder.generate_report(duplicates)

    # Output report
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, "w") as f:
                f.write(report)
            logger.info(f"Report written to: {args.output}")
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to write report: {e}")
            sys.exit(1)
    else:
        print(report)


if __name__ == "__main__":
    main()
