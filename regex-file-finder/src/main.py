"""Regex File Finder - Find files matching regex patterns.

This module provides functionality to find files matching regex patterns
in filenames or file content, with options to move, copy, or list matching files.
"""

import logging
import logging.handlers
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class RegexFileFinder:
    """Finds files matching regex patterns in names or content."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize RegexFileFinder with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.matched_files: List[Dict[str, Any]] = []
        self.stats = {
            "files_scanned": 0,
            "files_matched": 0,
            "files_moved": 0,
            "files_copied": 0,
            "errors": 0,
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
        if os.getenv("SEARCH_DIRECTORY"):
            config["search"]["directory"] = os.getenv("SEARCH_DIRECTORY")
        if os.getenv("OUTPUT_DIRECTORY"):
            config["operations"]["output_directory"] = os.getenv("OUTPUT_DIRECTORY")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/regex_finder.log")

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

    def _validate_path(self, path: Path) -> bool:
        """Validate that path exists and is accessible.

        Args:
            path: Path to validate.

        Returns:
            True if path is valid, False otherwise.
        """
        if not path.exists():
            logger.error(f"Path does not exist: {path}")
            return False

        if not path.is_dir() and not path.is_file():
            logger.error(f"Path is not a directory or file: {path}")
            return False

        return True

    def _is_excluded(self, file_path: Path) -> bool:
        """Check if file should be excluded from search.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file should be excluded, False otherwise.
        """
        exclude_config = self.config.get("search", {}).get("exclude", {})
        exclude_patterns = exclude_config.get("patterns", [])
        exclude_dirs = exclude_config.get("directories", [])
        exclude_extensions = exclude_config.get("extensions", [])

        # Check directory exclusion
        for exclude_dir in exclude_dirs:
            if exclude_dir in file_path.parts:
                return True

        # Check extension exclusion
        if exclude_extensions:
            file_ext = file_path.suffix.lower()
            if file_ext in [ext.lower() for ext in exclude_extensions]:
                return True

        # Check pattern exclusion
        file_str = str(file_path)
        for pattern in exclude_patterns:
            try:
                if re.search(pattern, file_str, re.IGNORECASE):
                    return True
            except re.error as e:
                logger.warning(f"Invalid exclude pattern '{pattern}': {e}")

        return False

    def _matches_name_pattern(self, file_path: Path, pattern: str) -> bool:
        """Check if filename matches regex pattern.

        Args:
            file_path: Path to file.
            pattern: Regex pattern to match.

        Returns:
            True if filename matches pattern, False otherwise.
        """
        try:
            flags = re.IGNORECASE if self.config.get("search", {}).get("case_sensitive", False) is False else 0
            if re.search(pattern, file_path.name, flags):
                return True
            # Also check full path if configured
            if self.config.get("search", {}).get("match_full_path", False):
                if re.search(pattern, str(file_path), flags):
                    return True
            return False
        except re.error as e:
            logger.error(f"Invalid regex pattern '{pattern}': {e}")
            self.stats["errors"] += 1
            return False

    def _matches_content_pattern(self, file_path: Path, pattern: str) -> bool:
        """Check if file content matches regex pattern.

        Args:
            file_path: Path to file.
            pattern: Regex pattern to match.

        Returns:
            True if content matches pattern, False otherwise.
        """
        if not file_path.is_file():
            return False

        # Check file size limit
        max_size = self.config.get("search", {}).get("max_file_size", 10485760)  # 10MB default
        try:
            if file_path.stat().st_size > max_size:
                logger.debug(f"File too large to search: {file_path}")
                return False
        except OSError as e:
            logger.warning(f"Could not get file size for {file_path}: {e}")
            return False

        # Check if file is binary
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(8192)
                if b"\x00" in chunk:
                    logger.debug(f"Skipping binary file: {file_path}")
                    return False
        except (OSError, PermissionError) as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return False

        # Try to read and search content
        try:
            encoding = self.config.get("search", {}).get("encoding", "utf-8")
            with open(file_path, "r", encoding=encoding, errors="ignore") as f:
                flags = re.IGNORECASE if self.config.get("search", {}).get("case_sensitive", False) is False else 0
                flags |= re.MULTILINE
                
                # Read in chunks for large files
                chunk_size = 8192
                buffer = ""
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    buffer += chunk
                    # Search in buffer
                    if re.search(pattern, buffer, flags):
                        return True
                    # Keep last part of buffer to handle matches across chunks
                    if len(buffer) > chunk_size:
                        buffer = buffer[-chunk_size:]

                # Final check
                if re.search(pattern, buffer, flags):
                    return True

        except (UnicodeDecodeError, PermissionError, OSError) as e:
            logger.debug(f"Could not search content of {file_path}: {e}")
            return False

        return False

    def find_files(
        self,
        pattern: str,
        search_directory: Optional[str] = None,
        search_in: str = "name",
        recursive: bool = True,
    ) -> List[Dict[str, Any]]:
        """Find files matching regex pattern.

        Args:
            pattern: Regex pattern to match.
            search_directory: Directory to search (overrides config).
            search_in: Where to search - "name", "content", or "both".
            recursive: Whether to search recursively.

        Returns:
            List of dictionaries with matched file information.

        Raises:
            ValueError: If search_in is invalid or pattern is empty.
            FileNotFoundError: If search directory doesn't exist.
        """
        if not pattern:
            raise ValueError("Pattern cannot be empty")

        valid_search_in = ["name", "content", "both"]
        if search_in not in valid_search_in:
            raise ValueError(f"search_in must be one of: {', '.join(valid_search_in)}")

        # Determine search directory
        if search_directory:
            search_dir = Path(search_directory)
        else:
            search_dir = Path(self.config.get("search", {}).get("directory", "."))

        if not self._validate_path(search_dir):
            raise FileNotFoundError(f"Search directory does not exist: {search_dir}")

        if not search_dir.is_dir():
            raise ValueError(f"Search path is not a directory: {search_dir}")

        logger.info(
            f"Searching for pattern '{pattern}' in {search_in} "
            f"starting from {search_dir}"
        )

        self.matched_files = []
        self.stats["files_scanned"] = 0
        self.stats["files_matched"] = 0

        # Compile pattern once for efficiency
        try:
            compiled_pattern = re.compile(pattern)
        except re.error as e:
            logger.error(f"Invalid regex pattern '{pattern}': {e}")
            raise ValueError(f"Invalid regex pattern: {e}")

        # Walk directory
        if recursive:
            iterator = search_dir.rglob("*")
        else:
            iterator = search_dir.glob("*")

        for item_path in iterator:
            if not item_path.is_file():
                continue

            self.stats["files_scanned"] += 1

            # Check exclusions
            if self._is_excluded(item_path):
                continue

            matched = False
            match_type = None

            # Search in name
            if search_in in ["name", "both"]:
                if self._matches_name_pattern(item_path, pattern):
                    matched = True
                    match_type = "name"

            # Search in content
            if not matched and search_in in ["content", "both"]:
                if self._matches_content_pattern(item_path, pattern):
                    matched = True
                    match_type = "content" if match_type is None else "both"

            if matched:
                try:
                    file_info = {
                        "path": str(item_path),
                        "name": item_path.name,
                        "size": item_path.stat().st_size,
                        "match_type": match_type,
                        "pattern": pattern,
                    }
                    self.matched_files.append(file_info)
                    self.stats["files_matched"] += 1
                    logger.debug(f"Matched: {item_path}")
                except OSError as e:
                    logger.warning(f"Could not get file info for {item_path}: {e}")
                    self.stats["errors"] += 1

        logger.info(
            f"Found {self.stats['files_matched']} matching file(s) "
            f"out of {self.stats['files_scanned']} scanned"
        )

        return self.matched_files

    def list_files(self, pattern: str, **kwargs) -> List[Dict[str, Any]]:
        """List files matching pattern (wrapper around find_files).

        Args:
            pattern: Regex pattern to match.
            **kwargs: Additional arguments passed to find_files.

        Returns:
            List of matched file information dictionaries.
        """
        return self.find_files(pattern, **kwargs)

    def copy_files(
        self,
        pattern: str,
        destination: Optional[str] = None,
        preserve_structure: bool = False,
        **kwargs,
    ) -> int:
        """Copy files matching pattern to destination.

        Args:
            pattern: Regex pattern to match.
            destination: Destination directory (overrides config).
            preserve_structure: Preserve directory structure in destination.
            **kwargs: Additional arguments passed to find_files.

        Returns:
            Number of files successfully copied.

        Raises:
            ValueError: If destination is not specified.
            FileNotFoundError: If destination directory doesn't exist.
        """
        matched_files = self.find_files(pattern, **kwargs)

        if not matched_files:
            logger.info("No files to copy")
            return 0

        # Determine destination
        if destination:
            dest_dir = Path(destination)
        else:
            dest_dir = Path(self.config.get("operations", {}).get("output_directory", "output"))

        if not dest_dir.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created destination directory: {dest_dir}")

        if not dest_dir.is_dir():
            raise ValueError(f"Destination is not a directory: {dest_dir}")

        copied_count = 0

        for file_info in matched_files:
            source_path = Path(file_info["path"])

            if preserve_structure:
                # Preserve relative path structure
                try:
                    # Get relative path from search directory
                    search_dir = kwargs.get("search_directory")
                    if search_dir:
                        rel_path = source_path.relative_to(Path(search_dir))
                    else:
                        search_dir = Path(self.config.get("search", {}).get("directory", "."))
                        try:
                            rel_path = source_path.relative_to(search_dir)
                        except ValueError:
                            rel_path = Path(source_path.name)
                    dest_path = dest_dir / rel_path
                except Exception as e:
                    logger.warning(f"Could not preserve structure for {source_path}: {e}")
                    dest_path = dest_dir / source_path.name
            else:
                dest_path = dest_dir / source_path.name

            # Handle duplicate names
            if dest_path.exists():
                if self.config.get("operations", {}).get("overwrite_existing", False):
                    logger.warning(f"Overwriting existing file: {dest_path}")
                else:
                    # Add suffix to avoid overwrite
                    counter = 1
                    base_name = dest_path.stem
                    extension = dest_path.suffix
                    while dest_path.exists():
                        dest_path = dest_dir / f"{base_name}_{counter}{extension}"
                        counter += 1
                    logger.debug(f"Renamed to avoid overwrite: {dest_path}")

            try:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, dest_path)
                copied_count += 1
                self.stats["files_copied"] += 1
                logger.info(f"Copied: {source_path} -> {dest_path}")
            except (OSError, PermissionError, shutil.Error) as e:
                logger.error(f"Error copying {source_path} to {dest_path}: {e}")
                self.stats["errors"] += 1

        logger.info(f"Copied {copied_count} file(s) to {dest_dir}")
        return copied_count

    def move_files(
        self,
        pattern: str,
        destination: Optional[str] = None,
        preserve_structure: bool = False,
        **kwargs,
    ) -> int:
        """Move files matching pattern to destination.

        Args:
            pattern: Regex pattern to match.
            destination: Destination directory (overrides config).
            preserve_structure: Preserve directory structure in destination.
            **kwargs: Additional arguments passed to find_files.

        Returns:
            Number of files successfully moved.

        Raises:
            ValueError: If destination is not specified.
            FileNotFoundError: If destination directory doesn't exist.
        """
        matched_files = self.find_files(pattern, **kwargs)

        if not matched_files:
            logger.info("No files to move")
            return 0

        # Determine destination
        if destination:
            dest_dir = Path(destination)
        else:
            dest_dir = Path(self.config.get("operations", {}).get("output_directory", "output"))

        if not dest_dir.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created destination directory: {dest_dir}")

        if not dest_dir.is_dir():
            raise ValueError(f"Destination is not a directory: {dest_dir}")

        moved_count = 0

        for file_info in matched_files:
            source_path = Path(file_info["path"])

            if preserve_structure:
                # Preserve relative path structure
                try:
                    search_dir = kwargs.get("search_directory")
                    if search_dir:
                        rel_path = source_path.relative_to(Path(search_dir))
                    else:
                        search_dir = Path(self.config.get("search", {}).get("directory", "."))
                        try:
                            rel_path = source_path.relative_to(search_dir)
                        except ValueError:
                            rel_path = Path(source_path.name)
                    dest_path = dest_dir / rel_path
                except Exception as e:
                    logger.warning(f"Could not preserve structure for {source_path}: {e}")
                    dest_path = dest_dir / source_path.name
            else:
                dest_path = dest_dir / source_path.name

            # Handle duplicate names
            if dest_path.exists():
                if self.config.get("operations", {}).get("overwrite_existing", False):
                    logger.warning(f"Overwriting existing file: {dest_path}")
                else:
                    counter = 1
                    base_name = dest_path.stem
                    extension = dest_path.suffix
                    while dest_path.exists():
                        dest_path = dest_dir / f"{base_name}_{counter}{extension}"
                        counter += 1
                    logger.debug(f"Renamed to avoid overwrite: {dest_path}")

            try:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source_path), str(dest_path))
                moved_count += 1
                self.stats["files_moved"] += 1
                logger.info(f"Moved: {source_path} -> {dest_path}")
            except (OSError, PermissionError, shutil.Error) as e:
                logger.error(f"Error moving {source_path} to {dest_path}: {e}")
                self.stats["errors"] += 1

        logger.info(f"Moved {moved_count} file(s) to {dest_dir}")
        return moved_count

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics.

        Returns:
            Dictionary with statistics.
        """
        return self.stats.copy()


