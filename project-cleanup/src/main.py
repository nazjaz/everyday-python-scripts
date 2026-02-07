"""Project Cleanup - CLI tool for cleaning up old project folders.

This module provides a command-line tool for archiving or removing project
folders based on inactivity periods. It scans a directory for projects and
processes them according to configurable rules.
"""

import argparse
import logging
import logging.handlers
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ProjectCleanup:
    """Cleans up old project folders based on inactivity."""

    def __init__(self, config: Dict) -> None:
        """Initialize ProjectCleanup.

        Args:
            config: Configuration dictionary containing cleanup settings.
        """
        self.config = config
        self.source_dir = Path(config.get("source_directory", "."))
        self.archive_dir = Path(config.get("archive_directory", "./archive"))
        self.action_config = config.get("actions", {})
        self.filter_config = config.get("filtering", {})
        self.safety_config = config.get("safety", {})

        # Setup logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging for the application."""
        log_level = self.config.get("logging", {}).get("level", "INFO")
        log_file = self.config.get("logging", {}).get("file", "logs/cleanup.log")

        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.handlers.RotatingFileHandler(
                    log_file, maxBytes=10485760, backupCount=5
                ),
                logging.StreamHandler(sys.stdout),
            ],
        )

    def get_project_last_modified(self, project_path: Path) -> Optional[datetime]:
        """Get the last modification time of a project.

        Checks the most recent modification time across all files in the
        project directory.

        Args:
            project_path: Path to the project directory.

        Returns:
            Datetime of last modification, or None if project is empty or
            inaccessible.
        """
        if not project_path.exists() or not project_path.is_dir():
            return None

        last_modified = None
        try:
            for root, dirs, files in os.walk(project_path):
                # Skip excluded directories
                dirs[:] = [
                    d
                    for d in dirs
                    if not self._should_exclude_directory(Path(root) / d)
                ]

                for file in files:
                    file_path = Path(root) / file
                    if self._should_exclude_file(file_path):
                        continue

                    try:
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if last_modified is None or mtime > last_modified:
                            last_modified = mtime
                    except (OSError, PermissionError) as e:
                        logger.warning(
                            f"Cannot access {file_path}: {e}",
                            extra={"file_path": str(file_path)},
                        )
                        continue

            # Also check directory modification time
            try:
                dir_mtime = datetime.fromtimestamp(project_path.stat().st_mtime)
                if last_modified is None or dir_mtime > last_modified:
                    last_modified = dir_mtime
            except (OSError, PermissionError):
                pass

        except (OSError, PermissionError) as e:
            logger.error(
                f"Cannot access project directory {project_path}: {e}",
                extra={"project_path": str(project_path)},
            )
            return None

        return last_modified

    def _should_exclude_directory(self, dir_path: Path) -> bool:
        """Check if directory should be excluded from processing.

        Args:
            dir_path: Path to directory to check.

        Returns:
            True if directory should be excluded, False otherwise.
        """
        exclude_patterns = self.filter_config.get("exclude_directories", [])
        dir_name = dir_path.name

        for pattern in exclude_patterns:
            if pattern in dir_name or dir_name.startswith(pattern):
                return True

        # Always exclude common system directories
        system_dirs = {".git", "__pycache__", ".pytest_cache", "node_modules"}
        return dir_name in system_dirs

    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from modification time check.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file should be excluded, False otherwise.
        """
        exclude_patterns = self.filter_config.get("exclude_files", [])
        file_name = file_path.name

        for pattern in exclude_patterns:
            if pattern in file_name or file_name.endswith(pattern):
                return True

        return False

    def is_project_inactive(
        self, project_path: Path, threshold_days: int
    ) -> Tuple[bool, Optional[datetime]]:
        """Check if project has been inactive for specified days.

        Args:
            project_path: Path to the project directory.
            threshold_days: Number of days of inactivity threshold.

        Returns:
            Tuple of (is_inactive, last_modified_datetime).
        """
        last_modified = self.get_project_last_modified(project_path)
        if last_modified is None:
            return False, None

        threshold_date = datetime.now() - timedelta(days=threshold_days)
        is_inactive = last_modified < threshold_date

        return is_inactive, last_modified

    def archive_project(self, project_path: Path) -> bool:
        """Archive a project by moving it to archive directory.

        Args:
            project_path: Path to the project directory to archive.

        Returns:
            True if archiving succeeded, False otherwise.
        """
        try:
            # Create archive directory if it doesn't exist
            self.archive_dir.mkdir(parents=True, exist_ok=True)

            # Generate archive path with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"{project_path.name}_{timestamp}"
            archive_path = self.archive_dir / archive_name

            # Move project to archive
            shutil.move(str(project_path), str(archive_path))
            logger.info(
                f"Archived project: {project_path.name} -> {archive_path}",
                extra={
                    "source": str(project_path),
                    "destination": str(archive_path),
                },
            )
            return True

        except (OSError, PermissionError, shutil.Error) as e:
            logger.error(
                f"Failed to archive project {project_path}: {e}",
                extra={"project_path": str(project_path), "error": str(e)},
            )
            return False

    def remove_project(self, project_path: Path) -> bool:
        """Remove a project directory permanently.

        Args:
            project_path: Path to the project directory to remove.

        Returns:
            True if removal succeeded, False otherwise.
        """
        try:
            shutil.rmtree(project_path)
            logger.info(
                f"Removed project: {project_path}",
                extra={"project_path": str(project_path)},
            )
            return True

        except (OSError, PermissionError, shutil.Error) as e:
            logger.error(
                f"Failed to remove project {project_path}: {e}",
                extra={"project_path": str(project_path), "error": str(e)},
            )
            return False

    def scan_projects(self) -> List[Path]:
        """Scan source directory for project folders.

        Returns:
            List of paths to project directories.
        """
        projects = []
        if not self.source_dir.exists():
            logger.error(f"Source directory does not exist: {self.source_dir}")
            return projects

        try:
            for item in self.source_dir.iterdir():
                if not item.is_dir():
                    continue

                # Skip excluded directories
                if self._should_exclude_directory(item):
                    continue

                # Check if it looks like a project directory
                if self._is_project_directory(item):
                    projects.append(item)

        except (OSError, PermissionError) as e:
            logger.error(
                f"Cannot scan source directory {self.source_dir}: {e}",
                extra={"source_directory": str(self.source_dir), "error": str(e)},
            )

        return projects

    def _is_project_directory(self, dir_path: Path) -> bool:
        """Check if directory appears to be a project directory.

        Args:
            dir_path: Path to directory to check.

        Returns:
            True if directory appears to be a project, False otherwise.
        """
        # Check for common project indicators
        project_indicators = self.filter_config.get("project_indicators", [])
        if not project_indicators:
            # Default indicators
            project_indicators = [
                "README.md",
                "requirements.txt",
                "package.json",
                "setup.py",
                "pyproject.toml",
                "Cargo.toml",
                "go.mod",
                "pom.xml",
            ]

        for indicator in project_indicators:
            if (dir_path / indicator).exists():
                return True

        # If no indicators found, check if directory has subdirectories
        # suggesting it's a project structure
        try:
            subdirs = [d for d in dir_path.iterdir() if d.is_dir()]
            if len(subdirs) > 0:
                return True
        except (OSError, PermissionError):
            pass

        return False

    def process_projects(self, dry_run: bool = False) -> Dict[str, int]:
        """Process all projects according to configuration.

        Args:
            dry_run: If True, only report what would be done without
                making changes.

        Returns:
            Dictionary with counts of processed projects.
        """
        results = {
            "scanned": 0,
            "archived": 0,
            "removed": 0,
            "skipped": 0,
            "failed": 0,
        }

        projects = self.scan_projects()
        results["scanned"] = len(projects)

        logger.info(
            f"Found {len(projects)} projects to process",
            extra={"project_count": len(projects), "dry_run": dry_run},
        )

        archive_threshold = self.action_config.get("archive_after_days", 90)
        remove_threshold = self.action_config.get("remove_after_days", 365)

        for project_path in projects:
            try:
                # Check for archiving threshold
                is_inactive_archive, last_modified = self.is_project_inactive(
                    project_path, archive_threshold
                )

                if is_inactive_archive and last_modified:
                    # Check if it should be removed instead
                    is_inactive_remove, _ = self.is_project_inactive(
                        project_path, remove_threshold
                    )

                    if is_inactive_remove and self.action_config.get(
                        "enable_removal", False
                    ):
                        if dry_run:
                            logger.info(
                                f"[DRY RUN] Would remove: {project_path.name} "
                                f"(last modified: {last_modified.date()})"
                            )
                        else:
                            if self.remove_project(project_path):
                                results["removed"] += 1
                            else:
                                results["failed"] += 1
                    else:
                        if dry_run:
                            logger.info(
                                f"[DRY RUN] Would archive: {project_path.name} "
                                f"(last modified: {last_modified.date()})"
                            )
                        else:
                            if self.archive_project(project_path):
                                results["archived"] += 1
                            else:
                                results["failed"] += 1
                else:
                    results["skipped"] += 1
                    logger.debug(
                        f"Skipped active project: {project_path.name}",
                        extra={
                            "project": str(project_path),
                            "last_modified": (
                                last_modified.isoformat() if last_modified else None
                            ),
                        },
                    )

            except Exception as e:
                logger.error(
                    f"Error processing project {project_path}: {e}",
                    extra={"project_path": str(project_path), "error": str(e)},
                    exc_info=True,
                )
                results["failed"] += 1

        return results


def load_config(config_path: Path) -> Dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to configuration file.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        yaml.YAMLError: If config file is invalid YAML.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config or {}
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in config file: {e}") from e


def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Clean up old project folders based on inactivity"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making changes",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(str(e))
        sys.exit(1)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    cleanup = ProjectCleanup(config)

    if args.dry_run:
        logger.info("Running in dry-run mode - no changes will be made")

    results = cleanup.process_projects(dry_run=args.dry_run)

    # Print summary
    print("\n" + "=" * 60)
    print("Cleanup Summary")
    print("=" * 60)
    print(f"Projects scanned: {results['scanned']}")
    print(f"Projects archived: {results['archived']}")
    print(f"Projects removed: {results['removed']}")
    print(f"Projects skipped: {results['skipped']}")
    print(f"Projects failed: {results['failed']}")
    print("=" * 60)

    if results["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
