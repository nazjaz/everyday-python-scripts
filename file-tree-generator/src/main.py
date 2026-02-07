"""File Tree Generator - Generate visual directory tree diagrams.

This module provides functionality to generate visual file tree diagrams
showing directory structure with file sizes and counts. Supports
customizable depth, exclusion patterns, and multiple output formats.
Includes comprehensive logging and error handling.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FileTreeGenerator:
    """Generates visual file tree diagrams with file sizes and counts."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize FileTreeGenerator with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_directories()
        self.tree_lines: List[str] = []
        self.stats = {
            "directories_scanned": 0,
            "files_counted": 0,
            "total_size": 0,
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
        if os.getenv("ROOT_DIRECTORY"):
            config["root_directory"] = os.getenv("ROOT_DIRECTORY")
        if os.getenv("OUTPUT_FILE"):
            config["output_file"] = os.getenv("OUTPUT_FILE")
        if os.getenv("MAX_DEPTH"):
            config["max_depth"] = int(os.getenv("MAX_DEPTH"))
        if os.getenv("SHOW_HIDDEN"):
            config["show_hidden"] = (
                os.getenv("SHOW_HIDDEN").lower() == "true"
            )

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/file_tree_generator.log")

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
        """Set up root directory for tree generation."""
        self.root_dir = Path(
            os.path.expanduser(self.config["root_directory"])
        )

        if not self.root_dir.exists():
            raise FileNotFoundError(
                f"Root directory does not exist: {self.root_dir}"
            )

        if not self.root_dir.is_dir():
            raise ValueError(
                f"Root path is not a directory: {self.root_dir}"
            )

        logger.info(f"Root directory: {self.root_dir}")

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: File size in bytes.

        Returns:
            Formatted size string (e.g., "1.5 MB").
        """
        if size_bytes == 0:
            return "0 B"

        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def _should_include_path(self, path: Path, is_directory: bool) -> bool:
        """Check if path should be included in tree.

        Args:
            path: Path to check.
            is_directory: True if path is a directory.

        Returns:
            True if path should be included, False otherwise.
        """
        # Check hidden files/directories
        if not self.config.get("show_hidden", False):
            if path.name.startswith("."):
                return False

        exclusions = self.config.get("exclusions", {})
        path_str = str(path)

        # Check excluded directories
        excluded_dirs = exclusions.get("directories", [])
        for excluded_dir in excluded_dirs:
            excluded_path = Path(os.path.expanduser(excluded_dir))
            try:
                if path.is_relative_to(excluded_path):
                    return False
            except (ValueError, AttributeError):
                # Python < 3.9 compatibility
                if str(path).startswith(str(excluded_path)):
                    return False

        # Check excluded patterns
        excluded_patterns = exclusions.get("patterns", [])
        for pattern in excluded_patterns:
            if pattern in path_str or pattern in path.name:
                return False

        # Check file extensions
        if not is_directory:
            excluded_extensions = exclusions.get("extensions", [])
            if path.suffix.lower() in [
                ext.lower() for ext in excluded_extensions
            ]:
                return False

        return True

    def _calculate_directory_stats(
        self, directory: Path, max_depth: int, current_depth: int
    ) -> Tuple[int, int]:
        """Calculate total size and file count for directory.

        Args:
            directory: Directory to calculate stats for.
            max_depth: Maximum depth to traverse.
            current_depth: Current depth in tree.

        Returns:
            Tuple of (total_size_bytes, file_count).
        """
        total_size = 0
        file_count = 0

        if current_depth >= max_depth:
            return total_size, file_count

        try:
            for item in directory.iterdir():
                if not self._should_include_path(item, item.is_dir()):
                    continue

                if item.is_file():
                    try:
                        size = item.stat().st_size
                        total_size += size
                        file_count += 1
                    except (OSError, PermissionError) as e:
                        error_msg = f"Error accessing {item}: {e}"
                        logger.debug(error_msg)
                        # Don't increment errors here to avoid double counting

                elif item.is_dir():
                    dir_size, dir_file_count = self._calculate_directory_stats(
                        item, max_depth, current_depth + 1
                    )
                    total_size += dir_size
                    file_count += dir_file_count

        except (PermissionError, OSError) as e:
            error_msg = f"Error scanning directory {directory}: {e}"
            logger.warning(error_msg)
            self.stats["errors"] += 1
            if error_msg not in self.stats["errors_list"]:
                self.stats["errors_list"].append(error_msg)

        return total_size, file_count

    def _generate_tree_node(
        self,
        directory: Path,
        prefix: str,
        is_last: bool,
        max_depth: int,
        current_depth: int,
    ) -> None:
        """Generate tree node for directory recursively.

        Args:
            directory: Directory to generate node for.
            prefix: Prefix string for tree visualization.
            is_last: True if this is the last item in parent directory.
            max_depth: Maximum depth to traverse.
            current_depth: Current depth in tree.
        """
        if current_depth >= max_depth:
            return

        self.stats["directories_scanned"] += 1

        # Calculate directory stats for display
        # Note: We don't add to total_size here to avoid double counting
        # Total size is accumulated only when processing individual files
        dir_size, file_count = self._calculate_directory_stats(
            directory, max_depth, current_depth
        )

        # Format directory name with stats
        dir_name = directory.name or str(directory)
        size_str = self._format_size(dir_size)
        stats_str = f" [{file_count} files, {size_str}]"

        # Generate tree line
        connector = "└── " if is_last else "├── "
        tree_line = f"{prefix}{connector}{dir_name}{stats_str}"
        self.tree_lines.append(tree_line)

        # Prepare prefix for children
        extension = "    " if is_last else "│   "
        child_prefix = prefix + extension

        # Get sorted items (directories first, then files)
        try:
            items = sorted(
                directory.iterdir(),
                key=lambda x: (x.is_file(), x.name.lower()),
            )
            # Filter items based on exclusions
            items = [
                item
                for item in items
                if self._should_include_path(item, item.is_dir())
            ]

            # Process directories first
            dirs = [item for item in items if item.is_dir()]
            files = [item for item in items if item.is_file()]

            # Process directories
            for i, item in enumerate(dirs):
                is_last_dir = i == len(dirs) - 1 and len(files) == 0
                self._generate_tree_node(
                    item, child_prefix, is_last_dir, max_depth, current_depth + 1
                )

            # Process files
            for i, item in enumerate(files):
                is_last_file = i == len(files) - 1
                try:
                    file_size = item.stat().st_size
                    size_str = self._format_size(file_size)
                    connector = "└── " if is_last_file else "├── "
                    file_line = (
                        f"{child_prefix}{connector}{item.name} "
                        f"({size_str})"
                    )
                    self.tree_lines.append(file_line)
                    self.stats["files_counted"] += 1
                    self.stats["total_size"] += file_size
                except (OSError, PermissionError) as e:
                    error_msg = f"Error accessing {item}: {e}"
                    logger.debug(error_msg)
                    self.stats["errors"] += 1
                    if error_msg not in self.stats["errors_list"]:
                        self.stats["errors_list"].append(error_msg)

        except (PermissionError, OSError) as e:
            error_msg = f"Error reading directory {directory}: {e}"
            logger.warning(error_msg)
            self.stats["errors"] += 1
            if error_msg not in self.stats["errors_list"]:
                self.stats["errors_list"].append(error_msg)

    def generate_tree(self) -> str:
        """Generate file tree diagram.

        Returns:
            Tree diagram as string.
        """
        logger.info("Starting file tree generation")
        logger.info(f"Root directory: {self.root_dir}")
        logger.info(f"Max depth: {self.config.get('max_depth', 'unlimited')}")

        self.tree_lines = []
        self.stats = {
            "directories_scanned": 0,
            "files_counted": 0,
            "total_size": 0,
            "errors": 0,
            "errors_list": [],
        }

        # Add header
        max_depth = self.config.get("max_depth")
        depth_str = str(max_depth) if max_depth else "unlimited"
        header_lines = [
            "=" * 80,
            f"File Tree: {self.root_dir}",
            f"Max Depth: {depth_str}",
            "=" * 80,
            "",
        ]

        # Add root directory
        root_name = self.root_dir.name or str(self.root_dir)
        root_size, root_file_count = self._calculate_directory_stats(
            self.root_dir, max_depth or 999, 0
        )
        root_stats = f" [{root_file_count} files, {self._format_size(root_size)}]"
        header_lines.append(f"{root_name}{root_stats}")

        self.tree_lines = header_lines

        # Generate tree for root directory contents
        try:
            items = sorted(
                self.root_dir.iterdir(),
                key=lambda x: (x.is_file(), x.name.lower()),
            )
            items = [
                item
                for item in items
                if self._should_include_path(item, item.is_dir())
            ]

            dirs = [item for item in items if item.is_dir()]
            files = [item for item in items if item.is_file()]

            # Process directories
            for i, item in enumerate(dirs):
                is_last = i == len(dirs) - 1 and len(files) == 0
                self._generate_tree_node(
                    item, "", is_last, max_depth or 999, 1
                )

            # Process root-level files
            for i, item in enumerate(files):
                is_last = i == len(files) - 1
                try:
                    file_size = item.stat().st_size
                    size_str = self._format_size(file_size)
                    connector = "└── " if is_last else "├── "
                    file_line = f"{connector}{item.name} ({size_str})"
                    self.tree_lines.append(file_line)
                    self.stats["files_counted"] += 1
                    self.stats["total_size"] += file_size
                except (OSError, PermissionError) as e:
                    error_msg = f"Error accessing {item}: {e}"
                    logger.debug(error_msg)
                    self.stats["errors"] += 1
                    if error_msg not in self.stats["errors_list"]:
                        self.stats["errors_list"].append(error_msg)

        except (PermissionError, OSError) as e:
            error_msg = f"Error reading root directory: {e}"
            logger.error(error_msg)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)

        # Add footer with statistics
        footer_lines = [
            "",
            "=" * 80,
            "Statistics",
            "=" * 80,
            f"Directories Scanned: {self.stats['directories_scanned']}",
            f"Files Counted: {self.stats['files_counted']}",
            f"Total Size: {self._format_size(self.stats['total_size'])}",
            f"Errors: {self.stats['errors']}",
        ]

        if self.stats["errors_list"]:
            footer_lines.append("")
            footer_lines.append("Errors:")
            for error in self.stats["errors_list"][:10]:  # Limit to 10 errors
                footer_lines.append(f"  - {error}")
            if len(self.stats["errors_list"]) > 10:
                footer_lines.append(
                    f"  ... and {len(self.stats['errors_list']) - 10} more"
                )

        self.tree_lines.extend(footer_lines)

        tree_content = "\n".join(self.tree_lines)
        logger.info("File tree generation completed")
        logger.info(f"Statistics: {self.stats}")

        return tree_content

    def save_tree(self, output_file: Optional[str] = None) -> Path:
        """Save tree diagram to file.

        Args:
            output_file: Optional path to output file.

        Returns:
            Path to saved file.
        """
        tree_content = self.generate_tree()

        if output_file:
            output_path = Path(output_file)
        else:
            output_path = Path(self.config.get("output_file", "tree.txt"))

        if not output_path.is_absolute():
            project_root = Path(__file__).parent.parent
            output_path = project_root / output_path

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(tree_content)

        logger.info(f"Tree diagram saved to: {output_path}")
        return output_path


def main() -> int:
    """Main entry point for file tree generator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate visual file tree diagrams with file sizes "
        "and counts"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-d",
        "--directory",
        help="Root directory to generate tree for (overrides config)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path (overrides config)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        help="Maximum depth to traverse (overrides config)",
    )
    parser.add_argument(
        "--print",
        action="store_true",
        help="Print tree to console instead of saving to file",
    )

    args = parser.parse_args()

    try:
        generator = FileTreeGenerator(config_path=args.config)

        # Override config with command-line arguments
        if args.directory:
            generator.root_dir = Path(os.path.expanduser(args.directory))
            if not generator.root_dir.exists():
                raise FileNotFoundError(
                    f"Directory does not exist: {generator.root_dir}"
                )

        if args.max_depth:
            generator.config["max_depth"] = args.max_depth

        # Generate tree
        tree_content = generator.generate_tree()

        # Output tree
        if args.print:
            print(tree_content)
        else:
            output_path = generator.save_tree(
                output_file=args.output
            )
            print(f"Tree diagram saved to: {output_path}")

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
