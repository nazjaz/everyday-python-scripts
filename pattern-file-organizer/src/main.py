"""Pattern File Organizer - Organize files using custom pattern rules.

This module provides functionality to organize files by matching custom patterns
defined in a configuration file, supporting multiple pattern rules and destinations.
"""

import logging
import logging.handlers
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class PatternRule:
    """Represents a pattern matching rule."""

    def __init__(self, name: str, pattern: str, destination: str, **kwargs: Any) -> None:
        """Initialize pattern rule.

        Args:
            name: Rule name/identifier.
            pattern: Regex pattern to match against filenames or paths.
            destination: Destination directory for matched files.
            **kwargs: Additional rule options (case_sensitive, match_type, etc.).
        """
        self.name = name
        self.pattern = pattern
        self.destination = Path(destination)
        self.case_sensitive = kwargs.get("case_sensitive", False)
        self.match_type = kwargs.get("match_type", "filename")  # filename, path, extension
        self.priority = kwargs.get("priority", 0)  # Higher priority matches first
        self.enabled = kwargs.get("enabled", True)

        # Compile regex pattern
        flags = 0 if self.case_sensitive else re.IGNORECASE
        try:
            self.regex = re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{pattern}': {e}") from e

    def matches(self, file_path: Path) -> bool:
        """Check if file matches this rule's pattern.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file matches rule, False otherwise.
        """
        if not self.enabled:
            return False

        if self.match_type == "filename":
            text = file_path.name
        elif self.match_type == "path":
            text = str(file_path)
        elif self.match_type == "extension":
            text = file_path.suffix
        else:
            text = file_path.name

        return bool(self.regex.search(text))


