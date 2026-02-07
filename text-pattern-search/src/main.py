"""Text Pattern Search.

A Python script that searches file contents for specific text patterns,
listing all files containing the search terms with line numbers and context.
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/search.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


class TextPatternSearch:
    """Searches for text patterns in files with context."""

    TEXT_FILE_EXTENSIONS = {
        ".txt",
        ".py",
        ".js",
        ".html",
        ".css",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".md",
        ".sh",
        ".bat",
        ".log",
        ".csv",
        ".sql",
        ".java",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".go",
        ".rs",
        ".php",
        ".rb",
        ".pl",
        ".r",
        ".m",
        ".swift",
        ".kt",
        ".ts",
        ".tsx",
        ".jsx",
        ".vue",
        ".scala",
        ".clj",
        ".lua",
        ".vim",
        ".conf",
        ".config",
        ".ini",
        ".cfg",
        ".properties",
    }

    def __init__(
        self,
        pattern: str,
        use_regex: bool = False,
        case_sensitive: bool = True,
        context_lines: int = 2,
        file_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> None:
        """Initialize the text pattern search.

        Args:
            pattern: Text pattern to search for
            use_regex: If True, treat pattern as regex; if False, literal text
            case_sensitive: If True, case-sensitive search; if False, case-insensitive
            context_lines: Number of context lines to show before and after matches
            file_patterns: List of file extensions or patterns to include
            exclude_patterns: List of file patterns to exclude

        Raises:
            re.error: If pattern is invalid regex when use_regex is True
        """
        self.pattern = pattern
        self.use_regex = use_regex
        self.case_sensitive = case_sensitive
        self.context_lines = context_lines
        self.file_patterns = file_patterns or []
        self.exclude_patterns = exclude_patterns or []

        flags = 0 if case_sensitive else re.IGNORECASE
        if use_regex:
            try:
                self.compiled_pattern = re.compile(pattern, flags)
            except re.error as e:
                raise re.error(f"Invalid regex pattern: {e}") from e
        else:
            escaped_pattern = re.escape(pattern)
            self.compiled_pattern = re.compile(escaped_pattern, flags)

        self.stats = {
            "files_searched": 0,
            "files_matched": 0,
            "total_matches": 0,
            "errors": 0,
        }

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file is likely a text file.

        Args:
            file_path: Path to file

        Returns:
            True if file appears to be a text file, False otherwise
        """
        suffix = file_path.suffix.lower()
        if suffix in self.TEXT_FILE_EXTENSIONS:
            return True

        if self.file_patterns:
            for pattern in self.file_patterns:
                if pattern.startswith("."):
                    if suffix == pattern.lower():
                        return True
                elif pattern in file_path.name.lower():
                    return True
            return False

        return True

    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from search.

        Args:
            file_path: Path to file

        Returns:
            True if file should be excluded, False otherwise
        """
        for pattern in self.exclude_patterns:
            if pattern in file_path.name or pattern in str(file_path):
                return True
        return False

    def _is_binary_file(self, file_path: Path) -> bool:
        """Check if file is binary.

        Args:
            file_path: Path to file

        Returns:
            True if file appears to be binary, False otherwise
        """
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(8192)
                if b"\x00" in chunk:
                    return True
                try:
                    chunk.decode("utf-8")
                except UnicodeDecodeError:
                    return True
        except (IOError, PermissionError):
            return True

        return False

    def search_file(self, file_path: Path) -> List[Tuple[int, str, str]]:
        """Search for pattern in a single file.

        Args:
            file_path: Path to file to search

        Returns:
            List of tuples (line_number, line_content, match_context)

        Raises:
            IOError: If file cannot be read
            UnicodeDecodeError: If file encoding is not supported
        """
        matches: List[Tuple[int, str, str]] = []

        try:
            if self._is_binary_file(file_path):
                logger.debug(f"Skipping binary file: {file_path}")
                return matches

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, start=1):
                if self.compiled_pattern.search(line):
                    start_context = max(0, line_num - self.context_lines - 1)
                    end_context = min(len(lines), line_num + self.context_lines)
                    context_lines_list = lines[start_context:end_context]

                    context = "".join(context_lines_list)
                    matches.append((line_num, line.rstrip("\n"), context))

        except (IOError, PermissionError) as e:
            logger.warning(f"Cannot read file {file_path}: {e}")
            self.stats["errors"] += 1
        except UnicodeDecodeError as e:
            logger.warning(f"Encoding error in {file_path}: {e}")
            self.stats["errors"] += 1

        return matches

    def search_directory(
        self, directory: Path, recursive: bool = False
    ) -> List[Tuple[Path, List[Tuple[int, str, str]]]]:
        """Search for pattern in all files in a directory.

        Args:
            directory: Directory path to search
            recursive: If True, search subdirectories recursively

        Returns:
            List of tuples (file_path, matches_list)
        """
        results: List[Tuple[Path, List[Tuple[int, str, str]]]] = []

        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return results

        if not directory.is_dir():
            logger.warning(f"Path is not a directory: {directory}")
            return results

        if recursive:
            file_paths = list(directory.rglob("*"))
        else:
            file_paths = list(directory.glob("*"))

        for file_path in file_paths:
            if not file_path.is_file():
                continue

            if self._should_exclude_file(file_path):
                logger.debug(f"Excluding file: {file_path}")
                continue

            if not self._is_text_file(file_path):
                logger.debug(f"Skipping non-text file: {file_path}")
                continue

            self.stats["files_searched"] += 1
            matches = self.search_file(file_path)

            if matches:
                self.stats["files_matched"] += 1
                self.stats["total_matches"] += len(matches)
                results.append((file_path, matches))

        return results

    def search_paths(
        self, paths: List[Path], recursive: bool = False
    ) -> List[Tuple[Path, List[Tuple[int, str, str]]]]:
        """Search for pattern in multiple paths (files or directories).

        Args:
            paths: List of file or directory paths
            recursive: If True, search subdirectories recursively

        Returns:
            List of tuples (file_path, matches_list)
        """
        all_results: List[Tuple[Path, List[Tuple[int, str, str]]]] = []

        for path in paths:
            path = Path(path).expanduser().resolve()

            if path.is_file():
                if self._should_exclude_file(path):
                    continue

                if not self._is_text_file(path):
                    continue

                self.stats["files_searched"] += 1
                matches = self.search_file(path)

                if matches:
                    self.stats["files_matched"] += 1
                    self.stats["total_matches"] += len(matches)
                    all_results.append((path, matches))

            elif path.is_dir():
                results = self.search_directory(path, recursive=recursive)
                all_results.extend(results)

            else:
                logger.warning(f"Path does not exist: {path}")

        return all_results

    def format_results(
        self, results: List[Tuple[Path, List[Tuple[int, str, str]]]]
    ) -> str:
        """Format search results as readable text.

        Args:
            results: List of search results

        Returns:
            Formatted string with search results
        """
        if not results:
            return f"No matches found for pattern: {self.pattern}"

        lines = [
            f"Search Results for Pattern: {self.pattern}",
            "=" * 80,
            "",
            f"Files searched: {self.stats['files_searched']}",
            f"Files matched: {self.stats['files_matched']}",
            f"Total matches: {self.stats['total_matches']}",
            f"Errors: {self.stats['errors']}",
            "",
            "-" * 80,
            "",
        ]

        for file_path, matches in results:
            lines.append(f"File: {file_path}")
            lines.append(f"Matches: {len(matches)}")
            lines.append("")

            for line_num, line_content, context in matches:
                lines.append(f"  Line {line_num}:")
                lines.append(f"    {line_content}")
                if self.context_lines > 0:
                    lines.append("    Context:")
                    for ctx_line in context.split("\n"):
                        if ctx_line.strip():
                            lines.append(f"      {ctx_line}")

            lines.append("-" * 80)
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
        description="Search file contents for text patterns with context"
    )
    parser.add_argument(
        "pattern",
        type=str,
        help="Text pattern to search for",
    )
    parser.add_argument(
        "paths",
        type=str,
        nargs="+",
        help="File paths or directory paths to search",
    )
    parser.add_argument(
        "--regex",
        action="store_true",
        help="Treat pattern as regular expression",
    )
    parser.add_argument(
        "--case-insensitive",
        action="store_true",
        help="Perform case-insensitive search",
    )
    parser.add_argument(
        "--context",
        type=int,
        default=2,
        help="Number of context lines to show (default: 2)",
    )
    parser.add_argument(
        "--file-patterns",
        type=str,
        nargs="+",
        default=None,
        help="File extensions or patterns to include",
    )
    parser.add_argument(
        "--exclude",
        type=str,
        nargs="+",
        default=None,
        help="File patterns to exclude",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively search subdirectories",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path for search results",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file (YAML)",
    )

    args = parser.parse_args()

    try:
        pattern = args.pattern
        use_regex = args.regex
        case_sensitive = not args.case_insensitive
        context_lines = args.context
        file_patterns = args.file_patterns
        exclude_patterns = args.exclude or []
        recursive = args.recursive

        if args.config:
            config = load_config(Path(args.config))
            if "use_regex" in config:
                use_regex = config["use_regex"]
            if "case_sensitive" in config:
                case_sensitive = config["case_sensitive"]
            if "context_lines" in config:
                context_lines = config["context_lines"]
            if "file_patterns" in config:
                file_patterns = config["file_patterns"]
            if "exclude_patterns" in config:
                exclude_patterns = config["exclude_patterns"]
            if "recursive" in config:
                recursive = config["recursive"]

        searcher = TextPatternSearch(
            pattern=pattern,
            use_regex=use_regex,
            case_sensitive=case_sensitive,
            context_lines=context_lines,
            file_patterns=file_patterns,
            exclude_patterns=exclude_patterns,
        )

        file_paths = [Path(p) for p in args.paths]
        results = searcher.search_paths(file_paths, recursive=recursive)

        formatted_results = searcher.format_results(results)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(formatted_results)
            logger.info(f"Results saved to {output_path}")
        else:
            print(formatted_results)

        return 0

    except (ValueError, FileNotFoundError, re.error) as e:
        logger.error(f"Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
