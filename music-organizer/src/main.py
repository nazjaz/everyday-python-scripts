"""Music Organizer - Organize music files by ID3 tags.

This module provides functionality to organize music files by reading ID3
tags, creating folder structures like Artist/Album/Track, and renaming
files with track numbers. Supports multiple audio formats and includes
comprehensive logging and duplicate handling.
"""

import logging
import logging.handlers
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv
from mutagen import File as MutagenFile
from mutagen.id3 import ID3NoHeaderError

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class MusicOrganizer:
    """Organizes music files by reading ID3 tags and creating folder structures."""

    # Supported audio file extensions
    SUPPORTED_EXTENSIONS = {
        ".mp3",
        ".flac",
        ".ogg",
        ".m4a",
        ".aac",
        ".wma",
        ".wav",
        ".opus",
    }

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize MusicOrganizer with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_directories()
        self.stats = {
            "files_scanned": 0,
            "files_organized": 0,
            "files_skipped": 0,
            "errors": 0,
            "errors_list": [],
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
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}"
            )

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Override with environment variables if present
        if os.getenv("SOURCE_DIRECTORY"):
            config["source_directory"] = os.getenv("SOURCE_DIRECTORY")
        if os.getenv("DESTINATION_DIRECTORY"):
            config["destination_directory"] = os.getenv("DESTINATION_DIRECTORY")
        if os.getenv("DRY_RUN"):
            config["operations"]["dry_run"] = (
                os.getenv("DRY_RUN").lower() == "true"
            )

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/music_organizer.log")

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

    def _setup_directories(self) -> None:
        """Set up source and destination directories."""
        self.source_dir = Path(
            os.path.expanduser(self.config["source_directory"])
        )
        self.dest_dir = Path(
            os.path.expanduser(self.config["destination_directory"])
        )

        if not self.source_dir.exists():
            raise FileNotFoundError(
                f"Source directory does not exist: {self.source_dir}"
            )

        if self.config["operations"]["create_destination"]:
            self.dest_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Source directory: {self.source_dir}")
        logger.info(f"Destination directory: {self.dest_dir}")

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility.

        Args:
            filename: Original filename.

        Returns:
            Sanitized filename safe for filesystem.
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")

        # Remove leading/trailing spaces and dots
        filename = filename.strip(" .")

        # Limit length
        max_length = self.config.get("max_filename_length", 255)
        if len(filename) > max_length:
            filename = filename[:max_length]

        return filename

    def _read_id3_tags(self, file_path: Path) -> Dict[str, Optional[str]]:
        """Read ID3 tags from music file.

        Args:
            file_path: Path to music file.

        Returns:
            Dictionary with tag information (artist, album, track, title).
        """
        tags = {
            "artist": None,
            "album": None,
            "track": None,
            "title": None,
        }

        try:
            audio_file = MutagenFile(file_path)

            if audio_file is None:
                logger.warning(f"Could not read tags from {file_path}")
                return tags

            # Try common tag keys
            tag_mappings = {
                "artist": ["TPE1", "ARTIST", "\xa9ART", "Author"],
                "album": ["TALB", "ALBUM", "\xa9alb"],
                "track": ["TRCK", "TRACKNUMBER", "TRACK", "trkn"],
                "title": ["TIT2", "TITLE", "\xa9nam", "Title"],
            }

            for tag_name, possible_keys in tag_mappings.items():
                for key in possible_keys:
                    if key in audio_file:
                        value = audio_file[key]
                        if isinstance(value, list) and len(value) > 0:
                            tags[tag_name] = str(value[0])
                        elif hasattr(value, "text") and len(value.text) > 0:
                            tags[tag_name] = str(value.text[0])
                        elif isinstance(value, str):
                            tags[tag_name] = value
                        break

            # Handle track number - extract number from string if needed
            if tags["track"]:
                track_str = str(tags["track"])
                # Extract first number found (e.g., "1/12" -> "1")
                if "/" in track_str:
                    tags["track"] = track_str.split("/")[0].strip()
                # Remove non-numeric characters
                track_num = "".join(filter(str.isdigit, track_str))
                if track_num:
                    tags["track"] = track_num.zfill(2)  # Zero-pad to 2 digits

        except ID3NoHeaderError:
            logger.debug(f"No ID3 header in {file_path}")
        except Exception as e:
            logger.warning(f"Error reading tags from {file_path}: {e}")

        return tags

    def _get_default_values(self, file_path: Path) -> Dict[str, str]:
        """Get default values for missing tags.

        Args:
            file_path: Path to music file.

        Returns:
            Dictionary with default values.
        """
        defaults = self.config.get("defaults", {})
        return {
            "artist": defaults.get("artist", "Unknown Artist"),
            "album": defaults.get("album", "Unknown Album"),
            "track": defaults.get("track", "00"),
            "title": defaults.get("title", file_path.stem),
        }

    def _build_destination_path(
        self, tags: Dict[str, Optional[str]], file_path: Path
    ) -> Tuple[Path, str]:
        """Build destination path and filename from tags.

        Args:
            tags: Dictionary with tag information.
            file_path: Original file path.

        Returns:
            Tuple of (destination_path, new_filename).
        """
        defaults = self._get_default_values(file_path)

        # Get values, using defaults if missing
        artist = self._sanitize_filename(
            tags.get("artist") or defaults["artist"]
        )
        album = self._sanitize_filename(tags.get("album") or defaults["album"])
        track_num = tags.get("track") or defaults["track"]
        title = self._sanitize_filename(tags.get("title") or defaults["title"])

        # Build folder structure: Artist/Album/
        folder_structure = self.config.get("folder_structure", "Artist/Album")
        folder_path = folder_structure.replace("Artist", artist).replace(
            "Album", album
        )

        dest_folder = self.dest_dir / folder_path

        # Build filename
        filename_format = self.config.get(
            "filename_format", "{track} - {title}{ext}"
        )
        file_ext = file_path.suffix

        new_filename = filename_format.format(
            track=track_num, title=title, ext=file_ext
        )
        new_filename = self._sanitize_filename(new_filename)

        dest_path = dest_folder / new_filename

        return dest_path, new_filename

    def _handle_duplicate(
        self, dest_path: Path, original_path: Path
    ) -> Optional[Path]:
        """Handle duplicate file names.

        Args:
            dest_path: Intended destination path.
            original_path: Original file path.

        Returns:
            Final destination path (may be modified if duplicate).
        """
        if not dest_path.exists():
            return dest_path

        action = self.config.get("duplicate_handling", "rename")

        if action == "skip":
            logger.info(f"Skipping duplicate: {dest_path.name}")
            self.stats["files_skipped"] += 1
            return None

        elif action == "rename":
            # Add counter to filename
            counter = 1
            stem = dest_path.stem
            suffix = dest_path.suffix
            parent = dest_path.parent

            while dest_path.exists():
                new_name = f"{stem}_{counter}{suffix}"
                dest_path = parent / new_name
                counter += 1

            logger.debug(f"Renamed duplicate to: {dest_path.name}")
            return dest_path

        elif action == "overwrite":
            logger.warning(f"Overwriting existing file: {dest_path}")
            return dest_path

        return dest_path

    def _organize_file(self, file_path: Path) -> bool:
        """Organize a single music file.

        Args:
            file_path: Path to music file to organize.

        Returns:
            True if successful, False otherwise.
        """
        self.stats["files_scanned"] += 1

        try:
            # Read ID3 tags
            tags = self._read_id3_tags(file_path)

            # Build destination path
            dest_path, new_filename = self._build_destination_path(
                tags, file_path
            )

            # Handle duplicates
            dest_path = self._handle_duplicate(dest_path, file_path)
            if dest_path is None:
                return False

            # Create destination directory
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Move or copy file
            if self.config["operations"]["dry_run"]:
                logger.info(
                    f"[DRY RUN] Would move: {file_path.name} -> "
                    f"{dest_path.relative_to(self.dest_dir)}"
                )
                self.stats["files_organized"] += 1
                return True

            if self.config["operations"]["method"] == "move":
                shutil.move(str(file_path), str(dest_path))
                logger.info(
                    f"Moved: {file_path.name} -> "
                    f"{dest_path.relative_to(self.dest_dir)}"
                )
            else:
                shutil.copy2(str(file_path), str(dest_path))
                logger.info(
                    f"Copied: {file_path.name} -> "
                    f"{dest_path.relative_to(self.dest_dir)}"
                )

            # Preserve timestamps
            if self.config["operations"]["preserve_timestamps"]:
                stat = file_path.stat()
                os.utime(dest_path, (stat.st_atime, stat.st_mtime))

            self.stats["files_organized"] += 1
            return True

        except Exception as e:
            error_msg = f"Error organizing {file_path}: {e}"
            logger.error(error_msg, exc_info=True)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            return False

    def _is_music_file(self, file_path: Path) -> bool:
        """Check if file is a supported music file.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file is a supported music format, False otherwise.
        """
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def organize_music(self) -> Dict[str, any]:
        """Organize all music files in source directory.

        Returns:
            Dictionary with statistics about the operation.
        """
        logger.info("Starting music organization")
        logger.info(f"Dry run mode: {self.config['operations']['dry_run']}")

        # Scan source directory
        music_files = []
        if self.config["operations"]["recursive"]:
            for file_path in self.source_dir.rglob("*"):
                if file_path.is_file() and self._is_music_file(file_path):
                    music_files.append(file_path)
        else:
            for file_path in self.source_dir.iterdir():
                if file_path.is_file() and self._is_music_file(file_path):
                    music_files.append(file_path)

        logger.info(f"Found {len(music_files)} music files to organize")

        # Organize each file
        for file_path in music_files:
            self._organize_file(file_path)

        logger.info("Music organization completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats


def main() -> int:
    """Main entry point for music organizer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Organize music files by reading ID3 tags and creating "
        "folder structures"
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
        help="Preview changes without moving files",
    )

    args = parser.parse_args()

    try:
        organizer = MusicOrganizer(config_path=args.config)

        if args.dry_run:
            organizer.config["operations"]["dry_run"] = True

        stats = organizer.organize_music()

        # Print summary
        print("\n" + "=" * 60)
        print("Music Organization Summary")
        print("=" * 60)
        print(f"Files Scanned: {stats['files_scanned']}")
        print(f"Files Organized: {stats['files_organized']}")
        print(f"Files Skipped: {stats['files_skipped']}")
        print(f"Errors: {stats['errors']}")

        if stats["errors_list"]:
            print("\nErrors:")
            for error in stats["errors_list"][:10]:
                print(f"  - {error}")
            if len(stats["errors_list"]) > 10:
                print(f"  ... and {len(stats['errors_list']) - 10} more")

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
