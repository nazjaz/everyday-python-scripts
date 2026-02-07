"""Similar File Finder - Find files with similar names using string similarity.

This module provides functionality to scan directories and identify files
with similar names using various string similarity algorithms, useful for
finding potential duplicates or related files.
"""

import difflib
import logging
import logging.handlers
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class SimilarFileFinder:
    """Finds files with similar names using string similarity algorithms."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize SimilarFileFinder with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.files: List[Dict[str, Any]] = []
        self.similar_pairs: List[Dict[str, Any]] = []
        self.stats = {
            "files_scanned": 0,
            "similar_pairs_found": 0,
            "directories_scanned": 0,
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

    def _sequence_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity using SequenceMatcher (difflib).

        Args:
            str1: First string.
            str2: Second string.

        Returns:
            Similarity ratio between 0.0 and 1.0.
        """
        return difflib.SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    def _levenshtein_distance(self, str1: str, str2: str) -> int:
        """Calculate Levenshtein distance between two strings.

        Args:
            str1: First string.
            str2: Second string.

        Returns:
            Levenshtein distance (number of edits needed).
        """
        str1 = str1.lower()
        str2 = str2.lower()

        if len(str1) < len(str2):
            return self._levenshtein_distance(str2, str1)

        if len(str2) == 0:
            return len(str1)

        previous_row = range(len(str2) + 1)
        for i, c1 in enumerate(str1):
            current_row = [i + 1]
            for j, c2 in enumerate(str2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _levenshtein_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity based on Levenshtein distance.

        Args:
            str1: First string.
            str2: Second string.

        Returns:
            Similarity ratio between 0.0 and 1.0.
        """
        max_len = max(len(str1), len(str2))
        if max_len == 0:
            return 1.0

        distance = self._levenshtein_distance(str1, str2)
        return 1.0 - (distance / max_len)

    def _jaro_winkler_similarity(self, str1: str, str2: str) -> float:
        """Calculate Jaro-Winkler similarity.

        Args:
            str1: First string.
            str2: Second string.

        Returns:
            Similarity ratio between 0.0 and 1.0.
        """
        str1 = str1.lower()
        str2 = str2.lower()

        if str1 == str2:
            return 1.0

        # Jaro similarity
        len1, len2 = len(str1), len(str2)
        match_window = max(len1, len2) // 2 - 1
        if match_window < 0:
            match_window = 0

        str1_matches = [False] * len1
        str2_matches = [False] * len2

        matches = 0
        transpositions = 0

        for i in range(len1):
            start = max(0, i - match_window)
            end = min(i + match_window + 1, len2)

            for j in range(start, end):
                if str2_matches[j] or str1[i] != str2[j]:
                    continue
                str1_matches[i] = True
                str2_matches[j] = True
                matches += 1
                break

        if matches == 0:
            return 0.0

        k = 0
        for i in range(len1):
            if not str1_matches[i]:
                continue
            while not str2_matches[k]:
                k += 1
            if str1[i] != str2[k]:
                transpositions += 1
            k += 1

        jaro = (
            matches / len1
            + matches / len2
            + (matches - transpositions / 2) / matches
        ) / 3.0

        # Winkler modification
        prefix_len = 0
        for i in range(min(len1, len2, 4)):
            if str1[i] == str2[i]:
                prefix_len += 1
            else:
                break

        winkler = jaro + (0.1 * prefix_len * (1 - jaro))
        return winkler

    def _calculate_similarity(
        self, str1: str, str2: str, algorithm: str = "sequence"
    ) -> float:
        """Calculate similarity using specified algorithm.

        Args:
            str1: First string.
            str2: Second string.
            algorithm: Algorithm to use ('sequence', 'levenshtein', 'jaro_winkler').

        Returns:
            Similarity ratio between 0.0 and 1.0.
        """
        if algorithm == "sequence":
            return self._sequence_similarity(str1, str2)
        elif algorithm == "levenshtein":
            return self._levenshtein_similarity(str1, str2)
        elif algorithm == "jaro_winkler":
            return self._jaro_winkler_similarity(str1, str2)
        else:
            logger.warning(f"Unknown algorithm: {algorithm}, using sequence")
            return self._sequence_similarity(str1, str2)

    def _extract_filename_parts(self, file_path: Path) -> Dict[str, str]:
        """Extract filename parts for comparison.

        Args:
            file_path: Path to file.

        Returns:
            Dictionary with filename parts.
        """
        name = file_path.stem
        extension = file_path.suffix
        full_name = file_path.name

        return {
            "full_name": full_name,
            "name": name,
            "extension": extension,
            "path": str(file_path),
        }

    def scan_directory(self, directory: str) -> None:
        """Scan directory and collect file information.

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

        self.files = []
        self.similar_pairs = []
        self.stats = {
            "files_scanned": 0,
            "similar_pairs_found": 0,
            "directories_scanned": 0,
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

                self.stats["directories_scanned"] += 1

                for file_name in files:
                    file_path = root_path / file_name

                    if self._should_skip_path(file_path):
                        continue

                    try:
                        file_info = self._extract_filename_parts(file_path)
                        file_info["size"] = file_path.stat().st_size
                        self.files.append(file_info)
                        self.stats["files_scanned"] += 1
                    except (OSError, PermissionError) as e:
                        logger.warning(
                            f"Cannot access file {file_path}: {e}",
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
            f"Scan completed: {self.stats['files_scanned']} files found",
            extra=self.stats,
        )

    def find_similar_files(self) -> None:
        """Find files with similar names using configured algorithm."""
        algorithm = self.config.get("similarity", {}).get(
            "algorithm", "sequence"
        )
        threshold = self.config.get("similarity", {}).get("threshold", 0.8)
        compare_by = self.config.get("similarity", {}).get(
            "compare_by", "name"
        )

        logger.info(
            f"Finding similar files using {algorithm} algorithm "
            f"(threshold: {threshold})"
        )

        self.similar_pairs = []

        for i in range(len(self.files)):
            for j in range(i + 1, len(self.files)):
                file1 = self.files[i]
                file2 = self.files[j]

                # Determine what to compare
                if compare_by == "name":
                    str1 = file1["name"]
                    str2 = file2["name"]
                elif compare_by == "full_name":
                    str1 = file1["full_name"]
                    str2 = file2["full_name"]
                else:
                    str1 = file1["name"]
                    str2 = file2["name"]

                # Calculate similarity
                similarity = self._calculate_similarity(str1, str2, algorithm)

                if similarity >= threshold:
                    self.similar_pairs.append(
                        {
                            "file1": file1["path"],
                            "file2": file2["path"],
                            "name1": file1["name"],
                            "name2": file2["name"],
                            "similarity": similarity,
                            "algorithm": algorithm,
                        }
                    )

        # Sort by similarity (highest first)
        self.similar_pairs.sort(key=lambda x: x["similarity"], reverse=True)

        self.stats["similar_pairs_found"] = len(self.similar_pairs)

        logger.info(
            f"Found {len(self.similar_pairs)} similar file pairs",
            extra={"similar_pairs": len(self.similar_pairs)},
        )

    def generate_report(self, output_path: Optional[str] = None) -> str:
        """Generate report of similar files.

        Args:
            output_path: Optional path to save report file. If None,
                uses default from config.

        Returns:
            Report content as string.
        """
        report_config = self.config.get("report", {})
        default_output = report_config.get(
            "output_file", "similar_files_report.txt"
        )

        output_file = output_path or default_output

        report_lines = [
            "=" * 80,
            "SIMILAR FILES REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY",
            "-" * 80,
            f"Files scanned: {self.stats['files_scanned']:,}",
            f"Directories scanned: {self.stats['directories_scanned']:,}",
            f"Similar pairs found: {self.stats['similar_pairs_found']:,}",
            f"Errors encountered: {self.stats['errors']}",
            "",
            "SIMILAR FILE PAIRS",
            "-" * 80,
        ]

        if not self.similar_pairs:
            report_lines.append("No similar files found.")
        else:
            for pair in self.similar_pairs:
                report_lines.extend(
                    [
                        f"Similarity: {pair['similarity']:.3f} "
                        f"({pair['algorithm']})",
                        f"  File 1: {pair['file1']}",
                        f"  Name:   {pair['name1']}",
                        f"  File 2: {pair['file2']}",
                        f"  Name:   {pair['name2']}",
                        "",
                    ]
                )

        report_content = "\n".join(report_lines)

        # Save report to file
        try:
            output_path_obj = Path(output_file)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path_obj, "w", encoding="utf-8") as f:
                f.write(report_content)
            logger.info(
                f"Report saved to {output_file}",
                extra={"output_file": output_file},
            )
        except (IOError, PermissionError) as e:
            logger.error(
                f"Failed to save report to {output_file}: {e}",
                extra={"output_file": output_file},
            )
            raise

        return report_content


def main() -> None:
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Find files with similar names using string similarity "
        "algorithms"
    )
    parser.add_argument(
        "directory",
        help="Directory to scan for similar files",
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
        help="Output path for report (overrides config)",
    )

    args = parser.parse_args()

    try:
        finder = SimilarFileFinder(config_path=args.config)
        finder.scan_directory(args.directory)
        finder.find_similar_files()
        finder.generate_report(output_path=args.output)

        print(
            f"\nScan complete. Found {finder.stats['similar_pairs_found']} "
            f"similar file pairs from {finder.stats['files_scanned']} files."
        )

    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
