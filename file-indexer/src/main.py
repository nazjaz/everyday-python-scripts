"""File Indexer - CLI tool for generating searchable file index with metadata.

This module provides a command-line tool for indexing files in directory trees,
extracting metadata (size, modification date, type, path), and saving to JSON
format for searchable access.
"""

import argparse
import hashlib
import json
import logging
import logging.handlers
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FileIndexer:
    """Generates searchable file index with metadata."""

    def __init__(self, config: Dict) -> None:
        """Initialize FileIndexer.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.options = config.get("options", {})
        self.metadata_config = config.get("metadata", {})
        self.exclude_patterns = [
            re.compile(pattern) for pattern in config.get("exclude_patterns", [])
        ]
        self.exclude_directories = [
            re.compile(pattern) for pattern in config.get("exclude_directories", [])
        ]

    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from indexing.

        Args:
            file_path: Path to file.

        Returns:
            True if file should be excluded.
        """
        filename = file_path.name

        # Check hidden files
        if not self.options.get("include_hidden", False) and filename.startswith("."):
            return True

        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if pattern.search(filename):
                return True

        # Check file size limits
        try:
            file_size = file_path.stat().st_size

            if not self.options.get("include_empty", True) and file_size == 0:
                return True

            min_size = self.options.get("min_file_size", 0)
            if min_size > 0 and file_size < min_size:
                return True

            max_size = self.options.get("max_file_size", 0)
            if max_size > 0 and file_size > max_size:
                return True
        except (OSError, IOError):
            return True

        return False

    def should_exclude_directory(self, dir_path: Path) -> bool:
        """Check if directory should be excluded from indexing.

        Args:
            dir_path: Path to directory.

        Returns:
            True if directory should be excluded.
        """
        dirname = str(dir_path)

        for pattern in self.exclude_directories:
            if pattern.search(dirname):
                return True

        return False

    def calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """Calculate hash of a file.

        Args:
            file_path: Path to file.

        Returns:
            Hexadecimal hash string or None if error.
        """
        if not self.options.get("calculate_hashes", False):
            return None

        try:
            algorithm = self.options.get("hash_algorithm", "sha256").lower()
            hash_obj = hashlib.new(algorithm)

            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    hash_obj.update(chunk)

            return hash_obj.hexdigest()

        except (IOError, OSError) as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return None

    def get_file_metadata(self, file_path: Path, base_path: Optional[Path] = None) -> Dict:
        """Extract metadata from a file.

        Args:
            file_path: Path to file.
            base_path: Base path for calculating relative paths.

        Returns:
            Dictionary with file metadata.
        """
        try:
            file_stat = file_path.stat()

            metadata = {
                "name": file_path.name,
            }

            # Full path
            if self.metadata_config.get("full_path", True):
                metadata["full_path"] = str(file_path.resolve())

            # Relative path
            if self.metadata_config.get("relative_path", False) and base_path:
                try:
                    metadata["relative_path"] = str(file_path.relative_to(base_path))
                except ValueError:
                    metadata["relative_path"] = str(file_path)

            # File size
            if self.metadata_config.get("size", True):
                metadata["size"] = file_stat.st_size
                metadata["size_human"] = self._format_size(file_stat.st_size)

            # Modification date
            if self.metadata_config.get("modification_date", True):
                metadata["modified"] = datetime.fromtimestamp(
                    file_stat.st_mtime
                ).isoformat()
                metadata["modified_timestamp"] = file_stat.st_mtime

            # Creation date
            if self.metadata_config.get("creation_date", True):
                metadata["created"] = datetime.fromtimestamp(
                    file_stat.st_ctime
                ).isoformat()
                metadata["created_timestamp"] = file_stat.st_ctime

            # File type (extension)
            if self.metadata_config.get("file_type", True):
                ext = file_path.suffix.lower().lstrip(".")
                metadata["file_type"] = ext or "no_extension"
                metadata["extension"] = ext

            # Permissions
            if self.options.get("include_permissions", True):
                import stat
                mode = file_stat.st_mode
                metadata["permissions_octal"] = oct(stat.S_IMODE(mode))[2:]
                metadata["permissions_string"] = stat.filemode(mode)

            # Owner information
            if self.options.get("include_owner", False):
                try:
                    metadata["owner_uid"] = file_stat.st_uid
                    metadata["owner_gid"] = file_stat.st_gid
                except (OSError, AttributeError):
                    pass

            # Hash
            file_hash = self.calculate_file_hash(file_path)
            if file_hash:
                metadata["hash"] = file_hash
                metadata["hash_algorithm"] = self.options.get("hash_algorithm", "sha256")

            # MIME type (if requested and available)
            if self.metadata_config.get("mime_type", False):
                try:
                    import mimetypes
                    mime_type, _ = mimetypes.guess_type(str(file_path))
                    if mime_type:
                        metadata["mime_type"] = mime_type
                except ImportError:
                    pass

            return metadata

        except (OSError, IOError) as e:
            logger.error(f"Error getting metadata for {file_path}: {e}")
            return {}

    def index_directory(
        self, directory: Path, recursive: bool = True, base_path: Optional[Path] = None
    ) -> List[Dict]:
        """Index all files in a directory.

        Args:
            directory: Directory to index.
            recursive: Whether to index recursively.
            base_path: Base path for relative paths.

        Returns:
            List of file metadata dictionaries.
        """
        directory = directory.resolve()

        if not directory.exists() or not directory.is_dir():
            logger.warning(f"Directory does not exist: {directory}")
            return []

        if self.should_exclude_directory(directory):
            logger.debug(f"Excluding directory: {directory}")
            return []

        if base_path is None:
            base_path = directory

        files_indexed = []

        # Find all files
        if recursive:
            file_paths = directory.rglob("*")
        else:
            file_paths = directory.glob("*")

        for file_path in file_paths:
            if not file_path.is_file():
                continue

            if self.should_exclude_file(file_path):
                continue

            metadata = self.get_file_metadata(file_path, base_path)
            if metadata:
                files_indexed.append(metadata)

        return files_indexed

    def create_index(
        self, directories: List[Path], recursive: bool = True
    ) -> Dict:
        """Create file index for multiple directories.

        Args:
            directories: List of directories to index.
            recursive: Whether to index recursively.

        Returns:
            Dictionary with index data.
        """
        all_files = []

        for directory in directories:
            directory = directory.resolve()

            if not directory.exists():
                logger.warning(f"Directory does not exist: {directory}")
                continue

            logger.info(f"Indexing directory: {directory}")
            files = self.index_directory(directory, recursive, directory)
            all_files.extend(files)
            logger.info(f"Indexed {len(files)} files from {directory}")

        index = {
            "created_at": datetime.now().isoformat(),
            "total_files": len(all_files),
            "directories_indexed": [str(d.resolve()) for d in directories],
            "recursive": recursive,
            "files": all_files,
        }

        return index

    def save_index(self, index: Dict, output_path: Path) -> None:
        """Save index to JSON file.

        Args:
            index: Index dictionary.
            output_path: Path where index will be saved.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(index, f, indent=2, ensure_ascii=False)

            logger.info(f"Index saved to {output_path}")
        except IOError as e:
            logger.error(f"Error saving index: {e}")
            raise

    def search_index(self, index: Dict, query: str, case_sensitive: bool = False) -> List[Dict]:
        """Search the file index.

        Args:
            index: Index dictionary.
            query: Search query string.
            flags: re flags for search.

        Returns:
            List of matching file metadata dictionaries.
        """
        if not query:
            return []

        search_config = self.config.get("search", {})
        search_fields = search_config.get("search_fields", ["name", "path"])

        matches = []
        query_lower = query if case_sensitive else query.lower()

        for file_info in index.get("files", []):
            match_found = False

            for field in search_fields:
                field_value = file_info.get(field, "")
                if not field_value:
                    continue

                field_str = str(field_value)
                if not case_sensitive:
                    field_str = field_str.lower()

                if query_lower in field_str:
                    match_found = True
                    break

            if match_found:
                matches.append(file_info)

        return matches

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


def setup_logging(config: Dict) -> None:
    """Configure logging based on config file.

    Args:
        config: Configuration dictionary with logging settings.
    """
    log_config = config.get("logging", {})
    log_level = os.getenv("LOG_LEVEL", log_config.get("level", "INFO"))
    log_file = log_config.get("file", "logs/file_indexer.log")
    max_bytes = log_config.get("max_bytes", 10485760)
    backup_count = log_config.get("backup_count", 5)
    log_format = log_config.get(
        "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    handler.setFormatter(logging.Formatter(log_format))

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.addHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)


def load_config(config_path: Optional[Path] = None) -> Dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. Defaults to config.yaml in project root.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file does not exist.
        yaml.YAMLError: If config file is invalid.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def load_index(index_path: Path) -> Dict:
    """Load index from JSON file.

    Args:
        index_path: Path to index file.

    Returns:
        Index dictionary.

    Raises:
        FileNotFoundError: If index file does not exist.
        json.JSONDecodeError: If index file is invalid.
    """
    if not index_path.exists():
        raise FileNotFoundError(f"Index file not found: {index_path}")

    with open(index_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Generate searchable file index with metadata"
    )
    parser.add_argument(
        "command",
        choices=["index", "search"],
        help="Command to execute",
    )
    parser.add_argument(
        "-d",
        "--directories",
        nargs="+",
        type=Path,
        help="Directories to index (overrides config, for index command)",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Index directories recursively (default: true)",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Do not index directories recursively",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output index file path (overrides config)",
    )
    parser.add_argument(
        "-i",
        "--index",
        type=Path,
        help="Index file to search (for search command)",
    )
    parser.add_argument(
        "-q",
        "--query",
        type=str,
        help="Search query (for search command)",
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Case-sensitive search (for search command)",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to configuration file",
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config)
        setup_logging(config)

        if args.command == "index":
            # Override config with command-line arguments
            if args.directories:
                config["index_directories"] = [str(d) for d in args.directories]
            if args.no_recursive:
                recursive = False
            else:
                recursive = args.recursive if args.recursive else config.get("options", {}).get("recursive", True)
            if args.output:
                config["index_file"] = str(args.output)

            # Get directories to index
            directories = [
                Path(d).resolve() for d in config.get("index_directories", [])
            ]

            if not directories:
                logger.error("No directories specified for indexing")
                print("Error: No directories specified for indexing")
                sys.exit(1)

            print(f"Indexing directories: {', '.join(str(d) for d in directories)}")
            print(f"Recursive: {recursive}")
            print()

            # Create index
            indexer = FileIndexer(config)
            index = indexer.create_index(directories, recursive)

            # Save index
            index_path = Path(config.get("index_file", "data/file_index.json"))
            indexer.save_index(index, index_path)

            print()
            print("=" * 60)
            print("INDEXING SUMMARY")
            print("=" * 60)
            print(f"Total files indexed: {index['total_files']:,}")
            print(f"Index saved to: {index_path}")
            print("=" * 60)

        elif args.command == "search":
            if not args.index and not args.query:
                # Try to use default index file
                index_path = Path(config.get("index_file", "data/file_index.json"))
            elif args.index:
                index_path = args.index
            else:
                index_path = Path(config.get("index_file", "data/file_index.json"))

            if not args.query:
                print("Error: --query is required for search command")
                sys.exit(1)

            # Load index
            index = load_index(index_path)

            # Search
            indexer = FileIndexer(config)
            matches = indexer.search_index(
                index, args.query, case_sensitive=args.case_sensitive
            )

            print(f"Search results for '{args.query}': {len(matches)} match(es)\n")

            if matches:
                for i, file_info in enumerate(matches, 1):
                    print(f"{i}. {file_info.get('name', 'Unknown')}")
                    print(f"   Path: {file_info.get('full_path', 'N/A')}")
                    if "size_human" in file_info:
                        print(f"   Size: {file_info['size_human']}")
                    if "modified" in file_info:
                        print(f"   Modified: {file_info['modified']}")
                    if "file_type" in file_info:
                        print(f"   Type: {file_info['file_type']}")
                    print()
            else:
                print("No matches found.")

    except FileNotFoundError as e:
        logger.error(f"Configuration or index error: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Invalid configuration file: {e}")
        print(f"Error: Invalid configuration file: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid index file: {e}")
        print(f"Error: Invalid index file: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        print("\nOperation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
