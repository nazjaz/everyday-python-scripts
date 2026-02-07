"""File Ownership Analyzer - Organize files by owner and group permissions.

This module provides functionality to analyze file ownership patterns in
multi-user systems, organizing files by owner or group permissions and
identifying ownership patterns.
"""

import grp
import logging
import logging.handlers
import os
import pwd
import stat
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FileOwnershipAnalyzer:
    """Analyzes file ownership and group permissions."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize FileOwnershipAnalyzer with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.file_data: List[Dict[str, Any]] = []
        self.owner_stats: Dict[str, Dict[str, Any]] = {}
        self.group_stats: Dict[str, Dict[str, Any]] = {}
        self.stats = {
            "files_scanned": 0,
            "directories_scanned": 0,
            "errors": 0,
            "unique_owners": 0,
            "unique_groups": 0,
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
        if os.getenv("SCAN_DIRECTORY"):
            config["scan"]["directory"] = os.getenv("SCAN_DIRECTORY")
        if os.getenv("OUTPUT_DIRECTORY"):
            config["output"]["directory"] = os.getenv("OUTPUT_DIRECTORY")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/ownership_analyzer.log")

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

    def _get_owner_name(self, uid: int) -> str:
        """Get owner name from user ID.

        Args:
            uid: User ID.

        Returns:
            Owner username or UID as string if not found.
        """
        try:
            return pwd.getpwuid(uid).pw_name
        except KeyError:
            return str(uid)

    def _get_group_name(self, gid: int) -> str:
        """Get group name from group ID.

        Args:
            gid: Group ID.

        Returns:
            Group name or GID as string if not found.
        """
        try:
            return grp.getgrgid(gid).gr_name
        except KeyError:
            return str(gid)

    def _get_file_permissions(self, file_path: Path) -> Dict[str, Any]:
        """Get file permissions and ownership information.

        Args:
            file_path: Path to file.

        Returns:
            Dictionary with permission and ownership information.
        """
        try:
            stat_info = file_path.stat()
            mode = stat_info.st_mode

            owner_uid = stat_info.st_uid
            group_gid = stat_info.st_gid

            owner_name = self._get_owner_name(owner_uid)
            group_name = self._get_group_name(group_gid)

            # Parse permissions
            permissions = {
                "owner_read": bool(mode & stat.S_IRUSR),
                "owner_write": bool(mode & stat.S_IWUSR),
                "owner_execute": bool(mode & stat.S_IXUSR),
                "group_read": bool(mode & stat.S_IRGRP),
                "group_write": bool(mode & stat.S_IWGRP),
                "group_execute": bool(mode & stat.S_IXGRP),
                "other_read": bool(mode & stat.S_IROTH),
                "other_write": bool(mode & stat.S_IWOTH),
                "other_execute": bool(mode & stat.S_IXOTH),
            }

            # Calculate octal permission
            octal_permission = oct(mode & 0o777)[2:]

            return {
                "path": str(file_path),
                "name": file_path.name,
                "owner_uid": owner_uid,
                "owner_name": owner_name,
                "group_gid": group_gid,
                "group_name": group_name,
                "permissions": permissions,
                "octal_permission": octal_permission,
                "size": stat_info.st_size,
                "is_file": file_path.is_file(),
                "is_directory": file_path.is_dir(),
                "is_symlink": file_path.is_symlink(),
            }

        except (OSError, PermissionError) as e:
            logger.warning(f"Could not get permissions for {file_path}: {e}")
            self.stats["errors"] += 1
            return {}

    def _is_excluded(self, file_path: Path) -> bool:
        """Check if file should be excluded from scan.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file should be excluded, False otherwise.
        """
        exclude_config = self.config.get("scan", {}).get("exclude", {})
        exclude_patterns = exclude_config.get("patterns", [])
        exclude_dirs = exclude_config.get("directories", [])

        # Check directory exclusion
        for exclude_dir in exclude_dirs:
            if exclude_dir in file_path.parts:
                return True

        # Check pattern exclusion
        file_str = str(file_path)
        for pattern in exclude_patterns:
            try:
                import re

                if re.search(pattern, file_str):
                    return True
            except Exception:
                pass

        return False

    def scan_directory(
        self, directory: Optional[str] = None, recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """Scan directory and collect file ownership information.

        Args:
            directory: Directory to scan (overrides config).
            recursive: Whether to scan recursively.

        Returns:
            List of file information dictionaries.

        Raises:
            FileNotFoundError: If directory doesn't exist.
            PermissionError: If directory is not accessible.
        """
        if directory:
            scan_dir = Path(directory)
        else:
            scan_dir = Path(self.config.get("scan", {}).get("directory", "."))

        if not scan_dir.exists():
            raise FileNotFoundError(f"Directory does not exist: {scan_dir}")

        if not scan_dir.is_dir():
            raise ValueError(f"Path is not a directory: {scan_dir}")

        logger.info(f"Scanning directory: {scan_dir} (recursive: {recursive})")

        self.file_data = []
        self.stats["files_scanned"] = 0
        self.stats["directories_scanned"] = 0
        self.stats["errors"] = 0

        # Walk directory
        if recursive:
            iterator = scan_dir.rglob("*")
        else:
            iterator = scan_dir.glob("*")

        for item_path in iterator:
            # Skip if excluded
            if self._is_excluded(item_path):
                continue

            # Count directories
            if item_path.is_dir():
                self.stats["directories_scanned"] += 1
                continue

            # Only process files
            if not item_path.is_file():
                continue

            self.stats["files_scanned"] += 1

            # Get file information
            file_info = self._get_file_permissions(item_path)
            if file_info:
                self.file_data.append(file_info)

        logger.info(
            f"Scanned {self.stats['files_scanned']} file(s) in "
            f"{self.stats['directories_scanned']} directory(ies)"
        )

        return self.file_data

    def organize_by_owner(self) -> Dict[str, List[Dict[str, Any]]]:
        """Organize files by owner.

        Returns:
            Dictionary mapping owner names to lists of file information.
        """
        owner_files: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for file_info in self.file_data:
            owner = file_info.get("owner_name", "unknown")
            owner_files[owner].append(file_info)

        logger.info(f"Organized files by {len(owner_files)} owner(s)")
        return dict(owner_files)

    def organize_by_group(self) -> Dict[str, List[Dict[str, Any]]]:
        """Organize files by group.

        Returns:
            Dictionary mapping group names to lists of file information.
        """
        group_files: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for file_info in self.file_data:
            group = file_info.get("group_name", "unknown")
            group_files[group].append(file_info)

        logger.info(f"Organized files by {len(group_files)} group(s)")
        return dict(group_files)

    def calculate_owner_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Calculate statistics for each owner.

        Returns:
            Dictionary mapping owner names to statistics.
        """
        owner_files = self.organize_by_owner()
        self.owner_stats = {}

        for owner, files in owner_files.items():
            total_size = sum(f.get("size", 0) for f in files)
            file_count = len(files)

            # Count by file type (extension)
            extensions: Dict[str, int] = defaultdict(int)
            for file_info in files:
                ext = Path(file_info["path"]).suffix.lower() or "no_extension"
                extensions[ext] += 1

            # Count by group
            groups: Dict[str, int] = defaultdict(int)
            for file_info in files:
                group = file_info.get("group_name", "unknown")
                groups[group] += 1

            self.owner_stats[owner] = {
                "file_count": file_count,
                "total_size": total_size,
                "average_size": total_size / file_count if file_count > 0 else 0,
                "extensions": dict(extensions),
                "groups": dict(groups),
                "files": files,
            }

        self.stats["unique_owners"] = len(self.owner_stats)
        logger.info(f"Calculated statistics for {len(self.owner_stats)} owner(s)")

        return self.owner_stats

    def calculate_group_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Calculate statistics for each group.

        Returns:
            Dictionary mapping group names to statistics.
        """
        group_files = self.organize_by_group()
        self.group_stats = {}

        for group, files in group_files.items():
            total_size = sum(f.get("size", 0) for f in files)
            file_count = len(files)

            # Count by owner
            owners: Dict[str, int] = defaultdict(int)
            for file_info in files:
                owner = file_info.get("owner_name", "unknown")
                owners[owner] += 1

            # Count by file type (extension)
            extensions: Dict[str, int] = defaultdict(int)
            for file_info in files:
                ext = Path(file_info["path"]).suffix.lower() or "no_extension"
                extensions[ext] += 1

            self.group_stats[group] = {
                "file_count": file_count,
                "total_size": total_size,
                "average_size": total_size / file_count if file_count > 0 else 0,
                "owners": dict(owners),
                "extensions": dict(extensions),
                "files": files,
            }

        self.stats["unique_groups"] = len(self.group_stats)
        logger.info(f"Calculated statistics for {len(self.group_stats)} group(s)")

        return self.group_stats

    def identify_patterns(self) -> Dict[str, Any]:
        """Identify ownership patterns.

        Returns:
            Dictionary with identified patterns.
        """
        if not self.owner_stats:
            self.calculate_owner_statistics()
        if not self.group_stats:
            self.calculate_group_statistics()

        patterns = {
            "top_owners_by_count": [],
            "top_owners_by_size": [],
            "top_groups_by_count": [],
            "top_groups_by_size": [],
            "orphaned_files": [],
            "common_ownership_patterns": [],
        }

        # Top owners by file count
        owners_by_count = sorted(
            self.owner_stats.items(),
            key=lambda x: x[1]["file_count"],
            reverse=True,
        )
        patterns["top_owners_by_count"] = [
            {"owner": owner, "file_count": stats["file_count"]}
            for owner, stats in owners_by_count[:10]
        ]

        # Top owners by total size
        owners_by_size = sorted(
            self.owner_stats.items(),
            key=lambda x: x[1]["total_size"],
            reverse=True,
        )
        patterns["top_owners_by_size"] = [
            {"owner": owner, "total_size": stats["total_size"]}
            for owner, stats in owners_by_size[:10]
        ]

        # Top groups by file count
        groups_by_count = sorted(
            self.group_stats.items(),
            key=lambda x: x[1]["file_count"],
            reverse=True,
        )
        patterns["top_groups_by_count"] = [
            {"group": group, "file_count": stats["file_count"]}
            for group, stats in groups_by_count[:10]
        ]

        # Top groups by total size
        groups_by_size = sorted(
            self.group_stats.items(),
            key=lambda x: x[1]["total_size"],
            reverse=True,
        )
        patterns["top_groups_by_size"] = [
            {"group": group, "total_size": stats["total_size"]}
            for group, stats in groups_by_size[:10]
        ]

        # Find files where owner != group (potential issues)
        for file_info in self.file_data:
            owner = file_info.get("owner_name", "")
            group = file_info.get("group_name", "")
            if owner != group and owner != "unknown" and group != "unknown":
                patterns["common_ownership_patterns"].append(
                    {
                        "path": file_info["path"],
                        "owner": owner,
                        "group": group,
                    }
                )

        logger.info("Identified ownership patterns")
        return patterns

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate text report of ownership analysis.

        Args:
            output_file: Path to output file (overrides config).

        Returns:
            Report content as string.
        """
        if not self.owner_stats:
            self.calculate_owner_statistics()
        if not self.group_stats:
            self.calculate_group_statistics()

        patterns = self.identify_patterns()

        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append("File Ownership Analysis Report")
        report_lines.append("=" * 70)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Summary statistics
        report_lines.append("Summary Statistics")
        report_lines.append("-" * 70)
        report_lines.append(f"Files scanned: {self.stats['files_scanned']}")
        report_lines.append(f"Directories scanned: {self.stats['directories_scanned']}")
        report_lines.append(f"Unique owners: {self.stats['unique_owners']}")
        report_lines.append(f"Unique groups: {self.stats['unique_groups']}")
        report_lines.append(f"Errors: {self.stats['errors']}")
        report_lines.append("")

        # Top owners by count
        report_lines.append("Top 10 Owners by File Count")
        report_lines.append("-" * 70)
        for item in patterns["top_owners_by_count"]:
            report_lines.append(
                f"  {item['owner']:20s} {item['file_count']:10d} files"
            )
        report_lines.append("")

        # Top owners by size
        report_lines.append("Top 10 Owners by Total Size")
        report_lines.append("-" * 70)
        for item in patterns["top_owners_by_size"]:
            size_mb = item["total_size"] / (1024 * 1024)
            report_lines.append(
                f"  {item['owner']:20s} {size_mb:10.2f} MB"
            )
        report_lines.append("")

        # Top groups by count
        report_lines.append("Top 10 Groups by File Count")
        report_lines.append("-" * 70)
        for item in patterns["top_groups_by_count"]:
            report_lines.append(
                f"  {item['group']:20s} {item['file_count']:10d} files"
            )
        report_lines.append("")

        # Top groups by size
        report_lines.append("Top 10 Groups by Total Size")
        report_lines.append("-" * 70)
        for item in patterns["top_groups_by_size"]:
            size_mb = item["total_size"] / (1024 * 1024)
            report_lines.append(
                f"  {item['group']:20s} {size_mb:10.2f} MB"
            )
        report_lines.append("")

        # Ownership patterns
        if patterns["common_ownership_patterns"]:
            report_lines.append("Files with Owner != Group (Sample)")
            report_lines.append("-" * 70)
            for item in patterns["common_ownership_patterns"][:20]:
                report_lines.append(
                    f"  {item['path']} (owner: {item['owner']}, group: {item['group']})"
                )
            report_lines.append("")

        report_content = "\n".join(report_lines)

        # Write to file if specified
        if output_file:
            output_path = Path(output_file)
            if not output_path.is_absolute():
                output_dir = self.config.get("output", {}).get("directory", "output")
                output_path = Path(output_dir) / output_file
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            logger.info(f"Report saved to: {output_path}")

        return report_content

    def get_files_by_owner(self, owner: str) -> List[Dict[str, Any]]:
        """Get all files owned by specific owner.

        Args:
            owner: Owner name or UID.

        Returns:
            List of file information dictionaries.
        """
        owner_files = self.organize_by_owner()
        return owner_files.get(owner, [])

    def get_files_by_group(self, group: str) -> List[Dict[str, Any]]:
        """Get all files in specific group.

        Args:
            group: Group name or GID.

        Returns:
            List of file information dictionaries.
        """
        group_files = self.organize_by_group()
        return group_files.get(group, [])

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics.

        Returns:
            Dictionary with statistics.
        """
        return self.stats.copy()


def main() -> int:
    """Main entry point for file ownership analyzer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze file ownership and group permissions"
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
        help="Directory to scan (overrides config)",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Disable recursive directory scan",
    )
    parser.add_argument(
        "-o",
        "--owner",
        help="Show files for specific owner",
    )
    parser.add_argument(
        "-g",
        "--group",
        help="Show files for specific group",
    )
    parser.add_argument(
        "-r",
        "--report",
        help="Generate report file (specify filename)",
    )
    parser.add_argument(
        "--list-owners",
        action="store_true",
        help="List all owners",
    )
    parser.add_argument(
        "--list-groups",
        action="store_true",
        help="List all groups",
    )

    args = parser.parse_args()

    try:
        analyzer = FileOwnershipAnalyzer(config_path=args.config)

        # Scan directory
        analyzer.scan_directory(
            directory=args.directory, recursive=not args.no_recursive
        )

        # Calculate statistics
        analyzer.calculate_owner_statistics()
        analyzer.calculate_group_statistics()

        # Handle specific queries
        if args.owner:
            files = analyzer.get_files_by_owner(args.owner)
            print(f"\nFiles owned by '{args.owner}': {len(files)}")
            print("=" * 70)
            for file_info in files[:50]:  # Limit output
                print(f"  {file_info['path']}")
            if len(files) > 50:
                print(f"  ... and {len(files) - 50} more files")

        if args.group:
            files = analyzer.get_files_by_group(args.group)
            print(f"\nFiles in group '{args.group}': {len(files)}")
            print("=" * 70)
            for file_info in files[:50]:  # Limit output
                print(f"  {file_info['path']}")
            if len(files) > 50:
                print(f"  ... and {len(files) - 50} more files")

        if args.list_owners:
            owner_stats = analyzer.calculate_owner_statistics()
            print("\nAll Owners:")
            print("=" * 70)
            for owner, stats in sorted(owner_stats.items()):
                print(f"  {owner:20s} {stats['file_count']:6d} files, "
                      f"{stats['total_size'] / (1024*1024):.2f} MB")

        if args.list_groups:
            group_stats = analyzer.calculate_group_statistics()
            print("\nAll Groups:")
            print("=" * 70)
            for group, stats in sorted(group_stats.items()):
                print(f"  {group:20s} {stats['file_count']:6d} files, "
                      f"{stats['total_size'] / (1024*1024):.2f} MB")

        # Generate report
        if args.report:
            report_content = analyzer.generate_report(output_file=args.report)
            print(f"\nReport generated: {args.report}")
        else:
            # Print summary if no specific action
            if not any([args.owner, args.group, args.list_owners, args.list_groups]):
                patterns = analyzer.identify_patterns()
                print("\n" + "=" * 70)
                print("Ownership Analysis Summary")
                print("=" * 70)
                print(f"Files scanned: {analyzer.stats['files_scanned']}")
                print(f"Unique owners: {analyzer.stats['unique_owners']}")
                print(f"Unique groups: {analyzer.stats['unique_groups']}")
                print("\nTop 5 Owners by File Count:")
                for item in patterns["top_owners_by_count"][:5]:
                    print(f"  {item['owner']}: {item['file_count']} files")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        return 1
    except PermissionError as e:
        logger.error(f"Permission error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