class PatternFileOrganizer:
    """Organizes files using custom pattern rules."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize PatternFileOrganizer with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
            ValueError: If configuration is invalid.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.rules: List[PatternRule] = []
        self._load_rules()
        self.stats = {
            "files_scanned": 0,
            "files_matched": 0,
            "files_moved": 0,
            "files_skipped": 0,
            "errors": 0,
        }
        self.operations: List[Dict[str, Any]] = []

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
        if os.getenv("SOURCE_DIRECTORY"):
            config["source"]["directory"] = os.getenv("SOURCE_DIRECTORY")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/organizer.log")

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

    def _load_rules(self) -> None:
        """Load pattern rules from configuration."""
        rules_config = self.config.get("rules", [])

        if not rules_config:
            raise ValueError("No pattern rules defined in configuration")

        for rule_config in rules_config:
            try:
                rule = PatternRule(
                    name=rule_config.get("name", "unnamed"),
                    pattern=rule_config["pattern"],
                    destination=rule_config["destination"],
                    case_sensitive=rule_config.get("case_sensitive", False),
                    match_type=rule_config.get("match_type", "filename"),
                    priority=rule_config.get("priority", 0),
                    enabled=rule_config.get("enabled", True),
                )
                self.rules.append(rule)
            except KeyError as e:
                raise ValueError(f"Invalid rule configuration: missing {e}") from e
            except ValueError as e:
                raise ValueError(f"Invalid rule configuration: {e}") from e

        # Sort rules by priority (higher priority first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

        logger.info(f"Loaded {len(self.rules)} pattern rule(s)")

    def _is_excluded(self, file_path: Path) -> bool:
        """Check if file should be excluded from processing.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file should be excluded, False otherwise.
        """
        exclude_config = self.config.get("source", {}).get("exclude", {})
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
                if re.search(pattern, file_str):
                    return True
            except Exception:
                pass

        return False

    def _find_matching_rule(self, file_path: Path) -> Optional[PatternRule]:
        """Find first matching rule for file.

        Args:
            file_path: Path to file to match.

        Returns:
            Matching PatternRule or None if no match.
        """
        for rule in self.rules:
            if rule.matches(file_path):
                return rule
        return None

    def _resolve_destination(
        self, file_path: Path, rule: PatternRule, base_directory: Path
    ) -> Path:
        """Resolve destination path for file.

        Args:
            file_path: Path to file being moved.
            rule: Matching pattern rule.
            base_directory: Base directory for relative path resolution.

        Returns:
            Resolved destination path.
        """
        destination = rule.destination

        # Handle relative paths
        if not destination.is_absolute():
            destination = base_directory / destination

        # Create destination if it doesn't exist
        destination.mkdir(parents=True, exist_ok=True)

        # Handle destination variables/placeholders
        destination_str = str(destination)
        destination_str = destination_str.replace("{filename}", file_path.stem)
        destination_str = destination_str.replace("{extension}", file_path.suffix[1:])
        destination_str = destination_str.replace(
            "{year}", datetime.now().strftime("%Y")
        )
        destination_str = destination_str.replace(
            "{month}", datetime.now().strftime("%m")
        )
        destination_str = destination_str.replace("{day}", datetime.now().strftime("%d"))

        return Path(destination_str)

    def organize_files(
        self,
        source_directory: Optional[str] = None,
        recursive: bool = True,
        dry_run: bool = False,
        match_mode: str = "first",
    ) -> Dict[str, Any]:
        """Organize files based on pattern rules.

        Args:
            source_directory: Directory to scan (overrides config).
            recursive: Whether to search recursively.
            dry_run: If True, show what would be done without actually moving files.
            match_mode: "first" to use first matching rule, "all" to apply all matches.

        Returns:
            Dictionary with operation results and statistics.

        Raises:
            FileNotFoundError: If source directory doesn't exist.
            ValueError: If match_mode is invalid.
        """
        if match_mode not in ["first", "all"]:
            raise ValueError("match_mode must be 'first' or 'all'")

        source_config = self.config.get("source", {})
        if source_directory:
            source_dir = Path(source_directory)
        else:
            source_dir = Path(source_config.get("directory", "."))

        if not source_dir.exists():
            raise FileNotFoundError(f"Source directory does not exist: {source_dir}")

        if not source_dir.is_dir():
            raise ValueError(f"Path is not a directory: {source_dir}")

        logger.info(f"Organizing files in: {source_dir} (recursive={recursive}, dry_run={dry_run})")

        # Reset stats
        self.stats = {
            "files_scanned": 0,
            "files_matched": 0,
            "files_moved": 0,
            "files_skipped": 0,
            "errors": 0,
        }
        self.operations = []

        # Get operation settings
        operation_config = self.config.get("operations", {})
        create_backup = operation_config.get("create_backup", False)
        skip_existing = operation_config.get("skip_existing", True)
        preserve_structure = operation_config.get("preserve_structure", False)

        # Scan files
        if recursive:
            iterator = source_dir.rglob("*")
        else:
            iterator = source_dir.glob("*")

        for item_path in iterator:
            if not item_path.is_file():
                continue

            self.stats["files_scanned"] += 1

            # Check exclusions
            if self._is_excluded(item_path):
                logger.debug(f"Excluded: {item_path}")
                continue

            try:
                # Find matching rule(s)
                if match_mode == "first":
                    matching_rules = [self._find_matching_rule(item_path)]
                    matching_rules = [r for r in matching_rules if r is not None]
                else:
                    matching_rules = [r for r in self.rules if r.matches(item_path)]

                if not matching_rules:
                    logger.debug(f"No matching rule for: {item_path.name}")
                    self.stats["files_skipped"] += 1
                    continue

                self.stats["files_matched"] += 1

                # Process each matching rule
                for rule in matching_rules:
                    destination = self._resolve_destination(item_path, rule, source_dir)

                    # Handle preserve_structure option
                    if preserve_structure:
                        rel_path = item_path.relative_to(source_dir)
                        destination = destination / rel_path.parent
                        destination.mkdir(parents=True, exist_ok=True)

                    destination_file = destination / item_path.name

                    # Check if destination file already exists
                    if destination_file.exists() and skip_existing:
                        logger.warning(
                            f"Destination file exists, skipping: {destination_file}"
                        )
                        self.stats["files_skipped"] += 1
                        continue

                    # Create backup if requested
                    if create_backup and not dry_run:
                        backup_dir = source_dir / ".backup"
                        backup_dir.mkdir(exist_ok=True)
                        backup_path = backup_dir / item_path.relative_to(source_dir)
                        backup_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item_path, backup_path)
                        logger.debug(f"Created backup: {backup_path}")

                    # Move file
                    operation = {
                        "file": str(item_path),
                        "rule": rule.name,
                        "destination": str(destination_file),
                        "status": "pending",
                    }

                    if dry_run:
                        logger.info(
                            f"[DRY RUN] Would move: {item_path.name} -> {destination_file}"
                        )
                        operation["status"] = "dry_run"
                    else:
                        try:
                            shutil.move(str(item_path), str(destination_file))
                            logger.info(f"Moved: {item_path.name} -> {destination_file}")
                            operation["status"] = "moved"
                            self.stats["files_moved"] += 1
                        except (OSError, PermissionError) as e:
                            logger.error(f"Error moving {item_path} to {destination_file}: {e}")
                            operation["status"] = "error"
                            operation["error"] = str(e)
                            self.stats["errors"] += 1

                    self.operations.append(operation)

                    # If match_mode is "first", only process first match
                    if match_mode == "first":
                        break

            except Exception as e:
                logger.error(f"Error processing {item_path}: {e}", exc_info=True)
                self.stats["errors"] += 1

        logger.info(
            f"Organization complete: {self.stats['files_moved']} moved, "
            f"{self.stats['files_skipped']} skipped, {self.stats['errors']} errors"
        )

        return {
            "stats": self.stats.copy(),
            "operations": self.operations.copy(),
        }

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate text report of organization operations.

        Args:
            output_file: Path to output file (overrides config).

        Returns:
            Report content as string.
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("Pattern File Organization Report")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Summary
        report_lines.append("Summary Statistics")
        report_lines.append("-" * 80)
        report_lines.append(f"Files scanned: {self.stats['files_scanned']:,}")
        report_lines.append(f"Files matched: {self.stats['files_matched']:,}")
        report_lines.append(f"Files moved: {self.stats['files_moved']:,}")
        report_lines.append(f"Files skipped: {self.stats['files_skipped']:,}")
        report_lines.append(f"Errors: {self.stats['errors']}")
        report_lines.append("")

        # Rules summary
        report_lines.append("Pattern Rules")
        report_lines.append("-" * 80)
        for rule in self.rules:
            status = "enabled" if rule.enabled else "disabled"
            report_lines.append(
                f"  {rule.name} (priority: {rule.priority}, {status}): "
                f"pattern='{rule.pattern}' -> {rule.destination}"
            )
        report_lines.append("")

        # Operations
        if self.operations:
            report_lines.append("File Operations")
            report_lines.append("-" * 80)
            for op in self.operations:
                status_icon = {
                    "moved": "✓",
                    "dry_run": "[DRY RUN]",
                    "error": "✗",
                    "pending": "?",
                }.get(op["status"], "?")
                report_lines.append(f"{status_icon} {op['file']}")
                report_lines.append(f"    Rule: {op['rule']}")
                report_lines.append(f"    Destination: {op['destination']}")
                if op["status"] == "error" and "error" in op:
                    report_lines.append(f"    Error: {op['error']}")
                report_lines.append("")
        else:
            report_lines.append("No file operations performed.")

        report_lines.append("=" * 80)

        report_content = "\n".join(report_lines)

        # Write to file if specified
        if output_file:
            output_path = Path(output_file)
            if not output_path.is_absolute():
                output_dir = self.config.get("report", {}).get("output_directory", "output")
                output_path = Path(output_dir) / output_file
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            logger.info(f"Report saved to: {output_path}")

        return report_content

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics.

        Returns:
            Dictionary with statistics.
        """
        return self.stats.copy()


