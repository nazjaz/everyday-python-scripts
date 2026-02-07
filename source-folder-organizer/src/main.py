"""Source Folder Organizer.

A Python script that organizes files by their source folder, maintaining
a mapping of original locations when moving files to organized structures.
"""

import argparse
import hashlib
import json
import logging
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/organizer.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


class SourceFolderOrganizer:
    """Organizes files by source folder with location mapping."""

    def __init__(
        self,
        source_folders: List[Path],
        destination_root: Path,
        mapping_file: Path,
        dry_run: bool = False,
        handle_duplicates: str = "skip",
    ) -> None:
        """Initialize the organizer with configuration.

        Args:
            source_folders: List of source folder paths to organize
            destination_root: Root directory for organized file structure
            mapping_file: Path to JSON file storing original location mappings
            dry_run: If True, simulate operations without moving files
            handle_duplicates: How to handle duplicates: "skip", "rename", "overwrite"

        Raises:
            ValueError: If handle_duplicates value is invalid
        """
        if handle_duplicates not in ["skip", "rename", "overwrite"]:
            raise ValueError(
                "handle_duplicates must be one of: skip, rename, overwrite"
            )

        self.source_folders = [Path(f).expanduser().resolve() for f in source_folders]
        self.destination_root = Path(destination_root).expanduser().resolve()
        self.mapping_file = Path(mapping_file).expanduser().resolve()
        self.dry_run = dry_run
        self.handle_duplicates = handle_duplicates

        self.location_mapping: Dict[str, str] = {}
        self.processed_files: List[str] = []
        self.duplicate_files: List[str] = []
        self.error_files: List[Tuple[str, str]] = []

        self._validate_paths()
        self._load_mapping()

    def _validate_paths(self) -> None:
        """Validate that source folders exist and destination is writable.

        Raises:
            FileNotFoundError: If source folder does not exist
            PermissionError: If destination is not writable
        """
        for source_folder in self.source_folders:
            if not source_folder.exists():
                raise FileNotFoundError(f"Source folder does not exist: {source_folder}")
            if not source_folder.is_dir():
                raise NotADirectoryError(
                    f"Source path is not a directory: {source_folder}"
                )

        self.destination_root.mkdir(parents=True, exist_ok=True)

        if not self.destination_root.is_dir():
            raise NotADirectoryError(
                f"Destination root is not a directory: {self.destination_root}"
            )

        try:
            test_file = self.destination_root / ".write_test"
            test_file.touch()
            test_file.unlink()
        except (PermissionError, OSError) as e:
            raise PermissionError(
                f"Destination root is not writable: {self.destination_root}"
            ) from e

    def _load_mapping(self) -> None:
        """Load existing location mapping from file."""
        if self.mapping_file.exists():
            try:
                with open(self.mapping_file, "r") as f:
                    self.location_mapping = json.load(f)
                logger.info(
                    f"Loaded {len(self.location_mapping)} existing mappings",
                    extra={"mapping_count": len(self.location_mapping)},
                )
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(
                    f"Could not load mapping file: {e}. Starting with empty mapping."
                )
                self.location_mapping = {}

    def _save_mapping(self) -> None:
        """Save location mapping to file."""
        self.mapping_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.mapping_file, "w") as f:
                json.dump(self.location_mapping, f, indent=2)
            logger.info(
                f"Saved {len(self.location_mapping)} mappings to {self.mapping_file}"
            )
        except (IOError, OSError) as e:
            logger.error(f"Failed to save mapping file: {e}")

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file for duplicate detection.

        Args:
            file_path: Path to file to hash

        Returns:
            Hexadecimal hash string

        Raises:
            IOError: If file cannot be read
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except IOError as e:
            raise IOError(f"Cannot read file for hashing: {file_path}") from e

    def _get_organized_path(self, source_file: Path, source_folder: Path) -> Path:
        """Generate organized destination path based on source folder.

        Args:
            source_file: Path to source file
            source_folder: Source folder containing the file

        Returns:
            Destination path for organized file
        """
        relative_path = source_file.relative_to(source_folder)
        source_folder_name = source_folder.name

        destination_path = (
            self.destination_root / source_folder_name / relative_path
        )

        return destination_path

    def _handle_duplicate(
        self, source_file: Path, destination_path: Path
    ) -> Optional[Path]:
        """Handle duplicate file at destination.

        Args:
            source_file: Source file path
            destination_path: Intended destination path

        Returns:
            Final destination path, or None if duplicate should be skipped
        """
        if not destination_path.exists():
            return destination_path

        source_hash = self._calculate_file_hash(source_file)
        dest_hash = self._calculate_file_hash(destination_path)

        if source_hash == dest_hash:
            logger.info(
                f"Duplicate file detected (same content): {source_file}",
                extra={"source": str(source_file), "destination": str(destination_path)},
            )
            self.duplicate_files.append(str(source_file))

            if self.handle_duplicates == "skip":
                return None
            elif self.handle_duplicates == "overwrite":
                return destination_path
            elif self.handle_duplicates == "rename":
                counter = 1
                while destination_path.exists():
                    stem = destination_path.stem
                    suffix = destination_path.suffix
                    parent = destination_path.parent
                    destination_path = parent / f"{stem}_copy{counter}{suffix}"
                    counter += 1
                return destination_path

        logger.warning(
            f"File exists at destination with different content: {destination_path}",
            extra={"source": str(source_file), "destination": str(destination_path)},
        )

        if self.handle_duplicates == "rename":
            counter = 1
            while destination_path.exists():
                stem = destination_path.stem
                suffix = destination_path.suffix
                parent = destination_path.parent
                destination_path = parent / f"{stem}_copy{counter}{suffix}"
                counter += 1
            return destination_path

        return None

    def _move_file(self, source_file: Path, destination_path: Path) -> bool:
        """Move file from source to destination.

        Args:
            source_file: Source file path
            destination_path: Destination file path

        Returns:
            True if move was successful, False otherwise
        """
        try:
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            if self.dry_run:
                logger.info(
                    f"[DRY RUN] Would move: {source_file} -> {destination_path}",
                    extra={
                        "source": str(source_file),
                        "destination": str(destination_path),
                    },
                )
                return True

            shutil.move(str(source_file), str(destination_path))
            logger.info(
                f"Moved file: {source_file} -> {destination_path}",
                extra={
                    "source": str(source_file),
                    "destination": str(destination_path),
                },
            )
            return True

        except (shutil.Error, OSError, PermissionError) as e:
            error_msg = f"Failed to move {source_file}: {e}"
            logger.error(error_msg, extra={"source": str(source_file), "error": str(e)})
            self.error_files.append((str(source_file), str(e)))
            return False

    def organize_files(self) -> Dict[str, int]:
        """Organize all files from source folders.

        Returns:
            Dictionary with statistics:
                - processed: Number of files processed
                - moved: Number of files successfully moved
                - duplicates: Number of duplicate files
                - errors: Number of files with errors
        """
        stats = {
            "processed": 0,
            "moved": 0,
            "duplicates": 0,
            "errors": 0,
        }

        logger.info(
            f"Starting organization of {len(self.source_folders)} source folder(s)",
            extra={"source_folders": [str(f) for f in self.source_folders]},
        )

        for source_folder in self.source_folders:
            logger.info(f"Processing source folder: {source_folder}")

            for file_path in source_folder.rglob("*"):
                if not file_path.is_file():
                    continue

                stats["processed"] += 1
                source_str = str(file_path)

                try:
                    destination_path = self._get_organized_path(file_path, source_folder)

                    final_destination = self._handle_duplicate(file_path, destination_path)

                    if final_destination is None:
                        stats["duplicates"] += 1
                        continue

                    if self._move_file(file_path, final_destination):
                        stats["moved"] += 1
                        self.location_mapping[str(final_destination)] = source_str
                        self.processed_files.append(source_str)
                    else:
                        stats["errors"] += 1

                except Exception as e:
                    stats["errors"] += 1
                    error_msg = f"Unexpected error processing {file_path}: {e}"
                    logger.exception(error_msg, extra={"file": str(file_path)})
                    self.error_files.append((source_str, str(e)))

        self._save_mapping()

        logger.info(
            "Organization complete",
            extra={
                "processed": stats["processed"],
                "moved": stats["moved"],
                "duplicates": stats["duplicates"],
                "errors": stats["errors"],
            },
        )

        return stats

    def get_mapping_report(self) -> str:
        """Generate a report of the location mapping.

        Returns:
            Formatted string report
        """
        if not self.location_mapping:
            return "No location mappings found."

        report_lines = [f"Location Mapping Report ({len(self.location_mapping)} entries)"]
        report_lines.append("=" * 80)
        report_lines.append("")

        for destination, original in sorted(self.location_mapping.items()):
            report_lines.append(f"Original: {original}")
            report_lines.append(f"  -> Organized: {destination}")
            report_lines.append("")

        return "\n".join(report_lines)


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
        description="Organize files by source folder with location mapping"
    )
    parser.add_argument(
        "--source-folders",
        type=str,
        nargs="+",
        required=True,
        help="Source folder paths to organize (space-separated)",
    )
    parser.add_argument(
        "--destination",
        type=str,
        required=True,
        help="Root directory for organized file structure",
    )
    parser.add_argument(
        "--mapping-file",
        type=str,
        default="location_mapping.json",
        help="Path to JSON file storing location mappings",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate operations without moving files",
    )
    parser.add_argument(
        "--handle-duplicates",
        type=str,
        choices=["skip", "rename", "overwrite"],
        default="skip",
        help="How to handle duplicate files (default: skip)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file (YAML)",
    )
    parser.add_argument(
        "--report",
        type=str,
        default=None,
        help="Output file path for mapping report",
    )

    args = parser.parse_args()

    try:
        source_folders = [Path(f) for f in args.source_folders]
        destination = Path(args.destination)
        mapping_file = Path(args.mapping_file)

        if args.config:
            config = load_config(Path(args.config))
            if "source_folders" in config:
                source_folders = [Path(f) for f in config["source_folders"]]
            if "destination" in config:
                destination = Path(config["destination"])
            if "mapping_file" in config:
                mapping_file = Path(config["mapping_file"])
            if "handle_duplicates" in config:
                args.handle_duplicates = config["handle_duplicates"]

        organizer = SourceFolderOrganizer(
            source_folders=source_folders,
            destination_root=destination,
            mapping_file=mapping_file,
            dry_run=args.dry_run,
            handle_duplicates=args.handle_duplicates,
        )

        stats = organizer.organize_files()

        print("\nOrganization Statistics:")
        print(f"  Processed: {stats['processed']}")
        print(f"  Moved: {stats['moved']}")
        print(f"  Duplicates: {stats['duplicates']}")
        print(f"  Errors: {stats['errors']}")

        if args.report:
            report = organizer.get_mapping_report()
            report_path = Path(args.report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, "w") as f:
                f.write(report)
            print(f"\nMapping report saved to: {report_path}")
        else:
            print("\n" + organizer.get_mapping_report())

        return 0

    except (
        ValueError,
        FileNotFoundError,
        NotADirectoryError,
        PermissionError,
    ) as e:
        logger.error(f"Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