def main() -> int:
    """Main entry point for regex file finder."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Find files matching regex patterns in names or content"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        required=True,
        help="Regex pattern to match",
    )
    parser.add_argument(
        "-d",
        "--directory",
        help="Directory to search (overrides config)",
    )
    parser.add_argument(
        "-s",
        "--search-in",
        choices=["name", "content", "both"],
        default="name",
        help="Where to search: name, content, or both (default: name)",
    )
    parser.add_argument(
        "-a",
        "--action",
        choices=["list", "copy", "move"],
        default="list",
        help="Action to perform: list, copy, or move (default: list)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory for copy/move operations (overrides config)",
    )
    parser.add_argument(
        "--preserve-structure",
        action="store_true",
        help="Preserve directory structure in output",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Disable recursive directory search",
    )

    args = parser.parse_args()

    try:
        finder = RegexFileFinder(config_path=args.config)

        kwargs = {
            "search_directory": args.directory,
            "search_in": args.search_in,
            "recursive": not args.no_recursive,
        }

        if args.action == "list":
            files = finder.list_files(args.pattern, **kwargs)
            print(f"\nFound {len(files)} matching file(s):")
            print("=" * 60)
            for file_info in files:
                print(f"  {file_info['path']}")
                print(f"    Size: {file_info['size']} bytes")
                print(f"    Match type: {file_info['match_type']}")
                print()

        elif args.action == "copy":
            count = finder.copy_files(
                args.pattern,
                destination=args.output,
                preserve_structure=args.preserve_structure,
                **kwargs,
            )
            print(f"\nCopied {count} file(s)")

        elif args.action == "move":
            count = finder.move_files(
                args.pattern,
                destination=args.output,
                preserve_structure=args.preserve_structure,
                **kwargs,
            )
            print(f"\nMoved {count} file(s)")

        # Print statistics
        stats = finder.get_stats()
        print("\nStatistics:")
        print(f"  Files scanned: {stats['files_scanned']}")
        print(f"  Files matched: {stats['files_matched']}")
        if args.action == "copy":
            print(f"  Files copied: {stats['files_copied']}")
        elif args.action == "move":
            print(f"  Files moved: {stats['files_moved']}")
        print(f"  Errors: {stats['errors']}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
