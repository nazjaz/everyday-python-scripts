"""Dependency Graph Analyzer.

A Python script that analyzes file relationships by examining references,
imports, or dependencies found in file contents, generating a dependency graph.
"""

import argparse
import json
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/analyzer.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


class DependencyGraphAnalyzer:
    """Analyzes file dependencies and generates dependency graphs."""

    PYTHON_IMPORT_PATTERNS = [
        re.compile(r"^import\s+(\w+)", re.MULTILINE),
        re.compile(r"^from\s+(\S+)\s+import", re.MULTILINE),
        re.compile(r"^import\s+(\S+)", re.MULTILINE),
    ]

    JAVASCRIPT_IMPORT_PATTERNS = [
        re.compile(r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]", re.MULTILINE),
        re.compile(r"require\(['\"]([^'\"]+)['\"]\)", re.MULTILINE),
        re.compile(r"import\s+['\"]([^'\"]+)['\"]", re.MULTILINE),
    ]

    FILE_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
    }

    def __init__(
        self,
        base_path: Optional[Path] = None,
        follow_external: bool = False,
        max_depth: Optional[int] = None,
    ) -> None:
        """Initialize the dependency analyzer.

        Args:
            base_path: Base path for resolving relative imports
            follow_external: If True, include external dependencies
            max_depth: Maximum depth for dependency traversal (None = unlimited)
        """
        self.base_path = base_path
        self.follow_external = follow_external
        self.max_depth = max_depth

        self.graph: Dict[str, Set[str]] = defaultdict(set)
        self.file_to_module: Dict[str, str] = {}
        self.module_to_files: Dict[str, List[str]] = defaultdict(list)

        self.stats = {
            "files_processed": 0,
            "dependencies_found": 0,
            "external_dependencies": 0,
            "internal_dependencies": 0,
            "errors": 0,
        }

    def _get_file_type(self, file_path: Path) -> Optional[str]:
        """Determine file type from extension.

        Args:
            file_path: Path to file

        Returns:
            File type string or None
        """
        suffix = file_path.suffix.lower()
        return self.FILE_EXTENSIONS.get(suffix)

    def _extract_python_imports(self, content: str) -> Set[str]:
        """Extract Python imports from file content.

        Args:
            content: File content

        Returns:
            Set of imported module names
        """
        imports: Set[str] = set()

        for pattern in self.PYTHON_IMPORT_PATTERNS:
            for match in pattern.finditer(content):
                module = match.group(1)
                if module and not module.startswith("."):
                    imports.add(module.split(".")[0])

        return imports

    def _extract_javascript_imports(self, content: str) -> Set[str]:
        """Extract JavaScript imports from file content.

        Args:
            content: File content

        Returns:
            Set of imported module paths
        """
        imports: Set[str] = set()

        for pattern in self.JAVASCRIPT_IMPORT_PATTERNS:
            for match in pattern.finditer(content):
                module_path = match.group(1)
                if module_path and not module_path.startswith("."):
                    imports.add(module_path)

        return imports

    def _extract_imports(self, file_path: Path, content: str) -> Set[str]:
        """Extract imports based on file type.

        Args:
            file_path: Path to file
            content: File content

        Returns:
            Set of imported module names
        """
        file_type = self._get_file_type(file_path)

        if file_type == "python":
            return self._extract_python_imports(content)
        elif file_type in ["javascript", "typescript"]:
            return self._extract_javascript_imports(content)
        else:
            return set()

    def _resolve_module_to_file(self, module_name: str, source_file: Path) -> Optional[Path]:
        """Resolve module name to file path.

        Args:
            module_name: Module name to resolve
            source_file: Source file making the import

        Returns:
            Resolved file path or None if not found
        """
        if not self.base_path:
            base = source_file.parent
        else:
            base = self.base_path

        possible_paths = [
            base / f"{module_name}.py",
            base / module_name / "__init__.py",
            base / f"{module_name}.js",
            base / f"{module_name}.jsx",
            base / f"{module_name}.ts",
            base / f"{module_name}.tsx",
        ]

        for path in possible_paths:
            if path.exists() and path.is_file():
                return path.resolve()

        module_parts = module_name.split(".")
        current_path = base

        for part in module_parts:
            current_path = current_path / part
            init_file = current_path / "__init__.py"
            if init_file.exists():
                return init_file.resolve()

            py_file = current_path.with_suffix(".py")
            if py_file.exists():
                return py_file.resolve()

        return None

    def _is_external_dependency(self, module_name: str) -> bool:
        """Check if dependency is external (not in project).

        Args:
            module_name: Module name to check

        Returns:
            True if external, False otherwise
        """
        if not self.base_path:
            return True

        module_parts = module_name.split(".")
        check_path = self.base_path / module_parts[0]

        return not check_path.exists()

    def analyze_file(self, file_path: Path) -> Set[str]:
        """Analyze a single file for dependencies.

        Args:
            file_path: Path to file to analyze

        Returns:
            Set of dependency file paths

        Raises:
            FileNotFoundError: If file does not exist
            IOError: If file cannot be read
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File does not exist: {file_path}")

        logger.debug(f"Analyzing file: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            logger.warning(f"Encoding error in {file_path}, trying latin-1")
            with open(file_path, "r", encoding="latin-1") as f:
                content = f.read()

        imports = self._extract_imports(file_path, content)
        dependencies: Set[str] = set()

        for module_name in imports:
            if self._is_external_dependency(module_name):
                if self.follow_external:
                    dependencies.add(module_name)
                    self.stats["external_dependencies"] += 1
                else:
                    logger.debug(f"Skipping external dependency: {module_name}")
                continue

            resolved_file = self._resolve_module_to_file(module_name, file_path)
            if resolved_file:
                dependencies.add(str(resolved_file))
                self.stats["internal_dependencies"] += 1
            else:
                logger.debug(f"Could not resolve module: {module_name}")

        self.stats["files_processed"] += 1
        self.stats["dependencies_found"] += len(dependencies)

        return dependencies

    def analyze_files(
        self, file_paths: List[Path], recursive: bool = False
    ) -> Dict[str, Set[str]]:
        """Analyze multiple files and build dependency graph.

        Args:
            file_paths: List of file paths or directory paths
            recursive: If True, recursively scan directories

        Returns:
            Dictionary mapping file paths to sets of dependencies
        """
        all_files: List[Path] = []

        for path in file_paths:
            path = Path(path).expanduser().resolve()

            if path.is_file():
                all_files.append(path)
            elif path.is_dir():
                if recursive:
                    for ext in self.FILE_EXTENSIONS.keys():
                        all_files.extend(path.rglob(f"*{ext}"))
                else:
                    for ext in self.FILE_EXTENSIONS.keys():
                        all_files.extend(path.glob(f"*{ext}"))

        logger.info(f"Found {len(all_files)} files to analyze")

        for file_path in all_files:
            try:
                dependencies = self.analyze_file(file_path)
                file_str = str(file_path)
                self.graph[file_str] = dependencies

            except (FileNotFoundError, IOError) as e:
                logger.warning(f"Error analyzing {file_path}: {e}")
                self.stats["errors"] += 1
            except Exception as e:
                logger.exception(f"Unexpected error analyzing {file_path}: {e}")
                self.stats["errors"] += 1

        return dict(self.graph)

    def get_reverse_dependencies(self) -> Dict[str, Set[str]]:
        """Get reverse dependency graph (what depends on each file).

        Returns:
            Dictionary mapping file paths to sets of files that depend on them
        """
        reverse_graph: Dict[str, Set[str]] = defaultdict(set)

        for file_path, dependencies in self.graph.items():
            for dep in dependencies:
                reverse_graph[dep].add(file_path)

        return dict(reverse_graph)

    def format_graph_text(self) -> str:
        """Format dependency graph as text.

        Returns:
            Formatted string representation of the graph
        """
        lines = [
            "Dependency Graph Analysis",
            "=" * 80,
            "",
            f"Files processed: {self.stats['files_processed']}",
            f"Dependencies found: {self.stats['dependencies_found']}",
            f"  - Internal: {self.stats['internal_dependencies']}",
            f"  - External: {self.stats['external_dependencies']}",
            f"Errors: {self.stats['errors']}",
            "",
            "-" * 80,
            "",
            "Dependency Graph:",
            "",
        ]

        for file_path, dependencies in sorted(self.graph.items()):
            lines.append(f"{file_path}")
            if dependencies:
                for dep in sorted(dependencies):
                    lines.append(f"  -> {dep}")
            else:
                lines.append("  (no dependencies)")
            lines.append("")

        return "\n".join(lines)

    def format_graph_json(self) -> str:
        """Format dependency graph as JSON.

        Returns:
            JSON string representation of the graph
        """
        graph_data = {
            "stats": self.stats,
            "graph": {file: list(deps) for file, deps in self.graph.items()},
            "reverse_graph": {
                file: list(deps)
                for file, deps in self.get_reverse_dependencies().items()
            },
        }

        return json.dumps(graph_data, indent=2)

    def format_graph_dot(self) -> str:
        """Format dependency graph as Graphviz DOT format.

        Returns:
            DOT format string
        """
        lines = ["digraph dependencies {", "  rankdir=LR;", ""]

        for file_path, dependencies in self.graph.items():
            node_id = self._sanitize_node_id(file_path)
            node_label = Path(file_path).name

            if dependencies:
                for dep in dependencies:
                    dep_id = self._sanitize_node_id(dep)
                    dep_label = Path(dep).name if Path(dep).exists() else dep
                    lines.append(f'  "{node_id}" [label="{node_label}"];')
                    lines.append(f'  "{dep_id}" [label="{dep_label}"];')
                    lines.append(f'  "{node_id}" -> "{dep_id}";')

        lines.append("}")
        return "\n".join(lines)

    def _sanitize_node_id(self, path: str) -> str:
        """Sanitize path for use as node ID in DOT format.

        Args:
            path: File path

        Returns:
            Sanitized node ID
        """
        return path.replace("/", "_").replace("\\", "_").replace(".", "_").replace("-", "_")


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
        description="Analyze file dependencies and generate dependency graph"
    )
    parser.add_argument(
        "paths",
        type=str,
        nargs="+",
        help="File paths or directory paths to analyze",
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default=None,
        help="Base path for resolving relative imports",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively scan directories",
    )
    parser.add_argument(
        "--follow-external",
        action="store_true",
        help="Include external dependencies in graph",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum depth for dependency traversal",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path for text report",
    )
    parser.add_argument(
        "--json",
        type=str,
        default=None,
        help="Output JSON file path",
    )
    parser.add_argument(
        "--dot",
        type=str,
        default=None,
        help="Output Graphviz DOT file path",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file (YAML)",
    )

    args = parser.parse_args()

    try:
        base_path = Path(args.base_path) if args.base_path else None
        recursive = args.recursive
        follow_external = args.follow_external
        max_depth = args.max_depth

        if args.config:
            config = load_config(Path(args.config))
            if "base_path" in config:
                base_path = Path(config["base_path"])
            if "recursive" in config:
                recursive = config["recursive"]
            if "follow_external" in config:
                follow_external = config["follow_external"]
            if "max_depth" in config:
                max_depth = config["max_depth"]

        analyzer = DependencyGraphAnalyzer(
            base_path=base_path,
            follow_external=follow_external,
            max_depth=max_depth,
        )

        file_paths = [Path(p) for p in args.paths]
        graph = analyzer.analyze_files(file_paths, recursive=recursive)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(analyzer.format_graph_text())
            logger.info(f"Text report saved to {output_path}")

        if args.json:
            json_path = Path(args.json)
            json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(json_path, "w") as f:
                f.write(analyzer.format_graph_json())
            logger.info(f"JSON graph saved to {json_path}")

        if args.dot:
            dot_path = Path(args.dot)
            dot_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dot_path, "w") as f:
                f.write(analyzer.format_graph_dot())
            logger.info(f"DOT graph saved to {dot_path}")

        if not (args.output or args.json or args.dot):
            print(analyzer.format_graph_text())

        return 0

    except (ValueError, FileNotFoundError) as e:
        logger.error(f"Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