def main() -> int:
    """Main entry point for pattern file organizer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Organize files using custom pattern rules"
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
        help="Source directory to organize (overrides config)",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Disable recursive directory search",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually moving files",
    )
    parser.add_argument(
        "--match-mode",
        choices=["first", "all"],
        default="first",
        help="Match mode: 'first' uses first matching rule, 'all' applies all matches",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file for report (overrides config)",
    )

    args = parser.parse_args()

    try:
        organizer = PatternFileOrganizer(config_path=args.config)

        # Organize files
        result = organizer.organize_files(
            source_directory=args.directory,
            recursive=not args.no_recursive,
            dry_run=args.dry_run,
            match_mode=args.match_mode,
        )

        # Generate report
        output_file = args.output or organizer.config.get("report", {}).get("output_file")
        report_content = organizer.generate_report(output_file=output_file)

        # Print summary
        print("\n" + "=" * 60)
        print("Pattern File Organization Summary")
        print("=" * 60)
        stats = result["stats"]
        print(f"Files scanned: {stats['files_scanned']:,}")
        print(f"Files matched: {stats['files_matched']:,}")
        print(f"Files moved: {stats['files_moved']:,}")
        print(f"Files skipped: {stats['files_skipped']:,}")
        print(f"Errors: {stats['errors']}")

        if args.dry_run:
            print("\n[DRY RUN MODE] No files were actually moved.")

        if output_file:
            print(f"\nReport saved to: {output_file}")

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
