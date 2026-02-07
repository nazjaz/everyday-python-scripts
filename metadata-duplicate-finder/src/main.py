"""Metadata Duplicate Finder.

A Python script that identifies files with duplicate metadata like identical
EXIF data, creation dates, or other attributes, grouping related files.
"""

import argparse
import hashlib
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/finder.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL/Pillow not available. EXIF extraction disabled.")


class MetadataDuplicateFinder:
    """Finds files with duplicate metadata."""

    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp"}

    def __init__(
        self,
        check_exif: bool = True,
        check_dates: bool = True,
        check_size: bool = False,
        check_filename: bool = False,
        similarity_threshold: float = 1.0,
    ) -> None:
        """Initialize the metadata duplicate finder.

        Args:
            check_exif: If True, check EXIF data for duplicates
            check_dates: If True, check creation/modification dates
            check_size: If True, check file sizes
            check_filename: If True, check similar filenames
            similarity_threshold: Threshold for similarity matching (0.0-1.0)
        """
        self.check_exif = check_exif and PIL_AVAILABLE
        self.check_dates = check_dates
        self.check_size = check_size
        self.check_filename = check_filename
        self.similarity_threshold = similarity_threshold

        self.stats = {
            "files_processed": 0,
            "files_with_exif": 0,
            "duplicate_groups": 0,
            "total_duplicates": 0,
            "errors": 0,
        }

    def _extract_exif_data(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Extract EXIF data from image file.

        Args:
            file_path: Path to image file

        Returns:
            Dictionary of EXIF data or None if not available
        """
        if not self.check_exif:
            return None

        if file_path.suffix.lower() not in self.IMAGE_EXTENSIONS:
            return None

        try:
            with Image.open(file_path) as img:
                exif_data = img._getexif()
                if not exif_data:
                    return None

                exif_dict = {}
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if isinstance(value, (str, int, float, tuple)):
                        exif_dict[tag] = value

                return exif_dict

        except Exception as e:
            logger.debug(f"Error extracting EXIF from {file_path}: {e}")
            return None

    def _extract_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract file system metadata.

        Args:
            file_path: Path to file

        Returns:
            Dictionary of file metadata
        """
        metadata: Dict[str, Any] = {
            "path": str(file_path),
            "name": file_path.name,
            "size": file_path.stat().st_size if file_path.exists() else 0,
        }

        try:
            stat = file_path.stat()
            metadata["created"] = datetime.fromtimestamp(stat.st_ctime).isoformat()
            metadata["modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            metadata["size"] = stat.st_size
        except (OSError, PermissionError) as e:
            logger.warning(f"Cannot access metadata for {file_path}: {e}")
            self.stats["errors"] += 1

        if self.check_exif:
            exif_data = self._extract_exif_data(file_path)
            if exif_data:
                metadata["exif"] = exif_data
                self.stats["files_with_exif"] += 1

        return metadata

    def _create_metadata_signature(self, metadata: Dict[str, Any]) -> str:
        """Create a signature from metadata for comparison.

        Args:
            metadata: File metadata dictionary

        Returns:
            String signature representing the metadata
        """
        signature_parts = []

        if self.check_exif and "exif" in metadata:
            exif = metadata["exif"]
            exif_keys = sorted(exif.keys())
            exif_values = [str(exif.get(k, "")) for k in exif_keys]
            signature_parts.append(f"exif:{':'.join(exif_values)}")

        if self.check_dates:
            created = metadata.get("created", "")
            modified = metadata.get("modified", "")
            signature_parts.append(f"dates:{created}:{modified}")

        if self.check_size:
            size = metadata.get("size", 0)
            signature_parts.append(f"size:{size}")

        if self.check_filename:
            name = metadata.get("name", "")
            signature_parts.append(f"name:{name}")

        return "|".join(signature_parts)

    def _calculate_similarity(self, sig1: str, sig2: str) -> float:
        """Calculate similarity between two metadata signatures.

        Args:
            sig1: First metadata signature
            sig2: Second metadata signature

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if sig1 == sig2:
            return 1.0

        parts1 = set(sig1.split("|"))
        parts2 = set(sig2.split("|"))

        if not parts1 or not parts2:
            return 0.0

        intersection = parts1.intersection(parts2)
        union = parts1.union(parts2)

        return len(intersection) / len(union) if union else 0.0

    def find_duplicates(
        self, file_paths: List[Path], recursive: bool = False
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Find files with duplicate metadata.

        Args:
            file_paths: List of file paths or directory paths
            recursive: If True, recursively scan directories

        Returns:
            Dictionary mapping signature to list of file metadata
        """
        all_files: List[Path] = []

        for path in file_paths:
            path = Path(path).expanduser().resolve()

            if path.is_file():
                all_files.append(path)
            elif path.is_dir():
                if recursive:
                    all_files.extend(path.rglob("*"))
                else:
                    all_files.extend(path.glob("*"))

        logger.info(f"Found {len(all_files)} files to process")

        metadata_list: List[Dict[str, Any]] = []
        signature_to_files: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for file_path in all_files:
            if not file_path.is_file():
                continue

            try:
                metadata = self._extract_file_metadata(file_path)
                signature = self._create_metadata_signature(metadata)

                if signature:
                    signature_to_files[signature].append(metadata)
                    metadata_list.append(metadata)

                self.stats["files_processed"] += 1

            except Exception as e:
                logger.warning(f"Error processing {file_path}: {e}")
                self.stats["errors"] += 1

        duplicate_groups = {
            sig: files
            for sig, files in signature_to_files.items()
            if len(files) > 1
        }

        self.stats["duplicate_groups"] = len(duplicate_groups)
        self.stats["total_duplicates"] = sum(
            len(files) - 1 for files in duplicate_groups.values()
        )

        return duplicate_groups

    def find_similar_metadata(
        self, file_paths: List[Path], recursive: bool = False
    ) -> List[Tuple[Dict[str, Any], Dict[str, Any], float]]:
        """Find files with similar metadata.

        Args:
            file_paths: List of file paths or directory paths
            recursive: If True, recursively scan directories

        Returns:
            List of tuples (file1_metadata, file2_metadata, similarity_score)
        """
        all_files: List[Path] = []

        for path in file_paths:
            path = Path(path).expanduser().resolve()

            if path.is_file():
                all_files.append(path)
            elif path.is_dir():
                if recursive:
                    all_files.extend(path.rglob("*"))
                else:
                    all_files.extend(path.glob("*"))

        metadata_list: List[Dict[str, Any]] = []

        for file_path in all_files:
            if not file_path.is_file():
                continue

            try:
                metadata = self._extract_file_metadata(file_path)
                signature = self._create_metadata_signature(metadata)

                if signature:
                    metadata["_signature"] = signature
                    metadata_list.append(metadata)

                self.stats["files_processed"] += 1

            except Exception as e:
                logger.warning(f"Error processing {file_path}: {e}")
                self.stats["errors"] += 1

        similar_pairs: List[Tuple[Dict[str, Any], Dict[str, Any], float]] = []

        for i, metadata1 in enumerate(metadata_list):
            for metadata2 in metadata_list[i + 1 :]:
                sig1 = metadata1.get("_signature", "")
                sig2 = metadata2.get("_signature", "")

                similarity = self._calculate_similarity(sig1, sig2)

                if similarity >= self.similarity_threshold:
                    similar_pairs.append((metadata1, metadata2, similarity))

        return similar_pairs

    def format_report(
        self, duplicate_groups: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """Format duplicate groups as a report.

        Args:
            duplicate_groups: Dictionary of duplicate groups

        Returns:
            Formatted string report
        """
        if not duplicate_groups:
            return "No duplicate metadata found."

        lines = [
            "Metadata Duplicate Report",
            "=" * 80,
            "",
            f"Files processed: {self.stats['files_processed']}",
            f"Files with EXIF: {self.stats['files_with_exif']}",
            f"Duplicate groups: {self.stats['duplicate_groups']}",
            f"Total duplicates: {self.stats['total_duplicates']}",
            f"Errors: {self.stats['errors']}",
            "",
            "-" * 80,
            "",
        ]

        for group_id, files in enumerate(duplicate_groups.values(), start=1):
            lines.append(f"Group {group_id}: {len(files)} files with identical metadata")
            lines.append("")

            for file_metadata in files:
                lines.append(f"  File: {file_metadata['path']}")
                lines.append(f"    Size: {file_metadata.get('size', 0):,} bytes")
                lines.append(f"    Created: {file_metadata.get('created', 'Unknown')}")
                lines.append(f"    Modified: {file_metadata.get('modified', 'Unknown')}")

                if "exif" in file_metadata:
                    exif = file_metadata["exif"]
                    if "DateTime" in exif:
                        lines.append(f"    EXIF DateTime: {exif['DateTime']}")
                    if "Make" in exif:
                        lines.append(f"    EXIF Make: {exif['Make']}")
                    if "Model" in exif:
                        lines.append(f"    EXIF Model: {exif['Model']}")

                lines.append("")

            lines.append("-" * 80)
            lines.append("")

        return "\n".join(lines)

    def format_similarity_report(
        self, similar_pairs: List[Tuple[Dict[str, Any], Dict[str, Any], float]]
    ) -> str:
        """Format similarity pairs as a report.

        Args:
            similar_pairs: List of similar file pairs

        Returns:
            Formatted string report
        """
        if not similar_pairs:
            return "No similar metadata found."

        lines = [
            "Metadata Similarity Report",
            "=" * 80,
            "",
            f"Files processed: {self.stats['files_processed']}",
            f"Similar pairs: {len(similar_pairs)}",
            f"Similarity threshold: {self.similarity_threshold}",
            "",
            "-" * 80,
            "",
        ]

        for file1, file2, similarity in similar_pairs:
            lines.append(f"Similarity: {similarity:.2%}")
            lines.append(f"  File 1: {file1['path']}")
            lines.append(f"  File 2: {file2['path']}")
            lines.append("")

        return "\n".join(lines)


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Dictionary containing configuration values

    Raises:
        FileNotFoundError: If config file does not exist
        yaml.YAMLError: If config file is invalid YAML
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config if config else {}
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in config file: {e}")
        raise


def main() -> int:
    """Main entry point for the script.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        description="Find files with duplicate metadata"
    )
    parser.add_argument(
        "paths",
        type=str,
        nargs="+",
        help="File paths or directory paths to scan",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively scan directories",
    )
    parser.add_argument(
        "--check-exif",
        action="store_true",
        default=True,
        help="Check EXIF data for duplicates (default: True)",
    )
    parser.add_argument(
        "--no-exif",
        action="store_true",
        help="Disable EXIF checking",
    )
    parser.add_argument(
        "--check-dates",
        action="store_true",
        default=True,
        help="Check creation/modification dates (default: True)",
    )
    parser.add_argument(
        "--check-size",
        action="store_true",
        help="Check file sizes",
    )
    parser.add_argument(
        "--check-filename",
        action="store_true",
        help="Check similar filenames",
    )
    parser.add_argument(
        "--similarity",
        action="store_true",
        help="Find similar metadata instead of exact duplicates",
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.8,
        help="Similarity threshold for matching (0.0-1.0, default: 0.8)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path for report",
    )
    parser.add_argument(
        "--json",
        type=str,
        default=None,
        help="Output JSON file path for results",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file (YAML)",
    )

    args = parser.parse_args()

    try:
        check_exif = args.check_exif and not args.no_exif
        check_dates = args.check_dates
        check_size = args.check_size
        check_filename = args.check_filename
        similarity_mode = args.similarity
        similarity_threshold = args.similarity_threshold
        recursive = args.recursive

        if args.config:
            config = load_config(Path(args.config))
            if "check_exif" in config:
                check_exif = config["check_exif"]
            if "check_dates" in config:
                check_dates = config["check_dates"]
            if "check_size" in config:
                check_size = config["check_size"]
            if "check_filename" in config:
                check_filename = config["check_filename"]
            if "similarity_threshold" in config:
                similarity_threshold = config["similarity_threshold"]
            if "recursive" in config:
                recursive = config["recursive"]

        finder = MetadataDuplicateFinder(
            check_exif=check_exif,
            check_dates=check_dates,
            check_size=check_size,
            check_filename=check_filename,
            similarity_threshold=similarity_threshold,
        )

        file_paths = [Path(p) for p in args.paths]

        if similarity_mode:
            similar_pairs = finder.find_similar_metadata(file_paths, recursive=recursive)
            report = finder.format_similarity_report(similar_pairs)

            if args.json:
                json_data = [
                    {
                        "file1": pair[0]["path"],
                        "file2": pair[1]["path"],
                        "similarity": pair[2],
                    }
                    for pair in similar_pairs
                ]
                with open(args.json, "w") as f:
                    json.dump(json_data, f, indent=2)
        else:
            duplicate_groups = finder.find_duplicates(file_paths, recursive=recursive)
            report = finder.format_report(duplicate_groups)

            if args.json:
                json_data = {
                    "groups": [
                        {
                            "signature": sig,
                            "files": [
                                {
                                    "path": f["path"],
                                    "size": f.get("size", 0),
                                    "created": f.get("created"),
                                    "modified": f.get("modified"),
                                    "exif": f.get("exif"),
                                }
                                for f in files
                            ],
                        }
                        for sig, files in duplicate_groups.items()
                    ]
                }
                with open(args.json, "w") as f:
                    json.dump(json_data, f, indent=2, default=str)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(report)
            logger.info(f"Report saved to {output_path}")
        else:
            print(report)

        return 0

    except (ValueError, FileNotFoundError) as e:
        logger.error(f"Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
